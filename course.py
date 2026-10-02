"""Guided course runtime: persisted per-user progress, teaching pages, practice sessions (via ui's exercise engine), placement test,
jump/skip/restart, daily-reminder hook. Curriculum: curriculum.py; content/exercises: lesson_content.py."""
import json, logging, random, functools
import config, db, logic, srs, langs
import core as C
import curriculum as Cu
import lesson_content as LC
from core import btn, kb, esc, num, rtl, send
from texts import tr

log = logging.getLogger("course")

# ---------------------------------------------------------------- state
def _ul(uid): return logic.user_lang(uid)
def _el(uid): return logic.expl_lang(uid)

def get(uid):
    r = db.q1("SELECT * FROM course WHERE user_id=? AND lang=?", (uid, Cu.cur_lang()))
    if not r: return None
    for k, d in (("passed", []), ("skipped", []), ("scores", {}), ("plan", []), ("placed", {})):
        try: r[k] = json.loads(r[k]) if r[k] else d
        except Exception: r[k] = d
    return r

def save(uid, **kw):
    for k in ("passed", "skipped", "scores", "plan", "placed"):
        if k in kw and not isinstance(kw[k], str): kw[k] = json.dumps(kw[k], ensure_ascii=False)
    kw["updated"] = db.now()
    db.ex(f"UPDATE course SET {', '.join(k + '=?' for k in kw)} WHERE user_id=? AND lang=?", (*kw.values(), uid, Cu.cur_lang()))

def ensure(uid):
    db.ex("INSERT OR IGNORE INTO course(user_id,lang,cur,step,started,updated) VALUES(?,?,?,?,?,?)", (uid, Cu.cur_lang(), Cu.get(0)["id"], "teach", db.now(), db.now()))
    return get(uid)

def has_course(uid):
    r = get(uid); return bool(r and r["started_course"])

def _done_ids(r): return set(r["passed"]) | set(r["skipped"])

def _cur_index(r):
    i = Cu.index(r["cur"]); return 0 if i is None else i

def _next_after(r, i):
    """First lesson after index i that is neither passed nor skipped; None when the course is complete."""
    done = _done_ids(r)
    for j in range(i + 1, Cu.total()):
        if Cu.get(j)["id"] not in done: return j
    for j in range(0, i + 1):          # wrapped: something earlier was left open
        if Cu.get(j)["id"] not in done and Cu.get(j)["id"] != Cu.get(i)["id"]: return j
    return None

def _pct(r): return round(100 * len(_done_ids(r)) / max(1, Cu.total()))

# ---------------------------------------------------------------- views
def _edit(uid, mid, text, markup=None):
    from ui import edit
    return edit(uid, mid, text[:4000], markup)

def _menu_row(lang): return [btn(tr(lang, "b_menu"), "m:menu")]

def _k(key):
    """Text key for the current course language: Chinese keeps the original cr_* texts, German/Russian use the generic cx_* ones."""
    return key if Cu.cur_lang() == "zh" else "cx_" + key[3:]

def _lp(): return {"l": langs.name(Cu.cur_lang(), "en")}      # unused placeholder source (texts use {ln})

def _ln(lang): return langs.label(Cu.cur_lang(), lang)

def path_menu(uid, mid=None, pre="c"):
    """The three-way choice. pre='ob' during onboarding, 'c' anywhere else."""
    lang = _ul(uid)
    rows = [[btn(tr(lang, "cr_b_place"), f"{pre}:pl")], [btn(tr(lang, "cr_b_zero"), f"{pre}:zero")], [btn(tr(lang, "cr_b_self"), f"{pre}:self")]]
    if pre != "ob": rows.append(_menu_row(lang))
    _edit(uid, mid, tr(lang, _k("cr_pick_path"), ln=_ln(lang), n=num(lang, Cu.total())), kb(rows))

def self_menu(uid, mid=None, pre="c"):
    lang = _ul(uid)
    L = Cu.cur_lang()
    rows = [[btn(tr(lang, f"lvl_{n}") if L == "zh" else (f"🌱 {tr(lang, 'cr_tier0')}" if n == 0 else f"{langs.flag(L)} {langs.level_name(L, n)}"), f"ob:lv:{n}" if pre == "ob" else f"st:lv:{n}")] for n in langs.levels(L)]
    rows.append([btn(tr(lang, "cr_b_zero2"), f"{pre}:zero")])
    if pre != "ob": rows.append(_menu_row(lang))
    _edit(uid, mid, tr(lang, "cr_self_text"), kb(rows))

