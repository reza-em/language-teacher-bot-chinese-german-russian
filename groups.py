"""Group behaviour: commands, mentions/replies, group quiz (first correct answer scores), per-group settings (admins only), my_chat_member."""
import json, re, time, logging, random
import config, db, logic, data, llm, fmt, tts, langs, uix
import exercises as X
import core as C
import ui
import teacher as T
from core import btn, kb, grid, esc, send, show, rtl, num
from texts import tr, LANG_LABEL

log = logging.getLogger("groups")
ADMIN_STATUSES = ("administrator", "creator")

def glang(ch): return ch.get("ui") if ch.get("ui") in config.LANGS else "fa"
def gexpl(ch): return ch.get("expl") if ch.get("expl") in config.LANGS else glang(ch)
def gout(chat_id, ch, text, markup=None, **kw): return send(chat_id, rtl(glang(ch), text), markup, **kw)

def is_group_admin(chat_id, uid):
    if logic.is_admin(uid): return True
    try:
        m = C.call("getChatMember", {"chat_id": chat_id, "user_id": uid})
        return m.get("status") in ADMIN_STATUSES
    except C.ApiError:
        return False

def open_private_markup(lang, chat_id):
    return kb([[btn(tr(lang, "g_btn_private"), url=C.deep_link("g%d" % abs(chat_id)))]])

# ---------------------------------------------------------------- my_chat_member
def on_my_chat_member(upd):
    chat = upd["chat"]; new = upd["new_chat_member"]; old = upd["old_chat_member"]; by = upd.get("from") or {}
    st_new, st_old = new.get("status"), old.get("status")
    if chat["type"] == "private":                       # the user started / blocked the bot
        if st_new in ("kicked", "left"): db.ex("UPDATE users SET can_dm=0 WHERE id=?", (chat["id"],))
        elif st_new == "member": db.ex("UPDATE users SET can_dm=1 WHERE id=?", (chat["id"],))
        return
    if chat["type"] == "channel":
        if st_new in ADMIN_STATUSES:
            can = int(bool(new.get("can_post_messages", st_new == "creator")))
            db.ex("INSERT INTO pending_channels(chat_id,title,username,ts,can_post) VALUES(?,?,?,?,?) ON CONFLICT(chat_id) DO UPDATE SET title=excluded.title, username=excluded.username, ts=excluded.ts, can_post=excluded.can_post",
                  (chat["id"], chat.get("title"), chat.get("username"), db.now(), can))
            owner = db.meta_get("owner_id")
            if db.val("SELECT can_dm FROM users WHERE id=?", (owner,), 0):
                send(owner, rtl(ui.ul(owner), tr(ui.ul(owner), "c_detected", title=esc(chat.get("title") or ""))))
        elif st_new in ("left", "kicked"):
            db.ex("DELETE FROM pending_channels WHERE chat_id=?", (chat["id"],))
            db.ex("UPDATE channels SET enabled=0 WHERE chat_id=?", (chat["id"],))
        return
    if chat["type"] not in ("group", "supergroup"): return
    cid = chat["id"]
    if st_new in ("left", "kicked"):
        logic.update_chat(cid, active=0, bot_admin=0); return
    rejoined = st_old in ("left", "kicked", None) and st_new in ("member", "administrator", "restricted")
    existed = bool(logic.get_chat(cid))
    ch = logic.register_chat(chat, by.get("id"))
    if rejoined or not existed: logic.update_chat(cid, intro_sent=0)
    if not existed: _guess_lang(logic.get_chat(cid), by)
    is_admin = st_new == "administrator"
    logic.update_chat(cid, bot_admin=int(is_admin), can_read_all=1 if is_admin else logic.get_chat(cid)["can_read_all"])
    announce(cid, thanks=is_admin)

