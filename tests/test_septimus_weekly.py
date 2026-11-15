"""Tests for scripts/septimus_weekly.py with an in-memory fake Store. No Firebase, no emulator, no network."""
import json
import subprocess
import sys
import logging
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import septimus_assign as A  # noqa: E402
import septimus_weekly as W  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "septimus_stories"
LAUNCH = date(2026, 12, 6)                      # a Sunday
SUNDAY, MONDAY = date(2026, 12, 6), date(2026, 12, 7)


class FakeStore:
    """Same methods as Store, kept in dicts. Records every write so tests can see whether anything changed."""

    def __init__(self, users, rows=(), summary=None):
        self.user_docs = {u["uid"]: dict(u) for u in users}
        self.rows = {r["id"]: dict(r) for r in rows}
        self.runs = {}
        self.summary = summary
        self.writes = 0
        self.reads = 0
        self.read_row_ids = []          # ids of every assignment row handed to the runner
        self.deleted_auth = []
        self.user_updates = []          # (uid, fields) for every update_user call
        self.write_batches = []         # one entry per person per write_rows call: that person's row ids
        self.fail_delete = set()        # uids whose delete_person raises

    def users(self):
        self.reads += len(self.user_docs)
        return [dict(u) for u in self.user_docs.values()]

    def get_summary(self):
        self.reads += 1
        return dict(self.summary) if self.summary else None

    def assignments(self, from_round=1):
        """Rows with round >= from_round plus every open row, like the real Store."""
        out = [dict(r) for r in self.rows.values()
               if r["round"] >= from_round or (not r.get("doneAt") and not r.get("releasedAt"))]
        self.reads += len(out)
        self.read_row_ids += [r["id"] for r in out]
        return out

    def get_run(self, week):
        self.reads += 1
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
        by_uid = {}
        for r in rows:
            by_uid.setdefault(r["uid"], []).append(r)
        for mine in by_uid.values():
            if any(r["id"] in self.rows for r in mine):          # create semantics: the whole person is left alone
                continue
            self.write_batches.append([r["id"] for r in mine])
            for r in mine:
                self.writes += 1
                self.rows[r["id"]] = {**r, "assignedAt": 1}

    def release_row(self, row_id):
        """False only when the row was marked learned; True otherwise (like the real Store)."""
        r = self.rows.get(row_id)
        if r is None:
            return True
        if r.get("doneAt"):
            return False
        if not r.get("releasedAt"):
            self.writes += 1
            r["releasedAt"] = "x"
        return True

    def update_user(self, uid, fields):
        self.writes += 1
        self.user_updates.append((uid, dict(fields)))
        self.user_docs[uid].update(fields)

    def set_paused(self, uid, value):
        self.writes += 1
        self.user_docs[uid].update({"pausedAt": 50, "lapses": []} if value else {"pausedAt": None})

    def write_summary(self, summary):
        self.writes += 1
        self.summary = dict(summary)

    def delete_person(self, uid):
        if uid in self.fail_delete:
            raise RuntimeError(f"auth failure for {uid}")        # a real error text can carry the uid
        self.writes += 1
        self.deleted_auth.append(uid)
        for rid, r in list(self.rows.items()):
            if r.get("uid") == uid:
                del self.rows[rid]
                new = {**r, "uid": ""}
                if not r.get("doneAt") and not r.get("releasedAt"):
                    new["releasedAt"] = "x"
                self.rows[f"{r['week']}_deleted-{len(self.rows):012x}_{r['storyId']}"] = new
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
    first = go(store, SUNDAY, order)
    assert first["handedOut"] > 0 and first["week"] == 1
    before = snapshot(store)
    second = go(store, SUNDAY, order)
    assert snapshot(store) == before and second["handedOut"] == 0
    go(store, date(2026, 12, 8), order)                       # a later day, same week: still nothing
    assert snapshot(store) == before


def test_a_run_on_monday_does_the_weeks_handout_if_sunday_never_ran(order):
    store = FakeStore([person("a", 8, 1)])
    counts = go(store, MONDAY, order)
    assert counts["week"] == 1 and counts["handedOut"] > 0
    assert all(r["week"] == 1 for r in store.rows.values())
    assert store.runs[1]["counts"] == counts and store.runs[1]["finishedAt"]


