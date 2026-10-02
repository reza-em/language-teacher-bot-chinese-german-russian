"""Exercise generation + checking (+ explanations/corrections). Pure logic: returns dicts / strings, no Telegram calls."""
import random, re, json
import config, data, logic, llm
import pinyin_utils as P
from texts import tr
from textnorm import norm_fa, norm_latin

CHOICE_TYPES = {"zh2m", "m2zh", "recog", "tone", "listen", "radical", "strokes", "cloze", "custom", "course", "snd_init", "snd_final", "snd_tone",
                "x_art", "x_plural", "x_stress", "x_gender", "x_conj", "x_drill", "x_letter", "x_read", "x_hear"}
TEXT_TYPES = {"pytype", "fa2zh", "zh2fa", "listen_py", "trans", "x_type", "x_dict"}
ALL_MIX = ["zh2m", "m2zh", "recog", "tone", "pytype", "fa2zh", "zh2fa", "cloze", "build", "listen", "listen_py", "match", "radical", "strokes"]
METHOD_TYPES = {
    "flashcards": ["zh2m", "m2zh"], "mnemonic": ["recog", "zh2m"], "radicals": ["radical", "recog"], "strokes": ["strokes", "radical"],
    "dictation": ["listen", "listen_py"], "pinyin": ["pytype", "tone"], "building": ["build"], "cloze": ["cloze"], "matching": ["match"],
}

TIPS = {  # confusion key -> (fa, en, de)
 "conf_zh_z": ("zh با زبان برگشته است، z بدون آن.", "zh has the tongue curled back; z doesn't.", "zh mit zurückgebogener Zunge, z ohne."),
 "conf_ch_c": ("ch با زبان برگشته است، c بدون آن.", "ch is retroflex; c is not.", "ch ist retroflex, c nicht."),
 "conf_sh_s": ("sh شبیه «ش» با زبان برگشته است، s مثل «س».", "sh is retroflex “sh”; s is plain “s”.", "sh ist retroflex „sch“, s ist einfaches „s“."),
 "conf_j_zh": ("j با زبان تخت پشت دندان پایین است؛ zh برگشته.", "j has a flat tongue; zh is curled back.", "j mit flacher Zunge; zh zurückgebogen."),
 "conf_q_ch": ("q زبان تخت است؛ ch برگشته.", "q has a flat tongue; ch is curled back.", "q mit flacher Zunge; ch zurückgebogen."),
 "conf_x_sh": ("x زبان تخت است؛ sh برگشته.", "x has a flat tongue; sh is curled back.", "x mit flacher Zunge; sh zurückgebogen."),
 "conf_n_l": ("n خیشومی است، l از کناره‌ی زبان.", "n is nasal; l is lateral.", "n ist nasal, l lateral."),
 "conf_b_p": ("b بدون فوت هوا، p با فوت هوا.", "b is unaspirated; p is aspirated.", "b ohne Hauch, p mit Hauch."),
 "conf_d_t": ("d بدون فوت هوا، t با فوت هوا.", "d is unaspirated; t is aspirated.", "d ohne Hauch, t mit Hauch."),
 "conf_g_k": ("g بدون فوت هوا، k با فوت هوا.", "g is unaspirated; k is aspirated.", "g ohne Hauch, k mit Hauch."),
 "conf_an_ang": ("an با n (زبان بالا می‌رود)، ang با «نگ» (دهان باز می‌ماند).", "an ends with n; ang ends with the “ng” sound.", "an endet auf n, ang auf „ng“."),
 "conf_en_eng": ("en با n، eng با «نگ».", "en ends with n; eng with “ng”.", "en endet auf n, eng auf „ng“."),
 "conf_in_ing": ("in با n، ing با «نگ».", "in ends with n; ing with “ng”.", "in endet auf n, ing auf „ng“."),
 "conf_u_v": ("u مثل «او»ی کشیده، ü با لب گرد مثل «ی» گفتن.", "u is “oo”; ü is “ee” with rounded lips.", "u wie „u“; ü wie „i“ mit gerundeten Lippen."),
 "conf_ie_ei": ("ie یعنی i+e، ei یعنی e+i.", "ie is i+e; ei is e+i.", "ie ist i+e, ei ist e+i."),
}
LI = {"fa": 0, "en": 1, "de": 2}

def _short(s, n=42):
    s = re.split(r"[;؛]|\s\(", s)[0].strip(" ,،")
    return s[:n]

def meaning(w, lang):
    """Short meaning for options/answers + source."""
    g, src = logic.gloss(w, lang)
    return _short(g), src

