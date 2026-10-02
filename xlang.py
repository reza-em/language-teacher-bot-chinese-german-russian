"""German + Russian exercises, corrections and cards (Chinese lives in exercises.py / fmt.py; this module reuses their engine shapes).
All exercise dicts carry ex["L"] = language code and use the same fields the Telegram layer already understands."""
import random, re, difflib, unicodedata
from html import escape as esc
import langs, logic
import exercises as X
from texts import tr

IDX = {"fa": 0, "en": 1}
def T(lang, tup): return tup[IDX.get(lang, 1)] if len(tup) < 3 else tup[{"fa": 0, "en": 1, "de": 2}[lang]]

def ac(s, L): return langs.ru_accent(s) if L == "ru" else s
def disp(w): return w["ac"] if w.get("lang") == "ru" else w["hz"]
def lname(L, el): return langs.name(L, el)

Q = {
 "m2w": ("کدام واژهٔ {l} یعنی «{x}»؟", "Which {l} word means “{x}”?"),
 "type": ("«{x}» را به {l} بنویس:", "Write “{x}” in {l}:"),
 "dict": ("🎧 گوش کن و واژه را بنویس:", "🎧 Listen and type the word:"),
 "cloze": ("جای خالی را پر کن:\n\n<b>{x}</b>\n{tr}", "Fill in the blank:\n\n<b>{x}</b>\n{tr}"),
 "build": ("کلمه‌ها را به ترتیب درست بزن تا جمله ساخته شود:\n{tr}\n\n<b>{x}</b>", "Tap the words in the right order to build the sentence:\n{tr}\n\n<b>{x}</b>"),
 "art": ("حرف تعریف درست کدام است؟\n\n<b>___ {x}</b>", "Which article is right?\n\n<b>___ {x}</b>"),
 "plural": ("جمعِ <b>{x}</b> کدام است؟", "What is the plural of <b>{x}</b>?"),
 "stress": ("تکیه روی کدام مصوتِ «<b>{x}</b>» است؟", "Where is the stress in “<b>{x}</b>”?"),
 "gender": ("جنسیت واژهٔ <b>{x}</b> چیست؟", "What is the gender of <b>{x}</b>?"),
 "conj": ("شکل درست فعل را انتخاب کن:\n\n<b>{x}</b>", "Choose the correct verb form:\n\n<b>{x}</b>"),
 "drill": ("جای خالی را پر کن:\n\n<b>{x}</b>", "Fill in the blank:\n\n<b>{x}</b>"),
 "letter": ("حرف <b>{x}</b> چه صدایی دارد؟", "Which sound does the letter <b>{x}</b> make?"),
 "read": ("این واژه چطور خوانده می‌شود؟\n\n<b>{x}</b>", "How is this word read?\n\n<b>{x}</b>"),
 "hear": ("🎧 گوش کن: کدام واژه را شنیدی؟", "🎧 Listen: which word did you hear?"),
 "cyr": ("(با حروف سیریلیک بنویس)", "(write in Cyrillic)"),
}
def q(el, key, **kw):
    s = Q[key][IDX.get(el, 1)]; return s.format(**kw)

GENDER_NAMES = {"m": ("مذکر ♂", "masculine ♂"), "f": ("مؤنث ♀", "feminine ♀"), "n": ("خنثی ⚪", "neuter ⚪"), "pl": ("جمع (فقط جمع)", "plural only")}

# ---------------------------------------------------------------- helpers
def _pool(L, level):
    p = langs.pool(L, level); return p or langs.pool(L, 1)

def _opts_words(w, pool, k=3, same_pos=True):
    cands = [x for x in pool if x["i"] != w["i"] and x["hz"] != w["hz"] and (not same_pos or x["pos"] == w["pos"])]
    if len(cands) < k: cands = [x for x in pool if x["i"] != w["i"]]
    random.shuffle(cands); out = []
    for x in cands:
        if x["en"] == w["en"]: continue
        out.append(x)
        if len(out) == k: break
    return out

def _ex(t, w, el, L, text, **kw):
    ex = X._base(t, w, el, text, **kw); ex["L"] = L; return ex

def by_base(L):
    k = ("byb", L)
    if k not in langs._cache: langs._cache[k] = {w["base"].lower(): w for w in langs.words(L)}
    return langs._cache[k]

# ---------------------------------------------------------------- word exercises
def mk_w2m(w, pool, el):
    L = w["lang"]; ex = X.mk_zh2m(w, pool, el); ex["text"] = tr(el, "q_zh2m", x=esc(disp(w))); ex["L"] = L
    ex["audio"] = w["hz"]; ex["t"] = "zh2m"; return ex

def mk_m2w(w, pool, el):
    L = w["lang"]; right = X.meaning(w, el)[0]
    others = _opts_words(w, pool, 3)
    opts = [disp(w)] + [disp(o) for o in others]; opts = list(dict.fromkeys(opts)); random.shuffle(opts)
    if len(opts) < 3: return None
    return _ex("m2zh", w, el, L, q(el, "m2w", l=lname(L, el), x=esc(right)), opts=opts, ans=opts.index(disp(w)))