def hub(uid, mid=None):
    r = get(uid); lang = _ul(uid)
    if not r or not r["started_course"]: return path_menu(uid, mid)
    i = _cur_index(r); les = Cu.get(i); done = _done_ids(r)
    lines = []
    for key, emoji, name in Cu.modules():
        a, b = Cu.module_range(key); n = b - a + 1; d = sum(1 for j in range(a, b + 1) if Cu.get(j)["id"] in done)
        lines.append(f"{'✅' if d == n else ('▶️' if a <= i <= b else '▫️')} {emoji} {esc(Cu.t3(name, lang))} — {num(lang, d)}/{num(lang, n)}")
    if r["step"] == "done":
        head = tr(lang, "cr_hub_done")
    else:
        sub = {"teach": "cr_st_teach", "practice": "cr_st_practice", "retry": "cr_st_retry"}[r["step"]]
        pos = f" ({num(lang, r['pos'])}/{num(lang, len(r['plan']))})" if r["step"] == "practice" and r["plan"] else ""
        head = tr(lang, "cr_hub_cur", i=num(lang, i + 1), n=num(lang, Cu.total()), title=esc(Cu.title(les, lang)), st=tr(lang, sub) + pos)
    text = tr(lang, "cr_hub", pct=num(lang, _pct(r)), head=head, mods="\n".join(lines))
    if Cu.cur_lang() != "zh": text = f"{langs.label(Cu.cur_lang(), lang)}\n" + text
    rows = []
    if r["step"] != "done": rows.append([btn(tr(lang, "cr_b_go"), "c:go")])
    rows.append([btn(tr(lang, "cr_b_jump"), "c:jm"), btn(tr(lang, "cr_b_skip"), "c:sk")] if r["step"] != "done" else [btn(tr(lang, "cr_b_jump"), "c:jm")])
    rows.append([btn(tr(lang, "cr_b_place"), "c:pl"), btn(tr(lang, "cr_b_restart"), "c:rs")])
    rows.append([btn(tr(lang, "b_review"), "m:review"), btn(tr(lang, "b_progress"), "m:progress")])
    rows.append(_menu_row(lang))
    _edit(uid, mid, text, kb(rows))

def start_zero(uid, mid=None):
    """Begin the guided course at lesson 1 (never wipes existing progress: asks first)."""
    r = get(uid)
    if r and r["started_course"] and (r["passed"] or r["skipped"]): return hub(uid, mid)
    ensure(uid); save(uid, cur=Cu.get(0)["id"], step="teach", page=0, plan=[], pos=0, ok=0, started_course=1, pending="")
    lang = _ul(uid); from ui import out
    out(uid, tr(lang, _k("cr_zero_intro"), n=num(lang, Cu.total()), ln=_ln(lang)))
    teach(uid, None, 0)

def teach(uid, mid=None, page=0):
    r = get(uid); lang = _ul(uid)
    if not r: return path_menu(uid, mid)
    i = _cur_index(r); les = Cu.get(i)
    pg = LC.pages(les, lang, _el(uid), i, Cu.total()); page = max(0, min(page, len(pg) - 1))
    for wid in LC.srs_items(les): srs.add_card(uid, wid)          # taught items enter the user's Leitner/SM-2 box
    save(uid, step="teach", page=page, plan=[], pos=0, ok=0, cur=les["id"])
    text, rows = pg[page]; rows = [list(x) for x in rows]
    nav = []
    if page > 0: nav.append(btn("⬅️", f"c:pg:{page - 1}"))
    if len(pg) > 1: nav.append(btn(f"{num(lang, page + 1)}/{num(lang, len(pg))}", "noop"))
    if page < len(pg) - 1: nav.append(btn("➡️", f"c:pg:{page + 1}"))
    if nav: rows.append(nav)
    if page == len(pg) - 1: rows.append([btn(tr(lang, "cr_b_practice"), "c:pr")])
    rows.append([btn(tr(lang, "cr_b_skip"), "c:sk"), btn(tr(lang, "cr_b_hub"), "c:hub")])
    _edit(uid, mid, text, kb(rows))

