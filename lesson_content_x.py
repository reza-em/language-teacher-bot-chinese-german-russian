"""Guided course content for German and Russian: teaching pages, practice plans (JSON-able specs), exercise builders, placement.
Dispatched to from lesson_content.py when a lesson / spec belongs to a non-Chinese language. No Telegram I/O."""
import random, re, math
import logic, langs, xlang
import exercises as X
import curriculum as Cu
import curriculum_x as CX
from core import btn, esc, num
from texts import tr

IDX = {"fa": 0, "en": 1, "de": 1}
def pick(tup, el): return tup[IDX.get(el, 1)] if len(tup) > IDX.get(el, 1) else tup[1]

METHOD = {
    "alpha": ("🎧 هر حرف را بشنو، بلند تکرار کن و به واژهٔ نمونه‌اش گره بزن.", "🎧 Listen to each letter, repeat aloud and tie it to its example word."),
    "rules": ("🎧 قاعده را بخوان، مثال‌ها را بشنو و تکرار کن.", "🎧 Read the rule, listen to the examples and repeat them."),
    "words": ("🔁 تکرار فاصله‌دار + 🎧 صدا: این واژه‌ها خودکار به جعبهٔ مرورت می‌روند. اسم‌های آلمانی را همیشه با حرف تعریف یاد بگیر و روسی را با تکیه.", "🔁 Spaced repetition + 🎧 audio: these words go into your review box. Learn German nouns with their article and Russian words with their stress."),
    "grammar": ("🧩 الگو را بخوان، مثال را بشنو، بعد تمرین کن.", "🧩 Read the pattern, hear the example, then practise."),
    "sent": ("🧩 واژه‌ها را در جمله ببین، جمله بساز و جای خالی را پر کن.", "🧩 See the words inside sentences, build sentences and fill gaps."),
    "check": ("🔁 مرور مخلوط همهٔ این بخش با سؤال‌های متنوع.", "🔁 Mixed review of this whole section with varied questions."),
    "soundcheck": ("🎧 فقط گوش بده و تشخیص بده؛ مرحلهٔ مرور است.", "🎧 Just listen and decide; this is a review step."),
}
def _hdr(les, lang, elang, pos, total):
    return tr(lang, "cr_lesson_head", i=num(lang, pos + 1), n=num(lang, total), mod=esc(Cu.module_name(les["mod"], lang)), title=esc(Cu.title(les, lang))) \
        + "\n" + tr(lang, "cr_method", m=esc(pick(METHOD[les["kind"]], elang)))

def _grid(buttons, per): return [buttons[i:i + per] for i in range(0, len(buttons), per)]
def _w(wid): return logic.get_word(wid)
def _ac(s, L): return langs.ru_accent(s) if L == "ru" else s
def _short(s, n=60): return (s[:n - 1] + "…") if len(s) > n else s
def _bytes_ok(text, limit=52): return len(("hz:" + text).encode()) <= limit + 3

def _alphabet(): 
    import content.ru_extra as E; return E.ALPHABET
def _rules(L):
    if L == "de":
        import content.de_extra as E; return E.SOUNDS
    import content.ru_extra as E; return E.RULES

def _split_examples(s): return [x.strip() for x in re.split(r"[·/,]", s) if x.strip()]