def mk_listen(w, pool, el):
    ex = mk_w2m(w, pool, el); ex["t"] = "listen"; ex["text"] = tr(el, "q_listen"); ex["hide_hz"] = True; return ex

def mk_type(w, pool, el):
    L = w["lang"]; m = X.meaning(w, el)[0]
    return _ex("x_type", w, el, L, q(el, "type", l=lname(L, el), x=esc(m)) + (" " + q(el, "cyr") if L == "ru" else "") + "\n\n" + tr(el, "type_hint"), ans=disp(w))

def mk_dict(w, pool, el):
    L = w["lang"]
    return _ex("x_dict", w, el, L, q(el, "dict") + (" " + q(el, "cyr") if L == "ru" else "") + "\n\n" + tr(el, "type_hint"), ans=disp(w), audio=w["hz"])

def _cloze_opts(s, w, L, pool):
    right = s["blank"]
    if w is not None:
        right = w["base"]; others = _opts_words(w, pool, 3)
        distract = [o["base"] for o in others]
    else:
        distract = [x["blank"] for x in langs.sentences(L) if x["blank"] and x["blank"].lower() != right.lower() and x["blank"] != s["blank"]]
        random.shuffle(distract); distract = distract[:3]
    # keep the sentence's surface form: German/Russian cloze words that are inflected come from the sentence itself
    right = s["blank"] if (w is None or w["base"].lower() != s["blank"].lower()) else w["base"]
    opts = list(dict.fromkeys([right] + distract))
    return right, opts

def blank_sentence(s):
    t = s["ac"] if s.get("ac") else s["t"]
    plain = s["t"]; b = s["blank"]
    # mask the blank in the displayed (stress-marked) sentence by matching the plain word position
    m = re.search(r"(?<!\w)" + re.escape(b) + r"(?!\w)", plain)
    if not m: return None
    return plain[:m.start()] + "＿＿" + plain[m.end():]

def mk_cloze_sent(s, w, pool, el, L):
    if not s.get("blank"): return None
    masked = blank_sentence(s)
    if not masked: return None
    right, opts = _cloze_opts(s, w, L, pool)
    if len(opts) < 3: return None
    random.shuffle(opts)
    trn = s["fa"] if el == "fa" else s["en"]
    return _ex("cloze", w, el, L, tr(el, "q_cloze", x=esc(masked), tr=esc(trn)), opts=opts, ans=opts.index(right), full=s["ac"], audio=None)

def mk_cloze(w, pool, el):
    L = w["lang"]; ss = langs.sentences_for(w)
    if not ss: return None
    return mk_cloze_sent(random.choice(ss), w, pool, el, L)

def mk_build_sent(s, w, el, L):
    toks = langs.tokens(s["t"])
    if not 3 <= len(toks) <= 8: return None
    order = list(range(len(toks))); random.shuffle(order)
    if order == list(range(len(toks))): order.reverse()
    trn = s["fa"] if el == "fa" else s["en"]
    return _ex("build", w, el, L, q(el, "build", tr=esc(trn), x=""), toks=toks, order=order, picked=[], ans=" ".join(toks), full=s["ac"], trn=trn, sep=" ", audio=None)

def mk_build(w, pool, el):
    L = w["lang"]; ss = langs.sentences_for(w)
    if not ss: return None
    return mk_build_sent(random.choice(ss), w, el, L)

# ---------------------------------------------------------------- German grammar-ish exercises
ART_TIPS = [(("ung", "heit", "keit", "schaft", "ion", "tät", "ik"), "die"), (("chen", "lein", "um", "ment"), "das"), (("ling", "ismus", "er"), "der")]
def art_rule(base, art):
    b = base.lower()
    for sufs, a in ART_TIPS:
        for suf in sufs:
            if b.endswith(suf) and a == art:
                return (f"💡 -{suf} → {a}",)
    return ()

def mk_art(w, pool, el):
    if w.get("art") is None: return None
    L = "de"; opts = ["der", "die", "das"]
    ex = _ex("x_art", w, el, L, q(el, "art", x=esc(w["base"])), opts=opts, ans=opts.index(w["art"]), row=3, audio=w["hz"])
    ex["explain"] = f"{w['art']} {w['base']}" + ((" · " + art_rule(w["base"], w["art"])[0]) if art_rule(w["base"], w["art"]) else "")
    return ex

def _umlaut(s):
    for i in range(len(s) - 1, -1, -1):
        if s[i] in "aou":
            if i + 1 < len(s) and s[i + 1] in "aeiou": continue
            return s[:i] + {"a": "ä", "o": "ö", "u": "ü"}[s[i]] + s[i + 1:]
        if s[i] in "AOU" and i == 0: return {"A": "Ä", "O": "Ö", "U": "Ü"}[s[i]] + s[1:]
    return s

