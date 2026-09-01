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
  WITHHELD - the covering story exists but Stage 4g moved it to `mishnah_stories`.
          Found, bounded, then set aside on a scope judgment still open with Jeff
          (`jeff:mishnah-scope`). Never folded into the score in either direction,
          and never reported as N/A: a withheld story is not a story we missed
          (Lesson 27).

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
    """Returns (data, stories, segs, withheld).

    `withheld` is read from `mishnah_stories` and kept apart from `stories` on
    purpose. Before this key was read here, a target on a withheld story scored
    N/A — the bucket that means "we found nothing on that segment" — so Stage 4g's
    scope decision was reported as a detection gap (Lesson 27).
    """
    data = json.loads(Path(path).read_text())
    stories, withheld, segs = [], [], {}
    for page in data['pages']:
        segs[page['ref']] = {s['index']: s['hebrew'] for s in page.get('segments', [])}
        for s in page.get('stories', []):
            if s.get('classification') != 'NOT_A_STORY':
                stories.append((page['ref'], s))
        for s in page.get('mishnah_stories', []) or []:
            if s.get('classification') != 'NOT_A_STORY':
                withheld.append((page['ref'], s))
    return data, stories, segs, withheld


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


DEFAULT_TARGETS = 'tests/expert_boundary_targets.json'


def load_targets(specs):
    """Pool one or more target files. Each target keeps its source file so the
    two kinds — Jeff's CORRECTIONS and his detector-blind 2005 list — can be
    reported apart as well as together. They measure different things: the
    corrections ask 'did we fix known failures', the 2005 list asks 'are we
    right in general', and only the latter can catch a regression."""
    pooled = []
    for spec in specs:
        data = json.loads((PROJECT_ROOT / spec).read_text())
        for tgt in data['targets']:
            pooled.append({**tgt, 'target_file': Path(spec).name})
    return pooled


def score(path, targets, skip_needs_human=True):
    _, stories, segs, withheld = load_run(path)
    out = Counter()
    rows = []
    for t in targets:
        if skip_needs_human and t.get('needs_human'):
            continue
        ref = t.get('located_on') or t['ref']
        seg, want = t['segment'], t['clause']
        cover = [s for r, s in stories
                 if r == ref and s['start_segment'] <= seg <= s['end_segment']]
        if not cover:
            held = any(r == ref and s['start_segment'] <= seg <= s['end_segment']
                       for r, s in withheld)
            verdict = 'WITHHELD' if held else 'N/A'
            out[verdict] += 1
            rows.append((ref, seg, t['direction'], want, None, verdict))
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
        rows.append((ref, seg, t['direction'], want, got, verdict, t.get('target_file')))
    return out, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--runs', nargs='+', required=True, help='NAME=path ...')
    ap.add_argument('--detail', action='store_true')
    ap.add_argument('--targets', nargs='+', default=[DEFAULT_TARGETS],
                    help='one or more target files to pool')
    ap.add_argument('--by-source', action='store_true',
                    help='also break the score out per target file')
    ap.add_argument('--include-needs-human', action='store_true',
                    help='score targets flagged for human polarity review (default: skip)')
    args = ap.parse_args()

    targets = load_targets(args.targets)
    skipped = sum(1 for t in targets if t.get('needs_human'))
    # Classify by what the target IS, not by which file it arrived in. The filename
    # test here was `!= 'expert_boundary_targets_2005.json'`, which silently counted
    # the blind Kiddushin set as corrections the moment a second 2005 file existed.
    blind = lambda t: str(t.get('source_round', '')).startswith('jeff_2005_')
    corrections = sum(1 for t in targets if not blind(t))
    print(f"targets: {len(targets)} pooled from {len(args.targets)} file(s) — "
          f"{corrections} corrections, {len(targets)-corrections} detector-blind (2005 list)"
          + (f"; {skipped} skipped pending human polarity review" if skipped and not args.include_needs_human else ""))
    print("BIAS NOTE: a CORRECTION target is a case Jeff flagged as wrong, so it measures "
          "fixing known failures. The 2005 list is a neutral sample and also catches regressions.\n")
    print(f"{'run':10s} {'scored':>7s} {'HIT':>5s} {'NEAR':>5s} {'MISS':>5s} {'N/A':>5s} "
          f"{'WITHHELD':>9s} {'hit%':>6s} {'hit+near%':>10s}")
    details = {}
    for spec in args.runs:
        name, path = spec.split('=', 1)
        c, rows = score(path, targets, not args.include_needs_human)
        details[name] = rows
        scored = c['HIT'] + c['NEAR'] + c['MISS']
        h = c['HIT'] / scored if scored else 0
        hn = (c['HIT'] + c['NEAR']) / scored if scored else 0
        print(f"{name:10s} {scored:7d} {c['HIT']:5d} {c['NEAR']:5d} {c['MISS']:5d} {c['N/A']:5d} "
              f"{c['WITHHELD']:9d} {h:6.0%} {hn:10.0%}")
        if c['WITHHELD']:
            print(f"{'':10s} {c['WITHHELD']} target(s) sit on a story Stage 4g withheld to "
                  f"`mishnah_stories` — found, then set aside (jeff:mishnah-scope). "
                  f"Not scored, and not a detection gap.")

    if args.by_source:
        files = sorted({t['target_file'] for t in targets})
        print()
        for f in files:
            sub = [t for t in targets if t['target_file'] == f]
            print(f"--- {f}  ({len(sub)} targets)")
            for spec in args.runs:
                name, path = spec.split('=', 1)
                c, _ = score(path, sub, not args.include_needs_human)
                s = c['HIT'] + c['NEAR'] + c['MISS']
                if not s:
                    print(f"    {name:12s} no scorable targets"); continue
                print(f"    {name:12s} scored {s:3d}  hit {c['HIT']/s:4.0%}  "
                      f"hit+near {(c['HIT']+c['NEAR'])/s:4.0%}   "
                      f"(N/A {c['N/A']}, withheld {c['WITHHELD']})")

    if args.detail:
        for name, rows in details.items():
            print(f"\n--- {name} ---")
            for r in rows:
                if r[5] in ('MISS', 'NEAR'):
                    print(f"  {r[0]:16s} seg{r[1]:<3d} {r[2]:5s} want clause {r[3]} got {r[4]}  {r[5]}")


if __name__ == '__main__':
    main()
