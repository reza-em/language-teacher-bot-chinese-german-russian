"""Telegram-facing screens for the multi-language edition: language switching, German/Russian alphabet & sound screens, dictionary, ask, tips.
(The Chinese screens stay in ui.py; this module is only used when the learner's target language is not Chinese, plus the /lang menu.)"""
import re, random
import config, db, logic, langs, xlang, fmt
import curriculum_x as CX
import lesson_content_x as LX
from core import btn, kb, grid, esc, rtl, num
from texts import tr

IDX = {"fa": 0, "en": 1, "de": 1}
def _pk(tup, el): return tup[IDX.get(el, 1)]

def _ui():
    import ui; return ui

# ---------------------------------------------------------------- language menu / switching
def target_buttons(prefix, lang, current=None, studied=()):
    rows = []
    for l in langs.CODES:
        mark = "✅ " if l == current else ""
        rows.append([btn(mark + langs.label(l, lang), prefix + l)])
    return rows

def lang_menu(uid, mid=None):
    ui = _ui(); lang = ui.ul(uid); cur = logic.target(uid)
    text = tr(lang, "lang_menu", cur=esc(langs.label(cur, lang))) + "\n\n" + tr(lang, "cx_gloss_note")
    rows = target_buttons("lg:", lang, cur) + [ui.menu_row(lang)]
    ui.edit(uid, mid, text, kb(rows))

def lang_cb(uid, mid, p):
    ui = _ui(); lang = ui.ul(uid)
    if len(p) < 2 or p[1] == "menu": return lang_menu(uid, mid)
    code = p[1]
    if code not in langs.CODES: return lang_menu(uid, mid)
    known = code in logic.user_langs(uid)
    logic.set_target(uid, code); logic.set_await(uid, None)
    import course
    cur = esc(langs.label(code, lang))
    if known:
        ui.edit(uid, mid, tr(lang, "lang_switched", cur=cur), ui.main_menu(lang, uid))
    else:
        ui.edit(uid, mid, tr(lang, "lang_switched", cur=cur) + "\n\n" + tr(lang, "lang_new_hint"), kb([[btn("➡️", "c:hub")]]))
        course.path_menu(uid, None)

def level_text(uid, lang, n=None):
    """Human label of the learner's level in the active language."""
    tl = logic.target(uid); n = logic.get_user(uid)["level"] if n is None else n
    if tl == "zh": return tr(lang, f"lvl_{n}")
    return tr(lang, f"cx_lvl_{min(max(n, 0), 2)}")

def progress_label(uid, lang):
    tl = logic.target(uid)
    if tl == "zh":
        pr = [logic.level_progress(uid, lv) for lv in (1, 2, 3)]
        return " • ".join(f"HSK {i + 1}: {num(lang, a)}/{num(lang, b)}" for i, (a, b) in enumerate(pr))
    pr = [logic.level_progress(uid, lv) for lv in (1, 2)]
    return f"A1: {num(lang, pr[0][0])}/{num(lang, pr[0][1])} • A2: {num(lang, pr[1][0])}/{num(lang, pr[1][1])}"

# ---------------------------------------------------------------- alphabet / sounds
def alpha_menu(uid, mid=None):
    ui = _ui(); lang = ui.ul(uid); L = logic.target(uid)
    if L == "ru":
        rows = [[btn(tr(lang, "cx_b_letters"), "al:xl:0"), btn(tr(lang, "cx_b_rules"), "al:xr:0")], [btn(tr(lang, "b_a_practice"), "qz:snd"), btn(tr(lang, "b_a_grammar"), "al:xg:0")], ui.menu_row(lang)]
    else:
        rows = [[btn(tr(lang, "cx_b_sounds"), "al:xr:0")], [btn(tr(lang, "b_a_practice"), "qz:snd"), btn(tr(lang, "b_a_grammar"), "al:xg:0")], ui.menu_row(lang)]
    ui.edit(uid, mid, tr(lang, "cx_alpha_menu_" + L), kb(rows))

def _nav(kind, i, n):
    return [btn("⬅️", f"al:{kind}:{(i - 1) % n}"), btn(f"{i + 1}/{n}", "noop"), btn("➡️", f"al:{kind}:{(i + 1) % n}")]