def practice(uid, mid=None, fresh=True):
    r = get(uid)
    if not r: return path_menu(uid, mid)
    les = Cu.get(_cur_index(r))
    if fresh or not r["plan"]:
        sp = LC.plan(les, uid); save(uid, step="practice", plan=sp, pos=0, ok=0); r = get(uid)
    _open_session(uid, r, les)

def _open_session(uid, r, les):
    from ui import set_sess, next_exercise, out
    lang = _ul(uid); plan = r["plan"]
    set_sess(uid, {"mode": "course", "kind": "course", "n": r["pos"], "ok": r["ok"], "xp": 0, "total": len(plan), "plan": plan, "lid": les["id"], "wq": [], "L": Cu.cur_lang()})
    logic.set_await(uid, None)
    out(uid, tr(lang, "cr_practice_intro", title=esc(Cu.title(les, lang)), n=num(lang, len(plan)), need=num(lang, LC.pass_need(len(plan)))))
    next_exercise(uid, None)

def go(uid, mid=None):
    """'ادامه درس': resume exactly where the learner stopped."""
    r = get(uid)
    if not r or not r["started_course"]: return path_menu(uid, mid)
    if r["step"] == "done": return hub(uid, mid)
    if r["step"] == "practice" and r["plan"] and r["pos"] < len(r["plan"]): return practice(uid, mid, fresh=False)
    if r["step"] == "retry": return _retry_screen(uid, mid, r)
    return teach(uid, mid, r["page"] if r["step"] == "teach" else 0)

def _retry_screen(uid, mid, r):
    lang = _ul(uid); les = Cu.get(_cur_index(r))
    rows = [[btn(tr(lang, "cr_b_again"), "c:pr"), btn(tr(lang, "cr_b_review_lesson"), "c:pg:0")], [btn(tr(lang, "cr_b_skip"), "c:sk"), btn(tr(lang, "cr_b_hub"), "c:hub")]]
    _edit(uid, mid, tr(lang, "cr_retry", title=esc(Cu.title(les, lang))), kb(rows))

def make_ex(uid, s):
    """ui.next_exercise hook for course/placement sessions."""
    spec = s["plan"][s["n"]]
    return LC.build_exercise(spec, uid, _el(uid))

def on_answer(uid, s, ok):
    """ui.apply_result hook (also called for a skipped question)."""
    if s.get("mode") == "course":
        save(uid, pos=s["n"], ok=s["ok"])
    elif s.get("mode") == "place":
        spec = s["plan"][s["n"] - 1]; t = s.setdefault("tiers", {}); k = str(spec.get("tier", 0))
        t[k] = t.get(k, 0) + (1 if ok else 0); from ui import set_sess; set_sess(uid, s)

