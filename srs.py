"""Spaced repetition: Leitner boxes 1-5 (explicit intervals) or SM-2. Pure functions + tiny DB layer."""
import db

DAY = 86400
BOX_INTERVAL_DAYS = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16}     # box -> days until next review
RELEARN_SECONDS = 600                                    # a wrong answer returns the card in 10 minutes
MASTERED_DAYS = 30                                       # a correct answer in box 5 -> "mastered", review in 30 days

def leitner(box, correct):
    """-> (new_box, interval_seconds). Wrong: back to box 1. Right: next box (box 5 stays, 30 days)."""
    if not correct: return 1, RELEARN_SECONDS
    if box >= 5: return 5, MASTERED_DAYS * DAY
    nb = box + 1
    return nb, BOX_INTERVAL_DAYS[nb] * DAY

def sm2(ease, ivl_days, reps, quality):
    """Classic SM-2. quality 0-5 (>=3 is a pass). -> (ease, ivl_days, reps)."""
    if quality < 3: return max(1.3, ease - 0.2), 0.0, 0
    reps += 1
    if reps == 1: ivl = 1.0
    elif reps == 2: ivl = 6.0
    else: ivl = round(ivl_days * ease, 1)
    ease = max(1.3, ease + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    return ease, ivl, reps

def get_card(uid, wid): return db.q1("SELECT * FROM cards WHERE user_id=? AND wid=?", (uid, wid))

def add_card(uid, wid):
    db.ex("INSERT OR IGNORE INTO cards(user_id,wid,box,due,added) VALUES(?,?,1,?,?)", (uid, wid, db.now(), db.now()))

def review(uid, wid, correct, mode="leitner", quality=None):
    """Record one answer for a card (creates it if missing). Returns the updated card."""
    add_card(uid, wid)
    c = get_card(uid, wid); now = db.now()
    if mode == "sm2":
        qv = quality if quality is not None else (4 if correct else 1)
        ease, ivl, reps = sm2(c["ease"], c["ivl"], c["reps"], qv)
        due = now + (int(ivl * DAY) if ivl > 0 else RELEARN_SECONDS)
        box = c["box"]
        if correct: box = min(5, box + 1) if ivl >= 6 else box
        else: box = 1
        db.ex("UPDATE cards SET ease=?,ivl=?,reps=?,due=?,box=?,last=?,ok=ok+?,bad=bad+?,lapses=lapses+? WHERE user_id=? AND wid=?",
              (ease, ivl, reps, due, box, now, int(correct), int(not correct), int(not correct), uid, wid))
    else:
        box, secs = leitner(c["box"], correct)
        db.ex("UPDATE cards SET box=?,due=?,last=?,reps=reps+?,ok=ok+?,bad=bad+?,lapses=lapses+? WHERE user_id=? AND wid=?",
              (box, now + secs, now, int(correct), int(correct), int(not correct), int(not correct), uid, wid))
    return get_card(uid, wid)

def _rng(uid, lang=None):
    """(lo, hi) word-id window of the learner's active target language (Chinese < 1,000,000; German 1M+; Russian 2M+)."""
    if lang is None: lang = db.val("SELECT target FROM users WHERE id=?", (uid,), "zh") or "zh"
    return {"de": (1_000_000, 2_000_000), "ru": (2_000_000, 3_000_000)}.get(lang, (0, 1_000_000))

def due_cards(uid, limit=20, now=None, lang=None):
    now = db.now() if now is None else now; lo, hi = _rng(uid, lang)
    return db.q("SELECT * FROM cards WHERE user_id=? AND due<=? AND wid>=? AND wid<? ORDER BY due LIMIT ?", (uid, now, lo, hi, limit))

def due_count(uid, lang=None):
    lo, hi = _rng(uid, lang)
    return db.val("SELECT COUNT(*) FROM cards WHERE user_id=? AND due<=? AND wid>=? AND wid<?", (uid, db.now(), lo, hi), 0)

def box_counts(uid, lang=None):
    out = {b: 0 for b in range(1, 6)}; lo, hi = _rng(uid, lang)
    for r in db.q("SELECT box, COUNT(*) n FROM cards WHERE user_id=? AND wid>=? AND wid<? GROUP BY box", (uid, lo, hi)): out[r["box"]] = r["n"]
    return out

def total_cards(uid, lang=None):
    lo, hi = _rng(uid, lang)
    return db.val("SELECT COUNT(*) FROM cards WHERE user_id=? AND wid>=? AND wid<?", (uid, lo, hi), 0)
def mastered(uid, lang=None):
    lo, hi = _rng(uid, lang)
    return db.val("SELECT COUNT(*) FROM cards WHERE user_id=? AND box=5 AND reps>=3 AND wid>=? AND wid<?", (uid, lo, hi), 0)
