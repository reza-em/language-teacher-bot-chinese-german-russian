"""Text-to-speech. Primary: edge-tts (Microsoft Edge neural voices, needs internet, free, no key). Fallback: gTTS if installed.
Results are cached on disk by text hash. Telegram voice messages need OGG/Opus, so mp3 is converted with ffmpeg when available
(otherwise the mp3 is sent with sendAudio)."""
import os, hashlib, asyncio, subprocess, logging, shutil, threading
import config

log = logging.getLogger("tts")
VOICE = os.environ.get("CHINESE_TTS_VOICE", "zh-CN-XiaoxiaoNeural")
VOICES = {"zh": VOICE, "de": os.environ.get("GERMAN_TTS_VOICE", "de-DE-KatjaNeural"), "ru": os.environ.get("RUSSIAN_TTS_VOICE", "ru-RU-SvetlanaNeural")}
GTTS_LANG = {"zh": "zh-CN", "de": "de", "ru": "ru"}
_lock = threading.Lock()

def detect(text, hint=None):
    """Which language's voice reads this text: hanzi -> zh, Cyrillic -> ru, otherwise the hint (the learner's target language) or zh."""
    t = text or ""
    if any("\u4e00" <= c <= "\u9fff" or "\u3400" <= c <= "\u4dbf" for c in t): return "zh"
    if any("\u0400" <= c <= "\u04ff" for c in t): return "ru"
    return hint if hint in VOICES else "zh"

def cache_path(text, ext="mp3", lang="zh"):
    h = hashlib.sha256((VOICES.get(lang, VOICE) + "|" + text).encode()).hexdigest()[:24]
    os.makedirs(config.TTS_DIR, exist_ok=True)
    return os.path.join(config.TTS_DIR, f"{h}.{ext}")

def _edge(text, out, lang="zh"):
    import edge_tts
    async def run():
        await asyncio.wait_for(edge_tts.Communicate(text, VOICES.get(lang, VOICE)).save(out), 25)
    asyncio.run(run())

def _gtts(text, out, lang="zh"):
    from gtts import gTTS
    gTTS(text, lang=GTTS_LANG.get(lang, "zh-CN")).save(out)

def synth_mp3(text, lang=None):
    """-> path of an mp3 file, or None if every engine failed. `lang` = zh/de/ru voice (auto-detected by script when omitted)."""
    text = (text or "").strip()[:300]
    if not text: return None
    lang = detect(text, lang)
    text = text.replace("\u0301", "")
    p = cache_path(text, lang=lang)
    if os.path.exists(p) and os.path.getsize(p) > 500: return p
    with _lock:
        for eng in (_edge, _gtts):
            try:
                tmp = p + ".part"
                eng(text, tmp, lang)
                if os.path.exists(tmp) and os.path.getsize(tmp) > 500:
                    os.replace(tmp, p); return p
            except Exception as e:
                log.warning("tts engine %s failed: %s", eng.__name__, type(e).__name__)
            finally:
                try: os.remove(p + ".part")
                except OSError: pass
    return None

def to_ogg(mp3):
    ogg = mp3[:-4] + ".ogg"
    if os.path.exists(ogg): return ogg
    if not shutil.which("ffmpeg"): return None
    try:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-c:a", "libopus", "-b:a", "32k", ogg], check=True, timeout=30)
        return ogg
    except Exception as e:
        log.warning("ffmpeg failed: %s", type(e).__name__); return None

def audio_bytes(text, lang=None):
    """-> (bytes, kind) kind='voice' (ogg/opus) or 'audio' (mp3) or (None, None)."""
    mp3 = synth_mp3(text, lang)
    if not mp3: return None, None
    ogg = to_ogg(mp3)
    if ogg: return open(ogg, "rb").read(), "voice"
    return open(mp3, "rb").read(), "audio"

def prebuilt(name):
    """Pre-generated pinyin audio (initials/finals/tones) shipped in assets/audio."""
    p = os.path.join(config.ASSETS, "audio", name + ".mp3")
    return open(p, "rb").read() if os.path.exists(p) else None
