"""Load test of the weekly script against the STAGING Firebase project (docs/technical/septimus-staging.md).

Adds 300 pretend people (records only, no sign-in accounts), runs the weekly script for four more pretend weeks the
way the GitHub Action would, plays the people between runs, and reports how long each run took and how many
database reads it used. Then removes the pretend people and their rows again.

Run by hand, with a virtualenv that has requirements-septimus.txt installed:
    python scripts/staging_load_test.py            # add --keep to leave the pretend people on staging
It needs the staging key at ~/keys/ (KEY below) and refuses to run against anything but septimus-stories-staging.
The free plan allows 50,000 reads and 20,000 writes a day; this test is sized to stay well under both.
"""
import datetime as dt
import json
import os
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore

REPO = Path(__file__).resolve().parent.parent
KEY = Path.home() / "keys/septimus-stories-staging-firebase-adminsdk-fbsvc-79363ae1db.json"
CONFIG = Path(tempfile.gettempdir()) / "septimus-staging-test-config.js"
LAUNCH = dt.date(2026, 11, 8)          # the same pretend launch Sunday the multi-week test used
PEOPLE = 300
WEEKS = 4
PREFIX = "load-"

info = json.loads(KEY.read_text())
assert info["project_id"] == "septimus-stories-staging", "this test only runs on staging"
firebase_admin.initialize_app(credentials.Certificate(info))
db = firestore.client()


def batched(items, size=400):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def run_script(day):
    env = dict(os.environ, FIREBASE_SERVICE_ACCOUNT=KEY.read_text())
    env.pop("FIRESTORE_EMULATOR_HOST", None)
    env.pop("FIREBASE_AUTH_EMULATOR_HOST", None)
    start = time.time()
    out = subprocess.run([sys.executable, str(REPO / "scripts/septimus_weekly.py"), "--date", day.isoformat(),
                          "--config", str(CONFIG)], capture_output=True, text=True, env=env, cwd=str(REPO))
    if out.returncode != 0:
        print(out.stdout[-1500:], out.stderr[-1500:])
        raise SystemExit("the weekly script failed")
    assert "septimus-stories-staging" in out.stdout + out.stderr
    counts = json.loads([l for l in out.stdout.splitlines() if l.startswith("{")][-1])
    return counts, time.time() - start


def main():
    keep = "--keep" in sys.argv
    random.seed(7)
    text = (REPO / "site/config.js").read_text().replace('launchDate: ""', 'launchDate: "%s"' % LAUNCH.isoformat())
    assert LAUNCH.isoformat() in text
    CONFIG.write_text(text)

    last_run = max(int(d.id) for d in db.collection("runs").stream())
    print("staging is at pretend week %d; adding %d people" % (last_run, PEOPLE))

    # Minutes as real sign-ups are likely to choose them; how each person behaves.
    people = {}
    for i in range(PEOPLE):
        uid = "%s%03d" % (PREFIX, i)
        mins = random.choices([5, 10, 15, 30, 60], weights=[25, 40, 20, 12, 3])[0]
        habit = random.choices(["all", "half", "none"], weights=[60, 25, 15])[0]
        people[uid] = (mins, habit)
    for chunk in batched(list(people.items())):
        b = db.batch()
        for uid, (mins, _) in chunk:
            b.set(db.collection("users").document(uid), {"createdAt": firestore.SERVER_TIMESTAMP, "minutesPerWeek": mins,
                                                           "src": "", "deleteRequested": False})
        b.commit()
    print("  total minutes a week pledged: %d" % sum(m for m, _ in people.values()))

    results = []
    for n in range(1, WEEKS + 1):
        week = last_run + n
        day = LAUNCH + dt.timedelta(days=7 * (week - 1))
        counts, secs = run_script(day)
        new = [d for d in db.collection("assignments").where("week", "==", week).stream()]
        per_person = {}
        for d in new:
            per_person.setdefault(d.get("uid"), []).append(d)
        results.append((week, counts, secs, len(new)))
        print("week %d: %d stories to %d people in %.0f s; released %d, paused %d; reads %d" % (
            week, counts["handedOut"], len(per_person), secs, counts["released"], counts["paused"], counts["reads"]))
        # People read: "all" marks everything, "half" every other story, "none" nothing.
        to_mark = []
        for uid, docs in per_person.items():
            habit = people.get(uid, (0, "all"))[1] if uid.startswith(PREFIX) else "none"
            if habit == "all":
                to_mark += docs
            elif habit == "half":
                to_mark += docs[::2]
        for chunk in batched(to_mark):
            b = db.batch()
            for d in chunk:
                b.update(d.reference, {"doneAt": firestore.SERVER_TIMESTAMP})
            b.commit()

    again, secs = run_script(LAUNCH + dt.timedelta(days=7 * (last_run + WEEKS - 1)))
    print("same week again: handed out %d (must be 0), %.0f s, reads %d  <- an ordinary daily run" % (
        again["handedOut"], secs, again["reads"]))
    summary = db.collection("progress").document("summary").get().to_dict()
    print("public summary: learned %s, joined %s, week %s" % (summary.get("learned"), summary.get("joined"), summary.get("week")))

    worst = max(r[1]["reads"] for r in results)
    print("\nlargest hand-out run: %d reads (free limit 50,000 a day); slowest run %.0f s (the job allows 15 minutes)" % (
        worst, max(r[2] for r in results)))

    if not keep:
        print("removing the pretend people and their rows")
        refs = [d.reference for d in db.collection("assignments").stream() if str(d.get("uid")).startswith(PREFIX)]
        refs += [db.collection("users").document(uid) for uid in people]
        for chunk in batched(refs):
            b = db.batch()
            for r in chunk:
                b.delete(r)
            b.commit()
        counts, _ = run_script(LAUNCH + dt.timedelta(days=7 * (last_run + WEEKS - 1)))     # refresh the public totals
        print("removed %d documents; staging back to %d people" % (len(refs), counts["users"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
