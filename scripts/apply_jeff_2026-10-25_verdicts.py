#!/usr/bin/env python3
"""
Apply Jeff's 2026-10-25 reply to the goldens and to the 2005-list annotations.

Source: `jeff comms/10-25-2026/reply.md`, his answers to the two questions of the
2026-10-11 email (`comms/sent/2026-10-11-email-jeff.md`):

  Q1  one event, then a ruling or discussion, nothing changes afterwards ->
      *"these cases and similar ones are not a story rather than that they are
      borderline"*. An order that only implies someone acted does not count: *"it is
      not really stated explicitly"*.
  2A  Ketubot 65a (Rav Nehemya apportions wine) -> borderline: *"a little more than a
      ruling"*. 2B Yevamot 45a and 2C Gittin 89a -> not a story.

Two tiers, because "and similar ones" is his generalisation but WHICH passages are
similar is ours (Lesson 27: count what a rule touches before applying it):

  direct       passages he named, in this reply or in the question he answered
  description  passages whose borderline he justified, in his own February words, as
               exactly this shape ("basically one event and then a legal ruling and
               discussion"). Not named by him; applied only with --tier description

Printed and never applied: FLAGGED -- his borderlines that are near the shape but have
a feature his 65a answer could save (an act of compulsion, a ruling that changes
something) -- and the list stories the v5 judges rejected under the narrowed rule
(results/consensus/phase1/bl_v5_*.json): those are the judges' reading, CIRCULAR.

Segment indices 0-based; the email's Sefaria links are 1-based. Idempotent; an entry
not in its expected prior state is an ERROR, not a skip (Lesson 38).

    python3 scripts/apply_jeff_2026-10-25_verdicts.py --dry-run
    python3 scripts/apply_jeff_2026-10-25_verdicts.py --dry-run --tier description
    python3 scripts/apply_jeff_2026-10-25_verdicts.py [--tier description]
"""
import argparse
import json
import logging
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
from measure_recall_vs_expert_list import apply_superseded, load_expert_json, parse_expert_doc, SUPERSEDED  # noqa: E402

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [jeff-2026-10-25] %(message)s',
                    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

GOLDENS = {t: PROJECT_ROOT / f'results/canonical/{t.lower()}_canonical.json'
           for t in ('Ketubot', 'Kiddushin', 'Gittin')}
LISTS = {'Ketubot': ('doc', PROJECT_ROOT / 'jeff comms/b.ketubot (1).doc'),
         'Yevamot': ('json', PROJECT_ROOT / 'results/expert_lists/yevamot_2005.json'),
         'Gittin': ('json', PROJECT_ROOT / 'results/expert_lists/gittin_2005.json')}
SOURCE = 'jeff comms/10-25-2026/reply.md'
DATE = '2026-10-25'

Q1 = ('these cases and similar ones are not a story rather than that they are borderline. '
      '... Shmuel orders R. Benai to sustain the daughters. You could argue that the interaction '
      'implies that R. Benai did so. But it is not really stated explicitly. So probably better '
      'to consider such cases as not even stories rather than borderline.')
A2 = ('Borderline. In this case, it is a little more than a ruling. It is a courtroom drama, and '
      'the rabbi "apportions" wine for the woman, that is, grants her a wine allowance. I think '
      'this creates more dynamism, that is, more change. So it is borderline. Had the rabbi just '
      'stated something, ("Said R. Ami...") it would not even be borderline.')
B2 = 'Yes, I think we can reject this one. Not a story.'
C2 = 'This one too should not be considered a story'

# (tier, question, ref, start, end, expected before, after, rule, his words, his February words)
# expected before None = absent from the golden: added, with provenance.
GOLDEN = [
    ('direct', 'Q1', 'Ketubot 50b', 9, 10, 'LOW_CONFIDENCE', 'NOT_A_STORY', 'R-C0', Q1,
     'just one real event and then discussion'),
    ('direct', 'Q1', 'Ketubot 51a', 1, 2, None, 'NOT_A_STORY', 'R-C0', Q1,
     'really just one event, then a legal discussion'),
    ('direct', 'Q1', 'Ketubot 50b', 4, 4, 'NOT_A_STORY', 'NOT_A_STORY', 'R-C0', Q1, None),
    ('direct', 'Q1', 'Kiddushin 39a', 12, 13, 'NOT_A_STORY', 'NOT_A_STORY', 'R-C0', Q1, None),
    ('direct', '2A', 'Ketubot 65a', 10, 10, 'LOW_CONFIDENCE', 'BORDERLINE', 'R-C0', A2, None),
    ('direct', '2C', 'Gittin 89a', 19, 19, 'YES', 'NOT_A_STORY', 'R-C0', C2, None),
    ('description', 'Q1', 'Ketubot 53a', 12, 12, 'LOW_CONFIDENCE', 'NOT_A_STORY', 'R-C0', Q1,
     'Basically one event and a discussion about it.'),
]

