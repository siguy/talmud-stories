#!/usr/bin/env python3
"""Mark drafted notes as reviewed (shippable). Usage:
    approve_notes.py --tractate ketubot            # all notes in that tractate
    approve_notes.py --ids ketubot-20a-2-3 ...     # specific stories
    approve_notes.py --all --unflagged             # every note in every tractate that is not held
    approve_notes.py --tractate ketubot --revoke --ids ...   # un-approve

--unflagged skips every id in results/site_notes/held.json (scripts/build_site_notes.py writes
it: the drafter flagged the passage, or the note failed a check). Simon spot-checked the drafts
and set this rule on 2026-11-15 (work/2026-11-15-shas-background-notes.md).
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTES = ROOT / "site/data/notes"
HELD = ROOT / "results/site_notes/held.json"
ap = argparse.ArgumentParser()
ap.add_argument("--tractate")
ap.add_argument("--all", action="store_true")
ap.add_argument("--ids", nargs="*", default=[])
ap.add_argument("--unflagged", action="store_true", help="skip notes listed in results/site_notes/held.json")
ap.add_argument("--revoke", action="store_true")
a = ap.parse_args()
assert a.tractate or a.ids or a.all, "give --tractate, --ids or --all"
if a.unflagged:
    assert HELD.exists(), "no held.json: run scripts/build_site_notes.py first"
held = set(json.loads(HELD.read_text())) if a.unflagged else set()
if a.all:
    tractates = sorted(p.stem for p in NOTES.glob("*.json"))
else:
    tractates = [a.tractate] if a.tractate else sorted({i.split("-")[0] for i in a.ids})
for t in tractates:
    p = NOTES / f"{t}.json"
    d = json.loads(p.read_text())
    n = skipped = 0
    for i, rec in d["notes"].items():
        if (not a.ids or i in a.ids) and rec["approved"] == a.revoke:
            if i in held and not a.revoke:
                skipped += 1
                continue
            rec["approved"] = not a.revoke
            n += 1
    unknown = [i for i in a.ids if i.split("-")[0] == t and i not in d["notes"]]
    assert not unknown, f"unknown ids: {unknown}"
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1))
    print(f"{t}: {n} {'revoked' if a.revoke else 'approved'}" + (f", {skipped} held" if skipped else ""))
