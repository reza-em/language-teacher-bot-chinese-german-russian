"""Pluggable OpenAI-compatible LLM client (optional). Key ONLY from the environment (CHINESE_LLM_API_KEY); base URL / model from env
or the owner's admin panel (stored in the DB, never the key). Everything degrades gracefully when not configured."""
import os, json, logging, requests
import config, db

log = logging.getLogger("llm")

def settings():
    s = db.meta_get("llm", {}) or {}
    return {"enabled": s.get("enabled", True),
            "base": (s.get("base") or os.environ.get(config.LLM_BASE_ENV) or config.LLM_DEFAULT_BASE).rstrip("/"),
            "model": s.get("model") or os.environ.get(config.LLM_MODEL_ENV) or config.LLM_DEFAULT_MODEL,
            "stt_model": s.get("stt_model") or os.environ.get(config.LLM_STT_ENV) or "",
            "daily_limit": int(s.get("daily_limit", config.LLM_DAILY_LIMIT))}

def set_setting(**kw):
    s = db.meta_get("llm", {}) or {}; s.update(kw); db.meta_set("llm", s)

def key(): return os.environ.get(config.LLM_KEY_ENV, "")
def configured(): return bool(key()) and settings()["enabled"]

def _post(path, **kw):
    s = settings()
    return requests.post(s["base"] + path, headers={"Authorization": "Bearer " + key()}, timeout=60, **kw)

def chat(system, user, max_tokens=600, history=None):
    """-> text or None (never raises, never logs the key)."""
    if not configured(): return None
    s = settings()
    msgs = [{"role": "system", "content": system}] + (history or []) + [{"role": "user", "content": user}]
    try:
        r = _post("/chat/completions", json={"model": s["model"], "messages": msgs, "max_tokens": max_tokens, "temperature": 0.3})
        if r.status_code != 200:
            log.warning("llm HTTP %s", r.status_code); return None
        return (r.json()["choices"][0]["message"]["content"] or "").strip()
    except Exception as e:
        log.warning("llm failed: %s", type(e).__name__); return None

def transcribe(audio_bytes, filename="voice.ogg"):
    """Speech-to-text for pronunciation checks (needs CHINESE_LLM_STT_MODEL + a provider with /audio/transcriptions)."""
    s = settings()
    if not configured() or not s["stt_model"]: return None
    try:
        r = _post("/audio/transcriptions", data={"model": s["stt_model"], "language": "zh"}, files={"file": (filename, audio_bytes)})
        if r.status_code != 200: log.warning("stt HTTP %s", r.status_code); return None
        return (r.json().get("text") or "").strip()
    except Exception as e:
        log.warning("stt failed: %s", type(e).__name__); return None

LANG_NAMES = {"fa": "Persian (Farsi)", "en": "English", "de": "German"}

def teacher_system(lang):
    return ("You are a friendly, precise Mandarin Chinese teacher for learners whose first language is Persian. "
            f"Answer in {LANG_NAMES.get(lang, 'Persian')}. Keep it short (max ~180 words), use simplified characters with pinyin (tone marks) and a short translation for every Chinese example. "
            "Explain grammar simply with 1-3 examples. If the question is not about Chinese language or learning, politely say you only help with Chinese. Do not invent words; say if unsure.")

def grade_system(lang):
    return ("You grade a Chinese learner's answer. Reply in " + LANG_NAMES.get(lang, "Persian") +
            ". First line: exactly VERDICT: CORRECT, VERDICT: ALMOST or VERDICT: WRONG. Then 1-3 short sentences: what is wrong (characters, word choice, word order, tone/pinyin), and the corrected Chinese with pinyin. Accept natural synonyms.")

def gloss_system(lang):
    return f"Translate the dictionary glosses to {LANG_NAMES.get(lang)}. Return only a short translation of at most 12 words, no commentary."

def used_today(uid):
    from datetime import date
    u = db.q1("SELECT llm_day, llm_n FROM users WHERE id=?", (uid,)) or {}
    return u.get("llm_n", 0) if u.get("llm_day") == date.today().isoformat() else 0

def allow(uid):
    return used_today(uid) < settings()["daily_limit"]

def count(uid):
    from datetime import date
    d = date.today().isoformat()
    db.ex("UPDATE users SET llm_n=CASE WHEN llm_day=? THEN llm_n+1 ELSE 1 END, llm_day=? WHERE id=?", (d, d, uid))
