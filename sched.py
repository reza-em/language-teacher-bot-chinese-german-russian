"""Background scheduler: opt-in per-user reminders (user's time zone), group word of the day (opt-in per group), channel posts, quiz expiry."""
import time, logging, threading
import config, db, logic, srs, fmt
import core as C
import channels as CH
import groups as G
import ui
import course
from core import btn, kb, send, rtl, num
from texts import tr

log = logging.getLogger("sched")
REMIND_MAX_LATE_MIN = 180

def _minutes(hhmm): h, m = hhmm.split(":"); return int(h) * 60 + int(m)

def due_now(tz, hhmm, last_day, ts=None):
    """-> True when it is at/after hhmm in tz, not more than REMIND_MAX_LATE_MIN late, and not yet done for this local day."""
    now = logic.local_now(tz, ts); day = now.strftime("%Y-%m-%d")
    if last_day == day: return False
    late = now.hour * 60 + now.minute - _minutes(hhmm)
    return 0 <= late <= REMIND_MAX_LATE_MIN

def reminders(ts=None):
    sent = 0
    for u in db.q("SELECT * FROM users WHERE remind!='' AND can_dm=1 AND banned=0 AND onboarded=1"):
        if not logic.hhmm_ok(u["remind"]): continue
        day = logic.local_day(u["tz"], ts)
        if not due_now(u["tz"], u["remind"], u["last_remind"], ts):
            # past the window without sending (bot was down): mark the day so we never send late spam
            if u["last_remind"] != day and logic.local_now(u["tz"], ts).hour * 60 + logic.local_now(u["tz"], ts).minute - _minutes(u["remind"]) > REMIND_MAX_LATE_MIN:
                logic.update_user(u["id"], last_remind=day)
            continue
        logic.update_user(u["id"], last_remind=day)
        st = db.q1("SELECT * FROM daily WHERE user_id=? AND day=?", (u["id"], day))
        if st and st["answers"] >= u["daily_goal"]: continue           # goal already reached today: no nag
        lang = u["ui"] if u["ui"] in config.LANGS else "fa"
        ls = logic.user_langs(u["id"])                      # every language the learner studies: reviews are summed, each started course is mentioned
        text = tr(lang, "remind_msg", due=num(lang, sum(srs.due_count(u["id"], lang=l) for l in ls)), streak=num(lang, logic.streak_alive(u["id"])))
        rows = [[btn(tr(lang, "b_today"), "m:today")], [btn(tr(lang, "b_off"), "st:rm:n")]]
        for n_, l_ in enumerate(ls):
            try:
                ce = course.reminder_extra(u["id"], lang, tl=l_)
                if ce:
                    text += "\n\n" + ce[0]
                    if n_ == 0: rows.insert(0, ce[1])        # the guided course (of the active language) continues from the reminder
            except Exception as e: log.warning("course reminder: %s", type(e).__name__)
        r = send(u["id"], rtl(lang, text), kb(rows))
        if r: sent += 1
        else: logic.update_user(u["id"], can_dm=0)       # blocked the bot: stop trying
        time.sleep(0.05)
    return sent

def group_daily(ts=None):
    n = 0
    for ch in db.q("SELECT * FROM chats WHERE active=1 AND enabled=1 AND daily=1 AND type IN ('group','supergroup')"):
        if not due_now(ch["tz"], ch["daily_time"], ch["last_daily"], ts): continue
        logic.update_chat(ch["id"], last_daily=logic.local_day(ch["tz"], ts))
        try: G.group_word(ch["id"], ch, pin=True); n += 1
        except Exception as e: log.warning("group daily failed: %s", type(e).__name__)
    return n

def tick(ts=None):
    for fn in (reminders, group_daily, CH.tick):
        try: fn(ts)
        except Exception as e: log.exception("scheduler %s failed: %s", fn.__name__, C.safe(e))
    try: G.expire_quizzes()
    except Exception as e: log.warning("expire: %s", type(e).__name__)

def loop(interval=30):
    while True:
        tick(); time.sleep(interval)

def start():
    t = threading.Thread(target=loop, daemon=True, name="scheduler"); t.start(); return t
