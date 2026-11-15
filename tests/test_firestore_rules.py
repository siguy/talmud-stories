"""Tests for firestore.rules, run against the local Firestore emulator.

Needs `firebase` (firebase-tools) and a working `java` on PATH. If either is missing, or
port 8080 is already taken, the whole module is skipped with a reason (or fails, when
REQUIRE_RULES_TESTS=1 is set).

Conventions (checked against the emulator):
  signed-in person   Authorization: Bearer <unsigned JWT with sub = uid>
  the weekly script  Authorization: Bearer owner   (bypasses rules)
  signed out         no Authorization header
"""
import base64
import json
import os
import shutil
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.request

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = "demo-septimus"
HOST = "http://localhost:8080"
DOCS = f"{HOST}/v1/projects/{PROJECT}/databases/(default)/documents"
SCRIPT = "owner"  # Admin-level token: bypasses rules like the weekly script


# ---------- emulator lifecycle ----------

def _port_open(port=8080):
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _java_works():
    """macOS ships a /usr/bin/java stub that exists but does not run, so run it."""
    try:
        return subprocess.run(["java", "-version"], capture_output=True, timeout=10).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _skip(reason):
    """Skip, unless REQUIRE_RULES_TESTS=1 (CI): then not testing the rules is a failure."""
    if os.environ.get("REQUIRE_RULES_TESTS") == "1":
        pytest.fail("REQUIRE_RULES_TESTS=1 but the rules tests cannot run: " + reason)
    pytest.skip(reason)


@pytest.fixture(scope="module", autouse=True)
def emulator():
    if not shutil.which("firebase"):
        _skip("firebase CLI is needed to run the Firestore emulator")
    if not _java_works():
        _skip("no working Java runtime: the Firestore emulator needs one (brew install openjdk)")
    if _port_open(8080):
        _skip("port 8080 is already in use by something else")
    proc = subprocess.Popen(
        ["firebase", "emulators:start", "--only", "firestore", "--project", PROJECT],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,  # own process group, so we can kill the Java child
    )
    try:
        deadline = time.time() + 90
        while time.time() < deadline:
            if proc.poll() is not None:
                _skip("firebase emulator exited during start-up")
            if _port_open(8080):
                break
            time.sleep(0.5)
        else:
            _skip("firebase emulator did not start within 90 seconds")
        yield
    finally:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=15)
        except Exception:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                pass


@pytest.fixture(autouse=True)
def clean_db(emulator):
    _http("DELETE", f"{HOST}/emulator/v1/projects/{PROJECT}/databases/(default)/documents")
    yield


# ---------- low-level http ----------

def _b64(d):
    return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()


def token(uid):
    now = int(time.time())
    header = {"alg": "none", "typ": "JWT"}
    payload = {
        "sub": uid, "user_id": uid,
        "iss": f"https://securetoken.google.com/{PROJECT}", "aud": PROJECT,
        "iat": now, "exp": now + 3600, "auth_time": now,
        "firebase": {"sign_in_provider": "google.com", "identities": {}},
    }
    return f"{_b64(header)}.{_b64(payload)}."


def _http(method, url, body=None, as_uid=None):
    """as_uid: None = signed out, SCRIPT = script, else that person."""
    headers = {"Content-Type": "application/json"}
    if as_uid == SCRIPT:
        headers["Authorization"] = "Bearer owner"
    elif as_uid is not None:
        headers["Authorization"] = "Bearer " + token(as_uid)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


# ---------- value helpers ----------

def val(v):
    """Python value -> Firestore REST value."""
    if v is None:
        return {"nullValue": None}
    if isinstance(v, bool):
        return {"booleanValue": v}
    if isinstance(v, int):
        return {"integerValue": str(v)}
    if isinstance(v, float):
        return {"doubleValue": v}
    if isinstance(v, str):
        return {"stringValue": v}
    raise TypeError(v)


def ts(iso):
    return {"timestampValue": iso}


