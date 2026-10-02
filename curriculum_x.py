"""Guided courses for German and Russian (structure only). Same lesson dict shape as curriculum.py plus lesson["lang"]."""
import math
import langs

MODULES_X = {
    "de": [("sounds", "🔤", ("تلفظ و املا", "Pronunciation & spelling", "Aussprache & Schreibung")),
           ("a1", "1️⃣", ("A1: واژه، دستور، جمله", "A1: words, grammar, sentences", "A1: Wörter, Grammatik, Sätze")),
           ("a2", "2️⃣", ("A2: واژه، دستور، جمله", "A2: words, grammar, sentences", "A2: Wörter, Grammatik, Sätze"))],
    "ru": [("alpha", "🔤", ("الفبا و تلفظ", "Alphabet & pronunciation", "Alphabet & Aussprache")),
           ("a1", "1️⃣", ("A1: واژه، دستور، جمله", "A1: words, grammar, sentences", "A1: Wörter, Grammatik, Sätze")),
           ("a2", "2️⃣", ("A2: واژه، دستور، جمله", "A2: words, grammar, sentences", "A2: Wörter, Grammatik, Sätze"))],
}
GRAMMAR_PLAN = {   # language -> (A1 grammar ids, A2 grammar ids), in teaching order
    "de": (["gender", "present", "plural", "wordorder", "negation", "time", "modal"], ["cases", "prepositions", "separable", "perfekt"]),
    "ru": (["gender", "tobe", "plural", "present", "questions", "accusative", "prepositional", "past"], ["genitive", "motion", "aspect", "cases"]),
}

def _chunks(lst, size):
    if not lst: return []
    n = math.ceil(len(lst) / size); base, extra = divmod(len(lst), n); out = []; i = 0
    for k in range(n):
        m = base + (1 if k < extra else 0); out.append(lst[i:i + m]); i += m
    return out

def grammar_notes(L):
    if L == "de":
        import content.de_extra as E
    else:
        import content.ru_extra as E
    return E.GRAMMAR

def grammar_note(L, gid): return next(g for g in grammar_notes(L) if g[0] == gid)

def _weave_x(L, words_lessons, grammar_ids, sent_every, prefix, mod, seed_wids=()):
    n = len(words_lessons); g = len(grammar_ids); gpos = {}
    for k, gid in enumerate(grammar_ids):
        gpos.setdefault(max(1, round((k + 1) * n / (g + 1))), []).append(gid)
    out = []; recent = []; seen = list(seed_wids)
    for i, wl in enumerate(words_lessons, 1):
        out.append(wl); recent.append(wl); seen += wl["arg"]["wids"]
        for gid in gpos.get(i, []):
            note = grammar_note(L, gid)
            out.append({"id": f"{L}.g.{gid}", "lang": L, "mod": mod, "kind": "grammar", "title": (f"دستور: {note[1][0]}", f"Grammar: {note[1][1]}"), "arg": {"gid": gid, "wids": list(seen)}})
        if i % sent_every == 0 or i == n:
            ids = [x for r in recent[-sent_every:] for x in r["arg"]["wids"]]; k = (i - 1) // sent_every
            out.append({"id": f"{prefix}.s{k}", "lang": L, "mod": mod, "kind": "sent", "title": (f"جمله‌سازی ({k + 1})", f"Sentence practice ({k + 1})"), "arg": {"wids": ids}})
            recent = []
    return out

def build(L):
    out = []
    def add(lid, mod, kind, title, **arg): out.append({"id": f"{L}.{lid}", "lang": L, "mod": mod, "kind": kind, "title": title, "arg": arg})
    if L == "de":
        import content.de_extra as E
        n = len(E.SOUNDS)
        for k, ch in enumerate(_chunks(list(range(n)), 3)):
            add(f"snd{k}", "sounds", "rules", (f"تلفظ ({k + 1}): قاعده‌های {ch[0] + 1}–{ch[-1] + 1}", f"Pronunciation ({k + 1}): rules {ch[0] + 1}–{ch[-1] + 1}"), idx=ch)
        add("sndcheck", "sounds", "soundcheck", ("مرور تلفظ", "Pronunciation checkpoint"))
    else:
        import content.ru_extra as E
        for k, ch in enumerate(_chunks(list(range(len(E.ALPHABET))), 6)):
            first, last = E.ALPHABET[ch[0]][0][0], E.ALPHABET[ch[-1]][0][0]
            add(f"al{k}", "alpha", "alpha", (f"حروف {first}–{last}", f"Letters {first}–{last}"), idx=ch)
        for k, ch in enumerate(_chunks(list(range(len(E.RULES))), 3)):
            add(f"rl{k}", "alpha", "rules", (f"قاعده‌های خواندن ({k + 1})", f"Reading rules ({k + 1})"), idx=ch)
        add("alcheck", "alpha", "soundcheck", ("مرور الفبا", "Alphabet checkpoint"))
    g1, g2 = GRAMMAR_PLAN[L]
    for mod, lv, size, gl in (("a1", 1, 6, g1), ("a2", 2, 6, g2)):
        words = sorted(langs.level_words(L, lv), key=lambda w: w["freq"])
        wl = [{"id": f"{L}.{mod}.w{k}", "lang": L, "mod": mod, "kind": "words", "title": (f"واژه‌ها ({k + 1})", f"Words ({k + 1})"), "arg": {"wids": [w["i"] for w in ch]}}
              for k, ch in enumerate(_chunks(words, size))]
        seed = [w["i"] for w in langs.level_words(L, 1)] if mod == "a2" else []
        seq = _weave_x(L, wl, gl, 5, f"{L}.{mod}", mod, seed)
        allw = seed + [x for l_ in wl for x in l_["arg"]["wids"]]
        seq.append({"id": f"{L}.{mod}.check", "lang": L, "mod": mod, "kind": "check", "title": (f"مرور {mod.upper()}", f"{mod.upper()} checkpoint"), "arg": {"wids": allw}})
        out += seq
    return out