def alpha_cb(uid, mid, p):
    ui = _ui(); lang = ui.ul(uid); e = ui.el(uid); L = logic.target(uid); op = p[1]; back = [btn(tr(lang, "b_back"), "al:menu")]
    if op == "menu": return alpha_menu(uid, mid)
    i = int(p[2]) if len(p) > 2 and p[2].isdigit() else 0
    if op == "xl" and L == "ru":
        chunks = CX._chunks(list(range(len(LX._alphabet()))), 6); i %= len(chunks); lines = []; btns = []
        for k in chunks[i]:
            up, trn, fa, en, exw, mean = LX._alphabet()[k]
            lines.append(f"<b>{esc(up)}</b>  [{esc(trn) or '—'}]  {esc(fa if e == 'fa' else en)}\n     {esc(langs.ru_accent(exw))} — {esc(mean)}")
            plain = langs.ru_plain(exw)
            if len(plain.encode()) < 40: btns.append(btn("🔊 " + up[0], "hz:" + plain))
        rows = grid(btns, 3) + [_nav("xl", i, len(chunks)), back]
        ui.edit(uid, mid, "\n".join(lines), kb(rows))
    elif op == "xr":
        rs = LX._rules(L); i %= len(rs); r = rs[i]
        exs = LX._split_examples(r[2])
        rows = grid([btn("🔊 " + langs.ru_accent(x) if L == "ru" else "🔊 " + x, "hz:" + langs.ru_plain(x)) for x in exs[:6] if len(langs.ru_plain(x).encode()) < 40], 3)
        rows += [_nav("xr", i, len(rs)), back]
        ac = langs.ru_accent if L == "ru" else (lambda s: s)
        ui.edit(uid, mid, f"<b>{esc(ac(_pk(r[0], e)))}</b>\n{esc(ac(_pk(r[1], e)))}\n\n{tr(lang, 'cr_examples')}: <b>{esc(ac(r[2]))}</b>", kb(rows))
    elif op == "xg":
        gs = CX.grammar_notes(L); i %= len(gs); g = gs[i]
        ac = langs.ru_accent if L == "ru" else (lambda s: s)
        first = langs.ru_plain(re.split(r"(?<=[.!?])\s", g[3])[0])
        rows = ([[btn(tr(lang, "b_hear"), "hz:" + first)]] if len(first.encode()) < 50 else []) + [_nav("xg", i, len(gs)), back]
        ui.edit(uid, mid, grammar_text(L, g, e), kb(rows))

def grammar_text(L, g, e):
    ac = langs.ru_accent if L == "ru" else (lambda s: s)
    return f"<b>{esc(ac(_pk(g[1], e)))}</b>\n\n🧩 <code>{esc(ac(g[2]))}</code>\n📝 {esc(ac(g[3]))}\n<i>{esc(_pk(g[4], e))}</i>\n\n{esc(ac(_pk(g[5], e)))}"

