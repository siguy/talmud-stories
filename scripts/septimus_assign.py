#!/usr/bin/env python3
"""Septimus sign-up: who gets which story this week. Pure logic, no database, no network, no clock.

Think of it as a dealer at a card table. The deck is every story in Shas, in reading order. Each week the
dealer walks round the table and gives each person the next few cards that nobody holds, as many as fit in
the minutes that person promised. Cards not read within three weeks go back in the deck, to someone else.

Everything here takes plain data in and returns plain data out, so it can be tested with ordinary pytest.
The thin runner that talks to Firestore is scripts/septimus_weekly.py. Plan: docs/technical/septimus-signup-plan.md
sections 4 to 7.

The week is done in two steps so the runner can release rows for real before dealing (a story marked learned at
the last second must not be dealt to someone else): `due_releases` says which rows go back in the deck, then
`hand_out` deals. `assign_week` runs both on copies, for simulations and tests.

Plain-English terms used below:
  - "round": one pass through the whole list. Round 1 = first time through Shas, round 2 = second, ...
  - "row" (assignment): one person's copy of one story. Fields: id, uid, storyId, round, week, doneAt, releasedAt.
  - "open" row: handed out, not marked learned, not released.
  - "covered": somebody holds an unreleased row for that story in that round, so nobody else is given it.
  - "week": campaign week. Week 1 is the seven days starting on the launch Sunday.
  - "lapsed": a row nobody marked learned in three weeks, so it went back in the deck.
  - everLearned / lapses: two fields on the person's record that only the script writes. everLearned = they have
    marked at least one story learned, ever. lapses = the weeks (assignment weeks) of rows that lapsed on them.
"""
import json
import re
from collections import Counter, namedtuple
from pathlib import Path

import tractates as T  # the one table of tractates; its order is the order through Shas

# id, tractate (slug), words. Nothing else about a story is read here (plan section 7a): never `minutes`.
Story = namedtuple("Story", "id tractate words")

# A row is released on the run of week W + RELEASE_AFTER_WEEKS: it stays on the person's list for W, W+1, W+2.
RELEASE_AFTER_WEEKS = 3
# Pause someone who never learned anything and whose lapsed rows come from weeks at least this far apart
# (two separate lapse rounds, not two rows of one week).
PAUSE_LAPSE_SPAN_WEEKS = 3


class Plan:
    """What one weekly run decides. Row dicts are ready to write; the runner adds `assignedAt`."""

    def __init__(self):
        self.new_rows = []        # rows to create
        self.release_ids = []     # ids released first (filled by assign_week only; the runner does its own)
        self.pause_uids = []      # people to pause
        self.eligible_uids = []   # who was served this week (for the counts)

    def __repr__(self):
        return (f"Plan(new_rows={len(self.new_rows)}, release_ids={len(self.release_ids)}, "
                f"pause={self.pause_uids})")


# ---------------------------------------------------------------- the list

def _daf_key(ref):
    """'Ketubot 8b' -> 17. Number first, then a before b (same rule as dafKey in site/app.js)."""
    m = re.search(r"(\d+)([ab])", ref)
    return int(m.group(1)) * 2 + (1 if m.group(2) == "b" else 0) if m else 0


def load_story_order(data_dir):
    """Every story in hand-out order: tractates in the order of TABLE (Berakhot first, NOT index.json's order),
    then daf, then segment. Only stories whose tier is "story" or absent (absent means story)."""
    data_dir = Path(data_dir)
    index = json.loads((data_dir / "index.json").read_text())
    present = {t["tractate"] for t in index.get("tractates", [])}
    order = []
    for english, _hebrew in T.TABLE:
        slug = T.slug_of(english)
        path = data_dir / f"{slug}.json"
        if slug not in present or not path.exists():
            continue
        stories = [s for s in json.loads(path.read_text()).get("stories", []) if s.get("tier", "story") == "story"]
        stories.sort(key=lambda s: (_daf_key(s["ref"]), s["start_segment"], s["id"]))
        order.extend(Story(s["id"], slug, s["words"]) for s in stories)
    return order


def load_list_version(data_dir):
    """`list_version` from index.json, or None until the data carries one (plan step s)."""
    return json.loads((Path(data_dir) / "index.json").read_text()).get("list_version")


# ---------------------------------------------------------------- small helpers

def reading_minutes(words, wpm):
    """Minutes to read `words` at `wpm` words a minute. Not rounded."""
    return words / wpm


def is_longer_than_usual(words, minutes_per_week, wpm):
    """True when one story takes longer than the person's whole weekly time. Display only, never stored."""
    return reading_minutes(words, wpm) > minutes_per_week