def announce(cid, thanks=False):
    """Intro once per join; the admin-thanks message once when the bot is an admin."""
    ch = logic.get_chat(cid)
    if not ch: return
    cur = db.ex("UPDATE chats SET intro_sent=1 WHERE id=? AND intro_sent=0", (cid,))
    if cur.rowcount:
        if not send_intro(cid, ch):                       # could not post (no rights yet?): allow one retry later
            db.ex("UPDATE chats SET intro_sent=0 WHERE id=?", (cid,))
            log.warning("intro could not be posted in %s", cid)
    if thanks and not db.meta_get(f"thanks:{cid}"):
        db.meta_set(f"thanks:{cid}", 1)
        if not send_admin_thanks(cid, logic.get_chat(cid)): db.meta_set(f"thanks:{cid}", 0)

def ensure_chat(chat, frm=None, kind="message"):
    """Lazily register any group we see an update from; if it is new (or its intro never went out) post the intro once.
    Covers: bot added while it was down, missed my_chat_member, privacy-mode edge cases."""
    cid = chat["id"]; ch = logic.get_chat(cid)
    if ch and ch["active"] and ch["intro_sent"]: return ch
    if ch and ch["active"] and not C.rate_ok(("intro", cid), 1, 600): return ch       # failed intro: retry at most every 10 minutes
    new = not ch
    ch = logic.register_chat(chat, (frm or {}).get("id"))
    if new:
        log.info("lazily registered group %s (%s) from a %s update", cid, chat.get("type"), kind)
        _guess_lang(ch, frm or {})
    bot_admin = False
    try:
        m = C.call("getChatMember", {"chat_id": cid, "user_id": C.BOT_ID}); bot_admin = m.get("status") in ADMIN_STATUSES
    except C.ApiError as e:
        log.warning("getChatMember(bot) failed in %s: %s", cid, C.safe(e)[:80])
    logic.update_chat(cid, bot_admin=int(bot_admin), can_read_all=1 if bot_admin else logic.get_chat(cid)["can_read_all"])
    announce(cid, thanks=bot_admin)
    ch = logic.get_chat(cid)
    if not ch["intro_sent"]: C.rate_ok(("intro", cid), 1, 600)      # intro failed: start the retry back-off now
    return ch

def migrate_chat(old_id, new_id):
    """Group upgraded to a supergroup: carry settings, scores, prompts over to the new id (idempotent)."""
    if old_id == new_id: return
    log.info("chat migrated %s -> %s", old_id, new_id)
    old = logic.get_chat(old_id); new = logic.get_chat(new_id)
    if old and not new:
        db.ex("UPDATE chats SET id=?, type='supergroup' WHERE id=?", (new_id, old_id))
    elif old and new:
        keep = {k: old[k] for k in ("ui", "expl", "level", "daily", "daily_time", "tz", "enabled", "pin", "teacher", "intro_sent", "bot_admin", "can_read_all", "target")}
        logic.update_chat(new_id, active=1, **keep); db.ex("DELETE FROM chats WHERE id=?", (old_id,))
    for tbl in ("gscores", "gquiz", "gprompt"):
        db.ex(f"UPDATE OR IGNORE {tbl} SET chat_id=? WHERE chat_id=?", (new_id, old_id))
    db.ex("UPDATE OR IGNORE sess SET chat_id=? WHERE chat_id=?", (new_id, old_id))
    if db.meta_get(f"thanks:{old_id}"): db.meta_set(f"thanks:{new_id}", 1)

def _guess_lang(ch, by):
    lc = (by.get("language_code") or "")[:2]
    if ch.get("added_at") and lc in ("en", "de") and ch["ui"] == "fa" and ch["expl"] == "fa":
        logic.update_chat(ch["id"], ui=lc, expl=lc)