# ---------------------------------------------------------------- daily tip
def daily_tip(d, L, e):
    notes = CX.grammar_notes(L); rules = LX._rules(L)
    if d % 2 == 0:
        return grammar_text(L, notes[(d // 2) % len(notes)], e)
    r = rules[(d // 2) % len(rules)]; ac = langs.ru_accent if L == "ru" else (lambda s: s)
    return f"<b>{esc(ac(_pk(r[0], e)))}</b>\n{esc(ac(_pk(r[1], e)))}\n\n<b>{esc(ac(r[2]))}</b>"

# ---------------------------------------------------------------- dictionary (curated list only)
def search(L, q, limit=6):
    qn = langs.strip_marks(q); qd = xlang._umlaut_free(q) if L == "de" else qn; out = []; seen = set()
    if not qn: return out
    for w in langs.words(L):
        keys = {langs.strip_marks(w["base"]), langs.strip_marks(w["hz"]), langs.strip_marks(w.get("plural") or "")}
        if L == "de": keys |= {xlang._umlaut_free(w["base"]), xlang._plain_de(w["base"])}
        if L == "ru" and re.fullmatch(r"[a-z' ]+", qn): keys.add(langs.translit(langs.ru_plain(w["base"])).lower())
        score = 0
        if qn in keys or qd in keys: score = 3
        else:
            ens = re.split(r"[;,/]| or ", w["en"].lower()); fas = re.split(r"[،؛,/]", w["fa"])
            if any(qn == x.strip(" ()") or qn == re.sub(r"^to ", "", x.strip()) for x in ens): score = 2
            elif any(qn == x.strip() for x in fas) or q.strip() in w["fa"].split("،"): score = 2
            elif len(qn) >= 4 and (any(k.startswith(qn) for k in keys) or qn in w["en"].lower()): score = 1
            elif len(q.strip()) >= 3 and q.strip() in w["fa"]: score = 1
        if score and w["i"] not in seen: seen.add(w["i"]); out.append((score, w["freq"], w))
    out.sort(key=lambda t: (-t[0], t[1]))
    return [w for _, _, w in out[:limit]]

def dict_html(L, q, lang, e):
    ws = search(L, q)
    if not ws: return None
    return "\n\n".join(xlang.word_card(w, lang, e) for w in ws[:4])

def do_dict(uid, q):
    ui = _ui(); lang = ui.ul(uid); e = ui.el(uid); L = logic.target(uid)
    html = dict_html(L, q[:60], lang, e)
    if html is None:
        from llm import configured, allow
        if configured() and allow(uid): return ui.do_ask(uid, q)
        ui.out(uid, tr(lang, "cx_dict_none", q=esc(q[:40])), kb([[btn(tr(lang, "b_ask"), "m:ask")], ui.menu_row(lang)])); return
    ws = search(L, q[:60]); rows = []
    if ws: rows.append([btn(tr(lang, "b_hear"), f"hr:{ws[0]['i']}")])
    rows.append(ui.menu_row(lang)); ui.out(uid, html, kb(rows))

# ---------------------------------------------------------------- ask (grammar notes; LLM when configured)
def grammar_matches(L, q, limit=2):
    ql = q.lower(); res = []
    kw = {"de": {"gender": ["artikel", "article", "der die das", "جنسیت", "gender", "geschlecht"], "plural": ["plural", "mehrzahl", "جمع"], "present": ["präsens", "present", "conjugat", "konjug", "حال", "صرف"],
                 "wordorder": ["wortstellung", "word order", "ترتیب", "verb position"], "cases": ["akkusativ", "dativ", "genitiv", "nominativ", "kasus", "case", "حالت"], "negation": ["nicht", "kein", "negat", "نفی"],
                 "modal": ["modal", "können", "müssen", "wollen", "möchte"], "separable": ["trennbar", "separable"], "perfekt": ["perfekt", "past", "گذشته"], "prepositions": ["präposition", "preposition", "حرف اضافه"], "time": ["uhr", "time", "ساعت", "zeit"]},
          "ru": {"gender": ["род", "gender", "جنسیت", "мужской"], "tobe": ["быть", "to be", "است"], "plural": ["множественное", "plural", "جمع"], "present": ["настоящее", "present", "حال", "спряжение", "conjug"],
                 "past": ["прошедшее", "past", "گذشته"], "cases": ["падеж", "case", "حالت", "cases"], "accusative": ["винительный", "accusative", "مفعولی"], "prepositional": ["предложный", "prepositional", "حرف‌اضافه‌ای"],
                 "genitive": ["родительный", "genitive", "اضافه"], "motion": ["идти", "ходить", "ехать", "ездить", "motion", "حرکت"], "aspect": ["вид", "aspect", "совершенный", "نوع فعل"], "questions": ["вопрос", "question", "سؤال", "кто", "что"]}}[L]
    for g in CX.grammar_notes(L):
        score = sum(1 for k in kw.get(g[0], []) if k in ql)
        if g[0] in re.findall(r"[a-zа-я]+", ql): score += 2
        if score: res.append((score, g))
    res.sort(key=lambda t: -t[0]); return [g for _, g in res[:limit]]

def ask_answer(uid, q, lang, e, use_llm=True, L=None):
    import llm
    L = L or (logic.target(uid) if uid is not None else "zh")
    q = q.strip()[:500]
    if use_llm and llm.configured():
        if uid is not None and not llm.allow(uid): return tr(lang, "ask_limit")
        if uid is not None: llm.count(uid)
        system = (f"You are a friendly, precise {langs.name(L, 'en')} teacher for learners whose first language is Persian. Answer in {llm.LANG_NAMES.get(e, 'Persian')}. "
                  "Keep it short (max ~180 words); give 1-3 examples with translations; for Russian mark the stressed vowel. If the question is not about language learning, say you only help with languages. Do not invent words; say if unsure.")
        ans = llm.chat(system, q, max_tokens=500)
        if ans: return "🤖 " + esc(ans)[:3800]
    parts = [tr(lang, "ask_nollm")]
    for g in grammar_matches(L, q): parts.append(grammar_text(L, g, e))
    ws = []
    for t in [x for x in re.sub(r"[?؟!.,،]", " ", q).split() if len(x) >= 3][:6]:
        ws += search(L, t, 1)
    for w in list(dict.fromkeys(w["i"] for w in ws))[:2]: parts.append(xlang.word_card(langs.word(w) if isinstance(w, int) else w, lang, e, with_example=False))
    if len(parts) == 1: parts.append(tr(lang, "cx_ask_none"))
    return "\n\n".join(parts)[:4000]
