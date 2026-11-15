#!/usr/bin/env python3
"""
Record Jeff's two 2026-11-12 replies as data (`jeff comms/11-12-2026/`).

1. ERUVIN -- his verdicts on 20 entries of his 2005 Eruvin list, chosen 2026-11-08 as the
   ones his later rulings might disqualify (review file `axis_eruvin_ 20 passages from your
   2005 list_review_2026-11-12.json`, axes-3). 19 `no`, 1 `borderline`. The list is evidence
   and is never edited: each verdict goes into results/expert_lists/superseded_by_rule.json
   beside its entry, and a `no` leaves the recall denominator (STORY_RULES.md, "we never edit
   the evidence"). His cover note: the Eruvin list *"seems to just be the preliminary list
   before refining"*, and these entries were *"all flagged as questionable"* in it.

   The review page keyed each card by page_ref + segments; the page was built from list ids
   in a fixed order (scripts/build_eruvin_rulings_page.py on feat/eruvin-run-v11, commit
   121c78b). ERUVIN_ITEMS carries that order. Each key is checked against the segments the
   recall harness itself locates for that id (results/recall/eruvin_jeff2005_matches.json),
   so a wrong id raises here rather than annotating the wrong story.

2. YEVAMOT 78b:9 (yevamot_051, `jeff:question-and-answer`) -- not named by him, settled by
   the rule he stated on Shabbat 147a the same day: a setting plus a question and answer is
   not a story. 78b:9 has the question and answer and not even the setting. tier `rule`, so
   it can be told apart from the passages he ruled on by name.

3. SEPTIMUS precision sample -- his verdicts on the 8 passages of the 2026-11-12 email
   (comms/sent/2026-11-12-email-jeff.md): the 6 non-yes of Simon's pre-read of the 60-story
   sample, plus 2 stories the site lacks. Written to
   results/shas_run/precision_sample/jeff_verdicts_2026-11-12.json beside sample.json;
   the 6 are checked against sample.json and Simon's pre-read. Nothing on the site changes
   here -- that is a separate step (docs/technical/septimus-story-filter.md).

Segment indices 0-based. Idempotent; a key that does not map, or an entry in an unexpected
prior state, is an ERROR, never a skip (Lesson 38).

    python3 scripts/apply_jeff_2026-11-12_verdicts.py --dry-run
    python3 scripts/apply_jeff_2026-11-12_verdicts.py
"""
import argparse
import json
import logging
import sys
import tempfile
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
from measure_recall_vs_expert_list import apply_superseded, load_expert_json, SUPERSEDED  # noqa: E402

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [jeff-2026-11-12] %(message)s',
                    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

DATE = '2026-11-12'
DIR = PROJECT_ROOT / 'jeff comms/11-12-2026'
REVIEW = DIR / 'axis_eruvin_ 20 passages from your 2005 list_review_2026-11-12.json'
REPLY = 'jeff comms/11-12-2026/reply.md'
ERUVIN_LIST = PROJECT_ROOT / 'results/expert_lists/eruvin_2005.json'
ERUVIN_MATCHES = PROJECT_ROOT / 'results/recall/eruvin_jeff2005_matches.json'
YEVAMOT_LIST = PROJECT_ROOT / 'results/expert_lists/yevamot_2005.json'
SAMPLE = PROJECT_ROOT / 'results/shas_run/precision_sample/sample.json'
SIMON = PROJECT_ROOT / 'validation/feedback/2026-11-simon-precision-sample.json'
LEPERS_IN_SAMPLE = 'Berakhot 54b_0-0'
SEPTIMUS_OUT = PROJECT_ROOT / 'results/shas_run/precision_sample/jeff_verdicts_2026-11-12.json'

# review index (the card number on the page) -> 2005 list id. Order of build_eruvin_rulings_page.ITEMS.
ERUVIN_ITEMS = {1: 'eruvin_007', 2: 'eruvin_013', 3: 'eruvin_034', 4: 'eruvin_050', 5: 'eruvin_055',
                6: 'eruvin_063', 7: 'eruvin_064', 8: 'eruvin_008', 9: 'eruvin_014', 10: 'eruvin_019',
                11: 'eruvin_021', 12: 'eruvin_035', 13: 'eruvin_052', 14: 'eruvin_054', 15: 'eruvin_073',
                16: 'eruvin_026', 17: 'eruvin_037', 18: 'eruvin_040', 19: 'eruvin_041', 20: 'eruvin_042'}
ERUVIN_COVER = ('none of these are really stories, except perhaps one, which is borderline. I looked back at '
                'the list I sent you and these are all flagged as questionable. When we made these lists we '
                'initially included everything that could be even considered a story, and then eliminated those '
                'that did not make the cut. At least for the other tractates. This list seems to just be the '
                'preliminary list before refining.')
