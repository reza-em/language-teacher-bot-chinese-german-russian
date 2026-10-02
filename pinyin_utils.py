"""Pinyin helpers: tone marks <-> numbers, syllable segmentation, strict comparison with explainable differences."""
import re, json, os, unicodedata
import config

TONE_VOWELS = {"a": "āáǎà", "e": "ēéěè", "i": "īíǐì", "o": "ōóǒò", "u": "ūúǔù", "v": "ǖǘǚǜ"}
MARK2 = {}
for _b, _s in TONE_VOWELS.items():
    for _i, _c in enumerate(_s): MARK2[_c] = (_b, _i + 1)
INITIALS = ["zh", "ch", "sh", "b", "p", "m", "f", "d", "t", "n", "l", "g", "k", "h", "j", "q", "x", "r", "z", "c", "s", "y", "w"]

_SYL = None
def syllables():
    global _SYL
    if _SYL is None:
        p = os.path.join(config.DATA_DIR, "syllables.json")
        _SYL = set(json.load(open(p, encoding="utf8"))) if os.path.exists(p) else set()
    return _SYL

def num2mark(syl, tone):
    """('xue', 2) -> 'xué', ('lv', 4) -> 'lǜ', tone 5/0/None -> plain (ü for v)."""
    s = syl.lower().replace("u:", "v").replace("ü", "v")
    if not tone or tone == 5: return s.replace("v", "ü")
    i = s.find("a")
    if i < 0: i = s.find("e")
    if i < 0 and "ou" in s: i = s.find("o")
    if i < 0:
        idx = [k for k, c in enumerate(s) if c in "aeiouv"]; i = idx[-1] if idx else -1
    if i < 0: return s
    return (s[:i] + TONE_VOWELS[s[i]][tone - 1] + s[i + 1:]).replace("v", "ü")

def mark2num(py):
    """'nǐ hǎo' -> 'ni3 hao3'  (also accepts already-numbered text)"""
    return " ".join(f"{b}{t if t else ''}" for b, t in parse(py))

def _segment(base):
    """Split a toneless run of letters into valid syllables (DP, fewest pieces). Returns list of (start,end) or None."""
    S = syllables(); n = len(base)
    if not S: return [(0, n)]
    best = [None] * (n + 1); best[0] = []
    for i in range(n):
        if best[i] is None: continue
        for j in range(min(n, i + 6), i, -1):
            if base[i:j] in S:
                cand = best[i] + [(i, j)]
                if best[j] is None or len(cand) < len(best[j]): best[j] = cand
    return best[n]

def parse(text):
    """Parse user pinyin into [(base, tone|None)]. Accepts marks, digits (ni3hao3), spaces, apostrophes, u:/v/ü."""
    out = []
    t = unicodedata.normalize("NFC", (text or "").lower().replace("u:", "v").replace("ü", "v").replace("ǖ", "v1").replace("’", " ").replace("'", " "))
    for tok in re.split(r"[\s,.;·\-]+", t):
        if not tok: continue
        base = []; tone_at = {}
        for ch in tok:
            if ch in MARK2:
                b, tn = MARK2[ch]; tone_at[len(base)] = tn; base.append(b)
            elif ch in "1234":
                if base: tone_at[len(base) - 1] = int(ch)
            elif ch in "05":
                if base: tone_at[len(base) - 1] = 5
            elif ch.isalpha() and ch.isascii(): base.append(ch)
            elif ch == "v": base.append("v")
        if not base: continue
        word = "".join(base); seg = _segment(word)
        if seg is None:
            seg = [(0, len(word))]
        for a, b in seg:
            tones = [tone_at[k] for k in range(a, b) if k in tone_at]
            out.append((word[a:b], tones[-1] if tones else None))
    return out

def fmt(parsed):
    return " ".join(num2mark(b, t) if t else b.replace("v", "ü") for b, t in parsed)

def split_syl(base):
    for ini in INITIALS:
        if base.startswith(ini) and len(base) > len(ini): return ini, base[len(ini):]
    return "", base

CONFUSIONS = {frozenset(("zh", "z")): "conf_zh_z", frozenset(("ch", "c")): "conf_ch_c", frozenset(("sh", "s")): "conf_sh_s",
              frozenset(("j", "zh")): "conf_j_zh", frozenset(("q", "ch")): "conf_q_ch", frozenset(("x", "sh")): "conf_x_sh",
              frozenset(("n", "l")): "conf_n_l", frozenset(("b", "p")): "conf_b_p", frozenset(("d", "t")): "conf_d_t", frozenset(("g", "k")): "conf_g_k",
              frozenset(("an", "ang")): "conf_an_ang", frozenset(("en", "eng")): "conf_en_eng", frozenset(("in", "ing")): "conf_in_ing",
              frozenset(("u", "v")): "conf_u_v", frozenset(("ie", "ei")): "conf_ie_ei"}

def compare(expected, given):
    """expected/given: parsed lists. Returns dict(exact, same_letters, tone_missing, diffs=[(i, kind, exp, got, extra)])."""
    diffs = []
    e = [(b, t if t else 5) for b, t in expected]
    g = list(given)
    if len(e) != len(g):
        return {"exact": False, "same_letters": [b for b, _ in expected] == [b for b, _ in given], "tone_missing": False, "count_mismatch": True, "diffs": diffs}
    for i, ((eb, et), (gb, gt)) in enumerate(zip(e, g)):
        if eb != gb:
            ei, ef = split_syl(eb); gi, gf = split_syl(gb)
            if ei != gi:
                diffs.append((i, "initial", ei or "∅", gi or "∅", CONFUSIONS.get(frozenset((ei or "∅", gi or "∅")))))
            elif ef != gf:
                diffs.append((i, "final", ef, gf, CONFUSIONS.get(frozenset((ef, gf)))))
            else:
                diffs.append((i, "letters", eb, gb, None))
        elif gt is None:
            if et != 5: diffs.append((i, "tone_missing", et, None, None))
        elif gt != et:
            diffs.append((i, "tone", et, gt, None))
    exact = not diffs
    letters_ok = all(d[1] in ("tone", "tone_missing") for d in diffs)
    return {"exact": exact, "same_letters": letters_ok, "tone_missing": bool(diffs) and all(d[1] == "tone_missing" for d in diffs), "count_mismatch": False, "diffs": diffs}

def strip_marks(py):
    return "".join(b for b, _ in parse(py))

def build_syllables_from_cedict(db_path, out_path):
    import sqlite3
    c = sqlite3.connect(db_path); S = set()
    for (py,) in c.execute("SELECT py FROM cedict"):
        for tok in py.lower().replace("u:", "v").split():
            m = re.fullmatch(r"([a-z]+)[0-5]?", tok)
            if m and 1 <= len(m.group(1)) <= 6: S.add(m.group(1))
    # keep only plausible syllables (contain a vowel; exclude single junk letters except a/e/o)
    S = {s for s in S if re.search(r"[aeiouv]", s) and (len(s) > 1 or s in "aeo")}
    json.dump(sorted(S), open(out_path, "w"))
    return len(S)
