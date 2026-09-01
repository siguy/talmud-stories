#!/usr/bin/env python3
"""
Screen every end-trim the clause spans make, by DEPTH. No API calls.

WHY THIS EXISTS. `work/2026-08-30-second-story-guard.md` was written from two
cases — Ketubot 62a and 105b — where the end-trim discards a whole second story.
Lesson 18 says an expert sample LOCATES a defect and never SIZES it, and that
rule has already been paid for once here: Jeff's 8 flagged Wave 4 spans turned
out to be 8 of 104 corrupt cuts. So before changing the prompt on the strength of
two cases, count how many trims across the corpus are deep enough to be the same
shape.

WHAT IT MEASURES, AND WHAT IT DOES NOT. Trim DEPTH is structural — clauses and
characters discarded off the end of a story. It is a NECESSARY condition for
"we deleted a second story" and nowhere near a sufficient one: a deep trim is
just as likely to be a long stam-Talmud legal discussion, which the prompt is
supposed to cut. This script therefore SCREENS and does not judge. It prints the
discarded Hebrew and English so a human can judge, and every count it reports is
INDICATED, not measured.

Deliberately no lexical rule. `כי הא`/`וכן`/`נמי` and their English counterparts
("Similarly", "The Gemara likewise relates") are the obvious way to auto-classify
these, and Lesson 15 is exactly that such markers are story content about half the
time. Wave 3's regex trimmer shipped on a 10/17 audit built from that reasoning
and Jeff killed it. Markers appear in the output as EVIDENCE, on their own line,
never as a filter.

Usage:
  python3 scripts/screen_end_trim_depth.py --runs results/v11/wave5_summaryfix/*.json
  python3 scripts/screen_end_trim_depth.py --runs ... --min-depth 4 --show
  python3 scripts/screen_end_trim_depth.py --runs ... --json out.json
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.story_detector_v11 import _split_into_clauses  # noqa: E402

HTML = re.compile(r'<[^>]+>')

# Evidence only. Never a filter — see the module docstring and Lesson 15.
HEB_PARALLEL = ('כי הא', 'וכן', 'נמי', 'כיוצא בו')
ENG_PARALLEL = ('similarly', 'likewise', 'so too', 'the same')


def trims(run_path):
    """Every end-trim in one run, with the text it discards."""
    data = json.loads(Path(run_path).read_text())
    out = []
    for page in data.get('pages', []):
        segs = {s['index']: s for s in page.get('segments', [])}
        for st in page.get('stories', []):
            if st.get('classification') == 'NOT_A_STORY':
                continue
            span = st.get('text_span_end') or {}
            ci = span.get('clause_index')
            seg = segs.get(st.get('end_segment'))
            if ci is None or seg is None:
                continue
            clauses = _split_into_clauses(seg.get('hebrew', ''))
            depth = len(clauses) - 1 - ci
            if depth <= 0:
                continue
            heb = seg['hebrew'][clauses[ci + 1][0]:clauses[-1][1]]
            eng = HTML.sub('', seg.get('english', ''))
            out.append({
                'ref': page['ref'],
                'segment': st['end_segment'],
                'kept_through_clause': ci,
                'n_clauses': len(clauses),
                'depth': depth,
                'chars': len(heb),
                'summary': (st.get('one_sentence_summary') or '')[:120],
                'dropped_hebrew': heb,
                'segment_english': eng,
                'markers': ([m for m in HEB_PARALLEL if m in heb]
                            + [m for m in ENG_PARALLEL if m in eng.lower()]),
                'run': Path(run_path).name,
            })
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--runs', nargs='+', required=True)
    ap.add_argument('--min-depth', type=int, default=4,
                    help='depth at or above which a trim is listed as a candidate (default 4)')
    ap.add_argument('--show', action='store_true', help='print the discarded Hebrew')
    ap.add_argument('--json', help='write the full screen to this path')
    args = ap.parse_args()

    all_trims = []
    for r in args.runs:
        all_trims.extend(trims(r))

    if not all_trims:
        print('no end-trims found in these runs — do they carry clause spans?')
        return

    dist = Counter(t['depth'] for t in all_trims)
    print(f"end-trims: {len(all_trims)} across {len(args.runs)} run(s)\n")
    print(f"{'depth':>6s} {'trims':>6s}   share")
    for d in sorted(dist):
        n = dist[d]
        print(f"{d:6d} {n:6d}   {n/len(all_trims):5.0%}  {'#' * min(n, 50)}")

    deep = sorted((t for t in all_trims if t['depth'] >= args.min_depth),
                  key=lambda t: -t['depth'])
    print(f"\ncandidates at depth >= {args.min_depth}: {len(deep)} "
          f"({len(deep)/len(all_trims):.0%} of trims)")
    print("INDICATED, NOT MEASURED — depth is structural. A deep trim is as likely to be "
          "a long\nstam-Talmud discussion (which the prompt SHOULD cut) as a second story. "
          "Judge each by eye.\n")
    for t in deep:
        mk = f"  markers: {', '.join(t['markers'])}" if t['markers'] else ''
        print(f"  {t['ref']:18s} seg {t['segment']:<3d} depth {t['depth']:2d}  "
              f"{t['chars']:4d} chars  kept 0..{t['kept_through_clause']} of "
              f"{t['n_clauses'] - 1}{mk}")
        if args.show:
            print(f"      dropped: {t['dropped_hebrew'][:300]}")

    if args.json:
        Path(args.json).write_text(json.dumps(
            {'n_trims': len(all_trims),
             'depth_distribution': {str(k): v for k, v in sorted(dist.items())},
             'min_depth': args.min_depth,
             'candidates': deep}, ensure_ascii=False, indent=2))
        print(f"\nwrote {args.json}")


if __name__ == '__main__':
    main()