def full_meaning(w, lang):
    g, src = logic.gloss(w, lang)
    return g, src

def _sample_other(pool, w, k, same_len=False, avoid_gloss=None):
    cands = [x for x in pool if x["i"] != w["i"] and x["hz"] != w["hz"]]
    if same_len: 
        c2 = [x for x in cands if len(x["hz"]) == len(w["hz"])]
        if len(c2) >= k: cands = c2
    random.shuffle(cands)
    out = []; seen = set(avoid_gloss or [])
    for x in cands:
        key = x["en"]
        if key in seen: continue
        seen.add(key); out.append(x)
        if len(out) == k: break
    return out

def word_line(w, lang):
    m, _ = full_meaning(w, lang)
    return tr(lang, "explain_word", hz=w["hz"], py=w["py"], mean=_short(m, 90))

def tone_of_syllable(w):
    parsed = P.parse(w["py"])
    return [(b, t or 5) for b, t in parsed]

# ---------------- creators: each returns ex dict ----------------
def _base(t, w, lang, text, **kw):
    ex = {"t": t, "wid": w["i"] if w else None, "lang": lang, "text": text, "ts": 0}; ex.update(kw); return ex

def mk_zh2m(w, pool, lang):
    right, _ = meaning(w, lang)
    others = _sample_other(pool, w, 3, avoid_gloss=[w["en"]])
    opts = [right] + [meaning(o, lang)[0] for o in others]
    opts = list(dict.fromkeys(opts))
    while len(opts) < 4: opts.append(random.choice(pool)["en"][:30])
    random.shuffle(opts)
    return _base("zh2m", w, lang, tr(lang, "q_zh2m", x=w["hz"]), opts=opts, ans=opts.index(right), audio=w["hz"])

def mk_m2zh(w, pool, lang):
    right, _ = meaning(w, lang)
    others = _sample_other(pool, w, 3, same_len=True, avoid_gloss=[w["en"]])
    opts = [w["hz"]] + [o["hz"] for o in others]; random.shuffle(opts)
    return _base("m2zh", w, lang, tr(lang, "q_m2zh", x=right), opts=opts, ans=opts.index(w["hz"]))

def mk_recog(w, pool, lang):
    others = _sample_other(pool, w, 3, same_len=True)
    opts = [w["hz"]] + [o["hz"] for o in others]; random.shuffle(opts)
    return _base("recog", w, lang, tr(lang, "q_recog", x=w["py"]), opts=opts, ans=opts.index(w["hz"]), audio=w["hz"])

def mk_tone(w, pool, lang):
    syl = tone_of_syllable(w); i = random.randrange(len(syl)); b, t = syl[i]
    opts = ["1 ˉ", "2 ˊ", "3 ˇ", "4 ˋ", "5 · (0)"]
    return _base("tone", w, lang, tr(lang, "q_tone", x=b, w=w["hz"]), opts=opts, ans=t - 1, audio=w["hz"], row=5, syl=i)

def mk_pytype(w, pool, lang):
    return _base("pytype", w, lang, tr(lang, "q_pytype", x=w["hz"]) + "\n\n" + tr(lang, "type_hint"), ans=w["py"], audio=w["hz"])

def mk_fa2zh(w, pool, lang):
    m, _ = meaning(w, lang)
    return _base("fa2zh", w, lang, tr(lang, "q_fa2zh", x=m) + "\n\n" + tr(lang, "type_hint"), ans=w["hz"])

def mk_zh2fa(w, pool, lang):
    return _base("zh2fa", w, lang, tr(lang, "q_zh2fa", x=w["hz"]) + "\n\n" + tr(lang, "type_hint"), ans=w["hz"], audio=w["hz"])

def mk_listen(w, pool, lang):
    ex = mk_zh2m(w, pool, lang); ex["t"] = "listen"; ex["text"] = tr(lang, "q_listen"); ex["audio"] = w["hz"]; ex["hide_hz"] = True
    return ex

def mk_listen_py(w, pool, lang):
    return _base("listen_py", w, lang, tr(lang, "q_listen_py") + "\n\n" + tr(lang, "type_hint"), ans=w["py"], audio=w["hz"])

