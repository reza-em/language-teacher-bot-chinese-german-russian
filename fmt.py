"""Text rendering of cards, dictionary entries and curriculum pages (pure functions -> HTML strings)."""
import random
import config, data, logic
from core import esc, rtl
from texts import tr
import content.alphabet as A
import content.lessons as L

LI = {"fa": 0, "en": 1, "de": 2}
SRC_KEY = {"curated": None, "cedict": None, "hande": "src_hande", "llm": "src_llm", "missing": "src_missing"}

def lvl_tag(lang, lv):
    return tr(lang, "lvl_tag", lv=lv) if lv else ""

def src_note(lang, src):
    k = SRC_KEY.get(src)
    return tr(lang, k) if k else ""

def example_block(w, lang, elang):
    ss = data.sentences(w["hz"])
    if not ss: return ""
    s = ss[0]
    from pypinyin import pinyin, Style
    py = " ".join(x[0] for x in pinyin(s["zh"], style=Style.TONE))
    trn = s["de"] if elang == "de" and s.get("de") else s["en"]
    return tr(lang, "example_line", zh=esc(s["zh"]), py=esc(py), tr=esc(trn))

def word_card(w, lang, elang, with_example=True):
    if w.get("lang", "zh") != "zh":
        import xlang; return xlang.word_card(w, lang, elang, with_example)
    mean, src = logic.gloss(w, elang)
    lines = [esc(mean)]
    if elang != "en" and w.get("en"): lines.append("🇬🇧 " + esc("; ".join(w["cc"][:2]) if w.get("cc") else w["en"]))
    return tr(lang, "card", hz=f"<b>{esc(w['hz'])}</b>", py=esc(w["py"]), lvl=lvl_tag(lang, w["lv"]),
              mean="\n".join(lines), src=src_note(lang, src),
              ex=example_block(w, lang, elang) if with_example else "")

def entry_text(e, lang, elang, show_all_en=True):
    """One dictionary entry (CC-CEDICT dict from data.*) -> html."""
    hw = data.by_hz(e["simp"])
    lv = hw["lv"] if hw and hw["py"].replace(" ", "").lower() == e["py"].replace(" ", "").lower() else 0
    meanings, src = logic.entry_gloss(e, elang)
    mean = "\n".join("• " + esc(m) for m in meanings[:4])
    if elang != "en" and src != "missing":
        en = [d for d in e["defs"] if not d.startswith("CL:")][:2]
        if en: mean += "\n🇬🇧 " + esc("; ".join(en))
    trad = f"({esc(e['trad'])})" if e["trad"] != e["simp"] else ""
    cl = next((d for d in e["defs"] if d.startswith("CL:")), None)
    if cl: mean += "\n📏 " + esc(cl)
    return tr(lang, "dict_entry", hz=esc(e["simp"]), trad=trad, py=esc(e["py"]), lvl=lvl_tag(lang, lv), mean=mean, src=src_note(lang, src))

def char_line(ch, elang):
    ci = data.char_info(ch)
    if not ci: return f"{esc(ch)}"
    n = data.stroke_count(ch)
    return f"<b>{esc(ch)}</b> {esc(ci['py'])} — {esc((ci['defn'] or '')[:60])} (部首 {esc(ci['radical'])}, {n}✍️)"

def parts_text(ch, lang, elang):
    ci = data.char_info(ch)
    if not ci: return tr(lang, "parts_none")
    comps = data.components(ch)
    lines = [f"• {esc(c)} — {esc(d[:50])}" for c, d in comps] or ["—"]
    ety = ci["etym"].get("hint") if ci.get("etym") else ""
    ety_t = tr(lang, "ety_line", hint=esc(ety)) if ety else ""
    rad = ci["radical"]; rd = data.char_info(rad); rad_s = f"{esc(rad)} ({esc((rd or {}).get('defn', '')[:30])})"
    return tr(lang, "parts", ch=esc(ch), rad=rad_s, parts="\n".join(lines), ety=ety_t)

def story_text(w, lang, elang):
    ch = next((c for c in w["hz"] if data.is_hanzi(c)), None)
    out = [tr(lang, "story_head", hz=esc(w["hz"]))]
    ci = data.char_info(ch) if ch and data.available() else None
    if ci:
        hint = (ci.get("etym") or {}).get("hint")
        if hint: out.append("📜 " + esc(hint))
        comps = data.components(ch)
        if comps: out.append("🧩 " + " + ".join(f"{esc(c)} ({esc(d[:25])})" for c, d in comps))
    out.append(tr(lang, "story_auto"))
    out.append(tr(lang, "story_sound", py=esc(w["py"])))
    return "\n\n".join(out)

# ---------- alphabet pages ----------
def initial_page(gi, lang, elang):
    grp, name = A.INITIAL_GROUPS[gi]
    letters = grp.split()
    lines = []
    for l, hz, py, en, hint in A.INITIALS:
        if l in letters: lines.append(tr(lang, "init_item", l=l, hz=hz, py=py, mean=esc(en), hint=esc(hint[LI[elang]])))
    return tr(lang, "init_head", grp=f"{grp} ({name[LI[elang]]})", lines="\n".join(lines)), letters

