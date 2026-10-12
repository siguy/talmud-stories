#!/usr/bin/env python3
"""
Apply Jeff's 2026-10-07 verdicts to the Ketubot and Kiddushin goldens.

Source: `jeff comms/10-7-2026/Brief response, 10.7.docx`, his answers to the eight
passages in the 2026-10-02 email (`comms/2026-10-02-email-jeff-DRAFT.md`). Each
question set two of his own rulings against each other; he answered seven of the eight
passages (4B, Ketubot 67b:17, is blank and is re-asked). He also told Simon that his 2005
lists were initial attempts and his recent rulings win -- so where a verdict here
disagrees with the list, the golden follows the verdict, and the list entry is annotated
in `results/expert_lists/superseded_by_rule.json` rather than edited.

What changes, and on whose word (segment indices 0-based; the email's Sefaria links
are 1-based):

  Q  passage              golden before        after         rule
  1A Kiddushin 80b:11     LOW_CONFIDENCE    -> BORDERLINE    R-C6
  2A Ketubot 21b:0        LOW_CONFIDENCE    -> NOT_A_STORY   R-C2
  2B Ketubot 53a:11       YES (2005 list)   -> NOT_A_STORY   R-C2
  3A Ketubot 50b:4        LOW_CONFIDENCE    -> NOT_A_STORY   R-C0 (his Feb `no` stands)
  3B Ketubot 50a:10       absent            -> BORDERLINE    R-C2 (added)
  4A Ketubot 61a:14       absent            -> YES           R-C3 (added)

1B (Yevamot 107b) has no golden to change; it is in the annotation file, and in the
Yevamot golden item.

Counts: Ketubot entries 187 -> 189; accepted (anything not NOT_A_STORY) 163 -> 162.
Kiddushin unchanged (96 / 85).

Idempotent: an entry already in its target state is reported and left alone. An entry
that cannot be found is an ERROR, not a skip (Lesson 38).

    python3 scripts/apply_jeff_2026-10-07_verdicts.py --dry-run
    python3 scripts/apply_jeff_2026-10-07_verdicts.py
"""
import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [jeff-2026-10-07] %(message)s',
                    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

KETUBOT = PROJECT_ROOT / 'results/canonical/ketubot_canonical.json'
KIDDUSHIN = PROJECT_ROOT / 'results/canonical/kiddushin_canonical.json'
SOURCE = 'jeff comms/10-7-2026/Brief response, 10.7.docx'
DATE = '2026-10-07'

# (question, ref, start, end, expected classification before, after, rule, his words)
RECLASSIFY = [
    ('1A', 'Kiddushin 80b', 11, 11, 'LOW_CONFIDENCE', 'BORDERLINE', 'R-C6',
     'borderline. This is an unusual case, as the “incident” is not narrated in full, and has '
     'to be filled in based on the context and with the help of the Talmudic commentaries. If '
     'the Talmud had provided the entire story, it would have counted as a story. But since so '
     'much is missing and basically conjectured, or filled in through an oral tradition that the '
     'Talmudic commentaries had access to, we should consider it borderline.'),
    ('2A', 'Ketubot 21b', 0, 0, 'LOW_CONFIDENCE', 'NOT_A_STORY', 'R-C2',
     'not a story. There is not really enough conflict here to make the dialogue into a story. '
     'That one rabbis praises a ruling and another rebukes him or questions the praise is not '
     'that exceptional in Talmudic dialogue, so I would not count it as a story.'),
    ('2B', 'Ketubot 53a', 11, 11, 'YES', 'NOT_A_STORY', 'R-C2',
     'not a story. No conflict or change. Rav Hisda is just explaining why he accepts the '
     'ruling, which is because it is attributed to a great rabbi. This is standard rabbinic '
     'dialogue and not a story.'),
    ('3A', 'Ketubot 50b', 4, 4, 'LOW_CONFIDENCE', 'NOT_A_STORY', 'R-C0',
     'not a story. The daughters do come to a rabbi, and he then makes a ruling. But there is '
     'not really another action or change that is narrated.'),
]