def send_intro(chat_id, ch):
    lang = glang(ch)
    text = tr(lang, "g_intro", name=esc(config.BOT_NAME_FA if lang == "fa" else config.BOT_NAME_EN if lang == "en" else config.BOT_NAME_DE), bot=C.BOT_USERNAME)
    text += "\n\n" + tr(lang, "g_teacher_intro" if tl(ch) == "zh" else "g_teacher_zh_only") + "\n\n" + tr(lang, "g_privacy_note")
    rows = [[btn(tr(lang, "g_btn_private"), url=C.deep_link("g%d" % abs(chat_id)))], [btn(tr(lang, "g_btn_settings"), "gs:menu")]]
    r = gout(chat_id, ch, text, kb(rows))
    if r: logic.update_chat(chat_id, intro_sent=1)
    return r

def send_admin_thanks(chat_id, ch):
    return gout(chat_id, ch, tr(glang(ch), "g_admin_thanks") + "\n\n" + tr(glang(ch), "g_teacher_intro" if tl(ch) == "zh" else "g_teacher_zh_only"))

# ---------------------------------------------------------------- message routing
def mention_re():
    # the username as a whole token: "@YourLanguageBot," matches, "@YourLanguageBotx" and "a@YourLanguageBot" do not; case-insensitive
    return re.compile(r"(?<![A-Za-z0-9_])@" + re.escape(C.BOT_USERNAME) + r"(?![A-Za-z0-9_])", re.I)

def mentions_bot(msg, text):
    if mention_re().search(text or ""): return True
    for e in (msg.get("entities") or []) + (msg.get("caption_entities") or []):
        if e.get("type") == "text_mention" and (e.get("user") or {}).get("id") == C.BOT_ID: return True
    return False

def addressed(msg, text):
    """Is the message addressed to the bot (command for us, @username anywhere in the text, or reply to our message)?"""
    t = text or ""
    if t.startswith("/"):
        cmd = t.split()[0]
        if "@" in cmd and cmd.split("@", 1)[1].lower() != C.BOT_USERNAME.lower(): return False
        return True
    if mentions_bot(msg, t): return True
    rt = msg.get("reply_to_message") or {}
    if (rt.get("from") or {}).get("id") == C.BOT_ID: return True
    return False

def strip_mention(text):
    t = mention_re().sub(" ", text or "")
    t = re.sub(r"[ \t]{2,}", " ", t).strip()
    return re.sub(r"^[\s,:;،\-–—]+", "", t).strip()

def reply_subject(msg):
    """Text of the message being replied to when it is a member's Chinese text (so '@bot' + reply to a sentence means 'please look at this')."""
    rt = msg.get("reply_to_message") or {}
    if not rt or (rt.get("from") or {}).get("id") == C.BOT_ID or (rt.get("from") or {}).get("is_bot"): return ""
    t = rt.get("text") or rt.get("caption") or ""
    return t[:400] if data.has_hanzi(t) else ""

