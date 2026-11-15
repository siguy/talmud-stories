#!/usr/bin/env python3
"""
Undo a boundary we applied by reading Jeff's segment numbers in the wrong base.

On 2026-05-25 we sent Jeff "Ketubot 106a segs 1-2 -- Elijah stops visiting Rav Anan after a
legal error" (comms/sent/2026-05-25-email-jeff-wave3.md). The numbers were our 0-based
indices; the email did not say so, and its only link was the Sefaria page, which numbers
segments from 1. His reply (Gmail, 2026-05-26, verbatim):

    Ketubot 106a segs 1-2*. This is a story, but the story is segments 2-3, not
    really 1.

scripts/apply_jeff_2026-06-03_corrections.py read "2-3" as 0-based and stretched the
Rav Yosef famine entry (106a 3-3) back to 2-3. Read 1-based, his words fit the text and the
0-based reading does not (docs/findings/2026-11-14-jeff-segment-numbering.md):

  1-based  2-3 = our 1-2 = Elijah stops visiting, Rav Anan fasts, the box, Seder Eliyahu --
                 exactly the passage we described, and his own 2005 list (ketubot_129)
           "not really 1" = our 0 = Rav Nahman sets the orphans' case aside -- the end of
                 the fish story, which his 2005 list ends there (ketubot_128)
  0-based  2-3 = the box (the tail of the Elijah story) + the Rav Yosef famine -- two
                 unrelated passages, cutting the Elijah story off from its own opening

So the 2-3 entry is reverted to 3-3: the famine passage alone, the extent he rated HIGH on
2026-03-17 ("Mainly a request and a rejections"). Whether the Elijah passage (our 1-2) is
its own story or the end of the 105b fish story stitched to 106a 0-2 is NOT settled here:
his 2005 list, his 2026-02-26 note and this reply say separate; his 2026-03-08 approval of
the stitched 105b entry says one. That is `jeff:106a-elijah-split` in comms/JEFF.md.

The other three items of that reply (7a seg 1, 26a seg 9, 102a seg 6) were verdicts on the
passages we described, not boundaries; none changes here (see the finding's table).

Story counts do not change (a boundary only). Idempotent: an entry already fixed is reported
and left alone. An entry in neither state is an ERROR, never a skip (Lesson 38).

    python3 scripts/fix_jeff_segment_numbering_2026-11-14.py --dry-run
    python3 scripts/fix_jeff_segment_numbering_2026-11-14.py
"""
import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [jeff-seg-base] %(message)s',
                    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

KETUBOT = PROJECT_ROOT / 'results/canonical/ketubot_canonical.json'
FIXED_BY = 'scripts/fix_jeff_segment_numbering_2026-11-14.py'
DATE = '2026-11-14'
FINDING = 'docs/findings/2026-11-14-jeff-segment-numbering.md'

HIS_WORDS = 'Ketubot 106a segs 1-2*. This is a story, but the story is segments 2-3, not really 1.'

# (ref, wrong (start, end), right (start, end), evidence)
FIXES = [
    ('Ketubot 106a', (2, 3), (3, 3), {
        'what_we_sent': ('2026-05-25 email: "Ketubot 106a segs 1-2 -- Elijah stops visiting Rav Anan after a '
                         'legal error; Rav Anan fasts until he returns", our 0-based indices, base not stated, '
                         'linked only to the Sefaria page (1-based)'),
        'his_words': HIS_WORDS,
        'his_words_source': 'Jeff email to Simon, 2026-05-26 (Gmail), quoted verbatim',
        'misread_by': 'scripts/apply_jeff_2026-06-03_corrections.py (read 0-based: 3-3 -> 2-3)',
        'one_based_reading': ('2-3 = our 1-2, the Elijah passage we described (= his 2005 list ketubot_129); '
                              '"not really 1" = our 0, Rav Nahman setting the orphans\' case aside, where his '
                              '2005 list ends the fish story (ketubot_128)'),
        'zero_based_reading': ('2-3 = the box (tail of the Elijah story) + the Rav Yosef famine: two unrelated '
                               'passages, the Elijah story cut from its own opening -- does not fit'),
        'restores': '3-3, the famine passage he rated HIGH on 2026-03-17 ("Mainly a request and a rejections")',
        'left_open': 'jeff:106a-elijah-split (comms/JEFF.md)',
    }),
]


def find(data, ref, a, b):
    pages = [p for p in data['pages'] if p['ref'] == ref]
    if not pages:
        raise LookupError(f'{ref} is not a page in the golden')
    return next((s for s in pages[0]['stories'] if s['start_segment'] == a and s['end_segment'] == b), None)


def counts(data):
    stories = [s for p in data['pages'] for s in p['stories']]
    return len(stories), sum(s['classification'] != 'NOT_A_STORY' for s in stories)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    data = json.loads(KETUBOT.read_text())
    before = counts(data)
    log.info('Ketubot golden: %d entries, %d accepted', *before)

    applied = []
    for ref, (wa, wb), (ra, rb), evidence in FIXES:
        wrong, right = find(data, ref, wa, wb), find(data, ref, ra, rb)
        if right is not None and wrong is None and any(c.get('fixed_by') == FIXED_BY
                                                       for c in right.get('corrections', [])):
            log.info('%s already %d-%d -- unchanged', ref, ra, rb)
            continue
        if wrong is None or right is not None:
            raise RuntimeError(f'{ref}: expected one entry at {wa}-{wb} and none at {ra}-{rb}; found '
                               f'{wa}-{wb}={wrong is not None}, {ra}-{rb}={right is not None}. Refusing.')
        if not any(c.get('date') == '2026-06-03' and c.get('new_range') == f'{wa}-{wb}'
                   for c in wrong.get('corrections', [])):
            raise RuntimeError(f'{ref} {wa}-{wb} carries no 2026-06-03 correction to {wa}-{wb}; '
                               f'this is not the entry the misread produced. Refusing.')
        wrong['start_segment'], wrong['end_segment'] = ra, rb
        wrong['corrections'].append({
            'date': DATE, 'action': 'revert_misread_boundary', 'old_range': f'{wa}-{wb}',
            'new_range': f'{ra}-{rb}', 'fixed_by': FIXED_BY, 'finding': FINDING, 'evidence': evidence,
            'note': ('The 2026-06-03 extend_start read his segment numbers 0-based; he was counting '
                     "Sefaria's 1-based segments. Measured against the text and his 2005 list."),
        })
        applied.append({'key': f'{ref}_{wa}-{wb} -> {ra}-{rb}', 'fixed_by': FIXED_BY, 'finding': FINDING})
        log.info('%s: %d-%d -> %d-%d', ref, wa, wb, ra, rb)

    after = counts(data)
    if after != before:
        raise RuntimeError(f'story counts moved {before} -> {after}; a boundary fix must not change them')
    if not applied:
        log.info('nothing to do')
        return 0
    data.setdefault('jeff_segment_numbering_fix_2026_11_14', {'finding': FINDING, 'applied': []})['applied'].extend(applied)
    if args.dry_run:
        log.info('dry run -- nothing written (%d fix)', len(applied))
        return 0
    KETUBOT.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    log.info('wrote %s (%d fix; counts unchanged %d/%d)', KETUBOT.relative_to(PROJECT_ROOT), len(applied), *after)
    return 0


if __name__ == '__main__':
    sys.exit(main())
