#!/usr/bin/env python3
"""Septimus sign-up: who gets which story this week. Pure logic, no database, no network, no clock.

Think of it as a dealer at a card table. The deck is every story in Shas, in reading order. Each week the
dealer walks round the table and gives each person the next few cards that nobody holds, as many as fit in
the minutes that person promised. Cards not read within three weeks go back in the deck, to someone else.

Everything here takes plain data in and returns plain data out, so it can be tested with ordinary pytest.
The thin runner that talks to Firestore is scripts/septimus_weekly.py. Plan: docs/technical/septimus-signup-plan.md
sections 4 to 7.

Plain-English terms used below:
  - "round": one pass through the whole list. Round 1 = first time through Shas, round 2 = second, ...
  - "row" (assignment): one person's copy of one story. Fields: id, uid, storyId, round, week, doneAt, releasedAt.
  - "open" row: handed out, not marked learned, not released.
  - "covered": somebody holds an unreleased row for that story in that round, so nobody else is given it.
  - "week": campaign week. Week 1 is the seven days starting on the launch Monday.
"""
import json
from collections import namedtuple
from datetime import date
from pathlib import Path

import tractates as T  # the one table of tractates; its order is the order through Shas

# id, tractate (slug), words. Nothing else about a story is read here (plan section 7a): never `minutes`.
Story = namedtuple("Story", "id tractate words")

# A row is released on the run of week W + RELEASE_AFTER_WEEKS: it stays on the person's list for W, W+1, W+2.
RELEASE_AFTER_WEEKS = 3
# Pause someone whose released rows come from at least this many different weeks and who never learned anything.
PAUSE_AFTER_RELEASE_WEEKS = 2


class Plan:
    """What one weekly run decides. Row dicts are ready to write; the runner adds `assignedAt`."""

    def __init__(self):
        self.new_rows = []        # rows to create
        self.release_ids = []     # ids of open rows to mark released
        self.pause_uids = []      # people to pause
        self.unpause_uids = []    # people to un-pause
        self.eligible_uids = []   # who was served this week (for the counts)

    def __repr__(self):
        return (f"Plan(new_rows={len(self.new_rows)}, release_ids={len(self.release_ids)}, "
                f"pause={self.pause_uids}, unpause={self.unpause_uids})")


# ---------------------------------------------------------------- the list

def _daf_key(ref):
    """'Ketubot 8b' -> 17. Number first, then a before b (same rule as dafKey in site/app.js)."""
    import re
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


def stopped_release_ids(assignments, users):
    """Ids of open rows belonging to people who stopped or asked for deletion (released on every run)."""
    stopped = {u["uid"] for u in users if _is_stopped(u)}
    return sorted(r["id"] for r in assignments if _is_open(r) and r.get("uid") in stopped)


# ---------------------------------------------------------------- the weekly decision

def assign_week(story_order, assignments, users, week, wpm, last_week, max_minutes=120):
    """Decide this week's hand-out. Returns a Plan. Does not change its inputs.

    Order of the rules (plan section 6): nothing outside the campaign; release; pause/unpause; work out what is
    covered; hand out in sign-up order."""
    plan = Plan()
    if week < 1 or week > last_week:
        return plan

    rows = [dict(r) for r in assignments]          # local copies: releasing below marks these, not the caller's
    people = [dict(u) for u in users]
    stopped = {u["uid"] for u in people if _is_stopped(u)}

    # 2. Release: stayed on the list for weeks W, W+1, W+2; or the person stopped / asked for deletion.
    for r in rows:
        if _is_open(r) and (week >= r["week"] + RELEASE_AFTER_WEEKS or r.get("uid") in stopped):
            r["releasedAt"] = "released-this-run"
            plan.release_ids.append(r["id"])
    plan.release_ids.sort()

    # 3. Pause the quiet; un-pause anyone who has learned something since they were paused.
    paused = {u["uid"] for u in people if u.get("pausedAt")}
    for u in sorted(people, key=lambda p: p["uid"]):
        uid = u["uid"]
        mine = [r for r in rows if r.get("uid") == uid]
        if u.get("pausedAt"):
            if any(r.get("doneAt") and r["doneAt"] > u["pausedAt"] for r in mine):
                plan.unpause_uids.append(uid)
                paused.discard(uid)
        elif not _is_stopped(u):
            never_learned = not any(r.get("doneAt") for r in mine)
            lapsed_weeks = {r["week"] for r in mine if r.get("releasedAt")}
            if never_learned and len(lapsed_weeks) >= PAUSE_AFTER_RELEASE_WEEKS:
                plan.pause_uids.append(uid)
                paused.add(uid)

    # 4. Covered: an unreleased row in that round. Rows for stories no longer on the list never count.
    on_list = {s.id for s in story_order}
    covered = {(r["round"], r["storyId"]) for r in rows if not r.get("releasedAt") and r["storyId"] in on_list}
    # Who let which story lapse (released), so it can go to someone else.
    lapsed = {(r.get("uid"), r["round"], r["storyId"]) for r in rows if r.get("releasedAt")}
    held_this_week = {r["id"] for r in rows if r["week"] == week}
    served_this_week = {r.get("uid") for r in rows if r["week"] == week}

    # 5. Hand out, in sign-up order. Paused, stopped and delete-requested people get nothing.
    eligible = sorted((u for u in people if u.get("minutesPerWeek", 0) > 0 and u["uid"] not in paused
                       and not u.get("deleteRequested")),
                      key=lambda p: (p["createdAt"], p["uid"]))
    plan.eligible_uids = [u["uid"] for u in eligible]
    only_one_person = len(eligible) == 1
    words_of = {s.id: s.words for s in story_order}

    for u in eligible:
        uid = u["uid"]
        if uid in served_this_week:      # already served this week (a re-run, or a run that died halfway)
            continue
        open_minutes = sum(reading_minutes(words_of.get(r["storyId"], 0), wpm)
                           for r in rows if r.get("uid") == uid and _is_open(r))
        budget = min(u["minutesPerWeek"], max_minutes) - open_minutes
        if budget <= 0 or not story_order:
            continue
        total, got, taken = 0.0, 0, set()
        rnd, stop = 1, False
        while not stop:
            for s in story_order:
                if (rnd, s.id) in covered or s.id in taken:
                    continue
                if not only_one_person and (uid, rnd, s.id) in lapsed:
                    continue                      # they let this one lapse: it goes to someone else
                row_id = f"{week}_{uid}_{s.id}"
                if row_id in held_this_week:
                    continue
                mins = reading_minutes(s.words, wpm)
                if got > 0 and total + mins > budget:
                    stop = True                   # first story that does not fit: stop, never skip ahead
                    break
                total += mins
                got += 1
                taken.add(s.id)
                covered.add((rnd, s.id))
                plan.new_rows.append({"id": row_id, "uid": uid, "storyId": s.id, "round": rnd, "week": week,
                                      "doneAt": None, "releasedAt": None})
            if not stop:
                if len(taken) >= len(story_order):
                    break                         # this person already has every story on the list this week
                rnd += 1                          # nothing uncovered left in this round: continue in the next
    return plan


# ---------------------------------------------------------------- the public totals

def summarise(story_order, assignments, users, list_version):
    """The numbers for progress/summary (public). Always measured against the current list."""
    on_list = {s.id: s for s in story_order}
    done_by_round = {}
    max_round = 0
    for r in assignments:
        max_round = max(max_round, r["round"])
        if r.get("doneAt") and r["storyId"] in on_list:
            done_by_round.setdefault(r["round"], set()).add(r["storyId"])
    completed = 0
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