def on_message(msg):
    chat = msg["chat"]; cid = chat["id"]; frm = msg.get("from") or {}; uid = frm.get("id")
    text = msg.get("text") or msg.get("caption") or ""
    if msg.get("migrate_to_chat_id"): return migrate_chat(cid, msg["migrate_to_chat_id"])
    if msg.get("migrate_from_chat_id"): return migrate_chat(msg["migrate_from_chat_id"], cid)
    if not uid or frm.get("is_bot"): return
    if msg.get("new_chat_members"):
        if any(m.get("id") == C.BOT_ID for m in msg["new_chat_members"]):
            ensure_chat(chat, frm, "new_chat_members")
        return
    if (msg.get("left_chat_member") or {}).get("id") == C.BOT_ID:
        logic.update_chat(cid, active=0, bot_admin=0); return
    is_addr = addressed(msg, text)
    ch = logic.get_chat(cid)
    if not ch or not ch["active"] or not ch["intro_sent"]: ch = ensure_chat(chat, frm, "message")
    if not is_addr and not ch.get("can_read_all"):
        logic.update_chat(cid, can_read_all=1)       # we received an unaddressed message -> privacy mode is off (or we are admin)
    logic.touch_user(frm)
    if logic.is_banned(uid): return
    ch = logic.get_chat(cid)
    # a reply to one of the teacher's mini-exercises
    if ch["enabled"] and T.mode_of(ch) != "off" and msg.get("reply_to_message") and T.handle_prompt_answer(msg, ch): return
    if not is_addr:
        if ch["enabled"] and T.mode_of(ch) == "always" and text:
            try: T.maybe_unsolicited(msg, ch, text)
            except Exception as e: log.exception("teacher (unsolicited) failed: %s", C.safe(e))
        return
    lang = glang(ch)
    if not ch["enabled"] and not (text.startswith("/settings") or text.startswith("/start")):
        if C.rate_ok(("dis", cid), 1, 300): gout(cid, ch, tr(lang, "g_disabled"))
        return
    if not C.rate_ok(("gu", cid, uid), config.GROUP_USER_CMDS_PER_MIN) or not C.rate_ok(("gc", cid), config.GROUP_CHAT_CMDS_PER_MIN):
        return
    body = strip_mention(text)
    cmd = ""; arg = ""
    if body.startswith("/"):
        sp = body.split(None, 1); cmd = sp[0][1:].split("@")[0].lower(); arg = strip_mention(sp[1]) if len(sp) > 1 else ""
    else:
        arg = body
    subject = ""
    if not cmd and not (arg and data.has_hanzi(arg)):
        subject = reply_subject(msg)
        if subject: arg = (arg + " " + subject).strip()
    mid = msg.get("message_id")
    if cmd in ("start", "help"):
        return send_intro(cid, ch)
    if cmd in ("quiz", "q"): return group_quiz_start(cid, ch, frm)
    if cmd in ("word", "today"): return group_word(cid, ch)
    if cmd in ("top", "leaderboard"): return group_top(cid, ch)
    if cmd in ("settings", "admin"): return group_settings(cid, ch, uid)
    if cmd in ("dict", "d"):
        if not arg: return gout(cid, ch, tr(lang, "g_need_arg"), reply_to_message_id=mid)
        return group_dict(cid, ch, arg, mid)
    if cmd in ("ask", "a"):
        if not arg: return gout(cid, ch, tr(lang, "g_need_arg"), reply_to_message_id=mid)
        return group_ask(cid, ch, uid, arg, mid)
    if cmd:  # other command
        return gout(cid, ch, tr(lang, "g_unknown"), reply_to_message_id=mid)
    # mention / reply without a command -> teacher conversation
    bare = not re.sub(r"[\W_]+", "", arg)           # only the username (maybe with punctuation)
    if T.mode_of(ch) == "off":
        if bare: return T.quickstart(msg, ch)
        if tl(ch) != "zh":
            if C.rate_ok(("toff", cid), 1, 60): gout(cid, ch, tr(lang, "g_teacher_zh_only"), reply_to_message_id=mid)
            return
        if C.rate_ok(("toff", cid), 1, 60): gout(cid, ch, tr(lang, "t_off_hint"), reply_to_message_id=mid)
        return
    try: T.respond(msg, ch, arg, True)
    except Exception as e:
        log.exception("teacher failed: %s", C.safe(e))
        gout(cid, ch, tr(lang, "unexpected"), reply_to_message_id=mid)

# ---------------------------------------------------------------- dict / ask / word
def group_dict(cid, ch, q, mid):
    lang = glang(ch)
    if tl(ch) != "zh":
        html = uix.dict_html(tl(ch), q[:60], lang, gexpl(ch))
        if html is None: return gout(cid, ch, tr(lang, "cx_dict_none", q=esc(q[:40])), reply_to_message_id=mid)
        ws = uix.search(tl(ch), q[:60]); rows = [btn(tr(lang, "b_hear"), f"hr:{ws[0]['i']}")] if ws else []
        return gout(cid, ch, html[:3800], kb([rows]) if rows else None, reply_to_message_id=mid)
    html, _, first = ui.dictionary_html(q, lang, gexpl(ch))
    if html is None:
        return gout(cid, ch, tr(lang, "dict_none", q=esc(q[:40])), reply_to_message_id=mid)
    rows = []
    if first and len(first.encode()) <= 40: rows.append(btn(tr(lang, "b_hear"), f"hz:{first}"))
    gout(cid, ch, html[:3800], kb([rows]) if rows else None, reply_to_message_id=mid)

