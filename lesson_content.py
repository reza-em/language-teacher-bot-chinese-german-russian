"""Guided course: what each lesson teaches (pages) and how it is practised (exercise plan + builders). No Telegram I/O.
Pages are lists of (html, button_rows); button rows use the bot's existing callbacks (audio, strokes, ...)."""
import random, math, re
import config, data, logic
import exercises as X
import fmt
import pinyin_utils as P
import content.alphabet as A
import content.lessons as L
import curriculum as Cu
from curriculum import t3, LI
from core import btn, esc, num
from texts import tr

PREBUILT_FINALS = {"a", "o", "e", "i", "u", "ai", "ei", "ao", "ou", "an", "en", "ang", "eng", "ong", "ü"}

METHOD = {  # one-line "how to learn this" per lesson kind
    "init": ("🎧 اول گوش بده، 🗣 بلند تکرار کن، بعد هر حرف را به یک واژهٔ نمونه گره بزن.", "🎧 Listen first, 🗣 repeat aloud, then tie each letter to an example word.", "🎧 Erst hören, 🗣 laut nachsprechen, dann jeden Buchstaben an ein Beispielwort knüpfen."),
    "fin": ("🎧 گوش بده و 🗣 تکرار کن؛ وان‌ها را گروه‌گروه یاد بگیر، نه تک‌تک.", "🎧 Listen and 🗣 repeat; learn finals in groups, not one by one.", "🎧 Hören und 🗣 nachsprechen; Finale gruppenweise lernen."),
    "tones": ("✋ حرکت لحن را با دست در هوا بکش و هر واژه را همیشه همراه لحنش بیاموز.", "✋ Draw each tone in the air and always learn a word together with its tone.", "✋ Zeichne jeden Ton in die Luft und lerne ein Wort immer mit seinem Ton."),
    "marks": ("📏 چند قاعدهٔ کوتاه + مثال؛ با تمرین خودکار می‌شود.", "📏 A few short rules + examples; practice makes it automatic.", "📏 Ein paar kurze Regeln + Beispiele; Übung macht es automatisch."),
    "sandhi": ("🔁 قاعده را با چند مثال بشنو؛ نوشته می‌شود یک‌جور و خوانده می‌شود جور دیگر.", "🔁 Hear the rule with examples; it is written one way and spoken another.", "🔁 Regel mit Beispielen hören; geschrieben anders als gesprochen."),
    "spell": ("📏 قواعد املا را با مثال ببین؛ یک بار بفهمی، همیشه درست می‌نویسی.", "📏 See the spelling rules with examples; understand once, spell right forever.", "📏 Rechtschreibregeln mit Beispielen; einmal verstehen, immer richtig."),
    "pycheck": ("🎧 فقط گوش بده و تشخیص بده؛ این مرحلهٔ مرور است.", "🎧 Just listen and decide; this is a review step.", "🎧 Nur zuhören und entscheiden; Wiederholungsschritt."),
    "rad": ("🧠 هر ریشه را با یک تصویر ذهنی ببند، بعد در نویسه‌ها دنبالش بگرد.", "🧠 Attach each radical to a mental picture, then hunt for it inside characters.", "🧠 Verknüpfe jedes Radikal mit einem inneren Bild und suche es in Zeichen."),
    "strokes": ("✍️ ضربه‌ها را با انگشت روی میز بکش و نام‌شان را بلند بگو.", "✍️ Trace the strokes with your finger and say their names aloud.", "✍️ Zeichne die Striche mit dem Finger nach und sprich ihre Namen."),
    "order": ("✍️ هفت قاعده کافی است؛ با دیدن انیمیشن ترتیب (دکمهٔ ✍️) تمرین کن.", "✍️ Seven rules are enough; practise with the stroke-order pictures (✍️ buttons).", "✍️ Sieben Regeln genügen; übe mit den Strichfolge-Bildern (✍️)."),
    "words": ("🔁 تکرار فاصله‌دار + 🎧 صدا + 🧠 داستان نویسه: این واژه‌ها خودکار به جعبهٔ مرورت می‌روند.", "🔁 Spaced repetition + 🎧 audio + 🧠 character stories: these words go into your review box automatically.", "🔁 Verteilte Wiederholung + 🎧 Audio + 🧠 Zeichengeschichten: Die Wörter landen automatisch in deiner Wiederholungsbox."),
    "grammar": ("🧩 الگو را بخوان، مثال را بشنو، بعد جمله بساز.", "🧩 Read the pattern, hear the example, then build sentences.", "🧩 Muster lesen, Beispiel hören, dann Sätze bauen."),
    "sent": ("🧩 واژه‌هایی که یاد گرفتی را در جمله ببین و جمله بساز.", "🧩 See the words you learned inside sentences and build some.", "🧩 Sieh die gelernten Wörter in Sätzen und baue welche."),
    "check": ("🔁 مرور مخلوط همهٔ این بخش با سؤال‌های متنوع.", "🔁 Mixed review of this whole section with varied questions.", "🔁 Gemischte Wiederholung dieses Abschnitts."),
}

