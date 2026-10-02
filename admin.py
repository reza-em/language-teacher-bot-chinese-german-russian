"""Owner/admin panel: stats, users, groups, throttled broadcast, content editor, LLM settings, export, channel kit (owner only)."""
import json, os, io, csv, time, zipfile, logging, threading, re
import config, db, logic, data, llm, srs, tts
import core as C
import channels as CH
import ui
from core import btn, kb, grid, esc, send, show, rtl, num
from texts import tr, LANG_LABEL

log = logging.getLogger("admin")

def L_(uid): return ui.ul(uid)
def say(uid, text, markup=None, mid=None):
    return show(uid, mid, rtl(L_(uid), text), markup) if mid else send(uid, rtl(L_(uid), text), markup)

def allowed(uid): return logic.is_admin(uid)
def owner(uid): return logic.is_owner(uid)

def panel(uid, mid=None):
    lang = L_(uid)
    rows = [[btn(tr(lang, "a_b_stats"), "ad:stats"), btn(tr(lang, "a_b_users"), "ad:users:1")],
            [btn(tr(lang, "a_b_groups"), "ad:groups"), btn(tr(lang, "a_b_channels"), "ad:ch")],
            [btn(tr(lang, "a_b_bc"), "ad:bc"), btn(tr(lang, "a_b_content"), "ad:content")],
            [btn(tr(lang, "a_b_settings"), "ad:set"), btn(tr(lang, "a_b_export"), "ad:export")], ui.menu_row(lang)]
    say(uid, tr(lang, "a_title"), kb(rows), mid)

def back_row(lang): return [btn(tr(lang, "a_back"), "ad:menu")]

# ---------------------------------------------------------------- dispatch
def callback(uid, mid, p):
    lang = L_(uid)
    if not allowed(uid): return
    op = p[1]
    if op in ("ch", "bc", "set", "export", "content", "cw", "ca") and not owner(uid) and op != "bc":
        return send(uid, tr(lang, "a_owner_only"))
    if op == "menu": return panel(uid, mid)
    if op == "stats": return stats(uid, mid)
    if op == "users": return users(uid, mid, int(p[2]))
    if op == "u": return user_card(uid, mid, int(p[2]), p[3] if len(p) > 3 else None)
    if op == "usearch":
        logic.set_await(uid, "a_search"); return say(uid, tr(lang, "a_search_ask"), kb([back_row(lang)]), mid)
    if op == "groups": return groups(uid, mid)
    if op == "g": return group_card(uid, mid, int(p[2]), p[3] if len(p) > 3 else None)
    if op == "bc": return bc_menu(uid, mid, p)
    if op == "content": return content_menu(uid, mid, p)
    if op == "set": return settings(uid, mid, p)
    if op == "export": return export(uid, mid, p)
    if op == "ch": return channels_cb(uid, mid, p)

def stats(uid, mid):
    lang = L_(uid); s = logic.stats()
    text = tr(lang, "a_stats", **{k: num(lang, v) for k, v in s.items()}, llm=tr(lang, "a_on") if llm.configured() else tr(lang, "a_off"), tts=esc(tts.VOICE))
    say(uid, text, kb([back_row(lang)]), mid)

def users(uid, mid, page):
    lang = L_(uid); rows_, page, pages, total = logic.users_page(page)
    rows = [[btn(f"{(r['name'] or '?')[:22]} {'🚫' if r['banned'] else ''}{'👑' if r['is_admin'] else ''}", f"ad:u:{r['id']}")] for r in rows_]
    nav = [btn("⬅️", f"ad:users:{max(1, page - 1)}"), btn(f"{page}/{pages}", "noop"), btn("➡️", f"ad:users:{min(pages, page + 1)}")]
    rows += [nav, [btn(tr(lang, "a_search"), "ad:usearch")], back_row(lang)]
    say(uid, tr(lang, "a_users", page=page, pages=pages, total=total), kb(rows), mid)