def finish(uid, s, mid=None):
    from ui import clear_sess
    mode = s.get("mode"); lang = _ul(uid)
    clear_sess(uid); logic.set_await(uid, None)
    if mode == "place": return _finish_place(uid, s)
    r = get(uid)
    if not r: return
    total = len(r["plan"]); les = Cu.get(_cur_index(r))
    if r["step"] != "practice" or r["pos"] < total:
        rows = [[btn(tr(lang, "cr_b_go"), "c:go")], [btn(tr(lang, "cr_b_hub"), "c:hub"), btn(tr(lang, "b_menu"), "m:menu")]]
        return send(uid, rtl(lang, tr(lang, "cr_paused", title=esc(Cu.title(les, lang)), pos=num(lang, r["pos"]), n=num(lang, total))), kb(rows))
    ok = r["ok"]; need = LC.pass_need(total); pct = round(100 * ok / max(1, total))
    if ok >= need:
        passed = list(dict.fromkeys(r["passed"] + [les["id"]])); sc = dict(r["scores"]); sc[les["id"]] = [ok, total]
        r2 = dict(r, passed=passed); nxt = _next_after(r2, _cur_index(r))
        db.ex("UPDATE users SET xp=xp+20 WHERE id=?", (uid,))
        if nxt is None:
            save(uid, passed=passed, scores=sc, step="done", plan=[], pos=0, ok=0, page=0)
            rows = [[btn(tr(lang, "cr_b_hub"), "c:hub")], [btn(tr(lang, "b_review"), "m:review"), btn(tr(lang, "b_quiz"), "m:quiz")], _menu_row(lang)]
            return send(uid, rtl(lang, tr(lang, "cr_pass", ok=num(lang, ok), n=num(lang, total), pct=num(lang, pct), nxt=tr(lang, "cr_all_done"))), kb(rows))
        save(uid, passed=passed, scores=sc, cur=Cu.get(nxt)["id"], step="teach", plan=[], pos=0, ok=0, page=0)
        rows = [[btn(tr(lang, "cr_b_next_lesson"), "c:go")], [btn(tr(lang, "b_mistakes"), "ms:list"), btn(tr(lang, "cr_b_hub"), "c:hub")], _menu_row(lang)]
        return send(uid, rtl(lang, tr(lang, "cr_pass", ok=num(lang, ok), n=num(lang, total), pct=num(lang, pct), nxt=tr(lang, "cr_next_is", title=esc(Cu.title(Cu.get(nxt), lang))))), kb(rows))
    save(uid, step="retry")
    rows = [[btn(tr(lang, "cr_b_again"), "c:pr"), btn(tr(lang, "cr_b_review_lesson"), "c:pg:0")], [btn(tr(lang, "b_mistakes"), "ms:list"), btn(tr(lang, "cr_b_skip"), "c:sk")], [btn(tr(lang, "cr_b_hub"), "c:hub")]]
    send(uid, rtl(lang, tr(lang, "cr_fail", ok=num(lang, ok), n=num(lang, total), pct=num(lang, pct), need=num(lang, need))), kb(rows))

# ---------------------------------------------------------------- placement test
def start_placement(uid, mid=None):
    from ui import set_sess, next_exercise, out
    lang = _ul(uid); L = Cu.cur_lang(); plan = LC.placement_plan(L)
    set_sess(uid, {"mode": "place", "kind": "place", "n": 0, "ok": 0, "xp": 0, "total": len(plan), "plan": plan, "wq": [], "tiers": {}, "L": L})
    logic.set_await(uid, None)
    out(uid, tr(lang, _k("cr_place_intro"), n=num(lang, len(plan)), ln=_ln(lang)))
    next_exercise(uid, None)

def _finish_place(uid, s):
    lang = _ul(uid); answered = s["n"] - (0 if s.get("answered") else 1)
    if answered < s["total"]:
        return send(uid, rtl(lang, tr(lang, "cr_place_stopped")), kb([[btn(tr(lang, "cr_b_place"), "c:pl"), btn(tr(lang, "cr_b_zero"), "c:zero")], _menu_row(lang)]))
    tiers = {int(k): v for k, v in (s.get("tiers") or {}).items()}
    L = Cu.cur_lang(); lid, level, why = LC.recommend(tiers, L)
    ensure(uid); save(uid, placed={"lid": lid, "level": level, "tiers": tiers})
    if L == "zh": names = [tr(lang, "cr_tier0"), "HSK 1", "HSK 2", "HSK 3"]; per, need_ = 3, 2
    else: names = [tr(lang, "cx_tier0_" + L), "A1", "A2"]; per, need_ = 4, 3
    lines = "\n".join(f"{'✅' if tiers.get(t, 0) >= need_ else '⚠️'} {names[t]}: {num(lang, tiers.get(t, 0))}/{num(lang, per)}" for t in range(len(names)))
    les = Cu.get(Cu.index(lid))
    text = tr(lang, "cr_place_result", lines=lines, rec=tr(lang, why), start=esc(Cu.title(les, lang)), mod=esc(Cu.module_name(les["mod"], lang)))
    rows = [[btn(tr(lang, "cr_b_take_rec"), "c:rec")], [btn(tr(lang, "cr_b_zero"), "c:zero")], _menu_row(lang)]
    send(uid, rtl(lang, text), kb(rows))

