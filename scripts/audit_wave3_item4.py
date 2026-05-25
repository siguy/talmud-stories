#!/usr/bin/env python3
"""
Audit Wave 3 Item 4 (text-internal boundary edits) against Jeff's
2026-04-23 Kiddushin feedback. Story matching is by OVERLAP of the
Jeff-flagged seg range with the detector's current story range (Wave 2
post-processors may have changed start/end), not by exact ID.

For each text-internal boundary case Jeff flagged, print:
  - Story ref + classification
  - Jeff's note (what he wants)
  - Proposed text_span_start / text_span_end slice
  - Hand-call: match Jeff's intent?

For START cases, anchor = the introducer Jeff named (should appear at
start of the kept slice).
For END cases, anchor = the LAST PHRASE Jeff said the story should end
with (should appear in the tail of the kept slice).
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
import os
OUT = Path(os.environ.get(
    'AUDIT_INPUT',
    str(ROOT / 'results' / 'v9' / 'wave3_item4' / 'kiddushin_v8.json')))
FEEDBACK = ROOT / 'validation' / 'feedback' / 'kiddushin_review_2026-04-23.json'

# (review_key, kind, start_anchor_no_nikud, end_kept_anchor_no_nikud)
# end_kept_anchor = the LAST words Jeff says the story should keep.
TEXT_INTERNAL_CASES = [
    ('Kiddushin 8a_9-9',     'start', 'כי הא ד',           None),
    ('Kiddushin 8a_10-10',   'start', 'כי הא ד',           None),
    ('Kiddushin 12a_13-13',  'end',   None,                'אי לא – לא'),
    ('Kiddushin 25a_17-17',  'start', 'מעשה ב',            None),
    ('Kiddushin 26b_4-5',    'end',   None,                'וקיימו חכמים את דבריו'),
    ('Kiddushin 26b_10-10',  'end',   None,                'לסחור בה'),   # Jeff: trim "שמע מינה..." → keep through merchant story
    ('Kiddushin 29b_10-12',  'start', 'כי הא ד',           None),
    ('Kiddushin 32b_2-2',    'end',   None,                'ואיקפד'),
    ('Kiddushin 32b_3-5',    'start', 'מעשה ב',            None),
    ('Kiddushin 33a_16-16',  'start', 'רבי יוחנן',         None),
    ('Kiddushin 52b_2-2',    'end',   None,                'מאן אחלך'),
    ('Kiddushin 57a_0-1',    'start', 'כדתניא',            None),
    ('Kiddushin 66a_7-11',   'start', 'מעשה ב',            None),
    ('Kiddushin 66b_0-5',    'start', 'מעשה ב',            None),
    ('Kiddushin 72a_3-3',    'end',   None,                'בין הנהרות עומדת'),
    ('Kiddushin 72a_10-10',  'end',   None,                'נולד רב יהודה בבבל'),
    ('Kiddushin 79b_6-7',    'both',  None,                None),   # no canonical anchor
]

_NIKUD = re.compile(r'[\u0591-\u05C7]')
def sn(s): return _NIKUD.sub('', s or '')


def parse_ref(key):
    m = re.match(r'(.+?)_(\d+)-(\d+)$', key)
    return m.group(1), int(m.group(2)), int(m.group(3))


def find_story_overlap(pages, ref, st, en):
    """Return (page, story) whose segment range overlaps [st, en], else None,None."""
    for p in pages:
        if p['ref'] != ref:
            continue
        for s in p.get('stories', []):
            if s.get('classification') == 'NOT_A_STORY':
                continue
            ss = s.get('start_segment')
            se = s.get('end_segment')
            if ss is None or se is None:
                continue
            if ss <= en and se >= st:
                return p, s
        return p, None
    return None, None


def main():
    data = json.load(open(OUT))
    fb = json.load(open(FEEDBACK))
    reviews = fb['reviews']

    n_total = 0
    n_correct = 0

    for key, kind, start_anchor, end_anchor in TEXT_INTERNAL_CASES:
        n_total += 1
        ref, st, en = parse_ref(key)
        page, story = find_story_overlap(data['pages'], ref, st, en)
        review = reviews.get(key, {})
        print(f"\n=== {key} ({kind}) ===")
        print(f"  Jeff: {review.get('notes','')[:140]}")
        if story is None:
            print(f"  *** NO LIVE STORY OVERLAPPING segs {st}-{en} ***")
            continue
        print(f"  detector now: {story['start_segment']}-{story['end_segment']} ({story['classification']})")

        segs = {s.get('index', i): s for i, s in enumerate(page['segments'])}

        tss = story.get('text_span_start')
        tse = story.get('text_span_end')
        case_correct = True

        if kind in ('start', 'both'):
            if tss is None:
                print(f"  START: no text_span_start recorded")
                case_correct = False
            else:
                seg = segs.get(tss['segment'], {})
                heb = seg.get('hebrew', '')
                co = tss['char_offset']
                slice_stripped = sn(heb[co:])
                intro = tss.get('introducer', '')
                hit = bool(start_anchor) and slice_stripped.startswith(start_anchor)
                tag = '✓' if hit else ('?' if not start_anchor else '✗')
                print(f"  START: intro={intro!r} offset={co}")
                print(f"         kept={slice_stripped[:90]!r} [{tag}]")
                if start_anchor and not hit:
                    case_correct = False

        if kind in ('end', 'both'):
            if tse is None:
                print(f"  END: no text_span_end recorded")
                case_correct = False
            else:
                seg = segs.get(tse['segment'], {})
                heb = seg.get('hebrew', '')
                co = tse['char_offset']
                kept_stripped = sn(heb[:co]).rstrip(' ,.;:')
                marker_field = tse.get('marker', '')
                hit = bool(end_anchor) and end_anchor in kept_stripped[-80:]
                tag = '✓' if hit else ('?' if not end_anchor else '✗')
                print(f"  END:   marker={marker_field!r} offset={co}")
                print(f"         kept_tail=...{kept_stripped[-80:]!r} [{tag}]")
                if end_anchor and not hit:
                    case_correct = False

        n_correct += int(case_correct)

    print(f"\n--- SUMMARY ---")
    print(f"Total flagged text-internal cases: {n_total}")
    print(f"Cases fully matching Jeff's intent: {n_correct}/{n_total}")
    print(f"Plan gate: ≥10/{n_total}: {'PASS' if n_correct >= 10 else 'FAIL'}")


if __name__ == '__main__':
    main()