# 2005-list annotations (results/expert_lists/superseded_by_rule.json). `ref` and
# `text_starts` as the recall harness's own reader sees the row; matched through
# apply_superseded, so a wrong one raises here exactly as it would there.
# (tier, question, tractate, ref, list_id, text_starts, ruling, his words)
LIST = [
    ('direct', 'Q1', 'Ketubot', 'Ketubot 51a', 'ketubot_030', 'ההוא יתום ויתומה דאתו לקמיה דרבא', 'not', Q1),
    ('direct', '2A', 'Ketubot', 'Ketubot 65b', 'ketubot_065',
     'דביתהו דרב יוסף בריה דרבא אתאי לקמיה דרב נחמיה', 'borderline', A2),
    ('direct', '2B', 'Yevamot', 'Yevamot 45a', 'yevamot_014', 'ואף רב מתנה מורה בה להיתירא', 'not', B2),
    ('direct', '2C', 'Gittin', 'Gittin 89a', 'gittin_111',
     'ההיא דנפק עלה קלא דאיקדשה לחד מבני פלניא', 'not', C2),
    ('description', 'Q1', 'Ketubot', 'Ketubot 53a', 'ketubot_034', 'יתיב ר"נ ועולא ואבימי בר רב פפי', 'not', Q1),
]

# Near the shape, but his 65a line ("a little more than a ruling ... more change") could
# keep them borderline. His call, not ours -- printed for the next email or phase 2.
FLAGGED = [
    ('Ketubot 77a', 8, 8, '"one event following by a ruling. But it has an implied change" -- his Q1 reasoning says '
     'implied change does not count, but this is the Mishnah story he affirmed (R-C1, tests/test_golden_rules.py); '
     'ask, do not apply'),
    ('Ketubot 54a', 13, 14, 'his February note names the shape ("basically one event and then a legal ruling and '
     'discussion"), but Rav Nahman CHANGES his ruling -- the 65a line may keep it borderline (Simon, 2026-10-26)'),
    ('Ketubot 49b', 6, 6, 'basically one event ... He forced a man to give charity -- compulsion is an act, cf. 65a'),
    ('Ketubot 100b', 17, 18, 'a situation, then a request for a ruling; "the change in outcome is absent, or at best, implied" (shape 3)'),
    ('Ketubot 54a', 21, 21, 'temporal progression, but "the result of the depreciated dowry is just a ruling" (shape 3)'),
]
V5_RUNS = [PROJECT_ROOT / f'results/consensus/phase1/bl_{v}_{m}.json' for v in ('v4', 'v5') for m in ('gemini', 'claude')]


def find(data, ref, a, b):
    pages = [p for p in data['pages'] if p['ref'] == ref]
    if not pages:
        raise LookupError(f'{ref} is not a page in the golden')
    return pages[0], next((s for s in pages[0]['stories']
                           if s['start_segment'] == a and s['end_segment'] == b), None)


def counts(data):
    stories = [s for p in data['pages'] for s in p['stories']]
    return len(stories), sum(s['classification'] != 'NOT_A_STORY' for s in stories)


def list_rows(tractate):
    kind, path = LISTS[tractate]
    return parse_expert_doc(str(path), tractate) if kind == 'doc' else load_expert_json(str(path), 'recall')


