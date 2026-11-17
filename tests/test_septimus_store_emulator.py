"""The real Firestore-backed Store in scripts/septimus_weekly.py, run against the local Firebase emulators.

tests/test_septimus_weekly.py proves the hand-out logic with an in-memory fake. This file proves the part the fake
cannot: that the real Store reads and writes Firestore and Firebase Auth the way the plan (section 5) says.

Needs `firebase_admin` (pip install -r requirements-septimus.txt), the `firebase` CLI and a working `java`.
If any is missing, or ports 8080 / 9099 are busy, the module is skipped with a reason (or fails when
REQUIRE_RULES_TESTS=1, same switch as tests/test_firestore_rules.py).

Only the emulators are ever used: the fixture refuses to build a Store unless both emulator variables are set.
"""
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
FIX = ROOT / "tests" / "fixtures" / "septimus_stories"
PROJECT = "demo-septimus"
FS_HOST, AUTH_HOST = "localhost:8080", "localhost:9099"
EMU_ENV = {"FIRESTORE_EMULATOR_HOST": FS_HOST, "FIREBASE_AUTH_EMULATOR_HOST": AUTH_HOST,
           "GOOGLE_CLOUD_PROJECT": PROJECT}

WEEK1, WEEK2, WEEK3, WEEK4 = date(2026, 12, 6), date(2026, 12, 13), date(2026, 12, 20), date(2026, 12, 27)


def _skip(reason):
    if os.environ.get("REQUIRE_RULES_TESTS") == "1":
        pytest.fail("REQUIRE_RULES_TESTS=1 but the Store emulator tests cannot run: " + reason)
    pytest.skip(reason, allow_module_level=True)


try:
    import firebase_admin  # noqa: F401
    from firebase_admin import auth as fb_auth
    from firebase_admin import firestore as fb_fs
except ImportError:
    _skip("firebase_admin is not installed (pip install -r requirements-septimus.txt)")

import septimus_assign as A  # noqa: E402
import septimus_weekly as W  # noqa: E402


def _port_open(port):
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _java_works():
    """macOS ships a /usr/bin/java stub that exists but does not run, so run it."""
    try:
        return subprocess.run(["java", "-version"], capture_output=True, timeout=10).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


@pytest.fixture(scope="module", autouse=True)
def emulators():
    if not shutil.which("firebase"):
        _skip("firebase CLI is needed to run the emulators")
    if not _java_works():
        _skip("no working Java runtime: the Firestore emulator needs one")
    for port in (8080, 9099):
        if _port_open(port):
            _skip(f"port {port} is already in use by something else")
    proc = subprocess.Popen(
        ["firebase", "emulators:start", "--only", "auth,firestore", "--project", PROJECT],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    saved = {k: os.environ.get(k) for k in EMU_ENV}
    try:
        deadline = time.time() + 120
        while time.time() < deadline:
            if proc.poll() is not None:
                _skip("firebase emulators exited during start-up")
            if _port_open(8080) and _port_open(9099):
                break
            time.sleep(0.5)
        else:
            _skip("firebase emulators did not start within 120 seconds")
        os.environ.update(EMU_ENV)
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=20)
        except Exception:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                pass


def _http_delete(url):
    urllib.request.urlopen(urllib.request.Request(url, method="DELETE"), timeout=10).read()


@pytest.fixture(autouse=True)
def clean(emulators):
    _http_delete(f"http://{FS_HOST}/emulator/v1/projects/{PROJECT}/databases/(default)/documents")
    _http_delete(f"http://{AUTH_HOST}/emulator/v1/projects/{PROJECT}/accounts")
    yield


@pytest.fixture
def store():
    """The REAL Store, pointed at the emulators. Refuses to run against anything else."""
    assert os.environ.get("FIRESTORE_EMULATOR_HOST") == FS_HOST, "FIRESTORE_EMULATOR_HOST not set: refusing"
    assert os.environ.get("FIREBASE_AUTH_EMULATOR_HOST") == AUTH_HOST, "FIREBASE_AUTH_EMULATOR_HOST not set: refusing"
    s = W.Store(PROJECT)
    yield s
    firebase_admin.delete_app(firebase_admin.get_app())


# ---------------------------------------------------------------- helpers

def config():
    return W.Config(launch_date=WEEK1, yahrzeit=date(2027, 9, 10), wpm=75, max_minutes=120)


@pytest.fixture(scope="module")
def order():
    return A.load_story_order(FIX)


