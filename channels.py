"""Channel kit: ready-made post templates, rotation of content types, scheduler slots, pinned intro, quiz polls."""
import json, re, time, random, logging
import config, db, logic, data, fmt
import core as C
import content.alphabet as A
import content.lessons as L
from core import btn, kb, esc, send, rtl
from texts import tr

log = logging.getLogger("channels")
TYPES = ["word", "char", "tone", "quiz", "grammar", "idiom", "culture"]
DEFAULT_TYPES = ["word", "tone", "char", "quiz", "grammar", "idiom", "culture"]
LI = {"fa": 0, "en": 1, "de": 2}

def get(chat_id): return db.q1("SELECT * FROM channels WHERE chat_id=?", (chat_id,))
def all_channels(): return db.q("SELECT * FROM channels ORDER BY id")
def times_of(c):
    try: return [t for t in json.loads(c["times"]) if logic.hhmm_ok(t)]
    except Exception: return list(config.DEFAULT_CHANNEL_TIMES)
def types_of(c):
    try: return [t for t in json.loads(c["types"]) if t in TYPES] or list(DEFAULT_TYPES)
    except Exception: return list(DEFAULT_TYPES)

def slot_now(c, ts=None):
    """-> (slot_string, minutes_late) for the latest configured time that has passed today, or (None, None)."""
    now = logic.local_now(c["tz"], ts); best = None
    for t in sorted(times_of(c)):
        h, m = map(int, t.split(":"))
        if (h, m) <= (now.hour, now.minute): best = (t, now.hour * 60 + now.minute - (h * 60 + m))
    if not best: return None, None
    return now.strftime("%Y-%m-%d") + " " + best[0], best[1]

def register(chat_id, title, username):
    times = json.dumps(config.DEFAULT_CHANNEL_TIMES); types = json.dumps(DEFAULT_TYPES)
    ex = get(chat_id)
    if ex:
        db.ex("UPDATE channels SET title=?, username=?, enabled=1 WHERE chat_id=?", (title, username, chat_id)); return get(chat_id)
    c = {"chat_id": chat_id, "tz": config.DEFAULT_TZ}
    db.ex("INSERT INTO channels(chat_id,title,username,times,types,tz,added_at,last_slot) VALUES(?,?,?,?,?,?,?,?)", (chat_id, title, username, times, types, config.DEFAULT_TZ, db.now(), ""))
    c = get(chat_id)
    s, _ = slot_now(c)      # do not back-post slots that already passed today
    db.ex("UPDATE channels SET last_slot=? WHERE chat_id=?", (s or "", chat_id))
    db.ex("DELETE FROM pending_channels WHERE chat_id=?", (chat_id,))
    return get(chat_id)

# ---------------------------------------------------------------- post builders (return dict: text | poll)
def _pyline(zh):
    from pypinyin import pinyin, Style
    return " ".join(x[0] for x in pinyin(zh, style=Style.TONE))

def build_post(c, kind=None):
    lang = c["lang"] if c["lang"] in config.LANGS else "fa"; n = c["counter"]
    types = types_of(c); kind = kind or types[n % len(types)]
    k = n // max(1, len(types))    # index within this type
    words = data.words()
    if kind == "word":
        w = words[(k * 13 + c["id"] * 7) % len(words)]; ss = data.sentences(w["hz"])
        ex = ""
        if ss:
            s = ss[0]; ex = f"\n\n📝 {esc(s['zh'])}\n<i>{esc(_pyline(s['zh']))}</i>\n{esc(s['en'])}"
        de = "; ".join(w["de"][:2]) if w.get("de") else (w.get("en") or "")
        return {"kind": kind, "text": tr(lang, "c_post_word", lv=w["lv"], hz=f"<b>{esc(w['hz'])}</b>", py=esc(w["py"]), fa=esc(w["fa"]), en=esc(w["en"]), de=esc(de), ex=ex), "wid": w["i"], "audio": w["hz"]}
    if kind == "char":
        cand = [w for w in words if len(w["hz"]) == 1] or words
        w = cand[(k * 7 + c["id"]) % len(cand)]
        ch = w["hz"][0]; cnt = data.stroke_count(ch) if data.available() else 0
        ci = data.char_info(ch) if data.available() else None
        mean = {"fa": w["fa"], "en": w["en"], "de": "; ".join(w["de"][:2]) if w.get("de") else w["en"]}[lang]
        txt = tr(lang, "c_post_char", ch=ch, py=esc(w["py"]), mean=esc(mean), n=cnt or "?", rad=esc((ci or {}).get("radical", w.get("rad", "")) or "—"))
        png = None
        try:
            import strokes_img; png = strokes_img.stroke_order_png(ch) if cnt else None
        except Exception as e: log.warning("stroke img: %s", type(e).__name__)
        return {"kind": kind, "text": txt, "photo": png, "wid": w["i"]}
    if kind == "tone":
        t = A.TONE_TIPS[k % len(A.TONE_TIPS)][LI[lang]]
        return {"kind": kind, "text": tr(lang, "c_post_tone", t=esc(t))}
    if kind == "grammar":
        g = L.GRAMMAR[k % len(L.GRAMMAR)]
        return {"kind": kind, "text": tr(lang, "c_post_grammar", title=esc(g[5][LI[lang]]), pattern=esc(g[2]), body=esc(g[6][LI[lang]]), zh=esc(g[3]), py=esc(g[4]), tr=esc(g[7][LI[lang]]))}
    if kind == "idiom":
        i = L.CHENGYU[k % len(L.CHENGYU)]
        return {"kind": kind, "text": tr(lang, "c_post_idiom", zh=f"<b>{esc(i[0])}</b>", py=esc(i[1]), mean=esc(i[2][LI[lang]]), lit=esc(i[3])), "audio": i[0]}
    if kind == "culture":
        cu = L.CULTURE[k % len(L.CULTURE)]
        return {"kind": kind, "text": tr(lang, "c_post_culture", title=esc(cu[0][LI[lang]]), body=esc(cu[1][LI[lang]]))}
    if kind == "quiz":
        import exercises as X
        lv = 1 + (k % 3); w = random.Random(f"{c['id']}-{k}").choice([x for x in words if x["lv"] == lv])
        pool = [x for x in words if x["lv"] <= lv]
        ex = X.mk_zh2m(w, pool, lang)
        q = tr(lang, "c_quiz_q", lv=lv, hz=w["hz"]) + f"\n{w['py']}"
        return {"kind": kind, "poll": {"question": re.sub(r"<[^>]+>", "", q)[:300], "options": [str(o)[:100] for o in ex["opts"]], "correct": ex["ans"],
                "explanation": re.sub(r"<[^>]+>", "", tr(lang, "c_quiz_expl", hz=w["hz"], py=w["py"], mean=X.meaning(w, lang)[0]))[:200]}, "wid": w["i"]}
    raise ValueError(kind)