def take_recommendation(uid, mid=None):
    r = get(uid); lang = _ul(uid)
    pl = (r or {}).get("placed") or {}
    if not pl.get("lid") or Cu.index(pl["lid"]) is None: return start_placement(uid, mid)
    j = Cu.index(pl["lid"]); before = [Cu.get(n)["id"] for n in range(j)]
    skipped = list(dict.fromkeys(r["skipped"] + [x for x in before if x not in r["passed"]]))
    save(uid, skipped=skipped, cur=pl["lid"], step="teach", page=0, plan=[], pos=0, ok=0, started_course=1)
    logic.update_user(uid, level=int(pl.get("level", 1)))
    teach(uid, mid, 0)

# ---------------------------------------------------------------- jump / skip / restart
def jump_modules(uid, mid=None):
    lang = _ul(uid); r = get(uid); done = _done_ids(r) if r else set(); rows = []
    for mi, (key, emoji, name) in enumerate(Cu.modules()):
        a, b = Cu.module_range(key); d = sum(1 for j in range(a, b + 1) if Cu.get(j)["id"] in done)
        rows.append([btn(f"{emoji} {Cu.t3(name, lang)} ({num(lang, d)}/{num(lang, b - a + 1)})", f"c:jm:{mi}:0")])
    rows.append([btn(tr(lang, "cr_b_hub"), "c:hub")])
    _edit(uid, mid, tr(lang, "cr_jump_title"), kb(rows))

