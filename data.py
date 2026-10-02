"""Read-only access to the open datasets: HSK 1-3 list (+fa/en/de glosses), CC-CEDICT, HanDeDict, MakeMeAHanzi, Tatoeba examples."""
import os, re, json, zlib, sqlite3, threading, unicodedata
import config
import pinyin_utils as P

_lock = threading.Lock()
_words = _by_hz = _sent = _db = _cedict_set = None

def _load():
    global _words, _by_hz, _sent
    if _words is None:
        with _lock:
            if _words is None:
                _words = json.load(open(os.path.join(config.DATA_DIR, "hsk13.json"), encoding="utf8"))
                _by_hz = {w["hz"]: w for w in _words}
                p = os.path.join(config.DATA_DIR, "sentences.json")
                _sent = json.load(open(p, encoding="utf8")) if os.path.exists(p) else {}

def words(): _load(); return _words
def word(wid):
    _load(); return _words[wid] if 0 <= wid < len(_words) else None
def by_hz(hz): _load(); return _by_hz.get(hz)
def sentences(hz): _load(); return _sent.get(hz, [])
def level_words(level): return [w for w in words() if w["lv"] == level]
def pool(level):
    """Words a learner at `level` (0 = beginner) may be taught/quizzed on."""
    ws = words()
    if level <= 0: return [w for w in ws if w["lv"] == 1 and w["i"] < 60 and len(w["hz"]) <= 2][:40]
    return [w for w in ws if w["lv"] <= level]

def db():
    global _db
    if _db is None:
        p = os.path.join(config.DATA_DIR, "dict.sqlite")
        if not os.path.exists(p): raise FileNotFoundError("data/dict.sqlite missing: run  python3 build_data.py")
        _db = sqlite3.connect(p, check_same_thread=False)
        _db.row_factory = sqlite3.Row
    return _db

def available(): return os.path.exists(os.path.join(config.DATA_DIR, "dict.sqlite"))

def is_hanzi(c): return "\u4e00" <= c <= "\u9fff" or "\u3400" <= c <= "\u4dbf"
def has_hanzi(s): return any(is_hanzi(c) for c in s or "")

def cedict_pinyin_marks(py):
    """'xue2 xiao4' -> 'xué xiào' ; 'lu:e4' -> 'lüè' ; keeps non-syllable tokens."""
    out = []
    for tok in py.split():
        m = re.fullmatch(r"([A-Za-züÜ:]+?)([1-5])?", tok)
        if m and m.group(1).replace(":", "").replace("ü", "v").isalpha():
            base = m.group(1).replace("u:", "v").replace("U:", "V").replace("ü", "v")
            t = int(m.group(2) or 5)
            out.append(P.num2mark(base.lower(), t) if base.lower() != base else P.num2mark(base, t))
        else: out.append(tok)
    return " ".join(out)

def _rows(table, where, args, limit=40):
    return db().execute(f"SELECT trad,simp,py,defs FROM {table} WHERE {where} LIMIT {limit}", args).fetchall()

def _entry(r):
    return {"trad": r["trad"], "simp": r["simp"], "py_num": r["py"], "py": cedict_pinyin_marks(r["py"]), "defs": json.loads(r["defs"])}

def lookup_hanzi(text, limit=6):
    """Exact CC-CEDICT entries for a word (simplified or traditional)."""
    rows = _rows("cedict", "simp=? OR trad=?", (text, text), 30)
    ents = [_entry(r) for r in rows]
    # drop pure 'variant of' / surname-only noise when better entries exist
    good = [e for e in ents if not all(d.startswith(("surname", "variant of", "old variant", "see ", "abbr. for")) for d in e["defs"])]
    ents = good or ents
    ents.sort(key=lambda e: (e["py_num"][:1].isupper(), ))
    return ents[:limit]

def german_for(text, py_num=None):
    rows = _rows("hande", "simp=? OR trad=?", (text, text), 10)
    out = []
    for r in rows:
        if py_num and r["py"].lower().replace(" ", "") != py_num.lower().replace(" ", "") and len(rows) > 1: continue
        for d in json.loads(r["defs"]):
            out.append(re.split(r"; Bsp\.:", d)[0].strip())
    return out[:5]

def cedict_wordset():
    global _cedict_set
    if _cedict_set is None:
        _cedict_set = {r[0] for r in db().execute("SELECT simp FROM cedict")} | {w["hz"] for w in words()}
    return _cedict_set

def segment(text, maxlen=6):
    """Forward maximum matching with CC-CEDICT words (good enough for short sentences)."""
    S = cedict_wordset(); out = []; i = 0
    while i < len(text):
        if not is_hanzi(text[i]):
            j = i
            while j < len(text) and not is_hanzi(text[j]): j += 1
            out.append(text[i:j]); i = j; continue
        for L in range(min(maxlen, len(text) - i), 0, -1):
            if text[i:i + L] in S or L == 1:
                out.append(text[i:i + L]); i += L; break
    return out

def char_info(ch):
    r = db().execute("SELECT * FROM chars WHERE ch=?", (ch,)).fetchone()
    if not r: return None
    et = json.loads(r["etym"] or "{}")
    return {"ch": ch, "py": r["py"], "defn": r["defn"], "radical": r["radical"], "decomp": r["decomp"], "etym": et}

