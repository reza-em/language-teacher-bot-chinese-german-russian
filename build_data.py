#!/usr/bin/env python3
"""Build the offline data used by the bot from open datasets (see README for licenses).
   python3 build_data.py            # uses data/raw/* if present, downloads what is missing
Outputs: data/hsk13.json, data/sentences.json (small, shipped) and data/dict.sqlite (big, rebuilt, not shipped)."""
import os, sys, re, json, bz2, zipfile, sqlite3, zlib, unicodedata, urllib.request
BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "data", "raw"); SRC = os.path.join(BASE, "data", "src"); OUT = os.path.join(BASE, "data")
URLS = {
 "cedict.zip": "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip",
 "hsk.json": "https://raw.githubusercontent.com/drkameleon/complete-hsk-vocabulary/main/complete.json",
 "mmh_graphics.txt": "https://raw.githubusercontent.com/skishore/makemeahanzi/master/graphics.txt",
 "mmh_dictionary.txt": "https://raw.githubusercontent.com/skishore/makemeahanzi/master/dictionary.txt",
 "handedict.u8": "https://raw.githubusercontent.com/gugray/HanDeDict/master/handedict.u8",
 "cmn_sentences.tsv.bz2": "https://downloads.tatoeba.org/exports/per_language/cmn/cmn_sentences.tsv.bz2",
 "cmn-eng_links.tsv.bz2": "https://downloads.tatoeba.org/exports/per_language/cmn/cmn-eng_links.tsv.bz2",
 "cmn-deu_links.tsv.bz2": "https://downloads.tatoeba.org/exports/per_language/cmn/cmn-deu_links.tsv.bz2",
 "eng_sentences.tsv.bz2": "https://downloads.tatoeba.org/exports/per_language/eng/eng_sentences.tsv.bz2",
 "deu_sentences.tsv.bz2": "https://downloads.tatoeba.org/exports/per_language/deu/deu_sentences.tsv.bz2",
}
def fetch(name):
    p = os.path.join(RAW, name)
    if not os.path.exists(p) or os.path.getsize(p) < 1000:
        os.makedirs(RAW, exist_ok=True); print("downloading", name)
        urllib.request.urlretrieve(URLS[name], p)
    return p

def plain(s):
    s = unicodedata.normalize("NFD", s.lower().replace("ü", "v").replace("u:", "v"))
    s = "".join(c for c in s if c.isalpha() and not unicodedata.combining(c))
    return s

TONES = {"a": "āáǎà", "e": "ēéěè", "i": "īíǐì", "o": "ōóǒò", "u": "ūúǔù", "v": "ǖǘǚǜ"}
def num2mark(syl):
    """'xue2' -> 'xué', 'lv4' -> 'lǜ', 'ma5' -> 'ma'"""
    m = re.fullmatch(r"([a-züÜ:]+?)([1-5])?", syl.replace("u:", "v").replace("ü", "v"))
    if not m: return syl
    s, t = m.group(1), int(m.group(2) or 5)
    if t == 5: return s.replace("v", "ü")
    low = s.lower()
    i = low.find("a")
    if i < 0: i = low.find("e")
    if i < 0 and "ou" in low: i = low.find("o")
    if i < 0:
        idx = [k for k, c in enumerate(low) if c in "aeiouv"]; i = idx[-1] if idx else -1
    if i < 0: return s
    out = s[:i] + TONES[low[i]][t - 1] + s[i + 1:]
    return out.replace("v", "ü")

def parse_cedict(lines):
    rx = re.compile(r"^(\S+) (\S+) \[([^\]]*)\] /(.*)/\s*$")
    for ln in lines:
        if ln.startswith("#") or not ln.strip(): continue
        m = rx.match(ln)
        if m: yield m.group(1), m.group(2), m.group(3), [x for x in m.group(4).split("/") if x]