# ================================================================== pages
def pages(les, lang, elang, pos=0, total=1):
    L = les["lang"]; k = les["kind"]; a = les["arg"]; hd = _hdr(les, lang, elang, pos, total); out = []
    if k == "alpha":
        lines = []; btns = []
        for i in a["idx"]:
            up, trn, fa, en, exw, mean = _alphabet()[i]
            hint = fa if elang == "fa" else en
            lines.append(f"<b>{esc(up)}</b>  [{esc(trn) or '—'}]  {esc(hint)}\n     {esc(_ac(exw, 'ru'))} — {esc(mean)}")
            plain = langs.ru_plain(exw)
            if _bytes_ok(plain): btns.append(btn("🔊 " + up[0], "hz:" + plain))
        out.append((hd + "\n\n" + "\n".join(lines), _grid(btns, 3)))
        if any(_alphabet()[i][0][0] in "ЪЬЫЭЁЙ" for i in a["idx"]):
            out.append((tr(lang, "cx_alpha_tip"), []))
    elif k == "rules":
        for ri in a["idx"]:
            r = _rules(L)[ri]; title, body, exs = r[0], r[1], r[2]
            ws = [langs.ru_plain(x) for x in _split_examples(exs)]
            rows = _grid([btn("🔊 " + _ac(x, L), "hz:" + langs.ru_plain(x)) for x in _split_examples(exs)[:6] if _bytes_ok(langs.ru_plain(x))], 3)
            out.append((hd + "\n\n" + f"<b>{esc(_ac(pick(title, elang), L))}</b>\n{esc(_ac(pick(body, elang), L))}\n\n{tr(lang, 'cr_examples')}: <b>{esc(_ac(exs, L))}</b>", rows))
    elif k == "words":
        ws = [w for w in (_w(x) for x in a["wids"]) if w]; lines = []
        for w in ws:
            mean, _ = logic.gloss(w, elang)
            if L == "de":
                extra = (f"Pl. die {w['plural']}" if w.get("plural") else "") if w.get("art") else (w.get("py") or "")
                line = f"<b>{esc(w['hz'])}</b>" + (f" · {esc(extra)}" if extra else "") + f" — {esc(_short(mean, 70))}"
            else:
                g = {"m": "♂", "f": "♀", "n": "⚪", "pl": "pl."}.get(w.get("gender"), "")
                line = f"<b>{esc(w['ac'])}</b> [{esc(langs.translit(w['ac']))}] {g} — {esc(_short(mean, 70))}"
            lines.append(line)
        rows = _grid([btn("🔊 " + (w["hz"] if L == "de" else w["ac"]), f"hr:{w['i']}") for w in ws], 2)
        out.append((hd + "\n\n" + "\n".join(lines) + "\n\n" + tr(lang, "cr_srs_note"), rows))
        ss = [s for w in ws for s in langs.sentences_for(w)][:5]
        if ss: out.append((tr(lang, "cr_in_sentences") + "\n\n" + "\n\n".join(f"{esc(s['ac'])}\n<i>{esc(s['fa'] if elang == 'fa' else s['en'])}</i>" for s in ss), []))
    elif k == "grammar":
        g = CX.grammar_note(L, a["gid"]); title, pattern, example, ex_tr, body = g[1], g[2], g[3], g[4], g[5]
        text = f"<b>{esc(_ac(pick(title, elang), L))}</b>\n\n🧩 <code>{esc(_ac(pattern, L))}</code>\n📝 {esc(_ac(example, L))}\n<i>{esc(pick(ex_tr, elang))}</i>\n\n{esc(_ac(pick(body, elang), L))}"
        first = langs.ru_plain(re.split(r"(?<=[.!?])\s", example)[0])
        rows = [[btn(tr(lang, "b_hear"), "hz:" + first)]] if _bytes_ok(first) else []
        out.append((hd + "\n\n" + text, rows))
    elif k == "sent":
        ws = set(a["wids"]); ss = [s for s in langs.sentences(L) if s["wid"] in ws]
        random.Random(len(ws)).shuffle(ss)
        if len(ss) < 4: ss += [s for s in langs.sentences(L) if s not in ss][:4 - len(ss)]
        out.append((hd + "\n\n" + "\n\n".join(f"{esc(s['ac'])}\n<i>{esc(s['fa'] if elang == 'fa' else s['en'])}</i>" for s in ss[:5]), []))
    elif k == "soundcheck":
        out.append((hd + "\n\n" + tr(lang, "cx_soundcheck_body"), []))
    else:
        out.append((hd + "\n\n" + tr(lang, "cr_check_body"), []))
    return out

# ================================================================== plans
def _nouns(L, wids):
    return [w for w in (_w(x) for x in wids) if w and (w.get("art") if L == "de" else w.get("gender") in ("m", "f", "n"))]

def _sent_specs(L, filt, n, t=("build", "cloze")):
    ss = [(i, s) for i, s in enumerate(langs.sentences(L)) if filt(s)]
    random.shuffle(ss); out = []
    for j, (i, s) in enumerate(ss[:n]):
        tt = t[j % len(t)]
        if tt == "cloze" and not s.get("blank"): tt = "build"
        out.append({"L": L, "k": "sent", "s": i, "t": tt})
    return out

