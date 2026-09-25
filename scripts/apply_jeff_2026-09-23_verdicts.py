#!/usr/bin/env python3
"""
Apply Jeff's 2026-09-23 verdicts to the Ketubot and Kiddushin goldens.

Source: validation/feedback/review_2026-09-16_bundle_jeff_2026-09-23.json (10 passages).
Gittin's two verdicts go through scripts/build_gittin_golden.py, which builds that
golden; Yevamot has no golden yet (work/2026-08-30-yevamot-golden.md) and its four
verdicts are banked there.

What changes, and on whose word:

  Ketubot 7a:1      LOW_CONFIDENCE -> BORDERLINE   his verdict, 2026-09-23
  Ketubot 112a:11   LOW_CONFIDENCE -> BORDERLINE   his verdict, 2026-09-23
  Ketubot 15a:0     LOW_CONFIDENCE -> NOT_A_STORY  his verdict, 2026-09-23
  Kiddushin 39b     8-8 -> 7-7                     his verdict (8-10 is the Gemara's
                                                   commentary), his 2026-04-23 note, and
                                                   his 2005 list (kiddushin_041)

  and BORDERLINE for every Ketubot entry where HE used the word "borderline" in an
  earlier round and our auto-applier rounded it to LOW_CONFIDENCE. In those rounds he
  used "low confidence" and "borderline" as one category ("low confidence/borderline");
  the golden could only hold one of them. Now that BORDERLINE is a column (R-C2,
  settled 2026-09-23 on 7a and 112a), those entries go where he put them. The list is
  keyed and each carries the quote; our own prefix "Jeff noted borderline/low
  confidence:" is NOT evidence and is excluded from the match.

Counts: `accepted` (anything not NOT_A_STORY) falls by exactly one, Ketubot 15a:0.
BORDERLINE stays accepted under that definition, as it is for Gittin.

Idempotent: an entry already in its target state is reported and left alone. An entry
that cannot be found is an ERROR, not a skip (Lesson 38).

    python3 scripts/apply_jeff_2026-09-23_verdicts.py            # apply
    python3 scripts/apply_jeff_2026-09-23_verdicts.py --dry-run
"""
import argparse
import json
import logging
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [jeff-2026-09-23] %(message)s',
                    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

VERDICTS = PROJECT_ROOT / 'validation/feedback/review_2026-09-16_bundle_jeff_2026-09-23.json'
KETUBOT = PROJECT_ROOT / 'results/canonical/ketubot_canonical.json'
KIDDUSHIN = PROJECT_ROOT / 'results/canonical/kiddushin_canonical.json'
SOURCE = 'review_2026-09-16_bundle_jeff_2026-09-23'
DATE = '2026-09-23'

# Ketubot entries where Jeff himself said "borderline" in an earlier round. Read out of
# each entry's own `corrections` at run time -- the key only says where to look.
BORDERLINE_IN_HIS_WORDS = [
    ('Ketubot 8a', 9, 9), ('Ketubot 12b', 0, 0), ('Ketubot 14b', 11, 11),
    ('Ketubot 49b', 6, 6), ('Ketubot 52b', 4, 5), ('Ketubot 54a', 13, 14),
    ('Ketubot 54a', 22, 22), ('Ketubot 60b', 5, 9), ('Ketubot 85a', 13, 14),
    ('Ketubot 100b', 17, 18),
]
OUR_PREFIX = re.compile(r"^Jeff('s canonical review| noted borderline/low confidence| says borderline/low confidence)?:\s*")


def find(data, ref, a, b):
    for page in data['pages']:
        if page['ref'] == ref:
            for s in page['stories']:
                if s['start_segment'] == a and s['end_segment'] == b:
                    return s
    raise LookupError(f'{ref} {a}-{b} is not in the golden')


def his_borderline_quote(story):
    for c in story.get('corrections') or []:
        text = OUR_PREFIX.sub('', c.get('reason') or c.get('note') or '')
        if re.search(r'borderline', text, re.I):
            return text, c.get('source')
    return None, None


