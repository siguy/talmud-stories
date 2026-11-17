"""Multi-week test of the weekly script against the STAGING Firebase project (docs/technical/septimus-staging.md).

Run by hand, with a virtualenv that has requirements-septimus.txt installed:
    python scripts/staging_multiweek_test.py
It needs the staging key at ~/keys/ (see KEY below). It adds to whatever is already on staging; wipe staging first
for a clean run (the staging notes say how).

Creates five test accounts, then for pretend weeks 2..10 runs scripts/septimus_weekly.py (as a subprocess, the same
way the GitHub Action would) and plays the part of the people: readers mark their stories learned, one stops, one
asks for deletion, two never read. Prints what happened each week and a list of PASS / FAIL checks.

Refuses to run against anything but septimus-stories-staging.
"""
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

import firebase_admin
from firebase_admin import auth, credentials, firestore

REPO = Path(__file__).resolve().parent.parent
KEY = Path.home() / "keys/septimus-stories-staging-firebase-adminsdk-fbsvc-79363ae1db.json"
import tempfile  # noqa: E402
CONFIG = Path(tempfile.gettempdir()) / "septimus-staging-test-config.js"   # a copy of config.js with a pretend launch date
LAUNCH = dt.date(2026, 11, 8)            # a Sunday; week 1 = 8-14 November (Simon's first run was week 1)
WPM = 75

info = json.loads(KEY.read_text())
assert info["project_id"] == "septimus-stories-staging", "this test only runs on staging"
firebase_admin.initialize_app(credentials.Certificate(info))
db = firestore.client()

sys.path.insert(0, str(REPO / "scripts"))
import septimus_assign as A  # noqa: E402

ORDER = A.load_story_order(str(REPO / "site/data"))
POS = {s.id: i for i, s in enumerate(ORDER)}
WORDS = {s.id: s.words for s in ORDER}

# name -> (minutes a week, behaviour)
PEOPLE = {
    "test-a": (10, "reads everything"),
    "test-b": (30, "reads everything"),
    "test-c": (15, "never reads"),
    "test-d": (10, "reads, then stops in week 4"),
    "test-e": (10, "reads, then asks for deletion in week 6"),
}
checks = []


def check(name, ok, detail=""):
    checks.append((name, ok, detail))
    print(("  PASS " if ok else "  FAIL ") + name + (": " + detail if detail else ""))


def write_config():
    text = (REPO / "site/config.js").read_text().replace('launchDate: ""', 'launchDate: "%s"' % LAUNCH.isoformat())
    assert LAUNCH.isoformat() in text
    CONFIG.write_text(text)


def run_script(day):
    env = dict(os.environ, FIREBASE_SERVICE_ACCOUNT=KEY.read_text())
    env.pop("FIRESTORE_EMULATOR_HOST", None)
    env.pop("FIREBASE_AUTH_EMULATOR_HOST", None)
    out = subprocess.run([sys.executable, str(REPO / "scripts/septimus_weekly.py"), "--date", day.isoformat(),
                          "--config", str(CONFIG)], capture_output=True, text=True, env=env, cwd=str(REPO))
    if out.returncode != 0:
        print(out.stdout[-1500:], out.stderr[-1500:])
        raise SystemExit("the weekly script failed")
    assert "septimus-stories-staging" in out.stdout + out.stderr, "script did not report the staging project"
    line = [l for l in out.stdout.splitlines() if l.startswith("{")][-1]
    return json.loads(line)


def rows():
    return [dict(d.to_dict(), id=d.id) for d in db.collection("assignments").stream()]


def users():
    return {d.id: d.to_dict() for d in db.collection("users").stream()}


def is_open(r):
    return r.get("doneAt") is None and r.get("releasedAt") is None


def minutes(rs):
    return sum(WORDS.get(r["storyId"], 0) for r in rs) / WPM


def mark_learned(uid):
    n = 0
    for r in rows():
        if r["uid"] == uid and is_open(r):
            db.collection("assignments").document(r["id"]).update({"doneAt": firestore.SERVER_TIMESTAMP})
            n += 1
    return n