def _hearwords(L, idxs):
    rs = _rules(L); w = []
    for i in idxs: w += [langs.ru_plain(x) for x in _split_examples(rs[i][2])]
    return [x for x in dict.fromkeys(w) if " " not in x]

MODAL = re.compile(r"\b(will|kann|muss|möchte|darf|soll|kannst|musst|willst)\b", re.I)
PERF = re.compile(r"\b(habe|hat|haben|bin|ist|sind)\b.*\bge\w+", re.I)
SEP = re.compile(r"\b(\w+)\b.*\b(auf|an|ein|mit|aus|zu|zurück|ab|vor|fern|um)[.!?]$", re.I)

def plan(les, uid=None):
    L = les["lang"]; k = les["kind"]; a = les["arg"]; R = random; sp = []
    def S(**kw): sp.append(dict(L=L, **kw))
    if k == "alpha":
        idx = a["idx"]
        for i in idx:
            if _alphabet()[i][1]: S(k="letter", i=i)
        allex = [langs.ru_plain(x[4]) for x in _alphabet()]
        for i in R.sample(idx, min(3, len(idx))): S(k="hear", words=allex, r=langs.ru_plain(_alphabet()[i][4]))
        R.shuffle(sp)
    elif k == "rules":
        words = _hearwords(L, a["idx"]); allw = xlang.sound_words(L)
        for w_ in R.sample(words, min(5, len(words))): S(k="hear", words=list(dict.fromkeys(words + R.sample(allw, min(6, len(allw))))), r=w_)
        if L == "ru":
            for w_ in R.sample(langs.words("ru")[:60], 3): S(k="w", t="x_read", w=w_["i"])
        R.shuffle(sp)
    elif k == "soundcheck":
        allw = xlang.sound_words(L)
        for w_ in R.sample(allw, min(8, len(allw))): S(k="hear", words=allw, r=w_)
        if L == "ru":
            for i in R.sample(range(len(_alphabet())), 5):
                if _alphabet()[i][1]: S(k="letter", i=i)
            for w_ in R.sample(langs.words("ru")[:80], 4): S(k="w", t="x_read", w=w_["i"])
        R.shuffle(sp)
    elif k == "words":
        ids = list(a["wids"]); seq = ["zh2m", "m2zh", "listen", "x_type", "zh2m", "x_dict"]
        for n, wid in enumerate(ids): S(k="w", t=seq[n % len(seq)], w=wid)
        nn = _nouns(L, ids)
        if L == "de":
            for w_ in R.sample(nn, min(2, len(nn))): S(k="w", t="x_art", w=w_["i"])
            ps = [w_ for w_ in nn if w_.get("plural")]
            for w_ in R.sample(ps, min(1, len(ps))): S(k="w", t="x_plural", w=w_["i"])
        else:
            for w_ in R.sample(ids, min(2, len(ids))): S(k="w", t="x_stress", w=w_)
            for w_ in R.sample(nn, min(1, len(nn))): S(k="w", t="x_gender", w=w_["i"])
        R.shuffle(sp)
    elif k == "grammar":
        gid = a["gid"]; ids = a["wids"]; nn = _nouns(L, ids)
        def many(t, n, pool=None):
            pw = pool or nn
            for w_ in R.sample(pw, min(n, len(pw))): S(k="w", t=t, w=w_["i"])
        def drills(ix, n): 
            for i in R.sample(ix, min(n, len(ix))): S(k="drill", i=i)
        if L == "de":
            if gid == "gender": many("x_art", 6)
            elif gid == "plural": many("x_plural", 4, [w_ for w_ in nn if w_.get("plural")]); many("x_art", 2)
            elif gid == "present": [S(k="conj") for _ in range(6)]
            elif gid == "wordorder": sp += _sent_specs(L, lambda s: True, 5, ("build",)); sp += _sent_specs(L, lambda s: s.get("blank"), 2, ("cloze",))
            elif gid == "negation": drills([12, 13], 2); sp += _sent_specs(L, lambda s: re.search(r"\b(nicht|kein\w*)\b", s["t"], re.I), 4, ("build", "cloze"))
            elif gid == "time": sp += _sent_specs(L, lambda s: re.search(r"\b(heute|morgen|jetzt|Uhr|immer|oft|Montag|gestern)\b", s["t"], re.I), 5, ("build", "cloze"))
            elif gid == "modal": sp += _sent_specs(L, lambda s: MODAL.search(s["t"]), 6, ("build", "cloze"))
            elif gid == "cases": many("x_case", 4); drills([0, 1, 2, 3, 7, 10, 11], 3)
            elif gid == "prepositions": drills([4, 5, 6, 9, 11], 4); sp += _sent_specs(L, lambda s: re.search(r"\b(in|mit|aus|nach|zu|bei|von|für|auf)\b", s["t"], re.I), 3)
            elif gid == "separable": sp += _sent_specs(L, lambda s: SEP.search(s["t"]), 5, ("build",)); sp += _sent_specs(L, lambda s: True, 2)
            elif gid == "perfekt": sp += _sent_specs(L, lambda s: PERF.search(s["t"]), 5, ("build", "cloze")); sp += _sent_specs(L, lambda s: True, 2)
            else: sp += _sent_specs(L, lambda s: True, 6)
        else:
            if gid == "gender": many("x_gender", 5); many("x_stress", 2, [w_ for w_ in (_w(x) for x in ids) if w_])
            elif gid == "plural": many("x_plural", 5, [w_ for w_ in nn if w_.get("plural")])
            elif gid == "present": [S(k="conj", mode="pres") for _ in range(6)]
            elif gid == "past": [S(k="conj", mode="past") for _ in range(6)]
            elif gid == "accusative": many("x_case", 3, [w_ for w_ in nn if xlang._ru_forms(w_) and xlang._ru_forms(w_)["acc"] != xlang._ru_forms(w_)["nom"]]); drills([0, 3, 5, 8], 3)
            elif gid == "prepositional": many("x_case", 3); drills([1, 4, 7, 9], 3)
            elif gid == "genitive": drills([2, 5, 6], 3); many("x_case", 3)
            elif gid == "motion": drills([10, 11, 12, 13], 4); sp += _sent_specs(L, lambda s: re.search(r"(иду|идёт|идём|еду|едет|хожу|езжу|ходит|ездит|идти|ехать)", s["t"]), 3)
            elif gid == "cases": drills(list(range(10)), 5); many("x_case", 3)
            else: sp += _sent_specs(L, lambda s: True, 6)
        if len(sp) < 5:
            for w_ in R.sample([x for x in (_w(i) for i in ids) if x], min(5 - len(sp), len(ids))): S(k="w", t="zh2m", w=w_["i"])
        R.shuffle(sp)
    elif k == "sent":
        ws = set(a["wids"]); ss = [i for i, s in enumerate(langs.sentences(L)) if s["wid"] in ws or (not s["wid"] and s["blank"])]
        R.shuffle(ss)
        for n, i in enumerate(ss[:8]):
            s = langs.sentences(L)[i]; t = "build" if n % 2 == 0 or not s.get("blank") else "cloze"; S(k="sent", s=i, t=t)
        rest = [x for x in a["wids"]]; R.shuffle(rest)
        while len(sp) < 8 and rest: S(k="w", t="zh2m", w=rest.pop())
    else:   # check
        ids = list(a["wids"]); R.shuffle(ids); seq = ["zh2m", "m2zh", "listen", "x_type", "cloze", "zh2m", "x_dict", "m2zh", "build", "x_case"]
        extra = ["x_art", "x_plural"] if L == "de" else ["x_stress", "x_gender"]
        seq[3:3] = [extra[0]]
        for n, wid in enumerate(ids[:11]): S(k="w", t=seq[n % len(seq)], w=wid)
        R.shuffle(sp)
    return sp