def reclassify(story, new, correction, log_rows, key):
    old = story['classification']
    if old == new:
        log.info('%s already %s -- unchanged', key, new)
        return
    story['classification'] = new
    story.setdefault('corrections', []).append({**correction, 'action': 'reclassify',
                                                'old': old, 'new': new})
    log_rows.append({'key': key, 'old': old, 'new': new, 'source': correction['source']})
    log.info('%s: %s -> %s', key, old, new)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    reviews = json.loads(VERDICTS.read_text())['reviews']
    ket = json.loads(KETUBOT.read_text())
    kid = json.loads(KIDDUSHIN.read_text())
    ket_log, kid_log = [], []

    # ---- his verdicts on this page
    for key, new in (('Ketubot 7a_1-1', 'BORDERLINE'), ('Ketubot 112a_11-11', 'BORDERLINE'),
                     ('Ketubot 15a_0-0', 'NOT_A_STORY')):
        v = reviews[key]
        expected = {'BORDERLINE': 'borderline', 'NOT_A_STORY': 'no'}[new]
        assert v['is_story'] == expected, f'{key}: file says {v["is_story"]}, script expects {expected}'
        story = find(ket, v['page_ref'], v['start_segment'], v['end_segment'])
        reclassify(story, new, {'date': DATE, 'source': SOURCE, 'rule': 'R-C2' if new == 'BORDERLINE' else 'R-C5',
                                'note': f"Jeff: {v['notes'].strip()}"}, ket_log, key)

    # ---- where he had already said "borderline" in his own words
    for ref, a, b in BORDERLINE_IN_HIS_WORDS:
        story = find(ket, ref, a, b)
        quote, src = his_borderline_quote(story)
        if not quote:
            raise ValueError(f'{ref} {a}-{b}: no "borderline" in his own words -- refusing')
        reclassify(story, 'BORDERLINE',
                   {'date': '2026-09-25', 'source': src, 'rule': 'R-C2',
                    'note': ('His word, from that round, rounded to LOW_CONFIDENCE when the '
                             'golden had no BORDERLINE column: "' + quote.strip() + '"')},
                   ket_log, f'{ref}_{a}-{b}')

    # ---- Kiddushin 39b: the story is segment 7; 8-10 is the Gemara's commentary on it
    v = reviews['Kiddushin 39b_8-10']
    assert v['is_story'] == 'no'
    try:
        story = find(kid, 'Kiddushin 39b', 8, 8)
    except LookupError:
        find(kid, 'Kiddushin 39b', 7, 7)
        log.info('Kiddushin 39b already 7-7 -- unchanged')
    else:
        story['start_segment'] = story['end_segment'] = 7
        story.setdefault('corrections', []).append({
            'date': DATE, 'source': SOURCE, 'action': 'rebound', 'rule': 'R-B4',
            'old_range': '8-8', 'new_range': '7-7',
            'note': ("Segment 7 is the incident R. Ya'akov reports (his 2005 list, "
                     "kiddushin_041, begins there; his 2026-04-23 note: 'The previous line "
                     "should be included'). Segments 8-10 are the Gemara's commentary: "
                     f"\"{v['notes'].strip()}\""),
        })
        kid_log.append({'key': 'Kiddushin 39b_8-8 -> 7-7', 'source': SOURCE})
        log.info('Kiddushin 39b: 8-8 -> 7-7')

    for data, rows in ((ket, ket_log), (kid, kid_log)):
        data.setdefault('jeff_2026_09_23', {'source': str(VERDICTS.relative_to(PROJECT_ROOT)),
                                            'applied': []})['applied'].extend(rows)
    for data, added in ((ket, ('R-C2', 'R-C5')), (kid, ('R-B4',))):
        rules = data.setdefault('rules_applied', [])
        rules.extend(r for r in added if r not in rules)

    log.info('Ketubot: %d changed · Kiddushin: %d changed', len(ket_log), len(kid_log))
    if args.dry_run:
        log.info('dry run -- nothing written')
        return 0
    KETUBOT.write_text(json.dumps(ket, ensure_ascii=False, indent=2))
    KIDDUSHIN.write_text(json.dumps(kid, ensure_ascii=False, indent=2))
    log.info('wrote %s, %s', KETUBOT.name, KIDDUSHIN.name)
    return 0


if __name__ == '__main__':
    sys.exit(main())
