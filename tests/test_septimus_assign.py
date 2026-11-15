"""Tests for scripts/septimus_assign.py (the weekly hand-out logic). Plain pytest: no emulator, no network.

Run on the tiny fixture in tests/fixtures/septimus_stories/ (18 stories: 6 each in Berakhot, Shabbat, Ketubot;
one Ketubot story is 2700 words). Never reads the live site/data/.
"""
import copy
import json
from collections import Counter
import shutil
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import septimus_assign as A  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "septimus_stories"
WPM = 75
LAST = 40


@pytest.fixture(scope="module")
def order():
    return A.load_story_order(FIX)


def person(uid, minutes, created, **kw):
    return {"uid": uid, "createdAt": created, "minutesPerWeek": minutes, "deleteRequested": False,
            "pausedAt": None, **kw}


def row(uid, story, week, round_=1, done=None, released=None):
    return {"id": f"{week}_{uid}_{story}", "uid": uid, "storyId": story, "round": round_, "week": week,
            "doneAt": done, "releasedAt": released}


def step(order, rows, users, week, last=LAST):
    """One weekly run applied to shared state, the way the runner does it: release (recording lapses on the
    person), note who has ever learned, hand out, pause. Mutates `rows` and `users`. Returns the Plan."""
    by_id = {r["id"]: r for r in rows}
    by_uid = {u["uid"]: u for u in users}
    just_lapsed = set()
    for rid, why in A.due_releases(rows, users, week):
        r = by_id[rid]
        r["releasedAt"] = "x"
        if why == "lapsed":
            just_lapsed.add((r["uid"], r["storyId"], r["round"]))
            A.add_lapse(by_uid[r["uid"]], r["week"])
    for uid in A.ever_learned_uids(rows):
        by_uid[uid]["everLearned"] = True
    plan = A.hand_out(order, rows, users, week, WPM, last, just_lapsed)
    for uid in plan.pause_uids:
        by_uid[uid]["pausedAt"] = week
        by_uid[uid]["lapses"] = []                      # the runner clears them when it pauses
    rows.extend(plan.new_rows)
    return plan


def play(order, users, weeks, rows=None, mark_done=None):
    """Simulate weekly runs: feed each week's new rows (and releases) back in. Returns the rows."""
    rows = list(rows or [])
    for w in weeks:
        step(order, rows, users, w)
        if mark_done:
            mark_done(w, rows)
    return rows


def open_minutes(order, rows, uid):
    words = {s.id: s.words for s in order}
    return sum(words[r["storyId"]] / WPM for r in rows if r["uid"] == uid and not r["doneAt"] and not r["releasedAt"])


def ids_of(rows, uid):
    return [r["storyId"] for r in rows if r["uid"] == uid]


# ---------------------------------------------------------------- the list

def test_order_starts_at_berakhot_and_is_daf_then_segment(order):
    assert [s.tractate for s in order[:1]] == ["berakhot"]
    assert [s.tractate for s in order] == ["berakhot"] * 6 + ["shabbat"] * 6 + ["ketubot"] * 6
    index = json.loads((FIX / "index.json").read_text())
    assert index["tractates"][0]["tractate"] == "ketubot"      # the fixture lists Ketubot first on purpose
    berakhot = [s.id for s in order if s.tractate == "berakhot"]
    assert berakhot[:3] == ["berakhot-3a-11-13", berakhot[1], berakhot[2]]
    assert order[0].words == 456


def test_daf_order_puts_a_before_b_and_numbers_numerically(tmp_path):
    d = tmp_path
    (d / "index.json").write_text(json.dumps({"tractates": [{"tractate": "berakhot"}]}))
    st = [("x10a", "Berakhot 10a", 1), ("x9b", "Berakhot 9b", 1), ("x9a", "Berakhot 9a", 5), ("x9a0", "Berakhot 9a", 2)]
    (d / "berakhot.json").write_text(json.dumps({"stories": [
        {"id": i, "tractate": "berakhot", "ref": r, "refs": [r], "start_segment": s, "words": 10} for i, r, s in st]}))
    assert [s.id for s in A.load_story_order(d)] == ["x9a0", "x9a", "x9b", "x10a"]


