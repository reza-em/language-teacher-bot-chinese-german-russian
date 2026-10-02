"""Guided course: the fixed, ordered curriculum (structure only, no Telegram I/O).
pinyin (initials, finals, tones, tone marks, sandhi, spelling) -> 51 radicals -> stroke basics -> first 24 characters ->
HSK 1 (words + grammar + sentences) -> HSK 2 -> HSK 3. Lesson ids are stable strings; progress is stored by id."""
import math, threading
import data
import content.alphabet as A
import content.lessons as L

PASS_RATIO = 0.7            # a lesson is passed with >= 70 % correct answers
LI = {"fa": 0, "en": 1, "de": 2}

MODULES = [  # key, emoji, (fa, en, de)
    ("pinyin", "🔤", ("پینیین و لحن‌ها", "Pinyin & tones", "Pinyin & Töne")),
    ("radicals", "🧱", ("۵۱ ریشهٔ پرکاربرد", "51 key radicals", "51 wichtige Radikale")),
    ("strokes", "✍️", ("اصول نوشتن (ضربه‌ها)", "Writing basics (strokes)", "Schreibgrundlagen (Striche)")),
    ("first", "🌱", ("اولین نویسه‌ها و واژه‌ها", "First characters & words", "Erste Zeichen & Wörter")),
    ("hsk1", "1️⃣", ("HSK ۱: واژه، دستور، جمله", "HSK 1: words, grammar, sentences", "HSK 1: Wörter, Grammatik, Sätze")),
    ("hsk2", "2️⃣", ("HSK ۲", "HSK 2", "HSK 2")),
    ("hsk3", "3️⃣", ("HSK ۳", "HSK 3", "HSK 3")),
]
MOD_KEYS = [m[0] for m in MODULES]

FIRST_HZ = "我 你 他 好 是 不 人 大 小 一 二 三 十 水 日 月 爱 上 下 来 去 看 吃 喝".split()

_cache = {}

def t3(x, lang):
    """(fa, en, de) tuple or plain string -> text for `lang` (de falls back to en)."""
    if isinstance(x, (tuple, list)):
        i = LI.get(lang, 0)
        return x[i] if i < len(x) and x[i] else x[1]
    return x

def _chunks(lst, size):
    if not lst: return []
    n = math.ceil(len(lst) / size); base, extra = divmod(len(lst), n); out = []; i = 0
    for k in range(n):
        m = base + (1 if k < extra else 0); out.append(lst[i:i + m]); i += m
    return out

def _sorted_words(lv):
    return sorted([w for w in data.words() if w["lv"] == lv], key=lambda w: (w.get("freq", 10**6), w["i"]))

def _weave(words_lessons, extras_at_ratio, sent_every, sent_prefix, mod):
    """Insert grammar lessons evenly and a sentence-practice lesson after every `sent_every` word lessons."""
    n = len(words_lessons); g = len(extras_at_ratio)
    gpos = {}
    for k, lesson in enumerate(extras_at_ratio):
        gpos.setdefault(max(1, round((k + 1) * n / (g + 1))), []).append(lesson)
    out = []; recent = []; seen = []
    for i, wl in enumerate(words_lessons, 1):
        out.append(wl); recent.append(wl); seen += wl["arg"]["wids"]
        for gl in gpos.get(i, []):
            gl["arg"]["wids"] = list(seen); out.append(gl)
        if i % sent_every == 0 or i == n:
            ids = [x for r in recent[-sent_every:] for x in r["arg"]["wids"]]
            k = (i - 1) // sent_every
            out.append({"id": f"{sent_prefix}.s{k}", "mod": mod, "kind": "sent",
                        "title": (f"جمله‌سازی ({k + 1})", f"Sentence practice ({k + 1})", f"Satzübung ({k + 1})"), "arg": {"wids": ids}})
            recent = []
    return out