def mk_plural(w, pool, el):
    pl = w.get("plural")
    if not pl or w.get("art") is None: return None
    b = w["base"]; um = _umlaut(b)
    if b.endswith("e"): cands = {b + "n", b + "s", b}
    else: cands = {b + "e", b + "en", b + "er", b + "s", b}
    if um != b: cands |= {um + "e", um + "er", um, um + "n" if b.endswith("e") else um + "e"}
    if b.endswith(("er", "el", "en")): cands = {c for c in cands if not c.endswith(("en", "er")) or c == b} | {um, b + "n" if b.endswith("e") else b + "s"}
    cands.discard(pl); cands = [c for c in cands if c != pl]
    random.shuffle(cands); opts = [pl] + cands[:3]
    if len(opts) < 3: return None
    random.shuffle(opts)
    ex = _ex("x_plural", w, el, "de", q(el, "plural", x=esc(w["hz"])), opts=["die " + o for o in opts], ans=opts.index(pl), audio=w["hz"])
    ex["explain"] = f"{w['hz']} → die {pl}"
    return ex

REG_DE = ["wohnen", "lernen", "machen", "kaufen", "spielen", "hören", "fragen", "sagen", "kochen", "besuchen", "brauchen", "lieben"]
DE_PRON = [("ich", "e"), ("du", "st"), ("er", "t"), ("wir", "en"), ("ihr", "t"), ("sie (pl.)", "en")]
def mk_conj_de(el, w=None):
    verb = w["base"] if (w and w["base"] in REG_DE) else random.choice(REG_DE)
    stem = verb[:-2] if verb.endswith("en") else verb[:-1]
    pron, suf = random.choice(DE_PRON); right = stem + suf
    wrong = list({stem + s for _, s in DE_PRON} - {right}); random.shuffle(wrong)
    opts = [right] + wrong[:3]; random.shuffle(opts)
    vw = by_base("de").get(verb)
    ex = _ex("x_conj", vw, el, "de", q(el, "conj", x=f"{pron} ___ ({verb})"), opts=opts, ans=opts.index(right))
    ex["explain"] = f"{pron} {right}  (-e, -st, -t, -en, -t, -en)"
    return ex

REG_RU = ["чита'ть", "знать", "де'лать", "ду'мать", "рабо'тать", "слу'шать", "игра'ть", "понима'ть", "гуля'ть", "отдыха'ть", "спра'шивать"]
RU_PRON = [("я", "ю"), ("ты", "ешь"), ("он", "ет"), ("мы", "ем"), ("вы", "ете"), ("они'", "ют")]
def _ru_stem(inf):
    s = inf[:-2] if inf.endswith("ть") else inf
    return s                                   # keep stress apostrophe on the stem vowel (stress stays on the stem in these verbs)
def mk_conj_ru(el, w=None, mode=None):
    verb = random.choice(REG_RU); stem = _ru_stem(verb)
    if (mode == "pres") or (mode is None and random.random() < 0.5):
        pron, suf = random.choice(RU_PRON); right = stem + suf
        wrong = list({stem + s for _, s in RU_PRON} - {right}); random.shuffle(wrong)
        text = f"{pron} ___ ({verb})"; ex_note = f"{pron} {right}"
    else:
        sub = random.choice([("он", "л"), ("она'", "ла"), ("оно'", "ло"), ("они'", "ли")]); pron, suf = sub
        right = stem + suf; wrong = list({stem + s for s in ("л", "ла", "ло", "ли")} - {right}); random.shuffle(wrong)
        text = f"{pron} ___ ({verb}, прошлое)"; ex_note = f"{pron} {right}  (-л / -ла / -ло / -ли)"
    opts = [right] + wrong[:3]; random.shuffle(opts)
    vw = by_base("ru").get(langs.ru_plain(verb))
    ex = _ex("x_conj", vw, el, "ru", q(el, "conj", x=esc(ac(text, "ru"))), opts=[ac(o, "ru") for o in opts], ans=opts.index(right))
    ex["explain"] = ac(ex_note, "ru")
    return ex

def mk_plural_ru(w, pool, el):
    pl = langs.ru_plain(w.get("plural") or "")
    if not pl or w.get("gender") not in ("m", "f", "n"): return None
    b = w["hz"]; st = b[:-1] if b[-1] in "аяоеьй" else b
    cands = {st + x for x in ("ы", "и", "а", "я", "ов", "ей", "е", "ей", "ы")} | {b + "ы", b + "и", b + "а"}
    cands.discard(pl); cands.discard(b); cands = list(cands); random.shuffle(cands)
    opts = [pl] + cands[:3]
    if len(opts) < 3: return None
    random.shuffle(opts)
    ex = _ex("x_plural", w, el, "ru", q(el, "plural", x=esc(w["ac"])), opts=opts, ans=opts.index(pl), audio=w["hz"])
    ex["explain"] = f"{w['ac']} → {w['plural']}"
    return ex