def group_ask(cid, ch, uid, q, mid):
    lang = glang(ch)
    html = ui.ask_answer(q, lang, gexpl(ch), uid) if tl(ch) == "zh" else uix.ask_answer(uid, q, lang, gexpl(ch), L=tl(ch))
    gout(cid, ch, html[:3800] + "\n\n" + tr(lang, "g_ask_private"), open_private_markup(lang, cid), reply_to_message_id=mid)

def tl(ch): return ch.get("target") if ch.get("target") in langs.CODES else "zh"

def word_of_day(ch, day_key=None):
    lvl = max(1, ch["level"]); pool = logic.pool(lvl, tl(ch))
    r = random.Random(f"{ch['id']}-{day_key or logic.local_day(ch['tz'])}")
    return r.choice(pool)

def group_word(cid, ch, pin=False):
    lang = glang(ch); w = word_of_day(ch)
    text = tr(lang, "g_word_head") + "\n\n" + fmt.word_card(w, lang, gexpl(ch))
    rows = [[btn(tr(lang, "b_hear"), f"hr:{w['i']}")], [btn(tr(lang, "g_btn_private"), url=C.deep_link("g%d" % abs(cid)))]]
    r = gout(cid, ch, text, kb(rows))
    if pin and ch.get("pin") and ch.get("bot_admin") and r:
        try: C.call("pinChatMessage", {"chat_id": cid, "message_id": r["message_id"], "disable_notification": True})
        except C.ApiError: pass
    return r

def group_top(cid, ch):
    lang = glang(ch); rows = logic.gtop(cid, 10)
    if not rows: return gout(cid, ch, tr(lang, "g_top_empty"))
    medals = ["🥇", "🥈", "🥉"]
    lines = [tr(lang, "g_top_line", rank=medals[i] if i < 3 else num(lang, i + 1) , name=esc(r["name"] or "?"), pts=num(lang, r["points"]), wins=num(lang, r["wins"])) for i, r in enumerate(rows)]
    gout(cid, ch, tr(lang, "g_top", lines="\n".join(lines)))

# ---------------------------------------------------------------- group quiz
def open_quiz(cid):
    return db.q1("SELECT * FROM gquiz WHERE chat_id=? AND state='open' ORDER BY id DESC LIMIT 1", (cid,))

def group_quiz_start(cid, ch, frm):
    lang = glang(ch); uid = frm["id"]; now = db.now()
    oq = open_quiz(cid)
    if oq and now - oq["created"] < config.GROUP_QUIZ_TIMEOUT:
        return gout(cid, ch, tr(lang, "g_quiz_open"), reply_to_message_id=oq["msg_id"])
    if oq: close_quiz(oq, ch, timeout=True)
    if now - (ch.get("last_cmd") or 0) < config.GROUP_QUIZ_COOLDOWN and not is_group_admin(cid, uid):
        return gout(cid, ch, tr(lang, "g_quiz_cool"))
    types = [t for t in ("zh2m", "m2zh", "recog", "tone", "cloze", "radical") if t != "radical" or data.available()] if tl(ch) == "zh" else ["zh2m", "m2zh", "cloze", "listen", "m2zh"]
    ex = None
    for _ in range(5):
        try:
            ex = X.make_exercise(None, random.choice(types), profile={"level": max(1, ch["level"]), "lang": gexpl(ch), "types": types, "target": tl(ch)}); break
        except Exception as e:
            log.warning("group quiz build failed: %s", type(e).__name__)
    if not ex or "opts" not in ex: return gout(cid, ch, tr(lang, "unexpected"))
    if ex.get("audio") and ex["t"] in ("recog", "tone"):
        pass
    qid = db.ex("INSERT INTO gquiz(chat_id,msg_id,data,state,created) VALUES(?,?,?,?,?)", (cid, 0, json.dumps({"ex": ex, "answered": []}, ensure_ascii=False), "open", now)).lastrowid
    rows = grid([btn(str(o), f"gq:{qid}:{i}") for i, o in enumerate(ex["opts"])], ex.get("row") or (2 if max(len(str(o)) for o in ex["opts"]) > 4 else 4))
    text = tr(lang, "g_quiz_head") + "\n\n" + ex["text"]
    r = gout(cid, ch, text, kb(rows))
    if r: db.ex("UPDATE gquiz SET msg_id=? WHERE id=?", (r["message_id"], qid))
    logic.update_chat(cid, last_cmd=now)
    if ex.get("audio") and ex["t"] in (("recog",) if tl(ch) == "zh" else ("listen",)): ui.send_audio_quiet(cid, ex["audio"])

