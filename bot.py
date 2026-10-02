#!/usr/bin/env python3
"""Language Teacher bot (معلم زبان; Chinese, German, Russian) — long polling, single instance."""
import os, sys, json, time, logging, fcntl, threading, re
import config, db, logic, data, llm
import core as C
import course, ui, uix, groups as G, admin, sched, channels as CH, textnorm
from core import call, send, ApiError, btn, kb, esc, rtl
from texts import tr

log = logging.getLogger("bot")

# ---------------------------------------------------------------- private
def private_message(msg):
    frm = msg["from"]; uid = frm["id"]; text = (msg.get("text") or "").strip()
    u, new = logic.touch_user(frm, private=True)
    if logic.is_banned(uid): return send(uid, tr(logic.user_lang(uid), "banned_msg"))
    if not C.rate_ok(("p", uid), config.PRIVATE_MSGS_PER_MIN):
        if C.rate_ok(("pn", uid), 1, 30): send(uid, tr(logic.user_lang(uid), "rate_msg"))
        return
    lang = logic.user_lang(uid)
    if msg.get("voice") or msg.get("audio"):
        if not u.get("onboarded"): return ui.start(uid)
        return ui.on_voice(uid, msg)
    if not text: return
    if text.startswith("/"):
        cmd = text.split()[0][1:].split("@")[0].lower(); arg = text.split(None, 1)[1].strip() if len(text.split(None, 1)) > 1 else ""
        return private_command(uid, cmd, arg, new)
    u = logic.get_user(uid)
    if not u.get("onboarded"): return ui.start(uid)
    aw, d = logic.get_await(uid)
    if aw and aw.startswith("a_") and admin.on_text(uid, text): return
    if aw == "ans" and ui.on_text_answer(uid, text): return
    if aw == "remind": return ui.on_remind_text(uid, text)
    if aw == "dict": logic.set_await(uid, None); return ui.do_dict(uid, text)
    if aw == "ask": logic.set_await(uid, None); return ui.do_ask(uid, text)
    # free text -> auto-detect language, then dictionary or question
    if u["expl"] == "auto":
        det = textnorm.detect_lang(text)
        if det in config.LANGS: logic.update_user(uid, det=det)
    if ui.looks_like_question(text): return ui.do_ask(uid, text)
    ui.do_dict(uid, text)

def private_command(uid, cmd, arg, new=False):
    lang = logic.user_lang(uid)
    if cmd == "start":
        return ui.start(uid, payload=arg)
    if not logic.get_user(uid).get("onboarded"): return ui.start(uid)
    if cmd in ("cancel", "menu"):
        ui.clear_sess(uid); logic.set_await(uid, None); return send(uid, tr(lang, "cancelled"), ui.main_menu(lang, uid))
    if cmd == "help": return send(uid, rtl(lang, tr(lang, "help")), kb([ui.menu_row(lang)]))
    if cmd == "today": return ui.today(uid)
    if cmd in ("learn", "word"): return ui.show_new_word(uid)
    if cmd == "quiz": return ui.quiz_menu(uid) if not arg else ui.start_quiz(uid, "mix")
    if cmd == "review": return ui.review_start(uid)
    if cmd == "dict":
        return ui.do_dict(uid, arg) if arg else ui.dict_prompt(uid)
    if cmd == "ask":
        return ui.do_ask(uid, arg) if arg else ui.ask_prompt(uid)
    if cmd in ("lang", "language", "languages"): return uix.lang_menu(uid)
    if cmd == "course": return course.hub(uid)
    if cmd in ("placement", "level"): return course.start_placement(uid)
    if cmd == "alphabet": return ui.alpha_menu(uid)
    if cmd == "read": return ui.reader_list(uid)
    if cmd == "progress": return ui.progress(uid)
    if cmd == "settings": return ui.settings(uid)
    if cmd == "stroke":
        ch = next((c for c in arg if data.is_hanzi(c)), None)
        return ui.send_strokes(uid, ch, lang) if ch else send(uid, rtl(lang, tr(lang, "stroke_usage")))
    if cmd == "top": return send(uid, rtl(lang, tr(lang, "top_private")))
    if cmd == "admin":
        if not logic.is_admin(uid): return send(uid, tr(lang, "not_admin"))
        return admin.panel(uid)
    send(uid, rtl(lang, tr(lang, "unknown_cmd")), ui.main_menu(lang, uid))