# ================================================================== exercise builders
def build_exercise(spec, uid, el):
    L = spec["L"]; k = spec["k"]; R = random
    level = max(1, (logic.get_user(uid).get("level") if uid else 1) or 1)
    if k == "w":
        w = _w(spec["w"]); pool = langs.pool(L, max(w["lv"], 1)) or langs.pool(L, 1); t = spec["t"]
        fn = xlang.CREATORS.get(t) or {"x_art": xlang.mk_art, "x_plural": xlang.mk_plural if L == "de" else xlang.mk_plural_ru, "x_stress": xlang.mk_stress, "x_gender": xlang.mk_gender, "x_read": xlang.mk_read}.get(t)
        ex = fn(w, pool, el) if fn else None
        if ex is None and t in ("cloze", "build"):
            ex = (xlang.CREATORS["build" if t == "cloze" else "cloze"])(w, pool, el)
        if ex is None and t in ("x_case", "x_art", "x_plural", "x_stress", "x_gender", "x_read"): ex = xlang.mk_m2w(w, pool, el)
        return ex or xlang.mk_w2m(w, pool, el)
    if k == "sent":
        s = langs.sentences(L)[spec["s"]]; w = _w(s["wid"]) if s["wid"] else None; pool = langs.pool(L, 2)
        ex = xlang.mk_cloze_sent(s, w, pool, el, L) if spec["t"] == "cloze" else xlang.mk_build_sent(s, w, el, L)
        return ex or xlang.mk_build_sent(s, w, el, L) or xlang.mk_cloze_sent(s, w, pool, el, L) or xlang.mk_drill(L, el)
    if k == "drill": return xlang.mk_drill_fixed(L, el, spec["i"])
    if k == "letter": return xlang.mk_letter(el, spec["i"]) or xlang.mk_letter(el)
    if k == "hear": return xlang.mk_hear(L, el, target=spec["r"], wordlist=spec["words"]) or xlang.mk_hear(L, el)
    if k == "conj":
        if L == "de": return xlang.mk_conj_de(el)
        return xlang.mk_conj_ru(el, mode=spec.get("mode"))
    raise ValueError(k)