def go(store, today, order, **kw):
    return W.run(store, today, config(), story_order=order, list_version="test-1", **kw)


def seed_person(store, name, minutes, n, **extra):
    """An Auth account plus users/{uid} shaped exactly as the browser writes it."""
    uid = fb_auth.create_user(uid=name, email=f"{name}@example.com").uid
    store.db.collection("users").document(uid).set({
        "createdAt": datetime(2026, 11, 20, 12, n, tzinfo=timezone.utc),   # increasing: sign-up order a, b, c
        "minutesPerWeek": minutes, "src": "hadar", "deleteRequested": False, **extra})
    return uid


def seed3(store):
    return [seed_person(store, "pa", 30, 1), seed_person(store, "pb", 30, 2), seed_person(store, "pc", 30, 3)]


def dump(store, *collections):
    return {c: {d.id: d.to_dict() for d in store.db.collection(c).stream()} for c in collections}


def rows_of(store):
    return dump(store, "assignments")["assignments"]


def auth_exists(uid):
    try:
        fb_auth.get_user(uid)
        return True
    except fb_auth.UserNotFoundError:
        return False


# ---------------------------------------------------------------- 1. week 1

def test_week_one_writes_rows_run_and_summary(store, order):
    uids = seed3(store)
    counts = go(store, WEEK1, order)
    assert counts["week"] == 1 and counts["handedOut"] > 0 and counts["eligible"] == 3

    rows = rows_of(store)
    assert len(rows) == counts["handedOut"]
    for rid, r in rows.items():
        assert rid == f"{r['week']}_{r['uid']}_{r['storyId']}" and r["uid"] in uids
        assert set(r) == {"uid", "storyId", "round", "week", "assignedAt", "doneAt", "releasedAt"}
        assert r["week"] == 1 and r["round"] == 1
        assert isinstance(r["assignedAt"], datetime)                  # a real timestamp, not a string
        assert r["doneAt"] is None and r["releasedAt"] is None
    assert {r["uid"] for r in rows.values()} == set(uids)

    run1 = dump(store, "runs")["runs"]["1"]
    assert isinstance(run1["startedAt"], datetime) and isinstance(run1["finishedAt"], datetime)
    assert run1["counts"]["handedOut"] == counts["handedOut"] and run1["counts"]["newSignups"] == 3

    summary = dump(store, "progress")["progress"]["summary"]
    assert set(summary) == {"learned", "byTractate", "round", "roundsCompleted", "openInRound", "joined",
                            "listVersion", "week", "lastWeek", "updatedAt"}
    assert summary["learned"] == 0 and summary["joined"] == 3 and summary["listVersion"] == "test-1"
    assert summary["openInRound"] == len(order) and isinstance(summary["updatedAt"], datetime)


# ---------------------------------------------------------------- 2. rerun

def test_rerunning_the_same_week_changes_nothing(store, order):
    seed3(store)
    go(store, WEEK1, order)
    before = dump(store, "users", "assignments", "runs")
    summary_before = dump(store, "progress")["progress"]["summary"]
    again = go(store, WEEK1, order)
    assert again["handedOut"] == 0
    assert dump(store, "users", "assignments", "runs") == before        # every field, every doc
    assert len(rows_of(store)) == len(before["assignments"])
    # the summary is refreshed every run (only updatedAt moves)
    after = dump(store, "progress")["progress"]["summary"]
    assert {k: v for k, v in after.items() if k != "updatedAt"} == {k: v for k, v in summary_before.items() if k != "updatedAt"}

    # a half-finished week (rows written, run never finished) is safe to run again: no row is overwritten
    store.db.collection("runs").document("1").update({"finishedAt": fb_fs.DELETE_FIELD})
    pre = rows_of(store)
    go(store, WEEK1, order)
    assert rows_of(store) == pre


# ---------------------------------------------------------------- 3. done / release across weeks

def test_done_row_is_kept_and_a_stale_unread_row_moves_to_someone_else(store, order):
    seed3(store)
    go(store, WEEK1, order)
    wk1 = rows_of(store)
    done_id = sorted(rid for rid, r in wk1.items() if r["uid"] == "pa")[0]
    stale_id = sorted(rid for rid, r in wk1.items() if r["uid"] == "pb")[0]
    store.db.collection("assignments").document(done_id).update({"doneAt": datetime.now(timezone.utc)})

    go(store, WEEK2, order)
    go(store, WEEK3, order)
    assert rows_of(store)[stale_id]["releasedAt"] is None              # still on the list in weeks 2 and 3
    go(store, WEEK4, order)

    rows = rows_of(store)
    assert rows[done_id]["releasedAt"] is None and rows[done_id]["doneAt"] is not None
    stale = rows[stale_id]
    assert isinstance(stale["releasedAt"], datetime)
    again = [r for r in rows.values() if r["storyId"] == stale["storyId"] and r["round"] == stale["round"]
             and r["week"] == 4 and r["releasedAt"] is None]
    assert again and all(r["uid"] != "pb" for r in again)              # handed to a different person
    assert dump(store, "progress")["progress"]["summary"]["learned"] == 1
    assert len(rows) == len(set(rows))                                  # ids unique by construction