def private_callback(cb):
    msg = cb["message"]; uid = cb["from"]["id"]; mid = msg["message_id"]; d = cb.get("data") or ""; p = d.split(":")
    logic.touch_user(cb["from"], private=True)
    if logic.is_banned(uid): return C.answer_cb(cb["id"])
    C.answer_cb(cb["id"])
    if not C.rate_ok(("pc", uid), config.PRIVATE_MSGS_PER_MIN * 2): return
    if not logic.get_user(uid).get("onboarded") and p[0] != "ob": return ui.start(uid)
    k = p[0]
    if k == "ob": return ui.onboarding_cb(uid, mid, p)
    if k == "m":
        return {"menu": lambda: ui.show_menu(uid, mid), "today": lambda: ui.today(uid, mid), "learn": lambda: ui.show_new_word(uid, mid), "quiz": lambda: ui.quiz_menu(uid, mid),
                "review": lambda: ui.review_start(uid, mid), "dict": lambda: ui.dict_prompt(uid, mid), "ask": lambda: ui.ask_prompt(uid, mid), "alpha": lambda: ui.alpha_menu(uid, mid),
                "read": lambda: ui.reader_list(uid, mid), "progress": lambda: ui.progress(uid, mid), "settings": lambda: ui.settings(uid, mid),
                "course": lambda: course.hub(uid, mid), "lang": lambda: uix.lang_menu(uid, mid),
                "help": lambda: ui.edit(uid, mid, tr(logic.user_lang(uid), "help"), kb([ui.menu_row(logic.user_lang(uid))]))}[p[1]]()
    if k == "c": return course.callback(uid, mid, p)
    if k == "lg": return uix.lang_cb(uid, mid, p)
    if k == "ln": return ui.show_new_word(uid, None, advance=True)
    if k in ("hr", "sk", "pt", "sy", "mx"): return ui.word_action(uid, k, int(p[1]), mid)
    if k == "hz": return ui.send_word_audio(uid, ":".join(p[1:]), logic.user_lang(uid))
    if k == "sc": return [ui.send_strokes(uid, c, logic.user_lang(uid)) for c in ":".join(p[1:])[:3] if data.is_hanzi(c)] and None
    if k == "pc": return [ui.out(uid, ui.fmt.parts_text(c, logic.user_lang(uid), ui.el(uid))) for c in ":".join(p[1:])[:3] if data.is_hanzi(c)] and None
    if k == "rv":
        if p[1] == "show": return ui.review_card(uid, mid, reveal=True)
        if p[1] == "stop": ui.clear_sess(uid); return ui.show_menu(uid, mid)
        if p[1] in ("y", "n"): return ui.review_answer(uid, mid, p[1] == "y")
        if p[1].startswith("q"): q = int(p[1][1:]); return ui.review_answer(uid, mid, q >= 3, q)
    if k == "qz": return ui.start_quiz(uid, p[1], mid)
    if k == "q": return ui.quiz_ctl(uid, mid, p[1])
    if k == "x": return ui.on_choice(uid, mid, int(p[1]))
    if k == "b": return ui.on_build(uid, mid, p[1])
    if k == "mt": return ui.on_match(uid, mid, p[1])
    if k == "ms":
        return {"list": lambda: ui.mistakes_list(uid, mid), "practice": lambda: ui.mistakes_practice(uid, mid), "review": lambda: ui.mistakes_practice(uid, mid, True)}[p[1]]()
    if k == "mock": return ui.mock_start(uid, mid)
    if k == "sh":
        if p[1] == "hear":
            s = ui.get_sess(uid); return ui.send_audio_quiet(uid, s.get("zh", "")) if s.get("zh") else None
        return ui.shadow_start(uid, mid)
    if k == "al": return ui.alpha_cb(uid, mid, p)
    if k == "rd": return ui.reader_show(uid, mid, p[1], int(p[2]), int(p[3]))
    if k == "rda": return ui.reader_audio(uid, p[1])
    if k == "st": return ui.settings_cb(uid, mid, p)
    if k == "ad":
        if not logic.is_admin(uid): return
        return admin.callback(uid, mid, p)

# ---------------------------------------------------------------- group callbacks
def group_callback(cb):
    p = (cb.get("data") or "").split(":"); k = p[0]; cid = cb["message"]["chat"]["id"]; uid = cb["from"]["id"]
    if k == "gq":
        if p[1] == "next":
            C.answer_cb(cb["id"]); ch = logic.get_chat(cid)
            if ch and C.rate_ok(("gu", cid, uid), config.GROUP_USER_CMDS_PER_MIN): G.group_quiz_start(cid, ch, cb["from"])
            return
        if p[1] == "top":
            C.answer_cb(cb["id"]); ch = logic.get_chat(cid); return G.group_top(cid, ch) if ch else None
        return G.on_quiz_cb(cb, p)
    if k == "gt": return G.T.on_callback(cb, p)
    if k == "gw":
        C.answer_cb(cb["id"]); ch = logic.get_chat(cid)
        if ch and ch["enabled"] and C.rate_ok(("gw", cid), 2, 60): G.group_word(cid, ch)
        return
    if k == "gs":
        if p[1] == "menu": return G.on_settings_menu(cb)
        return G.on_settings_cb(cb, p)
    C.answer_cb(cb["id"])
    if k == "hr":
        w = logic.get_word(int(p[1]))
        if w and C.rate_ok(("ga", cid), 6): ui.send_audio_quiet(cid, w["hz"])
    elif k == "hz":
        if C.rate_ok(("ga", cid), 6): ui.send_audio_quiet(cid, ":".join(p[1:]))