def fields(d):
    return {k: (v if isinstance(v, dict) else val(v)) for k, v in d.items()}


def commit(path, as_uid, set_fields=None, server_time=(), exists=None,
           update_mask=None, delete=False):
    """One write via :commit so that server-time fields are possible."""
    name = f"projects/{PROJECT}/databases/(default)/documents/{path}"
    write = {}
    if delete:
        write["delete"] = name
    else:
        write["update"] = {"name": name, "fields": fields(set_fields or {})}
        if update_mask is not None:
            write["updateMask"] = {"fieldPaths": update_mask}
        if server_time:
            write["updateTransforms"] = [
                {"fieldPath": f, "setToServerValue": "REQUEST_TIME"} for f in server_time]
    if exists is not None:
        write["currentDocument"] = {"exists": exists}
    code, _ = _http("POST", f"{DOCS}:commit", {"writes": [write]}, as_uid)
    return code


def ok(code):
    return code == 200


def denied(code):
    return code == 403


# ---------- domain helpers ----------

def create_user(uid, as_uid=None, minutes=10, src="hadar", delete_requested=False,
                created_at="server", extra=None):
    as_uid = uid if as_uid is None else as_uid
    f = {"minutesPerWeek": minutes, "src": src, "deleteRequested": delete_requested}
    server_time = ()
    if created_at == "server":
        server_time = ("createdAt",)
    elif created_at is not None:
        f["createdAt"] = ts(created_at)
    f.update(extra or {})
    return commit(f"users/{uid}", as_uid, f, server_time=server_time, exists=False)


def seed_user(uid, minutes=10, src="hadar"):
    assert ok(create_user(uid, SCRIPT, minutes, src))


def update_user(uid, as_uid, set_fields, server_time=()):
    return commit(f"users/{uid}", as_uid, set_fields, server_time=server_time,
                  exists=True, update_mask=list(set_fields) + list(server_time))


def get_doc(path, as_uid):
    return _http("GET", f"{DOCS}/{path}", as_uid=as_uid)[0]


def list_docs(collection, as_uid):
    return _http("GET", f"{DOCS}/{collection}", as_uid=as_uid)[0]


def seed_assignment(row_id="1_alice_s1", uid="alice", story="s1", done=None):
    f = {"uid": uid, "storyId": story, "round": 1, "week": 1,
         "assignedAt": ts("2026-11-01T00:00:00Z"),
         "doneAt": ts(done) if done else None, "releasedAt": None}
    assert ok(commit(f"assignments/{row_id}", SCRIPT, f))


def set_done(row_id, as_uid, when="server"):
    if when == "server":
        return commit(f"assignments/{row_id}", as_uid, {}, server_time=("doneAt",),
                      exists=True, update_mask=["doneAt"])
    if when is None:
        return commit(f"assignments/{row_id}", as_uid, {"doneAt": None},
                      exists=True, update_mask=["doneAt"])
    return commit(f"assignments/{row_id}", as_uid, {"doneAt": ts(when)},
                  exists=True, update_mask=["doneAt"])


def query_assignments(as_uid, uid_filter=None):
    q = {"from": [{"collectionId": "assignments"}]}
    if uid_filter is not None:
        q["where"] = {"fieldFilter": {"field": {"fieldPath": "uid"}, "op": "EQUAL",
                                      "value": {"stringValue": uid_filter}}}
    return _http("POST", f"{DOCS}:runQuery", {"structuredQuery": q}, as_uid)[0]


# ---------- sanity: the two auth conventions work ----------

def test_script_bypasses_rules_and_signed_out_does_not():
    assert ok(create_user("alice", SCRIPT, minutes=500))  # would break the rules
    assert denied(get_doc("users/alice", None))
    assert ok(get_doc("users/alice", SCRIPT))


# ---------- users: create ----------

def test_user_owner_creates_valid_record():
    assert ok(create_user("alice"))


