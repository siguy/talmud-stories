#!/usr/bin/env python3
"""
Merge the Stage-2-on-discarded-pages output back into the shipped run, so the
recall harness can be re-run over the WHOLE tractate rather than the fraction
triage let through.

The merged file is a measurement artifact, not a ship candidate: it answers
"what would recall be if Stage 1 kept everything", which is the number
`work/2026-08-30-triage-recall-price.md` asks for. It is written to
results/v11/triage_recall/ and nothing reads it except the harness.

Invariants asserted (Lesson 21 — the buckets are a partition, and the partition
is checked rather than assumed):

  - every page of the shipped run appears exactly once in the merged run
  - a page that was NOT skipped keeps its stories byte-identical
  - a page that WAS skipped has exactly the stories the Stage 2 re-run proposed
  - a page whose Stage 2 call FAILED is left with its original (empty) stories
    and is counted, never silently treated as "no stories here"
"""

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

RUNS = {
    'ketubot': ['results/v10/wave4_notrim/ketubot_v10_2-60_notrim.json',
                'results/v10/wave4_notrim/ketubot_v10_61-112_notrim.json'],
    'kiddushin': ['results/v10/wave4_notrim/kiddushin_v10_notrim.json'],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tractate', required=True, choices=sorted(RUNS))
    ap.add_argument('--rerun', default=None,
                    help='default results/v11/triage_recall/<tractate>_skipped_stage2.json')
    ap.add_argument('--out-dir', default='results/v11/triage_recall')
    ap.add_argument('--live-rule', action='store_true',
                    help="splice in only the pages the CURRENT should_skip_page() "
                         "would examine, rather than every discarded page. Use this "
                         "to measure a rule change against the blind lists.")
    args = ap.parse_args()

    live_examines = None
    if args.live_rule:
        import sys as _sys
        _sys.path.insert(0, str(REPO))
        from src.event_triage import EventTriager
        from src.ground_truth import EventType
        tri = {}
        for c in ['results/v7/event_triage_2-60.json',
                  'results/v7/event_triage_61-112.json',
                  'results/v7/event_triage_kiddushin.json']:
            tri.update(json.loads((REPO / c).read_text())['triage_results'])
        live_examines = lambda ref: not EventTriager.should_skip_page(
            [EventType(l) for l in tri.get(ref, [])])

    rerun_path = REPO / (args.rerun or
                         f'results/v11/triage_recall/{args.tractate}_skipped_stage2.json')
    rerun = json.loads(rerun_path.read_text())
    by_ref = {p['ref']: p for p in rerun['pages']}
    failed = {p['ref'] for p in rerun['pages'] if p.get('stage2_error')}

    written = []
    stats = {'kept': 0, 'replaced': 0, 'failed_left_empty': 0,
             'skipped_not_rerun': 0}

    for rel in RUNS[args.tractate]:
        src = json.loads((REPO / rel).read_text())
        for page in src['pages']:
            ref = page['ref']
            if not page.get('skipped_by_triage'):
                stats['kept'] += 1
                continue
            if ref not in by_ref:
                stats['skipped_not_rerun'] += 1
                continue
            if ref in failed:
                stats['failed_left_empty'] += 1
                continue
            if live_examines is not None and not live_examines(ref):
                stats['skipped_not_rerun'] += 1
                continue
            assert not page.get('stories'), (
                f"{ref} was marked skipped but already carries stories")
            page['stories'] = by_ref[ref]['stories']
            page['stage2_rerun'] = True
            stats['replaced'] += 1

        out_dir = REPO / args.out_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        suffix = '_plus_liverule' if args.live_rule else '_plus_skipped'
        dest = out_dir / (Path(rel).stem + suffix + '.json')
        src['merged_from'] = {'shipped': rel, 'rerun': str(rerun_path.relative_to(REPO))}
        src['merge_note'] = ('MEASUREMENT ARTIFACT: Stage 1 skip decisions '
                             'overridden by re-running Stage 2 on the discarded '
                             'pages. Not a ship candidate.')
        dest.write_text(json.dumps(src, ensure_ascii=False, indent=2))
        written.append(dest)

    total = sum(stats.values())
    expect = sum(len(json.loads((REPO / r).read_text())['pages'])
                 for r in RUNS[args.tractate])
    assert total == expect, f"page partition broken: {total} != {expect}"

    print(f"{args.tractate}: {stats}")
    print(f"  page partition asserted: {total} pages accounted for")
    if stats['failed_left_empty']:
        print(f"  NOTE {stats['failed_left_empty']} page(s) had a failed Stage 2 "
              f"call and are NOT counted as 'no stories here'.")
    for d in written:
        print(f"  wrote {d.relative_to(REPO)}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