def close_quiz(q, ch, timeout=False, winner=None):
    db.ex("UPDATE gquiz SET state=?, winner=? WHERE id=?", ("timeout" if timeout else "done", winner, q["id"]))
    if timeout:
        d = json.loads(q["data"]); ex = d["ex"]; lang = glang(ch)
        w = logic.get_word(ex["wid"]) if ex.get("wid") is not None else None
        expl = X.word_line(w, gexpl(ch)) if w else ""
        gout(q["chat_id"], ch, tr(lang, "g_quiz_timeout", ans=esc(X.explain_ans(ex)), expl=expl), reply_to_message_id=q["msg_id"])
        try: C.call("editMessageReplyMarkup", {"chat_id": q["chat_id"], "message_id": q["msg_id"], "reply_markup": json.dumps({"inline_keyboard": []})})
        except C.ApiError: pass

def on_quiz_cb(cb, p):
    msg = cb["message"]; cid = msg["chat"]["id"]; frm = cb["from"]; uid = frm["id"]
    ch = logic.get_chat(cid) or {}; lang = glang(ch) if ch else "fa"
    qid, idx = int(p[1]), int(p[2])
    q = db.q1("SELECT * FROM gquiz WHERE id=? AND chat_id=?", (qid, cid))
    if not q or q["state"] != "open": return C.answer_cb(cb["id"], tr(lang, "g_quiz_closed"))
    logic.touch_user(frm)
    # atomic: one try per user, first correct wins
    with db.tx():
        q = db.q1("SELECT * FROM gquiz WHERE id=?", (qid,))
        if q["state"] != "open": return C.answer_cb(cb["id"], tr(lang, "g_quiz_closed"))
        d = json.loads(q["data"])
        if uid in d["answered"]: return C.answer_cb(cb["id"], tr(lang, "g_quiz_done"))
        d["answered"].append(uid); ex = d["ex"]; ok = idx == ex["ans"]
        name = ((frm.get("first_name") or "") + " " + (frm.get("last_name") or "")).strip() or frm.get("username") or str(uid)
        if ok:
            db.ex("UPDATE gquiz SET state='done', winner=?, data=? WHERE id=?", (uid, json.dumps(d, ensure_ascii=False), qid))
            logic.gscore_add(cid, uid, name[:40], 10, win=True)
        else:
            db.ex("UPDATE gquiz SET data=? WHERE id=?", (json.dumps(d, ensure_ascii=False), qid))
            logic.gscore_add(cid, uid, name[:40], 0)
    if not ok: return C.answer_cb(cb["id"], tr(lang, "g_quiz_wrong"))
    C.answer_cb(cb["id"], "🏆")
    w = logic.get_word(ex["wid"]) if ex.get("wid") is not None else None
    expl = X.word_line(w, gexpl(ch)) if w else ""
    rows = [[btn(tr(lang, "b_hear"), f"hr:{w['i']}")]] if w else []
    rows.append([btn(tr(lang, "g_btn_next"), "gq:next"), btn(tr(lang, "g_btn_top"), "gq:top")])
    try: C.call("editMessageReplyMarkup", {"chat_id": cid, "message_id": msg["message_id"], "reply_markup": json.dumps({"inline_keyboard": []})})
    except C.ApiError: pass
    gout(cid, ch, tr(lang, "g_quiz_win", name=esc(name), pts=num(lang, 10), ans=esc(X.explain_ans(ex)), expl=expl), kb(rows), reply_to_message_id=msg["message_id"])

