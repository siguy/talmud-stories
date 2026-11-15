#!/usr/bin/env python3
"""Septimus sign-up: the daily/weekly job. Reads Firestore, calls the pure logic in septimus_assign.py, writes back.

What one run does (plan section 6), in this order:
  1. every run   handle "delete my data" requests (one person failing never stops the job)
  2. hand-out    once per campaign week, on the first day the script runs in that week (so a missed Sunday is made
                 up the next day): release old stories FOR REAL (a story marked learned a second ago is not
                 given away), pause the quiet, deal new stories, record runs/<week>.
  3. other days  still release the stories of people who stopped
  4. every run   refresh progress/summary, last, from the up-to-date rows

Reads are kept small (the free plan allows 50,000 a day): it never reads the whole history, only rows from the
current round on, plus every open row. Every run logs how many it read.

Safe to run twice: runs/<week> marks a finished week, and row ids are fixed (<week>_<uid>_<storyId>).
The repository is public, so Action logs are public: nothing here logs an id, an email or a row.

Usage:
  python3 scripts/septimus_weekly.py              # the real run (needs FIREBASE_SERVICE_ACCOUNT)
  python3 scripts/septimus_weekly.py --dry-run    # read, compute, print; write nothing
  python3 scripts/septimus_weekly.py --date 2026-12-07
Environment: FIREBASE_SERVICE_ACCOUNT (the JSON key, as text), SEPTIMUS_PAUSE=1 (no hand-out),
SEPTIMUS_DEBUG=1 (print full error traces; only for local runs, they can contain ids),
FIRESTORE_EMULATOR_HOST / FIREBASE_AUTH_EMULATOR_HOST (point at the local emulator instead).
"""
import argparse
import json
import logging
import os
import re
import secrets
import sys
from collections import Counter
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


def _signup_block(text):
    """The text between the braces of `signup: { ... }` (nested braces counted)."""
    m = re.search(r"\bsignup\s*:\s*\{", text)
    if not m:
        return ""
    depth, i = 1, m.end()
    while i < len(text) and depth:
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        i += 1
    return text[m.end():i - 1]