def _hdr(les, lang, pos, total):
    return tr(lang, "cr_lesson_head", i=num(lang, pos + 1), n=num(lang, total), mod=esc(Cu.module_name(les["mod"], lang)), title=esc(Cu.title(les, lang))) \
        + "\n" + tr(lang, "cr_method", m=esc(t3(METHOD[les["kind"]], lang)))

def _w(wid): return logic.get_word(wid)

def _short(s, n=60): return (s[:n - 1] + "…") if len(s) > n else s

# ================================================================== pages
def pages(les, lang, elang, pos=0, total=1):
    """-> list of (html, rows). Never empty."""
    if les.get("lang", "zh") != "zh":
        import lesson_content_x as LX; return LX.pages(les, lang, elang, pos, total)
    k = les["kind"]; a = les["arg"]; i = LI[elang]; hd = _hdr(les, lang, pos, total)
    out = []
    if k == "init":
        text, letters = fmt.initial_page(a["gi"], lang, elang)
        rows = _grid([btn("🔊 " + l, f"al:h:i:{l}") for l in letters], 4)
        out.append((hd + "\n\n" + text, rows))
        tips = _conf_tips(letters, elang)
        if tips: out.append((tr(lang, "cr_tips_head") + "\n\n" + tips, []))
    elif k == "fin":
        text, letters = fmt.final_page(a["gi"], lang, elang)
        rows = _grid([btn("🔊 " + l, f"al:h:f:{l}") for l in letters if l in PREBUILT_FINALS], 4)
        out.append((hd + "\n\n" + text, rows))
        tips = _conf_tips(letters, elang)
        if tips: out.append((tr(lang, "cr_tips_head") + "\n\n" + tips, []))
    elif k == "tones":
        rows = [[btn(f"🔊 {n}", f"al:t:{n}") for n in range(1, 6)]]
        out.append((hd + "\n\n" + fmt.tones_page(lang, elang), rows))
        out.append((tr(lang, "cr_tips_head") + "\n\n" + "\n\n".join("• " + esc(t[i]) for t in A.TONE_TIPS[:5]), []))
    elif k == "marks":
        rules = "\n".join(esc(r[i]) for r in A.TONE_MARK_RULES)
        ex = "hǎo · xiě · gǒu · liù · shuǐ · duō · yī · lǜ"
        out.append((hd + "\n\n" + tr(lang, "cr_marks_body", rules=rules, ex=ex), [[btn("🔊 好", "hz:好"), btn("🔊 写", "hz:写"), btn("🔊 六", "hz:六"), btn("🔊 水", "hz:水")]]))
    elif k == "sandhi":
        out.append((hd + "\n\n" + fmt.sandhi_page(lang, elang), [[btn("🔊 你好", "hz:你好"), btn("🔊 不是", "hz:不是"), btn("🔊 一个", "hz:一个"), btn("🔊 一天", "hz:一天")]]))
    elif k == "spell":
        out.append((hd + "\n\n" + fmt.rules_page(lang, elang), []))
    elif k == "pycheck":
        out.append((hd + "\n\n" + tr(lang, "cr_pycheck_body"), [[btn(tr(lang, "b_a_tones"), "al:tones"), btn(tr(lang, "b_a_rules"), "al:rules")]]))
    elif k == "rad":
        names = {"fa": 3, "en": 2, "de": 4}[elang]; lines = []; rows = []
        for ri in a["idx"]:
            r = A.RADICALS[ri]; exs = r[5].split()
            lines.append(f"<b>{esc(r[0])}</b> · {esc(r[1])} — {esc(r[names])}\n     {tr(lang, 'cr_examples')}: {esc(r[5])}")
        out.append((hd + "\n\n" + "\n".join(lines), []))
        d2 = []
        for ri in a["idx"]:
            r = A.RADICALS[ri]; ch = next((c for c in r[5].split() if data.is_hanzi(c)), None)
            if ch and data.available():
                ci = data.char_info(ch)
                if ci: d2.append(f"<b>{esc(ch)}</b> {esc(ci['py'])} — {esc((ci['defn'] or '')[:40])}  ⟵ {esc(r[0])}")
            if ch: rows.append(btn("✍️ " + ch, f"sc:{ch}"))
        out.append((tr(lang, "cr_rad_p2") + ("\n\n" + "\n".join(d2) if d2 else ""), _grid(rows, 3)))
    elif k == "strokes":
        out.append((hd + "\n\n" + fmt.strokes_page(lang, elang), [[btn("✍️ 学", "sc:学"), btn("✍️ 人", "sc:人"), btn("✍️ 我", "sc:我"), btn("✍️ 国", "sc:国")]]))
    elif k == "order":
        rules = "\n".join(f"{n + 1}. {esc(r[i])} — {esc(r[3])}" for n, r in enumerate(A.STROKE_RULES))
        out.append((hd + "\n\n" + tr(lang, "cr_order_body", rules=rules), [[btn("✍️ 十", "sc:十"), btn("✍️ 三", "sc:三"), btn("✍️ 明", "sc:明"), btn("✍️ 小", "sc:小")]]))
    elif k == "words":
        ws = [w for w in (_w(x) for x in a["wids"]) if w]; lines = []; rows = []
        for w in ws:
            mean, _ = logic.gloss(w, elang)
            line = f"<b>{esc(w['hz'])}</b> · {esc(w['py'])} — {esc(_short(mean, 70))}"
            ch = next((c for c in w["hz"] if data.is_hanzi(c)), None); ci = data.char_info(ch) if ch and data.available() and len(w["hz"]) == 1 else None
            hint = ((ci or {}).get("etym") or {}).get("hint") if ci else None
            if hint: line += "\n     🧠 " + esc(_short(hint, 80))
            lines.append(line)
        rows = _grid([btn("🔊 " + w["hz"], f"hr:{w['i']}") for w in ws], 3)
        if a.get("first") and data.available():
            rows += _grid([btn("✍️ " + w["hz"], f"sk:{w['i']}") for w in ws if len(w["hz"]) == 1][:6], 3)
        out.append((hd + "\n\n" + "\n".join(lines) + "\n\n" + tr(lang, "cr_srs_note"), rows))
        ex = list(dict.fromkeys(e for e in (fmt.example_block(w, lang, elang) for w in ws) if e))
        if ex: out.append((tr(lang, "cr_in_sentences") + "\n\n" + "\n\n".join(ex[:6]), []))
    elif k == "grammar":
        out.append((hd + "\n\n" + (fmt.grammar_page(a["gid"], lang, elang) or ""), [[btn(tr(lang, "b_hear"), "hz:" + next(g for g in L.GRAMMAR if g[0] == a["gid"])[3][:12])]]))
    elif k == "sent":
        ws = [w for w in (_w(x) for x in a["wids"]) if w and data.sentences(w["hz"])]
        random.Random(len(a["wids"])).shuffle(ws)
        ex = [fmt.example_block(w, lang, elang) for w in ws[:5]]
        out.append((hd + "\n\n" + ("\n\n".join(ex) if ex else tr(lang, "cr_sent_none")), []))
    else:   # check
        out.append((hd + "\n\n" + tr(lang, "cr_check_body"), []))
    return out