# ---------------------------------------------------------------- 4. race: marked learned during the run

def test_release_row_leaves_a_row_marked_done_meanwhile(store, order):
    seed3(store)
    go(store, WEEK1, order)
    rid = sorted(rows_of(store))[0]
    store.db.collection("assignments").document(rid).update({"doneAt": datetime.now(timezone.utc)})
    assert store.release_row(rid) is False
    assert rows_of(store)[rid]["releasedAt"] is None
    other = sorted(r for r, d in rows_of(store).items() if not d["doneAt"])[0]
    assert store.release_row(other) is True
    first_release = rows_of(store)[other]["releasedAt"]
    assert store.release_row(other) is True                              # idempotent: already released is not "learned"
    assert rows_of(store)[other]["releasedAt"] == first_release          # and the time is not rewritten
    assert store.release_row("no_such_row") is True                      # gone: nothing left to free (False means done)


# ---------------------------------------------------------------- 5. delete request

def test_delete_request_removes_account_and_record_but_keeps_learned(store, order):
    seed3(store)
    go(store, WEEK1, order)
    mine = sorted(rid for rid, r in rows_of(store).items() if r["uid"] == "pb")
    done_story = rows_of(store)[mine[0]]["storyId"]
    open_stories = {rows_of(store)[rid]["storyId"] for rid in mine[1:]}
    store.db.collection("assignments").document(mine[0]).update({"doneAt": datetime.now(timezone.utc)})
    go(store, WEEK1, order)
    assert dump(store, "progress")["progress"]["summary"]["learned"] == 1
    total_rows = len(rows_of(store))

    store.db.collection("users").document("pb").update({"deleteRequested": True})
    counts = go(store, WEEK1, order)
    assert counts["deleted"] == 1 and counts["deleteFailed"] == 0
    assert not auth_exists("pb") and auth_exists("pa")
    assert not store.db.collection("users").document("pb").get().exists
    rows = rows_of(store)
    assert len(rows) == total_rows                                      # copied, not lost
    assert not any("pb" in rid for rid in rows)                         # no row id carries the uid any more ...
    assert all(r["uid"] != "pb" for r in rows.values())                 # ... and no field does
    anon = {rid: r for rid, r in rows.items() if r["uid"] == ""}
    assert len(anon) == len(mine)
    for rid in anon:
        assert re.fullmatch(r"1_deleted-[0-9a-f]{12}_.+", rid)
    kept = next(r for r in anon.values() if r["storyId"] == done_story)
    assert kept["doneAt"] is not None and kept["releasedAt"] is None    # the learned one stays learned
    assert all(r["releasedAt"] is not None for r in anon.values() if r["storyId"] in open_stories)  # open ones go back
    summary = dump(store, "progress")["progress"]["summary"]
    assert summary["learned"] == 1 and summary["joined"] == 2
    go(store, WEEK1, order)                                              # and a second pass is quiet
    assert dump(store, "progress")["progress"]["summary"]["learned"] == 1
    assert len(rows_of(store)) == total_rows


def test_delete_person_is_safe_to_repeat_after_a_crash_midway(store, order):
    seed3(store)
    go(store, WEEK1, order)
    mine = sorted(rid for rid, r in rows_of(store).items() if r["uid"] == "pb")
    n = len(mine)
    store.delete_person("pb")                                            # the whole thing ...
    after_first = rows_of(store)
    assert len(after_first) == len(rows_of(store)) and not any(r["uid"] == "pb" for r in after_first.values())
    # ... then pretend it crashed before the user record went: the account and record are gone already, so redo
    # the user record and the call must find nothing left to copy and not duplicate anything
    store.db.collection("users").document("pb").set({"minutesPerWeek": 30, "deleteRequested": True,
                                                     "createdAt": datetime(2026, 11, 20, tzinfo=timezone.utc)})
    store.delete_person("pb")
    assert rows_of(store) == after_first
    assert len([r for r in after_first.values() if r["uid"] == ""]) == n


