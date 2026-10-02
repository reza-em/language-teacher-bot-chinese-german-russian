"""Learning-language registry: Chinese (zh, HSK data in data/), German (de) and Russian (ru) vocabulary curated in content/.
Word ids: zh < 1_000_000 (custom owner words 100000+), de 1_000_000+, ru 2_000_000+ (append-only: cards store the id).
Every word is a dict with the same keys the exercise engine uses for Chinese: i, hz (headword), py (pronunciation/extra line), lv, en, fa, de, cc, pos, freq, lang."""
import re, unicodedata, zlib
import data

CODES = ("zh", "de", "ru")
BASE = {"zh": 0, "de": 1_000_000, "ru": 2_000_000}
INFO = {
    "zh": {"flag": "🇨🇳", "name": ("چینی", "Chinese", "Chinesisch"), "voice": "zh-CN-XiaoxiaoNeural", "levels": (0, 1, 2, 3), "level_names": ("🌱", "HSK 1", "HSK 2", "HSK 3")},
    "de": {"flag": "🇩🇪", "name": ("آلمانی", "German", "Deutsch"), "voice": "de-DE-KatjaNeural", "levels": (0, 1, 2), "level_names": ("🌱", "A1", "A2")},
    "ru": {"flag": "🇷🇺", "name": ("روسی", "Russian", "Russisch"), "voice": "ru-RU-SvetlanaNeural", "levels": (0, 1, 2), "level_names": ("🌱", "A1", "A2")},
}
UI_IDX = {"fa": 0, "en": 1, "de": 2}
ACUTE = "\u0301"

def lang_of_wid(wid):
    return "ru" if wid >= BASE["ru"] else ("de" if wid >= BASE["de"] else "zh")

def wid_range(lang):
    lo = BASE[lang]; hi = {"zh": BASE["de"], "de": BASE["ru"], "ru": BASE["ru"] + 1_000_000}[lang]; return lo, hi

def name(lang, ui="fa"): return INFO[lang]["name"][UI_IDX.get(ui, 0)]
def flag(lang): return INFO[lang]["flag"]
def label(lang, ui="fa"): return f"{flag(lang)} {name(lang, ui)}"
def levels(lang): return INFO[lang]["levels"]
def level_name(lang, lv): return INFO[lang]["level_names"][min(max(lv, 0), len(INFO[lang]["level_names"]) - 1)]
def voice(lang): return INFO[lang]["voice"]

# ---------------------------------------------------------------- transliteration (Russian)
_TR = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
       "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya"}
def translit(ru):
    out = []
    for ch in unicodedata.normalize("NFC", ru).lower().replace(ACUTE, "\u0301"):
        out.append(_TR.get(ch, ch))
    return "".join(out)

def ru_accent(s):
    """'кни'га' -> 'кни́га' (apostrophe after the stressed vowel becomes a combining acute)."""
    return re.sub(r"(?<=[аеёиоуыэюяАЕЁИОУЫЭЮЯ])'", ACUTE, s)

def ru_plain(s): return s.replace("'", "").replace(ACUTE, "")

def strip_marks(s):
    """Lower-cased comparison key: no stress marks/punctuation/extra spaces; ё=е; ß kept."""
    s = unicodedata.normalize("NFC", (s or "").replace(ACUTE, "").replace("'", "")).lower().replace("ё", "е").replace("’", "")
    return re.sub(r"[\s.,!?;:«»\"“”()\-–—]+", " ", s).strip()

# ---------------------------------------------------------------- loading
_cache = {}

def _plural(base, extra):
    extra = (extra or "").strip()
    if not extra or extra in ("(pl.)", "—"): return ""
    if extra == "-": return base
    if extra.startswith("-"): return base + extra[1:]
    return extra

