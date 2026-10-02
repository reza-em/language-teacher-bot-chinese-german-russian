"""SQLite (WAL) storage. One connection per thread, explicit transactions, tiny helpers."""
import os, json, time, sqlite3, threading
from contextlib import contextmanager
import config

_path = config.DB_PATH
_local = threading.local()
_clock = time.time

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY, username TEXT, name TEXT, language_code TEXT,
  ui TEXT NOT NULL DEFAULT 'fa', expl TEXT NOT NULL DEFAULT 'fa', auto_lang INTEGER NOT NULL DEFAULT 1,
  level INTEGER NOT NULL DEFAULT 1, methods TEXT NOT NULL DEFAULT '', srs_mode TEXT NOT NULL DEFAULT 'leitner',
  daily_goal INTEGER NOT NULL DEFAULT 10, remind TEXT NOT NULL DEFAULT '', tz TEXT NOT NULL DEFAULT 'Asia/Tehran',
  last_remind TEXT NOT NULL DEFAULT '', pinyin_style TEXT NOT NULL DEFAULT 'marks',
  streak INTEGER NOT NULL DEFAULT 0, best_streak INTEGER NOT NULL DEFAULT 0, last_day TEXT NOT NULL DEFAULT '',
  xp INTEGER NOT NULL DEFAULT 0, ok INTEGER NOT NULL DEFAULT 0, bad INTEGER NOT NULL DEFAULT 0,
  banned INTEGER NOT NULL DEFAULT 0, is_admin INTEGER NOT NULL DEFAULT 0, onboarded INTEGER NOT NULL DEFAULT 0,
  first_seen INTEGER, last_seen INTEGER, awaiting TEXT, await_data TEXT,
  llm_day TEXT NOT NULL DEFAULT '', llm_n INTEGER NOT NULL DEFAULT 0, can_dm INTEGER NOT NULL DEFAULT 0, det TEXT NOT NULL DEFAULT '',
  target TEXT NOT NULL DEFAULT 'zh', tlangs TEXT NOT NULL DEFAULT 'zh'
);
CREATE TABLE IF NOT EXISTS ulang(user_id INTEGER NOT NULL, lang TEXT NOT NULL, level INTEGER NOT NULL DEFAULT 1, PRIMARY KEY(user_id, lang));
CREATE TABLE IF NOT EXISTS cards(
  user_id INTEGER NOT NULL, wid INTEGER NOT NULL,
  box INTEGER NOT NULL DEFAULT 1, ease REAL NOT NULL DEFAULT 2.5, ivl REAL NOT NULL DEFAULT 0, reps INTEGER NOT NULL DEFAULT 0,
  lapses INTEGER NOT NULL DEFAULT 0, due INTEGER NOT NULL DEFAULT 0, ok INTEGER NOT NULL DEFAULT 0, bad INTEGER NOT NULL DEFAULT 0,
  last INTEGER NOT NULL DEFAULT 0, added INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY(user_id, wid)
);
CREATE INDEX IF NOT EXISTS ix_cards_due ON cards(user_id, due);
CREATE TABLE IF NOT EXISTS mistakes(
  id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, wid INTEGER, etype TEXT, given TEXT, expected TEXT, ts INTEGER, resolved INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_mistakes_u ON mistakes(user_id, resolved);
CREATE TABLE IF NOT EXISTS sess(
  user_id INTEGER NOT NULL, chat_id INTEGER NOT NULL, data TEXT, updated INTEGER, PRIMARY KEY(user_id, chat_id)
);
CREATE TABLE IF NOT EXISTS daily(
  user_id INTEGER NOT NULL, day TEXT NOT NULL, new_words INTEGER NOT NULL DEFAULT 0, answers INTEGER NOT NULL DEFAULT 0,
  ok INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(user_id, day)
);
CREATE TABLE IF NOT EXISTS chats(
  id INTEGER PRIMARY KEY, type TEXT, title TEXT, username TEXT, added_at INTEGER, active INTEGER NOT NULL DEFAULT 1,
  ui TEXT NOT NULL DEFAULT 'fa', expl TEXT NOT NULL DEFAULT 'fa', level INTEGER NOT NULL DEFAULT 1,
  daily INTEGER NOT NULL DEFAULT 0, daily_time TEXT NOT NULL DEFAULT '09:00', tz TEXT NOT NULL DEFAULT 'Asia/Tehran',
  enabled INTEGER NOT NULL DEFAULT 1, last_daily TEXT NOT NULL DEFAULT '', bot_admin INTEGER NOT NULL DEFAULT 0,
  can_read_all INTEGER NOT NULL DEFAULT 0, added_by INTEGER, last_cmd INTEGER NOT NULL DEFAULT 0,
  auto INTEGER NOT NULL DEFAULT 0, pin INTEGER NOT NULL DEFAULT 0, intro_sent INTEGER NOT NULL DEFAULT 0,
  target TEXT NOT NULL DEFAULT 'zh'
);
CREATE TABLE IF NOT EXISTS gquiz(
  id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER NOT NULL, msg_id INTEGER, data TEXT, state TEXT NOT NULL DEFAULT 'open',
  created INTEGER, winner INTEGER
);
CREATE INDEX IF NOT EXISTS ix_gquiz_chat ON gquiz(chat_id, state);
CREATE TABLE IF NOT EXISTS gscores(
  chat_id INTEGER NOT NULL, user_id INTEGER NOT NULL, name TEXT, points INTEGER NOT NULL DEFAULT 0, wins INTEGER NOT NULL DEFAULT 0,
  answered INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(chat_id, user_id)
);
CREATE TABLE IF NOT EXISTS pending_channels(chat_id INTEGER PRIMARY KEY, title TEXT, username TEXT, ts INTEGER, can_post INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS channels(
  id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER NOT NULL UNIQUE, title TEXT, username TEXT, enabled INTEGER NOT NULL DEFAULT 1,
  times TEXT NOT NULL DEFAULT '[]', types TEXT NOT NULL DEFAULT '[]', lang TEXT NOT NULL DEFAULT 'fa', tz TEXT NOT NULL DEFAULT 'Asia/Tehran',
  btn INTEGER NOT NULL DEFAULT 1, added_at INTEGER, last_slot TEXT NOT NULL DEFAULT '', counter INTEGER NOT NULL DEFAULT 0, pinned_msg INTEGER
);
CREATE TABLE IF NOT EXISTS custom(
  id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, data TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1, created_by INTEGER, created INTEGER
);
CREATE TABLE IF NOT EXISTS gloss_cache(
  key TEXT PRIMARY KEY, lang TEXT, text TEXT, ts INTEGER
);
CREATE TABLE IF NOT EXISTS broadcasts(
  id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT, target TEXT, ts INTEGER, total INTEGER, sent INTEGER DEFAULT 0, failed INTEGER DEFAULT 0, state TEXT DEFAULT 'queued'
);
CREATE TABLE IF NOT EXISTS activity(day TEXT NOT NULL, user_id INTEGER NOT NULL, PRIMARY KEY(day, user_id));
CREATE TABLE IF NOT EXISTS gprompt(
  id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER NOT NULL, msg_id INTEGER, data TEXT, state TEXT NOT NULL DEFAULT 'open', created INTEGER
);
CREATE INDEX IF NOT EXISTS ix_gprompt ON gprompt(chat_id, msg_id);
CREATE TABLE IF NOT EXISTS course(
  user_id INTEGER NOT NULL, lang TEXT NOT NULL DEFAULT 'zh', cur TEXT NOT NULL DEFAULT '', step TEXT NOT NULL DEFAULT 'teach', page INTEGER NOT NULL DEFAULT 0,
  plan TEXT NOT NULL DEFAULT '', pos INTEGER NOT NULL DEFAULT 0, ok INTEGER NOT NULL DEFAULT 0,
  passed TEXT NOT NULL DEFAULT '', skipped TEXT NOT NULL DEFAULT '', scores TEXT NOT NULL DEFAULT '', placed TEXT NOT NULL DEFAULT '',
  pending TEXT NOT NULL DEFAULT '', started_course INTEGER NOT NULL DEFAULT 0, started INTEGER, updated INTEGER, PRIMARY KEY(user_id, lang)
);
"""

def now(): return int(_clock())

def set_path(p):
    global _path
    _path = p; close_all()

def close_all():
    c = getattr(_local, "c", None)
    if c:
        try: c[1].close()
        except Exception: pass
    _local.c = None

def _migrate(cn):
    """Add columns introduced after the first release (idempotent)."""
    cols = {r[1] for r in cn.execute("PRAGMA table_info(chats)").fetchall()}
    if "teacher" not in cols:
        cn.execute("ALTER TABLE chats ADD COLUMN teacher TEXT NOT NULL DEFAULT 'always'")
    if "target" not in cols:
        cn.execute("ALTER TABLE chats ADD COLUMN target TEXT NOT NULL DEFAULT 'zh'")
    ucols = {r[1] for r in cn.execute("PRAGMA table_info(users)").fetchall()}
    if "target" not in ucols:
        cn.execute("ALTER TABLE users ADD COLUMN target TEXT NOT NULL DEFAULT 'zh'")
        cn.execute("ALTER TABLE users ADD COLUMN tlangs TEXT NOT NULL DEFAULT 'zh'")
    ccols = {r[1] for r in cn.execute("PRAGMA table_info(course)").fetchall()}
    if ccols and "lang" not in ccols:      # v1 course table (one row per user) -> one row per (user, language)
        cn.execute("ALTER TABLE course RENAME TO course_v1")
        cn.executescript(SCHEMA)
        names = [r[1] for r in cn.execute("PRAGMA table_info(course_v1)").fetchall()]
        cl = ",".join(names)
        cn.execute(f"INSERT OR IGNORE INTO course({cl},lang) SELECT {cl},'zh' FROM course_v1")
        cn.execute("DROP TABLE course_v1")

def conn():
    c = getattr(_local, "c", None)
    if c and c[0] == _path: return c[1]
    if c:
        try: c[1].close()
        except Exception: pass
    d = os.path.dirname(_path)
    if d: os.makedirs(d, exist_ok=True)
    new = not os.path.exists(_path)
    cn = sqlite3.connect(_path, timeout=30, isolation_level=None, check_same_thread=False)
    cn.row_factory = sqlite3.Row
    cn.execute("PRAGMA journal_mode=WAL"); cn.execute("PRAGMA synchronous=NORMAL"); cn.execute("PRAGMA busy_timeout=30000")
    cn.executescript(SCHEMA)
    _migrate(cn)
    if new:
        try: os.chmod(_path, 0o600)
        except OSError: pass
    _local.c = (_path, cn); _local.depth = 0
    return cn

@contextmanager
def tx():
    cn = conn(); depth = getattr(_local, "depth", 0)
    if depth:
        _local.depth = depth + 1
        try: yield cn
        finally: _local.depth -= 1
        return
    cn.execute("BEGIN IMMEDIATE"); _local.depth = 1
    try:
        yield cn; cn.execute("COMMIT")
    except BaseException:
        cn.execute("ROLLBACK"); raise
    finally:
        _local.depth = 0

def q(sql, args=()): return [dict(r) for r in conn().execute(sql, args).fetchall()]
def q1(sql, args=()):
    r = conn().execute(sql, args).fetchone(); return dict(r) if r else None
def val(sql, args=(), default=None):
    r = conn().execute(sql, args).fetchone()
    return default if r is None or r[0] is None else r[0]
def ex(sql, args=()): return conn().execute(sql, args)

def meta_get(key, default=None):
    r = conn().execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    if r is None: return default
    try: return json.loads(r[0])
    except Exception: return default

def meta_set(key, value):
    conn().execute("INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, json.dumps(value, ensure_ascii=False)))

def init():
    conn()
    with tx():
        if meta_get("schema_version") is None:
            meta_set("schema_version", 1); meta_set("owner_id", config.OWNER_ID)
