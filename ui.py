"""Private-chat teacher: menus, onboarding, learn/today/review, exercises (check + correct), dictionary, ask, alphabet, reader, settings."""
import json, time, random, logging, datetime, re
import config, db, logic, data, srs, llm, tts, fmt, langs, uix, exercises as X
import core as C
import pinyin_utils as P
import textnorm
import content.alphabet as A
import content.lessons as L
from core import btn, kb, grid, esc, send, show, rtl, num
from texts import tr, LANG_LABEL

log = logging.getLogger("ui")
LEVELS = (0, 1, 2, 3)
QMODES = ("quiz", "mock", "course", "place")      # session modes handled by the exercise engine

# ---------------------------------------------------------------- helpers
def ul(uid): return logic.user_lang(uid)
def el(uid): return logic.expl_lang(uid)

def out(uid, text, markup=None, **kw):
    return send(uid, rtl(ul(uid), text), markup, **kw)

def edit(uid, mid, text, markup=None):
    return show(uid, mid, rtl(ul(uid), text), markup)

def get_sess(uid, chat_id=None):
    r = db.q1("SELECT data FROM sess WHERE user_id=? AND chat_id=?", (uid, chat_id or uid))
    if not r: return {}
    try: return json.loads(r["data"])
    except Exception: return {}

def set_sess(uid, s, chat_id=None):
    db.ex("INSERT INTO sess(user_id,chat_id,data,updated) VALUES(?,?,?,?) ON CONFLICT(user_id,chat_id) DO UPDATE SET data=excluded.data, updated=excluded.updated",
          (uid, chat_id or uid, json.dumps(s, ensure_ascii=False), db.now()))

def clear_sess(uid): db.ex("DELETE FROM sess WHERE user_id=? AND chat_id=?", (uid, uid))

def lang_name(code): return LANG_LABEL.get(code, code)

def main_menu(lang, uid=None):
    zh = uid is None or logic.target(uid) == "zh"
    rows = [[btn(tr(lang, "b_today"), "m:today")],
            [btn(tr(lang, "b_course"), "m:course"), btn(tr(lang, "b_lang"), "m:lang")],
            [btn(tr(lang, "b_learn"), "m:learn"), btn(tr(lang, "b_quiz"), "m:quiz")],
            [btn(tr(lang, "b_review"), "m:review"), btn(tr(lang, "b_dict"), "m:dict")],
            [btn(tr(lang, "b_alpha"), "m:alpha")] + ([btn(tr(lang, "b_read"), "m:read")] if zh else []),
            [btn(tr(lang, "b_ask"), "m:ask"), btn(tr(lang, "b_progress"), "m:progress")],
            [btn(tr(lang, "b_settings"), "m:settings"), btn(tr(lang, "b_help"), "m:help")]]
    return kb(rows)

def menu_row(lang): return [btn(tr(lang, "b_menu"), "m:menu")]

def show_menu(uid, mid=None):
    logic.set_await(uid, None)
    edit(uid, mid, tr(ul(uid), "menu_title"), main_menu(ul(uid), uid))

# ---------------------------------------------------------------- onboarding
def lang_buttons(prefix, with_auto=False, lang="fa"):
    rows = [[btn(tr(lang, "lang_fa"), prefix + "fa"), btn(tr(lang, "lang_en"), prefix + "en"), btn(tr(lang, "lang_de"), prefix + "de")]]
    if with_auto: rows.append([btn(tr(lang, "expl_auto"), prefix + "auto")])
    return rows

def start(uid, first_name=None, payload=""):
    u = logic.get_user(uid)
    if not u.get("onboarded"):
        send(uid, "🌍 " + "<b>" + esc(config.BOT_NAME) + "</b>\n\n" + tr("fa", "pick_ui") + "\n" + tr("en", "pick_ui") + "\n" + tr("de", "pick_ui"),
             kb(lang_buttons("ob:ui:", lang=u.get("ui") or "fa")))
        return
    lang = ul(uid)
    if payload.startswith("g") and payload[1:].isdigit():
        ch = logic.get_chat(-int(payload[1:])) or {}
        if ch: out(uid, tr(lang, "g_dm_start", title=esc(ch.get("title") or "")))
    clear_sess(uid)
    cap = tr(lang, "welcome", name=esc(config.BOT_NAME_FA if lang == "fa" else config.BOT_NAME_EN if lang == "en" else config.BOT_NAME_DE))
    logo = db.meta_get("logo") or {}
    import os
    p = os.path.join(config.ASSETS, "logo.png")
    sent = None
    if os.path.exists(p):
        fid = logo.get("file_id") if logo.get("sha") == _logo_sha(p) else None
        try:
            if fid: sent = C.call("sendPhoto", {"chat_id": uid, "photo": fid, "caption": rtl(lang, cap), "parse_mode": "HTML", "reply_markup": main_menu(lang, uid)})
            else:
                with open(p, "rb") as f:
                    sent = C.call("sendPhoto", {"chat_id": uid, "caption": rtl(lang, cap), "parse_mode": "HTML", "reply_markup": main_menu(lang, uid)}, files={"photo": ("logo.png", f, "image/png")}, timeout=90)
                ph = (sent or {}).get("photo") or []
                if ph: db.meta_set("logo", {"sha": _logo_sha(p), "file_id": ph[-1]["file_id"]})
        except C.ApiError as e:
            log.warning("logo send failed: %s", C.safe(e)[:60]); sent = None
    if not sent: out(uid, cap, main_menu(lang, uid))

def _logo_sha(p):
    import hashlib
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def onboarding_cb(uid, mid, p):
    # ob:ui:<c> | ob:ex:<c> | ob:lv:<n> | ob:rm:<y|n>
    step, val = p[1], (p[2] if len(p) > 2 else "")
    if step == "ui" and val in config.LANGS:
        logic.update_user(uid, ui=val, expl=val)
        edit(uid, mid, tr(val, "pick_expl"), kb(lang_buttons("ob:ex:", True, val)))
    elif step == "ex" and (val in config.LANGS or val == "auto"):
        logic.update_user(uid, expl=val)
        edit(uid, mid, tr(ul(uid), "pick_target"), kb(uix.target_buttons("ob:tg:", ul(uid), logic.target(uid))))
    elif step == "tg" and val in langs.CODES:
        logic.set_target(uid, val)
        import course; course.path_menu(uid, mid, "ob")
    elif step in ("pl", "zero", "self"):
        import course; course.onboarding_choice(uid, mid, step)
    elif step == "lv" and val.isdigit() and int(val) in langs.levels(logic.target(uid)):
        logic.update_user(uid, level=int(val), onboarded=1); lang = ul(uid)
        e = el(uid)
        text = tr(lang, "onboard_done", level=esc(uix.level_text(uid, lang, int(val))), expl=esc(tr(lang, "expl_auto") if logic.get_user(uid)["expl"] == "auto" else lang_name(e)))
        text += "\n\n" + tr(lang, "pick_remind")
        t = config.DEFAULT_REMIND_TIME
        rows = [[btn(f"⏰ {t}", f"ob:rm:{t}"), btn(tr(lang, "b_off"), "ob:rm:n")]]
        edit(uid, mid, text, kb(rows))
    elif step == "rm":
        if val != "n" and re.fullmatch(r"\d\d:\d\d", p[2] + ":" + p[3] if len(p) > 3 else val): pass
        t = (p[2] + ":" + p[3]) if len(p) > 3 else val
        if t != "n" and logic.hhmm_ok(t):
            logic.update_user(uid, remind=t, last_remind=logic.local_day(logic.get_user(uid)["tz"]))
        lang = ul(uid)
        import course
        if not course.after_onboarding(uid, mid): edit(uid, mid, tr(lang, "menu_title"), main_menu(lang, uid))

