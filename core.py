"""Telegram plumbing: API calls, token redaction, keyboards, sending, rate limits, tiny helpers."""
import os, sys, json, logging, re, time, threading, collections
import requests
import config

TOKEN = os.environ.get(config.TOKEN_ENV, "")
BOT_USERNAME = ""
BOT_ID = 0
log = logging.getLogger("bot")

def api_url(method): return f"https://api.telegram.org/bot{TOKEN}/{method}"

class RedactFilter(logging.Filter):
    def filter(self, record):
        try: msg = record.getMessage()
        except Exception: return True
        if TOKEN and TOKEN in msg:
            record.msg = msg.replace(TOKEN, "<TOKEN>"); record.args = ()
        return True

def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    for h in logging.getLogger().handlers: h.addFilter(RedactFilter())
    logging.getLogger("urllib3").setLevel(logging.WARNING)

def safe(e):
    s = str(e)
    return s.replace(TOKEN, "<TOKEN>") if TOKEN else s

sess = requests.Session()

class ApiError(Exception):
    def __init__(self, msg, code=0, retry_after=0):
        super().__init__(msg); self.code = code; self.retry_after = retry_after

def call(method, data=None, files=None, timeout=60):
    try:
        r = sess.post(api_url(method), data=data, files=files, timeout=timeout)
    except requests.RequestException as e:
        raise ApiError("network: " + type(e).__name__)
    try: j = r.json()
    except Exception: raise ApiError(f"bad response HTTP {r.status_code}", r.status_code)
    if not j.get("ok"):
        raise ApiError(j.get("description", "unknown error"), j.get("error_code", 0), (j.get("parameters") or {}).get("retry_after", 0))
    return j["result"]

# ---------------- text helpers ----------------
def esc(t): return str(t if t is not None else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
def num(lang, n): return str(n).translate(_FA) if lang == "fa" else str(n)
_DIG = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
def norm_digits(s): return (s or "").translate(_DIG)
def parse_int(s, lo=0, hi=10**9):
    s = norm_digits(s).strip()
    if not re.fullmatch(r"\d{1,9}", s): return None
    n = int(s); return n if lo <= n <= hi else None

RLM = "\u200f"
def rtl(lang, text):
    """Persian messages: a right-to-left mark at the start of each line keeps mixed Persian/Latin/Chinese lines right-aligned."""
    if lang != "fa": return text
    return "\n".join((RLM + ln) if ln.strip() and not ln.startswith(RLM) else ln for ln in text.split("\n"))

# ---------------- keyboards ----------------
def kb(rows): return json.dumps({"inline_keyboard": rows})
def btn(text, data=None, url=None):
    b = {"text": text}
    if url: b["url"] = url
    else: b["callback_data"] = data
    return b
def grid(buttons, per=2): return [buttons[i:i + per] for i in range(0, len(buttons), per)]

def deep_link(payload=""):
    return f"https://t.me/{BOT_USERNAME}" + (f"?start={payload}" if payload else "")

# ---------------- sending ----------------
def send(chat_id, text, markup=None, html=True, **extra):
    data = {"chat_id": chat_id, "text": text[:4096], "disable_web_page_preview": True}
    if markup: data["reply_markup"] = markup
    if html: data["parse_mode"] = "HTML"
    data.update(extra)
    try: return call("sendMessage", data)
    except ApiError as e:
        if e.retry_after and e.retry_after <= 30:
            time.sleep(e.retry_after + 1)
            try: return call("sendMessage", data)
            except ApiError: pass
        log.warning("sendMessage failed: %s", safe(e)[:100])

def show(chat_id, msg_id, text, markup=None, html=True):
    """Edit a panel message in place if possible, else send a new one."""
    if msg_id:
        data = {"chat_id": chat_id, "message_id": msg_id, "text": text[:4096], "disable_web_page_preview": True}
        if markup: data["reply_markup"] = markup
        if html: data["parse_mode"] = "HTML"
        try: return call("editMessageText", data)
        except ApiError as e:
            if "not modified" in str(e).lower(): return None
    return send(chat_id, text, markup, html)

def send_photo(chat_id, photo, caption="", markup=None, **extra):
    """photo: bytes (upload) or a file_id/URL string."""
    data = {"chat_id": chat_id, "parse_mode": "HTML"}
    if caption: data["caption"] = caption[:1024]
    if markup: data["reply_markup"] = markup
    data.update(extra)
    try:
        if isinstance(photo, (bytes, bytearray)):
            return call("sendPhoto", data, files={"photo": ("img.png", photo, "image/png")}, timeout=90)
        data["photo"] = photo; return call("sendPhoto", data)
    except ApiError as e:
        log.warning("sendPhoto failed: %s", safe(e)[:100])

def send_voice(chat_id, ogg_bytes, caption="", markup=None, **extra):
    data = {"chat_id": chat_id}
    if caption: data["caption"] = caption[:1024]; data["parse_mode"] = "HTML"
    if markup: data["reply_markup"] = markup
    data.update(extra)
    try: return call("sendVoice", data, files={"voice": ("v.ogg", ogg_bytes, "audio/ogg")}, timeout=90)
    except ApiError as e:
        log.warning("sendVoice failed: %s", safe(e)[:100])

def send_document(chat_id, path, caption=""):
    try:
        with open(path, "rb") as f:
            return call("sendDocument", {"chat_id": chat_id, "caption": caption[:1000]}, files={"document": (os.path.basename(path), f)}, timeout=300)
    except ApiError as e:
        log.warning("sendDocument failed: %s", safe(e)[:100])

def delete_msg(chat_id, msg_id):
    if not msg_id: return
    try: call("deleteMessage", {"chat_id": chat_id, "message_id": msg_id})
    except ApiError: pass

def answer_cb(cid, text="", alert=False):
    d = {"callback_query_id": cid}
    if text: d["text"] = text[:200]; d["show_alert"] = alert
    try: call("answerCallbackQuery", d)
    except ApiError as e: log.warning("answerCallbackQuery: %s", safe(e)[:80])

# ---------------- rate limiting (sliding window, in memory) ----------------
_rl = collections.defaultdict(collections.deque)
_rl_lock = threading.Lock()
def rate_ok(key, limit, window=60.0, now=None):
    now = time.time() if now is None else now
    with _rl_lock:
        d = _rl[key]
        while d and d[0] <= now - window: d.popleft()
        if len(d) >= limit: return False
        d.append(now); return True

def rate_reset(): 
    with _rl_lock: _rl.clear()