def test_launch_date_unset_means_no_handout_but_summary_is_written(order):
    store = FakeStore([person("a", 8, 1)])
    counts = go(store, SUNDAY, order, cfg=config(launch=None))
    assert counts["handedOut"] == 0 and not store.rows and not store.runs
    assert store.summary and store.summary["joined"] == 1 and store.summary["listVersion"] == "test-1"


def test_before_launch_and_after_the_yahrzeit_week_no_handout(order):
    store = FakeStore([person("a", 8, 1)])
    assert go(store, date(2026, 12, 5), order)["handedOut"] == 0
    assert go(store, date(2027, 9, 20), order)["handedOut"] == 0
    assert not store.rows and not store.runs and store.summary


def test_pause_does_everything_except_the_handout(order):
    store = FakeStore([person("a", 0, 1, deleteRequested=False), person("b", 8, 2)],
                      [{"id": f"1_a_{order[0].id}", "uid": "a", "storyId": order[0].id, "round": 1, "week": 1,
                        "doneAt": None, "releasedAt": None}])
    counts = go(store, SUNDAY, order, pause=True)
    assert counts["handedOut"] == 0
    assert not [r for r in store.rows.values() if r["uid"] == "b"] and 1 not in store.runs
    assert store.rows[f"1_a_{order[0].id}"]["releasedAt"] == "x"         # the stopped person's story still released
    assert store.summary is not None
    assert go(store, SUNDAY, order)["handedOut"] > 0                      # un-pausing hands out the same week


def test_dry_run_writes_nothing(order, capsys):
    store = FakeStore([person("a", 8, 1), person("b", 8, 2, deleteRequested=True)])
    before = snapshot(store)
    counts = go(store, SUNDAY, order, dry_run=True)
    assert store.writes == 0 and snapshot(store) == before and store.deleted_auth == []
    assert counts["handedOut"] > 0 and counts["deleted"] == 1
    assert json.loads(capsys.readouterr().out.strip().splitlines()[-1]) == counts


def test_delete_request_removes_the_person_and_keeps_the_learned_total(order):
    rows = [{"id": f"1_b_{order[0].id}", "uid": "b", "storyId": order[0].id, "round": 1, "week": 1,
             "doneAt": 5, "releasedAt": None},
            {"id": f"1_b_{order[1].id}", "uid": "b", "storyId": order[1].id, "round": 1, "week": 1,
             "doneAt": None, "releasedAt": None}]
    store = FakeStore([person("a", 8, 1), person("b", 8, 2, deleteRequested=True)], rows)
    counts = go(store, SUNDAY, order)
    assert store.deleted_auth == ["b"] and "b" not in store.user_docs and counts["deleted"] == 1
    assert all(r["uid"] != "b" for r in store.rows.values())             # blanked
    assert store.summary["learned"] == 1                                 # the done story still counts
    assert store.summary["joined"] == 1
    assert not any("_b_" in rid for rid in store.rows)                   # no id carries the uid any more
    open_one = [r for r in store.rows.values() if r["storyId"] == order[1].id and r["uid"] == ""]
    assert open_one and open_one[0]["releasedAt"]                        # the open one went back to the pool
    a_rows = [r["storyId"] for r in store.rows.values() if r["uid"] == "a"]
    assert order[1].id in a_rows                                         # and a person who stayed got it


def test_counts_include_new_signups_since_the_previous_run(order):
    store = FakeStore([person("a", 8, 1), person("b", 8, 2)])
    first = go(store, SUNDAY, order)
    assert first["newSignups"] == 2 and first["users"] == 2 and first["eligible"] == 2
    assert first["totalMinutes"] == 16
    store.user_docs["c"] = person("c", 8, 500)                            # joined after week 1 finished (finishedAt 101)
    second = go(store, date(2026, 12, 14), order)
    assert second["week"] == 2 and second["newSignups"] == 1


def test_stopped_person_is_released_on_a_non_handout_day(order):
    rows = [{"id": f"1_a_{order[0].id}", "uid": "a", "storyId": order[0].id, "round": 1, "week": 1,
             "doneAt": None, "releasedAt": None}]
    store = FakeStore([person("a", 0, 1)], rows)
    counts = go(store, date(2026, 12, 5), order)                          # before launch
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
    c = W.parse_config(SAMPLE % "2026-12-06")
    assert (c.launch_date, c.yahrzeit, c.wpm, c.max_minutes) == (date(2026, 12, 6), date(2027, 9, 10), 75, 120)
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


# ---------------------------------------------------------------- review fixes