# ================================================================== placement
def placement_plan(L):
    """12 questions, 4 per tier: 0 basics (letters/sounds or the very first words), 1 = A1, 2 = A2."""
    R = random; sp = []
    def S(tier, **kw): sp.append(dict(L=L, tier=tier, **kw))
    a1 = sorted(langs.level_words(L, 1), key=lambda w: w["freq"]); a2 = langs.level_words(L, 2)
    easy = a1[:40]; mid = a1[40:]; 
    if L == "ru":
        letters = [i for i, a in enumerate(_alphabet()) if a[1]]
        for i in R.sample(letters, 2): S(0, k="letter", i=i)
        for w in R.sample(easy, 2): S(0, k="w", t="x_read", w=w["i"])
    else:
        for n, w in enumerate(R.sample(easy, 4)): S(0, k="w", t=["zh2m", "m2zh", "listen", "zh2m"][n], w=w["i"])
    nn = [w for w in mid if w.get("art")] if L == "de" else [w for w in mid if w.get("gender") in ("m", "f", "n")]
    for n, w in enumerate(R.sample(mid, 3)): S(1, k="w", t=["zh2m", "m2zh", "listen"][n], w=w["i"])
    S(1, k="w", t="x_art" if L == "de" else "x_gender", w=R.choice(nn)["i"])
    for n, w in enumerate(R.sample(a2, 3)): S(2, k="w", t=["zh2m", "m2zh", "zh2m"][n], w=w["i"])
    S(2, k="drill", i=R.choice([0, 1, 4, 5, 6, 7, 9, 11]) if L == "de" else R.choice([0, 1, 2, 3, 4, 7, 9, 10, 11, 12]))
    return sp

def recommend(L, tiers):
    """tiers: {0: ok, 1: ok, 2: ok} (each out of 4) -> (lesson id, level, reason key)."""
    Cu_old = Cu.set_lang(L)
    try:
        t0, t1, t2 = (tiers.get(i, 0) for i in (0, 1, 2))
        first = Cu.start_of(Cu.modules()[0][0])
        if t0 < 3: return first, 0, "cx_rec_zero"
        if t1 < 3: return Cu.start_of("a1"), 1, "cx_rec_a1"
        if t2 < 3: return Cu.start_of("a2"), 1, "cx_rec_a2"
        ls = Cu.lessons(); a2w = [l for l in ls if l["mod"] == "a2" and l["kind"] == "words"]
        return (a2w[-1]["id"] if a2w else Cu.start_of("a2")), 2, "cx_rec_top"
    finally: Cu.set_lang(Cu_old)

def srs_items(les):
    L = les["lang"]; k = les["kind"]; a = les["arg"]; out = []
    if k == "words": out = list(a["wids"])
    elif k == "alpha":
        by = xlang.by_base("ru")
        for i in a["idx"]:
            w = by.get(langs.ru_plain(_alphabet()[i][4]).lower())
            if w: out.append(w["i"])
    return list(dict.fromkeys(out))