def expire_quizzes():
    cutoff = db.now() - config.GROUP_QUIZ_TIMEOUT
    for q in db.q("SELECT * FROM gquiz WHERE state='open' AND created<?", (cutoff,)):
        ch = logic.get_chat(q["chat_id"]) or {}
        try: close_quiz(q, ch, timeout=True)
        except Exception as e: log.warning("expire quiz: %s", type(e).__name__)

# ---------------------------------------------------------------- settings (group admins only)
def group_settings(cid, ch, uid, mid=None):
    lang = glang(ch)
    if not is_group_admin(cid, uid): return gout(cid, ch, tr(lang, "g_only_admin"))
    text, markup = settings_panel(ch)
    if mid: show(cid, mid, rtl(lang, text), markup)
    else: gout(cid, ch, text, markup)

def settings_panel(ch):
    lang = glang(ch)
    onoff = lambda v: tr(lang, "a_on") if v else tr(lang, "a_off")
    lvl_t = tr(lang, f"lvl_{max(1, ch['level'])}") if tl(ch) == "zh" else langs.level_name(tl(ch), min(2, max(1, ch["level"])))
    text = tr(lang, "g_settings", ui=LANG_LABEL[ch["ui"]], expl=LANG_LABEL[ch["expl"]], level=esc(lvl_t),
              daily=onoff(ch["daily"]), time=ch["daily_time"] if ch["daily"] else "", enabled=onoff(ch["enabled"]))
    text += "\n" + tr(lang, "g_target", tl=esc(langs.label(tl(ch), lang)))
    text += "\n" + tr(lang, "g_teacher_line", mode=tr(lang, "g_tm_" + T.mode_of(ch)))
    rows = [[btn(tr(lang, "g_b_ui"), "gs:ui"), btn(tr(lang, "g_b_expl"), "gs:ex"), btn(tr(lang, "g_b_level"), "gs:lv")],
            [btn(tr(lang, "b_g_target") + ": " + langs.flag(tl(ch)), "gs:tg")],
            [btn(tr(lang, "g_b_daily") + (" ✅" if ch["daily"] else " ⬜"), "gs:daily"), btn(tr(lang, "g_b_time"), "gs:time")],
            [btn(tr(lang, "g_b_teacher") + ": " + tr(lang, "g_tm_" + T.mode_of(ch)), "gs:tm")] if tl(ch) == "zh" else [],
            [btn(tr(lang, "g_b_pin") + (" ✅" if ch["pin"] else " ⬜"), "gs:pin"), btn(tr(lang, "g_b_enabled") + (" ✅" if ch["enabled"] else " ⬜"), "gs:en")],
            [btn(tr(lang, "g_btn_private"), url=C.deep_link("g%d" % abs(ch["id"])))]]
    return text, kb([r for r in rows if r])