def test_a_row_marked_learned_at_release_time_is_not_given_to_someone_else(order):
    store = FakeStore([person("alice", 30, 1), person("bob", 30, 2)])
    go(store, SUNDAY, order)
    alice_week1 = {r["storyId"] for r in store.rows.values() if r["uid"] == "alice"}
    assert alice_week1

    class Racy(FakeStore):
        def release_row(self, rid):                              # alice ticks the story at the very last second
            if self.rows[rid]["uid"] == "alice":
                self.rows[rid]["doneAt"] = 999
            return super().release_row(rid)

    racy = Racy([])
    racy.user_docs, racy.rows, racy.runs = store.user_docs, store.rows, store.runs
    go(racy, date(2026, 12, 28), order)                          # week 4: week-1 rows come due
    regiven = [r for r in racy.rows.values() if r["week"] == 4 and r["uid"] != "alice"
               and r["round"] == 1 and r["storyId"] in alice_week1]
    assert regiven == []                                         # still hers: covered, not free
    assert racy.user_docs["alice"]["lastLearnedWeek"] == 1      # and it counts as learning
    assert not racy.user_docs["alice"].get("lapses")             # not a lapse


def test_a_failing_delete_does_not_stop_the_handout_and_logs_no_uid(order, caplog, capsys):
    store = FakeStore([person("UIDcarol777", 30, 1, deleteRequested=True), person("UIDdan888", 30, 2)])
    store.fail_delete.add("UIDcarol777")
    with caplog.at_level(logging.INFO):
        counts = go(store, SUNDAY, order)
    assert counts["deleteFailed"] == 1 and counts["deleted"] == 0 and counts["handedOut"] > 0
    assert "UIDcarol777" in store.user_docs and store.runs[1]["finishedAt"]
    assert [r for r in store.rows.values() if r["uid"] == "UIDdan888"]
    assert any(rec.levelno == logging.WARNING for rec in caplog.records)
    everything = caplog.text + capsys.readouterr().out
    assert "UIDcarol777" not in everything and "UIDdan888" not in everything


def test_no_uid_in_logs_or_dry_run_output(order, caplog, capsys):
    rows = [{"id": f"1_UIDaaa111_{order[0].id}", "uid": "UIDaaa111", "storyId": order[0].id, "round": 1, "week": 1,
             "doneAt": None, "releasedAt": None}]
    store = FakeStore([person("UIDaaa111", 30, 1), person("UIDbbb222", 30, 2, deleteRequested=True),
                       person("UIDccc333", 0, 3)], rows)
    with caplog.at_level(logging.DEBUG):
        go(store, SUNDAY, order, dry_run=True)
        go(store, SUNDAY, order)
    everything = caplog.text + capsys.readouterr().out
    for uid in ("UIDaaa111", "UIDbbb222", "UIDccc333"):
        assert uid not in everything
    assert "1_UID" not in everything                              # no row id either


def test_dry_run_prints_counts_and_story_ids_only(order, caplog, capsys):
    store = FakeStore([person("UIDaaa111", 30, 1), person("UIDbbb222", 30, 2)])
    with caplog.at_level(logging.INFO):
        go(store, SUNDAY, order, dry_run=True)
    dry = [rec.getMessage() for rec in caplog.records if "DRY RUN" in rec.getMessage()]
    assert dry and order[0].id in dry[0] and "UID" not in dry[0]


def test_rows_read_are_limited_to_the_current_round_plus_open_rows(order):
    # round 1 complete and done; round 2 under way; one stray OPEN round-1 row (an old doubled-up row)
    done_r1 = [{"id": f"1_u{i}_{s.id}", "uid": f"u{i % 3}", "storyId": s.id, "round": 1, "week": 1,
                "doneAt": 5, "releasedAt": None} for i, s in enumerate(order)]
    stray = {"id": f"1_zz_{order[0].id}", "uid": "zz", "storyId": order[0].id, "round": 1, "week": 1,
             "doneAt": None, "releasedAt": None}
    r2 = [{"id": f"2_u0_{order[0].id}", "uid": "u0", "storyId": order[0].id, "round": 2, "week": 2,
           "doneAt": 6, "releasedAt": None}]
    old_released = [{"id": f"1_old_{order[0].id}", "uid": "old", "storyId": order[0].id, "round": 1, "week": 1,
                     "doneAt": None, "releasedAt": 3}]
    store = FakeStore([person("u0", 30, 1), person("u1", 30, 2), person("zz", 30, 3)],
                      done_r1 + [stray] + r2 + old_released, summary={"round": 2})
    go(store, SUNDAY, order)
    read = set(store.read_row_ids)
    assert f"2_u0_{order[0].id}" in read and stray["id"] in read                     # round 2 and the open row
    assert not (read & {r["id"] for r in done_r1}) and old_released[0]["id"] not in read   # complete round 1: not read
    # the summary still counts from round 2, not from scratch
    assert store.summary["round"] == 2 and store.summary["roundsCompleted"] == 1 and store.summary["learned"] == 1
    # and the new rows start in round 2, never re-dealing round 1
    new = [r for r in store.rows.values() if r.get("assignedAt")]
    assert new and {r["round"] for r in new} == {2}