# ---------------------------------------------------------------- 6. stop

def test_stopping_releases_open_rows_and_hands_out_nothing_more(store, order):
    seed3(store)
    go(store, WEEK1, order)
    store.db.collection("users").document("pc").update({"minutesPerWeek": 0})
    counts = go(store, date(2026, 12, 8), order)                         # not a hand-out day (already handed out)
    assert counts["released"] >= 1
    rows = rows_of(store)
    assert all(r["releasedAt"] is not None for r in rows.values() if r["uid"] == "pc")
    before = len(rows)
    for rid, r in rows.items():                                          # the others read everything, so have room again
        if r["uid"] in ("pa", "pb"):
            store.db.collection("assignments").document(rid).update({"doneAt": datetime.now(timezone.utc)})
    go(store, WEEK2, order)
    assert not [r for r in rows_of(store).values() if r["uid"] == "pc" and r["week"] == 2]
    assert len(rows_of(store)) > before                                  # the others still got week 2
    assert store.db.collection("users").document("pc").get().exists      # stopping is not deleting


# ---------------------------------------------------------------- reads per run

def test_reads_per_quiet_run_are_users_plus_summary_plus_current_round_and_open_rows(store, order):
    seed3(store)
    go(store, WEEK1, order)
    all_rows = rows_of(store)
    before = store.reads
    counts = go(store, date(2026, 12, 8), order)                         # a quiet day in an already-finished week
    # users + summary + (round >= 1 rows, and then the open rows AGAIN: the two queries overlap) + the run doc
    open_rows = [r for r in all_rows.values() if not r["doneAt"] and not r["releasedAt"]]
    assert store.reads - before == 3 + 1 + len(all_rows) + len(open_rows) + 1
    assert counts["reads"] == store.reads - before                  # the counts line carries this run's reads


def test_old_complete_rounds_are_not_read_but_open_rows_always_are(store, order):
    seed3(store)
    for i, s in enumerate(order):                                        # round 1 complete
        store.db.collection("assignments").document(f"0_x{i}_{s.id}").set(
            {"uid": f"x{i}", "storyId": s.id, "round": 1, "week": 1, "doneAt": datetime(2026, 12, 1, tzinfo=timezone.utc),
             "releasedAt": None, "assignedAt": datetime(2026, 12, 1, tzinfo=timezone.utc)})
    store.db.collection("assignments").document("0_stray_open").set(       # an open row left over in round 1
        {"uid": "stray", "storyId": order[0].id, "round": 1, "week": 1, "doneAt": None, "releasedAt": None})
    store.db.collection("assignments").document("0_old_released").set(
        {"uid": "old", "storyId": order[0].id, "round": 1, "week": 1, "doneAt": None,
         "releasedAt": datetime(2026, 12, 1, tzinfo=timezone.utc)})
    store.db.collection("assignments").document("0_r2").set(
        {"uid": "y", "storyId": order[0].id, "round": 2, "week": 2,
         "doneAt": datetime(2026, 12, 2, tzinfo=timezone.utc), "releasedAt": None})
    ids = {r["id"] for r in store.assignments(2)}
    assert ids == {"0_stray_open", "0_r2"}
    assert len(store.assignments(1)) == len(order) + 3                   # from round 1: everything, merged by id
    # the runner reads the summary's round
    store.db.collection("progress").document("summary").set({"round": 2})
    store.reads = 0
    go(store, WEEK1, order)
    assert store.reads < len(order)                                      # never the 18 complete-round rows


def test_write_rows_is_one_batch_per_person_and_never_overwrites(store, order):
    seed3(store)
    rows = [{"id": f"1_pa_{order[i].id}", "uid": "pa", "storyId": order[i].id, "round": 1, "week": 1,
             "doneAt": None, "releasedAt": None} for i in range(3)]
    rows += [{"id": f"1_pb_{order[3].id}", "uid": "pb", "storyId": order[3].id, "round": 1, "week": 1,
              "doneAt": None, "releasedAt": None}]
    store.db.collection("assignments").document(rows[1]["id"]).set({**{k: v for k, v in rows[1].items() if k != "id"},
                                                                     "doneAt": datetime(2026, 12, 2, tzinfo=timezone.utc)})
    store.write_rows(rows)
    got = rows_of(store)
    assert got[rows[1]["id"]]["doneAt"] is not None                      # the existing row was not overwritten
    assert rows[0]["id"] not in got and rows[2]["id"] not in got         # pa's batch failed as a whole: all or nothing
    assert rows[3]["id"] in got                                          # pb's batch went through on its own


