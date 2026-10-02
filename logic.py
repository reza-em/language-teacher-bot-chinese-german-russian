"""Users, chats, progress, content access, glosses. No Telegram calls here."""
import json, time, random, secrets, datetime
from zoneinfo import ZoneInfo
import config, db, data, srs, llm, langs

CUSTOM_BASE = 100000      # word ids >= this are owner-added custom words (table custom, kind='word')

# ---------------- time helpers ----------------
def tzinfo(name):
    try: return ZoneInfo(name or config.DEFAULT_TZ)
    except Exception: return ZoneInfo(config.DEFAULT_TZ)

def local_now(tz, ts=None):
    return datetime.datetime.fromtimestamp(db.now() if ts is None else ts, tzinfo(tz))

def local_day(tz, ts=None): return local_now(tz, ts).strftime("%Y-%m-%d")
def hhmm_ok(s):
    try:
        h, m = s.split(":"); return 0 <= int(h) <= 23 and 0 <= int(m) <= 59 and len(m) == 2
    except Exception: return False

# ---------------- users ----------------
def get_user(uid): return db.q1("SELECT * FROM users WHERE id=?", (uid,)) or {}

def touch_user(tg, private=False):
    """Create/update a user row from a Telegram `from` object. Returns (user, is_new)."""
    uid = tg["id"]; now = db.now(); u = db.q1("SELECT * FROM users WHERE id=?", (uid,))
    name = ((tg.get("first_name") or "") + " " + (tg.get("last_name") or "")).strip()[:80]
    if not u:
        lc = (tg.get("language_code") or "")[:5]
        ui = "de" if lc.startswith("de") else ("en" if lc.startswith("en") else "fa")
        db.ex("INSERT INTO users(id,username,name,language_code,ui,expl,first_seen,last_seen,is_admin,tz) VALUES(?,?,?,?,?,?,?,?,?,?)",
              (uid, tg.get("username"), name, lc, ui, ui, now, now, int(uid == db.meta_get("owner_id")), config.DEFAULT_TZ))
        return get_user(uid), True
    db.ex("UPDATE users SET username=?, name=?, last_seen=? WHERE id=?", (tg.get("username"), name, now, uid))
    if private: db.ex("UPDATE users SET can_dm=1 WHERE id=?", (uid,))
    if uid == db.meta_get("owner_id") and not u["is_admin"]: db.ex("UPDATE users SET is_admin=1 WHERE id=?", (uid,))
    return get_user(uid), False

def update_user(uid, **kw):
    if not kw: return
    db.ex("UPDATE users SET " + ",".join(f"{k}=?" for k in kw) + " WHERE id=?", (*kw.values(), uid))

def is_owner(uid): return uid == db.meta_get("owner_id")
def is_admin(uid): return bool(is_owner(uid) or (get_user(uid).get("is_admin")))
def is_banned(uid): return bool(get_user(uid).get("banned")) and not is_admin(uid)

def user_lang(uid):
    l = get_user(uid).get("ui"); return l if l in config.LANGS else config.DEFAULT_LANG
def expl_lang(uid):
    u = get_user(uid); l = u.get("expl")
    if l == "auto": return u.get("det") if u.get("det") in config.LANGS else user_lang(uid)
    return l if l in config.LANGS else user_lang(uid)

def set_await(uid, kind, data_=None):
    update_user(uid, awaiting=kind, await_data=json.dumps(data_, ensure_ascii=False) if data_ is not None else None)

def get_await(uid):
    u = get_user(uid); d = {}
    try: d = json.loads(u.get("await_data") or "{}")
    except Exception: pass
    return u.get("awaiting"), d

def methods_of(u):
    return [m for m in (u.get("methods") or "").split(",") if m]

ALL_METHODS = ["flashcards", "mnemonic", "radicals", "strokes", "dictation", "pinyin", "building", "shadowing", "cloze", "matching", "review", "mock", "reader"]

def toggle_method(uid, m):
    ms = methods_of(get_user(uid))
    ms = [x for x in ms if x != m] if m in ms else ms + [m]
    update_user(uid, methods=",".join(ms)); return ms