def campaign_week(today, launch_date):
    """Week 1 = the seven days starting on launch_date. 0 or negative before launch.
    `today` is a date (the caller converts "now" to US Eastern first)."""
    return (today - launch_date).days // 7 + 1


def _is_open(row):
    return not row.get("doneAt") and not row.get("releasedAt")


def _is_stopped(user):
    """Stopped = minutesPerWeek 0, or asked for deletion. Their open rows are released at once."""
    return user.get("minutesPerWeek") == 0 or bool(user.get("deleteRequested"))


# ---------------------------------------------------------------- the person's bookkeeping fields

def ever_learned_uids(assignments):
    """Uids with at least one row marked learned among the rows given."""
    return {r.get("uid") for r in assignments if r.get("doneAt") and r.get("uid")}


def add_lapse(user, week):
    """Record that a row from `week` lapsed on this person. Changes the dict; True if anything changed.
    A paused person's leftover rows lapsing is not recorded: after they resume they start counting afresh."""
    if user.get("pausedAt"):
        return False
    weeks = sorted({int(w) for w in user.get("lapses") or []} | {int(week)})
    if weeks == list(user.get("lapses") or []):
        return False
    user["lapses"] = weeks
    return True


def should_pause(user):
    """Never learned anything, and lapsed rows from two different lapse rounds (weeks at least 3 apart).
    Releases for stopping never count (they are not recorded in `lapses`). No automatic un-pause: the person
    resumes by clearing pausedAt themselves, and the script clears `lapses` when it pauses, so they start fresh."""
    if user.get("pausedAt") or _is_stopped(user) or user.get("everLearned"):
        return False
    weeks = sorted({int(w) for w in user.get("lapses") or []})
    return len(weeks) >= 2 and weeks[-1] - weeks[0] >= PAUSE_LAPSE_SPAN_WEEKS


# ---------------------------------------------------------------- step 1: what goes back in the deck

def due_releases(assignments, users, week):
    """Open rows to release this run, as (row_id, reason), sorted by id.
    reason "lapsed": assigned in week W and now week >= W+3 (pass week=None to skip this kind).
    reason "stopped": the person stopped (minutesPerWeek 0) or asked for deletion; always, on every run."""
    stopped = {u["uid"] for u in users if _is_stopped(u)}
    out = []
    for r in assignments:
        if not _is_open(r):
            continue
        if r.get("uid") in stopped:
            out.append((r["id"], "stopped"))
        elif week is not None and week >= r["week"] + RELEASE_AFTER_WEEKS:
            out.append((r["id"], "lapsed"))
    return sorted(out)


# ---------------------------------------------------------------- step 2: the deal

