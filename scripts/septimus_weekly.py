#!/usr/bin/env python3
"""Septimus sign-up: the daily/weekly job. Reads Firestore, calls the pure logic in septimus_assign.py, writes back.

What one run does (plan section 6):
  every run   handle "delete my data" requests, release stories of people who stopped, refresh progress/summary
  hand-out    once per campaign week, on the first day the script runs in that week (so a missed Monday is made
              up the next day): release old stories, pause/unpause, give out new stories, record runs/<week>.

Safe to run twice: runs/<week> marks a finished week, and row ids are fixed (<week>_<uid>_<storyId>).

Usage:
  python3 scripts/septimus_weekly.py              # the real run (needs FIREBASE_SERVICE_ACCOUNT)
  python3 scripts/septimus_weekly.py --dry-run    # read, compute, print; write nothing
  python3 scripts/septimus_weekly.py --date 2026-12-08
Environment: FIREBASE_SERVICE_ACCOUNT (the JSON key, as text), SEPTIMUS_PAUSE=1 (no hand-out),
FIRESTORE_EMULATOR_HOST / FIREBASE_AUTH_EMULATOR_HOST (point at the local emulator instead).
"""
import argparse
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import septimus_assign as A  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CONFIG_JS = ROOT / "site" / "config.js"
DATA_DIR = ROOT / "site" / "data"
LOG = logging.getLogger("septimus_weekly")


# ---------------------------------------------------------------- settings

@dataclass
class Config:
    launch_date: "date | None"   # None = not set yet: no hand-out
    yahrzeit: date
    wpm: int
    max_minutes: int
    project_id: str = "septimus-stories"

    @property
    def last_week(self):
        return A.campaign_week(self.yahrzeit, self.launch_date) if self.launch_date else 0


def parse_config(text):
    """Read launchDate, yahrzeit, wpm, maxMinutes from the `signup` block of site/config.js."""
    m = re.search(r"signup:\s*\{(.*?)\n  \}", text, re.S)
    block = m.group(1) if m else ""

    def grab(pattern, what):
        found = re.search(pattern, block)
        if not found:
            raise ValueError(f"site/config.js signup block has no {what}")
        return found.group(1)

    launch = grab(r'launchDate:\s*"([^"]*)"', "launchDate")
    project = re.search(r'projectId:\s*"([^"]+)"', text)
    return Config(
        launch_date=date.fromisoformat(launch) if launch else None,
        yahrzeit=date.fromisoformat(grab(r'yahrzeit:\s*"([^"]+)"', "yahrzeit")),
        wpm=int(grab(r"\bwpm:\s*(\d+)", "wpm")),
        max_minutes=int(grab(r"maxMinutes:\s*(\d+)", "maxMinutes")),
        project_id=project.group(1) if project else "septimus-stories",
    )


def today_eastern(override=None):
    """Today's date in US Eastern (the hand-out week turns over at midnight there, not in UTC)."""
    if override:
        return date.fromisoformat(override)
    return datetime.now(ZoneInfo("America/New_York")).date()


# ---------------------------------------------------------------- the job

def _apply_delete_locally(uid, users, rows):
    """Mirror Store.delete_person on our in-memory copies so later steps see the same world."""
    users[:] = [u for u in users if u["uid"] != uid]
    for r in rows:
        if r.get("uid") == uid:
            r["uid"] = None
            if A._is_open(r):
                r["releasedAt"] = "released-this-run"