def _load_de():
    import content.de_words as D
    out = []; seen = set()
    for line in D.RAW.splitlines():
        p = [x.strip() for x in line.split(";")]
        if len(p) != 6 or not p[1] or not p[3] or not p[4] or not p[5].isdigit(): continue
        pos, word, extra, en, fa, lv = p; key = (pos in ("der", "die", "das"), word)
        if key in seen or word in seen: continue
        seen.add(key); seen.add(word); n = len(out)
        w = {"i": BASE["de"] + n, "lang": "de", "base": word, "lv": int(lv), "en": en, "fa": fa, "de": [], "cc": [], "freq": n, "extra": extra, "trad": word, "rad": ""}
        if pos in ("der", "die", "das"):
            pl = _plural(word, extra); w.update(hz=f"{pos} {word}", art=pos, pos=["n"], plural=pl, py=(f"Pl. {('die ' + pl) if pl else '—'}"))
        elif pos == "v":
            w.update(hz=word, pos=["v"], py=extra)
        else:
            w.update(hz=word, pos=[pos], py="")
        out.append(w)
    return out

def _load_ru():
    import content.ru_words as R
    out = []; seen = set()
    for line in R.RAW.splitlines():
        p = [x.strip() for x in line.split(";")]
        if len(p) != 6 or not p[1] or not p[3] or not p[4] or not p[5].isdigit(): continue
        pos, word, extra, en, fa, lv = p; plain = ru_plain(word)
        if plain in seen: continue
        seen.add(plain); n = len(out); acc = ru_accent(word)
        w = {"i": BASE["ru"] + n, "lang": "ru", "base": plain, "lv": int(lv), "en": en, "fa": fa, "de": [], "cc": [], "freq": n, "trad": plain, "rad": "",
             "hz": plain, "ac": acc, "py": f"{acc} [{translit(acc)}]", "extra": extra}
        if pos.startswith("n-"):
            w.update(pos=["n"], gender=pos[2:]); 
            pl = ru_accent(extra) if extra and extra != "—" else ""
            w["plural"] = pl
        else:
            w["pos"] = [pos]
        out.append(w)
    return out

def _load_sent(lang):
    if lang == "de": import content.de_extra as E
    else: import content.ru_extra as E
    byb = {w["base"].lower(): w for w in words(lang)}
    out = []
    for line in E.SENT.splitlines():
        p = [x.strip() for x in line.split("|")]
        if len(p) != 3: continue
        raw, en, fa = p; m = re.search(r"\[([^\]]+)\]", raw)
        blank = ru_plain(m.group(1)) if m else None
        text = re.sub(r"[\[\]]", "", raw); plain = ru_plain(text) if lang == "ru" else text
        disp = ru_accent(text) if lang == "ru" else text
        w = byb.get(blank.lower()) if blank else None
        out.append({"t": plain, "ac": disp, "en": en, "fa": fa, "blank": blank, "wid": w["i"] if w else None})
    return out

def words(lang):
    if lang == "zh": return data.words()
    if lang not in _cache: _cache[lang] = _load_de() if lang == "de" else _load_ru()
    return _cache[lang]

def _index(lang):
    k = ("idx", lang)
    if k not in _cache: _cache[k] = {w["i"]: w for w in words(lang)}
    return _cache[k]

def word(wid):
    lang = lang_of_wid(wid)
    if lang == "zh": return data.word(wid)
    return _index(lang).get(wid)

def sentences(lang):
    k = ("sent", lang)
    if k not in _cache: _cache[k] = _load_sent(lang)
    return _cache[k]

def sentences_for(w):
    """Example sentences that contain this word as their cloze word (non-Chinese languages)."""
    lang = w.get("lang", "zh")
    if lang == "zh": return []
    return [s for s in sentences(lang) if s["wid"] == w["i"]]

def pool(lang, level):
    if lang == "zh": return data.pool(level)
    ws = words(lang)
    if level <= 0: return [w for w in ws if w["lv"] == 1][:40]
    return [w for w in ws if w["lv"] <= level]

def level_words(lang, lv): return [w for w in words(lang) if w["lv"] == lv]

def tokens(text):
    """Word tiles for sentence building (spaces; punctuation removed)."""
    return [t for t in re.sub(r"[.,!?;:«»\"“”]", " ", text).split() if t]