def on_settings_cb(cb, p):
    msg = cb["message"]; cid = msg["chat"]["id"]; uid = cb["from"]["id"]; mid = msg["message_id"]
    ch = logic.get_chat(cid)
    if not ch: return C.answer_cb(cb["id"])
    lang = glang(ch)
    if not is_group_admin(cid, uid): return C.answer_cb(cb["id"], tr(lang, "g_only_admin"), True)
    op = p[1]; val = p[2] if len(p) > 2 else None
    if op == "ui" and val: logic.update_chat(cid, ui=val)
    elif op == "ui": return _pick(cb, ch, "gs:ui:", config.LANGS, lambda v: LANG_LABEL[v])
    elif op == "ex" and val: logic.update_chat(cid, expl=val)
    elif op == "ex": return _pick(cb, ch, "gs:ex:", config.LANGS, lambda v: LANG_LABEL[v])
    elif op == "lv" and val: logic.update_chat(cid, level=int(val))
    elif op == "lv": return _pick(cb, ch, "gs:lv:", ("1", "2", "3") if tl(ch) == "zh" else ("1", "2"), (lambda v: "HSK " + v) if tl(ch) == "zh" else (lambda v: langs.level_name(tl(ch), int(v))))
    elif op == "tg" and val in langs.CODES: logic.update_chat(cid, target=val, level=min(ch["level"], 3 if val == "zh" else 2))
    elif op == "tg": return _pick(cb, ch, "gs:tg:", langs.CODES, lambda v: langs.label(v, lang))
    elif op == "daily": logic.update_chat(cid, daily=0 if ch["daily"] else 1, last_daily=logic.local_day(ch["tz"]) if not ch["daily"] else ch["last_daily"])
    elif op == "tm":
        modes = config.TEACHER_MODES; logic.update_chat(cid, teacher=modes[(modes.index(T.mode_of(ch)) + 1) % len(modes)])
    elif op == "pin": logic.update_chat(cid, pin=0 if ch["pin"] else 1)
    elif op == "en": logic.update_chat(cid, enabled=0 if ch["enabled"] else 1)
    elif op == "time":
        db.ex("INSERT INTO sess(user_id,chat_id,data,updated) VALUES(?,?,?,?) ON CONFLICT(user_id,chat_id) DO UPDATE SET data=excluded.data, updated=excluded.updated",
              (uid, cid, json.dumps({"mode": "gtime", "mid": mid}), db.now()))
        C.answer_cb(cb["id"]); return gout(cid, ch, tr(lang, "g_time_ask"), json.dumps({"force_reply": True, "selective": True}), reply_to_message_id=mid)
    C.answer_cb(cb["id"])
    ch = logic.get_chat(cid); text, markup = settings_panel(ch); show(cid, mid, rtl(glang(ch), text), markup)

def _pick(cb, ch, prefix, options, label):
    lang = glang(ch); cid = ch["id"]
    rows = [[btn(label(v), prefix + v) for v in options], [btn(tr(lang, "b_back"), "gs:menu")]]
    C.answer_cb(cb["id"]); show(cid, cb["message"]["message_id"], rtl(lang, tr(lang, "g_pick")), kb(rows))

def on_settings_menu(cb):
    cid = cb["message"]["chat"]["id"]; ch = logic.get_chat(cid); uid = cb["from"]["id"]
    if not ch: return C.answer_cb(cb["id"])
    if not is_group_admin(cid, uid): return C.answer_cb(cb["id"], tr(glang(ch), "g_only_admin"), True)
    C.answer_cb(cb["id"]); text, markup = settings_panel(ch); show(cid, cb["message"]["message_id"], rtl(glang(ch), text), markup)

def on_time_reply(msg):
    """Reply to the 'send time' prompt; only group admins."""
    cid = msg["chat"]["id"]; uid = msg["from"]["id"]
    r = db.q1("SELECT data FROM sess WHERE user_id=? AND chat_id=?", (uid, cid))
    if not r: return False
    d = json.loads(r["data"])
    if d.get("mode") != "gtime": return False
    ch = logic.get_chat(cid); lang = glang(ch)
    t = C.norm_digits(msg.get("text") or "").strip()
    if re.fullmatch(r"\d:\d\d", t): t = "0" + t
    if not is_group_admin(cid, uid): return True
    if not logic.hhmm_ok(t): gout(cid, ch, tr(lang, "bad_time")); return True
    logic.update_chat(cid, daily_time=t, daily=1); db.ex("DELETE FROM sess WHERE user_id=? AND chat_id=?", (uid, cid))
    ch = logic.get_chat(cid); gout(cid, ch, tr(lang, "g_time_set", t=t))
    return True