# ---------------- words (HSK + custom) ----------------
def get_word(wid):
    if wid >= langs.BASE["de"]: return langs.word(wid)
    if wid >= CUSTOM_BASE:
        r = db.q1("SELECT * FROM custom WHERE id=? AND kind='word' AND enabled=1", (wid - CUSTOM_BASE,))
        if not r: return None
        d = json.loads(r["data"])
        return {"i": wid, "hz": d["hz"], "py": d.get("py", ""), "lv": int(d.get("lv", 1)), "en": d.get("en", ""), "fa": d.get("fa", ""), "cc": [], "de": [d["de"]] if d.get("de") else [],
                "pos": [], "rad": "", "trad": d["hz"], "freq": 10**6, "custom": True}
    return data.word(wid)

def custom_words(level=None):
    out = []
    for r in db.q("SELECT id FROM custom WHERE kind='word' AND enabled=1"):
        w = get_word(CUSTOM_BASE + r["id"])
        if w and (level is None or w["lv"] <= level): out.append(w)
    return out

def pool(level, lang="zh"):
    if lang != "zh": return langs.pool(lang, level)
    return data.pool(level) + custom_words(max(level, 1) if level else 1)

# ---------------- learning languages (zh / de / ru) ----------------
def target(uid):
    t = get_user(uid).get("target") or "zh"; return t if t in langs.CODES else "zh"

def user_langs(uid):
    """Languages this learner studies (active one first)."""
    u = get_user(uid); cur = target(uid)
    ls = [l for l in (u.get("tlangs") or "zh").split(",") if l in langs.CODES]
    if cur not in ls: ls.append(cur)
    return [cur] + [l for l in ls if l != cur]

def set_target(uid, lang):
    """Switch the active language. users.level always holds the ACTIVE language's level; the others are parked in table ulang."""
    if lang not in langs.CODES: return False
    u = get_user(uid); cur = target(uid)
    if lang == cur and (u.get("tlangs") or "").find(lang) >= 0: return True
    db.ex("INSERT OR REPLACE INTO ulang(user_id,lang,level) VALUES(?,?,?)", (uid, cur, u["level"]))
    r = db.q1("SELECT level FROM ulang WHERE user_id=? AND lang=?", (uid, lang))
    ls = user_langs(uid)
    if lang not in ls: ls.append(lang)
    lv = r["level"] if r else (1 if lang == "zh" else 0)
    update_user(uid, target=lang, level=lv, tlangs=",".join([lang] + [l for l in ls if l != lang]))
    db.ex("DELETE FROM sess WHERE user_id=? AND chat_id=?", (uid, uid))
    return True

def level_of(uid, lang):
    if lang == target(uid): return get_user(uid)["level"]
    r = db.q1("SELECT level FROM ulang WHERE user_id=? AND lang=?", (uid, lang)); return r["level"] if r else 0

def gloss(w, lang):
    """Meaning of an HSK/custom word in `lang`; always honest about what exists. Returns (text, source) source in {curated, hande, cedict, llm, missing}."""
    if w.get("lang", "zh") != "zh":     # German / Russian: own curated English + Persian glosses (unreviewed); German explanations fall back to English
        return (w.get("fa") or w.get("en", "")) if lang == "fa" else w.get("en", ""), "curated"
    if lang == "fa":
        if w.get("fa"): return w["fa"], "curated"
        t = llm_gloss(w["hz"], w.get("en") or "; ".join(w.get("cc", [])[:2]), "fa")
        return (t, "llm") if t else (w.get("en", ""), "missing")
    if lang == "de":
        if w.get("de"): return "; ".join(w["de"][:3]), "hande"
        t = llm_gloss(w["hz"], w.get("en", ""), "de")
        return (t, "llm") if t else (w.get("en", ""), "missing")
    return (w.get("en") or "; ".join(w.get("cc", [])[:2])), "curated"

def llm_gloss(hz, en, lang):
    key = f"{hz}|{lang}"; r = db.q1("SELECT text FROM gloss_cache WHERE key=?", (key,))
    if r: return r["text"]
    if not llm.configured(): return None
    t = llm.chat(llm.gloss_system(lang), f"{hz}: {en}", max_tokens=60)
    if t:
        db.ex("INSERT OR REPLACE INTO gloss_cache(key,lang,text,ts) VALUES(?,?,?,?)", (key, lang, t[:200], db.now()))
    return t