def _grid(buttons, per): return [buttons[i:i + per] for i in range(0, len(buttons), per)]

def _conf_tips(letters, elang):
    i = LI[elang]; lines = []
    for key, t in X.TIPS.items():
        parts = key.split("_")[1:]
        if parts and parts[0] in letters: lines.append("• " + esc(t[i]))
    return "\n".join(lines)

# ================================================================== plans (JSON-able exercise specs)
def _ws_with(wids, pred):
    return [w for w in (_w(x) for x in wids) if w and pred(w)]

def plan(les, uid=None):
    if les.get("lang", "zh") != "zh":
        import lesson_content_x as LX; return LX.plan(les, uid)
    k = les["kind"]; a = les["arg"]; R = random; sp = []
    if k == "init":
        letters = A.INITIAL_GROUPS[a["gi"]][0].split()
        for n in range(3): sp.append({"k": "snd", "t": "init", "set": letters, "r": letters[n % len(letters)]})
        for l in R.sample(letters, min(3, len(letters))): sp.append({"k": "init_word", "l": l})
        R.shuffle(sp)
    elif k == "fin":
        letters = A.FINAL_GROUPS[a["gi"]][0].split()
        aud = [l for l in letters if l in PREBUILT_FINALS and l != "ü"]
        for n in range(2 if aud else 0): sp.append({"k": "snd", "t": "final", "set": aud, "r": aud[n % len(aud)]})
        for l in R.sample(letters, min(4 if aud else 6, len(letters))): sp.append({"k": "fin_word", "l": l})
        while len(sp) < 6: sp.append({"k": "fin_word", "l": R.choice(letters)})
        R.shuffle(sp)
    elif k == "tones":
        sp = [{"k": "snd_tone"} for _ in range(3)] + [{"k": "tone_contour", "n": n} for n in R.sample([1, 2, 3, 4], 3)]
    elif k == "marks":
        sp = [{"k": "mark", "q": q} for q in R.sample(range(len(MARK_Q)), 6)]
    elif k == "sandhi":
        sp = [{"k": "table", "name": "sandhi", "q": q} for q in R.sample(range(len(SANDHI_Q)), 6)]
    elif k == "spell":
        sp = [{"k": "table", "name": "spell", "q": q} for q in range(len(SPELL_Q))]
    elif k == "pycheck":
        sp = [{"k": "snd", "t": "init", "set": [x[0] for x in A.INITIALS], "r": R.choice(A.INITIALS)[0]} for _ in range(3)] \
             + [{"k": "snd", "t": "final", "set": ["a", "o", "e", "i", "u", "ai", "ei", "ao", "ou", "an", "en", "ang", "eng", "ong"], "r": R.choice(["a", "o", "e", "ai", "ao", "an", "ang", "ong"])} for _ in range(2)] \
             + [{"k": "snd_tone"} for _ in range(3)]
        R.shuffle(sp)
    elif k == "rad":
        idx = a["idx"]
        for ri in idx[:4] if len(idx) >= 4 else idx: sp.append({"k": "rad_mean", "r": ri})
        for ri in R.sample(idx, min(4, len(idx))): sp.append({"k": "rad_in", "r": ri})
        while len(sp) < 6: sp.append({"k": "rad_mean", "r": R.choice(idx)})
        R.shuffle(sp)
    elif k == "strokes":
        sp = [{"k": "stroke_name", "s": s} for s in R.sample(range(len(A.STROKES)), 6)]
    elif k == "order":
        sp = [{"k": "table", "name": "order", "q": q} for q in range(len(ORDER_Q))]
    elif k == "words":
        ids = list(a["wids"]); R.shuffle(ids)
        seq = ["zh2m", "listen", "m2zh", "recog", "zh2m", "listen"]
        for n, wid in enumerate(a["wids"]): sp.append({"k": "w", "t": seq[n % len(seq)], "w": wid})
        sp.append({"k": "w", "t": "tone", "w": R.choice(a["wids"])}); sp.append({"k": "w", "t": "m2zh", "w": R.choice(a["wids"])})
        if not a.get("first") and len(a["wids"]) >= 5: sp[-1] = {"k": "w", "t": "pytype", "w": R.choice(a["wids"])}
        R.shuffle(sp)
    elif k == "grammar":
        sp = [{"k": "gr_build", "g": a["gid"]}, {"k": "gr_trans", "g": a["gid"]}, {"k": "gr_pattern", "g": a["gid"]}]
        ws = _ws_with(a["wids"], lambda w: data.sentences(w["hz"]))
        for n, w in enumerate(R.sample(ws, min(3, len(ws)))): sp.append({"k": "w", "t": "build" if n % 2 == 0 else "cloze", "w": w["i"]})
        while len(sp) < 6: sp.append({"k": "gr_trans", "g": a["gid"]} if len(sp) % 2 else {"k": "gr_pattern", "g": a["gid"]})
    elif k == "sent":
        ws = _ws_with(a["wids"], lambda w: data.sentences(w["hz"])); R.shuffle(ws)
        for n, w in enumerate(ws[:8]): sp.append({"k": "w", "t": "build" if n % 2 == 0 else "cloze", "w": w["i"]})
        rest = [x for x in a["wids"] if x not in {s["w"] for s in sp}]; R.shuffle(rest)
        while len(sp) < 8 and rest: sp.append({"k": "w", "t": "zh2m", "w": rest.pop()})
    else:   # check
        ids = list(a["wids"]); R.shuffle(ids); seq = ["zh2m", "m2zh", "recog", "listen", "tone", "zh2m", "m2zh", "listen", "cloze", "recog"]
        for n, wid in enumerate(ids[:10]): sp.append({"k": "w", "t": seq[n % len(seq)], "w": wid})
    return sp