# (question, ref, start, end, classification, rule, summary, his words)
ADD = [
    ('3B', 'Ketubot 50a', 10, 10, 'BORDERLINE', 'R-C2',
     'Rav Yitzhak bar Yosef finds R. Abbahu in the assembly at Usha, asks who taught the Usha '
     'ordinance, and learns it from him forty times until it is "as if in his pocket".',
     'borderline. That one rabbi learned from another rabbi 40 times could be considered 40 '
     'events, even if they are mainly verbal, i.e., one rabbi teaching another. But then we are '
     'told the student knew is very well (=as if it was in his pocket), which could be '
     'considered a second event, and a change. But since it is mainly about rabbinic teaching, '
     'speech-acts, I would still consider it borderline.'),
    ('4A', 'Ketubot 61a', 14, 14, 'YES', 'R-C3',
     'Two pious men: one fed the waiter before the meal, the other after it; Elijah spoke with '
     'the first and not with the second.',
     'story. In this case there are at least two actions and change. The pious man’s continuous '
     'action, feeding the waiter before the meal, leads to a change—that Elijah visits him. (And '
     'the reverse for the other pious man)'),
]


def page(data, ref):
    for p in data['pages']:
        if p['ref'] == ref:
            return p
    raise LookupError(f'{ref} is not a page in the golden')


def find(data, ref, a, b):
    for s in page(data, ref)['stories']:
        if s['start_segment'] == a and s['end_segment'] == b:
            return s
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    goldens = {'Ketubot': json.loads(KETUBOT.read_text()), 'Kiddushin': json.loads(KIDDUSHIN.read_text())}
    applied = {t: [] for t in goldens}

    for q, ref, a, b, before, after, rule, words in RECLASSIFY:
        data = goldens[ref.split()[0]]
        story = find(data, ref, a, b)
        if story is None:
            raise LookupError(f'{q}: {ref} {a}-{b} is not in the golden')
        old = story['classification']
        if old == after:
            log.info('%s %s %d-%d already %s -- unchanged', q, ref, a, b, after)
            continue
        if old != before:
            raise ValueError(f'{q}: {ref} {a}-{b} is {old}, script expects {before} -- refusing')
        story['classification'] = after
        story.setdefault('corrections', []).append({
            'date': DATE, 'source': SOURCE, 'action': 'reclassify', 'rule': rule,
            'old': old, 'new': after, 'note': f'Jeff ({q}): {words}'})
        applied[ref.split()[0]].append({'key': f'{ref}_{a}-{b}', 'question': q, 'old': old, 'new': after})
        log.info('%s %s %d-%d: %s -> %s (%s)', q, ref, a, b, old, after, rule)

    for q, ref, a, b, cls, rule, summary, words in ADD:
        data = goldens[ref.split()[0]]
        if find(data, ref, a, b) is not None:
            log.info('%s %s %d-%d already present -- unchanged', q, ref, a, b)
            continue
        stories = page(data, ref)['stories']
        stories.append({
            'start_segment': a, 'end_segment': b, 'classification': cls,
            'one_sentence_summary': summary, 'source': 'jeff_verdict', 'rules': ['R-C1', rule],  # R-C1: every entry records its corpus
            'provenance': {
                'source': 'jeff_verdict', 'added': '2026-10-09', 'verdict_date': DATE,
                'verdict_source': SOURCE, 'question': q, 'his_words': words,
                'added_by': 'scripts/apply_jeff_2026-10-07_verdicts.py',
                'expert_confirmed_boundaries': False,
                'boundary_caveat': ('Segment-level, as shown to him in the 2026-10-02 email '
                                    '(Sefaria link). He ruled on the passage, not on a start/end.')},
            'corpus': 'talmud'})
        stories.sort(key=lambda s: (s['start_segment'], s['end_segment']))
        applied[ref.split()[0]].append({'key': f'{ref}_{a}-{b}', 'question': q, 'old': None, 'new': cls})
        log.info('%s %s %d-%d: added as %s (%s)', q, ref, a, b, cls, rule)

    for t, data in goldens.items():
        data.setdefault('jeff_2026_10_07', {'source': SOURCE, 'applied': []})['applied'].extend(applied[t])
        rules = data.setdefault('rules_applied', [])
        rules.extend(r for r in sorted({x[6] for x in RECLASSIFY if x[1].startswith(t)}
                                       | {x[5] for x in ADD if x[1].startswith(t)}) if r not in rules)

    log.info('Ketubot: %d changed · Kiddushin: %d changed', len(applied['Ketubot']), len(applied['Kiddushin']))
    if args.dry_run:
        log.info('dry run -- nothing written')
        return 0
    KETUBOT.write_text(json.dumps(goldens['Ketubot'], ensure_ascii=False, indent=2))
    KIDDUSHIN.write_text(json.dumps(goldens['Kiddushin'], ensure_ascii=False, indent=2))
    log.info('wrote %s, %s', KETUBOT.name, KIDDUSHIN.name)
    return 0


if __name__ == '__main__':
    sys.exit(main())