def final_page(gi, lang, elang):
    grp, name = A.FINAL_GROUPS[gi]; letters = grp.split(); lines = []
    for l, hz, py, en in A.FINALS:
        if l in letters: lines.append(tr(lang, "final_item", l=l, hz=hz, py=py, mean=esc(en)))
    return tr(lang, "final_head", grp=f"{grp} ({name[LI[elang]]})", lines="\n".join(lines)), letters

def tones_page(lang, elang):
    i = LI[elang]
    lines = []
    for n, mark, name, contour, hz, py, en in A.TONES:
        lines.append(f"<b>{n}. {name[i]}</b> {mark}  —  {contour[i]}\n     {hz} <b>{py}</b> ({esc(en)})")
    rules = "\n".join(r[i] for r in A.TONE_MARK_RULES)
    return tr(lang, "tones_head", lines="\n".join(lines), rules=esc(rules))

def rules_page(lang, elang):
    i = LI[elang]; return tr(lang, "rules_head", rules="\n\n".join(esc(r[i]) for r in A.SPELLING_RULES))

def sandhi_page(lang, elang):
    i = LI[elang]; return tr(lang, "sandhi_head", rules="\n\n".join(esc(r[i]) for r in A.SANDHI))

def strokes_page(lang, elang):
    i = LI[elang]
    lines = [f"{shape}  <b>{zh}</b> {py} — {name[i]}  ({ex})" for zh, py, shape, name, ex in A.STROKES]
    rules = "\n".join(f"• {r[i]} — {r[3]}" for r in A.STROKE_RULES)
    return tr(lang, "strokes_head", lines="\n".join(lines), rules=esc(rules))

def radicals_page(p, lang, elang, per=10):
    pages = (len(A.RADICALS) + per - 1) // per; p = max(0, min(p, pages - 1))
    names = {"fa": 3, "en": 2, "de": 4}[elang]
    lines = [f"<b>{r[0]}</b> {r[1]} — {esc(r[names])}  ·  {r[5]}" for r in A.RADICALS[p * per:(p + 1) * per]]
    return tr(lang, "radicals_head", p=p + 1, pages=pages, lines="\n".join(lines)), p, pages

def tip_page(i, lang, elang):
    n = len(A.TONE_TIPS); i %= n
    return tr(lang, "tips_head", i=i + 1, n=n, t=esc(A.TONE_TIPS[i][LI[elang]])), i, n

def grammar_page(gid, lang, elang):
    g = next((x for x in L.GRAMMAR if x[0] == gid), None)
    if not g: return None
    i = LI[elang]
    return tr(lang, "grammar_note", title=esc(g[5][i]), pattern=esc(g[2]), body=esc(g[6][i]), zh=esc(g[3]), py=esc(g[4]), tr=esc(g[7][i]))

def culture_page(i, lang, elang):
    i %= len(L.CULTURE); c = L.CULTURE[i]; k = LI[elang]
    return tr(lang, "culture_head", title=esc(c[0][k]), body=esc(c[1][k])), i

def idiom_page(i, lang, elang):
    i %= len(L.CHENGYU); c = L.CHENGYU[i]; k = LI[elang]
    return tr(lang, "idiom", zh=c[0], py=esc(c[1]), mean=esc(c[2][k]), lit=esc(c[3])), i

def reader_page(rid, lang, elang, show_py=True, show_tr=True):
    r = next((x for x in L.READERS if x[0] == rid), None)
    if not r: return None
    k = {"fa": 2, "en": 3, "de": 4}[elang]; ti = {"fa": 1, "en": 2, "de": 3}[elang]
    lines = []
    for ln in r[3]:
        s = f"<b>{esc(ln[0])}</b>"
        if show_py: s += f"\n<i>{esc(ln[1])}</i>"
        if show_tr: s += f"\n{esc(ln[k])}"
        lines.append(s)
    return tr(lang, "reader_head", title=f"{esc(r[2][0])} — {esc(r[2][ti])}", lv=r[1], lines="\n\n".join(lines))

def daily_tip(uid_or_day, lang, elang):
    """Rotating 'tip of the day' (grammar -> tone tip -> idiom -> culture), by day number."""
    d = int(uid_or_day) if not isinstance(uid_or_day, int) else uid_or_day
    kinds = ["grammar", "tone", "idiom", "culture"]; k = kinds[d % 4]; j = d // 4
    if k == "grammar": return grammar_page(L.GRAMMAR[j % len(L.GRAMMAR)][0], lang, elang)
    if k == "tone": return tip_page(j, lang, elang)[0]
    if k == "idiom": return idiom_page(j, lang, elang)[0]
    return culture_page(j, lang, elang)[0]

def level_label(lang, lv): return tr(lang, f"lvl_{lv}")
def fmt_when(lang, secs):
    if secs < 3600: return tr(lang, "when_min", n=max(1, round(secs / 60)))
    return tr(lang, "when_day", n=max(1, round(secs / 86400)))
