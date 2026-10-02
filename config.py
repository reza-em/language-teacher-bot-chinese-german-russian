"""Central constants for the Chinese-teacher bot. Token comes ONLY from the environment (never printed/logged)."""
import os

BOT_NAME = "معلم زبان | Language Teacher"
BOT_NAME_FA = "معلم زبان"
BOT_NAME_EN = "Language Teacher"
BOT_NAME_DE = "Sprachlehrer"

TOKEN_ENV = "CHINESE_TELEGRAM_BOT_TOKEN"
OWNER_USERNAME = os.environ.get("OWNER_USERNAME", "example_owner")
OWNER_ID = int(os.environ.get("OWNER_ID", "0") or 0)

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("CHINESE_DB_PATH") or os.path.join(BASE, "chinese.db")
DATA_DIR = os.path.join(BASE, "data")
ASSETS = os.path.join(BASE, "assets")
TTS_DIR = os.environ.get("CHINESE_TTS_DIR") or os.path.join(BASE, "tts_cache")

LANGS = ("fa", "en", "de")
DEFAULT_LANG = "fa"
DEFAULT_TZ = "Asia/Tehran"
TIMEZONES = ["Asia/Tehran", "Europe/Berlin", "Europe/London", "Asia/Dubai", "Asia/Shanghai", "America/New_York", "UTC"]
DEFAULT_REMIND_TIME = "20:00"          # suggested time; reminders are OPT-IN (off until the user enables them)
DEFAULT_GROUP_DAILY_TIME = "09:00"     # group daily word: OFF until a group admin enables it
DEFAULT_CHANNEL_TIMES = ["09:00", "13:00", "18:00", "21:00"]

# ---- LLM (optional, OpenAI-compatible). The API key is read from the environment only. ----
LLM_KEY_ENV = "CHINESE_LLM_API_KEY"
LLM_BASE_ENV = "CHINESE_LLM_BASE_URL"      # default https://api.openai.com/v1
LLM_MODEL_ENV = "CHINESE_LLM_MODEL"        # default gpt-4o-mini
LLM_STT_ENV = "CHINESE_LLM_STT_MODEL"      # e.g. whisper-1 (voice-message pronunciation check); empty = off
LLM_DEFAULT_BASE = "https://api.openai.com/v1"
LLM_DEFAULT_MODEL = "gpt-4o-mini"
LLM_DAILY_LIMIT = 20                       # per user per day (owner can change in the admin panel)

# ---- limits / anti-spam ----
PRIVATE_MSGS_PER_MIN = 40
GROUP_USER_CMDS_PER_MIN = 6
GROUP_CHAT_CMDS_PER_MIN = 20
GROUP_QUIZ_COOLDOWN = 45               # seconds between group quizzes for non-admins
GROUP_QUIZ_TIMEOUT = 120               # seconds before an unanswered group quiz is closed
BROADCAST_PER_SEC = 20
PAGE_SIZE = 8

# ---- group teacher mode (unsolicited replies are rate-limited so the bot never spams) ----
TEACHER_MODES = ("always", "mention", "off")
TEACHER_DEFAULT_MODE = "always"        # only for messages that look like Chinese / learning questions
TEACHER_CHAT_COOLDOWN = 90             # seconds between unsolicited replies in one group
TEACHER_USER_COOLDOWN = 300            # seconds between unsolicited replies to the same member
TEACHER_MAX_PER_HOUR = 10              # unsolicited replies per group per hour
TEACHER_LLM_PER_GROUP_DAY = 80         # LLM-backed teacher replies per group per day
TEACHER_PROMPT_TTL = 900               # seconds a mini-exercise stays open for replies
TEACHER_MAX_LEN = 400                  # ignore unsolicited messages longer than this