# ---------------------------------------------------------------- word cards / learn
def card_markup(w, lang, last=False, extra_next=True, back="m:menu"):
    wid = w["i"]; rows = [[btn(tr(lang, "b_hear"), f"hr:{wid}")]]
    ch = next((c for c in w["hz"] if data.is_hanzi(c)), None)
    r2 = []
    if ch and data.available():
        r2 += [btn(tr(lang, "b_strokes"), f"sk:{wid}"), btn(tr(lang, "b_parts"), f"pt:{wid}")]
    rows.append(r2) if r2 else None
    if w.get("lang", "zh") != "zh":
        if langs.sentences_for(w): rows.append([btn(tr(lang, "b_more_ex"), f"mx:{wid}")])
        return rows
    rows.append([btn(tr(lang, "b_story"), f"sy:{wid}"), btn(tr(lang, "b_more_ex"), f"mx:{wid}")])
    return rows

def show_new_word(uid, mid=None, advance=False):
    lang = ul(uid); u = logic.get_user(uid); s = get_sess(uid)
    s2 = s if s.get("mode") == "learn" else {"mode": "learn", "i": 0, "seen": 0}
    n_target = logic.new_word_target(u)
    if advance: s2["i"] = s2.get("i", 0)
    if s2.get("seen", 0) >= n_target:
        set_sess(uid, {}); 
        edit(uid, mid, tr(lang, "learn_done"), kb([[btn(tr(lang, "b_quiz"), "m:quiz"), btn(tr(lang, "b_today"), "m:today")], menu_row(lang)])); return
    ws = logic.next_new_words(uid, 1)
    if not ws:
        edit(uid, mid, tr(lang, "learn_none"), kb([menu_row(lang)])); return
    w = ws[0]; srs.add_card(uid, w["i"]); logic.bump_new_word(uid)
    s2["seen"] = s2.get("seen", 0) + 1; s2["last"] = w["i"]; set_sess(uid, s2)
    text = tr(lang, "learn_intro", i=num(lang, s2["seen"]), n=num(lang, n_target)) + "\n\n" + fmt.word_card(w, lang, el(uid))
    rows = card_markup(w, lang); rows.append([btn(tr(lang, "b_next"), "ln:next"), btn(tr(lang, "b_stop"), "m:menu")])
    edit(uid, mid, text, kb(rows))

def tts_hint(chat):
    """Voice language for Latin-script text: the learner's (or group's) target language."""
    try: return logic.target(chat) if chat > 0 else (logic.get_chat(chat).get("target") or "zh")
    except Exception: return "zh"

def send_word_audio(uid, text, lang, tl=None):
    b, kind = tts.audio_bytes(text, tl or tts_hint(uid))
    if not b:
        out(uid, tr(lang, "tts_fail", t=esc(text))); return False
    if kind == "voice": C.send_voice(uid, b, caption=esc(text))
    else: _send_audio_file(uid, b, text)
    return True

def _send_audio_file(chat, b, caption=""):
    try: C.call("sendAudio", {"chat_id": chat, "caption": caption[:200], "title": caption[:40]}, files={"audio": ("a.mp3", b, "audio/mpeg")}, timeout=90)
    except C.ApiError as e: log.warning("sendAudio failed: %s", C.safe(e)[:80])

def send_prebuilt(chat, name, caption=""):
    b = tts.prebuilt(name)
    if b: _send_audio_file(chat, b, caption)
    return bool(b)

def send_strokes(uid, ch, lang):
    import strokes_img
    png = strokes_img.stroke_order_png(ch) if data.available() else None
    if not png: out(uid, tr(lang, "strokes_none")); return
    C.send_photo(uid, png, caption=rtl(lang, tr(lang, "strokes_cap", ch=esc(ch), n=data.stroke_count(ch))))

def word_action(uid, kind, wid, mid=None):
    lang = ul(uid); w = logic.get_word(wid)
    if not w: return
    ch = next((c for c in w["hz"] if data.is_hanzi(c)), None)
    if w.get("lang", "zh") != "zh":
        if kind == "hr": send_word_audio(uid, w["hz"], lang, w["lang"])
        elif kind == "mx":
            ss = langs.sentences_for(w); e = el(uid)
            out(uid, "📝\n\n" + "\n\n".join(f"{esc(s['ac'])}\n<i>{esc(s['fa'] if e == 'fa' else s['en'])}</i>" for s in ss) if ss else tr(lang, "word_none"))
        return
    if kind == "hr": send_word_audio(uid, w["hz"], lang)
    elif kind == "sk":
        for c in [c for c in w["hz"] if data.is_hanzi(c)][:3]: send_strokes(uid, c, lang)
    elif kind == "pt":
        for c in [c for c in w["hz"] if data.is_hanzi(c)][:3]: out(uid, fmt.parts_text(c, lang, el(uid)))
    elif kind == "sy": out(uid, fmt.story_text(w, lang, el(uid)))
    elif kind == "mx":
        ss = data.sentences(w["hz"]); e = el(uid)
        if not ss: out(uid, tr(lang, "word_none")); return
        from pypinyin import pinyin, Style
        lines = []
        for s in ss:
            pyx = " ".join(x[0] for x in pinyin(s["zh"], style=Style.TONE)); trn = s["de"] if e == "de" and s.get("de") else s["en"]
            lines.append(f"{esc(s['zh'])}\n<i>{esc(pyx)}</i>\n{esc(trn)}")
        out(uid, "📝\n\n" + "\n\n".join(lines) + "\n\n<i>Tatoeba (CC BY 2.0 FR)</i>")

# ---------------------------------------------------------------- today
def today(uid, mid=None):
    lang = ul(uid); u = logic.get_user(uid); st = logic.today_stats(uid); nt = logic.new_word_target(u); due = srs.due_count(uid)
    day = logic.local_day(u["tz"]); dnum = datetime.date.fromisoformat(day).toordinal()
    done_new = st["new_words"] >= nt; done_pr = st["answers"] >= u["daily_goal"]
    mark = lambda ok: "✅" if ok else "⬜"
    text = tr(lang, "today", date=day, l1=mark(done_new), nw=num(lang, st["new_words"]), nwt=num(lang, nt), l2=mark(due == 0), due=num(lang, due),
              l3=mark(done_pr), pr=num(lang, st["answers"]), prt=num(lang, u["daily_goal"]), streak=num(lang, logic.streak_alive(uid)))
    cl = db.q("SELECT * FROM custom WHERE kind='lesson' AND enabled=1 ORDER BY id")
    if cl:
        d = json.loads(cl[dnum % len(cl)]["data"]); text += f"\n\n📌 <b>{esc(d['title'])}</b>\n{esc(d['body'])}"
    if done_new and done_pr and due == 0: text += "\n\n" + tr(lang, "today_done")
    tip = fmt.daily_tip(dnum, lang, el(uid)) if logic.target(uid) == "zh" else uix.daily_tip(dnum, logic.target(uid), el(uid))
    text += "\n\n" + tr(lang, "tip_head") + "\n" + (tip or "")
    rows = [[btn(tr(lang, "b_t_new"), "m:learn"), btn(tr(lang, "b_t_rev", n=num(lang, due)), "m:review")],
            [btn(tr(lang, "b_t_prac"), "m:quiz"), btn(tr(lang, "b_progress"), "m:progress")], menu_row(lang)]
    edit(uid, mid, text[:4000], kb(rows))

# ---------------------------------------------------------------- review (flashcards)
def review_start(uid, mid=None, only_wids=None):
    lang = ul(uid)
    cards = srs.due_cards(uid, 20) if only_wids is None else [{"wid": w} for w in only_wids]
    if not cards:
        edit(uid, mid, tr(lang, "review_none"), kb([[btn(tr(lang, "b_learn"), "m:learn")], menu_row(lang)])); return
    set_sess(uid, {"mode": "review", "q": [c["wid"] for c in cards], "n": 0, "ok": 0, "show": False})
    review_card(uid, mid)