def user_card(uid, mid, tid, act=None):
    lang = L_(uid); u = logic.get_user(tid)
    if not u: return say(uid, tr(lang, "a_not_found"), kb([back_row(lang)]), mid)
    if act:
        if tid == db.meta_get("owner_id") and act in ("ban", "rmadmin"): return send(uid, tr(lang, "a_owner_only"))
        if act in ("mkadmin", "rmadmin") and not owner(uid): return send(uid, tr(lang, "a_owner_only"))
        if act == "ban": logic.update_user(tid, banned=1)
        elif act == "unban": logic.update_user(tid, banned=0)
        elif act == "mkadmin": logic.update_user(tid, is_admin=1)
        elif act == "rmadmin": logic.update_user(tid, is_admin=0)
        elif act == "reset":
            for t in ("cards", "mistakes", "daily"): db.ex(f"DELETE FROM {t} WHERE user_id=?", (tid,))
            logic.update_user(tid, xp=0, ok=0, bad=0, streak=0, best_streak=0, last_day="")
        u = logic.get_user(tid)
    tot = u["ok"] + u["bad"]
    st = ("🚫 banned" if u["banned"] else "✅") + (" 👑" if u["is_admin"] else "")
    text = tr(lang, "a_user_card", name=esc(u["name"]), uname=("@" + u["username"]) if u["username"] else "", id=tid, level=u["level"], xp=u["xp"], streak=u["streak"], ok=u["ok"], tot=tot,
              cards=srs.total_cards(tid), ui=u["ui"], expl=u["expl"], status=st)
    rows = [[btn(tr(lang, "a_unban") if u["banned"] else tr(lang, "a_ban"), f"ad:u:{tid}:{'unban' if u['banned'] else 'ban'}"), btn(tr(lang, "a_reset"), f"ad:u:{tid}:reset")]]
    if owner(uid): rows.append([btn(tr(lang, "a_rm_admin") if u["is_admin"] else tr(lang, "a_make_admin"), f"ad:u:{tid}:{'rmadmin' if u['is_admin'] else 'mkadmin'}")])
    rows.append([btn(tr(lang, "b_back"), "ad:users:1")])
    say(uid, text, kb(rows), mid)

def groups(uid, mid):
    lang = L_(uid); gs = db.q("SELECT * FROM chats WHERE active=1 AND type IN ('group','supergroup') ORDER BY added_at DESC LIMIT 30")
    if not gs: return say(uid, tr(lang, "a_group_none"), kb([back_row(lang)]), mid)
    rows = [[btn((g["title"] or str(g["id"]))[:40] + (" 👑" if g["bot_admin"] else ""), f"ad:g:{g['id']}")] for g in gs] + [back_row(lang)]
    say(uid, tr(lang, "a_groups", n=len(gs)), kb(rows), mid)

def group_card(uid, mid, gid, act=None):
    lang = L_(uid); g = logic.get_chat(gid)
    if not g: return say(uid, tr(lang, "a_not_found"), kb([back_row(lang)]), mid)
    if act == "leave" and owner(uid):
        try: C.call("leaveChat", {"chat_id": gid})
        except C.ApiError: pass
        logic.update_chat(gid, active=0); return groups(uid, mid)
    if act == "toggle" and owner(uid): logic.update_chat(gid, enabled=0 if g["enabled"] else 1); g = logic.get_chat(gid)
    text = tr(lang, "a_group_card", title=esc(g["title"]), id=gid, ui=g["ui"], expl=g["expl"], level=g["level"], daily=tr(lang, "a_on") if g["daily"] else tr(lang, "a_off"), time=g["daily_time"],
              admin="✅" if g["bot_admin"] else "—", enabled="✅" if g["enabled"] else "⛔")
    rows = [[btn(tr(lang, "a_toggle"), f"ad:g:{gid}:toggle")] + ([btn(tr(lang, "a_leave"), f"ad:g:{gid}:leave")] if owner(uid) else []), [btn(tr(lang, "b_back"), "ad:groups")]]
    say(uid, text, kb(rows), mid)

