#!/usr/bin/env python3
"""
Stamp Jeff's later rulings onto the recall denominators already on disk.

`measure_recall_vs_expert_list.py` applies `results/expert_lists/superseded_by_rule.json`
on every new run. This applies the same function to the four unsuffixed recall files
(`results/recall/<t>_jeff2005_matches.json` -- always the denominator, per board.py)
without re-running the matcher, so nothing else in them can move: it only adds
`counts_for_recall` and `superseded_by_rule` to each row. Suffixed files are
sensitivity variants and are left as they were.

Idempotent. Prints recall before and after for each tractate.

    python3 scripts/stamp_superseded_recall.py --dry-run
    python3 scripts/stamp_superseded_recall.py
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from measure_recall_vs_expert_list import apply_superseded, log  # noqa: E402

ROOT = Path(__file__).parent.parent
TRACTATES = ['Ketubot', 'Kiddushin', 'Gittin', 'Yevamot']


def recall(rows):
    return sum(1 for r in rows if r['in_detector']), len(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    for tractate in TRACTATES:
        path = ROOT / f'results/recall/{tractate.lower()}_jeff2005_matches.json'
        rows = json.loads(path.read_text())
        before = recall(rows)
        apply_superseded(rows, tractate)
        after = recall([r for r in rows if r['counts_for_recall']])
        log.info('%s: recall %d/%d -> %d/%d (%s)', tractate, *before, *after, path.name)
        if not args.dry_run:
            path.write_text(json.dumps(rows, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