RULING = {'no': 'not', 'borderline': 'borderline'}

SHABBAT_147A = ('Not a story. This is a legal ruling, a question and answer. It start with the setting, that '
                'Ulla visited Asi bar Hini. But that is not enough for a story.')
# (tractate, ref, list_id, ruling, rule, his words, tier)
BY_RULE = [('Yevamot', 'Yevamot 78b', 'yevamot_051', 'not', 'R-C2',
            f'(his rule, on Shabbat 147a, {DATE}) {SHABBAT_147A}', 'rule')]

# The 8 passages of the 2026-11-12 email. in_sample: one of the 60 (sample.json key);
# simon: Simon's pre-read grade of it; jeff: his verdict (story / borderline / not / out_of_scope).
SEPTIMUS = [
    dict(n=1, ref='Arakhin 23b', start=0, end=1, in_sample=True, simon='no', jeff='not', rule='R-C0',
         words='Not a story. The narrative elements appear within the give and take of the legal discussion to '
               'work out the law. They are hypothetical or possible answers, not events.'),
    dict(n=2, ref='Pesachim 66b', start=4, end=4, in_sample=True, simon='no', jeff='not', rule='R-B4',
         words='Not a story. Similar to the last case. This is the Talmud discussing a story that appeared '
               'previously and trying to make sense of it. But it is a legal discussion.'),
    dict(n=3, ref='Chullin 46a', start=8, end=8, in_sample=True, simon='borderline', jeff='borderline', rule='R-C7',
         words='Borderline. Agreed. There are two events the dialogue is not really connected to the events. '
               'So a borderline case.'),
    dict(n=4, ref='Chullin 57b', start=6, end=7, in_sample=True, simon='borderline', jeff='borderline', rule='R-C7',
         words='Borderline. There is some change, the hen lives, but there is hardly drama or development or real '
               'change. Some would count it a minimal story: you have a protagonist, two events (the splinting, '
               'the hen living) and change. If the choice were story or not, I would say story. But if we have '
               'the option for borderline story, I think it is borderline'),
    dict(n=5, ref='Niddah 7b', start=4, end=5, in_sample=True, simon='borderline', jeff='borderline', rule='R-C7',
         words='Borderline. I agree with your classification. The return of the practice could be a literary '
               'ruling, not a real event. Even if it is, there is not much drama or development.'),
    dict(n=6, ref='Shabbat 147a', start=6, end=6, in_sample=True, simon='borderline', jeff='not', rule='R-C2',
         words=SHABBAT_147A),
    # Not in the sample: Simon's notes on Berakhot 54b:0 and Sanhedrin 52b:3 flagged them.
    dict(n=7, ref='Berakhot 54a', start=15, end=None, in_sample=False, simon=None, jeff='out_of_scope', rule='R-S1',
         note='the two lepers Et and Hev ("Vahev in Sufa"); starts at the bottom of 54a, the site has only the 54b '
              'part (berakhot-54b-0-0, a sample story Simon graded yes). End segment not stated by him',
         words='Not a story for our database. This is a story based on the biblical events, an exegetical '
               'narrative. We are collecting sage-stories of post biblical times.'),
    dict(n=8, ref='Sanhedrin 52b', start=4, end=4, in_sample=False, simon=None, jeff='story', rule='R-C1',
         note='v14 run 1 found it at LOW_CONFIDENCE, so the definite-only site filter held it back',
         words='Story. But this story basically appears in the Mishnah (Sanhedrin 7:2) in slightly different form. '
               'Here it is indeed presented as a baraita. I think it could be included. (The Talmud follows by '
               'saying it was a separate incident (than the Mishnah) but scholars would consider them two '
               'versions of one source. In any case, I would include it.'),
]


def text_starts(row, rows):
    """Shortest word prefix (at least 5 words) of the entry's text unique among rows on its daf."""
    words = row['text'].split()
    for n in range(5, len(words) + 1):
        pre = ' '.join(words[:n])
        if sum(r['ref'] == row['ref'] and r['text'].startswith(pre) for r in rows) == 1:
            return pre
    raise ValueError(f"{row['id']}: no unique prefix on {row['ref']}")