def review_card(uid, mid=None, reveal=False):
    lang = ul(uid); s = get_sess(uid)
    if s.get("mode") != "review": return
    if not s["q"]:
        boxes = srs.box_counts(uid); bt = " ".join(f"{b}:{num(lang, n)}" for b, n in boxes.items())
        set_sess(uid, {}); edit(uid, mid, tr(lang, "review_done", n=num(lang, s["n"]), boxes=bt), kb([[btn(tr(lang, "b_today"), "m:today")], menu_row(lang)])); return
    w = logic.get_word(s["q"][0])
    if not w: s["q"].pop(0); set_sess(uid, s); return review_card(uid, mid)
    c = srs.get_card(uid, w["i"]) or {"box": 1}
    if not reveal:
        text = tr(lang, "review_front", left=num(lang, len(s["q"])), box=num(lang, c["box"]), hz=f"<b>{esc(w['hz'])}</b>")
        rows = [[btn(tr(lang, "b_hear"), f"hr:{w['i']}"), btn(tr(lang, "b_show"), "rv:show")], [btn(tr(lang, "b_stop"), "rv:stop")]]
    else:
        text = tr(lang, "review_front", left=num(lang, len(s["q"])), box=num(lang, c["box"]), hz=f"<b>{esc(w['hz'])}</b>").split("\n\n")[0] + "\n\n" + fmt.word_card(w, lang, el(uid))
        rows = [[btn(tr(lang, "b_hear"), f"hr:{w['i']}"), btn(tr(lang, "b_story"), f"sy:{w['i']}")], [btn(tr(lang, "b_know"), "rv:y"), btn(tr(lang, "b_dontknow"), "rv:n")]]
        if logic.get_user(uid)["srs_mode"] == "sm2":
            rows = [[btn(tr(lang, "b_hear"), f"hr:{w['i']}")], [btn("😣 1", "rv:q1"), btn("😕 3", "rv:q3"), btn("🙂 4", "rv:q4"), btn("😎 5", "rv:q5")]]
    edit(uid, mid, text, kb(rows))

def review_answer(uid, mid, correct, quality=None):
    lang = ul(uid); s = get_sess(uid)
    if s.get("mode") != "review" or not s.get("q"): return
    wid = s["q"].pop(0); u = logic.get_user(uid)
    c = srs.review(uid, wid, correct, u["srs_mode"], quality)
    logic.record_answer(uid, correct, xp=5 if correct else 1)
    if not correct:
        w = logic.get_word(wid); logic.add_mistake(uid, wid, "review", "?", w["hz"] if w else "")
        s["q"].append(wid) if len(s["q"]) < 25 and s["q"].count(wid) < 1 and False else None
    s["n"] += 1; s["ok"] += int(correct); set_sess(uid, s)
    secs = max(0, c["due"] - db.now())
    out(uid, tr(lang, "box_moved", b=num(lang, c["box"]), when=fmt.fmt_when(lang, secs)))
    review_card(uid, None)

# ---------------------------------------------------------------- exercises
def quiz_menu(uid, mid=None):
    lang = ul(uid); tl = logic.target(uid)
    if tl != "zh":
        rows = [[btn("🎲 " + tr(lang, "b_quiz"), "qz:mix")], [btn(tr(lang, "cx_mock"), "mock:start")], [btn(tr(lang, "b_mistakes"), "ms:list")],
                [btn(tr(lang, "m_dictation"), "qz:listen"), btn(tr(lang, "m_building"), "qz:build")],
                [btn(tr(lang, "m_cloze"), "qz:cloze"), btn(tr(lang, "m_matching"), "qz:match")],
                [btn({"de": "🔤 der/die/das", "ru": "🔤 Ударение"}[tl], "qz:" + ("art" if tl == "de" else "stress")),
                 btn({"fa": "📐 دستور (حالت‌ها)", "en": "📐 Grammar drills", "de": "📐 Grammatik"}[lang], "qz:drill")],
                [btn(tr(lang, "b_a_practice"), "qz:snd"), btn(tr(lang, "m_flashcards"), "m:review")], menu_row(lang)]
        edit(uid, mid, "🧠 <b>" + tr(lang, "b_quiz").replace("🧠 ", "") + "</b> — " + langs.label(tl, lang), kb(rows)); return
    rows = [[btn("🎲 " + tr(lang, "b_quiz"), "qz:mix")], [btn(tr(lang, "m_mock"), "mock:start")],
            [btn(tr(lang, "b_mistakes"), "ms:list")],
            [btn(tr(lang, "m_dictation"), "qz:listen"), btn(tr(lang, "m_pinyin"), "qz:pytype")],
            [btn(tr(lang, "m_building"), "qz:build"), btn(tr(lang, "m_cloze"), "qz:cloze")],
            [btn(tr(lang, "m_matching"), "qz:match"), btn(tr(lang, "m_radicals"), "qz:radical")],
            [btn(tr(lang, "m_strokes"), "qz:strokes"), btn(tr(lang, "m_shadowing"), "sh:start")],
            [btn(tr(lang, "b_a_practice"), "qz:snd"), btn(tr(lang, "m_flashcards"), "m:review")],
            menu_row(lang)]
    edit(uid, mid, tr(lang, "b_quiz") + "\n" + tr(lang, "methods_head").split("\n")[0] if False else "🧠 <b>" + tr(lang, "b_quiz").replace("🧠 ", "") + "</b>", kb(rows))

def start_quiz(uid, kind, mid=None, total=8, mode="quiz", wids=None):
    s = {"mode": mode, "kind": kind, "n": 0, "ok": 0, "xp": 0, "total": total, "wq": wids or []}
    set_sess(uid, s); next_exercise(uid, mid)

def next_exercise(uid, mid=None):
    lang = ul(uid); s = get_sess(uid)
    if s.get("mode") not in QMODES: return
    if s["n"] >= s["total"]:
        return finish_quiz(uid, mid)
    if s["mode"] in ("course", "place"):
        import course; ex = course.make_ex(uid, s)
    else:
        kind = s.get("kind"); kind = None if kind in ("mix", None) else kind
        word = None
        if s.get("wq"):
            word = logic.get_word(s["wq"].pop(0))
        if s["mode"] == "mock":
            kind = random.choice(["zh2m", "m2zh", "recog", "tone", "cloze", "pytype", "fa2zh", "listen"]) if logic.target(uid) == "zh" else random.choice(["zh2m", "m2zh", "cloze", "x_type", "listen", "x_dict", None])
        if kind == "snd":
            kind = random.choice(["snd_init", "snd_final", "snd_tone"])
        ex = X.make_exercise(uid, kind, word=word)
    s["ex"] = ex; s["n"] += 1; s["answered"] = False; set_sess(uid, s)
    send_exercise(uid, ex, s["n"], s["total"], mid)

def exercise_markup(ex, lang):
    t = ex["t"]; rows = []
    if "opts" in ex and t not in ("build",):
        per = ex.get("row") or (2 if max(len(str(o)) for o in ex["opts"]) > 6 else 4)
        if len(ex["opts"]) == 4 and per == 4 and max(len(str(o)) for o in ex["opts"]) > 3: per = 2
        rows = grid([btn(str(o), f"x:{i}") for i, o in enumerate(ex["opts"])], per)
    elif t == "build":
        picked = set(ex["picked"])
        rows = grid([btn(ex["toks"][i], f"b:{i}") for i in ex["order"] if i not in picked], 3)
        rows.append([btn("↩️", "b:u"), btn("✅", "b:c")])
    elif t == "match":
        L_ = [btn(("✅ " if i in ex["done"] else ("▶️ " if ex["sel"] == i else "")) + ex["left"][i], f"mt:L{i}") for i in range(len(ex["left"]))]
        done_r = {ex["map"].index(i) for i in ex["done"]}
        R_ = [btn(("✅ " if j in done_r else "") + ex["right"][j], f"mt:R{j}") for j in range(len(ex["right"]))]
        rows = grid(L_, 2) + grid(R_, 1)
    ctl = [btn(tr(lang, "b_skip"), "q:skip"), btn(tr(lang, "b_stop"), "q:stop")]
    if ex.get("audio") or ex.get("prebuilt"): ctl.insert(0, btn(tr(lang, "b_hear"), "q:hear"))
    rows.append(ctl)
    return kb(rows)

