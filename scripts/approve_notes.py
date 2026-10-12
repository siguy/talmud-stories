#!/usr/bin/env python3
"""Mark drafted notes as reviewed (shippable). Usage:
    approve_notes.py --tractate ketubot            # all notes in that tractate
    approve_notes.py --ids ketubot-20a-2-3 ...     # specific stories
    approve_notes.py --tractate ketubot --revoke --ids ...   # un-approve
"""
import argparse
import json
from pathlib import Path

NOTES = Path(__file__).resolve().parent.parent / "site/data/notes"
ap = argparse.ArgumentParser()
ap.add_argument("--tractate")
ap.add_argument("--ids", nargs="*", default=[])
ap.add_argument("--revoke", action="store_true")
a = ap.parse_args()
assert a.tractate or a.ids, "give --tractate and/or --ids"
tractates = [a.tractate] if a.tractate else sorted({i.split("-")[0] for i in a.ids})
for t in tractates:
    p = NOTES / f"{t}.json"
    d = json.loads(p.read_text())
    n = 0
    for i, rec in d["notes"].items():
        if (not a.ids or i in a.ids) and rec["approved"] == a.revoke:
            rec["approved"] = not a.revoke
            n += 1
    unknown = [i for i in a.ids if i.split("-")[0] == t and i not in d["notes"]]
    assert not unknown, f"unknown ids: {unknown}"
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1))
    print(f"{t}: {n} {'revoked' if a.revoke else 'approved'}")