def eruvin_entries():
    review = json.loads(REVIEW.read_text())
    assert review['schema_version'] == 'axes-3' and review['reviewed'] == 20, 'unexpected review file'
    reviews = review['reviews']
    if len(reviews) != 20 or sorted(v['index'] for v in reviews.values()) != list(range(1, 21)):
        raise ValueError(f'expected 20 reviews indexed 1..20, got {len(reviews)}')
    rows = {r['id']: r for r in load_expert_json(str(ERUVIN_LIST), 'all')}
    located = {r['id']: r['located'] for r in json.loads(ERUVIN_MATCHES.read_text())}
    out = []
    for key, v in sorted(reviews.items(), key=lambda kv: kv[1]['index']):
        lid = ERUVIN_ITEMS[v['index']]
        row = rows[lid]
        segs = sorted(i for ref, i in located[lid] if ref == v['page_ref'])
        if not segs or (segs[0], segs[-1]) != (v['start_segment'], v['end_segment']):
            raise ValueError(f'{key} (card {v["index"]}) does not map to {lid}: the harness locates it at '
                             f'{located[lid]}')
        if v['is_story'] not in RULING:
            raise ValueError(f'{key}: unexpected verdict {v["is_story"]!r}')
        ruling = RULING[v['is_story']]
        out.append({'tractate': 'Eruvin', 'ref': row['ref'], 'list_id': lid, 'text_starts': text_starts(row, rows.values()),
                    'ruling': ruling, 'counts_for_recall': ruling != 'not', 'rule': 'jeff-verdict',
                    'date': DATE, 'source': f'{REPLY} (Eruvin review, card {v["index"]}, {key})',
                    'his_words': v['notes'].strip() or f'(no note on this card) cover note: {ERUVIN_COVER}',
                    'review_key': key, 'tier': 'direct'})
    log.info('Eruvin: %d of 20 review keys mapped to list ids (%s)', len(out),
             dict(Counter(e['ruling'] for e in out)))
    return out


def by_rule_entries():
    rows = load_expert_json(str(YEVAMOT_LIST), 'all')
    out = []
    for tr, ref, lid, ruling, rule, words, tier in BY_RULE:
        row = next(r for r in rows if r['id'] == lid)
        assert row['ref'] == ref, (lid, row['ref'])
        out.append({'tractate': tr, 'ref': ref, 'list_id': lid, 'text_starts': text_starts(row, rows),
                    'ruling': ruling, 'counts_for_recall': ruling != 'not', 'rule': rule, 'date': DATE,
                    'source': f'{REPLY} (8 passages, item 6, Shabbat 147a) -- applied by rule, not named by him',
                    'his_words': words, 'tier': tier})
    return out


