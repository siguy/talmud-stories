#!/usr/bin/env python3
"""
Score a detector output against Jeff's expert boundary targets.

Test set: tests/expert_boundary_targets.json (built by build_boundary_testset.py)
— 52 boundaries Jeff stated in Hebrew across seven review rounds, located by TEXT
so rounds from different detector versions pool safely.

For each target we ask one question: does the run place its boundary at the clause
Jeff quoted?
  HIT   - boundary is at the target clause
  NEAR  - within one clause (usually a framing word either side)
  MISS  - elsewhere
  N/A   - this run has no story covering that segment (a detection gap, not a
          boundary error; reported separately so the two never get conflated)

BIAS — always report it with the number: every target is a case Jeff flagged as
WRONG. This measures whether known failures get fixed, not whether correct
boundaries get broken. Pair with scripts/audit_text_spans.py (structural, 100%
coverage) and a random sample of currently-correct stories.

Usage:
  python3 scripts/score_boundary_targets.py --runs A=results/... B=results/...
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.story_detector_v11 import _split_into_clauses  # noqa: E402


def load_run(path):
    data = json.loads(Path(path).read_text())
    stories, segs = [], {}
    for page in data['pages']:
        segs[page['ref']] = {s['index']: s['hebrew'] for s in page.get('segments', [])}
        for s in page.get('stories', []):
            if s.get('classification') != 'NOT_A_STORY':
                stories.append((page['ref'], s))
    return data, stories, segs


def boundary_clause(story, segs, ref, side):
    """Which clause index this run's boundary sits at, on its start/end segment."""
    seg = story['start_segment'] if side == 'start' else story['end_segment']
    heb = segs.get(ref, {}).get(seg)
    if heb is None:
        return None, None
    n = len(_split_into_clauses(heb))
    span = story.get('text_span_start' if side == 'start' else 'text_span_end')
    if span and span.get('clause_index') is not None:
        return seg, span['clause_index']
    return seg, (0 if side == 'start' else max(n - 1, 0))


def score(path):
    _, stories, segs = load_run(path)
    ts = json.loads((PROJECT_ROOT / 'tests/expert_boundary_targets.json').read_text())
    out = Counter()
    rows = []
    for t in ts['targets']:
        ref = t.get('located_on') or t['ref']
        seg, want = t['segment'], t['clause']
        cover = [s for r, s in stories
                 if r == ref and s['start_segment'] <= seg <= s['end_segment']]
        if not cover:
            out['N/A'] += 1
            rows.append((ref, seg, t['direction'], want, None, 'N/A'))
            continue
        st = cover[0]
        gseg, got = boundary_clause(st, segs, ref, t['direction'])
        if got is None or gseg != seg:
            verdict = 'MISS'
        elif got == want:
            verdict = 'HIT'
        elif abs(got - want) <= 1:
            verdict = 'NEAR'
        else:
            verdict = 'MISS'
        out[verdict] += 1
        rows.append((ref, seg, t['direction'], want, got, verdict))
    return out, rows, ts


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--runs', nargs='+', required=True, help='NAME=path ...')
    ap.add_argument('--detail', action='store_true')
    args = ap.parse_args()

    print("BIAS NOTE: every target is a case Jeff flagged as wrong. This measures "
          "fixing known failures, not avoiding new ones.\n")
    print(f"{'run':10s} {'scored':>7s} {'HIT':>5s} {'NEAR':>5s} {'MISS':>5s} {'N/A':>5s} {'hit%':>6s} {'hit+near%':>10s}")
    details = {}
    for spec in args.runs:
        name, path = spec.split('=', 1)
        c, rows, ts = score(path)
        details[name] = rows
        scored = c['HIT'] + c['NEAR'] + c['MISS']
        h = c['HIT'] / scored if scored else 0
        hn = (c['HIT'] + c['NEAR']) / scored if scored else 0
        print(f"{name:10s} {scored:7d} {c['HIT']:5d} {c['NEAR']:5d} {c['MISS']:5d} {c['N/A']:5d} "
              f"{h:6.0%} {hn:10.0%}")

    if args.detail:
        for name, rows in details.items():
            print(f"\n--- {name} ---")
            for r in rows:
                if r[5] in ('MISS', 'NEAR'):
                    print(f"  {r[0]:16s} seg{r[1]:<3d} {r[2]:5s} want clause {r[3]} got {r[4]}  {r[5]}")


if __name__ == '__main__':
    main()