def pass_need(total): return max(1, math.ceil(Cu.PASS_RATIO * total - 1e-9))

# ---------------- hand-made question tables: (question (fa,en,de), right, [wrong...], explanation)
MARK_Q = [("hao", 3, "a"), ("xie", 3, "e"), ("gou", 3, "o"), ("liu", 2, "u"), ("shui", 3, "i"), ("duo", 1, "o"), ("mang", 2, "a"), ("tou", 2, "o"), ("gui", 4, "i"), ("lü", 4, "ü"), ("mei", 3, "e")]
SANDHI_Q = [("你好", "nǐ hǎo", "ní hǎo", ["nǐ hǎo", "nī hǎo", "nì hǎo"]), ("不是", "bù shì", "bú shì", ["bù shì", "bǔ shì", "bū shì"]), ("不好", "bù hǎo", "bù hǎo", ["bú hǎo", "bǔ hǎo", "bū hǎo"]),
            ("一个", "yī gè", "yí gè", ["yī gè", "yì gè", "yǐ gè"]), ("一天", "yī tiān", "yì tiān", ["yī tiān", "yí tiān", "yǐ tiān"]), ("很好", "hěn hǎo", "hén hǎo", ["hěn hǎo", "hēn hǎo", "hèn hǎo"]),
            ("不对", "bù duì", "bú duì", ["bù duì", "bǔ duì", "bū duì"]), ("一起", "yī qǐ", "yì qǐ", ["yī qǐ", "yí qǐ", "yǐ qǐ"])]