@pytest.mark.parametrize("minutes", [0, 121, 10.5, "10"])
def test_user_create_bad_minutes_denied(minutes):
    assert denied(create_user("alice", minutes=minutes))


@pytest.mark.parametrize("src", ["Hadar!", "a" * 33])
def test_user_create_bad_src_denied(src):
    assert denied(create_user("alice", src=src))


def test_user_create_empty_src_allowed():
    assert ok(create_user("alice", src=""))


def test_user_create_client_supplied_created_at_denied():
    assert denied(create_user("alice", created_at="2020-01-01T00:00:00Z"))


def test_user_create_missing_created_at_denied():
    assert denied(create_user("alice", created_at=None))


@pytest.mark.parametrize("extra", [{"pausedAt": None}, {"email": "a@b.c"}])
def test_user_create_extra_field_denied(extra):
    assert denied(create_user("alice", extra=extra))


def test_user_create_delete_requested_true_denied():
    assert denied(create_user("alice", delete_requested=True))


def test_user_create_someone_elses_record_denied():
    assert denied(create_user("alice", as_uid="mallory"))


def test_user_signed_out_create_denied():
    assert denied(commit("users/alice", None, {"minutesPerWeek": 10, "src": "",
                                               "deleteRequested": False},
                         server_time=("createdAt",), exists=False))


# ---------- users: read ----------

def test_user_owner_reads_own():
    seed_user("alice")
    assert ok(get_doc("users/alice", "alice"))


def test_user_reads_another_denied():
    seed_user("alice")
    assert denied(get_doc("users/alice", "mallory"))


def test_user_list_denied():
    seed_user("alice")
    assert denied(list_docs("users", "alice"))


# ---------- users: update / delete ----------

@pytest.mark.parametrize("minutes", [0, 30])
def test_user_owner_updates_minutes_allowed(minutes):
    seed_user("alice")
    assert ok(update_user("alice", "alice", {"minutesPerWeek": minutes}))


def test_user_owner_updates_minutes_to_121_denied():
    seed_user("alice")
    assert denied(update_user("alice", "alice", {"minutesPerWeek": 121}))


@pytest.mark.parametrize("minutes", [-1, 10.5, "10"])
def test_user_owner_updates_minutes_bad_value_denied(minutes):
    seed_user("alice")
    assert denied(update_user("alice", "alice", {"minutesPerWeek": minutes}))


def test_user_owner_sets_delete_requested_non_bool_denied():
    seed_user("alice")
    assert denied(update_user("alice", "alice", {"deleteRequested": "yes"}))


def test_user_owner_sets_delete_requested_allowed():
    seed_user("alice")
    assert ok(update_user("alice", "alice", {"deleteRequested": True}))


def test_user_owner_changes_src_denied():
    seed_user("alice")
    assert denied(update_user("alice", "alice", {"src": "other"}))


def test_user_owner_changes_created_at_denied():
    seed_user("alice")
    assert denied(update_user("alice", "alice", {}, server_time=("createdAt",)))


def test_user_owner_adds_paused_at_denied():
    seed_user("alice")
    assert denied(update_user("alice", "alice", {"pausedAt": ts("2026-11-02T00:00:00Z")}))


def seed_paused_user(uid):
    """A person the weekly script has paused: pausedAt set, plus the script's own everLearned / lapses."""
    f = {"minutesPerWeek": 10, "src": "hadar", "deleteRequested": False, "pausedAt": ts("2026-11-02T00:00:00Z"),
         "everLearned": False, "lapses": {"arrayValue": {"values": [{"integerValue": "1"}, {"integerValue": "4"}]}}}
    assert ok(commit(f"users/{uid}", SCRIPT, f, server_time=("createdAt",)))


def test_user_owner_clears_paused_at_allowed():
    seed_paused_user("alice")
    assert ok(update_user("alice", "alice", {"pausedAt": None}))


def test_user_owner_sets_paused_at_on_a_person_not_paused_denied():
    seed_user("alice")
    assert denied(update_user("alice", "alice", {"pausedAt": ts("2026-12-01T00:00:00Z")}))


