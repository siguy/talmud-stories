#!/usr/bin/env python3
"""
Diff Kiddushin v7 (baseline) vs Wave 1 output.

Verifies plan's expected wins:
  - #75 (70b) + #77 (71b): first-segment skip fixed
  - #11, 21, 26: false continuation bridges removed
  - #58 (50b): Mishnah-only story moved to mishnah_stories
  - 45a, 53a: new stories detected (Issue #5 introducer override)
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
OLD = ROOT / 'results' / 'v7' / 'kiddushin_v7.json'
NEW = ROOT / 'results' / 'v8' / 'wave1' / 'kiddushin_v8.json'


def real_stories(page):
    return [s for s in page.get('stories', [])
            if s.get('classification') != 'NOT_A_STORY']


def index_pages(data):
    return {p['ref']: p for p in data['pages']}


def main():
    with open(OLD) as f: old = json.load(f)
    with open(NEW) as f: new = json.load(f)
    old_p = index_pages(old)
    new_p = index_pages(new)

    print('=' * 60)
    print('  Wave 1 diff: Kiddushin baseline vs Wave 1')
    print('=' * 60)

    # Per-page story counts
    old_total = sum(len(real_stories(p)) for p in old['pages'])
    new_total = sum(len(real_stories(p)) for p in new['pages'])
    print(f"\nTotal real stories: {old_total} → {new_total}")

    # Cross-page stories
    def cross_page(pages):
        out = []
        for p in pages:
            for s in real_stories(p):
                if s.get('spans_pages'):
                    out.append((p['ref'], s.get('spans_pages')[-1],
                                s.get('start_segment'), s.get('end_segment'),
                                s.get('start_segment_page2'),
                                s.get('end_segment_page2')))
        return out

    old_cp = cross_page(old['pages'])
    new_cp = cross_page(new['pages'])
    print(f"\nCross-page stories: {len(old_cp)} → {len(new_cp)}")

    old_keys = {(a, b) for a, b, *_ in old_cp}
    new_keys = {(a, b) for a, b, *_ in new_cp}
    removed = old_keys - new_keys
    added = new_keys - old_keys
    if removed:
        print('  Removed bridges:')
        for k in sorted(removed):
            print('    -', k[0], '→', k[1])
    if added:
        print('  Added bridges:')
        for k in sorted(added):
            print('    +', k[0], '→', k[1])

    # Check specific cases
    print('\n--- Plan-specific checks ---')

    targets = ['Kiddushin 12b', 'Kiddushin 29b', 'Kiddushin 31a',
               'Kiddushin 39b', 'Kiddushin 70a', 'Kiddushin 70b',
               'Kiddushin 71b', 'Kiddushin 45a', 'Kiddushin 53a',
               'Kiddushin 50b']
    for ref in targets:
        o = old_p.get(ref, {})
        n = new_p.get(ref, {})
        os_ = real_stories(o)
        ns_ = real_stories(n)
        print(f'\n{ref}:')
        print(f'  OLD: skipped={o.get("skipped_by_triage")} stories={len(os_)}')
        for s in os_:
            print(f'    {s.get("classification")} {s.get("start_segment")}-{s.get("end_segment")} spans={s.get("spans_pages")} p2={s.get("start_segment_page2")}-{s.get("end_segment_page2")}')
        print(f'  NEW: skipped={n.get("skipped_by_triage")} stories={len(ns_)} mishnah_filtered={len(n.get("mishnah_stories", []))}')
        for s in ns_:
            tags = []
            if s.get('first_segment_skip_fix'): tags.append('SEG0FIX')
            if s.get('continuation_check_extended'): tags.append('4f')
            print(f'    {s.get("classification")} {s.get("start_segment")}-{s.get("end_segment")} spans={s.get("spans_pages")} p2={s.get("start_segment_page2")}-{s.get("end_segment_page2")} {tags}')
        for s in n.get('mishnah_stories', []):
            print(f'    [MISHNAH] {s.get("classification")} {s.get("start_segment")}-{s.get("end_segment")}')


if __name__ == '__main__':
    main()