def mk_stress(w, pool, el):
    V = "аеёиоуыэюя"; plain = w["hz"]; idxs = [i for i, c in enumerate(plain) if c in V]
    if len(idxs) < 2 or " " in plain or "ё" in plain: return None
    acc = w["ac"]; pos = acc.find(langs.ACUTE)
    if pos < 1: return None
    right_i = pos - 1
    if right_i not in idxs: return None
    chosen = [right_i] + random.sample([i for i in idxs if i != right_i], min(3, len(idxs) - 1)); random.shuffle(chosen)
    opts = [plain[:i + 1] + langs.ACUTE + plain[i + 1:] for i in chosen]
    return _ex("x_stress", w, el, "ru", q(el, "stress", x=esc(plain)), opts=opts, ans=chosen.index(right_i), audio=plain,
               explain=f"{acc} — " + {"fa": "تکیه در روسی ثابت نیست؛ با هر واژه یاد بگیر.", "en": "Russian stress is not fixed; learn it with each word."}[el if el in IDX else "en"])

def mk_gender(w, pool, el):
    g = w.get("gender")
    if g not in ("m", "f", "n"): return None
    keys = ["m", "f", "n"]
    opts = [T(el, GENDER_NAMES[k]) for k in keys]
    b = w["hz"]; tip = ""
    if b.endswith(("а", "я")): tip = "-а/-я → ♀"
    elif b.endswith(("о", "е")): tip = "-о/-е → ⚪"
    elif b.endswith("ь"): tip = {"fa": "-ь: هم مذکر هم مؤنث ممکن است؛ باید حفظ کرد.", "en": "-ь: can be masculine or feminine; learn it."}[el if el in IDX else "en"]
    elif b[-1] not in "аеёиоуыэюя": tip = "consonant → ♂"
    return _ex("x_gender", w, el, "ru", q(el, "gender", x=esc(w["ac"])), opts=opts, ans=keys.index(g), row=3, audio=w["hz"], explain=f"{w['ac']}: {opts[keys.index(g)]}  {tip}")

# ---------------------------------------------------------------- authored drills
def drill_list(L):
    if L == "de":
        import content.de_extra as E
    else:
        import content.ru_extra as E
    return E.DRILLS

def mk_drill(L, el, idx=None):
    ds = drill_list(L); i = random.randrange(len(ds)) if idx is None else idx % len(ds)
    sent, options, right, expl = ds[i]
    opts = list(options); random.shuffle(opts)
    return mk_drill_fixed(L, el, i, opts)

def mk_drill_fixed(L, el, i, opts=None):
    sent, options, right, expl = drill_list(L)[i]
    opts = opts or list(options)
    ex = _ex("x_drill", None, el, L, q(el, "drill", x=esc(ac(sent, L))), opts=[ac(o, L) for o in opts], ans=opts.index(right), explain=ac(T(el, expl), L) + f"  →  {ac(sent, L).replace('___', ac(right, L))}", di=i)
    return ex


# ---------------------------------------------------------------- programmatic case drills (use the learner's own nouns)
DE_ACC = {"der": "den", "die": "die", "das": "das"}
DE_DAT = {"der": "dem", "die": "der", "das": "dem"}
def mk_case_de(w, pool, el, case=None):
    if w.get("art") is None: return None
    case = case or random.choice(["acc", "dat"]); art = w["art"]; b = w["base"]
    if case == "acc":
        right = DE_ACC[art]; sent = f"Ich sehe ___ {b}."; opts = ["der", "die", "das", "den"]
        why = {"fa": f"مفعولی: فقط مذکر تغییر می‌کند (der → den). {art} {b} ← {right} {b}", "en": f"accusative: only masculine changes (der → den). {art} {b} → {right} {b}"}
    else:
        right = DE_DAT[art]; sent = f"Ich helfe ___ {b}."; opts = ["dem", "der", "den", "die"]
        why = {"fa": f"با helfen حالت دوم‌شخصی (Dativ) می‌آید: der/das → dem، die → der. {art} {b} ← {right} {b}", "en": f"helfen takes the dative: der/das → dem, die → der. {art} {b} → {right} {b}"}
    random.shuffle(opts)
    return _ex("x_drill", w, el, "de", q(el, "drill", x=esc(sent)), opts=opts, ans=opts.index(right), explain=why[el if el in IDX else "en"] + f"  →  {sent.replace('___', right)}")

