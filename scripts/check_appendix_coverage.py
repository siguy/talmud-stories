#!/usr/bin/env python3
"""Which of our runs ever proposed the appendix cases?

`jeff comms/8-30-2026/Kiddushin missed stories.docx` is the appendix Jeff refers to
as "additional stories that you and Claude found that were not on my list" -- cases
drawn from across many of our runs, which he then annotated Yes / Low confidence and
merged into his Kiddushin list. That merge is what makes those entries NOT BLIND
(FRAMEWORK sec.3): they are in his list because of our output.

This answers the separate question of what we actually detected, per run, which is
capability history rather than provenance -- `NEXT/06` needs it to say which of the
five it should expect to score as misses, and it is the kind of per-capability record
`NEXT/00` is meant to collect.

full = a single proposed span covers every segment the case occupies
PART = a span overlaps it but does not cover it (usually a truncated end)
  -   = nothing proposed there at all

Usage:  python3 scripts/check_appendix_coverage.py
"""
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
from parse_kiddushin_list import grams, overlap          # noqa: E402

HTML = re.compile(r'<[^>]+>')
EXPERT_LIST = PROJECT_ROOT / 'results/expert_lists/kiddushin_2005.json'
SEGMENT_SOURCE = PROJECT_ROOT / 'results/v10/wave4_notrim/kiddushin_v10_notrim.json'
SKIP = {'kiddushin_2005.json', 'event_triage_kiddushin.json', 'kiddushin_pages.json'}
RUN_ORDER = ['v7/kiddushin_v7', 'v8/wave1', 'v8/wave2', 'v9/wave3/', 'v9/wave3_item4',
             'canonical', 'v10/wave4/', 'v10/wave4_notrim', 'v11/wave5/', 'v11/wave5_summaryfix']


def occupied_segments(cases):
    """Which segments each case actually occupies, from the page text."""
    pages = {p['ref']: p for p in json.loads(SEGMENT_SOURCE.read_text())['pages']}
    out = {}
    for c in cases:
        g = grams(c['text'])
        out[c['ref']] = [s['index'] for s in pages[c['ref']]['segments']
                         if overlap(g, grams(HTML.sub('', s.get('hebrew', '')))) > 0.30]
    return out


def main():
    cases = [s for s in json.loads(EXPERT_LIST.read_text())['stories'] if s.get('in_appendix')]
    if not cases:
        sys.exit('no appendix entries found - run scripts/parse_kiddushin_list.py first')
    occ = occupied_segments(cases)
    runs = sorted((p for p in (PROJECT_ROOT / 'results').rglob('*.json')
                   if 'kiddushin' in p.name.lower() and p.name not in SKIP),
                  key=lambda r: next((i for i, o in enumerate(RUN_ORDER) if o in str(r)), 99))

    print(f"{'run':50}" + ''.join(f"{c['ref'].split()[1]:>8}" for c in cases))
    print('-' * (50 + 8 * len(cases)))
    ever = {c['ref']: False for c in cases}
    for r in runs:
        pages = {p['ref']: p for p in json.loads(r.read_text())['pages']}
        row = f"{str(r.relative_to(PROJECT_ROOT / 'results')):50}"
        for c in cases:
            segs = set(occ[c['ref']])
            spans = [set(range(s['start_segment'], s['end_segment'] + 1))
                     for s in pages.get(c['ref'], {}).get('stories', [])]
            full = any(segs <= s for s in spans)
            part = any(segs & s for s in spans)
            ever[c['ref']] |= part
            row += f"{'   full ' if full else '   PART ' if part else '    -   '}"
        print(row)
    print('\nnever proposed in any run:',
          ', '.join(ref for ref, hit in ever.items() if not hit) or 'none')


if __name__ == '__main__':
    main()