def build():
    out = []
    def add(lid, mod, kind, title, **arg): out.append({"id": lid, "mod": mod, "kind": kind, "title": title, "arg": arg})
    # ---- 1. pinyin
    for gi, (grp, name) in enumerate(A.INITIAL_GROUPS):
        add(f"py.i{gi}", "pinyin", "init", (f"حروف آغازین: {grp}", f"Initials: {grp}", f"Anlaute: {grp}"), gi=gi)
    for gi, (grp, name) in enumerate(A.FINAL_GROUPS):
        add(f"py.f{gi}", "pinyin", "fin", (f"وان‌ها: {grp}", f"Finals: {grp}", f"Finale: {grp}"), gi=gi)
    add("py.tones", "pinyin", "tones", ("چهار لحن + لحن خنثی", "The four tones + neutral", "Die vier Töne + neutral"))
    add("py.marks", "pinyin", "marks", ("جای علامت لحن", "Where the tone mark goes", "Wo das Tonzeichen steht"))
    add("py.sandhi", "pinyin", "sandhi", ("تغییر لحن (۳+۳، 不، 一)", "Tone sandhi (3+3, 不, 一)", "Tonsandhi (3+3, 不, 一)"))
    add("py.spell", "pinyin", "spell", ("قواعد املای پینیین", "Pinyin spelling rules", "Pinyin-Schreibregeln"))
    add("py.check", "pinyin", "pycheck", ("مرور پینیین و لحن", "Pinyin & tones checkpoint", "Pinyin & Töne: Wiederholung"))
    # ---- 2. radicals (51)
    for k, ch in enumerate(_chunks(list(range(len(A.RADICALS))), 6)):
        add(f"rad.{k}", "radicals", "rad", (f"ریشه‌ها {ch[0] + 1}–{ch[-1] + 1}", f"Radicals {ch[0] + 1}–{ch[-1] + 1}", f"Radikale {ch[0] + 1}–{ch[-1] + 1}"), idx=ch)
    # ---- 3. stroke basics
    add("st.types", "strokes", "strokes", ("ضربه‌های پایه", "Basic strokes", "Grundstriche"))
    add("st.order", "strokes", "order", ("ترتیب نوشتن ضربه‌ها", "Stroke order rules", "Strichfolge-Regeln"))
    # ---- 4. first characters
    hsk1 = _sorted_words(1)
    first = [data.by_hz(h) for h in FIRST_HZ if data.by_hz(h) and data.by_hz(h)["lv"] == 1]
    first_ids = {w["i"] for w in first}
    for k, ch in enumerate(_chunks(first, 6)):
        add(f"fc.{k}", "first", "words", (f"اولین نویسه‌ها ({k + 1})", f"First characters ({k + 1})", f"Erste Zeichen ({k + 1})"), wids=[w["i"] for w in ch], first=True)
    # ---- 5. HSK1 .. 3
    g_all = [g[0] for g in L.GRAMMAR]; g1 = g_all[:10]; g2 = g_all[10:]
    def gram(gid, mod):
        g = next(x for x in L.GRAMMAR if x[0] == gid)
        return {"id": f"g.{gid}", "mod": mod, "kind": "grammar", "title": (f"دستور: {g[5][0]}", f"Grammar: {g[5][1]}", f"Grammatik: {g[5][2]}"), "arg": {"gid": gid, "wids": []}}
    for mod, lv, size, gl in (("hsk1", 1, 6, g1), ("hsk2", 2, 6, g2), ("hsk3", 3, 8, [])):
        words = [w for w in _sorted_words(lv) if w["i"] not in first_ids]
        p = {"hsk1": "h1", "hsk2": "h2", "hsk3": "h3"}[mod]
        wl = [{"id": f"{p}.w{k}", "mod": mod, "kind": "words", "title": (f"واژه‌ها ({k + 1})", f"Words ({k + 1})", f"Wörter ({k + 1})"), "arg": {"wids": [w["i"] for w in ch], "first": False}}
              for k, ch in enumerate(_chunks(words, size))]
        seed = [w["i"] for w in first] if mod == "hsk1" else []     # the first characters count as seen words in HSK 1
        seq = _weave(wl, [gram(g, mod) for g in gl], 5, p, mod)
        for l_ in seq:
            if l_["kind"] == "grammar": l_["arg"]["wids"] = seed + l_["arg"]["wids"]
        allw = [x for l_ in wl for x in l_["arg"]["wids"]] + seed
        seq.append({"id": f"{p}.check", "mod": mod, "kind": "check", "title": (f"مرور {mod.upper().replace('HSK', 'HSK ')}", f"{mod.upper().replace('HSK', 'HSK ')} checkpoint", f"{mod.upper().replace('HSK', 'HSK ')}: Wiederholung"), "arg": {"wids": allw}})
        out += seq
    return out

_ctx = threading.local()
def cur_lang(): return getattr(_ctx, "lang", "zh")
def set_lang(lang):
    """Select which language's curriculum lessons()/get()/index()/... operate on; returns the previous one."""
    old = cur_lang(); _ctx.lang = lang or "zh"; return old

def modules(lang=None):
    import curriculum_x as CX
    lang = lang or cur_lang(); return MODULES if lang == "zh" else CX.MODULES_X[lang]

def lessons(lang=None):
    lang = lang or cur_lang()
    if ("l", lang) not in _cache:
        if lang == "zh": ls = build()
        else:
            import curriculum_x as CX; ls = CX.build(lang)
        _cache[("l", lang)] = ls; _cache[("i", lang)] = {l["id"]: n for n, l in enumerate(ls)}
    return _cache[("l", lang)]

def index(lid):
    lessons(); return _cache[("i", cur_lang())].get(lid)

def get(i):
    ls = lessons(); return ls[i] if 0 <= i < len(ls) else None

def total(): return len(lessons())

def module_range(mod):
    ls = lessons(); idx = [n for n, l in enumerate(ls) if l["mod"] == mod]
    return (idx[0], idx[-1]) if idx else (0, -1)

def module_name(mod, lang):
    m = next(x for x in modules() if x[0] == mod); return f"{m[1]} {t3(m[2], lang)}"

def title(les, lang): return t3(les["title"], lang)

def start_of(mod):
    """Lesson id where a module starts (for placement recommendations)."""
    a, b = module_range(mod); return get(a)["id"]