RU_PREP_BLACK = {"лес", "сад", "мост", "угол", "шкаф", "год", "аэропорт", "пол", "нос", "лёд", "берег", "снег", "глаз", "край", "рот", "порт", "мозг", "бок", "ряд", "тыл"}
def _ru_forms(w):
    b = w["hz"]; g = w.get("gender")
    if g == "f" and b.endswith("а") and not b.endswith("ия"):
        st = b[:-1]; return {"nom": b, "acc": st + "у", "gen": st + ("и" if st[-1] in "гкхжшчщ" else "ы"), "prep": st + "е"}
    if g == "f" and b.endswith("я") and not b.endswith(("ия", "ья")):
        st = b[:-1]; return {"nom": b, "acc": st + "ю", "gen": st + "и", "prep": st + "е"}
    if g == "m" and b[-1] not in "ьйаяеёиоуыэюя" and b not in RU_PREP_BLACK and not b.endswith(("ц", "г")) and w.get("pos") == ["n"]:
        return {"nom": b, "acc": b, "gen": b + "а", "prep": b + "е"}
    if g == "n" and b.endswith("о") and not b.endswith(("ье",)):
        st = b[:-1]; return {"nom": b, "acc": b, "gen": st + "а", "prep": st + "е"}
    return None

def mk_case_ru(w, pool, el, case=None):
    f = _ru_forms(w)
    if not f: return None
    case = case or random.choice(["acc", "prep", "gen"])
    if case == "acc":
        if f["acc"] == f["nom"]: case = "prep"
    if case == "gen":
        sent = "У меня нет ___."; right = f["gen"]; cand = [f["nom"], f["prep"], f["acc"] if f["acc"] != f["nom"] else f["prep"] + "м"]
        why = {"fa": f"بعد از «нет» حالت اضافه (Родительный) می‌آید ({f['nom']} ← {f['gen']})", "en": f"after “нет” comes the genitive ({f['nom']} → {f['gen']})"}
        opts = list(dict.fromkeys([right] + [c for c in cand if c != right])); random.shuffle(opts)
        if len(opts) < 3: return None
        return _ex("x_drill", w, el, "ru", q(el, "drill", x=esc(sent) + f"\n({esc(w['hz'])} — {esc(X.meaning(w, el)[0])})"), opts=opts, ans=opts.index(right), explain=why[el if el in IDX else "en"] + f"  →  {sent.replace('___', right)}")
    if case == "acc":
        sent = "Я вижу ___."; right = f["acc"]; cand = [f["nom"], f["gen"], f["prep"]]
        why = {"fa": f"مفعولی مؤنث: -а ← -у، -я ← -ю ({f['nom']} ← {f['acc']})", "en": f"accusative feminine: -а → -у, -я → -ю ({f['nom']} → {f['acc']})"}
    else:
        o = "об" if w["hz"][0] in "аэиоу" else "о"
        sent = f"Мы говорим {o} ___."; right = f["prep"]; cand = [f["nom"], f["gen"], f["acc"] if f["acc"] != f["nom"] else f["gen"][:-1] + "у"]
        why = {"fa": f"بعد از «{o}» حالت حرف‌اضافه‌ای (Предложный) می‌آید: پایان -е ({f['nom']} ← {f['prep']})", "en": f"after “{o}” comes the prepositional case: ending -е ({f['nom']} → {f['prep']})"}
    opts = list(dict.fromkeys([right] + [c for c in cand if c != right]))
    if len(opts) < 3: return None
    random.shuffle(opts)
    return _ex("x_drill", w, el, "ru", q(el, "drill", x=esc(sent) + f"\n({esc(w['hz'])} — {esc(X.meaning(w, el)[0])})"), opts=opts, ans=opts.index(right), explain=why[el if el in IDX else "en"] + f"  →  {sent.replace('___', right)}")

# ---------------------------------------------------------------- Russian alphabet / reading
def alphabet():
    import content.ru_extra as E
    return E.ALPHABET

def mk_letter(el, i=None):
    A_ = alphabet(); i = random.randrange(len(A_)) if i is None else i % len(A_)
    up, tr_, fa, en, ex_w, mean = A_[i]
    right = tr_ or "—"
    # distinct transliterations only (several letters can share one: е/э, ь/ъ have none)
    pool = [a for a in A_ if a[1] and a[1] != right and a[0] != up]
    random.shuffle(pool); opts = [right]
    for a in pool:
        if a[1] not in opts: opts.append(a[1])
        if len(opts) == 4: break
    if not tr_:
        return None
    random.shuffle(opts)
    return _ex("x_letter", None, el, "ru", q(el, "letter", x=esc(up)), opts=opts, ans=opts.index(right), row=4, audio=langs.ru_plain(ex_w),
               explain=f"{up} = {right} — {ac(ex_w, 'ru')} ({mean})", li=i)

def _translit_distractors(w, pool, k=3):
    right = langs.translit(w["ac"])
    cands = [langs.translit(x["ac"]) for x in pool if x["i"] != w["i"] and abs(len(x["hz"]) - len(w["hz"])) <= 1]
    cands = [c for c in dict.fromkeys(cands) if c != right]; random.shuffle(cands); return right, cands[:k]

def mk_read(w, pool, el):
    right, d = _translit_distractors(w, pool)
    if len(d) < 2: return None
    opts = [right] + d; random.shuffle(opts)
    return _ex("x_read", w, el, "ru", q(el, "read", x=esc(w["hz"])), opts=opts, ans=opts.index(right), audio=w["hz"], explain=f"{w['ac']} = {right}")