def test_tier_story_or_absent_is_in_borderline_is_out(tmp_path):
    shutil.copytree(FIX, tmp_path / "d")
    p = tmp_path / "d" / "berakhot.json"
    data = json.loads(p.read_text())
    data["stories"][0].pop("tier")                       # no tier: counts as a story
    data["stories"][1]["tier"] = "borderline"            # not a story for the sign-up
    p.write_text(json.dumps(data))
    got = [s.id for s in A.load_story_order(tmp_path / "d")]
    assert data["stories"][0]["id"] in got and data["stories"][1]["id"] not in got
    assert len(got) == 17


def test_minutes_field_is_never_read(order):
    assert order[0]._fields == ("id", "tractate", "words")


# ---------------------------------------------------------------- small functions

def test_reading_minutes_and_longer_than_usual(order):
    assert A.reading_minutes(750, 75) == 10
    long = next(s for s in order if s.words == 2700)
    assert A.is_longer_than_usual(long.words, 5, WPM)
    assert not A.is_longer_than_usual(300, 10, WPM)


def test_campaign_week_around_launch_and_new_year():
    launch = date(2026, 12, 6)                           # a Sunday
    assert A.campaign_week(date(2026, 12, 5), launch) == 0
    assert A.campaign_week(date(2026, 11, 29), launch) == 0        # the whole week before launch is 0
    assert A.campaign_week(date(2026, 11, 28), launch) == -1
    assert A.campaign_week(date(2026, 12, 6), launch) == 1
    assert A.campaign_week(date(2026, 12, 12), launch) == 1
    assert A.campaign_week(date(2026, 12, 13), launch) == 2
    assert A.campaign_week(date(2027, 1, 3), launch) == 5          # across New Year
    assert A.campaign_week(date(2027, 9, 10), launch) == 40        # the yahrzeit week


# ---------------------------------------------------------------- assign_week

def test_nothing_before_launch_or_after_last_week(order):
    users = [person("a", 30, 1)]
    for w in (0, -3, LAST + 1):
        plan = A.assign_week(order, [], users, w, WPM, LAST)
        assert (plan.new_rows, plan.release_ids, plan.pause_uids) == ([], [], [])
    assert A.assign_week(order, [], users, LAST, WPM, LAST).new_rows       # the last week itself still hands out
    assert A.hand_out(order, [], users, LAST, WPM, LAST).new_rows          # exactly last_week hands out ...
    assert A.hand_out(order, [], users, LAST + 1, WPM, LAST).new_rows == []    # ... last_week + 1 does not


def test_three_people_four_weeks_consecutive_within_budget(order):
    users = [person("a", 10, 1), person("b", 10, 2), person("c", 10, 3)]
    # everyone marks everything learned at once, so each week they have a full budget again
    rows = play(order, users, [1, 2, 3, 4],
                mark_done=lambda w, rows: [r.update(doneAt=w) for r in rows if not r["doneAt"]])
    ids = [s.id for s in order]
    by_round = {}
    for r in sorted(rows, key=lambda r: (r["week"], r["uid"])):
        by_round.setdefault(r["round"], []).append(r["storyId"])
    assert len(by_round) >= 2                                        # the tiny list wraps into round 2
    for round_no, got in by_round.items():                           # consecutive, nothing skipped or repeated
        assert got == ids[:len(got)], round_no
    for w in (1, 2, 3, 4):
        for uid in "abc":
            mins = sum(A.reading_minutes(next(s.words for s in order if s.id == r["storyId"]), WPM)
                       for r in rows if r["uid"] == uid and r["week"] == w)
            assert 0 < mins <= 10 or len([r for r in rows if r["uid"] == uid and r["week"] == w]) == 1
    # the first week is exactly the first stories, in sign-up order
    assert [r["uid"] for r in rows if r["week"] == 1][0] == "a"
    assert [r["storyId"] for r in rows if r["week"] == 1 and r["uid"] == "a"][0] == order[0].id