def mk_radical(w, pool, lang):
    ch = next((c for c in w["hz"] if data.is_hanzi(c)), None)
    ci = data.char_info(ch) if ch and data.available() else None
    if not ci or not ci["radical"]: return None
    rad = ci["radical"]
    allr = list({(data.char_info(c) or {}).get("radical") for x in pool[:200] for c in x["hz"] if data.is_hanzi(c)} - {None, "", rad})
    random.shuffle(allr)
    if len(allr) < 3: return None
    opts = [rad] + allr[:3]; random.shuffle(opts)
    return _base("radical", w, lang, tr(lang, "q_radical", x=ch), opts=opts, ans=opts.index(rad), ch=ch)

def mk_strokes(w, pool, lang):
    ch = next((c for c in w["hz"] if data.is_hanzi(c)), None)
    n = data.stroke_count(ch) if ch and data.available() else 0
    if not n: return None
    cand = [x for x in (n - 2, n - 1, n + 1, n + 2, n + 3) if x > 0]; random.shuffle(cand)
    opts = sorted([n] + cand[:3])
    return _base("strokes", w, lang, tr(lang, "q_strokes", x=ch), opts=[str(o) for o in opts], ans=opts.index(n), ch=ch)

def mk_cloze(w, pool, lang):
    ss = [s for s in data.sentences(w["hz"]) if w["hz"] in s["zh"]]
    if not ss: return None
    s = random.choice(ss)
    blank = s["zh"].replace(w["hz"], "＿＿", 1)
    others = _sample_other(pool, w, 3, same_len=True)
    opts = [w["hz"]] + [o["hz"] for o in others]; random.shuffle(opts)
    trn = s["de"] if lang == "de" and s.get("de") else s["en"]
    return _base("cloze", w, lang, tr(lang, "q_cloze", x=blank, tr=trn), opts=opts, ans=opts.index(w["hz"]), full=s["zh"])

def mk_build(w, pool, lang):
    ss = data.sentences(w["hz"])
    for s in random.sample(ss, len(ss)):
        if not all(data.is_hanzi(c) or c in "，。！？、" for c in s["zh"]): continue
        toks = [t for t in data.segment(s["zh"]) if data.has_hanzi(t)]
        if 3 <= len(toks) <= 8 and "".join(toks) == _norm_zh(s["zh"]):
            order = list(range(len(toks))); random.shuffle(order)
            if order == list(range(len(toks))): order.reverse()
            trn = s["de"] if lang == "de" and s.get("de") else s["en"]
            return _base("build", w, lang, tr(lang, "q_build", tr=trn, x=""), toks=toks, order=order, picked=[], ans="".join(toks), full=s["zh"], trn=trn)
    return None

def mk_match(words, lang):
    ws = words[:4]
    if len(ws) < 3: return None
    right = [meaning(w, lang)[0] for w in ws]
    order = list(range(len(ws))); random.shuffle(order)
    return {"t": "match", "wid": None, "lang": lang, "text": tr(lang, "q_match"), "left": [w["hz"] for w in ws], "right": [right[i] for i in order], "map": order,
            "wids": [w["i"] for w in ws], "done": [], "sel": None, "errs": 0, "ts": 0}

def mk_snd_init(lang):
    import content.alphabet as A
    inits = [x[0] for x in A.INITIALS]; r = random.choice(inits)
    opts = [r] + random.sample([x for x in inits if x != r], 3); random.shuffle(opts)
    return {"t": "snd_init", "wid": None, "lang": lang, "text": tr(lang, "q_listen").replace(tr(lang, "q_listen"), {"fa": "🎧 گوش کن: کدام حرف آغازین را شنیدی؟", "en": "🎧 Listen: which initial did you hear?", "de": "🎧 Hör zu: Welchen Anlaut hast du gehört?"}[lang]),
            "opts": opts, "ans": opts.index(r), "prebuilt": "init_" + r, "explain": f"{r}"}

def mk_snd_final(lang):
    import content.alphabet as A
    fin = [x[0] for x in A.FINALS if x[0] not in ("ü", "er", "iong")]; fin = [f for f in fin if f != "ü"] or fin
    pool = [f for f in ("a", "o", "e", "i", "u", "ai", "ei", "ao", "ou", "an", "en", "ang", "eng", "ong")]
    r = random.choice(pool); fn = r if r != "ü" else "v"
    opts = [r] + random.sample([x for x in pool if x != r], 3); random.shuffle(opts)
    return {"t": "snd_final", "wid": None, "lang": lang, "text": {"fa": "🎧 گوش کن: کدام وان (韵母) را شنیدی؟", "en": "🎧 Listen: which final did you hear?", "de": "🎧 Hör zu: Welches Finale hast du gehört?"}[lang],
            "opts": opts, "ans": opts.index(r), "prebuilt": "final_" + fn, "explain": r}

