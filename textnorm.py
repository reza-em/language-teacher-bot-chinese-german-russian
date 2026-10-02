"""Text normalisation + language detection (fa / de / en / zh)."""
import re
_DIG = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_CH = str.maketrans({"ي": "ی", "ك": "ک", "ۀ": "ه", "ة": "ه", "أ": "ا", "إ": "ا", "\u200c": " ", "\u200f": "", "\u200e": "",
                     "\u064b": "", "\u064c": "", "\u064d": "", "\u064e": "", "\u064f": "", "\u0650": "", "\u0651": "", "\u0652": ""})
def digits(s): return (s or "").translate(_DIG)
def norm_fa(s): return re.sub(r"\s+", " ", digits(s).translate(_CH).lower()).strip()
def norm_latin(s): return re.sub(r"\s+", " ", (s or "").lower()).strip()

_DE_WORDS = {"der", "die", "das", "und", "ist", "nicht", "ich", "du", "wie", "was", "wo", "ein", "eine", "mit", "für", "wird", "heißt", "bedeutet", "auf", "deutsch", "warum", "wann", "kann", "mein", "bitte", "danke", "hallo", "gut", "zu", "von", "sind", "habe", "auch"}
_EN_WORDS = {"the", "is", "are", "what", "how", "why", "when", "where", "a", "an", "of", "to", "in", "and", "does", "do", "mean", "means", "word", "please", "thanks", "hello", "can", "i", "you", "my", "with", "for", "this", "that"}

def detect_lang(text):
    """Return 'fa' | 'de' | 'en' | 'zh' | None. Persian/Arabic script -> fa; German by umlauts/stop-words; otherwise English."""
    t = text or ""
    fa = sum(1 for c in t if "\u0600" <= c <= "\u06ff")
    zh = sum(1 for c in t if "\u4e00" <= c <= "\u9fff")
    lat = sum(1 for c in t if c.isascii() and c.isalpha())
    if fa and fa >= max(zh, 1) and fa >= lat * 0.5: return "fa"
    if zh and zh >= lat: return "zh"
    if lat:
        ws = set(re.findall(r"[a-zäöüß]+", t.lower()))
        de = len(ws & _DE_WORDS) + (2 if re.search(r"[äöüß]", t.lower()) else 0)
        en = len(ws & _EN_WORDS)
        if de > en and de >= 1: return "de"
        return "en"
    return None