def septimus():
    sample = {f"{s['ref']}_{s['start_segment']}-{s['end_segment']}": s for s in json.loads(SAMPLE.read_text())}
    simon = json.loads(SIMON.read_text())['reviews']
    if len(sample) != 60 or len(simon) != 60:
        raise ValueError(f'expected 60 sample stories and 60 pre-read grades, got {len(sample)} / {len(simon)}')
    rows = []
    for p in SEPTIMUS:
        key = f"{p['ref']}_{p['start']}-{p['end']}"
        if p['in_sample']:
            if key not in sample:
                raise ValueError(f'{key} is not in the precision sample')
            if simon[key]['is_story'] != p['simon']:
                raise ValueError(f"{key}: Simon's pre-read says {simon[key]['is_story']}, script expects {p['simon']}")
        rows.append(dict(key=key, item=p['n'], ref=p['ref'], start_segment=p['start'], end_segment=p['end'],
                         in_sample=p['in_sample'], stratum=sample[key]['stratum'] if p['in_sample'] else None,
                         simon_pre_read=p['simon'], jeff=p['jeff'], rule=p['rule'], his_words=p['words'],
                         **({'note': p['note']} if 'note' in p else {})))
    # The sample's verdicts: Jeff's where he gave one, otherwise Simon's pre-read (owner, indicated).
    jeff = {r['key']: r['jeff'] for r in rows if r['in_sample']}
    # Item 7 is the lepers passage as a whole (54a:15 into 54b). Its 54b half is a sample story
    # (berakhot-54b-0-0, biblical: true, Simon yes), so his ruling covers it: a story, but out of
    # scope for his catalogue (R-S1). The Septimus site ships biblical stories by Simon's
    # decision (septimus-story-filter.md, 2026-11-10), so for the SITE it still counts as a story.
    if simon[LEPERS_IN_SAMPLE]['is_story'] != 'yes' or not sample[LEPERS_IN_SAMPLE]['biblical']:
        raise ValueError(f'{LEPERS_IN_SAMPLE}: expected a biblical sample story Simon graded yes')
    jeff[LEPERS_IN_SAMPLE] = 'out_of_scope'
    norm = {'yes': 'story', 'no': 'not', 'borderline': 'borderline'}
    merged = {k: (jeff[k], 'jeff') if k in jeff else (norm[v['is_story']], 'simon') for k, v in simon.items()}
    tally = Counter(v for v, _ in merged.values())
    by_stratum = {}
    for k, (v, who) in merged.items():
        by_stratum.setdefault(sample[k]['stratum'], Counter())[v] += 1
    precision = {'n': 60, 'story': tally['story'], 'out_of_scope': tally['out_of_scope'],
                 'borderline': tally['borderline'], 'not': tally['not'],
                 'story_for_the_site': tally['story'] + tally['out_of_scope'],   # the site ships biblical stories
                 'graded_by_jeff': len(jeff), 'graded_by_simon_only': 60 - len(jeff),
                 'by_stratum': {s: dict(c) for s, c in sorted(by_stratum.items())},
                 'evidence': ('MIXED: 7 of the 60 carry Jeff\'s verdict (measured: the 6 non-yes he was sent, and '
                              'Berakhot 54b:0, covered by his ruling on the lepers passage); the other 53 are Simon\'s '
                              'pre-read yes (the project owner, indicated), never shown to Jeff. So the not-a-story '
                              'count is a measured lower bound, and the story count an indicated upper bound.')}
    return rows, precision


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    candidates = eruvin_entries() + by_rule_entries()
    sup = json.loads(SUPERSEDED.read_text())
    have = {(e['ref'], e['text_starts']): e for e in sup['entries']}
    new = []
    for e in candidates:
        old = have.get((e['ref'], e['text_starts']))
        if old is None:
            new.append(e)
        elif old['ruling'] != e['ruling'] or old['date'] != e['date']:
            raise ValueError(f"{e['list_id']} already annotated differently: {old['ruling']} {old['date']}")

    # Denominators before and after, through the recall harness's own reader.
    trial = dict(sup, entries=sup['entries'] + new)
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        json.dump(trial, f, ensure_ascii=False)
    for tr, path in (('Eruvin', ERUVIN_LIST), ('Yevamot', YEVAMOT_LIST)):
        rows = load_expert_json(str(path), 'recall')
        n0 = sum(r['counts_for_recall'] for r in apply_superseded([dict(r) for r in rows], tr, SUPERSEDED))
        n1 = sum(r['counts_for_recall'] for r in apply_superseded([dict(r) for r in rows], tr, Path(f.name)))
        print(f'{tr:8} recall denominator {n0} -> {n1}')
    Path(f.name).unlink()
    print(f'2005-list annotations to add: {len(new)} (already present: {len(candidates) - len(new)})')
    for e in new:
        print(f"   [{e['tier']}] {e['list_id']} {e['ref']}: {e['ruling']}"
              f"{'' if e['counts_for_recall'] else ' -- leaves the recall denominator'}")

    rows, precision = septimus()
    print('\nSeptimus 8 passages:')
    for r in rows:
        print(f"   {r['item']}. {r['key']}: Simon {r['simon_pre_read']} -> Jeff {r['jeff']} ({r['rule']})")
    print(f"Precision sample of 60 (Jeff on {precision['graded_by_jeff']}, Simon's pre-read on the rest): "
          f"story {precision['story']} / out of scope {precision['out_of_scope']} / borderline "
          f"{precision['borderline']} / not {precision['not']} -- story for the site {precision['story_for_the_site']}")
    for s, c in precision['by_stratum'].items():
        print(f'   {s:9} {c}')

    if args.dry_run:
        log.info('dry run -- nothing written')
        return 0
    if new:
        sup['entries'].extend(new)
        SUPERSEDED.write_text(json.dumps(sup, ensure_ascii=False, indent=1))
        log.info('wrote %s (+%d)', SUPERSEDED.name, len(new))
    SEPTIMUS_OUT.write_text(json.dumps({
        'what': "Jeff Rubenstein's verdicts on the 8 passages of the 2026-11-12 email: the 6 non-yes of Simon's "
                "pre-read of the 60-story Shas precision sample, plus 2 stories the site lacks.",
        'source': REPLY, 'original': 'jeff comms/11-12-2026/Brief Project. Eight Questions.docx',
        'date': DATE, 'reviewer': 'Jeff Rubenstein', 'evidence_grade': 'measured (expert verdict)',
        'cover_note': 'The interface did not work for me',
        'sample': str(SAMPLE.relative_to(PROJECT_ROOT)), 'simon_pre_read': str(SIMON.relative_to(PROJECT_ROOT)),
        'added_by': Path(__file__).name, 'verdicts': rows, 'sample_precision': precision},
        ensure_ascii=False, indent=1))
    log.info('wrote %s', SEPTIMUS_OUT.relative_to(PROJECT_ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