def run(store, today, config, dry_run=False, pause=False, story_order=None, list_version=None):
    """The whole job. Returns the counts dict. `store` is a Store (or a fake with the same methods)."""
    if story_order is None:
        story_order = A.load_story_order(DATA_DIR)
        list_version = A.load_list_version(DATA_DIR)
    users = [dict(u) for u in store.users()]
    rows = [dict(r) for r in store.assignments()]
    LOG.info("read %d users, %d assignment rows, %d stories on the list", len(users), len(rows), len(story_order))

    week = A.campaign_week(today, config.launch_date) if config.launch_date else 0
    counts = {"week": week, "users": 0, "eligible": 0, "totalMinutes": 0, "handedOut": 0,
              "released": 0, "paused": 0, "unpaused": 0, "deleted": 0, "newSignups": 0}

    # Every run: delete requests.
    for u in [u for u in users if u.get("deleteRequested")]:
        LOG.info("delete request: removing person %s", u["uid"])
        if not dry_run:
            store.delete_person(u["uid"])
        _apply_delete_locally(u["uid"], users, rows)
        counts["deleted"] += 1

    # Every run: release the open stories of people who stopped.
    for rid in A.stopped_release_ids(rows, users):
        if dry_run or store.release_row(rid):
            counts["released"] += 1
        for r in rows:
            if r["id"] == rid:
                r["releasedAt"] = "released-this-run"
    LOG.info("stopped people: released %d open rows", counts["released"])

    # The weekly hand-out.
    plan = None
    if config.launch_date is None:
        LOG.info("launch date not set: no hand-out")
    elif pause:
        LOG.info("SEPTIMUS_PAUSE is on: no hand-out (no run recorded, so un-pausing hands out this week)")
    elif week < 1 or week > config.last_week:
        LOG.info("campaign week %d is outside 1..%d: no hand-out", week, config.last_week)
    else:
        existing = store.get_run(week)
        if existing and existing.get("finishedAt"):
            LOG.info("week %d already handed out: nothing to do", week)
        else:
            plan = A.assign_week(story_order, rows, users, week, config.wpm, config.last_week, config.max_minutes)
            if not dry_run:
                store.start_run(week)
            counts["released"] += _release_all(store, plan.release_ids, dry_run)
            for uid in plan.pause_uids:
                if not dry_run:
                    store.set_paused(uid, True)
            for uid in plan.unpause_uids:
                if not dry_run:
                    store.set_paused(uid, False)
            if not dry_run:
                store.write_rows(plan.new_rows)
            counts["paused"], counts["unpaused"] = len(plan.pause_uids), len(plan.unpause_uids)
            counts["handedOut"] = len(plan.new_rows)
            counts["eligible"] = len(plan.eligible_uids)
            by_uid = {u["uid"]: u for u in users}
            counts["totalMinutes"] = sum(min(by_uid[uid]["minutesPerWeek"], config.max_minutes)
                                         for uid in plan.eligible_uids)
            since = store.previous_finished_at(week)
            counts["newSignups"] = sum(1 for u in users if since is None or u["createdAt"] > since)
            LOG.info("hand-out week %d: %d stories to %d people, released %d, paused %d, unpaused %d",
                     week, counts["handedOut"], counts["eligible"], len(plan.release_ids),
                     counts["paused"], counts["unpaused"])
    counts["users"] = len(users)

    # Every run: the public totals. Rows handed out just now have no doneAt, so they change nothing here.
    summary = A.summarise(story_order, rows, users, list_version)
    LOG.info("summary: %d learned, round %d, %d joined", summary["learned"], summary["round"], summary["joined"])
    if dry_run:
        LOG.info("DRY RUN: would write %s", json.dumps(plan.new_rows if plan else [], default=str)[:2000])
    else:
        store.write_summary(summary)
        if plan is not None:
            store.finish_run(week, counts)

    print(json.dumps(counts))
    # TODO(step e): email these counts to Simon here.
    return counts


def _release_all(store, ids, dry_run):
    """Release rows; the store skips any that were marked learned a moment ago. Returns how many were released."""
    n = 0
    for rid in ids:
        if dry_run or store.release_row(rid):
            n += 1
    return n


# ---------------------------------------------------------------- Firestore