def test_user_owner_moves_paused_at_to_a_new_time_denied():
    seed_paused_user("alice")
    assert denied(update_user("alice", "alice", {"pausedAt": ts("2026-12-01T00:00:00Z")}))


def test_user_owner_clears_pause_and_changes_minutes_together_allowed():
    seed_paused_user("alice")
    assert ok(update_user("alice", "alice", {"pausedAt": None, "minutesPerWeek": 20}))


def test_user_owner_writes_ever_learned_or_lapses_denied():
    seed_paused_user("alice")
    assert denied(update_user("alice", "alice", {"everLearned": True}))
    assert denied(update_user("alice", "alice", {"lapses": {"arrayValue": {"values": []}}}))
    assert denied(update_user("alice", "alice", {"pausedAt": None, "everLearned": True}))


def test_user_other_person_update_denied():
    seed_user("alice")
    assert denied(update_user("alice", "mallory", {"minutesPerWeek": 5}))


def test_user_owner_delete_denied():
    seed_user("alice")
    assert denied(commit("users/alice", "alice", delete=True))


# ---------- assignments ----------

def test_assignment_owner_reads_own_row():
    seed_assignment()
    assert ok(get_doc("assignments/1_alice_s1", "alice"))


def test_assignment_other_person_reads_denied():
    seed_assignment()
    assert denied(get_doc("assignments/1_alice_s1", "mallory"))


def test_assignment_owner_lists_with_uid_filter_allowed():
    seed_assignment()
    assert ok(query_assignments("alice", uid_filter="alice"))


def test_assignment_list_without_filter_denied():
    seed_assignment()
    assert denied(query_assignments("alice"))


def test_assignment_list_filtered_on_someone_else_denied():
    seed_assignment()
    assert denied(query_assignments("mallory", uid_filter="alice"))


def test_assignment_owner_sets_done_to_server_time_allowed():
    seed_assignment()
    assert ok(set_done("1_alice_s1", "alice"))


def test_assignment_owner_sets_done_back_to_null_allowed():
    seed_assignment(done="2026-11-05T00:00:00Z")
    assert ok(set_done("1_alice_s1", "alice", when=None))


def test_assignment_owner_sets_done_to_client_time_denied():
    seed_assignment()
    assert denied(set_done("1_alice_s1", "alice", when="2026-11-05T00:00:00Z"))


def test_assignment_other_person_sets_done_denied():
    seed_assignment()
    assert denied(set_done("1_alice_s1", "mallory"))


@pytest.mark.parametrize("field,value", [("storyId", "s2"), ("uid", "mallory")])
def test_assignment_owner_changes_other_field_denied(field, value):
    seed_assignment()
    code = commit("assignments/1_alice_s1", "alice", {field: value},
                  exists=True, update_mask=[field])
    assert denied(code)


def test_assignment_owner_creates_row_denied():
    f = {"uid": "alice", "storyId": "s9", "round": 1, "week": 1, "doneAt": None}
    assert denied(commit("assignments/1_alice_s9", "alice", f, exists=False))


def test_assignment_owner_deletes_row_denied():
    seed_assignment()
    assert denied(commit("assignments/1_alice_s1", "alice", delete=True))


# ---------- progress, runs, sent ----------

def test_progress_signed_out_read_allowed():
    assert ok(commit("progress/summary", SCRIPT, {"learned": 3}))
    assert ok(get_doc("progress/summary", None))


def test_progress_signed_in_write_denied():
    assert denied(commit("progress/summary", "alice", {"learned": 999}))


@pytest.mark.parametrize("path", ["runs/1", "sent/1_alice"])
def test_runs_and_sent_client_access_denied(path):
    assert ok(commit(path, SCRIPT, {"x": 1}))
    assert denied(get_doc(path, "alice"))
    assert denied(commit(path, "alice", {"x": 2}))