def send_exercise(uid, ex, n, total, mid=None):
    lang = ul(uid); head = tr(lang, "quiz_head", i=f"{num(lang, n)}/{num(lang, total)}")
    text = head + "\n\n" + ex["text"]
    if ex["t"] == "build":
        text = head + "\n\n" + ex["text"].replace("<b></b>", f"<b>{esc(ex.get('sep', '').join(ex['toks'][i] for i in ex['picked'])) or '…'}</b>")
    if ex.get("audio") or ex.get("prebuilt"):
        if ex.get("prebuilt"): send_prebuilt(uid, ex["prebuilt"], "")
        else: send_audio_quiet(uid, ex["audio"])
    if ex["t"] in X.TEXT_TYPES: logic.set_await(uid, "ans")
    else: logic.set_await(uid, None)
    send(uid, rtl(lang, text), exercise_markup(ex, lang))

def send_audio_quiet(uid, text):
    b, kind = tts.audio_bytes(text, tts_hint(uid))
    if not b: return False
    if kind == "voice": C.send_voice(uid, b)
    else: _send_audio_file(uid, b, "")
    return True

def refresh_exercise(uid, mid, s):
    ex = s["ex"]; lang = ul(uid); head = tr(lang, "quiz_head", i=f"{num(lang, s['n'])}/{num(lang, s['total'])}")
    text = head + "\n\n" + ex["text"]
    if ex["t"] == "build":
        text = head + "\n\n" + ex["text"].replace("<b></b>", f"<b>{esc(ex.get('sep', '').join(ex['toks'][i] for i in ex['picked'])) or '…'}</b>")
    edit(uid, mid, text, exercise_markup(ex, lang))

def feedback_text(res, lang, xp):
    parts = []
    if res["ok"]: parts.append(tr(lang, "almost_head" if res.get("almost") else "ok_head", xp=num(lang, xp)))
    else: parts.append(tr(lang, "bad_head"))
    if res.get("given") not in (None, "") and not res["ok"]: parts.append(tr(lang, "your_answer", a=esc(res["given"])))
    if not res["ok"] and res.get("right") is not None: parts.append(tr(lang, "right_answer", a=esc(res["right"])))
    elif res["ok"] and res["word"] is not None: parts.append(X.word_line(res["word"], lang))
    parts += res.get("lines", [])
    return "\n".join(parts)

def apply_result(uid, mid, res, ex):
    """Record progress, show feedback + next/stop buttons."""
    lang = ul(uid); s = get_sess(uid)
    if s.get("answered"): return
    s["answered"] = True
    xp = logic.record_answer(uid, res["ok"], xp=(10 if res["ok"] and not res.get("almost") else (6 if res["ok"] else 2)))
    if ex.get("wid") is not None:
        u = logic.get_user(uid)
        srs.review(uid, ex["wid"], res["ok"], u["srs_mode"])
        if not res["ok"]: logic.add_mistake(uid, ex["wid"], ex["t"], res.get("given"), res.get("right"))
    s["ok"] += int(res["ok"]); s["xp"] += xp; set_sess(uid, s); logic.set_await(uid, None)
    if s.get("mode") in ("course", "place"):
        import course; course.on_answer(uid, s, res["ok"])
    last = s["n"] >= s["total"]
    rows = [[btn(tr(lang, "b_hear"), f"hr:{ex['wid']}")]] if ex.get("wid") is not None else []
    rows.append([btn(tr(lang, "b_next") if not last else "🏁", "q:next"), btn(tr(lang, "b_stop"), "q:stop")])
    send(uid, rtl(lang, feedback_text(res, lang, xp)), kb(rows))

def finish_quiz(uid, mid=None):
    lang = ul(uid); s = get_sess(uid)
    if s.get("mode") in ("course", "place"):
        import course; return course.finish(uid, s, mid)
    if s.get("mode") not in ("quiz", "mock") or not s.get("n"):
        clear_sess(uid); logic.set_await(uid, None); edit(uid, mid, tr(lang, "menu_title"), main_menu(lang, uid)); return
    done = s["n"] - (0 if s.get("answered") else 1)
    done = max(done, 0)
    if s["mode"] == "mock":
        pct = round(100 * s["ok"] / max(1, s["total"]))
        grade = tr(lang, "grade_hi" if pct >= 80 else "grade_mid" if pct >= 50 else "grade_lo")
        if logic.target(uid) == "zh": text = tr(lang, "mock_done", lv=logic.get_user(uid)["level"] or 1, ok=num(lang, s["ok"]), n=num(lang, s["total"]), pct=num(lang, pct), grade=grade)
        else: text = tr(lang, "cx_mock_done", lv=uix.level_text(uid, lang, max(1, logic.get_user(uid)["level"])), ok=num(lang, s["ok"]), n=num(lang, s["total"]), pct=num(lang, pct), grade=grade)
    else:
        text = tr(lang, "q_done", ok=num(lang, s["ok"]), n=num(lang, done), xp=num(lang, s["xp"]))
    clear_sess(uid); logic.set_await(uid, None)
    rows = [[btn(tr(lang, "b_again"), "m:quiz"), btn(tr(lang, "b_mistakes"), "ms:list")], menu_row(lang)]
    send(uid, rtl(lang, text), kb(rows))

def on_choice(uid, mid, idx):
    s = get_sess(uid); ex = s.get("ex")
    if s.get("mode") not in QMODES or not ex or s.get("answered"): 
        if not ex: out(uid, tr(ul(uid), "no_session"))
        return
    res = X.check_choice(ex, idx); apply_result(uid, mid, res, ex)

def on_text_answer(uid, text):
    s = get_sess(uid); ex = s.get("ex")
    if s.get("mode") not in QMODES or not ex or s.get("answered") or ex["t"] not in X.TEXT_TYPES:
        logic.set_await(uid, None); return False
    res = X.check_text(ex, text, uid); apply_result(uid, None, res, ex); return True

def on_build(uid, mid, key):
    s = get_sess(uid); ex = s.get("ex")
    if not ex or ex["t"] != "build" or s.get("answered"): return
    if key == "u":
        if ex["picked"]: ex["picked"].pop()
    elif key == "c":
        if not ex["picked"]: return
        res = X.check_build(ex); apply_result(uid, mid, res, ex); return
    elif key.isdigit() and int(key) not in ex["picked"]:
        ex["picked"].append(int(key))
        if len(ex["picked"]) == len(ex["toks"]):
            set_sess(uid, s); res = X.check_build(ex); apply_result(uid, mid, res, ex); return
    set_sess(uid, s); refresh_exercise(uid, mid, s)

def on_match(uid, mid, key):
    s = get_sess(uid); ex = s.get("ex"); lang = ul(uid)
    if not ex or ex["t"] != "match" or s.get("answered"): return
    side, i = key[0], int(key[1:])
    if side == "L":
        if i in ex["done"]: return
        ex["sel"] = i
    else:
        if ex["sel"] is None: return
        li = ex["sel"]
        if ex["map"][li] == i or ex["right"][i] == ex["right"][ex["map"].index(li)] if False else ex["map"][i] == li:
            pass
        correct = (ex["map"][i] == li)
        if correct:
            ex["done"].append(li); ex["sel"] = None
        else:
            ex["errs"] += 1; ex["sel"] = None
    set_sess(uid, s)
    if len(ex["done"]) == len(ex["left"]):
        res = X.result(ex["errs"] == 0, lang, right=None, lines=[tr(lang, "match_done", n=num(lang, ex["errs"]))] + [f"{ex['left'][k]} = {ex['right'][ex['map'].index(k)]}" for k in range(len(ex['left']))])
        res["ok"] = ex["errs"] <= 1
        for wid in ex["wids"]:
            u = logic.get_user(uid); srs.review(uid, wid, ex["errs"] == 0, u["srs_mode"])
        s["answered"] = False; set_sess(uid, s)
        apply_result(uid, mid, dict(res, word=None, right=None), dict(ex, wid=None)); return
    refresh_exercise(uid, mid, s)