# ---------------------------------------------------------------- broadcast (throttled)
def bc_recipients(target):
    if target == "users": return [r["id"] for r in db.q("SELECT id FROM users WHERE banned=0 AND can_dm=1")]
    return [r["id"] for r in db.q("SELECT id FROM chats WHERE active=1 AND enabled=1 AND type IN ('group','supergroup')")]

def bc_menu(uid, mid, p):
    lang = L_(uid); op = p[2] if len(p) > 2 else ""
    if not owner(uid): return send(uid, tr(lang, "a_owner_only"))
    if op in ("users", "groups"):
        logic.set_await(uid, "a_bc", {"target": op}); return say(uid, tr(lang, "a_bc_text"), kb([[btn(tr(lang, "a_cancel"), "ad:bc:x")]]), mid)
    if op == "x":
        logic.set_await(uid, None); return panel(uid, mid)
    if op == "go":
        u = logic.get_user(uid); aw, d = logic.get_await(uid)
        if aw != "a_bc_ready": return panel(uid, mid)
        bid = db.ex("INSERT INTO broadcasts(text,target,ts,total,state) VALUES(?,?,?,?,?)", (d["text"], d["target"], db.now(), len(bc_recipients(d["target"])), "running")).lastrowid
        logic.set_await(uid, None); say(uid, tr(lang, "a_bc_started"), kb([back_row(lang)]), mid)
        threading.Thread(target=run_broadcast, args=(bid, uid), daemon=True).start(); return
    say(uid, tr(lang, "a_bc_target"), kb([[btn(tr(lang, "a_bc_users", n=len(bc_recipients("users"))), "ad:bc:users")], [btn(tr(lang, "a_bc_groups", n=len(bc_recipients("groups"))), "ad:bc:groups")], back_row(lang)]), mid)

def run_broadcast(bid, notify_uid, sleep=time.sleep):
    b = db.q1("SELECT * FROM broadcasts WHERE id=?", (bid,)); sent = failed = 0
    for rid in bc_recipients(b["target"]):
        try:
            C.call("sendMessage", {"chat_id": rid, "text": b["text"][:4096], "parse_mode": "HTML", "disable_web_page_preview": True}); sent += 1
        except C.ApiError as e:
            failed += 1
            if e.retry_after: sleep(min(e.retry_after, 30) + 1)
            if e.code in (403, 400) and b["target"] == "users": db.ex("UPDATE users SET can_dm=0 WHERE id=?", (rid,))
        sleep(1.0 / config.BROADCAST_PER_SEC)
    db.ex("UPDATE broadcasts SET sent=?, failed=?, state='done' WHERE id=?", (sent, failed, bid))
    send(notify_uid, rtl(L_(notify_uid), tr(L_(notify_uid), "a_bc_report", sent=sent, failed=failed)))

# ---------------------------------------------------------------- content editor
def content_menu(uid, mid, p):
    lang = L_(uid); op = p[2] if len(p) > 2 else ""
    cnt = lambda k: db.val("SELECT COUNT(*) FROM custom WHERE kind=?", (k,), 0)
    if op in ("word", "lesson", "ex"):
        logic.set_await(uid, "a_add", {"kind": op})
        return say(uid, tr(lang, {"word": "a_word_fmt", "lesson": "a_lesson_fmt", "ex": "a_ex_fmt"}[op]), kb([[btn(tr(lang, "a_cancel"), "ad:content")]]), mid)
    if op == "list":
        rows_ = db.q("SELECT * FROM custom ORDER BY id DESC LIMIT 20")
        if not rows_: return say(uid, tr(lang, "a_custom_none"), kb([[btn(tr(lang, "a_back"), "ad:content")]]), mid)
        rows = [[btn(f"{'✅' if r['enabled'] else '⬜'} {r['kind']} #{r['id']} {_title(r)}", f"ad:content:t:{r['id']}")] for r in rows_] + [[btn(tr(lang, "a_back"), "ad:content")]]
        return say(uid, tr(lang, "a_list_custom"), kb(rows), mid)
    if op == "t":
        db.ex("UPDATE custom SET enabled=1-enabled WHERE id=?", (int(p[3]),)); return content_menu(uid, mid, ["ad", "content", "list"])
    if op == "d":
        db.ex("DELETE FROM custom WHERE id=?", (int(p[3]),)); return content_menu(uid, mid, ["ad", "content", "list"])
    logic.set_await(uid, None)
    rows = [[btn(tr(lang, "a_add_word"), "ad:content:word"), btn(tr(lang, "a_add_lesson"), "ad:content:lesson"), btn(tr(lang, "a_add_ex"), "ad:content:ex")], [btn(tr(lang, "a_list_custom"), "ad:content:list")], back_row(lang)]
    say(uid, tr(lang, "a_content", nw=cnt("word"), nl=cnt("lesson"), ne=cnt("ex")), kb(rows), mid)