def sound_words(L):
    """Words from the pronunciation rules / alphabet examples (for 'which word did you hear')."""
    out = []
    if L == "de":
        import content.de_extra as E
        for t, b, exs in E.SOUNDS: out += [x.strip() for x in re.split(r"[·/,]", exs)]
    else:
        import content.ru_extra as E
        for r in E.RULES: out += [x.strip() for x in re.split(r"[·/,]", r[2])]
        out += [a[4] for a in E.ALPHABET]
    return [langs.ru_plain(x) for x in dict.fromkeys(o for o in out if o and " " not in o and len(o) > 1)]

def mk_hear(L, el, target=None, wordlist=None):
    wl = wordlist or sound_words(L)
    if len(wl) < 4: return None
    r = target or random.choice(wl); others = [x for x in wl if x != r]; random.shuffle(others)
    opts = [r] + others[:3]; random.shuffle(opts)
    return _ex("x_hear", None, el, L, q(el, "hear"), opts=[ac(o, L) if L == "ru" else o for o in opts], ans=opts.index(r), audio=langs.ru_plain(r), explain=r)

def mk_sound_pair(L, el):
    """German minimal pairs / rule words: hear and choose."""
    return mk_hear(L, el)

# ---------------------------------------------------------------- dispatcher
CREATORS = {"x_case": lambda w, p, el: (mk_case_de if w.get("lang") == "de" else mk_case_ru)(w, p, el), "zh2m": mk_w2m, "m2zh": mk_m2w, "listen": mk_listen, "x_type": mk_type, "x_dict": mk_dict, "cloze": mk_cloze, "build": mk_build}
MIX = {"de": ["zh2m", "m2zh", "listen", "x_type", "x_dict", "cloze", "build", "match", "x_art", "x_plural", "x_conj", "x_drill", "x_case"],
       "ru": ["zh2m", "m2zh", "listen", "x_type", "x_dict", "cloze", "build", "match", "x_stress", "x_gender", "x_plural", "x_conj", "x_drill", "x_read", "x_case"]}
KIND_MAP = {"art": "x_art", "plural": "x_plural", "stress": "x_stress", "gender": "x_gender", "drill": "x_drill", "conj": "x_conj", "type": "x_type", "dict": "x_dict", "read": "x_read", "letter": "x_letter",
            "pytype": "x_type", "listen_py": "x_dict", "snd": "x_snd", "radical": None, "strokes": None, "recog": "zh2m", "tone": None, "fa2zh": "x_type", "zh2fa": "zh2m"}

def _word_for(t, uid, level, L, pool):
    """A word suited to exercise type t (a sentence for cloze/build, a noun for article/plural/gender ...), preferring the learner's due/learned words."""
    need = {"cloze": lambda w: bool(langs.sentences_for(w)), "build": lambda w: bool(langs.sentences_for(w)), "x_art": lambda w: bool(w.get("art")), "x_plural": lambda w: bool(w.get("plural")),
            "x_stress": lambda w: len(re.findall("[аеёиоуыэюя]", w["hz"])) > 1, "x_gender": lambda w: w.get("gender") in ("m", "f", "n"), "x_case": lambda w: bool(w.get("art") if L == "de" else _ru_forms(w))}.get(t)
    ws = X.choose_words(uid, 12, level, lang=L)
    if need:
        c = [w for w in ws if need(w)]
        if not c:
            c = [w for w in pool if need(w)]; random.shuffle(c)
        if c: return c[0]
    return ws[0]

def make_exercise(uid, L, kind=None, word=None, avoid_types=(), profile=None):
    if profile: el = profile["lang"]; level = profile["level"]
    else: u = logic.get_user(uid); el = logic.expl_lang(uid); level = u["level"]
    pool = _pool(L, level)
    kind = KIND_MAP.get(kind, kind) if kind in KIND_MAP else kind
    if kind in ("mix", None) and level == 0 and L == "ru" and not (profile and profile.get("types")):
        kind = random.choice(["x_letter", "x_read", "x_letter", "zh2m", "listen", "x_hear"])
    for _ in range(14):
        t = kind or random.choice([x for x in MIX[L] if x not in avoid_types] or MIX[L])
        if t == "match":
            ws = X.choose_words(uid, 4, level, lang=L); ex = X.mk_match(ws, el)
            if ex:
                ex["L"] = L; ex["text"] = {"fa": f"🔗 جفت‌ها را وصل کن: اول یک واژهٔ {lname(L, el)}، بعد معنی‌اش را بزن.", "en": f"🔗 Match the pairs: tap a {lname(L, el)} word, then its meaning."}[el if el in IDX else "en"]
                ex["left"] = [disp(x) for x in ws[:4]]; return ex
            continue
        if t == "x_drill": return mk_drill(L, el)
        if t == "x_letter":
            ex = mk_letter(el) if L == "ru" else None
            if ex: return ex
            kind = None; continue
        if t == "x_snd" or t == "x_hear":
            ex = mk_hear(L, el)
            if ex: return ex
            kind = None; continue
        if t == "x_conj": return mk_conj_de(el) if L == "de" else mk_conj_ru(el)
        w = word or _word_for(t, uid, level, L, pool)
        fn = {"x_art": mk_art, "x_plural": mk_plural if L == "de" else mk_plural_ru, "x_stress": mk_stress, "x_gender": mk_gender, "x_read": mk_read}.get(t) or CREATORS.get(t)
        if fn is None: kind = None; continue
        if (t == "x_art" and L != "de") or (t in ("x_stress", "x_gender", "x_read") and L != "ru"):
            kind = None; continue
        ex = fn(w, pool, el)
        if ex: return ex
        word = None
        if kind in ("x_art", "x_plural", "x_stress", "x_gender", "x_read", "cloze", "build"):
            kind = kind if _ < 8 else None
    w = X.choose_words(uid, 1, level, lang=L)[0]
    return mk_w2m(w, pool, el)