def quiz_ctl(uid, mid, op):
    s = get_sess(uid); lang = ul(uid)
    if op == "next": next_exercise(uid, None)
    elif op == "skip":
        if s.get("ex") and not s.get("answered"):
            ex = s["ex"]; w = logic.get_word(ex["wid"]) if ex.get("wid") is not None else None
            if w: logic.add_mistake(uid, w["i"], ex["t"], "—", w["hz"])
            s["answered"] = True; s["n"] = s["n"]; set_sess(uid, s)
            if s.get("mode") in ("course", "place"):
                import course; course.on_answer(uid, s, False)
        next_exercise(uid, None)
    elif op == "stop": finish_quiz(uid, None)
    elif op == "hear":
        ex = s.get("ex") or {}
        if ex.get("prebuilt"): send_prebuilt(uid, ex["prebuilt"])
        elif ex.get("audio"): send_audio_quiet(uid, ex["audio"])

def mistakes_list(uid, mid=None):
    lang = ul(uid); rows_ = db.q("SELECT * FROM mistakes WHERE user_id=? AND resolved=0 AND wid IS NOT NULL ORDER BY id DESC LIMIT 40", (uid,))
    seen = []; items = []
    for r in rows_:
        if r["wid"] in seen: continue
        seen.append(r["wid"]); w = logic.get_word(r["wid"])
        if w: items.append((w, r))
        if len(items) >= 6: break
    if not items:
        edit(uid, mid, tr(lang, "mistakes_none"), kb([menu_row(lang)])); return
    lines = [tr(lang, "mistakes_head")]
    for w, r in items:
        lines.append(tr(lang, "mistake_line", hz=esc(w["hz"]), py=esc(w["py"]), mean=esc(X.meaning(w, el(uid))[0]), given=esc(r["given"] or "—"), exp=esc(r["expected"] or w["hz"])))
    rows = [[btn(tr(lang, "b_quiz"), "ms:practice"), btn(tr(lang, "b_review"), "ms:review")], menu_row(lang)]
    edit(uid, mid, "\n\n".join(lines), kb(rows))
    set_sess(uid, dict(get_sess(uid), mistakes=[w["i"] for w, _ in items]))

def mistakes_practice(uid, mid=None, review=False):
    ids = [r["wid"] for r in db.q("SELECT DISTINCT wid FROM mistakes WHERE user_id=? AND resolved=0 AND wid IS NOT NULL ORDER BY id DESC LIMIT 8", (uid,))]
    if not ids: return mistakes_list(uid, mid)
    if review: return review_start(uid, mid, ids)
    start_quiz(uid, "mix", mid, total=len(ids), wids=list(ids))
    db.ex("UPDATE mistakes SET resolved=1 WHERE user_id=? AND wid IN (%s)" % ",".join("?" * len(ids)), (uid, *ids))

def mock_start(uid, mid=None):
    lang = ul(uid); lv = max(1, logic.get_user(uid)["level"])
    out(uid, tr(lang, "mock_intro", lv=lv) if logic.target(uid) == "zh" else tr(lang, "cx_mock_intro", lv=uix.level_text(uid, lang, lv))); start_quiz(uid, "mock", None, total=10, mode="mock")

# ---------------------------------------------------------------- shadowing
def shadow_start(uid, mid=None):
    if logic.target(uid) != "zh": return out(uid, tr(ul(uid), "zh_only"), kb([menu_row(ul(uid))]))
    lang = ul(uid); u = logic.get_user(uid); pool = [w for w in logic.pool(max(1, u["level"])) if data.sentences(w["hz"])]
    w = random.choice(pool); ss = [s for s in data.sentences(w["hz"]) if all(data.is_hanzi(c) or c in "，。！？、" for c in s["zh"])] or data.sentences(w["hz"])
    s_ = random.choice(ss); from pypinyin import pinyin, Style
    py = " ".join(x[0] for x in pinyin(s_["zh"], style=Style.TONE)); e = el(uid); trn = s_["de"] if e == "de" and s_.get("de") else s_["en"]
    set_sess(uid, {"mode": "shadow", "zh": s_["zh"], "py": py})
    logic.set_await(uid, "voice")
    send_audio_quiet(uid, s_["zh"])
    out(uid, tr(lang, "q_shadow", zh=esc(s_["zh"]), py=esc(py), tr=esc(trn)), kb([[btn(tr(lang, "b_hear"), "sh:hear"), btn(tr(lang, "b_next"), "sh:start")], menu_row(lang)]))

def on_voice(uid, msg):
    lang = ul(uid); s = get_sess(uid)
    if s.get("mode") != "shadow": out(uid, tr(lang, "unknown_cmd"), main_menu(lang, uid)); return
    stt_ok = llm.configured() and llm.settings()["stt_model"]
    if not stt_ok:
        out(uid, tr(lang, "shadow_nostt", py=esc(s["py"]))); return
    v = msg.get("voice") or msg.get("audio") or {}
    try:
        info = C.call("getFile", {"file_id": v["file_id"]}, timeout=30)
        r = C.sess.get(f"https://api.telegram.org/file/bot{C.TOKEN}/{info['file_path']}", timeout=60); b = r.content
    except Exception as e:
        log.warning("voice download failed: %s", C.safe(e)[:60]); out(uid, tr(lang, "unexpected")); return
    if not llm.allow(uid): out(uid, tr(lang, "ask_limit")); return
    llm.count(uid); heard = llm.transcribe(b)
    if heard is None: out(uid, tr(lang, "shadow_nostt", py=esc(s["py"]))); return
    from pypinyin import lazy_pinyin
    a = "".join(lazy_pinyin(re.sub(r"[^\u4e00-\u9fff]", "", heard))); t = "".join(lazy_pinyin(re.sub(r"[^\u4e00-\u9fff]", "", s["zh"])))
    import difflib
    good = difflib.SequenceMatcher(None, a, t).ratio() >= 0.85
    logic.record_answer(uid, good, xp=8 if good else 2)
    out(uid, tr(lang, "shadow_res", heard=esc(heard), target=esc(s["zh"]), verdict=tr(lang, "shadow_good" if good else "shadow_diff")), kb([[btn(tr(lang, "b_next"), "sh:start")], menu_row(lang)]))

# ---------------------------------------------------------------- dictionary / ask
def dict_prompt(uid, mid=None):
    lang = ul(uid); logic.set_await(uid, "dict")
    edit(uid, mid, tr(lang, "dict_prompt"), kb([menu_row(lang)]))