def components(ch):
    """Return [(component, definition)] from the IDS decomposition."""
    ci = char_info(ch)
    if not ci: return []
    comps = []
    for c in ci["decomp"]:
        if is_hanzi(c) and c != ch or c in "亻氵忄扌讠饣钅纟衤艹灬犭刂攵⺮⺗":
            if c not in [x[0] for x in comps]:
                di = char_info(c); comps.append((c, (di or {}).get("defn", "")))
    return comps

def stroke_data(ch):
    r = db().execute("SELECT data FROM strokes WHERE ch=?", (ch,)).fetchone()
    return json.loads(zlib.decompress(r[0])) if r else None

def stroke_count(ch):
    d = stroke_data(ch); return len(d["strokes"]) if d else 0

def _norm(s): return re.sub(r"\s+", " ", s.lower()).strip()

def search_pinyin(parsed, limit=8):
    """Search words by (toneless) pinyin; tone numbers in the query filter the result. Prefers HSK words."""
    base = "".join(b for b, _ in parsed)
    if not base: return []
    rows = db().execute("SELECT trad,simp,py,defs FROM cedict WHERE pyn=? LIMIT 400", (base,)).fetchall()
    tones = [t for _, t in parsed]
    hsk = {w["hz"]: w for w in words()}
    res = []
    for r in rows:
        e = _entry(r)
        if e["py_num"][:1].isupper(): continue
        if all(d.startswith(("surname", "variant of", "old variant", "see ")) for d in e["defs"]): continue
        if any(tones):
            ep = P.parse(e["py_num"])
            if len(ep) != len(parsed) or any(t and t != et for (_, t), (_, et) in zip(parsed, ep) if t and et): continue
        sc = (0 if e["simp"] in hsk else 1, len(e["simp"]), hsk.get(e["simp"], {}).get("freq", 10**6))
        res.append((sc, e))
    res.sort(key=lambda x: x[0])
    seen = set(); out = []
    for _, e in res:
        k = (e["simp"], e["py_num"])
        if k in seen: continue
        seen.add(k); out.append(e)
    return out[:limit]

def search_english(q, limit=8):
    qn = _norm(q)
    if len(qn) < 2: return []
    like = f"%{qn.replace('%','').replace('_','')}%"
    rows = db().execute("SELECT trad,simp,py,defs FROM cedict WHERE lower(defs) LIKE ? LIMIT 800", (like,)).fetchall()
    hsk = {w["hz"]: w for w in words()}; res = []
    rx = re.compile(r"(?<![a-z])" + re.escape(qn) + r"(?![a-z])")
    for r in rows:
        e = _entry(r)
        if e["py_num"][:1].isupper() or all(d.startswith(("surname", "variant of", "old variant", "see ", "abbr. for", "CL:")) for d in e["defs"]): continue
        best = 9
        for d in e["defs"]:
            dl = d.lower(); dl2 = re.sub(r"\([^)]*\)", "", dl).strip()
            if dl2 in (qn, "to " + qn): best = min(best, 0)
            elif rx.search(dl): best = min(best, 2 if dl.startswith(qn) or dl.startswith("to " + qn) else 3)
        if best == 9: continue
        res.append(((best, 0 if e["simp"] in hsk else 1, len(e["simp"])), e))
    res.sort(key=lambda x: x[0]); out = []; seen = set()
    for _, e in res:
        k = (e["simp"], e["py_num"])
        if k not in seen: seen.add(k); out.append(e)
    return out[:limit]

def search_german(q, limit=8):
    qn = _norm(q)
    if len(qn) < 2: return []
    rows = db().execute("SELECT trad,simp,py,defs FROM hande WHERE lower(defs) LIKE ? LIMIT 800", (f"%{qn}%",)).fetchall()
    hsk = {w["hz"]: w for w in words()}; res = []
    rx = re.compile(r"(?<![a-zäöüß])" + re.escape(qn) + r"(?![a-zäöüß])")
    for r in rows:
        ds = [re.split(r"; Bsp\.:", d)[0] for d in json.loads(r["defs"])]
        best = 9
        for d in ds:
            dl = re.sub(r"\([^)]*\)", "", d.lower()).strip()
            if dl == qn: best = 0
            elif rx.search(d.lower()): best = min(best, 2)
        if best == 9: continue
        res.append(((best, 0 if r["simp"] in hsk else 1, len(r["simp"])), {"simp": r["simp"], "trad": r["trad"], "py_num": r["py"], "py": cedict_pinyin_marks(r["py"]), "defs": ds}))
    res.sort(key=lambda x: x[0]); return [e for _, e in res[:limit]]

def search_persian(q, limit=8):
    """Persian search works on the curated HSK 1-3 glosses only (honest limitation)."""
    from textnorm import norm_fa
    qn = norm_fa(q)
    if not qn: return []
    out = []
    for w in words():
        fa = norm_fa(w["fa"])
        parts = re.split(r"[،؛,;()/]| یا ", fa)
        score = None
        if qn in [p.strip() for p in parts]: score = 0
        elif re.search(r"(?<!\S)" + re.escape(qn) + r"(?!\S)", fa): score = 1
        if score is not None: out.append((score, w["lv"], w))
    out.sort(key=lambda x: (x[0], x[1]))
    return [w for _, _, w in out[:limit]]

def example_for(hz, lang_hint="en"):
    s = sentences(hz)
    return s[0] if s else None

def hsk_info(hz):
    w = by_hz(hz); return w