# ---------------------------------------------------------------- dispatch
def describe(up):
    """-> (update type, chat dict or None, short description without message contents)."""
    for k in ("message", "edited_message", "channel_post", "edited_channel_post"):
        if k in up:
            m = up[k]; txt = m.get("text") or ""
            if txt.startswith("/"): kind = "command " + txt.split()[0].split("@")[0][:32]
            elif m.get("text"): kind = "text"
            else:
                kind = next((x for x in ("new_chat_members", "left_chat_member", "migrate_to_chat_id", "migrate_from_chat_id", "photo", "voice", "audio", "sticker", "video", "document", "poll", "caption") if x in m), "other")
            return k, m.get("chat"), kind
    if "callback_query" in up:
        cb = up["callback_query"]; return "callback_query", (cb.get("message") or {}).get("chat"), "data " + (cb.get("data") or "").split(":")[0][:12]
    for k in ("my_chat_member", "chat_member"):
        if k in up:
            u = up[k]; return k, u.get("chat"), f"{(u.get('old_chat_member') or {}).get('status')}->{(u.get('new_chat_member') or {}).get('status')}"
    return next((k for k in up if k != "update_id"), "unknown"), None, ""

def handle_update(up):
    try:
        utype, chat, kind = describe(up)
        if chat and chat.get("type") != "private":
            log.info("update %s: chat=%s (%s) %s", utype, chat.get("id"), chat.get("type"), kind)
        if "my_chat_member" in up: return G.on_my_chat_member(up["my_chat_member"])
        if chat and chat.get("type") in ("group", "supergroup") and utype in ("callback_query", "edited_message", "chat_member"):
            frm = (up.get(utype) or {}).get("from")
            G.ensure_chat(chat, frm, utype)
        if "chat_member" in up or "edited_message" in up: return          # registered above; no replies to edits / member changes
        if "callback_query" in up:
            cb = up["callback_query"]
            if not cb.get("message"): return C.answer_cb(cb["id"])
            if cb["message"]["chat"]["type"] == "private": return private_callback(cb)
            return group_callback(cb)
        msg = up.get("message")
        if not msg or not msg.get("chat"): return
        t = msg["chat"]["type"]
        if t == "private":
            if msg.get("from") and not msg["from"].get("is_bot"): private_message(msg)
        elif t in ("group", "supergroup"):
            if msg.get("text") and msg.get("reply_to_message") and G.on_time_reply(msg): return
            G.on_message(msg)
    except Exception as e:
        log.exception("handler error: %s", C.safe(e))
        try:
            chat = (up.get("message") or (up.get("callback_query") or {}).get("message") or {}).get("chat", {})
            if chat.get("type") == "private" and chat.get("id"):
                send(chat["id"], tr(logic.user_lang(chat["id"]), "unexpected"), html=False)
        except Exception: pass

def single_instance():
    fd = open(os.path.join(config.BASE, "bot.lock"), "a+")
    try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("another instance is already running", file=sys.stderr); sys.exit(0)
    fd.seek(0); fd.truncate(); fd.write(str(os.getpid())); fd.flush()
    return fd

ALLOWED = ["message", "edited_message", "callback_query", "my_chat_member", "chat_member"]

def main():
    if not C.TOKEN:
        print(f"ERROR: {config.TOKEN_ENV} is not set", file=sys.stderr); sys.exit(1)
    _lock = single_instance()
    C.setup_logging(); db.init()
    me = call("getMe"); C.BOT_USERNAME = me["username"]; C.BOT_ID = me["id"]
    log.info("%s started: @%s", config.BOT_NAME, C.BOT_USERNAME)
    try:
        wh = call("getWebhookInfo")
        if wh.get("url"): log.info("Webhook was set; deleting to use long polling"); call("deleteWebhook")
    except ApiError as e: log.warning("webhook check: %s", C.safe(e)[:80])
    try:
        wh = call("getWebhookInfo"); log.info("polling with allowed_updates=%s, pending updates=%s", ALLOWED, wh.get("pending_update_count"))
    except ApiError: pass
    sched.start()
    offset = None
    while True:
        try:
            params = {"timeout": 30, "allowed_updates": json.dumps(ALLOWED)}
            if offset: params["offset"] = offset
            updates = call("getUpdates", params, timeout=45)
        except ApiError as e:
            log.warning("getUpdates: %s", C.safe(e)[:100]); time.sleep(5); continue
        for up in updates:
            offset = up["update_id"] + 1
            handle_update(up)

if __name__ == "__main__":
    main()