def dictionary_html(q, lang, elang, personal_uid=None):
    """-> (html, markup_rows, first_hanzi) ; html None when nothing was found."""
    if not data.available(): return tr(lang, "dict_nodata"), [], None
    q = (q or "").strip()[:60]
    entries = []; kind = None
    if data.has_hanzi(q):
        h = "".join(c for c in q if data.is_hanzi(c) or c in "，。！？")
        entries = data.lookup_hanzi(re.sub(r"[，。！？\s]", "", q)); kind = "zh"
    else:
        qq = textnorm.norm_latin(q); det = textnorm.detect_lang(q)
        if det == "fa":
            ws = data.search_persian(q); kind = "fa"
            for w in ws:
                hits = [e for e in data.lookup_hanzi(w["hz"]) if e["py"].replace(" ", "").lower() == w["py"].replace(" ", "").lower()] or data.lookup_hanzi(w["hz"])[:1]
                entries += hits[:1]
        else:
            parsed = P.parse(q); valid = bool(parsed) and all(b in P.syllables() for b, _ in parsed) and len(q) <= 24
            if valid and (any(c in q for c in "1234āáǎàēéěèīíǐìōóǒòūúǔù") or " " not in q.strip()):
                entries += data.search_pinyin(parsed, 5); kind = "py"
            if det == "de" or re.search(r"[äöüß]", q.lower()):
                entries += data.search_german(q, 6); kind = kind or "de"
            if len(entries) < 4:
                entries += data.search_english(q, 6); kind = kind or "en"
            if not entries and det != "de": entries += data.search_german(q, 4)
    seen = set(); uniq = []
    for e in entries:
        k = (e["simp"], e["py_num"])
        if k not in seen: seen.add(k); uniq.append(e)
    entries = uniq
    if not entries and data.has_hanzi(q):
        toks = [t for t in data.segment(re.sub(r"\s", "", q)) if data.has_hanzi(t)]
        if len(toks) > 1:
            blocks = []
            for t in toks[:8]:
                es = data.lookup_hanzi(t, 1)
                if es: blocks.append(fmt.entry_text(es[0], lang, elang))
            if blocks: return tr(lang, "seg_head") + "\n\n" + "\n\n".join(blocks)[:3500], [], toks[0]
    if not entries: return None, [], None
    shown = entries[:4]
    body = "\n\n".join(fmt.entry_text(e, lang, elang) for e in shown)
    if len(entries) > 4: body += "\n\n" + tr(lang, "dict_more", n=num(lang, len(entries) - 4))
    first = shown[0]["simp"]
    chars = [c for c in first if data.is_hanzi(c)][:4]
    if chars and data.available():
        body += tr(lang, "dict_chars", chars="\n".join(fmt.char_line(c, elang) for c in chars))
    body += tr(lang, "dict_credit")
    return body[:4000], [first], first

def dict_markup(first, lang):
    if not first or len(first.encode()) > 40: return kb([menu_row(lang)])
    rows = [[btn(tr(lang, "b_hear"), f"hz:{first}")]]
    if any(data.is_hanzi(c) for c in first):
        rows.append([btn(tr(lang, "b_strokes"), f"sc:{first}"), btn(tr(lang, "b_parts"), f"pc:{first}")])
    rows.append(menu_row(lang)); return kb(rows)

def do_dict(uid, q, lang=None, elang=None):
    if logic.target(uid) != "zh": return uix.do_dict(uid, q)
    lang = lang or ul(uid); elang = elang or el(uid)
    html, _, first = dictionary_html(q, lang, elang)
    if html is None:
        if llm.configured() and llm.allow(uid): return do_ask(uid, q)
        out(uid, tr(lang, "dict_none", q=esc(q[:40])), kb([[btn(tr(lang, "b_ask"), "m:ask")], menu_row(lang)])); return
    out(uid, html, dict_markup(first, lang))

_ASK_STOP = {"wie", "was", "warum", "welche", "lerne", "lernen", "chinesisch", "chinese", "mandarin", "learn", "how", "what", "why", "say", "word", "mean", "means", "meaning", "translate",
             "چیست", "چیه", "یعنی", "چطور", "چگونه", "چرا", "معنی", "ترجمه", "چینی", "زبان", "بگم", "بگویم", "میشه", "می‌شود", "کلمه", "واژه"}

def grammar_matches(q):
    ql = q.lower(); res = []
    toks = set(re.findall(r"[a-zäöüß]+", ql))
    for g in L.GRAMMAR:
        score = 0
        for k in g[1]:
            k = k.lower()
            if k.isascii() and k.replace(" ", "").isalpha() and " " not in k:
                score += k in toks          # ASCII keywords must match whole words ("le" must not match "lerne")
            else:
                score += k in ql
        if score: res.append((score, g[0]))
    res.sort(reverse=True); return [gid for _, gid in res[:2]]

def ask_answer(q, lang, elang, uid=None, use_llm=True, note=None):
    """Answer a free-text question. -> html. Uses the LLM when configured, else rule-based notes + dictionary."""
    q = q.strip()[:500]
    ctx = []
    toks = [t for t in data.segment(re.sub(r"[^\u4e00-\u9fff]", " ", q).replace("  ", " ")) if data.has_hanzi(t)] if data.has_hanzi(q) and data.available() else []
    for t in toks[:6]:
        es = data.lookup_hanzi(t, 1)
        if es: ctx.append(f"{t} [{es[0]['py']}]: {'; '.join(es[0]['defs'][:2])}")
    if use_llm and llm.configured():
        if uid is not None and not llm.allow(uid): return tr(lang, "ask_limit")
        if uid is not None: llm.count(uid)
        user = q + ("\n\nDictionary hints:\n" + "\n".join(ctx) if ctx else "")
        ans = llm.chat(llm.teacher_system(elang), user, max_tokens=500)
        if ans: return "🤖 " + esc(ans)[:3800]
    parts = [tr(lang, "ask_nollm") if note is None else note]
    gm = grammar_matches(q)
    for gid in gm: parts.append(fmt.grammar_page(gid, lang, elang))
    if toks:
        blocks = []
        for t in toks[:4]:
            es = data.lookup_hanzi(t, 1)
            if es: blocks.append(fmt.entry_text(es[0], lang, elang))
        if blocks: parts.append(tr(lang, "seg_head") + "\n\n" + "\n\n".join(blocks))
    elif not gm:
        w = re.sub(r"[?؟!.,،]", " ", q).split()
        stop = textnorm._DE_WORDS | textnorm._EN_WORDS | _ASK_STOP
        for t in [x for x in w if x.lower() not in stop][:6]:
            if len(t) >= 3 and data.available():
                html, _, _ = dictionary_html(t, lang, elang)
                if html and html != tr(lang, "dict_nodata"): parts.append(html); break
    if len(parts) == 1: parts.append(tr(lang, "ask_nothing"))
    return "\n\n".join(parts)[:4000]

def ask_prompt(uid, mid=None):
    lang = ul(uid); logic.set_await(uid, "ask")
    edit(uid, mid, tr(lang, "ask_prompt"), kb([menu_row(lang)]))

def do_ask(uid, q):
    lang = ul(uid); elang = el(uid)
    out(uid, ask_answer(q, lang, elang, uid) if logic.target(uid) == "zh" else uix.ask_answer(uid, q, lang, elang), kb([[btn(tr(lang, "b_ask"), "m:ask"), btn(tr(lang, "b_dict"), "m:dict")], menu_row(lang)]))

def looks_like_question(t, tl="zh"):
    t = t.strip()
    if t.endswith(("?", "؟", "？")): return True
    if data.has_hanzi(t): return len(re.sub(r"\s", "", t)) > 8 or "吗" in t and len(t) > 4
    return len(t.split()) >= 5

# ---------------------------------------------------------------- alphabet
def alpha_menu(uid, mid=None):
    if logic.target(uid) != "zh": return uix.alpha_menu(uid, mid)
    lang = ul(uid)
    rows = [[btn(tr(lang, "b_a_tones"), "al:tones"), btn(tr(lang, "b_a_init"), "al:init:0")],
            [btn(tr(lang, "b_a_final"), "al:fin:0"), btn(tr(lang, "b_a_rules"), "al:rules")],
            [btn(tr(lang, "b_a_sandhi"), "al:sandhi"), btn(tr(lang, "b_a_tips"), "al:tip:0")],
            [btn(tr(lang, "b_a_strokes"), "al:strokes"), btn(tr(lang, "b_a_radicals"), "al:rad:0")],
            [btn(tr(lang, "b_a_grammar"), "al:gram"), btn(tr(lang, "b_a_idiom"), "al:idi:0")],
            [btn(tr(lang, "b_a_culture"), "al:cul:0"), btn(tr(lang, "b_a_practice"), "qz:snd")], menu_row(lang)]
    edit(uid, mid, tr(lang, "alpha_menu"), kb(rows))