def test_unread_story_stays_through_w2_released_at_w3_goes_to_someone_else(order):
    users = [person("a", 6, 1), person("b", 6, 2)]       # 6 min: one 456-word story (6.08 min) uses the whole week
    rows = play(order, users, [1])
    a1 = [r for r in rows if r["uid"] == "a"]
    assert a1 and order[0].id == a1[0]["storyId"]
    # weeks 2 and 3 (W+1, W+2): nothing is released; a is full of open stories so gets nothing
    for w in (2, 3):
        plan = A.assign_week(order, rows, users, w, WPM, LAST)
        assert a1[0]["id"] not in plan.release_ids
        assert not [r for r in plan.new_rows if r["uid"] == "a"]
    plan = A.assign_week(order, rows, users, 4, WPM, LAST)           # the W+3 run
    assert a1[0]["id"] in plan.release_ids
    got_by_b = [r["storyId"] for r in plan.new_rows if r["uid"] == "b"]
    got_by_a = [r["storyId"] for r in plan.new_rows if r["uid"] == "a"]
    assert order[0].id in got_by_b                                   # released story goes to someone else first
    assert order[0].id not in got_by_a                               # and not back to the person who let it lapse


def test_done_story_is_never_released(order):
    users = [person("a", 8, 1)]
    rows = [row("a", order[0].id, 1, done=5)]
    plan = A.assign_week(order, rows, users, 9, WPM, LAST)
    assert plan.release_ids == []


def test_stopped_person_open_rows_released_at_once_and_nothing_given(order):
    users = [person("a", 0, 1), person("b", 10, 2)]
    rows = [row("a", order[0].id, 3), row("a", order[1].id, 3, done=4)]
    plan = A.assign_week(order, rows, users, 3, WPM, LAST)
    assert plan.release_ids == [f"3_a_{order[0].id}"]
    assert not [r for r in plan.new_rows if r["uid"] == "a"]
    assert order[0].id in [r["storyId"] for r in plan.new_rows]       # released at once, so b may have it
    assert A.due_releases(rows, users, None) == [(f"3_a_{order[0].id}", "stopped")]   # week=None: stopped only


def test_budget_subtracts_open_stories(order):
    users = [person("a", 10, 1)]
    open_row = row("a", order[0].id, 1)                               # 456 words = 6.08 min still open
    plan = A.assign_week(order, [open_row], users, 2, WPM, LAST)
    # 10 - 6.08 = 3.92 minutes left: the 280-word story (3.73) fits, the next (1.27) would not
    assert [r["storyId"] for r in plan.new_rows] == [order[1].id]
    # a person whose open stories already use the whole budget gets nothing
    full = [row("a", order[0].id, 1), row("a", order[1].id, 1)]       # 6.08 + 3.73 = 9.8 of 10... then add more
    users2 = [person("a", 9, 1)]
    assert A.assign_week(order, full, users2, 2, WPM, LAST).new_rows == []


def test_long_story_handed_out_to_5_minute_person_then_nothing_more(order):
    long = next(s for s in order if s.words == 2700)
    users = [person("a", 5, 1)]
    # walk the list until the long story is next: mark everything before it done
    before = [s for s in order[:order.index(long)]]
    rows = [row("a", s.id, 1, done=1) for s in before]
    plan = A.assign_week(order, rows, users, 2, WPM, LAST)
    assert [r["storyId"] for r in plan.new_rows] == [long.id]         # exactly the long story
    assert A.is_longer_than_usual(long.words, 5, WPM)
    rows2 = rows + plan.new_rows
    assert A.assign_week(order, rows2, users, 3, WPM, LAST).new_rows == []     # nothing until done or released
    rows2[-1]["doneAt"] = 3
    assert A.assign_week(order, rows2, users, 4, WPM, LAST).new_rows           # done: they get more


def test_next_person_continues_in_round_2_when_round_1_is_covered(order):
    users = [person("a", 120, 1), person("b", 10, 2)]
    plan = A.assign_week(order, [], users, 1, WPM, LAST)
    a = [r for r in plan.new_rows if r["uid"] == "a"]
    b = [r for r in plan.new_rows if r["uid"] == "b"]
    assert len(a) == 18 and {r["round"] for r in a} == {1}
    assert b and all(r["round"] == 2 for r in b) and b[0]["storyId"] == order[0].id


def test_round_two_when_one_person_finishes_the_whole_list(order):
    # one person, a huge weekly budget (capped at 120 min = 9000 words): the whole list is ~7800 words
    total_min = sum(s.words for s in order) / WPM
    assert total_min < 120
    users = [person("a", 120, 1)]
    plan = A.assign_week(order, [], users, 1, WPM, LAST)
    rounds = [(r["round"], r["storyId"]) for r in plan.new_rows]
    assert rounds[:18] == [(1, s.id) for s in order]                 # all of round 1 first
    # never the same story twice in one week for one person: ids stay unique
    assert len({r["id"] for r in plan.new_rows}) == len(plan.new_rows)
    assert len(plan.new_rows) == 18                                   # so the week stops at the end of the list