def judge_indicated():
    """List stories Claude moved to `not` from v4 to v5 (R-C7 shape 2 narrowed): the
    judges' reading of "similar ones". CIRCULAR -- printed, never applied."""
    if not all(p.exists() for p in V5_RUNS):
        log.warning('v4/v5 judge runs not on disk -- judge-indicated section skipped')
        return []
    verdict = {}
    for p in V5_RUNS:
        v, m = p.stem.split('_')[1:3]
        for r in json.loads(p.read_text())['rows']:
            verdict.setdefault(r['key'], {'label': r['label'], 'kind': r['kind']})[(v, m)] = \
                r['answers'].get(m, {}).get('verdict')
    covered = {f'{r}_{a}-{b}' for _, _, r, a, b, *_ in GOLDEN} | {e[4] for e in LIST}
    return sorted(k for k, x in verdict.items() if x['label'] in ('yes', 'borderline') and k not in covered
                  and x.get(('v5', 'claude')) == 'not' and x.get(('v4', 'claude')) != 'not')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--tier', choices=['direct', 'description'], default='direct',
                    help='direct = only passages he named; description = also those his own notes describe as the shape')
    args = ap.parse_args()
    tiers = {'direct'} | ({'description'} if args.tier == 'description' else set())

    goldens = {t: json.loads(p.read_text()) for t, p in GOLDENS.items()}
    before = {t: counts(d) for t, d in goldens.items()}
    changed = {t: [] for t in goldens}

    for tier, q, ref, a, b, expected, after, rule, words, feb in GOLDEN:
        if tier not in tiers:
            continue
        t = ref.split()[0]
        page, story = find(goldens[t], ref, a, b)
        old = story['classification'] if story else None
        if old == after:
            log.info('[%s] %s %s %d-%d already %s -- unchanged', tier, q, ref, a, b, after)
            continue
        if old != expected:
            raise ValueError(f'{q}: {ref} {a}-{b} is {old}, script expects {expected} -- refusing')
        note = f'Jeff ({q}, {DATE}): {words}' + (f' -- his February note on this passage: "{feb}"' if feb else '')
        if story is None:
            page['stories'].append({
                'start_segment': a, 'end_segment': b, 'classification': after,
                'one_sentence_summary': 'Orphans come before Rava, who tells the trustees to give the boy '
                                        'more so his sister is provided for; the Sages challenge him.',
                'source': 'jeff_verdict', 'rules': ['R-C1', rule], 'corpus': 'talmud',  # R-C1: every entry records its corpus
                'provenance': {'source': 'jeff_verdict', 'added': DATE, 'verdict_date': DATE,
                               'verdict_source': SOURCE, 'question': q, 'his_words': words,
                               'february_words': feb, 'added_by': Path(__file__).name,
                               'expert_confirmed_boundaries': False}})
            page['stories'].sort(key=lambda s: (s['start_segment'], s['end_segment']))
        else:
            story['classification'] = after
            story.setdefault('corrections', []).append({
                'date': DATE, 'source': SOURCE, 'action': 'reclassify', 'rule': rule, 'tier': tier,
                'old': old, 'new': after, 'note': note})
        changed[t].append({'key': f'{ref}_{a}-{b}', 'question': q, 'tier': tier, 'old': old, 'new': after})
        log.info('[%s] %s %s %d-%d: %s -> %s', tier, q, ref, a, b, old, after)

    # 2005-list annotations, checked through the recall harness's own matcher
    sup = json.loads(SUPERSEDED.read_text())
    have = {(e['ref'], e['text_starts']) for e in sup['entries']}
    new = [{'tractate': tr, 'ref': ref, 'list_id': lid, 'text_starts': ts, 'ruling': ruling,
            'counts_for_recall': ruling != 'not', 'rule': 'R-C0', 'date': DATE,
            'source': f'{SOURCE} ({q})', 'his_words': words, 'tier': tier}
           for tier, q, tr, ref, lid, ts, ruling, words in LIST
           if tier in tiers and (ref, ts) not in have]
    trial = dict(sup, entries=sup['entries'] + new)
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        json.dump(trial, f, ensure_ascii=False)
    recall = {}
    for tr in sorted({e['tractate'] for e in new} | {'Gittin'}):   # Gittin: its golden header carries the denominator
        rows = list_rows(tr)
        n0 = sum(r['counts_for_recall'] for r in apply_superseded([dict(r) for r in rows], tr, SUPERSEDED))
        n1 = sum(r['counts_for_recall'] for r in apply_superseded([dict(r) for r in rows], tr, Path(f.name)))
        recall[tr] = (n0, n1)
    Path(f.name).unlink()

    print('\n=== BLAST RADIUS (tier: %s) ===' % ' + '.join(sorted(tiers)))
    for t, d in goldens.items():
        e1, a1 = counts(d)
        print(f'{t:10} golden entries {before[t][0]} -> {e1} · accepted (not NOT_A_STORY) {before[t][1]} -> {a1}')
        for c in changed[t]:
            print(f'           [{c["tier"]}] {c["question"]} {c["key"]}: {c["old"]} -> {c["new"]}')
    print('2005-list annotations added: %d' % len(new))
    for e in new:
        print(f'           [{e["tier"]}] {e["list_id"]} {e["ref"]}: {e["ruling"]}'
              f'{"" if e["counts_for_recall"] else " -- leaves the recall denominator"}')
    for tr, (n0, n1) in recall.items():
        print(f'{tr:10} recall denominator {n0} -> {n1}')
    print('\nFLAGGED, not applied (his call -- the 65a line may keep them borderline):')
    for ref, a, b, why in FLAGGED:
        print(f'           {ref} {a}-{b}: {why}')
    ind = judge_indicated()
    print(f'\nJudge-indicated, not applied (CIRCULAR -- Claude moved to `not` under the narrowed rule): {len(ind)}')
    for k in ind:
        print(f'           {k}')

    if args.dry_run:
        log.info('dry run -- nothing written')
        return 0
    # The Gittin golden carries derived header fields its test pins; keep them true.
    from collections import Counter
    g = goldens['Gittin']
    g['classification_distribution'] = dict(sorted(Counter(
        s['classification'] for p in g['pages'] for s in p['stories']).items()))
    if 'Gittin' in recall:
        g['recall_denominator'] = recall['Gittin'][1]
    for t, d in goldens.items():
        if changed[t] or t == 'Gittin':
            d.setdefault('jeff_2026_10_25', {'source': SOURCE, 'applied': []})['applied'].extend(changed[t])
            GOLDENS[t].write_text(json.dumps(d, ensure_ascii=False, indent=2))
            log.info('wrote %s', GOLDENS[t].name)
    if new:
        sup['entries'].extend(new)
        SUPERSEDED.write_text(json.dumps(sup, ensure_ascii=False, indent=1))
        log.info('wrote %s (+%d)', SUPERSEDED.name, len(new))
    return 0


if __name__ == '__main__':
    sys.exit(main())