def mk_snd_tone(lang):
    t = random.randint(1, 4)
    return {"t": "snd_tone", "wid": None, "lang": lang, "text": {"fa": "🎧 گوش کن: این «ma» با کدام لحن بود؟", "en": "🎧 Listen: which tone was this “ma”?", "de": "🎧 Hör zu: Welchen Ton hatte dieses „ma“?"}[lang],
            "opts": ["1 ˉ", "2 ˊ", "3 ˇ", "4 ˋ"], "ans": t - 1, "prebuilt": f"tone_ma{t}", "row": 4, "explain": f"ma{t}"}

def mk_custom(rec, lang):
    d = json.loads(rec["data"]); opts = [d["right"]] + d["wrong"][:3]; random.shuffle(opts)
    return {"t": "custom", "wid": None, "lang": lang, "text": tr(lang, "q_custom", x=d["q"]), "opts": opts, "ans": opts.index(d["right"]), "explain": d.get("expl", ""), "cid": rec["id"]}

CREATORS = {"zh2m": mk_zh2m, "m2zh": mk_m2zh, "recog": mk_recog, "tone": mk_tone, "pytype": mk_pytype, "fa2zh": mk_fa2zh, "zh2fa": mk_zh2fa,
            "listen": mk_listen, "listen_py": mk_listen_py, "radical": mk_radical, "strokes": mk_strokes, "cloze": mk_cloze, "build": mk_build}

def choose_words(uid, n, level, prefer_due=True, lang=None):
    """Words for practice (of the learner's target language): due cards first, then learned cards, then fresh pool words."""
    import srs, db, langs
    lang = lang or (logic.target(uid) if uid is not None else "zh"); lo, hi = langs.wid_range(lang)
    out = []; ids = set()
    if uid is None: prefer_due = False
    if prefer_due:
        for c in srs.due_cards(uid, n, lang=lang):
            w = logic.get_word(c["wid"])
            if w and w["i"] not in ids: out.append(w); ids.add(w["i"])
    if len(out) < n and uid is not None:
        for r in db.q("SELECT wid FROM cards WHERE user_id=? AND wid>=? AND wid<? ORDER BY RANDOM() LIMIT ?", (uid, lo, hi, n * 2)):
            w = logic.get_word(r["wid"])
            if w and w["i"] not in ids and len(out) < n: out.append(w); ids.add(w["i"])
    if len(out) < n:
        pl = logic.pool(level, lang); random.shuffle(pl)
        for w in pl:
            if w["i"] not in ids and len(out) < n: out.append(w); ids.add(w["i"])
    random.shuffle(out)
    return out

def types_for(u):
    if u.get("types"): return u["types"]
    ms = logic.methods_of(u); ts = []
    for m in ms: ts += METHOD_TYPES.get(m, [])
    return list(dict.fromkeys(ts)) or ALL_MIX

def make_exercise(uid, kind=None, word=None, avoid_types=(), profile=None):
    """Build one exercise for user `uid` (or for a group: uid=None + profile={"level","lang","types"})."""
    tl = (profile or {}).get("target") if profile else logic.target(uid)
    if tl and tl != "zh":
        import xlang; return xlang.make_exercise(uid, tl, kind, word, avoid_types, profile)
    if profile:
        u = {"methods": ""}; lang = profile["lang"]; level = profile["level"]
    else:
        u = logic.get_user(uid); lang = logic.expl_lang(uid); level = u["level"]
    pool = logic.pool(level) or logic.pool(1)
    if level == 0 and kind in (None, "snd") and not (profile and profile.get("types")):
        k = random.choice(["snd_init", "snd_final", "snd_tone", "tone", "zh2m", "snd_init", "snd_tone"]) if not profile else random.choice(["snd_init", "snd_tone", "zh2m"])
        if k == "snd_init": return mk_snd_init(lang)
        if k == "snd_final": return mk_snd_final(lang)
        if k == "snd_tone": return mk_snd_tone(lang)
        kind = k
    if profile: u = dict(u, types=profile.get("types"))
    for _ in range(12):
        t = kind or random.choice([x for x in types_for(u) if x not in avoid_types] or types_for(u))
        if t == "match":
            ws = choose_words(uid, 4, level); ex = mk_match(ws, lang)
            if ex: return ex
            continue
        if t in ("snd_init", "snd_final", "snd_tone"): return {"snd_init": mk_snd_init, "snd_final": mk_snd_final, "snd_tone": mk_snd_tone}[t](lang)
        w = word or choose_words(uid, 1, level)[0]
        if t in ("pytype", "listen_py", "tone") and not w["py"]: continue
        ex = CREATORS[t](w, pool, lang)
        if ex: return ex
        if word is not None: word = None
    w = choose_words(uid, 1, level)[0]
    return mk_zh2m(w, pool, lang)