def alpha_cb(uid, mid, p):
    if p[1] in ("xl", "xr", "xg") or (p[1] == "menu" and logic.target(uid) != "zh"): return uix.alpha_cb(uid, mid, p)
    lang = ul(uid); e = el(uid); op = p[1]; back = [btn(tr(lang, "b_back"), "al:menu")]
    if op == "menu": return alpha_menu(uid, mid)
    if op == "init":
        gi = int(p[2]) % len(A.INITIAL_GROUPS); text, letters = fmt.initial_page(gi, lang, e)
        rows = grid([btn("🔊 " + l, f"al:h:i:{l}") for l in letters], 4)
        rows.append([btn("⬅️", f"al:init:{(gi - 1) % len(A.INITIAL_GROUPS)}"), btn(f"{gi + 1}/{len(A.INITIAL_GROUPS)}", "noop"), btn("➡️", f"al:init:{(gi + 1) % len(A.INITIAL_GROUPS)}")]); rows.append(back)
        edit(uid, mid, text, kb(rows))
    elif op == "fin":
        gi = int(p[2]) % len(A.FINAL_GROUPS); text, letters = fmt.final_page(gi, lang, e)
        rows = grid([btn("🔊 " + l, f"al:h:f:{l}") for l in letters if l.replace("ü", "v") in {x.replace("final_", "") for x in _prebuilt_names()}], 4)
        rows.append([btn("⬅️", f"al:fin:{(gi - 1) % len(A.FINAL_GROUPS)}"), btn(f"{gi + 1}/{len(A.FINAL_GROUPS)}", "noop"), btn("➡️", f"al:fin:{(gi + 1) % len(A.FINAL_GROUPS)}")]); rows.append(back)
        edit(uid, mid, text, kb(rows))
    elif op == "h":
        kindc, name = p[2], p[3].replace("ü", "v")
        if not send_prebuilt(uid, ("init_" if kindc == "i" else "final_") + name, name):
            hz = next((x[1] for x in (A.INITIALS if kindc == "i" else A.FINALS) if x[0].replace("ü", "v") == name), name); send_audio_quiet(uid, hz)
    elif op == "tones":
        rows = [[btn("🔊 1", "al:t:1"), btn("🔊 2", "al:t:2"), btn("🔊 3", "al:t:3"), btn("🔊 4", "al:t:4"), btn("🔊 5", "al:t:5")], [btn(tr(lang, "b_a_practice"), "qz:snd")], back]
        edit(uid, mid, fmt.tones_page(lang, e), kb(rows))
    elif op == "t": send_prebuilt(uid, f"tone_ma{p[2]}", "ma" + p[2])
    elif op == "rules": edit(uid, mid, fmt.rules_page(lang, e), kb([back]))
    elif op == "sandhi": edit(uid, mid, fmt.sandhi_page(lang, e), kb([back]))
    elif op == "strokes":
        rows = [[btn("✍️ 学", "sc:学"), btn("✍️ 人", "sc:人"), btn("✍️ 我", "sc:我"), btn("✍️ 国", "sc:国")], back]
        edit(uid, mid, fmt.strokes_page(lang, e), kb(rows))
    elif op == "rad":
        text, pg, pages = fmt.radicals_page(int(p[2]), lang, e)
        rows = [[btn("⬅️", f"al:rad:{(pg - 1) % pages}"), btn(f"{pg + 1}/{pages}", "noop"), btn("➡️", f"al:rad:{(pg + 1) % pages}")], back]
        edit(uid, mid, text, kb(rows))
    elif op == "tip":
        text, i, n = fmt.tip_page(int(p[2]), lang, e)
        edit(uid, mid, text, kb([[btn("⬅️", f"al:tip:{(i - 1) % n}"), btn(f"{i + 1}/{n}", "noop"), btn("➡️", f"al:tip:{(i + 1) % n}")], back]))
    elif op == "cul":
        text, i = fmt.culture_page(int(p[2]), lang, e); n = len(L.CULTURE)
        edit(uid, mid, text, kb([[btn("⬅️", f"al:cul:{(i - 1) % n}"), btn(f"{i + 1}/{n}", "noop"), btn("➡️", f"al:cul:{(i + 1) % n}")], back]))
    elif op == "idi":
        text, i = fmt.idiom_page(int(p[2]), lang, e); n = len(L.CHENGYU)
        edit(uid, mid, text, kb([[btn("⬅️", f"al:idi:{(i - 1) % n}"), btn(f"{i + 1}/{n}", "noop"), btn("➡️", f"al:idi:{(i + 1) % n}")], [btn(tr(lang, "b_hear"), f"hz:{L.CHENGYU[i][0]}")], back]))
    elif op == "gram":
        li = fmt.LI[e]
        rows = grid([btn(g[5][li], f"al:g:{g[0]}") for g in L.GRAMMAR], 2); rows.append(back)
        edit(uid, mid, tr(lang, "grammar_list"), kb(rows))
    elif op == "g":
        text = fmt.grammar_page(p[2], lang, e)
        if text:
            g = next(x for x in L.GRAMMAR if x[0] == p[2])
            edit(uid, mid, text, kb([[btn(tr(lang, "b_hear"), f"hz:{g[3][:12]}")], [btn(tr(lang, "b_back"), "al:gram")]]))

_PB = None
def _prebuilt_names():
    global _PB
    if _PB is None:
        import os
        d = os.path.join(config.ASSETS, "audio"); _PB = [f[:-4] for f in os.listdir(d)] if os.path.isdir(d) else []
    return _PB

# ---------------------------------------------------------------- reader
def reader_list(uid, mid=None):
    if logic.target(uid) != "zh": return out(uid, tr(ul(uid), "zh_only"), kb([menu_row(ul(uid))]))
    lang = ul(uid); lv = max(1, logic.get_user(uid)["level"]); li = {"fa": 1, "en": 2, "de": 3}[el(uid)]
    rows = [[btn(f"HSK{r[1]} · {r[2][0]} — {r[2][li]}", f"rd:{r[0]}:1:1")] for r in L.READERS if r[1] <= max(lv, 1) + (1 if lv == 0 else 0) or True]
    rows = [[btn(f"HSK{r[1]} · {r[2][0]} — {r[2][li]}", f"rd:{r[0]}:1:1")] for r in L.READERS if r[1] <= lv]
    rows.append(menu_row(lang)); edit(uid, mid, tr(lang, "reader_list"), kb(rows))

def reader_show(uid, mid, rid, py, trn):
    lang = ul(uid); text = fmt.reader_page(rid, lang, el(uid), bool(py), bool(trn))
    if not text: return
    rows = [[btn(tr(lang, "b_py_off" if py else "b_py_on"), f"rd:{rid}:{0 if py else 1}:{trn}"), btn(tr(lang, "b_tr_off" if trn else "b_tr_on"), f"rd:{rid}:{py}:{0 if trn else 1}")],
            [btn(tr(lang, "b_hear"), f"rda:{rid}")], [btn(tr(lang, "b_back"), "m:read")]]
    edit(uid, mid, text, kb(rows))

def reader_audio(uid, rid):
    r = next((x for x in L.READERS if x[0] == rid), None)
    if r: send_audio_quiet(uid, "。".join(l[0].split("：")[-1].rstrip("。") for l in r[3]) + "。")