def test_second_person_gets_round_2_when_round_1_is_fully_covered(order):
    big = person("a", 120, 1)
    small = person("b", 10, 2)
    plan = A.assign_week(order, [], [big, small], 1, WPM, LAST)
    assert {r["round"] for r in plan.new_rows if r["uid"] == "a"} == {1}
    b_rows = [r for r in plan.new_rows if r["uid"] == "b"]
    assert b_rows and {r["round"] for r in b_rows} == {2}
    assert b_rows[0]["storyId"] == order[0].id


def test_lapsed_story_goes_to_someone_else_but_only_in_the_run_it_lapsed(order):
    lapsed = row("a", order[0].id, 1, released="x")
    two = [person("a", 6, 1), person("b", 6, 2)]
    # a let it lapse in THIS run: a skips it, b gets it
    plan = A.hand_out(order, [lapsed], two, 5, WPM, LAST, just_lapsed={("a", order[0].id, 1)})
    assert order[0].id not in [r["storyId"] for r in plan.new_rows if r["uid"] == "a"]
    assert order[0].id in [r["storyId"] for r in plan.new_rows if r["uid"] == "b"]
    # ... the only person: nobody else to give it to, so it is offered again in a later run (no exception needed)
    later = A.hand_out(order, [lapsed], [person("a", 6, 1)], 6, WPM, LAST)
    assert [r["storyId"] for r in later.new_rows][0] == order[0].id
    # even in the same run, with a single person it simply moves on to the next story
    same = A.hand_out(order, [lapsed], [person("a", 6, 1)], 5, WPM, LAST, just_lapsed={("a", order[0].id, 1)})
    assert [r["storyId"] for r in same.new_rows][0] == order[1].id


def test_due_releases_lapsed_stopped_and_reasons(order):
    users = [person("a", 10, 1), person("b", 0, 2), person("c", 10, 3, deleteRequested=True)]
    rows = [row("a", order[0].id, 1), row("a", order[1].id, 2), row("a", order[2].id, 1, done=3),
            row("b", order[3].id, 3), row("c", order[4].id, 4), row("a", order[5].id, 1, released="x")]
    got = A.due_releases(rows, users, 4)
    assert got == sorted([(f"1_a_{order[0].id}", "lapsed"), (f"3_b_{order[3].id}", "stopped"),
                          (f"4_c_{order[4].id}", "stopped")])        # week 2 row is not due until week 5
    assert (f"2_a_{order[1].id}", "lapsed") in A.due_releases(rows, users, 5)
    assert not [x for x in A.due_releases(rows, users, 3) if x[1] == "lapsed"]     # W+3 exactly: 1+3 = 4, not 3


def test_never_hands_a_person_a_story_they_hold_open(order):
    # the reviewer's case: one person with 120 minutes and the whole list in 104
    users = [person("a", 120, 1)]
    rows = []
    step(order, rows, users, 1)
    assert len(rows) == 18
    plan = step(order, rows, users, 2)
    assert plan.new_rows == []                              # budget left, but everything on the list is theirs
    # two people: nobody is ever given a story they already hold, in any round, in any week
    users = [person("a", 120, 1), person("b", 120, 2)]
    rows = []
    for w in range(1, 12):
        step(order, rows, users, w)
        held = Counter((r["uid"], r["storyId"]) for r in rows if not r["doneAt"] and not r["releasedAt"])
        assert max(held.values(), default=1) == 1, w                    # never the same story open twice for one person


def test_story_lapsed_by_a_then_by_b_is_offered_again_and_the_round_completes(order):
    x = order[0].id
    users = [person("a", 5, 1), person("b", 5, 2)]
    rows, offered_x = [], []
    for w in range(1, 25):
        step(order, rows, users, w)
        offered_x += [r["uid"] for r in rows if r["storyId"] == x and r["week"] == w]
        for r in rows:                                       # both read everything except X
            if not r["doneAt"] and not r["releasedAt"] and r["storyId"] != x:
                r["doneAt"] = w
    assert "a" in offered_x and "b" in offered_x and len(offered_x) >= 4     # X keeps coming back round
    assert A.summarise(order, rows, users, "v")["roundsCompleted"] == 0       # X is the only story never read ...
    x_rows = [r for r in rows if r["storyId"] == x]
    for r in x_rows:                                         # ... and when someone finally reads it, round 1 closes
        if not r["releasedAt"] and not r["doneAt"] and r["round"] == 1:
            r["doneAt"] = 99
    assert A.summarise(order, rows, users, "v")["roundsCompleted"] >= 1