def build_dict(db):
    c = sqlite3.connect(db); c.executescript("""
    DROP TABLE IF EXISTS cedict; DROP TABLE IF EXISTS hande; DROP TABLE IF EXISTS chars; DROP TABLE IF EXISTS strokes; DROP TABLE IF EXISTS info;
    CREATE TABLE cedict(trad TEXT, simp TEXT, py TEXT, pyn TEXT, defs TEXT);
    CREATE TABLE hande(trad TEXT, simp TEXT, py TEXT, pyn TEXT, defs TEXT);
    CREATE TABLE chars(ch TEXT PRIMARY KEY, py TEXT, defn TEXT, radical TEXT, decomp TEXT, etym TEXT);
    CREATE TABLE strokes(ch TEXT PRIMARY KEY, data BLOB);
    CREATE TABLE info(k TEXT PRIMARY KEY, v TEXT);""")
    with zipfile.ZipFile(fetch("cedict.zip")) as z:
        lines = z.read("cedict_ts.u8").decode("utf8").splitlines()
    rows = []
    for t, s, py, d in parse_cedict(lines):
        rows.append((t, s, py, plain(py), json.dumps(d, ensure_ascii=False)))
    c.executemany("INSERT INTO cedict VALUES(?,?,?,?,?)", rows); print("cedict", len(rows))
    rows = []
    with open(fetch("handedict.u8"), encoding="utf8") as f:
        for t, s, py, d in parse_cedict(f):
            rows.append((t, s, py, plain(py), json.dumps(d, ensure_ascii=False)))
    c.executemany("INSERT INTO hande VALUES(?,?,?,?,?)", rows); print("handedict", len(rows))
    for tb in ("cedict", "hande"):
        c.execute(f"CREATE INDEX ix_{tb}_s ON {tb}(simp)"); c.execute(f"CREATE INDEX ix_{tb}_t ON {tb}(trad)"); c.execute(f"CREATE INDEX ix_{tb}_p ON {tb}(pyn)")
    rows = []
    with open(fetch("mmh_dictionary.txt"), encoding="utf8") as f:
        for ln in f:
            d = json.loads(ln)
            rows.append((d["character"], ",".join(d.get("pinyin") or []), d.get("definition", ""), d.get("radical", ""), d.get("decomposition", ""), json.dumps(d.get("etymology") or {}, ensure_ascii=False)))
    c.executemany("INSERT OR REPLACE INTO chars VALUES(?,?,?,?,?,?)", rows); print("chars", len(rows))
    rows = []
    with open(fetch("mmh_graphics.txt"), encoding="utf8") as f:
        for ln in f:
            d = json.loads(ln)
            rows.append((d["character"], zlib.compress(json.dumps({"strokes": d["strokes"], "medians": d["medians"]}).encode(), 9)))
    c.executemany("INSERT OR REPLACE INTO strokes VALUES(?,?)", rows); print("strokes", len(rows))
    c.execute("INSERT INTO info VALUES('built','1')"); c.commit(); return c

def load_gloss():
    g = {}
    for fn in ("gloss1.txt", "gloss2.txt", "gloss3.txt"):
        for ln in open(os.path.join(SRC, fn), encoding="utf8"):
            ln = ln.rstrip("\n")
            if ln.count("|") >= 2:
                hz, en, fa = ln.split("|", 2); g[hz] = (en, fa)
    return g

OVERRIDE_PY = {"了": "le", "的": "de", "地": "de", "得": "de", "着": "zhe", "吗": "ma", "呢": "ne", "吧": "ba", "个": "gè", "都": "dōu", "上": "shàng", "看": "kàn", "听": "tīng", "读": "dú",
               "长": "cháng", "还": "hái", "要": "yào", "好": "hǎo", "为": "wèi", "行李箱": "xíng li xiāng", "会": "huì", "什么": "shén me", "给": "gěi", "差": "chà", "角": "jiǎo", "和": "hé",
               "几": "jǐ", "分": "fēn", "离": "lí", "万": "wàn", "米": "mǐ", "教": "jiāo", "刮": "guā", "觉得": "jué de", "着急": "zháo jí", "一会儿": "yī huìr", "骑": "qí", "舒服": "shū fu"}