# ---------------------------------------------------------------- checking typed answers
def _fold_de(s):
    s = unicodedata.normalize("NFC", s.strip()).lower().replace("ß", "ss")
    return s
def _umlaut_free(s):
    return _fold_de(s).replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
def _plain_de(s):
    return _fold_de(s).replace("ä", "a").replace("ö", "o").replace("ü", "u")
def _rustrip(s): return langs.strip_marks(s)

def _closeness(a, b): return difflib.SequenceMatcher(None, a, b).ratio()

def mark_diff(right, given):
    """Show where a typed answer differs: wrong letters of the answer are wrapped in [ ]."""
    sm = difflib.SequenceMatcher(None, given.lower(), right.lower()); out = []
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        seg = right[b1:b2]
        out.append(seg if op == "equal" else (f"[{seg}]" if seg else ""))
    return "".join(out)

def check_text(ex, given, uid=None):
    el = ex["lang"]; L = ex.get("L"); w = logic.get_word(ex["wid"]) if ex.get("wid") is not None else None
    g = (given or "").strip(); lines = []
    right = ex["ans"]
    if L == "ru":
        if re.search(r"[A-Za-z]", g) and not re.search(r"[\u0400-\u04ff]", g):
            return X.result(False, el, right=right, lines=[{"fa": "⌨️ با حروف سیریلیک بنویس (مثلاً «привет»)؛ کیبورد روسی را فعال کن.", "en": "⌨️ Please type in Cyrillic (e.g. “привет”); enable a Russian keyboard."}[el if el in IDX else "en"], X.word_line(w, el)] if w else [], word=w, given=g)
        ok = _rustrip(g) == _rustrip(right)
        if ok:
            lines = []
            if w and w.get("ac") and langs.ACUTE not in g: lines.append("📌 " + {"fa": "تکیه: ", "en": "Stress: "}[el if el in IDX else "en"] + w["ac"])
            return X.result(True, el, right=right, lines=lines, word=w, given=g)
        r = _closeness(_rustrip(g), _rustrip(right))
        if r >= 0.75: lines.append({"fa": "✏️ تقریباً درست! املا را دوباره نگاه کن: ", "en": "✏️ Almost! Check the spelling: "}[el if el in IDX else "en"] + mark_diff(right, g))
        if w: lines.append(X.word_line(w, el))
        return X.result(False, el, right=right, lines=lines, word=w, given=g)
    # German
    base = w["base"] if w else right; art = (w or {}).get("art")
    toks = g.split()
    gart = None
    if len(toks) == 2 and toks[0].lower() in ("der", "die", "das"): gart, g2 = toks[0].lower(), toks[1]
    else: g2 = g
    ok_word = _fold_de(g2) == _fold_de(base)
    if ok_word and art and gart and gart != art:
        return X.result(False, el, right=right, lines=[{"fa": f"🔤 واژه درست است ولی حرف تعریف اشتباه: <b>{art}</b> {esc(base)}", "en": f"🔤 Right word, wrong article: <b>{art}</b> {esc(base)}"}[el if el in IDX else "en"], X.word_line(w, el)], word=w, given=g)
    if ok_word:
        lines = []
        if art and not gart: lines.append({"fa": f"📌 یادت نرود حرف تعریف: <b>{art}</b> {esc(base)}", "en": f"📌 Remember the article: <b>{art}</b> {esc(base)}"}[el if el in IDX else "en"])
        if g2 != base and g2.lower() == base.lower() and base[0].isupper():
            lines.append({"fa": "📌 اسم‌ها در آلمانی با حرف بزرگ نوشته می‌شوند.", "en": "📌 German nouns are written with a capital letter."}[el if el in IDX else "en"])
        return X.result(True, el, right=right, lines=lines, word=w, given=g)
    if _umlaut_free(g2) == _umlaut_free(base) or _plain_de(g2) == _plain_de(base):
        return X.result(True, el, right=right, almost=True, lines=[{"fa": f"✏️ تقریباً درست: املای درست <b>{esc(base)}</b> است (اومالوت/ß را فراموش نکن؛ ae=ä, oe=ö, ue=ü, ss=ß).", "en": f"✏️ Almost: the correct spelling is <b>{esc(base)}</b> (mind umlauts/ß: ae=ä, oe=ö, ue=ü, ss=ß)."}[el if el in IDX else "en"]], word=w, given=g)
    if _closeness(_fold_de(g2), _fold_de(base)) >= 0.75:
        lines.append({"fa": "✏️ تقریباً درست! املا: ", "en": "✏️ Almost! Spelling: "}[el if el in IDX else "en"] + mark_diff(base, g2))
    if w: lines.append(X.word_line(w, el))
    return X.result(False, el, right=right, lines=lines, word=w, given=g)