def entry_gloss(e, lang):
    """Meanings for a CC-CEDICT entry dict (from data.lookup_*). -> (list[str], source)"""
    en = [d for d in e["defs"] if not d.startswith("CL:")][:5]
    if lang == "en": return en, "cedict"
    hw = data.by_hz(e["simp"])
    if lang == "fa":
        if hw and hw.get("fa") and hw["py"].replace(" ", "") .lower() == e["py"].replace(" ", "").lower(): return [hw["fa"]], "curated"
        t = llm_gloss(e["simp"], "; ".join(en[:3]), "fa")
        return ([t], "llm") if t else (en, "missing")
    de = data.german_for(e["simp"], e["py_num"]) if data.available() else []
    if de: return de[:4], "hande"
    t = llm_gloss(e["simp"], "; ".join(en[:3]), "de")
    return ([t], "llm") if t else (en, "missing")

# ---------------- progress ----------------
def add_activity(uid, tz=None):
    tz = tz or get_user(uid).get("tz")
    db.ex("INSERT OR IGNORE INTO activity(day,user_id) VALUES(?,?)", (local_day(tz), uid))

def record_answer(uid, correct, xp=None):
    """Update xp, ok/bad, streak (days in a row with at least one answer), daily counters."""
    u = get_user(uid); tz = u.get("tz"); day = local_day(tz)
    gain = xp if xp is not None else (10 if correct else 2)
    streak = u["streak"]
    if u["last_day"] != day:
        yday = (datetime.datetime.strptime(day, "%Y-%m-%d") - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        streak = streak + 1 if u["last_day"] == yday else 1
    best = max(u["best_streak"], streak)
    db.ex("UPDATE users SET xp=xp+?, ok=ok+?, bad=bad+?, streak=?, best_streak=?, last_day=? WHERE id=?",
          (gain, int(correct), int(not correct), streak, best, day, uid))
    db.ex("INSERT INTO daily(user_id,day,answers,ok) VALUES(?,?,1,?) ON CONFLICT(user_id,day) DO UPDATE SET answers=answers+1, ok=ok+?", (uid, day, int(correct), int(correct)))
    add_activity(uid, tz)
    return gain

def streak_alive(uid):
    u = get_user(uid); day = local_day(u.get("tz"))
    yday = (datetime.datetime.strptime(day, "%Y-%m-%d") - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    return u["streak"] if u["last_day"] in (day, yday) else 0

def today_stats(uid):
    u = get_user(uid); day = local_day(u.get("tz"))
    return db.q1("SELECT * FROM daily WHERE user_id=? AND day=?", (uid, day)) or {"new_words": 0, "answers": 0, "ok": 0}

def bump_new_word(uid):
    u = get_user(uid); day = local_day(u.get("tz"))
    db.ex("INSERT INTO daily(user_id,day,new_words) VALUES(?,?,1) ON CONFLICT(user_id,day) DO UPDATE SET new_words=new_words+1", (uid, day))

def add_mistake(uid, wid, etype, given, expected):
    db.ex("INSERT INTO mistakes(user_id,wid,etype,given,expected,ts) VALUES(?,?,?,?,?,?)", (uid, wid, etype, str(given)[:200], str(expected)[:200], db.now()))

def level_name_key(level): return f"lvl_{level}"

def new_word_target(u): return max(3, u["daily_goal"] // 2)

def next_new_words(uid, n=1):
    u = get_user(uid); have = {r["wid"] for r in db.q("SELECT wid FROM cards WHERE user_id=?", (uid,))}
    return [w for w in sorted(pool(u["level"], target(uid)), key=lambda w: (w["lv"], w["freq"])) if w["i"] not in have][:n]

def level_progress(uid, level):
    ws = [w for w in langs.words(target(uid)) if w["lv"] == level]
    have = {r["wid"] for r in db.q("SELECT wid FROM cards WHERE user_id=?", (uid,))}
    return sum(1 for w in ws if w["i"] in have), len(ws)

# ---------------- chats ----------------
def get_chat(cid): return db.q1("SELECT * FROM chats WHERE id=?", (cid,)) or {}

def register_chat(chat, added_by=None):
    c = db.q1("SELECT * FROM chats WHERE id=?", (chat["id"],))
    if c:
        db.ex("UPDATE chats SET title=?, username=?, type=?, active=1 WHERE id=?", (chat.get("title"), chat.get("username"), chat.get("type"), chat["id"]))
    else:
        db.ex("INSERT INTO chats(id,type,title,username,added_at,added_by,level) VALUES(?,?,?,?,?,?,1)", (chat["id"], chat.get("type"), chat.get("title"), chat.get("username"), db.now(), added_by))
    return get_chat(chat["id"])

def update_chat(cid, **kw):
    if kw: db.ex("UPDATE chats SET " + ",".join(f"{k}=?" for k in kw) + " WHERE id=?", (*kw.values(), cid))

def gscore_add(cid, uid, name, pts, win=False):
    db.ex("INSERT INTO gscores(chat_id,user_id,name,points,wins,answered) VALUES(?,?,?,?,?,1) ON CONFLICT(chat_id,user_id) DO UPDATE SET name=excluded.name, points=points+?, wins=wins+?, answered=answered+1",
          (cid, uid, name, pts, int(win), pts, int(win)))

def gtop(cid, n=10): return db.q("SELECT * FROM gscores WHERE chat_id=? ORDER BY points DESC, wins DESC LIMIT ?", (cid, n))

# ---------------- stats / export ----------------
def stats():
    now = db.now(); day = local_day(config.DEFAULT_TZ)
    d7 = [(datetime.datetime.strptime(day, "%Y-%m-%d") - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    return {
        "users": db.val("SELECT COUNT(*) FROM users", default=0),
        "new24": db.val("SELECT COUNT(*) FROM users WHERE first_seen>?", (now - 86400,), 0),
        "active_today": db.val("SELECT COUNT(DISTINCT user_id) FROM activity WHERE day=?", (day,), 0),
        "active7": db.val("SELECT COUNT(DISTINCT user_id) FROM activity WHERE day IN (%s)" % ",".join("?" * 7), tuple(d7), 0),
        "banned": db.val("SELECT COUNT(*) FROM users WHERE banned=1", default=0),
        "groups": db.val("SELECT COUNT(*) FROM chats WHERE active=1 AND type IN ('group','supergroup')", default=0),
        "groups_admin": db.val("SELECT COUNT(*) FROM chats WHERE active=1 AND bot_admin=1", default=0),
        "channels": db.val("SELECT COUNT(*) FROM channels WHERE enabled=1", default=0),
        "cards": db.val("SELECT COUNT(*) FROM cards", default=0),
        "answers": db.val("SELECT COALESCE(SUM(ok+bad),0) FROM users", default=0),
        "correct": db.val("SELECT COALESCE(SUM(ok),0) FROM users", default=0),
        "mistakes": db.val("SELECT COUNT(*) FROM mistakes", default=0),
        "llm_today": db.val("SELECT COALESCE(SUM(llm_n),0) FROM users WHERE llm_day=?", (datetime.date.today().isoformat(),), 0),
        "gquizzes": db.val("SELECT COUNT(*) FROM gquiz", default=0),
        "reminders": db.val("SELECT COUNT(*) FROM users WHERE remind!=''", default=0),
    }

def users_page(page, size=config.PAGE_SIZE, q=None):
    where, args = "", ()
    if q:
        like = f"%{q.lstrip('@')}%"; where = "WHERE name LIKE ? OR username LIKE ? OR CAST(id AS TEXT)=?"; args = (like, like, q)
    total = db.val(f"SELECT COUNT(*) FROM users {where}", args, 0); pages = max(1, (total + size - 1) // size); page = max(1, min(page, pages))
    return db.q(f"SELECT * FROM users {where} ORDER BY last_seen DESC LIMIT ? OFFSET ?", (*args, size, (page - 1) * size)), page, pages, total