# ---------------- checking ----------------
def _norm_zh(s): return re.sub(r"[\s，。！？、,.!?；;：:“”\"'‘’（）()]", "", s or "")

def _split_meanings(s):
    parts = re.split(r"[;؛,،/]| or | یا |\bto ", s.lower() if s.isascii() else norm_fa(s))
    return [re.sub(r"\([^)]*\)|\[[^\]]*\]", "", p).strip(" .?!") for p in parts if p and p.strip()]

def _cands_meaning(w):
    out = set()
    for g in (w.get("fa", ""), w.get("en", ""), "; ".join(w.get("cc", [])), "; ".join(w.get("de", []))):
        for p in _split_meanings(g):
            if p: out.add(norm_fa(p) if not p.isascii() else norm_latin(p))
    return {x for x in out if len(x) >= 2}

def _diff_lines(exp_py, given_py, lang):
    """Explain pinyin differences in `lang`. exp_py: marks string; given_py: user text."""
    E = P.parse(exp_py); G = P.parse(given_py); lines = []
    cmp = P.compare(E, G)
    if cmp["exact"]: return cmp, lines
    if cmp.get("count_mismatch"):
        lines.append(tr(lang, "fb_count", n=len(E))); return cmp, lines
    exp_fmt = P.fmt(E)
    if cmp["tone_missing"]:
        lines.append(tr(lang, "fb_tone_missing", exp=exp_fmt)); return cmp, lines
    for i, kind, e, g, extra in cmp["diffs"]:
        if kind == "tone":
            eb = E[i][0]; gt = g
            lines.append(tr(lang, "fb_tone", i=i + 1, exp=P.num2mark(eb, e), et=e, gt=gt, got=P.num2mark(eb, gt)))
        elif kind == "tone_missing":
            lines.append(tr(lang, "fb_tone_missing", exp=exp_fmt)); break
        elif kind in ("initial", "final"):
            tip = TIPS.get(extra, ("", "", ""))[LI[lang]] if extra else ""
            lines.append(tr(lang, "fb_initial" if kind == "initial" else "fb_final", i=i + 1, exp=e, got=g, tip=tip))
        else:
            lines.append(tr(lang, "fb_letters", i=i + 1, exp=e, got=g))
    return cmp, lines

def result(ok, lang, right=None, lines=None, almost=False, word=None, given=None):
    return {"ok": bool(ok), "almost": almost, "right": right, "lines": lines or [], "word": word, "given": given}

def check_choice(ex, idx):
    if ex.get("L") not in (None, "zh"):
        import xlang; return xlang.check_choice(ex, idx)
    lang = ex["lang"]; ok = idx == ex["ans"]; w = logic.get_word(ex["wid"]) if ex.get("wid") is not None else None
    right = ex["opts"][ex["ans"]]; lines = []
    if w and not ok: lines.append(word_line(w, lang))
    if ex["t"] == "tone" and not ok:
        lines.append({"fa": "نکته: لحن را از روی صدا یاد بگیر؛ 🔊 را بزن و گوش کن.", "en": "Tip: learn tones by ear; tap 🔊 and listen.", "de": "Tipp: Lerne Töne nach Gehör; tippe auf 🔊."}[lang])
    if ex["t"] in ("snd_init", "snd_final", "snd_tone", "custom") and ex.get("explain") and not ok:
        lines.append(f"🔊 {ex['explain']}")
    if ex["t"] == "course" and ex.get("explain") and not ok:
        lines.append(f"💡 {ex['explain']}")
    if ex["t"] == "cloze" and ex.get("full"):
        lines.append(f"📝 {ex['full']}")
    if ex["t"] == "radical" and not ok and w:
        ci = data.char_info(ex["ch"]); 
        if ci: lines.append(f"🧱 {ex['ch']}: {ci['radical']} — {ci.get('defn','')[:60]}")
    return result(ok, lang, right=right, lines=lines, word=w, given=ex["opts"][idx] if 0 <= idx < len(ex["opts"]) else "")