def test_counts_report_the_reads(order):
    store = FakeStore([person("a", 30, 1)])
    counts = go(store, SUNDAY, order)
    assert counts["reads"] == store.reads > 0
    assert store.runs[1]["counts"]["reads"] == counts["reads"]
    again = go(store, SUNDAY, order)                                  # a second run reports its own reads, not a total
    assert again["reads"] == store.reads - counts["reads"]


def test_each_person_is_written_in_one_batch(order):
    store = FakeStore([person("a", 30, 1), person("b", 30, 2), person("c", 30, 3)])
    go(store, SUNDAY, order)
    assert len(store.write_batches) == 3
    for batch in store.write_batches:
        assert len({rid.split("_")[1] for rid in batch}) == 1               # one person per batch
    assert sum(len(b) for b in store.write_batches) == len(store.rows)


def test_a_never_reading_person_is_paused_at_the_week_7_run_and_lapses_are_stored(order):
    store = FakeStore([person("a", 30, 1)])
    for w in range(1, 8):
        counts = go(store, LAUNCH + (w - 1) * timedelta(days=7), order)
        if w < 7:
            assert counts["paused"] == 0, w
    assert counts["paused"] == 1 and store.user_docs["a"]["pausedAt"] and store.user_docs["a"]["lapses"] == []
    assert not [r for r in store.rows.values() if r["week"] == 7]
    # the person resumes by clearing pausedAt: handed stories again, and not re-paused by old history
    store.user_docs["a"]["pausedAt"] = None
    counts = go(store, date(2027, 1, 18), order)                             # week 7 again: its run did not finish? it did
    assert store.runs[7]["finishedAt"] and counts["handedOut"] == 0          # week 7 is finished; resume shows at week 8
    counts = go(store, date(2027, 1, 25), order)
    assert counts["week"] == 8 and counts["handedOut"] > 0 and counts["paused"] == 0


def test_last_learned_week_is_written_only_when_it_increases(order):
    store = FakeStore([person("a", 30, 1)])
    go(store, SUNDAY, order)
    first = next(r for r in store.rows.values() if r["uid"] == "a")
    first["doneAt"] = 5
    go(store, date(2026, 12, 8), order)
    assert [u for u in store.user_updates if "lastLearnedWeek" in u[1]] == [("a", {"lastLearnedWeek": 1})]
    go(store, date(2026, 12, 9), order)
    assert len([u for u in store.user_updates if "lastLearnedWeek" in u[1]]) == 1       # not written again


def test_a_person_who_keeps_learning_is_never_paused(order):
    store = FakeStore([person("a", 30, 1)])
    go(store, SUNDAY, order)
    for w in range(2, 10):
        for r in store.rows.values():
            r["doneAt"] = r.get("doneAt") or 5                  # learns whatever they were given
        counts = go(store, LAUNCH + (w - 1) * timedelta(days=7), order)
        assert counts["paused"] == 0


def test_launch_date_not_a_sunday_raises():
    with pytest.raises(ValueError, match="launchDate must be a Sunday"):
        W.parse_config(SAMPLE % "2026-12-07")


def test_config_parsing_survives_spacing_and_a_different_indent():
    text = SAMPLE.replace('launchDate: "%s"', 'launchDate :"%s"').replace("signup: {", "signup :{ ") % "2026-12-06"
    text = text.replace("wpm: 75", "wpm  :75").replace('\n  }\n};', '\n    }\n};')
    c = W.parse_config(text)
    assert (c.launch_date, c.wpm, c.max_minutes) == (date(2026, 12, 6), 75, 120)