SPELL_Q = [
    (("«ü» بعد از j چگونه نوشته می‌شود؟ (ü + j)", "How is “ü” written after j?", "Wie schreibt man „ü“ nach j?"), "ju", ["jü", "jv", "jiu"]),
    (("هجای «uo» بدون حرف آغازین چگونه نوشته می‌شود؟", "How is the syllable “uo” with no initial spelled?", "Wie schreibt man die Silbe „uo“ ohne Anlaut?"), "wo", ["uo", "vo", "wuo"]),
    (("هجای «i» بدون حرف آغازین چگونه نوشته می‌شود؟", "How is the syllable “i” with no initial spelled?", "Wie schreibt man die Silbe „i“ ohne Anlaut?"), "yi", ["i", "ji", "wi"]),
    (("هجای «ia» بدون حرف آغازین چگونه نوشته می‌شود؟", "How is “ia” with no initial spelled?", "Wie schreibt man „ia“ ohne Anlaut?"), "ya", ["ia", "yia", "ja"]),
    (("«l» + «iou» چگونه کوتاه نوشته می‌شود؟", "How is l + iou written (shortened)?", "Wie wird l + iou (verkürzt) geschrieben?"), "liu", ["liou", "lou", "lio"]),
    (("بعد از n، «ü» چگونه می‌ماند؟ (n + ü)", "After n, how is ü written? (n + ü)", "Wie wird ü nach n geschrieben? (n + ü)"), "nü", ["nu", "nyu", "niu"]),
]
ORDER_Q = [
    (("در نوشتن «十» کدام ضربه اول می‌آید؟", "Writing “十”: which stroke comes first?", "Beim Schreiben von „十“: welcher Strich zuerst?"), ("افقی 一", "the horizontal 一", "der waagerechte 一"), [("عمودی 丨", "the vertical 丨", "der senkrechte 丨"), ("هر دو هم‌زمان", "both at once", "beide gleichzeitig")], "横 قبل از 竖 · horizontal before vertical"),
    (("در «三» کدام خط اول نوشته می‌شود؟", "In “三”, which line is written first?", "Bei „三“: welche Linie zuerst?"), ("بالایی", "the top one", "die obere"), [("پایینی", "the bottom one", "die untere"), ("میانی", "the middle one", "die mittlere")], "از بالا به پایین · top to bottom"),
    (("در «人» کدام ضربه اول است؟", "In “人”, which stroke comes first?", "Bei „人“: welcher Strich zuerst?"), ("撇 (چپ‌پایین)", "撇 (left-falling)", "撇 (links abfallend)"), [("捺 (راست‌پایین)", "捺 (right-falling)", "捺 (rechts abfallend)"), ("هم‌زمان", "both at once", "gleichzeitig")], "撇 قبل از 捺"),
    (("در «明» کدام بخش اول نوشته می‌شود؟", "In “明”, which part is written first?", "Bei „明“: welcher Teil zuerst?"), ("日 (چپ)", "日 (left)", "日 (links)"), [("月 (راست)", "月 (right)", "月 (rechts)"), ("هر دو هم‌زمان", "both at once", "beide gleichzeitig")], "از چپ به راست · left to right"),
    (("در «国» کدام بخش آخر نوشته می‌شود؟", "In “国”, which part is written last?", "Bei „国“: welcher Teil zuletzt?"), ("بستن قاب (خط پایین)", "closing the box (bottom line)", "das Schließen des Rahmens (untere Linie)"), [("قاب بیرونی (چپ)", "the outer left side", "die äußere linke Seite"), ("نقطهٔ داخلی", "the inner dot", "der innere Punkt")], "بستن قاب در آخر · close the box last"),
    (("در «小» کدام ضربه اول می‌آید؟", "In “小”, which stroke comes first?", "Bei „小“: welcher Strich zuerst?"), ("وسط 丨", "the middle 丨", "der mittlere 丨"), [("چپ 丿", "the left 丿", "der linke 丿"), ("راست 丶", "the right 丶", "der rechte 丶")], "وسط قبل از دو طرف · middle before sides"),
]

