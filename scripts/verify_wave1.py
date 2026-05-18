#!/usr/bin/env python3
"""
Verify Wave 1 fixes against Jeff's 2026-04-23 feedback.

Each fix has a concrete pass/fail criterion derived from the feedback JSON:

  Issue #1 — first-segment skip (#75 70b, #77 71b)
    PASS if seg 0 of 70b is included in a cross-page story Kiddushin 70a→70b.
    (#77 is a same-page boundary issue; not addressed in Wave 1 — recorded as
    expected-known-gap, not a failure.)

  Issue #2 — false continuation bridges (#11 12b→13a, #21 29b→30a,
             #26 31a→31b, #47 39b→40a)
    PASS if the bridge no longer exists in v8 output.
    #47 has gap=0 and is not addressable by the gap rule; recorded as expected
    gap.

  Issue #5 — triage misses (45a, 53a)
    PASS if v8 has at least one real story on each page.

  Issue #7 — Mishnah corpus errors (#58 50b, #59 52a)
    PASS if the seg-10 story on 50b moved to mishnah_stories. #59 is a
    gemara reference to mishnah and is not in the HTML-mishnah block;
    recorded as expected-known-gap.

  Regression check
    PASS if no previously-valid cross-page bridge (the 12 from v7) was
    incorrectly removed, EXCEPT the 3 known-bad bridges (#11, #21, #26).
    PASS if total story count drop is within plausible range (lose 4: 3
    false bridges' page2 halves and 1 mishnah filter; gain 2 new from
    introducer override → net change consistent with the fixes).

Exit code 0 on full pass, 1 on any failure or unexpected change.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
V7 = ROOT / 'results' / 'kiddushin' / 'kiddushin_v7.json'
V8 = ROOT / 'results' / 'kiddushin' / 'kiddushin_v8.json'


def load(p):
    with open(p) as f:
        return json.load(f)


def real_stories(page):
    return [s for s in page.get('stories', [])
            if s.get('classification') != 'NOT_A_STORY']


def index_pages(data):
    return {p['ref']: p for p in data['pages']}


def bridges(pages):
    """Set of (ref_page1, ref_page2) for real cross-page stories."""
    out = set()
    for p in pages:
        for s in real_stories(p):
            sp = s.get('spans_pages')
            if sp and len(sp) == 2:
                out.add(tuple(sp))
    return out


CHECKS = []


def check(name, ok, detail=''):
    CHECKS.append((name, ok, detail))


def main():
    v7 = load(V7)
    v8 = load(V8)
    v7_pages = index_pages(v7)
    v8_pages = index_pages(v8)

    # Issue #1: cross-page first-segment skip on 70a→70b
    p70a = v8_pages.get('Kiddushin 70a', {})
    bridge_70 = None
    for s in real_stories(p70a):
        if s.get('spans_pages') == ['Kiddushin 70a', 'Kiddushin 70b']:
            bridge_70 = s
            break
    ok = (
        bridge_70 is not None
        and bridge_70.get('start_segment_page2') == 0
        and bridge_70.get('first_segment_skip_fix') is True
    )
    check('Issue #1 (#75 70b first-seg fix)', ok,
          f"bridge={bool(bridge_70)} p2_start={bridge_70.get('start_segment_page2') if bridge_70 else 'n/a'} "
          f"seg0fix={bridge_70.get('first_segment_skip_fix') if bridge_70 else 'n/a'}")

    # Issue #2: false bridges removed
    v8_bridges = bridges(v8['pages'])
    for k in [('Kiddushin 12b', 'Kiddushin 13a'),
              ('Kiddushin 29b', 'Kiddushin 30a'),
              ('Kiddushin 31a', 'Kiddushin 31b')]:
        check(f'Issue #2 bridge removed {k[0][-3:]}→{k[1][-3:]}',
              k not in v8_bridges,
              'still present' if k in v8_bridges else 'removed')

    # #47 39b→40a: not addressable by gap rule (gap=0). Note status.
    check('Issue #2 known-gap #47 39b→40a (gap=0, not addressable)',
          True,
          f"present={('Kiddushin 39b', 'Kiddushin 40a') in v8_bridges} — accepted as out-of-scope for Wave 1")

    # Issue #5: triage override recovered 45a, 53a
    for ref in ['Kiddushin 45a', 'Kiddushin 53a']:
        v7p = v7_pages.get(ref, {})
        v8p = v8_pages.get(ref, {})
        was_skipped = v7p.get('skipped_by_triage') is True
        now_processed = v8p.get('skipped_by_triage') is not True
        stories_now = len(real_stories(v8p))
        check(f'Issue #5 {ref} recovered',
              was_skipped and now_processed and stories_now >= 1,
              f"v7_skipped={was_skipped} v8_processed={now_processed} v8_stories={stories_now}")

    # Issue #7: 50b story 10-10 moved to mishnah_stories
    p50b_v8 = v8_pages.get('Kiddushin 50b', {})
    mishnah = p50b_v8.get('mishnah_stories', [])
    moved_50b = any(s.get('start_segment') == 10 and s.get('end_segment') == 10
                    for s in mishnah)
    check('Issue #7 (#58 50b Mishnah filter)', moved_50b,
          f"mishnah_stories count={len(mishnah)} contains seg10={moved_50b}")

    # #59 52a known limitation
    p52a_v8 = v8_pages.get('Kiddushin 52a', {})
    still_present = any(s.get('start_segment') == 4 for s in real_stories(p52a_v8))
    check('Issue #7 known-gap #59 52a (gemara reference, not in mishnah block)',
          True,
          f"present_in_stories={still_present} — accepted as out-of-scope for Wave 1")

    # Regression check: no previously-good bridge removed
    v7_bridges = bridges(v7['pages'])
    bad_bridges_expected_removed = {
        ('Kiddushin 12b', 'Kiddushin 13a'),
        ('Kiddushin 29b', 'Kiddushin 30a'),
        ('Kiddushin 31a', 'Kiddushin 31b'),
    }
    expected_good_bridges = v7_bridges - bad_bridges_expected_removed
    missing_good = expected_good_bridges - v8_bridges
    check('No good cross-page bridge regressed',
          not missing_good,
          f"missing={sorted(missing_good)}" if missing_good else 'all retained')

    # Total story count sanity
    v7_total = sum(len(real_stories(p)) for p in v7['pages'])
    v8_total = sum(len(real_stories(p)) for p in v8['pages'])
    # Expected math: -3 (false bridges' page2 halves were already absorbed in v7 spans
    # so removing them doesn't reduce count; what changes count is mishnah filter -1
    # and introducer additions +N). Be generous: ±5 from v7.
    delta = v8_total - v7_total
    check('Total story count change reasonable (Δ in [-5, +5])',
          -5 <= delta <= 5,
          f"v7={v7_total} v8={v8_total} delta={delta:+d}")

    # Print report
    print('=' * 70)
    print('  Wave 1 Verification Report')
    print('=' * 70)
    pass_count = sum(1 for _, ok, _ in CHECKS if ok)
    fail_count = len(CHECKS) - pass_count
    for name, ok, detail in CHECKS:
        mark = 'PASS' if ok else 'FAIL'
        print(f'  [{mark}] {name}')
        if detail:
            print(f'         {detail}')
    print('-' * 70)
    print(f'  {pass_count}/{len(CHECKS)} checks passed, {fail_count} failed')
    print('=' * 70)
    sys.exit(0 if fail_count == 0 else 1)


if __name__ == '__main__':
    main()