def test_never_reading_person_is_paused_only_after_two_lapse_rounds_and_never_piles_up(order):
    users = [person("a", 30, 1)]
    rows, paused_at = [], None
    for w in range(1, 10):
        plan = step(order, rows, users, w)
        if plan.pause_uids and paused_at is None:
            paused_at = w
        assert open_minutes(order, rows, "a") <= 30 + 456 / WPM + 1e-9, w         # budget, at most one extra story
        if w in (2, 3):
            assert plan.new_rows == [], w                    # holding a full budget: nothing more
    assert paused_at == 7                                       # weeks 1 and 4 lapse (at the week-4 and week-7 runs)
    assert users[0]["pausedAt"] == 7 and users[0]["lapses"] == []
    assert not [r for r in rows if r["week"] >= 7]              # paused: nothing handed out from week 7


def test_person_who_stops_and_restarts_is_not_paused(order):
    users = [person("a", 30, 1)]
    rows = []
    step(order, rows, users, 1)                                 # week-1 rows, never read
    users[0]["minutesPerWeek"] = 0
    step(order, rows, users, 4)                                 # stopped: due at W+3 too, but released as "stopped"
    assert all(r["releasedAt"] for r in rows) and not users[0].get("lapses")
    users[0]["minutesPerWeek"] = 30
    for w in range(5, 9):                                       # restarts; their week-5 rows lapse at week 8
        assert step(order, rows, users, w).pause_uids == [], w
    assert users[0]["lapses"] == [5] and users[0].get("pausedAt") is None
    # had the stop counted as a lapse, weeks 1 and 5 would have paused them (span 4)


def test_pause_rule_details():
    base = person("a", 10, 1)
    assert not A.should_pause({**base, "lapses": [1]})
    assert not A.should_pause({**base, "lapses": [1, 3]})                    # two weeks but under 3 apart
    assert A.should_pause({**base, "lapses": [1, 4]})
    assert A.should_pause({**base, "lapses": [4, 1, 2]})
    assert not A.should_pause({**base, "lapses": [1, 4], "everLearned": True})
    assert not A.should_pause({**base, "lapses": [1, 4], "pausedAt": 2})
    assert not A.should_pause({**base, "lapses": [1, 4], "minutesPerWeek": 0})
    assert A.add_lapse(base, 2) and base["lapses"] == [2] and not A.add_lapse(base, 2)


def test_ever_learned_in_the_rows_stops_a_pause(order):
    users = [person("a", 10, 1, lapses=[1, 4])]
    done = [row("a", order[0].id, 2, done=3)]
    assert A.hand_out(order, [], users, 7, WPM, LAST).pause_uids == ["a"]
    assert A.hand_out(order, done, users, 7, WPM, LAST).pause_uids == []


def test_120_minute_cap_applies_to_a_bigger_record():
    long_list = [A.Story(f"s{i}", "berakhot", 750) for i in range(60)]        # 10 minutes each
    plan = A.hand_out(long_list, [], [person("a", 500, 1)], 1, WPM, LAST)
    assert len(plan.new_rows) == 12                                             # 120 minutes, not 500
    plan = A.hand_out(long_list, [], [person("a", 500, 1)], 1, WPM, LAST, max_minutes=60)
    assert len(plan.new_rows) == 6


def test_at_least_one_story_only_when_holding_nothing(order):
    long = next(s for s in order if s.words == 2700)
    users = [person("a", 5, 1)]
    done_before = [row("a", s.id, 1, done=1) for s in order[:order.index(long)]]
    holding = done_before + [row("a", long.id, 1)]
    assert A.hand_out(order, done_before, users, 2, WPM, LAST).new_rows            # holds nothing: one story
    assert A.hand_out(order, holding, users, 2, WPM, LAST).new_rows == []          # holds a story: no extra one
    # holds a short story with room left, next story far too long: stops, does not hand out "at least one"
    small = [person("a", 10, 1)]
    nxt = [row("a", order[0].id, 1)]                                # 6.08 of 10 used; 3.92 left
    got = A.hand_out(order, nxt, small, 2, WPM, LAST).new_rows
    assert sum(next(s.words for s in order if s.id == r["storyId"]) for r in got) / WPM <= 3.92 + 1e-9