# ================================================================== exercise builders
def _choice(lang, text, right, wrongs, explain="", t="course", **kw):
    opts = list(dict.fromkeys([right] + [x for x in wrongs if x != right]))[:4]
    random.shuffle(opts)
    ex = {"t": t, "wid": None, "lang": lang, "text": text, "opts": opts, "ans": opts.index(right), "explain": explain, "ts": 0}
    ex.update(kw); return ex

def _snd(lang, kind, letters, right):
    inits = [x[0] for x in A.INITIALS]
    if kind == "init":
        pool_ = [l for l in inits if l != right]; opts = list(dict.fromkeys([right] + random.sample([l for l in letters if l != right], min(2, len(letters) - 1)) + random.sample(pool_, 4)))[:4]
        random.shuffle(opts)
        return {"t": "snd_init", "wid": None, "lang": lang, "text": {"fa": "🎧 گوش کن: کدام حرف آغازین را شنیدی؟", "en": "🎧 Listen: which initial did you hear?", "de": "🎧 Hör zu: Welchen Anlaut hast du gehört?"}[lang],
                "opts": opts, "ans": opts.index(right), "prebuilt": "init_" + right, "explain": right, "ts": 0}
    allf = ["a", "o", "e", "i", "u", "ai", "ei", "ao", "ou", "an", "en", "ang", "eng", "ong"]
    pool_ = [f for f in allf if f != right]; opts = list(dict.fromkeys([right] + random.sample([l for l in letters if l != right], min(2, len(letters) - 1)) + random.sample(pool_, 4)))[:4]
    random.shuffle(opts)
    return {"t": "snd_final", "wid": None, "lang": lang, "text": {"fa": "🎧 گوش کن: کدام وان (韵母) را شنیدی؟", "en": "🎧 Listen: which final did you hear?", "de": "🎧 Hör zu: Welches Finale hast du gehört?"}[lang],
            "opts": opts, "ans": opts.index(right), "prebuilt": "final_" + ("v" if right == "ü" else right), "explain": right, "ts": 0}

def _from_sentence(lang, zh, trn, wid=None):
    toks = [t for t in data.segment(zh) if data.has_hanzi(t)]
    if not (3 <= len(toks) <= 8 and "".join(toks) == X._norm_zh(zh)): return None
    order = list(range(len(toks))); random.shuffle(order)
    if order == list(range(len(toks))): order.reverse()
    return {"t": "build", "wid": wid, "lang": lang, "text": tr(lang, "q_build", tr=trn, x=""), "toks": toks, "order": order, "picked": [], "ans": "".join(toks), "full": zh, "trn": trn, "ts": 0}