# ---------------------------------------------------------------- cards (word card text for the non-Chinese languages)
def word_card(w, ui, el, with_example=True):
    L = w["lang"]; mean, src = logic.gloss(w, el)
    head = f"<b>{esc(disp(w))}</b>"
    extra = ""
    if L == "de":
        if w.get("art"): extra = f"{esc('Pl. die ' + w['plural']) if w.get('plural') else 'Pl. —'}"
        elif w["pos"] == ["v"] and w.get("py"): extra = esc(w["py"])
    else:
        extra = f"[{esc(langs.translit(w['ac']))}]"
        if w.get("gender"): extra += "  " + {"m": "♂", "f": "♀", "n": "⚪", "pl": "pl."}.get(w["gender"], "")
        if w.get("plural"): extra += f"  · pl. {esc(w['plural'])}"
        elif w["pos"] == ["v"] and w.get("extra"): extra += f"  · {esc(ac(w['extra'], 'ru'))}"
    lines = [esc(mean)]
    if el != "en" and w.get("en"): lines.append("🇬🇧 " + esc(w["en"]))
    ex = ""
    if with_example:
        ss = langs.sentences_for(w)
        if ss:
            s = ss[0]; ex = f"\n\n📝 {esc(s['ac'])}\n<i>{esc(s['fa'] if el == 'fa' else s['en'])}</i>"
    tag = langs.level_name(L, w["lv"])
    return f"{head}  {extra}  <code>{tag}</code>\n\n" + "\n".join(lines)+ ex

# ---------------------------------------------------------------- checking choices / building
def check_choice(ex, idx):
    el = ex["lang"]; ok = idx == ex["ans"]; w = logic.get_word(ex["wid"]) if ex.get("wid") is not None else None
    right = ex["opts"][ex["ans"]]; lines = []
    if w and not ok and ex["t"] not in ("x_art", "x_plural", "x_conj"): lines.append(X.word_line(w, el))
    if not ok and ex.get("explain"): lines.append(f"💡 {esc(str(ex['explain']))}")
    elif ok and ex["t"] in ("x_drill", "x_gender", "x_stress", "x_art", "x_plural", "x_conj") and ex.get("explain"):
        lines.append(f"💡 {esc(str(ex['explain']))}")
    if ex["t"] == "cloze" and ex.get("full"): lines.append(f"📝 {esc(ex['full'])}")
    if not ok and w and ex["t"] in ("x_art", "x_plural"): lines.append(X.word_line(w, el))
    return X.result(ok, el, right=right, lines=lines, word=w, given=ex["opts"][idx] if 0 <= idx < len(ex["opts"]) else "")

REMIND = {
 "de": ("یادآوری: در جملهٔ خبری آلمانی فعل همیشه در جایگاه دوم است (Ich lerne heute Deutsch / Heute lerne ich Deutsch).", "Reminder: in a German statement the verb is always in position 2 (Ich lerne heute Deutsch / Heute lerne ich Deutsch)."),
 "ru": ("یادآوری: ترتیب واژه‌ها در روسی آزادتر است، ولی ترتیب خنثی «فاعل – فعل – مفعول» است و حرف ربط/نفی کنار فعل می‌آید.", "Reminder: Russian word order is freer, but the neutral order is subject – verb – object."),
}
def check_build(ex):
    el = ex["lang"]; L = ex.get("L"); sep = ex.get("sep", " ")
    got = sep.join(ex["toks"][i] for i in ex["picked"]); ok = got == ex["ans"]
    w = logic.get_word(ex["wid"]) if ex.get("wid") is not None else None
    lines = []
    if not ok:
        lines.append(({"fa": "🧩 جملهٔ درست: ", "en": "🧩 Correct sentence: "}[el if el in IDX else "en"]) + f"<b>{esc(ex['full'])}</b>\n" + T(el, REMIND[L]))
        if w: lines.append(X.word_line(w, el))
    return X.result(ok, el, right=ex["full"], lines=lines, word=w, given=got)
