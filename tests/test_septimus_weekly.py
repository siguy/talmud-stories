"""Tests for scripts/septimus_weekly.py with an in-memory fake Store. No Firebase, no emulator, no network."""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import septimus_assign as A  # noqa: E402
import septimus_weekly as W  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "septimus_stories"
LAUNCH = date(2026, 12, 7)                      # a Monday
MONDAY, TUESDAY = date(2026, 12, 7), date(2026, 12, 8)


class FakeStore:
    """Same methods as Store, kept in dicts. Records every write so tests can see whether anything changed."""

    def __init__(self, users, rows=()):
        self.user_docs = {u["uid"]: dict(u) for u in users}
        self.rows = {r["id"]: dict(r) for r in rows}
        self.runs = {}
        self.summary = None
        self.writes = 0
        self.deleted_auth = []

    def users(self):
        return [dict(u) for u in self.user_docs.values()]

    def assignments(self):
        return [dict(r) for r in self.rows.values()]

    def get_run(self, week):
        return self.runs.get(week)

    def start_run(self, week):
        self.writes += 1
        self.runs.setdefault(week, {})["startedAt"] = 1

    def finish_run(self, week, counts):
        self.writes += 1
        self.runs[week].update(finishedAt=100 + week, counts=counts)

    def previous_finished_at(self, week):
        times = [r["finishedAt"] for w, r in self.runs.items() if w < week and r.get("finishedAt")]
        return max(times) if times else None

    def write_rows(self, rows):
        for r in rows:
            if r["id"] not in self.rows:
                self.writes += 1
                self.rows[r["id"]] = {**r, "assignedAt": 1}

    def release_row(self, row_id):
        r = self.rows[row_id]
        if r.get("doneAt") or r.get("releasedAt"):
            return False
        self.writes += 1
        r["releasedAt"] = "x"
        return True

    def set_paused(self, uid, value):
        self.writes += 1
        self.user_docs[uid]["pausedAt"] = 50 if value else None

    def write_summary(self, summary):
        self.writes += 1
        self.summary = dict(summary)

    def delete_person(self, uid):
        self.writes += 1
        self.deleted_auth.append(uid)
        for r in self.rows.values():
            if r.get("uid") == uid:
                r["uid"] = None
                if not r.get("doneAt") and not r.get("releasedAt"):
                    r["releasedAt"] = "x"
        del self.user_docs[uid]


def person(uid, minutes, created, **kw):
    return {"uid": uid, "createdAt": created, "minutesPerWeek": minutes, "deleteRequested": False,
            "pausedAt": None, **kw}


def config(launch=LAUNCH):
    return W.Config(launch_date=launch, yahrzeit=date(2027, 9, 10), wpm=75, max_minutes=120)


@pytest.fixture
def order():
    return A.load_story_order(FIX)


def go(store, today, order, cfg=None, **kw):
    return W.run(store, today, cfg or config(), story_order=order, list_version="test-1", **kw)


def snapshot(store):
    return json.dumps([store.user_docs, store.rows, store.runs, store.summary], sort_keys=True, default=str)


def test_second_run_for_the_same_week_changes_nothing(order):
    store = FakeStore([person("a", 8, 1), person("b", 8, 2)])
    first = go(store, MONDAY, order)
    assert first["handedOut"] > 0 and first["week"] == 1
    before = snapshot(store)
    second = go(store, MONDAY, order)
    assert snapshot(store) == before and second["handedOut"] == 0
    go(store, date(2026, 12, 9), order)                       # a later day, same week: still nothing
    assert snapshot(store) == before


def test_a_run_on_tuesday_does_the_weeks_handout_if_monday_never_ran(order):
    store = FakeStore([person("a", 8, 1)])
    counts = go(store, TUESDAY, order)
    assert counts["week"] == 1 and counts["handedOut"] > 0
    assert all(r["week"] == 1 for r in store.rows.values())
    assert store.runs[1]["counts"] == counts and store.runs[1]["finishedAt"]


def test_launch_date_unset_means_no_handout_but_summary_is_written(order):
    store = FakeStore([person("a", 8, 1)])
    counts = go(store, MONDAY, order, cfg=config(launch=None))
    assert counts["handedOut"] == 0 and not store.rows and not store.runs
    assert store.summary and store.summary["joined"] == 1 and store.summary["listVersion"] == "test-1"


def test_before_launch_and_after_the_yahrzeit_week_no_handout(order):
    store = FakeStore([person("a", 8, 1)])
    assert go(store, date(2026, 12, 6), order)["handedOut"] == 0
    assert go(store, date(2027, 9, 20), order)["handedOut"] == 0
    assert not store.rows and not store.runs and store.summary