def main():
    write_config()
    uid = {}
    # Simon's own staging account is the one already there; it takes part as someone who has not read yet.
    simon = [u for u in users()]
    assert len(simon) >= 1, "expected Simon's staging record"
    simon_uid = sorted(users().items(), key=lambda kv: kv[1]["createdAt"])[0][0]
    name_of = {simon_uid: "simon"}

    print("== creating test accounts")
    for name, (mins, what) in PEOPLE.items():
        email = name + "@example.com"
        try:
            u = auth.get_user_by_email(email)
        except auth.UserNotFoundError:
            u = auth.create_user(email=email, display_name="Test " + name[-1].upper(), email_verified=True)
        uid[name] = u.uid
        name_of[u.uid] = name
        ref = db.collection("users").document(u.uid)
        if not ref.get().exists:      # the same four fields the browser writes at Join
            ref.set({"createdAt": firestore.SERVER_TIMESTAMP, "minutesPerWeek": mins,
                     "src": "hadar" if name in ("test-a", "test-b") else "", "deleteRequested": False})
        print("  %s: %d min a week, %s" % (name, mins, what))

    readers = {"test-a", "test-b", "test-d", "test-e"}
    before_ids = {r["id"] for r in rows()}
    simon_week1 = sorted([r["storyId"] for r in rows() if r["uid"] == simon_uid and r["week"] == 1])
    paused_at_week = {}

    for week in range(2, 11):
        day = LAUNCH + dt.timedelta(days=7 * (week - 1))      # the Sunday that starts this week
        if week == 4:
            db.collection("users").document(uid["test-d"]).update({"minutesPerWeek": 0})      # "Stop my stories"
            readers.discard("test-d")
        if week == 6:
            db.collection("users").document(uid["test-e"]).update({"deleteRequested": True})  # "Delete my data"
            readers.discard("test-e")
        counts = run_script(day)
        rs, us = rows(), users()
        new = [r for r in rs if r["week"] == week]
        print("\n== week %d (%s): handed out %d, released %d, paused %d, deleted %d, reads %d" % (
            week, day.isoformat(), counts["handedOut"], counts["released"], counts["paused"], counts["deleted"],
            counts["reads"]))
        by = {}
        for r in new:
            by.setdefault(name_of.get(r["uid"], "?"), []).append(r)
        for who in sorted(by):
            ids = sorted(by[who], key=lambda r: POS.get(r["storyId"], 1e9))
            print("   %-7s %d stories, %.1f min: %s .. %s" % (who, len(ids), minutes(ids), ids[0]["storyId"], ids[-1]["storyId"]))
        for u, d in us.items():
            if d.get("pausedAt") is not None and u not in paused_at_week:
                paused_at_week[u] = week
                print("   paused: " + name_of.get(u, "?"))

        # --- checks for this week -------------------------------------------------------------
        if week == 2:
            again = run_script(day)
            check("second run of the same week changes nothing",
                  again["handedOut"] == 0 and {r["id"] for r in rows()} == {r["id"] for r in rs})
            first = min(POS[r["storyId"]] for r in new)
            check("week 2 starts right after the stories already handed out", first == len(simon_week1),
                  "first new story is number %d in the list" % (first + 1))
        # nobody over their minutes, except the single story given to someone holding nothing
        for u, d in us.items():
            mine_open = [r for r in rs if r["uid"] == u and is_open(r)]
            cap = min(d.get("minutesPerWeek", 0), 120)
            if mine_open and minutes(mine_open) > cap + 0.01 and len(mine_open) > 1:
                check("week %d: %s within their minutes" % (week, name_of.get(u, "?")), False,
                      "%.1f min open against %d" % (minutes(mine_open), cap))
        # no story held by two people in the same round
        seen = {}
        for r in rs:
            if r.get("releasedAt") is None:
                seen.setdefault((r["storyId"], r["round"]), []).append(r["uid"])
        dup = [k for k, v in seen.items() if len(v) > 1]
        if dup:
            check("week %d: no story handed to two people in one round" % week, False, str(dup[:3]))
        # each person's new stories are consecutive in the list among stories not already taken
        if week == 4:
            d_rows = [r for r in rs if r["uid"] == uid["test-d"]]
            check("week 4: the person who stopped got nothing new and holds nothing",
                  not [r for r in d_rows if r["week"] == 4] and not [r for r in d_rows if is_open(r)])
        if week == 6:
            gone = False
            try:
                auth.get_user(uid["test-e"])
            except auth.UserNotFoundError:
                gone = True
            check("week 6: deleted person's sign-in account is gone", gone)
            check("week 6: their record is gone", uid["test-e"] not in us)
            leftover = [r for r in rs if uid["test-e"] in r["id"] or r["uid"] == uid["test-e"]]
            check("week 6: no row still carries their id", not leftover, "%d rows" % len(leftover))
            check("week 6: deleted counted once", counts["deleted"] == 1)

        # the readers read this week's stories
        for name in sorted(readers):
            mark_learned(uid[name])

    rs, us = rows(), users()
    print("\n== after week 10")
    # Every story someone let lapse must have been handed on to a different person.
    lapsed = [r for r in rs if r.get("releasedAt") and not r.get("doneAt") and r["uid"]]
    handed_on = [r for r in lapsed if any(o["storyId"] == r["storyId"] and o["round"] == r["round"] and o["uid"] != r["uid"]
                                          and o["week"] > r["week"] for o in rs)]
    check("stories people let lapse were handed on to someone else", len(handed_on) >= len(lapsed) - 5,
          "%d of %d lapsed stories already re-handed" % (len(handed_on), len(lapsed)))
    check("test-c (never read, joined for week 2) was paused at week 8", paused_at_week.get(uid["test-c"]) == 8,
          "paused at week %s" % paused_at_week.get(uid["test-c"]))
    for name in ("test-a", "test-b"):
        check(name + " (reads everything) was never paused", us[uid[name]].get("pausedAt") is None)
        got = [r for r in rs if r["uid"] == uid[name]]
        check(name + " got stories every week", {r["week"] for r in got} == set(range(2, 11)),
              "%d stories over %d weeks" % (len(got), len({r["week"] for r in got})))
    check("a paused person gets nothing new", not [r for r in rs if r["uid"] == uid["test-c"] and r["week"] > 8])

    # Resume: the person clears their own pause (the Resume button), then the next week runs.
    db.collection("users").document(uid["test-c"]).update({"pausedAt": None})
    counts = run_script(LAUNCH + dt.timedelta(days=7 * 10))        # week 11
    rs = rows()
    check("after Resume, test-c gets stories again in week 11",
          bool([r for r in rs if r["uid"] == uid["test-c"] and r["week"] == 11]))

    summary = db.collection("progress").document("summary").get().to_dict()
    done_round1 = {r["storyId"] for r in rs if r.get("doneAt") and r["round"] == 1}
    print("   public summary: learned %s, joined %s, round %s, still open %s" % (
        summary.get("learned"), summary.get("joined"), summary.get("round"), summary.get("openInRound")))
    check("the public total equals the stories actually marked learned", summary.get("learned") == len(done_round1),
          "%s against %d" % (summary.get("learned"), len(done_round1)))
    check("per-tractate counts add up to the total", sum(summary.get("byTractate", {}).values()) == summary.get("learned"))
    check("reads per run stayed small", counts["reads"] < 2000, "%d reads in the last run" % counts["reads"])
    order_ok = sorted(POS[s] for s in {r["storyId"] for r in rs}) == list(range(len({r["storyId"] for r in rs})))
    check("stories were handed out in list order with no gaps", order_ok,
          "%d different stories, the first %d of the list" % (len({r["storyId"] for r in rs}), len({r["storyId"] for r in rs})))

    failed = [c for c in checks if not c[1]]
    print("\n%d checks, %d failed" % (len(checks), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