def post_markup(c):
    if not c["btn"] or not C.BOT_USERNAME: return None
    lang = c["lang"] if c["lang"] in config.LANGS else "fa"
    return kb([[btn(tr(lang, "c_btn_label"), url=C.deep_link("ch"))]])

def post(c, kind=None):
    """Publish one post. -> (ok, err_or_message_id). Never raises."""
    try: p = build_post(c, kind)
    except Exception as e:
        log.warning("build_post failed: %s", type(e).__name__); return False, "build"
    chat = c["chat_id"]; markup = post_markup(c)
    try:
        if p.get("poll"):
            d = {"chat_id": chat, "question": p["poll"]["question"], "options": json.dumps(p["poll"]["options"], ensure_ascii=False), "type": "quiz", "correct_option_id": p["poll"]["correct"],
                 "is_anonymous": True, "explanation": p["poll"]["explanation"]}
            if markup: d["reply_markup"] = markup
            r = C.call("sendPoll", d)
        elif p.get("photo"):
            d = {"chat_id": chat, "caption": rtl(c["lang"], p["text"])[:1024], "parse_mode": "HTML"}
            if markup: d["reply_markup"] = markup
            r = C.call("sendPhoto", d, files={"photo": ("strokes.png", p["photo"], "image/png")}, timeout=90)
        else:
            d = {"chat_id": chat, "text": rtl(c["lang"], p["text"])[:4096], "parse_mode": "HTML", "disable_web_page_preview": True}
            if markup: d["reply_markup"] = markup
            r = C.call("sendMessage", d)
    except C.ApiError as e:
        log.warning("channel post failed (%s): %s", chat, C.safe(e)[:80]); return False, str(e)[:100]
    db.ex("UPDATE channels SET counter=counter+1 WHERE chat_id=?", (chat,))
    # a short voice clip for word/idiom posts (best effort)
    if p.get("audio") and c.get("btn") is not None:
        try:
            import tts
            b, kind_ = tts.audio_bytes(p["audio"])
            if b and kind_ == "voice": C.send_voice(chat, b)
        except Exception as e: log.warning("channel audio: %s", type(e).__name__)
    return True, r.get("message_id")

def post_intro(c, pin=True):
    lang = c["lang"] if c["lang"] in config.LANGS else "fa"
    text = tr(lang, "c_intro", name=esc(config.BOT_NAME_FA if lang == "fa" else config.BOT_NAME_EN if lang == "en" else config.BOT_NAME_DE), bot=C.BOT_USERNAME)
    try:
        r = C.call("sendMessage", {"chat_id": c["chat_id"], "text": rtl(lang, text), "parse_mode": "HTML", "disable_web_page_preview": True, "reply_markup": post_markup(c) or ""} if post_markup(c) else
                   {"chat_id": c["chat_id"], "text": rtl(lang, text), "parse_mode": "HTML", "disable_web_page_preview": True})
    except C.ApiError as e: return False, str(e)[:100]
    db.ex("UPDATE channels SET pinned_msg=? WHERE chat_id=?", (r["message_id"], c["chat_id"]))
    if pin:
        try: C.call("pinChatMessage", {"chat_id": c["chat_id"], "message_id": r["message_id"], "disable_notification": True})
        except C.ApiError as e: return True, "pin_failed"
    return True, "ok"

# ---------------------------------------------------------------- scheduler tick
LATE_MINUTES = 90
def tick(ts=None):
    """Called every ~30 s. Posts at most one slot per channel; skips slots missed by more than LATE_MINUTES (bot was down)."""
    posted = 0
    for c in all_channels():
        if not c["enabled"]: continue
        slot, late = slot_now(c, ts)
        if not slot or slot <= (c["last_slot"] or ""): continue
        db.ex("UPDATE channels SET last_slot=? WHERE chat_id=?", (slot, c["chat_id"]))
        if late > LATE_MINUTES: continue
        ok, _ = post(get(c["chat_id"]))
        posted += int(ok)
    return posted