class Store:
    """All Firestore / Auth access, in one place. `firebase_admin` is imported only when this is built."""

    def __init__(self, project_id):
        import firebase_admin
        from firebase_admin import auth, credentials, firestore
        self._auth, self._fs = auth, firestore
        key = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
        if key:
            cred = credentials.Certificate(json.loads(key))
        elif os.environ.get("FIRESTORE_EMULATOR_HOST") or os.environ.get("FIREBASE_AUTH_EMULATOR_HOST"):
            from google.auth.credentials import AnonymousCredentials
            cred = AnonymousCredentials()      # the emulator does not check credentials
        else:
            raise SystemExit("Set FIREBASE_SERVICE_ACCOUNT (the service-account JSON) or point at the emulator.")
        firebase_admin.initialize_app(cred, {"projectId": project_id})
        self.db = firestore.client()

    def users(self):
        return [{**d.to_dict(), "uid": d.id} for d in self.db.collection("users").stream()]

    def assignments(self):
        return [{**d.to_dict(), "id": d.id} for d in self.db.collection("assignments").stream()]

    def get_run(self, week):
        d = self.db.collection("runs").document(str(week)).get()
        return d.to_dict() if d.exists else None

    def start_run(self, week):
        self.db.collection("runs").document(str(week)).set({"startedAt": self._fs.SERVER_TIMESTAMP}, merge=True)

    def finish_run(self, week, counts):
        self.db.collection("runs").document(str(week)).set(
            {"finishedAt": self._fs.SERVER_TIMESTAMP, "counts": counts}, merge=True)

    def previous_finished_at(self, week):
        """When the latest finished run before `week` finished, or None."""
        times = [d.to_dict().get("finishedAt") for d in self.db.collection("runs").stream() if int(d.id) < week]
        times = [t for t in times if t]
        return max(times) if times else None

    def write_rows(self, rows):
        """Create new rows. An id that already exists is left alone (never overwrite a person's doneAt)."""
        from google.api_core.exceptions import AlreadyExists
        col = self.db.collection("assignments")
        for r in rows:
            doc = {k: v for k, v in r.items() if k != "id"}
            doc["assignedAt"] = self._fs.SERVER_TIMESTAMP
            try:
                col.document(r["id"]).create(doc)
            except AlreadyExists:
                LOG.info("row %s already exists: left as it is", r["id"])

    def release_row(self, row_id):
        """Mark a row released unless it was marked learned meanwhile. Returns True if released."""
        ref = self.db.collection("assignments").document(row_id)

        @self._fs.transactional
        def txn(transaction):
            snap = ref.get(transaction=transaction)
            data = snap.to_dict() or {}
            if not snap.exists or data.get("doneAt") or data.get("releasedAt"):
                return False
            transaction.update(ref, {"releasedAt": self._fs.SERVER_TIMESTAMP})
            return True

        return txn(self.db.transaction())

    def set_paused(self, uid, value):
        self.db.collection("users").document(uid).update({"pausedAt": self._fs.SERVER_TIMESTAMP if value else None})

    def write_summary(self, summary):
        self.db.collection("progress").document("summary").set({**summary, "updatedAt": self._fs.SERVER_TIMESTAMP})

    def delete_person(self, uid):
        """Rows first (blank uid, release open ones), then the sign-in account, then users/{uid} last, so a run
        that dies halfway still sees deleteRequested and finishes next time."""
        from google.cloud.firestore_v1.base_query import FieldFilter
        for d in self.db.collection("assignments").where(filter=FieldFilter("uid", "==", uid)).stream():
            patch = {"uid": None}
            if not (d.to_dict().get("doneAt") or d.to_dict().get("releasedAt")):
                patch["releasedAt"] = self._fs.SERVER_TIMESTAMP
            d.reference.update(patch)
        try:
            self._auth.delete_user(uid)
        except self._auth.UserNotFoundError:
            LOG.info("no sign-in account for %s (already deleted)", uid)
        self.db.collection("users").document(uid).delete()


# ---------------------------------------------------------------- command line

def main(argv=None):
    ap = argparse.ArgumentParser(description="Septimus sign-up: weekly story hand-out and progress summary.")
    ap.add_argument("--date", help="pretend today is YYYY-MM-DD (default: now, US Eastern)")
    ap.add_argument("--dry-run", action="store_true", help="read and compute, print the plan, write nothing")
    ap.add_argument("--config", default=str(CONFIG_JS), help="config.js to read (default: site/config.js)")
    ap.add_argument("--data-dir", default=str(DATA_DIR), help="story data folder (default: site/data)")
    args = ap.parse_args(argv)
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        config = parse_config(Path(args.config).read_text())
        today = today_eastern(args.date)
        pause = os.environ.get("SEPTIMUS_PAUSE", "") not in ("", "0", "false")
        LOG.info("today (US Eastern) %s, launch %s, last week %s", today, config.launch_date, config.last_week)
        order = A.load_story_order(args.data_dir)
        run(Store(config.project_id), today, config, dry_run=args.dry_run, pause=pause,
            story_order=order, list_version=A.load_list_version(args.data_dir))
    except Exception:
        LOG.exception("septimus_weekly failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