# ---------------------------------------------------------------- progress
def progress(uid, mid=None):
    lang = ul(uid); u = logic.get_user(uid); boxes = srs.box_counts(uid); tot = u["ok"] + u["bad"]
    mist = db.val("SELECT COUNT(DISTINCT wid) FROM mistakes WHERE user_id=? AND resolved=0 AND wid IS NOT NULL", (uid,), 0)
    text = tr(lang, "progress", tl=esc(langs.label(logic.target(uid), lang)), plabel=esc(uix.progress_label(uid, lang)), level=esc(uix.level_text(uid, lang)), xp=num(lang, u["xp"]), streak=num(lang, logic.streak_alive(uid)), best=num(lang, u["best_streak"]),
              acc=num(lang, round(100 * u["ok"] / tot) if tot else 0), ok=num(lang, u["ok"]), tot=num(lang, tot), cards=num(lang, srs.total_cards(uid)), mast=num(lang, srs.mastered(uid)),
              boxes=" ".join(f"📦{b}:{num(lang, n)}" for b, n in boxes.items()),
              mist=num(lang, mist), due=num(lang, srs.due_count(uid)))
    import course; cl = course.progress_line(uid, lang)
    if cl: text += "\n\n" + cl
    rows = [[btn(tr(lang, "b_mistakes"), "ms:list"), btn(tr(lang, "b_review"), "m:review")], [btn(tr(lang, "b_course"), "m:course")], menu_row(lang)]
    edit(uid, mid, text, kb(rows))

# ---------------------------------------------------------------- settings
def settings_text(uid):
    lang = ul(uid); u = logic.get_user(uid)
    expl = tr(lang, "expl_auto") if u["expl"] == "auto" else lang_name(u["expl"])
    ms = [tr(lang, "m_" + m) for m in logic.methods_of(u)] or ["—"]
    return tr(lang, "settings", ui=lang_name(u["ui"]), expl=esc(expl), level=esc(uix.level_text(uid, lang)), goal=num(lang, u["daily_goal"]),
              srs=esc(tr(lang, "srs_" + u["srs_mode"].replace("sm2", "sm2"))), remind=u["remind"] or "⛔", tz=esc(u["tz"]), methods=esc("، ".join(ms) if lang == "fa" else ", ".join(ms)))

def settings(uid, mid=None):
    lang = ul(uid)
    rows = [[btn(tr(lang, "b_s_ui"), "st:ui"), btn(tr(lang, "b_s_expl"), "st:ex")], [btn(tr(lang, "b_s_level"), "st:lv"), btn(tr(lang, "b_s_goal"), "st:goal")],
            [btn(tr(lang, "b_s_srs"), "st:srs"), btn(tr(lang, "b_s_remind"), "st:rm")], [btn(tr(lang, "b_s_tz"), "st:tz"), btn(tr(lang, "b_s_methods"), "st:ms")],
            [btn(tr(lang, "b_s_del"), "st:del")], menu_row(lang)]
    edit(uid, mid, settings_text(uid), kb(rows))

def methods_panel(uid, mid=None):
    lang = ul(uid); on = set(logic.methods_of(logic.get_user(uid))); rows = []
    play = {"flashcards": "m:review", "mnemonic": "ln:next", "radicals": "qz:radical", "strokes": "qz:strokes", "dictation": "qz:listen", "pinyin": "qz:pytype", "building": "qz:build",
            "shadowing": "sh:start", "cloze": "qz:cloze", "matching": "qz:match", "review": "m:review", "mock": "mock:start", "reader": "m:read"}
    for m in logic.ALL_METHODS:
        rows.append([btn(("✅ " if m in on else "⬜ ") + tr(lang, "m_" + m), f"st:mt:{m}"), btn("▶️", play[m])])
    rows.append([btn(tr(lang, "b_back"), "m:settings")])
    edit(uid, mid, tr(lang, "methods_head"), kb(rows))

def settings_cb(uid, mid, p):
    lang = ul(uid); u = logic.get_user(uid); op = p[1]; back = [btn(tr(lang, "b_back"), "m:settings")]
    if op == "ui":
        if len(p) > 2:
            logic.update_user(uid, ui=p[2]); return settings(uid, mid)
        edit(uid, mid, tr(lang, "pick_ui"), kb(lang_buttons("st:ui:", lang=lang) + [back]))
    elif op == "ex":
        if len(p) > 2:
            logic.update_user(uid, expl=p[2]); return settings(uid, mid)
        edit(uid, mid, tr(lang, "pick_expl"), kb(lang_buttons("st:ex:", True, lang) + [back]))
    elif op == "lv":
        if len(p) > 2:
            if int(p[2]) in langs.levels(logic.target(uid)): logic.update_user(uid, level=int(p[2]))
            return settings(uid, mid)
        edit(uid, mid, tr(lang, "pick_level"), kb([[btn(uix.level_text(uid, lang, n), f"st:lv:{n}")] for n in langs.levels(logic.target(uid))] + [back]))
    elif op == "goal":
        if len(p) > 2:
            logic.update_user(uid, daily_goal=int(p[2])); return settings(uid, mid)
        edit(uid, mid, tr(lang, "pick_goal"), kb([[btn(num(lang, n), f"st:goal:{n}") for n in (5, 10, 20, 30, 50)], back]))
    elif op == "srs":
        if len(p) > 2:
            logic.update_user(uid, srs_mode=p[2]); return settings(uid, mid)
        edit(uid, mid, tr(lang, "srs_info"), kb([[btn(("✅ " if u["srs_mode"] == "leitner" else "") + tr(lang, "srs_leitner"), "st:srs:leitner")], [btn(("✅ " if u["srs_mode"] == "sm2" else "") + tr(lang, "srs_sm2"), "st:srs:sm2")], back]))
    elif op == "rm":
        if len(p) > 2:
            if p[2] == "n": logic.update_user(uid, remind=""); return settings(uid, mid)
            if p[2] == "c":
                logic.set_await(uid, "remind"); edit(uid, mid, tr(lang, "remind_type"), kb([back])); return
            t = p[2] + ":" + p[3]
            if logic.hhmm_ok(t): logic.update_user(uid, remind=t, last_remind=logic.local_day(u["tz"]))
            return settings(uid, mid)
        times = ["07:00", "09:00", "13:00", "18:00", "20:00", "22:00"]
        rows = grid([btn(t, "st:rm:" + t) for t in times], 3) + [[btn(tr(lang, "b_remind_custom"), "st:rm:c"), btn(tr(lang, "b_off"), "st:rm:n")], back]
        edit(uid, mid, tr(lang, "pick_remind"), kb(rows))
    elif op == "tz":
        if len(p) > 2:
            tzname = "/".join(p[2:]).replace("~", "/") if False else config.TIMEZONES[int(p[2])]
            logic.update_user(uid, tz=tzname); return settings(uid, mid)
        edit(uid, mid, tr(lang, "pick_tz"), kb(grid([btn(z, f"st:tz:{i}") for i, z in enumerate(config.TIMEZONES)], 2) + [back]))
    elif op == "ms":
        if len(p) > 3 and p[2] == "mt": pass
        methods_panel(uid, mid)
    elif op == "mt":
        logic.toggle_method(uid, p[2]); methods_panel(uid, mid)
    elif op == "del":
        if len(p) > 2 and p[2] == "y":
            for t in ("cards", "mistakes", "daily", "sess", "course", "ulang"): db.ex(f"DELETE FROM {t} WHERE user_id=?", (uid,))
            db.ex("DELETE FROM activity WHERE user_id=?", (uid,)); db.ex("DELETE FROM gscores WHERE user_id=?", (uid,))
            db.ex("DELETE FROM users WHERE id=?", (uid,))
            send(uid, tr(lang, "del_done")); return
        edit(uid, mid, tr(lang, "del_ask"), kb([[btn(tr(lang, "b_yes"), "st:del:y"), btn(tr(lang, "b_no"), "m:settings")]]))

def on_remind_text(uid, text):
    lang = ul(uid); t = C.norm_digits(text).strip()
    if re.fullmatch(r"\d:\d\d", t): t = "0" + t
    if not logic.hhmm_ok(t): out(uid, tr(lang, "bad_time")); return
    logic.update_user(uid, remind=t, last_remind=logic.local_day(logic.get_user(uid)["tz"])); logic.set_await(uid, None)
    out(uid, tr(lang, "remind_set", t=t, tz=esc(logic.get_user(uid)["tz"])), kb([menu_row(lang)]))
