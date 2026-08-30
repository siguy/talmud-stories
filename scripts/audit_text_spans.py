#!/usr/bin/env python3
"""
Structural gate for sub-segment text boundaries (Lesson 16).

Every emitted text-span boundary MUST sit on a real text unit. This script
measures two invariants over any detector output:

  mid-word rate    : cuts that sever a Hebrew word  -> MUST be 0%
  clause-edge rate : cuts sitting at a `. : ? !` clause boundary -> target 100%

Clause split is on SENTENCE-level punctuation only (. : ? !). It deliberately
does NOT split on commas: the comma is the most frequent mark in the corpus
(4,855 vs 3,959 periods) and Jeff's Kiddushin 12b seg 4 correction
(`...בְּסוּרָא, וּפְרַשׁוּ רַבָּנַן מִינַּהּ`) is precisely a case where the story
continues past a comma.

Baseline recorded 2026-08-28 on the Wave 4 (v10) outputs:
  ketubot_2-60     40 cuts  60% mid-word   0% clause-edge
  ketubot_61-112   63 cuts  59% mid-word  10% clause-edge
  kiddushin       86 cuts  50% mid-word   1% clause-edge
  TOTAL          189 cuts  55% mid-word   4% clause-edge

Usage:
  python3 scripts/audit_text_spans.py results/v10/wave4/*.json
  python3 scripts/audit_text_spans.py --strict results/v11/...   # exit 1 on any mid-word cut
"""
import argparse
import json
import re
import sys
from pathlib import Path

TERMINAL = '.:?!'
BREAKERS = set('.:?!,״׳()[]–—')
CLAUSE_SPLIT = re.compile(r'(?<=[\.\:\?\!])\s+')


def clause_edges(hebrew):
    """Legal (start_positions, end_positions) for a clause-anchored boundary."""
    starts, ends = {0}, {len(hebrew)}
    for m in CLAUSE_SPLIT.finditer(hebrew):
        ends.add(m.start())
        starts.add(m.end())
    return starts, ends


def on_word_boundary(hebrew, pos):
    if pos <= 0 or pos >= len(hebrew):
        return True
    return (hebrew[pos - 1].isspace() or hebrew[pos].isspace()
            or hebrew[pos - 1] in BREAKERS or hebrew[pos] in BREAKERS)


def audit(path):
    data = json.loads(Path(path).read_text())
    cuts = midword = at_edge = 0
    violations = []
    for page in data.get('pages', []):
        segments = {s['index']: s['hebrew'] for s in page.get('segments', [])}
        for story in page.get('stories', []):
            for side in ('text_span_start', 'text_span_end'):
                span = story.get(side)
                if not span:
                    continue
                hebrew = segments.get(span.get('segment'))
                offset = span.get('char_offset')
                if hebrew is None or offset is None:
                    continue
                cuts += 1
                starts, ends = clause_edges(hebrew)
                if offset in (starts if side.endswith('start') else ends):
                    at_edge += 1
                if not on_word_boundary(hebrew, offset):
                    midword += 1
                    violations.append(
                        f"{page['ref']} seg {span['segment']} {side} @{offset}: "
                        f"...{hebrew[max(0, offset-16):offset]}|{hebrew[offset:offset+16]}...")
    return cuts, midword, at_edge, violations


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('paths', nargs='+')
    ap.add_argument('--strict', action='store_true',
                    help='exit 1 if any cut lands mid-word (use as a CI gate for v11)')
    ap.add_argument('--show', type=int, default=5, help='violations to print per file')
    args = ap.parse_args()

    total = bad = edge = 0
    for path in args.paths:
        cuts, midword, at_edge, violations = audit(path)
        total, bad, edge = total + cuts, bad + midword, edge + at_edge
        pct = lambda n, d: f"{n/d:.0%}" if d else "n/a"
        print(f"{Path(path).name:34s} cuts={cuts:4d}  mid-word={midword:4d} ({pct(midword, cuts)})  "
              f"clause-edge={at_edge:4d} ({pct(at_edge, cuts)})")
        for v in violations[:args.show]:
            print(f"    ! {v}")
        if len(violations) > args.show:
            print(f"    ... {len(violations) - args.show} more")

    if len(args.paths) > 1:
        pct = lambda n, d: f"{n/d:.0%}" if d else "n/a"
        print(f"{'TOTAL':34s} cuts={total:4d}  mid-word={bad:4d} ({pct(bad, total)})  "
              f"clause-edge={edge:4d} ({pct(edge, total)})")

    if args.strict and bad:
        print(f"\nFAIL: {bad} mid-word cut(s). A boundary must sit on a real text unit (Lesson 16).")
        return 1
    if args.strict:
        print("\nPASS: no mid-word cuts.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