def test_previous_finished_at_walks_back_a_few_weeks_only(store):
    db = store.db.collection("runs")
    db.document("1").set({"finishedAt": datetime(2026, 12, 6, tzinfo=timezone.utc)})
    db.document("3").set({"startedAt": datetime(2026, 12, 20, tzinfo=timezone.utc)})       # started, never finished
    db.document("9").set({"finishedAt": datetime(2027, 2, 7, tzinfo=timezone.utc)})
    assert store.previous_finished_at(4) == datetime(2026, 12, 6, tzinfo=timezone.utc)      # skips the unfinished week 3
    assert store.previous_finished_at(7) is None                                            # week 1 is too far back
    store.reads = 0
    store.previous_finished_at(7)
    assert store.reads <= 4


def test_set_paused_clears_lapses_and_update_user_writes_only_what_it_is_given(store):
    seed_person(store, "pa", 30, 1, lapses=[1, 4], lastLearnedWeek=0)
    store.set_paused("pa", True)
    u = store.db.collection("users").document("pa").get().to_dict()
    assert isinstance(u["pausedAt"], datetime) and u["lapses"] == [] and u["minutesPerWeek"] == 30
    store.set_paused("pa", False)
    store.update_user("pa", {"lastLearnedWeek": 3})
    u = store.db.collection("users").document("pa").get().to_dict()
    assert u["pausedAt"] is None and u["lastLearnedWeek"] == 3 and u["lapses"] == []


# ---------------------------------------------------------------- 7 and 8: the command line

# ---------------------------------------------------------------- the email step (plan step e)

def test_sent_records_are_claimed_once_listed_by_week_and_can_be_given_back(store):
    assert store.claim_sent("3_pa", "pa", 3) is True
    assert store.claim_sent("3_pa", "pa", 3) is False               # the second claim loses: no double send
    assert store.claim_sent("pause-3_pb", "pb") is True             # not a weekly email: no week on it
    assert store.claim_sent("4_pa", "pa", 4) is True
    assert store.sent_keys(3) == {"3_pa"} and store.sent_keys(4) == {"4_pa"} and store.sent_keys(9) == set()
    store.unclaim_sent("3_pa")
    assert store.sent_keys(3) == set() and store.claim_sent("3_pa", "pa", 3) is True


def test_contacts_come_from_the_sign_in_system_and_skip_people_who_cannot_be_emailed(store):
    seed_person(store, "pa", 30, 1)
    fb_auth.update_user("pa", display_name="Pa Cohen")
    fb_auth.create_user(uid="noemail")
    fb_auth.create_user(uid="off", email="off@example.com", disabled=True)
    many = [fb_auth.create_user(uid=f"m{i}", email=f"m{i}@example.com").uid for i in range(105)]   # over one call's 100
    found = store.contacts(["pa", "noemail", "off", "ghost"] + many)
    assert found["pa"] == ("pa@example.com", "Pa Cohen")
    assert "noemail" not in found and "off" not in found and "ghost" not in found
    assert all(found[uid] == (f"{uid}@example.com", "") for uid in many)


def test_a_week_with_email_on_sends_once_writes_codes_and_marks_the_week_done(store, order):
    import septimus_email as E
    uids, sent = seed3(store), []

    def post(payload, key):
        sent.append((payload["to"][0], key, payload.get("headers")))
        return 200, {"id": "x"}, {}

    mailer = E.Mailer(E.Settings("re_test", "S <s@mail.example>", "https://site.example"), post=post)
    details = E.load_story_details(FIX)
    first = go(store, WEEK1, order, mailer=mailer, story_details=details)
    again = go(store, WEEK1, order, mailer=mailer, story_details=details)
    assert first["emailSent"] == 3 and again["emailSent"] == 0 and len(sent) == 3
    assert {to for to, _, _ in sent} == {f"{u}@example.com" for u in uids}
    users = dump(store, "users")["users"]
    for to, key, headers in sent:
        uid = to.split("@")[0]
        assert key == f"septimus-1_{uid}" and len(users[uid]["mailToken"]) >= 20
        assert headers["List-Unsubscribe"] == f"<https://site.example/api/unsubscribe?u={uid}&t={users[uid]['mailToken']}>"
    runs = dump(store, "runs")["runs"]
    assert runs["1"]["emailsDone"] is True and runs["1"]["finishedAt"]
    assert set(dump(store, "sent")["sent"]) == {f"1_{u}" for u in uids}