def test_person_with_a_row_this_week_gets_nothing_more(order):
    users = [person("a", 120, 1)]
    plan = A.hand_out(order, [row("a", order[5].id, 3, done=3)], users, 3, WPM, LAST)
    assert plan.new_rows == [] and plan.eligible_uids == ["a"]


def test_hand_out_starts_after_the_complete_rounds(order):
    plan = A.hand_out(order, [], [person("a", 10, 1)], 5, WPM, LAST, base_round=3)
    assert plan.new_rows and {r["round"] for r in plan.new_rows} == {3} and plan.new_rows[0]["storyId"] == order[0].id


def test_paused_and_delete_requested_get_nothing(order):
    users = [person("a", 10, 1, pausedAt=3), person("b", 10, 2, deleteRequested=True), person("c", 10, 3)]
    plan = A.assign_week(order, [], users, 2, WPM, LAST)
    assert {r["uid"] for r in plan.new_rows} == {"c"}
    assert plan.new_rows[0]["storyId"] == order[0].id


# ---------------------------------------------------------------- plan section 7: a list that changes

def test_story_added_early_in_the_list_is_picked_up_in_order(order):
    users = [person("a", 8, 1), person("b", 8, 2)]
    rows = play(order, users, [1])
    new = A.Story("berakhot-0a-0-0", "berakhot", 100)
    longer = [new] + list(order)                                       # an uncovered story at the very front
    users2 = [person("a", 8, 1), person("b", 8, 2), person("c", 8, 3)]
    plan = A.assign_week(longer, rows, users2, 2, WPM, LAST)
    assert plan.new_rows[0]["storyId"] == "berakhot-0a-0-0"           # the new one is handed out first


def test_story_added_late_in_the_list_is_reached_in_order(order):
    users = [person("a", 120, 1)]
    new = A.Story("ketubot-99b-1-1", "ketubot", 100)
    longer = list(order) + [new]
    plan = A.assign_week(longer, [], users, 1, WPM, LAST)
    assert [r["storyId"] for r in plan.new_rows][:19] == [s.id for s in longer]


def test_story_removed_while_someone_holds_it_is_ignored_and_nothing_breaks(order):
    users = [person("a", 8, 1), person("b", 8, 2)]
    held = row("a", order[2].id, 1)
    shorter = [s for s in order if s.id != order[2].id]
    plan = A.assign_week(shorter, [held], users, 2, WPM, LAST)
    assert order[2].id not in [r["storyId"] for r in plan.new_rows]   # never offered
    assert plan.new_rows                                               # and the week still works
    # the orphan row is released like any other at W+3, and counts for nothing in the summary
    assert held["id"] in A.assign_week(shorter, [held], users, 4, WPM, LAST).release_ids
    s = A.summarise(shorter, [row("a", order[2].id, 1, done=1)], users, "v1")
    assert s["learned"] == 0 and s["openInRound"] == 17


def test_list_changing_size_mid_round(order):
    users = [person("a", 8, 1), person("b", 8, 2)]
    rows = play(order, users, [1, 2])
    smaller = order[:10]
    plan = A.assign_week(smaller, rows, users, 3, WPM, LAST)
    assert all(r["storyId"] in {s.id for s in smaller} for r in plan.new_rows)
    bigger = list(order) + [A.Story(f"extra-{i}", "ketubot", 150) for i in range(4)]
    plan = A.assign_week(bigger, rows, users, 3, WPM, LAST)
    assert len({r["id"] for r in plan.new_rows}) == len(plan.new_rows)


# ---------------------------------------------------------------- idempotence and purity

def test_same_inputs_give_identical_row_ids(order):
    users = [person("a", 12, 1), person("b", 12, 2)]
    p1 = A.assign_week(order, [], users, 3, WPM, LAST)
    p2 = A.assign_week(order, [], users, 3, WPM, LAST)
    assert [r["id"] for r in p1.new_rows] == [r["id"] for r in p2.new_rows]
    assert p1.new_rows[0]["id"] == f"3_a_{order[0].id}"