def check_text(ex, given, uid=None):
    if ex.get("L") not in (None, "zh"):
        import xlang; return xlang.check_text(ex, given, uid)
    lang = ex["lang"]; t = ex["t"]; w = logic.get_word(ex["wid"]) if ex.get("wid") is not None else None
    g = (given or "").strip(); lines = []
    if t in ("pytype", "listen_py"):
        if data.has_hanzi(g):
            return result(False, lang, right=w["py"], lines=[tr(lang, "fb_typed_hanzi"), word_line(w, lang)], word=w, given=g)
        cmp, ls = _diff_lines(w["py"], g, lang)
        if cmp["exact"]: return result(True, lang, right=w["py"], word=w, given=g)
        lines = ls + [word_line(w, lang)]
        return result(False, lang, right=w["py"], lines=lines, word=w, given=g, almost=False)
    if t == "fa2zh":
        if not data.has_hanzi(g):
            lines = [tr(lang, "fb_typed_pinyin")] if re.search(r"[a-züāáǎàēéěèīíǐìōóǒòūúǔù]", g.lower()) else []
            return result(False, lang, right=w["hz"], lines=lines + [word_line(w, lang)], word=w, given=g)
        if _norm_zh(g) == _norm_zh(w["hz"]): return result(True, lang, right=w["hz"], word=w, given=g)
        wrong = [c for c in _norm_zh(g) if c not in w["hz"]]
        if wrong: lines.append(tr(lang, "fb_wrong_char", chars=" ".join(dict.fromkeys(wrong))))
        # a synonym? look it up
        try:
            hit = data.lookup_hanzi(_norm_zh(g))[:1]
            if hit: lines.append(f"ℹ️ {_norm_zh(g)} {hit[0]['py']} = {_short('; '.join(hit[0]['defs'][:2]), 60)}")
        except Exception: pass
        lines.append(word_line(w, lang))
        return result(False, lang, right=w["hz"], lines=lines, word=w, given=g)
    if t == "zh2fa":
        gn = norm_fa(g) if not g.isascii() else norm_latin(g)
        cands = _cands_meaning(w)
        ok = gn in cands or any(gn == c.replace("to ", "") for c in cands)
        if not ok and len(gn) >= 3:
            ok = any(gn in c.split() or c in gn.split() for c in cands if len(c) >= 3)
        if ok: return result(True, lang, right=_short(full_meaning(w, lang)[0], 60), word=w, given=g)
        if uid is not None and llm.configured() and llm.allow(uid):
            llm.count(uid)
            out = llm.chat(llm.grade_system(lang), f"Word: {w['hz']} ({w['py']}); reference meanings: {w.get('en')} / {w.get('fa')}. Learner answered: {g}", max_tokens=200)
            if out:
                v = "CORRECT" if "VERDICT: CORRECT" in out.upper() else ("ALMOST" if "VERDICT: ALMOST" in out.upper() else "WRONG")
                body = re.sub(r"(?i)^verdict:.*\n?", "", out).strip()
                return result(v != "WRONG", lang, right=_short(full_meaning(w, lang)[0], 60), lines=[tr(lang, "fb_llm", t=body)], word=w, given=g, almost=(v == "ALMOST"))
        return result(False, lang, right=_short(full_meaning(w, lang)[0], 60), lines=[word_line(w, lang)], word=w, given=g)
    return result(False, lang, right=str(ex.get("ans")), word=w, given=g)

def check_build(ex):
    if ex.get("L") not in (None, "zh"):
        import xlang; return xlang.check_build(ex)
    lang = ex["lang"]; got = "".join(ex["toks"][i] for i in ex["picked"]); ok = got == ex["ans"]
    w = logic.get_word(ex["wid"]) if ex.get("wid") is not None else None
    lines = []
    if not ok:
        lines.append({"fa": f"🧩 جملهٔ درست: <b>{ex['full']}</b>\nیادآوری: در چینی «زمان + مکان» قبل از فعل می‌آید و فعل صرف نمی‌شود.",
                      "en": f"🧩 Correct sentence: <b>{ex['full']}</b>\nReminder: in Chinese, time + place come before the verb, and verbs never conjugate.",
                      "de": f"🧩 Richtiger Satz: <b>{ex['full']}</b>\nErinnerung: Im Chinesischen stehen Zeit + Ort vor dem Verb, und Verben werden nicht konjugiert."}[lang])
        if w: lines.append(word_line(w, lang))
    return result(ok, lang, right=ex["full"], lines=lines, word=w, given=got)

def explain_ans(ex):
    """Plain-text answer for group quizzes."""
    if "opts" in ex: return ex["opts"][ex["ans"]]
    return str(ex.get("ans"))