def parse_config(text):
    """Read launchDate, yahrzeit, wpm, maxMinutes from the `signup` block of site/config.js."""
    block = _signup_block(text)

    def grab(pattern, what):
        found = re.search(pattern, block)
        if not found:
            raise ValueError(f"site/config.js signup block has no {what}")
        return found.group(1)

    launch = grab(r'\blaunchDate\s*:\s*"([^"]*)"', "launchDate")
    project = re.search(r'\bprojectId\s*:\s*"([^"]+)"', text)
    launch_date = date.fromisoformat(launch) if launch else None
    if launch_date is not None and launch_date.weekday() != 6:
        raise ValueError(f"launchDate must be a Sunday (got {launch}, a {launch_date:%A})")
    return Config(
        launch_date=launch_date,
        yahrzeit=date.fromisoformat(grab(r'\byahrzeit\s*:\s*"([^"]+)"', "yahrzeit")),
        wpm=int(grab(r"\bwpm\s*:\s*(\d+)", "wpm")),
        max_minutes=int(grab(r"\bmaxMinutes\s*:\s*(\d+)", "maxMinutes")),
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
            r["uid"] = ""
            if A._is_open(r):
                r["releasedAt"] = "released-this-run"


def _release_rows(store, due, rows_by_id, users_by_uid, dry_run):
    """Release each due row for real. Returns (how many released, just_lapsed, per-person field changes).

    store.release_row returns False only when the person marked the story learned a moment ago: then it is NOT
    free (it is marked done here and stays covered), and nothing is recorded against the person."""
    released, just_lapsed, patches = 0, set(), {}
    for rid, why in due:
        r = rows_by_id[rid]
        if dry_run or store.release_row(rid):
            r["releasedAt"] = "released-this-run"
            released += 1
            if why == "lapsed":
                just_lapsed.add((r["uid"], r["storyId"], r["round"]))
                u = users_by_uid.get(r["uid"])
                if u is not None and A.add_lapse(u, r["week"]):
                    patches.setdefault(u["uid"], {})["lapses"] = u["lapses"]
        else:
            r["doneAt"] = "marked-during-run"
    return released, just_lapsed, patches


def run(store, today, config, dry_run=False, pause=False, story_order=None, list_version=None):
    """The whole job. Returns the counts dict. `store` is a Store (or a fake with the same methods)."""
    if story_order is None:
        story_order = A.load_story_order(DATA_DIR)
        list_version = A.load_list_version(DATA_DIR)
    reads_before = getattr(store, "reads", 0)
    users = [dict(u) for u in store.users()]
    # Rounds below the summary's round are complete (every story in them is done), so they change neither which
    # stories are free nor the totals: they are never read. Open rows are always read, from any round.
    summary_doc = store.get_summary()
    base_round = max(1, int(summary_doc.get("round", 1))) if summary_doc else 1
    rows = [dict(r) for r in store.assignments(base_round)]
    LOG.info("read %d users, %d assignment rows (round %d on), %d stories on the list",
             len(users), len(rows), base_round, len(story_order))

    week = A.campaign_week(today, config.launch_date) if config.launch_date else 0
    counts = {"week": week, "users": 0, "eligible": 0, "totalMinutes": 0, "handedOut": 0, "released": 0,
              "paused": 0, "deleted": 0, "deleteFailed": 0, "newSignups": 0, "reads": 0}

    # 1. Delete requests. One person failing must not stop everyone else's hand-out.
    for u in [u for u in users if u.get("deleteRequested")]:
        if not dry_run:
            try:
                store.delete_person(u["uid"])
            except Exception as exc:
                counts["deleteFailed"] += 1
                LOG.warning("deleting one person's data failed (%s); it will be retried on the next run. "
                            "Failures so far: %d", type(exc).__name__, counts["deleteFailed"])
                continue
        _apply_delete_locally(u["uid"], users, rows)
        counts["deleted"] += 1
    LOG.info("delete requests: %d done, %d failed", counts["deleted"], counts["deleteFailed"])

    # Is this a hand-out run?
    handout = False
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
            handout = True

    # 2. Release. On a hand-out run: lapsed and stopped. On any other run: stopped only.
    if handout and not dry_run:
        store.start_run(week)
    rows_by_id = {r["id"]: r for r in rows}
    users_by_uid = {u["uid"]: u for u in users}
    due = A.due_releases(rows, users, week if handout else None)
    counts["released"], just_lapsed, patches = _release_rows(store, due, rows_by_id, users_by_uid, dry_run)
    LOG.info("released %d open rows (%d lapsed)", counts["released"], len(just_lapsed))

    # The two fields only this script writes. everLearned is worked out from the rows read, OR the stored flag,
    # so history below the base round is never needed; it is written back only when it changes.
    for uid in A.ever_learned_uids(rows):
        u = users_by_uid.get(uid)
        if u is not None and not u.get("everLearned"):
            u["everLearned"] = True
            patches.setdefault(uid, {})["everLearned"] = True
    for uid, fields in patches.items():
        if not dry_run:
            store.update_user(uid, fields)

    # 2b. The hand-out itself.
    plan = None
    if handout:
        plan = A.hand_out(story_order, rows, users, week, config.wpm, config.last_week, just_lapsed,
                          config.max_minutes, base_round)
        for uid in plan.pause_uids:
            if not dry_run:
                store.set_paused(uid, True)           # also clears `lapses`: after a resume they start fresh
        if not dry_run:
            store.write_rows(plan.new_rows)           # one person at a time, each all-or-nothing
        counts["paused"] = len(plan.pause_uids)
        counts["handedOut"] = len(plan.new_rows)
        counts["eligible"] = len(plan.eligible_uids)
        by_uid = {u["uid"]: u for u in users}
        counts["totalMinutes"] = sum(min(by_uid[uid]["minutesPerWeek"], config.max_minutes)
                                     for uid in plan.eligible_uids)
        since = store.previous_finished_at(week)
        counts["newSignups"] = sum(1 for u in users if since is None or u["createdAt"] > since)
        LOG.info("hand-out week %d: %d stories to %d people, paused %d",
                 week, counts["handedOut"], counts["eligible"], counts["paused"])
    counts["users"] = len(users)
    counts["reads"] = getattr(store, "reads", 0) - reads_before
    if plan is not None and not dry_run:
        store.finish_run(week, counts)

    # 4. The public totals, last, from the up-to-date local rows. Rows handed out just now have no doneAt.
    summary = A.summarise(story_order, rows, users, list_version, base_round)
    LOG.info("summary: %d learned, round %d, %d joined", summary["learned"], summary["round"], summary["joined"])
    if dry_run:
        per_story = Counter(r["storyId"] for r in (plan.new_rows if plan else []))
        LOG.info("DRY RUN: would hand out %d rows over %d stories (rows per story: %s)",
                 sum(per_story.values()), len(per_story), json.dumps(dict(sorted(per_story.items())))[:1500])
    else:
        store.write_summary(summary)

    print(json.dumps(counts))
    # TODO(step e): email these counts to Simon here. It is the alarm for a missed week: no counts, no hand-out.
    # TODO(before launch): delete everyone's personal data (accounts and users records, rows anonymised) on the
    #   configured date six months after the yahrzeit (plan section 6, Leaving). NOT BUILT: nothing does it yet.
    return counts


# ---------------------------------------------------------------- Firestore

class Store:
    """All Firestore / Auth access, in one place. `firebase_admin` is imported only when this is built.
    `self.reads` counts documents returned by every read (what the free plan's 50,000 a day is spent on)."""

    def __init__(self, project_id):
        import firebase_admin
        from firebase_admin import auth, credentials, firestore
        self._auth, self._fs = auth, firestore
        self.reads = 0
        key = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
        if key:
            # The key decides which project is touched (live or staging), not site/config.js: a staging key
            # must never be pointed at the live database, or the other way round.
            info = json.loads(key)
            cred = credentials.Certificate(info)
            project_id = info["project_id"]
        elif os.environ.get("FIRESTORE_EMULATOR_HOST") or os.environ.get("FIREBASE_AUTH_EMULATOR_HOST"):
            from google.auth.credentials import AnonymousCredentials
            cred = AnonymousCredentials()      # the emulator does not check credentials
        else:
            raise SystemExit("Set FIREBASE_SERVICE_ACCOUNT (the service-account JSON) or point at the emulator.")
        LOG.info("database: project %s", project_id)
        firebase_admin.initialize_app(cred, {"projectId": project_id})
        self.db = firestore.client()

    def users(self):
        out = [{**d.to_dict(), "uid": d.id} for d in self.db.collection("users").stream()]
        self.reads += len(out)
        return out

    def get_summary(self):
        self.reads += 1
        d = self.db.collection("progress").document("summary").get()
        return d.to_dict() if d.exists else None

    def assignments(self, from_round=1):
        """Rows with round >= from_round, plus every open row from any round, merged by id."""
        from google.cloud.firestore_v1.base_query import FieldFilter
        col = self.db.collection("assignments")
        merged = {}
        queries = (col.where(filter=FieldFilter("round", ">=", from_round)),
                   col.where(filter=FieldFilter("doneAt", "==", None)).where(
                       filter=FieldFilter("releasedAt", "==", None)))
        for q in queries:
            for d in q.stream():
                self.reads += 1
                merged.setdefault(d.id, {**d.to_dict(), "id": d.id})
        return list(merged.values())

    def get_run(self, week):
        self.reads += 1
        d = self.db.collection("runs").document(str(week)).get()
        return d.to_dict() if d.exists else None

    def start_run(self, week):
        self.db.collection("runs").document(str(week)).set({"startedAt": self._fs.SERVER_TIMESTAMP}, merge=True)

    def finish_run(self, week, counts):
        self.db.collection("runs").document(str(week)).set(
            {"finishedAt": self._fs.SERVER_TIMESTAMP, "counts": counts}, merge=True)

    def previous_finished_at(self, week, look_back=4):
        """When the latest finished run in the few weeks before `week` finished, or None. Reads those run docs
        by id (at most `look_back`), never the whole runs collection."""
        for w in range(week - 1, max(week - 1 - look_back, 0), -1):
            run_doc = self.get_run(w)
            if run_doc and run_doc.get("finishedAt"):
                return run_doc["finishedAt"]
        return None

    def write_rows(self, rows):
        """Create new rows, one person at a time in a single batch: a person is fully served or not at all.
        `create` fails on an existing id, so a row (and its doneAt) is never overwritten."""
        from google.api_core.exceptions import AlreadyExists
        col = self.db.collection("assignments")
        by_uid = {}
        for r in rows:
            by_uid.setdefault(r["uid"], []).append(r)
        for mine in by_uid.values():
            if len(mine) > 500:
                raise RuntimeError("one person's hand-out is over the 500-write batch limit")
            batch = self.db.batch()
            for r in mine:
                doc = {k: v for k, v in r.items() if k != "id"}
                doc["assignedAt"] = self._fs.SERVER_TIMESTAMP
                batch.create(col.document(r["id"]), doc)
            try:
                batch.commit()
            except AlreadyExists:
                LOG.info("one person's rows for this week already exist: left as they are")

    def release_row(self, row_id):
        """Mark a row released. Returns False ONLY if the person marked it learned meanwhile (it stays theirs);
        True otherwise, including a row that is already released or gone (nothing left to free)."""
        ref = self.db.collection("assignments").document(row_id)

        @self._fs.transactional
        def txn(transaction):
            snap = ref.get(transaction=transaction)
            data = snap.to_dict() or {}
            if snap.exists and data.get("doneAt"):
                return False
            if snap.exists and not data.get("releasedAt"):
                transaction.update(ref, {"releasedAt": self._fs.SERVER_TIMESTAMP})
            return True

        return txn(self.db.transaction())

    def update_user(self, uid, fields):
        """Script-only fields on the user record (everLearned, lapses)."""
        self.db.collection("users").document(uid).update(fields)

    def set_paused(self, uid, value):
        """Pause (also clears `lapses`, so a person who resumes starts counting afresh) or clear the pause."""
        fields = {"pausedAt": self._fs.SERVER_TIMESTAMP, "lapses": []} if value else {"pausedAt": None}
        self.db.collection("users").document(uid).update(fields)

    def write_summary(self, summary):
        self.db.collection("progress").document("summary").set({**summary, "updatedAt": self._fs.SERVER_TIMESTAMP})

    def delete_person(self, uid):
        """Anonymise the rows, delete the sign-in account, delete users/{uid} LAST, so a run that dies halfway
        still sees deleteRequested and finishes next time.

        Row ids contain the uid, so blanking the uid field is not enough: each row is copied under a new id
        (<week>_deleted-<12 random hex>_<storyId>, uid "", open rows released) and the original deleted. The
        copy and the delete go in ONE batch, so repeating after a crash never leaves two copies."""
        from google.cloud.firestore_v1.base_query import FieldFilter
        col = self.db.collection("assignments")
        snaps = list(col.where(filter=FieldFilter("uid", "==", uid)).stream())
        self.reads += len(snaps)
        for i in range(0, len(snaps), 200):
            batch = self.db.batch()
            for d in snaps[i:i + 200]:
                data = d.to_dict()
                copy = {**data, "uid": ""}
                if not (data.get("doneAt") or data.get("releasedAt")):
                    copy["releasedAt"] = self._fs.SERVER_TIMESTAMP
                new_id = f"{data.get('week')}_deleted-{secrets.token_hex(6)}_{data.get('storyId')}"
                batch.create(col.document(new_id), copy)
                batch.delete(d.reference)
            batch.commit()
        try:
            self._auth.delete_user(uid)
        except self._auth.UserNotFoundError:
            LOG.info("no sign-in account for one person (already deleted)")
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
    except Exception as exc:
        # The repository is public, so this log is public: error text can carry ids. Name the kind of error only,
        # unless SEPTIMUS_DEBUG is set (a local run).
        if os.environ.get("SEPTIMUS_DEBUG"):
            LOG.exception("septimus_weekly failed")
        else:
            LOG.error("septimus_weekly failed: %s (set SEPTIMUS_DEBUG=1 locally for the full trace)", type(exc).__name__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