def build_exercise(spec, uid, lang):
    if spec.get("L", "zh") != "zh":
        import lesson_content_x as LX; return LX.build_exercise(spec, uid, lang)
    k = spec["k"]; R = random
    if k == "w":
        w = _w(spec["w"]); pool_ = logic.pool(w["lv"]) or logic.pool(1)
        t = spec["t"]
        if t in ("tone", "pytype", "listen_py") and not w["py"]: t = "zh2m"
        ex = X.CREATORS[t](w, pool_, lang)
        if ex is None and t in ("build", "cloze"): ex = X.CREATORS["cloze" if t == "build" else "build"](w, pool_, lang)
        return ex or X.mk_zh2m(w, pool_, lang)
    if k == "snd": return _snd(lang, spec["t"], spec["set"], spec["r"])
    if k == "snd_tone": return X.mk_snd_tone(lang)
    if k == "init_word":
        l = spec["l"]; row = next(x for x in A.INITIALS if x[0] == l)
        allp = [x[0] for x in A.INITIALS]; wrong = R.sample([x for x in allp if x != l], 3)
        q = {"fa": f"واژهٔ «{row[1]}» ({row[2]}) با کدام حرف آغازین شروع می‌شود؟", "en": f"Which initial does “{row[1]}” ({row[2]}) start with?", "de": f"Mit welchem Anlaut beginnt „{row[1]}“ ({row[2]})?"}[lang]
        return _choice(lang, "❓ " + q, l, wrong, explain=f"{row[1]} {row[2]} → {l}", row=4)
    if k == "fin_word":
        l = spec["l"]; row = next(x for x in A.FINALS if x[0] == l)
        grp = next(g[0].split() for g in A.FINAL_GROUPS if l in g[0].split()); allf = [x[0] for x in A.FINALS]
        wrong = R.sample([x for x in grp if x != l], min(2, len(grp) - 1)) + R.sample([x for x in allf if x != l and x not in grp], 3)
        q = {"fa": f"واژهٔ «{row[1]}» ({row[2]}) چه وانی (韵母) دارد؟", "en": f"Which final does “{row[1]}” ({row[2]}) have?", "de": f"Welches Finale hat „{row[1]}“ ({row[2]})?"}[lang]
        return _choice(lang, "❓ " + q, l, wrong[:3], explain=f"{row[1]} {row[2]} → {l}", row=4)
    if k == "tone_contour":
        n = spec["n"]; row = A.TONES[n - 1]; names = ["1 ˉ", "2 ˊ", "3 ˇ", "4 ˋ"]
        q = {"fa": f"کدام لحن «{row[3][0]}» است؟", "en": f"Which tone is “{row[3][1]}”?", "de": f"Welcher Ton ist „{row[3][2]}“?"}[lang]
        ex = _choice(lang, "❓ " + q, names[n - 1], [x for x in names if x != names[n - 1]], explain=f"{row[4]} {row[5]}")
        ex["opts"] = names; ex["ans"] = n - 1; ex["row"] = 4; return ex
    if k == "mark":
        syl, tone, right = MARK_Q[spec["q"]]; vowels = [c for c in dict.fromkeys(syl) if c in "aeiouü"]
        wrong = [c for c in vowels if c != right] + [c for c in "aeoiu" if c not in vowels and c != right][:2]
        shown = P.num2mark(syl.replace("ü", "v"), tone) if True else syl
        q = {"fa": f"در هجای <b>{syl}</b> با لحن {num('fa', tone)} علامت لحن روی کدام حرف می‌رود؟", "en": f"In the syllable <b>{syl}</b> with tone {tone}, which letter gets the tone mark?", "de": f"In der Silbe <b>{syl}</b> mit Ton {tone}: auf welchen Buchstaben kommt das Zeichen?"}[lang]
        return _choice(lang, "❓ " + q, right, wrong[:3], explain=f"{syl} + {tone} = {shown}", row=4)
    if k == "table":
        name, qi = spec["name"], spec["q"]
        if name == "sandhi":
            hz, written, spoken, wrong = SANDHI_Q[qi]
            q = {"fa": f"«{hz}» ({written}) در گفتار واقعی چطور خوانده می‌شود؟", "en": f"How is “{hz}” ({written}) actually pronounced?", "de": f"Wie wird „{hz}“ ({written}) tatsächlich gesprochen?"}[lang]
            return _choice(lang, "❓ " + q, spoken, wrong, explain=f"{hz}: {written} → {spoken}", audio=hz, row=2)
        if name == "spell":
            qq, right, wrong = SPELL_Q[qi]
            return _choice(lang, "❓ " + t3(qq, lang), right, wrong, explain=right, row=4)
        qq, right, wrong, why = ORDER_Q[qi]
        return _choice(lang, "❓ " + t3(qq, lang), t3(right, lang), [t3(x, lang) for x in wrong], explain=why, row=1)
    if k == "rad_mean":
        r = A.RADICALS[spec["r"]]; names = {"fa": 3, "en": 2, "de": 4}[lang]
        others = [x for x in A.RADICALS if x[names] != r[names]]
        wrong = [x[names] for x in R.sample(others, 3)]
        q = {"fa": f"ریشهٔ <b>{r[0]}</b> ({r[1]}) یعنی چه؟", "en": f"What does the radical <b>{r[0]}</b> ({r[1]}) mean?", "de": f"Was bedeutet das Radikal <b>{r[0]}</b> ({r[1]})?"}[lang]
        return _choice(lang, "❓ " + q, r[names], wrong, explain=f"{r[0]} = {r[names]} · {r[5]}", row=2)
    if k == "rad_in":
        r = A.RADICALS[spec["r"]]; ch = next((c for c in r[5].split() if data.is_hanzi(c)), r[5].split()[0])
        banned = {x[0] for x in A.RADICALS if ch in x[5].split()}
        wrong = [x[0] for x in R.sample([x for x in A.RADICALS if x[0] not in banned], 3)]
        q = {"fa": f"کدام ریشه در نویسهٔ «{ch}» دیده می‌شود؟", "en": f"Which radical is in the character “{ch}”?", "de": f"Welches Radikal steckt im Zeichen „{ch}“?"}[lang]
        return _choice(lang, "❓ " + q, r[0], wrong, explain=f"{ch} ← {r[0]} ({r[1]})", row=2)
    if k == "stroke_name":
        s = A.STROKES[spec["s"]]; wrong = [x[0] for x in R.sample([x for x in A.STROKES if x[0] != s[0]], 3)]
        q = {"fa": f"نام این ضربه چیست؟ <b>{s[2]}</b>", "en": f"What is this stroke called? <b>{s[2]}</b>", "de": f"Wie heißt dieser Strich? <b>{s[2]}</b>"}[lang]
        return _choice(lang, "❓ " + q, s[0], wrong, explain=f"{s[2]} = {s[0]} {s[1]} — {s[3][LI[lang]]}", row=4)
    if k in ("gr_build", "gr_trans", "gr_pattern"):
        g = next(x for x in L.GRAMMAR if x[0] == spec["g"]); others = [x for x in L.GRAMMAR if x[0] != g[0]]; i = LI[lang]
        if k == "gr_build":
            ex = _from_sentence(lang, g[3], g[7][i])
            if ex: return ex
            k = "gr_trans"
        if k == "gr_trans":
            wrong = [x[7][i] for x in R.sample(others, 3)]
            return _choice(lang, "❓ " + {"fa": f"این جمله چه معنی دارد؟\n<b>{g[3]}</b> ({g[4]})", "en": f"What does this sentence mean?\n<b>{g[3]}</b> ({g[4]})", "de": f"Was bedeutet dieser Satz?\n<b>{g[3]}</b> ({g[4]})"}[lang], g[7][i], wrong, explain=f"{g[3]} = {g[7][i]}", row=1)
        key = {c for c in g[2] if data.is_hanzi(c)}
        safe = [x for x in others if not (key & set(x[3]))] or others          # no distractor may also follow the pattern
        wrong = [x[3] for x in R.sample(safe, 3)]
        return _choice(lang, "❓ " + {"fa": f"کدام جمله از الگوی «{g[2]}» ساخته شده؟", "en": f"Which sentence follows the pattern “{g[2]}”?", "de": f"Welcher Satz folgt dem Muster „{g[2]}“?"}[lang], g[3], wrong, explain=f"{g[2]} → {g[3]}", row=2)
    raise ValueError(k)