def _title(r):
    d = json.loads(r["data"]); return (d.get("hz") or d.get("title") or d.get("q") or "")[:20]

def parse_custom(kind, text):
    """-> dict or None."""
    text = text.strip()
    if kind == "word":
        p = [x.strip() for x in text.split("|")]
        if len(p) < 4 or not data.has_hanzi(p[0]) or not p[1]: return None
        lv = 1
        if len(p) >= 6 and p[5].isdigit(): lv = max(1, min(3, int(p[5])))
        return {"hz": p[0][:12], "py": p[1][:40], "fa": p[2][:80], "en": p[3][:80], "de": (p[4] if len(p) > 4 else "")[:80], "lv": lv}
    if kind == "lesson":
        lines = text.split("\n", 1)
        if len(lines) < 2 or not lines[0].strip() or not lines[1].strip(): return None
        return {"title": lines[0].strip()[:80], "body": lines[1].strip()[:1500]}
    if kind == "ex":
        p = [x.strip() for x in text.split("|")]
        if len(p) < 4 or not all(p[:4]): return None
        wrong = [x for x in p[2:5] if x]
        return {"q": p[0][:300], "a": p[1][:80], "wrong": wrong[:3], "explain": (p[5] if len(p) > 5 else "")[:300]}
    return None

def on_text(uid, text):
    """Handle text for admin awaiting states. -> True if consumed."""
    aw, d = logic.get_await(uid); lang = L_(uid)
    if not aw or not aw.startswith("a_") or not allowed(uid): return False
    if aw == "a_search":
        logic.set_await(uid, None); rows_, _, _, total = logic.users_page(1, 8, text.strip())
        if not rows_: return send(uid, tr(lang, "a_not_found")) and True
        rows = [[btn(f"{r['name'][:22]}", f"ad:u:{r['id']}")] for r in rows_] + [back_row(lang)]
        say(uid, tr(lang, "a_users", page=1, pages=1, total=total), kb(rows)); return True
    if not owner(uid): return False
    if aw == "a_bc":
        logic.set_await(uid, "a_bc_ready", {"target": d["target"], "text": text}); n = len(bc_recipients(d["target"]))
        say(uid, tr(lang, "a_bc_confirm", text=text, n=n, sec=max(1, n // config.BROADCAST_PER_SEC)), kb([[btn(tr(lang, "a_yes_go"), "ad:bc:go"), btn(tr(lang, "a_cancel"), "ad:bc:x")]])); return True
    if aw == "a_add":
        rec = parse_custom(d["kind"], text)
        if not rec: send(uid, rtl(lang, tr(lang, "a_bad_fmt"))); return True
        i = db.ex("INSERT INTO custom(kind,data,enabled,created_by,created) VALUES(?,?,1,?,?)", (d["kind"], json.dumps(rec, ensure_ascii=False), uid, db.now())).lastrowid
        logic.set_await(uid, None); say(uid, tr(lang, "a_added", id=i), kb([[btn(tr(lang, "a_add_" + {"word": "word", "lesson": "lesson", "ex": "ex"}[d["kind"]]), f"ad:content:{d['kind']}"), btn(tr(lang, "a_back"), "ad:content")]])); return True
    if aw == "a_set":
        field = d["field"]; v = text.strip()
        if field == "limit":
            if not v.isdigit() or not (0 <= int(v) <= 1000): send(uid, tr(lang, "a_val_bad")); return True
            llm.set_setting(daily_limit=int(v))
        elif field == "base":
            if not re.match(r"^https?://", v): send(uid, tr(lang, "a_val_bad")); return True
            llm.set_setting(base=v.rstrip("/"))
        elif field in ("model", "stt_model"):
            if len(v) > 80 or " " in v: send(uid, tr(lang, "a_val_bad")); return True
            llm.set_setting(**{field: "" if v in ("-", "off") else v})
        logic.set_await(uid, None); settings(uid, None, ["ad", "set"]); return True
    if aw == "a_ch_add":
        logic.set_await(uid, None); channel_register(uid, text.strip()); return True
    if aw == "a_ch_times":
        ts = [C.norm_digits(t).strip() for t in re.split(r"[\s,،;]+", text) if t.strip()]
        ts = ["0" + t if re.fullmatch(r"\d:\d\d", t) else t for t in ts]
        if not ts or len(ts) > 12 or not all(logic.hhmm_ok(t) for t in ts): send(uid, tr(lang, "bad_time")); return True
        ts = sorted(set(ts)); db.ex("UPDATE channels SET times=? WHERE chat_id=?", (json.dumps(ts), d["chat"]))
        c = CH.get(d["chat"]); s, _ = CH.slot_now(c); db.ex("UPDATE channels SET last_slot=? WHERE chat_id=?", (s or "", d["chat"]))
        logic.set_await(uid, None); send(uid, rtl(lang, tr(lang, "c_times_set", times=" ".join(ts)))); channel_card(uid, None, d["chat"]); return True
    return False

# ---------------------------------------------------------------- LLM settings
def settings(uid, mid, p):
    lang = L_(uid); s = llm.settings(); op = p[2] if len(p) > 2 else ""
    if op == "toggle": llm.set_setting(enabled=not s["enabled"]); s = llm.settings()
    elif op in ("base", "model", "stt_model", "limit"):
        logic.set_await(uid, "a_set", {"field": op}); return say(uid, tr(lang, "a_s_ask") + ("\n(- = off)" if op == "stt_model" else ""), kb([[btn(tr(lang, "a_cancel"), "ad:set")]]), mid)
    text = tr(lang, "a_set", llm=tr(lang, "a_on") if s["enabled"] else tr(lang, "a_off"), base=esc(s["base"]), model=esc(s["model"]), stt=esc(s["stt_model"] or "—"), limit=s["daily_limit"],
              key=tr(lang, "a_key_set") if llm.key() else tr(lang, "a_key_unset"))
    rows = [[btn(tr(lang, "a_s_toggle"), "ad:set:toggle")], [btn(tr(lang, "a_s_base"), "ad:set:base"), btn(tr(lang, "a_s_model"), "ad:set:model")],
            [btn(tr(lang, "a_s_stt"), "ad:set:stt_model"), btn(tr(lang, "a_s_limit"), "ad:set:limit")], back_row(lang)]
    say(uid, text, kb(rows), mid)

# ---------------------------------------------------------------- export
def build_export(path):
    """Zip with users/progress/groups/custom content (JSON+CSV). No tokens, no API keys."""
    users = db.q("SELECT id,username,name,ui,expl,level,methods,srs_mode,daily_goal,remind,tz,streak,best_streak,xp,ok,bad,banned,is_admin,first_seen,last_seen FROM users")
    cards = db.q("SELECT * FROM cards"); chats = db.q("SELECT * FROM chats"); chn = db.q("SELECT * FROM channels"); cust = db.q("SELECT * FROM custom")
    gs = db.q("SELECT * FROM gscores")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, rows in (("users", users), ("cards", cards), ("groups", chats), ("channels", chn), ("custom", cust), ("group_scores", gs)):
            z.writestr(name + ".json", json.dumps(rows, ensure_ascii=False, indent=1))
            if rows:
                buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows); z.writestr(name + ".csv", buf.getvalue())
    return path

def export(uid, mid, p):
    lang = L_(uid)
    if len(p) > 2 and p[2] == "go":
        path = os.path.join(os.path.dirname(config.DB_PATH) or ".", f"export_{int(time.time())}.zip")
        try:
            build_export(path)
            if not C.send_document(uid, path, "export"): send(uid, tr(lang, "a_export_none"))
        finally:
            try: os.remove(path)
            except OSError: pass
        return
    say(uid, tr(lang, "a_export"), kb([[btn(tr(lang, "a_export_go"), "ad:export:go")], back_row(lang)]), mid)

# ---------------------------------------------------------------- channel kit (owner only)
def channels_cb(uid, mid, p):
    lang = L_(uid)
    if not owner(uid): return send(uid, tr(lang, "a_owner_only"))
    op = p[2] if len(p) > 2 else ""
    if op == "add":
        logic.set_await(uid, "a_ch_add"); return say(uid, tr(lang, "c_add_ask"), kb([[btn(tr(lang, "a_cancel"), "ad:ch")]]), mid)
    if op == "reg": return channel_register(uid, int(p[3]), mid)
    if op == "c": return channel_card(uid, mid, int(p[3]))
    if op in ("toggle", "now", "pin", "del", "times", "types", "type", "lang", "btn"):
        cid = int(p[3]); c = CH.get(cid)
        if not c: return channels_cb(uid, mid, ["ad", "ch"])
        if op == "toggle": db.ex("UPDATE channels SET enabled=1-enabled WHERE chat_id=?", (cid,))
        elif op == "btn": db.ex("UPDATE channels SET btn=1-btn WHERE chat_id=?", (cid,))
        elif op == "lang":
            nxt = config.LANGS[(config.LANGS.index(c["lang"]) + 1) % 3] if c["lang"] in config.LANGS else "fa"; db.ex("UPDATE channels SET lang=? WHERE chat_id=?", (nxt, cid))
        elif op == "del":
            db.ex("DELETE FROM channels WHERE chat_id=?", (cid,)); send(uid, rtl(lang, tr(lang, "c_removed"))); return channels_cb(uid, None, ["ad", "ch"])
        elif op == "times":
            logic.set_await(uid, "a_ch_times", {"chat": cid}); return say(uid, tr(lang, "c_times_ask"), kb([[btn(tr(lang, "a_cancel"), f"ad:ch:c:{cid}")]]), mid)
        elif op == "types":
            return types_panel(uid, mid, cid)
        elif op == "type":
            ts = CH.types_of(c); t = p[4]
            if t in ts and len(ts) > 1: ts.remove(t)
            elif t not in ts and t in CH.TYPES: ts.append(t)
            db.ex("UPDATE channels SET types=? WHERE chat_id=?", (json.dumps(ts), cid)); return types_panel(uid, mid, cid)
        elif op == "now":
            ok, err = CH.post(c)
            send(uid, rtl(lang, tr(lang, "c_posted") if ok else tr(lang, "c_post_fail", err=esc(err))))
        elif op == "pin":
            ok, r = CH.post_intro(c)
            send(uid, rtl(lang, (tr(lang, "c_pinned") if r == "ok" else tr(lang, "c_pin_fail")) if ok else tr(lang, "c_post_fail", err=esc(r))))
        return channel_card(uid, mid, cid)
    pend = db.q("SELECT * FROM pending_channels ORDER BY ts DESC")
    chs = CH.all_channels()
    rows = [[btn(("✅ " if c["enabled"] else "⏸ ") + (c["title"] or str(c["chat_id"]))[:34], f"ad:ch:c:{c['chat_id']}")] for c in chs]
    rows += [[btn(tr(lang, "c_pending", title=(r["title"] or str(r["chat_id"]))[:30]), f"ad:ch:reg:{r['chat_id']}")] for r in pend if not CH.get(r["chat_id"])]
    rows += [[btn(tr(lang, "c_add"), "ad:ch:add")], back_row(lang)]
    say(uid, tr(lang, "c_title", n=len(chs)) + ("" if chs else "\n\n" + tr(lang, "c_none")), kb(rows), mid)

def types_panel(uid, mid, cid):
    lang = L_(uid); c = CH.get(cid); on = CH.types_of(c)
    rows = [[btn(("✅ " if t in on else "⬜ ") + tr(lang, "c_type_" + t), f"ad:ch:type:{cid}:{t}")] for t in CH.TYPES] + [[btn(tr(lang, "b_back"), f"ad:ch:c:{cid}")]]
    say(uid, tr(lang, "c_types_head"), kb(rows), mid)

def channel_card(uid, mid, cid):
    lang = L_(uid); c = CH.get(cid)
    if not c: return channels_cb(uid, mid, ["ad", "ch"])
    text = tr(lang, "c_card", title=esc(c["title"]), uname=("@" + c["username"]) if c["username"] else "", enabled=tr(lang, "a_on") if c["enabled"] else tr(lang, "a_off"), tz=c["tz"],
              times=" ".join(CH.times_of(c)), types=esc(" ".join(tr(lang, "c_type_" + t).split()[0] for t in CH.types_of(c))), lang=LANG_LABEL[c["lang"]],
              btn=tr(lang, "a_on") if c["btn"] else tr(lang, "a_off"), counter=num(lang, c["counter"]))
    rows = [[btn(tr(lang, "c_b_toggle"), f"ad:ch:toggle:{cid}"), btn(tr(lang, "c_b_times"), f"ad:ch:times:{cid}")],
            [btn(tr(lang, "c_b_types"), f"ad:ch:types:{cid}"), btn(tr(lang, "c_b_lang"), f"ad:ch:lang:{cid}")],
            [btn(tr(lang, "c_b_btn"), f"ad:ch:btn:{cid}"), btn(tr(lang, "c_b_now"), f"ad:ch:now:{cid}")],
            [btn(tr(lang, "c_b_pin"), f"ad:ch:pin:{cid}")], [btn(tr(lang, "c_b_del"), f"ad:ch:del:{cid}"), btn(tr(lang, "b_back"), "ad:ch")]]
    say(uid, text + "\n\n" + tr(lang, "c_pin_note"), kb(rows), mid)

def channel_register(uid, ref, mid=None):
    """ref: numeric chat id or @username. Validates with getChat/getChatMember."""
    lang = L_(uid)
    try:
        if isinstance(ref, str):
            ref = ref.strip()
            if re.fullmatch(r"-?\d+", ref): ref = int(ref)
            else:
                ref = "@" + ref.lstrip("@").replace("https://t.me/", "")
        chat = C.call("getChat", {"chat_id": ref})
        if chat.get("type") != "channel": raise C.ApiError("not a channel")
        m = C.call("getChatMember", {"chat_id": chat["id"], "user_id": C.BOT_ID})
        if m.get("status") not in ("administrator", "creator"): raise C.ApiError("bot is not an admin")
        if m.get("status") == "administrator" and not m.get("can_post_messages"): raise C.ApiError("bot lacks the Post messages right")
    except C.ApiError as e:
        send(uid, rtl(lang, tr(lang, "c_fail", err=esc(str(e))[:150]))); return None
    c = CH.register(chat["id"], chat.get("title"), chat.get("username"))
    send(uid, rtl(lang, tr(lang, "c_added", title=esc(chat.get("title") or "")))); channel_card(uid, mid, chat["id"]); return c