def test_pause_does_everything_except_the_handout(order):
    store = FakeStore([person("a", 0, 1, deleteRequested=False), person("b", 8, 2)],
                      [{"id": f"1_a_{order[0].id}", "uid": "a", "storyId": order[0].id, "round": 1, "week": 1,
                        "doneAt": None, "releasedAt": None}])
    counts = go(store, MONDAY, order, pause=True)
    assert counts["handedOut"] == 0
    assert not [r for r in store.rows.values() if r["uid"] == "b"] and 1 not in store.runs
    assert store.rows[f"1_a_{order[0].id}"]["releasedAt"] == "x"         # the stopped person's story still released
    assert store.summary is not None
    assert go(store, MONDAY, order)["handedOut"] > 0                      # un-pausing hands out the same week


def test_dry_run_writes_nothing(order, capsys):
    store = FakeStore([person("a", 8, 1), person("b", 8, 2, deleteRequested=True)])
    before = snapshot(store)
    counts = go(store, MONDAY, order, dry_run=True)
    assert store.writes == 0 and snapshot(store) == before and store.deleted_auth == []
    assert counts["handedOut"] > 0 and counts["deleted"] == 1
    assert json.loads(capsys.readouterr().out.strip().splitlines()[-1]) == counts


def test_delete_request_removes_the_person_and_keeps_the_learned_total(order):
    rows = [{"id": f"1_b_{order[0].id}", "uid": "b", "storyId": order[0].id, "round": 1, "week": 1,
             "doneAt": 5, "releasedAt": None},
            {"id": f"1_b_{order[1].id}", "uid": "b", "storyId": order[1].id, "round": 1, "week": 1,
             "doneAt": None, "releasedAt": None}]
    store = FakeStore([person("a", 8, 1), person("b", 8, 2, deleteRequested=True)], rows)
    counts = go(store, MONDAY, order)
    assert store.deleted_auth == ["b"] and "b" not in store.user_docs and counts["deleted"] == 1
    assert all(r["uid"] != "b" for r in store.rows.values())             # blanked
    assert store.summary["learned"] == 1                                 # the done story still counts
    assert store.summary["joined"] == 1
    assert store.rows[f"1_b_{order[1].id}"]["releasedAt"]                # the open one went back to the pool
    a_rows = [r["storyId"] for r in store.rows.values() if r["uid"] == "a"]
    assert order[1].id in a_rows                                         # and a person who stayed got it


def test_counts_include_new_signups_since_the_previous_run(order):
    store = FakeStore([person("a", 8, 1), person("b", 8, 2)])
    first = go(store, MONDAY, order)
    assert first["newSignups"] == 2 and first["users"] == 2 and first["eligible"] == 2
    assert first["totalMinutes"] == 16
    store.user_docs["c"] = person("c", 8, 500)                            # joined after week 1 finished (finishedAt 101)
    second = go(store, date(2026, 12, 14), order)
    assert second["week"] == 2 and second["newSignups"] == 1


def test_stopped_person_is_released_on_a_non_handout_day(order):
    rows = [{"id": f"1_a_{order[0].id}", "uid": "a", "storyId": order[0].id, "round": 1, "week": 1,
             "doneAt": None, "releasedAt": None}]
    store = FakeStore([person("a", 0, 1)], rows)
    counts = go(store, date(2026, 12, 6), order)                          # before launch
    assert counts["released"] == 1 and store.rows[f"1_a_{order[0].id}"]["releasedAt"]


SAMPLE = '''window.SEPTIMUS_CONFIG = {
  firebase: { projectId: "septimus-stories" },
  signup: {
    wpm: 75,                    // reading pace
    launchDate: "%s",           // ISO date
    yahrzeit: "2027-09-10",
    yahrzeitLabel: "8 Elul",
    maxMinutes: 120,
    contactEmail: "",
    communities: ["hadar"]
  }
};
'''


def test_config_parsing_launch_set_and_unset():
    c = W.parse_config(SAMPLE % "2026-12-07")
    assert (c.launch_date, c.yahrzeit, c.wpm, c.max_minutes) == (date(2026, 12, 7), date(2027, 9, 10), 75, 120)
    assert c.last_week == 40 and c.project_id == "septimus-stories"
    c = W.parse_config(SAMPLE % "")
    assert c.launch_date is None and c.last_week == 0


def test_real_config_js_parses():
    c = W.parse_config((ROOT / "site" / "config.js").read_text())
    assert c.wpm > 0 and c.max_minutes > 0


def test_help_works_without_firebase_admin():
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "septimus_weekly.py"), "--help"],
                         capture_output=True, text=True)
    assert out.returncode == 0 and "--dry-run" in out.stdout