def hand_out(story_order, assignments, users, week, wpm, last_week, just_lapsed=(), max_minutes=120,
             base_round=1):
    """Decide this week's hand-out. Returns a Plan (new_rows, pause_uids, eligible_uids). Changes nothing.

    `assignments` already reflect this run's releases. `just_lapsed` = {(uid, storyId, round)} released as "lapsed"
    in THIS run: that person is not given that story again this run, everybody else may be.
    `base_round`: every round below it is complete (the runner does not read them), so dealing starts there.

    Rules: never a story the person already holds open (any round); at-least-one story only when they hold
    nothing open at all; stop at the first story that does not fit (never skip ahead); anyone who already has a
    row for this week gets nothing more; paused, stopped and delete-requested people get nothing."""
    plan = Plan()
    if week < 1 or week > last_week or not story_order:
        return plan
    rows = list(assignments)
    just_lapsed = set(just_lapsed)

    # Pause the quiet (see should_pause). Rows in `assignments` also count as proof of having learned.
    learned = ever_learned_uids(rows)
    paused = {u["uid"] for u in users if u.get("pausedAt")}
    for u in sorted(users, key=lambda p: p["uid"]):
        if should_pause({**u, "everLearned": bool(u.get("everLearned")) or u["uid"] in learned}):
            plan.pause_uids.append(u["uid"])
            paused.add(u["uid"])

    # Covered: an unreleased row in that round. Rows for stories no longer on the list never count.
    on_list = {s.id for s in story_order}
    n = len(on_list)
    words_of = {s.id: s.words for s in story_order}
    covered = {(r["round"], r["storyId"]) for r in rows if not r.get("releasedAt") and r["storyId"] in on_list}
    covered_in = Counter(rnd for rnd, _ in covered)
    max_round = max([base_round] + [rnd for rnd, _ in covered])
    first_free = base_round
    open_of = {}
    for r in rows:
        if _is_open(r):
            open_of.setdefault(r.get("uid"), []).append(r)
    served_this_week = {r.get("uid") for r in rows if r["week"] == week}

    eligible = sorted((u for u in users if u.get("minutesPerWeek", 0) > 0 and u["uid"] not in paused
                       and not u.get("deleteRequested")),
                      key=lambda p: (p["createdAt"], p["uid"]))
    plan.eligible_uids = [u["uid"] for u in eligible]

    for u in eligible:
        uid = u["uid"]
        if uid in served_this_week:      # already served this week (a re-run, or a run that died halfway)
            continue
        mine = open_of.get(uid, [])
        holds_nothing = not mine
        budget = min(u["minutesPerWeek"], max_minutes) - sum(
            reading_minutes(words_of.get(r["storyId"], 0), wpm) for r in mine)
        if not holds_nothing and budget <= 0:
            continue
        held_open = {r["storyId"] for r in mine}                   # never hand these out again, in any round
        while first_free in covered_in and covered_in[first_free] >= n:
            first_free += 1
        rnd, ceiling = first_free, max(first_free, max_round) + 3
        total, got, taken, stop = 0.0, 0, set(), False
        while not stop:
            if rnd > ceiling:
                raise RuntimeError(f"hand_out: round {rnd} is past the safety ceiling {ceiling}; a rule is looping")
            for s in story_order:
                if (rnd, s.id) in covered or s.id in taken or s.id in held_open or (uid, s.id, rnd) in just_lapsed:
                    continue
                mins = reading_minutes(s.words, wpm)
                if total + mins > budget and not (holds_nothing and got == 0):
                    stop = True               # first story that does not fit: stop, never skip ahead
                    break
                total += mins
                got += 1
                taken.add(s.id)
                covered.add((rnd, s.id))
                covered_in[rnd] += 1
                max_round = max(max_round, rnd)
                plan.new_rows.append({"id": f"{week}_{uid}_{s.id}", "uid": uid, "storyId": s.id, "round": rnd,
                                      "week": week, "doneAt": None, "releasedAt": None})
            if not stop:
                if on_list <= (taken | held_open):
                    break                     # nothing left that this person could be given
                rnd += 1                      # nothing uncovered left in this round: continue in the next
    return plan


# ---------------------------------------------------------------- both steps on copies (simulations, tests)

def assign_week(story_order, assignments, users, week, wpm, last_week, max_minutes=120, base_round=1):
    """due_releases + hand_out in one call, on copies. Returns a Plan with release_ids filled in.
    Does not change its inputs."""
    if week < 1 or week > last_week:
        return Plan()
    rows = [dict(r) for r in assignments]
    people = [dict(u, lapses=list(u.get("lapses") or [])) for u in users]
    by_id = {r["id"]: r for r in rows}
    by_uid = {u["uid"]: u for u in people}
    due = due_releases(rows, people, week)
    just_lapsed = set()
    for rid, why in due:
        r = by_id[rid]
        r["releasedAt"] = "released-this-run"
        if why == "lapsed":
            just_lapsed.add((r["uid"], r["storyId"], r["round"]))
            if r["uid"] in by_uid:
                add_lapse(by_uid[r["uid"]], r["week"])
    learned = ever_learned_uids(rows)
    for u in people:
        u["everLearned"] = bool(u.get("everLearned")) or u["uid"] in learned
    plan = hand_out(story_order, rows, people, week, wpm, last_week, just_lapsed, max_minutes, base_round)
    plan.release_ids = [rid for rid, _ in due]
    return plan


# ---------------------------------------------------------------- the public totals

def summarise(story_order, assignments, users, list_version, base_round=1):
    """The numbers for progress/summary (public). Always measured against the current list.
    `assignments` may hold only rows with round >= base_round (the caller promises every lower round is
    complete); roundsCompleted then counts from base_round - 1."""
    on_list = {s.id: s for s in story_order}
    done_by_round = {}
    max_round = 0
    for r in assignments:
        max_round = max(max_round, r["round"])
        if r.get("doneAt") and r["storyId"] in on_list:
            done_by_round.setdefault(r["round"], set()).add(r["storyId"])
    completed = base_round - 1
    while on_list and completed < max_round and len(done_by_round.get(completed + 1, ())) == len(on_list):
        completed += 1
    current = completed + 1
    done_now = done_by_round.get(current, set())
    by_tractate = {}
    for sid in done_now:
        t = on_list[sid].tractate
        by_tractate[t] = by_tractate.get(t, 0) + 1
    return {
        "learned": len(done_now),
        "byTractate": by_tractate,
        "round": current,
        "roundsCompleted": completed,
        "openInRound": len(on_list) - len(done_now),
        "joined": sum(1 for u in users if not u.get("deleteRequested")),
        "listVersion": list_version,
    }