def test_delete_my_data_also_removes_the_persons_email_records(store, order):
    seed3(store)
    go(store, WEEK1, order)
    assert store.claim_sent("1_pa", "pa", 1) and store.claim_sent("pause-1_pa", "pa") and store.claim_sent("1_pb", "pb", 1)
    store.delete_person("pa")
    assert set(dump(store, "sent")["sent"]) == {"1_pb"}


def _cli_env(**extra):
    env = {k: v for k, v in os.environ.items()
           if k not in ("FIREBASE_SERVICE_ACCOUNT", "GOOGLE_APPLICATION_CREDENTIALS",
                        "FIRESTORE_EMULATOR_HOST", "FIREBASE_AUTH_EMULATOR_HOST")}
    env.update(extra)
    return env


def _temp_config(tmp_path):
    p = tmp_path / "config.js"
    p.write_text('window.SEPTIMUS_CONFIG = {\n  firebase: { projectId: "%s" },\n  signup: {\n'
                 '    wpm: 75,\n    launchDate: "2026-12-06",\n    yahrzeit: "2027-09-10",\n    maxMinutes: 120\n  }\n};\n'
                 % PROJECT)
    return p


def _everything(store):
    d = dump(store, "users", "assignments", "runs", "progress", "sent")
    d["auth"] = sorted(u.uid for u in fb_auth.list_users().iterate_all())
    return d


def test_dry_run_from_the_command_line_writes_nothing(store, order, tmp_path):
    seed3(store)
    seed_person(store, "pd", 30, 4, deleteRequested=True)
    before = _everything(store)
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "septimus_weekly.py"), "--dry-run", "--date", "2026-12-07",
         "--config", str(_temp_config(tmp_path)), "--data-dir", str(FIX)],
        capture_output=True, text=True, timeout=120, env=_cli_env(**EMU_ENV))
    assert out.returncode == 0, out.stdout + out.stderr
    counts = json.loads(out.stdout.strip().splitlines()[-1])
    assert counts["handedOut"] > 0 and counts["deleted"] == 1 and counts["week"] == 1
    assert _everything(store) == before                                  # no row, run, summary, user or account moved
    assert auth_exists("pd")


def test_real_run_from_the_command_line_does_the_job(store, order, tmp_path):
    seed3(store)
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "septimus_weekly.py"), "--date", "2026-12-07",
         "--config", str(_temp_config(tmp_path)), "--data-dir", str(FIX)],
        capture_output=True, text=True, timeout=120, env=_cli_env(**EMU_ENV))
    assert out.returncode == 0, out.stdout + out.stderr
    assert len(rows_of(store)) == json.loads(out.stdout.strip().splitlines()[-1])["handedOut"] > 0


def test_a_test_start_date_works_on_a_test_project_from_the_command_line(store, order, tmp_path):
    """--launch-date lets staging try a hand-out before the real date is in config.js (none is set here)."""
    seed3(store)
    no_date = tmp_path / "no-date.js"
    no_date.write_text(_temp_config(tmp_path).read_text().replace('launchDate: "2026-12-06"', 'launchDate: ""'))
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "septimus_weekly.py"), "--date", "2026-12-06",
                        "--launch-date", "2026-12-06", "--config", str(no_date), "--data-dir", str(FIX)],
                       capture_output=True, text=True, env=_cli_env(**EMU_ENV), timeout=120)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    assert json.loads(r.stdout.strip().splitlines()[-1])["handedOut"] > 0
    not_sunday = subprocess.run([sys.executable, str(ROOT / "scripts" / "septimus_weekly.py"), "--launch-date",
                                 "2026-12-07", "--data-dir", str(FIX)], capture_output=True, text=True,
                                env=_cli_env(**EMU_ENV), timeout=120)
    assert not_sunday.returncode == 1


def test_without_the_secret_or_an_emulator_it_fails_clearly_and_early(tmp_path):
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "septimus_weekly.py"), "--dry-run", "--date", "2026-12-07",
         "--config", str(_temp_config(tmp_path)), "--data-dir", str(FIX)],
        capture_output=True, text=True, timeout=60, env=_cli_env())
    assert out.returncode != 0
    assert "FIREBASE_SERVICE_ACCOUNT" in out.stdout + out.stderr
    assert "PRIVATE KEY" not in out.stdout + out.stderr and "private_key" not in out.stdout + out.stderr
    assert "handedOut" not in out.stdout                                 # never got as far as the job