PAGE = 10
def jump_lessons(uid, mid, mi, page):
    lang = _ul(uid); r = get(uid); done = _done_ids(r) if r else set(); cur = r["cur"] if r else ""
    key, emoji, name = Cu.modules()[mi]; a, b = Cu.module_range(key); ids = list(range(a, b + 1))
    pages = max(1, (len(ids) + PAGE - 1) // PAGE); page = max(0, min(page, pages - 1)); part = ids[page * PAGE:(page + 1) * PAGE]
    rows = []
    for j in part:
        l = Cu.get(j); mark = "▶️" if l["id"] == cur else ("✅" if r and l["id"] in r["passed"] else ("⏭" if l["id"] in done else "▫️"))
        rows.append([btn(f"{mark} {num(lang, j + 1)}. {Cu.title(l, lang)}"[:60], f"c:jl:{j}")])
    nav = []
    if page > 0: nav.append(btn("⬅️", f"c:jm:{mi}:{page - 1}"))
    nav.append(btn(f"{num(lang, page + 1)}/{num(lang, pages)}", "noop"))
    if page < pages - 1: nav.append(btn("➡️", f"c:jm:{mi}:{page + 1}"))
    rows += [nav, [btn(tr(lang, "b_back"), "c:jm"), btn(tr(lang, "cr_b_hub"), "c:hub")]]
    _edit(uid, mid, tr(lang, "cr_jump_mod", mod=esc(Cu.module_name(key, lang))), kb(rows))

def jump_to(uid, mid, j):
    if Cu.get(j) is None: return
    ensure(uid); save(uid, cur=Cu.get(j)["id"], step="teach", page=0, plan=[], pos=0, ok=0, started_course=1)
    from ui import clear_sess; clear_sess(uid); teach(uid, mid, 0)

def skip(uid, mid=None):
    r = get(uid)
    if not r or not r["started_course"]: return path_menu(uid, mid)
    i = _cur_index(r); les = Cu.get(i); sk = list(dict.fromkeys(r["skipped"] + [les["id"]]))
    r2 = dict(r, skipped=sk); nxt = _next_after(r2, i)
    from ui import clear_sess; clear_sess(uid)
    if nxt is None:
        save(uid, skipped=sk, step="done", plan=[], pos=0, ok=0); return hub(uid, mid)
    save(uid, skipped=sk, cur=Cu.get(nxt)["id"], step="teach", page=0, plan=[], pos=0, ok=0)
    teach(uid, mid, 0)

def restart_confirm(uid, mid=None):
    lang = _ul(uid)
    _edit(uid, mid, tr(lang, "cr_restart_q"), kb([[btn(tr(lang, "cr_b_yes_restart"), "c:rs2")], [btn(tr(lang, "cr_b_hub"), "c:hub")]]))

def restart(uid, mid=None):
    ensure(uid); save(uid, cur=Cu.get(0)["id"], step="teach", page=0, plan=[], pos=0, ok=0, passed=[], skipped=[], scores={}, placed={}, started_course=1)
    from ui import clear_sess; clear_sess(uid)
    teach(uid, mid, 0)

# ---------------------------------------------------------------- onboarding + callbacks + reminder
def onboarding_choice(uid, mid, what):
    """ob:pl / ob:zero / ob:self during the first /start."""
    lang = _ul(uid)
    if what == "self": return self_menu(uid, mid, "ob")
    ensure(uid)
    logic.update_user(uid, onboarded=1, level=(0 if what == "zero" else 1))
    save(uid, pending="place" if what == "pl" else "zero")
    t = config.DEFAULT_REMIND_TIME
    rows = [[btn(f"⏰ {t}", f"ob:rm:{t}"), btn(tr(lang, "b_off"), "ob:rm:n")]]
    _edit(uid, mid, tr(lang, "cr_ob_ready") + "\n\n" + tr(lang, "pick_remind"), kb(rows))

def after_onboarding(uid, mid=None):
    """Called when the reminder question of onboarding is answered. Returns True if it launched placement/course."""
    r = get(uid)
    if not r or not r.get("pending"): return False
    what = r["pending"]; save(uid, pending="")
    if what == "place": start_placement(uid, None)
    else: start_zero(uid, None)
    return True

def callback(uid, mid, p):
    op = p[1] if len(p) > 1 else "hub"
    if op == "hub": return hub(uid, mid)
    if op == "go": return go(uid, mid)
    if op == "pl": return start_placement(uid, mid)
    if op == "zero": return start_zero(uid, mid)
    if op == "self": return self_menu(uid, mid)
    if op == "rec": return take_recommendation(uid, mid)
    if op == "pg": return teach(uid, mid, int(p[2]) if len(p) > 2 and p[2].isdigit() else 0)
    if op == "pr": return practice(uid, mid, fresh=True)
    if op == "sk": return skip(uid, mid)
    if op == "rs": return restart_confirm(uid, mid)
    if op == "rs2": return restart(uid, mid)
    if op == "jm":
        if len(p) > 2 and p[2].isdigit(): return jump_lessons(uid, mid, min(int(p[2]), len(Cu.modules()) - 1), int(p[3]) if len(p) > 3 and p[3].isdigit() else 0)
        return jump_modules(uid, mid)
    if op == "jl" and len(p) > 2 and p[2].isdigit(): return jump_to(uid, mid, int(p[2]))

def reminder_extra(uid, lang, tl=None):
    """-> (text line, button row) to append to the daily reminder, or None when there is no course to continue."""
    r = get(uid)
    if not r or not r["started_course"] or r["step"] == "done": return None
    les = Cu.get(_cur_index(r))
    pre = "" if Cu.cur_lang() == "zh" else langs.flag(Cu.cur_lang()) + " "
    return pre + tr(lang, "cr_remind_line", title=esc(Cu.title(les, lang))), [btn(tr(lang, "cr_b_go"), "c:go")]

def progress_line(uid, lang, tl=None):
    r = get(uid)
    if not r or not r["started_course"]: return ""
    return tr(lang, "cr_progress_line", pct=num(lang, _pct(r)), d=num(lang, len(_done_ids(r))), n=num(lang, Cu.total()))


# ---------------------------------------------------------------- per-language context
# Every public entry point runs inside the learner's active course language (or the language stored in the practice session, so an
# answer is credited to the course it belongs to even after /lang switched the active language).
def _with_lang(fn, from_sess=False):
    @functools.wraps(fn)
    def wrapper(uid, *a, **k):
        tl = k.pop("tl", None)
        if from_sess and a and isinstance(a[0], dict) and a[0].get("L"): tl = a[0]["L"]
        old = Cu.set_lang(tl or logic.target(uid))
        try: return fn(uid, *a, **k)
        finally: Cu.set_lang(old)
    return wrapper

for _n in ("get", "save", "ensure", "has_course", "path_menu", "self_menu", "hub", "start_zero", "teach", "practice", "go", "start_placement", "take_recommendation", "jump_modules", "jump_lessons",
           "jump_to", "skip", "restart_confirm", "restart", "onboarding_choice", "after_onboarding", "callback", "reminder_extra", "progress_line"):
    globals()[_n] = _with_lang(globals()[_n])
for _n in ("make_ex", "on_answer", "finish"):
    globals()[_n] = _with_lang(globals()[_n], True)