def build_hsk(db):
    from pypinyin import pinyin, Style
    d = json.load(open(fetch("hsk.json"), encoding="utf8"))
    gloss = load_gloss(); words = []
    for e in d:
        lv = [int(l[4]) for l in e["level"] if l.startswith("old-") and int(l[4]) <= 3]
        if lv and e["simplified"] in gloss: words.append((min(lv), e["frequency"], e))
    words.sort(key=lambda x: (x[0], x[1]))
    out = []; hc = db.cursor()
    for i, (lv, fq, e) in enumerate(words):
        hz = e["simplified"]; en, fa = gloss[hz]
        key = "".join(x[0] for x in pinyin(hz, style=Style.TONE3, neutral_tone_with_five=False)).replace("5", "")
        py = None
        for f in e["forms"]:
            num = f["transcriptions"]["numeric"].lower().replace(" ", "").replace("5", "").replace("u:", "v").replace("ü", "v")
            if num == key.replace("ü", "v"): py = f["transcriptions"]["pinyin"].lower().replace("ü", "ü"); break
        if hz in OVERRIDE_PY: py = OVERRIDE_PY[hz]
        if not py: py = " ".join(x[0] for x in pinyin(hz, style=Style.TONE))
        pyn = plain(py)
        cc = [json.loads(r[0]) for r in hc.execute("SELECT defs FROM cedict WHERE simp=? AND pyn=?", (hz, pyn))]
        more = [x for ds in cc for x in ds if not x.startswith("surname") and not x.startswith("variant of") and not x.startswith("old variant")][:4]
        de = []
        for r in hc.execute("SELECT defs FROM hande WHERE simp=? AND pyn=?", (hz, pyn)):
            de += [re.split(r"; Bsp\.:", x)[0].strip() for x in json.loads(r[0]) if not x.lower().startswith("(nachname")][:4]
        out.append({"i": i, "hz": hz, "py": py, "lv": lv, "en": en, "fa": fa, "cc": more, "de": de[:4], "pos": e.get("pos", [])[:3], "rad": e.get("radical", ""),
                    "trad": e["forms"][0]["traditional"], "freq": fq})
    json.dump(out, open(os.path.join(OUT, "hsk13.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    print("hsk words", len(out), "with de:", sum(1 for w in out if w["de"])); return out

def rd(name):
    return bz2.open(fetch(name), "rt", encoding="utf8")

def build_sentences(words):
    wl = [w["hz"] for w in words]; known = set("".join(wl)); wset = set(wl)
    cmn = {}
    for ln in rd("cmn_sentences.tsv.bz2"):
        p = ln.rstrip("\n").split("\t")
        if len(p) >= 3 and 3 <= len(p[2]) <= 16: cmn[p[0]] = p[2]
    def links(fn):
        m = {}
        for ln in rd(fn):
            a, b = ln.split()[:2]
            if a in cmn: m.setdefault(a, []).append(b)
        return m
    le, ld = links("cmn-eng_links.tsv.bz2"), links("cmn-deu_links.tsv.bz2")
    need = {b for v in list(le.values()) + list(ld.values()) for b in v}; txt = {}
    for fn in ("eng_sentences.tsv.bz2", "deu_sentences.tsv.bz2"):
        for ln in rd(fn):
            p = ln.rstrip("\n").split("\t")
            if p[0] in need: txt[p[0]] = p[2]
    cand = {}
    for sid, s in cmn.items():
        if sid not in le: continue
        ch = [c for c in s if "\u4e00" <= c <= "\u9fff"]
        if not ch: continue
        cov = sum(c in known for c in ch) / len(ch)
        if cov < 0.9: continue
        en = next((txt[b] for b in le[sid] if b in txt), None)
        if not en: continue
        de = next((txt[b] for b in ld.get(sid, []) if b in txt), "")
        for w in wl:
            if w in s: cand.setdefault(w, []).append((-round(cov, 2), bool(de) * -1, abs(len(s) - 8), sid, s, en, de))
    res = {}
    for w, lst in cand.items():
        lst.sort(); seen = set(); pick = []
        for _, _, _, sid, s, en, de in lst:
            if s in seen: continue
            seen.add(s); pick.append({"id": sid, "zh": s, "en": en, "de": de})
            if len(pick) == 2: break
        res[w] = pick
    json.dump(res, open(os.path.join(OUT, "sentences.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    print("sentences for", len(res), "of", len(wl), "words")

def main():
    db = os.path.join(OUT, "dict.sqlite")
    if "--force" in sys.argv and os.path.exists(db): os.remove(db)
    c = build_dict(db) if not os.path.exists(db) else sqlite3.connect(db)
    words = build_hsk(c); c.close()
    if "--no-sentences" not in sys.argv: build_sentences(words)
if __name__ == "__main__": main()