def test_feeding_the_output_back_for_the_same_week_adds_nothing(order):
    users = [person("a", 12, 1), person("b", 12, 2)]
    first = A.assign_week(order, [], users, 3, WPM, LAST)
    again = A.assign_week(order, first.new_rows, users, 3, WPM, LAST)
    assert again.new_rows == []
    # even when a person still has budget left
    big = [person("a", 120, 1)]
    first = A.assign_week(order, [], big, 3, WPM, LAST)
    assert A.assign_week(order, first.new_rows, big, 3, WPM, LAST).new_rows == []


def test_inputs_are_not_mutated(order):
    users = [person("a", 8, 1, pausedAt=2), person("b", 0, 2), person("c", 8, 3)]
    rows = [row("a", order[0].id, 1, done=5), row("b", order[1].id, 1), row("c", order[2].id, 1)]
    u0, r0, o0 = copy.deepcopy(users), copy.deepcopy(rows), list(order)
    A.assign_week(order, rows, users, 4, WPM, LAST)
    A.summarise(order, rows, users, "v1")
    assert users == u0 and rows == r0 and order == o0


# ---------------------------------------------------------------- summarise

def test_summarise_counts_and_by_tractate_sums_to_learned(order):
    users = [person("a", 8, 1), person("b", 8, 2, deleteRequested=True)]
    rows = [row("a", order[0].id, 1, done=2), row("a", order[1].id, 1, done=2),
            row("a", order[7].id, 1, done=2),
            row("a", order[0].id, 2, done=3),                          # the same story twice: counted once
            row("b", order[3].id, 1)]                                  # open, not counted
    s = A.summarise(order, rows, users, "v1")
    assert s == {"learned": 3, "byTractate": {"berakhot": 2, "shabbat": 1}, "round": 1, "roundsCompleted": 0,
                 "openInRound": 15, "joined": 1, "listVersion": "v1"}
    assert sum(s["byTractate"].values()) == s["learned"]


def test_summarise_complete_round_and_open_story_blocking(order):
    users = [person("a", 8, 1)]
    full = [row("a", s.id, 1, done=1) for s in order]
    s = A.summarise(order, full, users, "v1")
    assert (s["roundsCompleted"], s["round"], s["learned"], s["openInRound"]) == (1, 2, 0, 18)
    assert sum(s["byTractate"].values()) == s["learned"]
    one_open = full[:-1] + [row("a", order[-1].id, 1)]                  # one story not done
    s = A.summarise(order, one_open, users, "v1")
    assert (s["roundsCompleted"], s["round"], s["learned"], s["openInRound"]) == (0, 1, 17, 1)
    # round 1 complete and a start on round 2
    s = A.summarise(order, full + [row("a", order[0].id, 5, round_=2, done=6)], users, "v1")
    assert (s["roundsCompleted"], s["round"], s["learned"]) == (1, 2, 1)
    assert s["byTractate"] == {"berakhot": 1}


def test_summarise_with_nothing_yet(order):
    s = A.summarise(order, [], [], None)
    assert (s["learned"], s["round"], s["roundsCompleted"], s["openInRound"], s["joined"]) == (0, 1, 0, 18, 0)
    assert s["byTractate"] == {} and s["listVersion"] is None


def test_summarise_with_a_base_round_counts_from_there(order):
    users = [person("a", 8, 1)]
    # rounds 1 and 2 complete (not supplied), round 3 under way: only round >= 3 rows are given
    rows = [row("a", s.id, 9, round_=3, done=9) for s in order[:5]]
    s = A.summarise(order, rows, users, "v1", base_round=3)
    assert (s["roundsCompleted"], s["round"], s["learned"], s["openInRound"]) == (2, 3, 5, 13)
    full = [row("a", s.id, 9, round_=3, done=9) for s in order]
    s = A.summarise(order, full, users, "v1", base_round=3)
    assert (s["roundsCompleted"], s["round"], s["learned"]) == (3, 4, 0)
    s = A.summarise(order, [], users, "v1", base_round=3)
    assert (s["roundsCompleted"], s["round"]) == (2, 3)
    assert A.summarise(order, rows, users, "v1") != s                              # the default counts from round 1