# ================================================================== placement
def placement_plan(L="zh"):
    if L != "zh":
        import lesson_content_x as LX; return LX.placement_plan(L)
    """12 questions, 3 per tier: 0 sounds/tones, 1-3 HSK words. Order: easy -> hard."""
    R = random; sp = [{"k": "snd", "t": "init", "set": [x[0] for x in A.INITIALS], "r": R.choice(["b", "p", "zh", "ch", "x", "q", "d", "t", "sh", "s"]), "tier": 0},
                      {"k": "snd", "t": "final", "set": ["a", "o", "e", "ai", "ao", "an", "ang", "ong"], "r": R.choice(["ai", "ao", "an", "ang", "ong", "e"]), "tier": 0},
                      {"k": "snd_tone", "tier": 0}]
    for lv in (1, 2, 3):
        ws = _sorted_by_level(lv)
        for n, w in enumerate(R.sample(ws, 3)): sp.append({"k": "w", "t": ["zh2m", "m2zh", "recog"][n], "w": w["i"], "tier": lv})
    return sp

def _sorted_by_level(lv): return [w for w in data.words() if w["lv"] == lv and len(w["hz"]) >= 1 and w["py"]]

def recommend(tiers, L="zh"):
    if L != "zh":
        import lesson_content_x as LX; return LX.recommend(L, tiers)
    """tiers: {0: ok, 1: ok, 2: ok, 3: ok} (each out of 3) -> (lesson id, level, reason key)."""
    t0, t1, t2, t3_ = (tiers.get(i, 0) for i in (0, 1, 2, 3))
    if t0 < 2: return "py.i0", 0, "cr_rec_zero"
    if t1 < 2: return Cu.start_of("radicals"), 1, "cr_rec_rad"
    if t2 < 2: return Cu.start_of("hsk1"), 1, "cr_rec_h1"
    if t3_ < 2: return Cu.start_of("hsk2"), 2, "cr_rec_h2"
    return Cu.start_of("hsk3"), 3, "cr_rec_h3"

def srs_items(les):
    """Words to put into the user's Leitner/SM-2 box when the lesson is taught."""
    if les.get("lang", "zh") != "zh":
        import lesson_content_x as LX; return LX.srs_items(les)
    k = les["kind"]; a = les["arg"]; out = []
    if k == "words": out = list(a["wids"])
    elif k == "init":
        for l in A.INITIAL_GROUPS[a["gi"]][0].split():
            row = next(x for x in A.INITIALS if x[0] == l); w = data.by_hz(row[1])
            if w: out.append(w["i"])
    elif k == "fin":
        for l in A.FINAL_GROUPS[a["gi"]][0].split():
            row = next(x for x in A.FINALS if x[0] == l); w = data.by_hz(row[1])
            if w: out.append(w["i"])
    elif k == "rad":
        for ri in a["idx"]:
            for c in A.RADICALS[ri][5].split():
                w = data.by_hz(c)
                if w: out.append(w["i"])
    return list(dict.fromkeys(out))
