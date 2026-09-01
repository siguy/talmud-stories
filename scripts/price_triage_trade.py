#!/usr/bin/env python3
"""
Price the triage trade: what Stage 1 saves, and what it costs.

FRAMEWORK §1.1 — a triage bar quoted without its cost saving is meaningless.
The gate says >=98% survival; nobody had ever priced the other side of it.

Three measurements, none of which spends an API call. Everything read here is
already on disk.

  1 CEILING     Stories on the blind lists that died in Stage 1, over the pages
                Stage 1 discarded. An upper bound on what re-examining those
                pages can return, because Stage 2 cannot find what it is never
                shown -- and does not always find what it is.

  2 AUDIT       `results/v7/ablation_v7_no_triage.json` looks like this item's
                experiment already run: v7 over all 118 Ketubot 2a-60b pages
                with 0 skipped. It is not, and this section is the evidence.
                `skip_triage=True` does not bypass Stage 1 -- it stamps every
                segment DELIBERATION (story_detector_v7.py:658-664) and Stage 2
                renders that label into its prompt as `[DELIBERATION] Seg N`
                (:75). So the ablation ran Stage 2 having told it, on every page,
                that nothing narrative happens there. Scored, it LOSES 6 stories
                the triaged run found on pages both runs examined -- impossible
                for a change that only ever adds pages. The file cannot answer
                this item; the real experiment is still unrun.

  3 RULE PRICE  Removing triage is not the only move. Stage 1's keep-condition
                is a threshold over cached per-segment labels, so every
                relaxation of it can be priced exactly -- pages newly examined
                against stories recovered -- from the cache alone. Including the
                one the diagnosis points at: nearly every story Stage 1 killed
                spans a daf boundary and so needs two independent keep-decisions
                to go right.

Usage:
  python3 scripts/price_triage_trade.py --out results/v11/triage_recall/
"""
import argparse
import json
import logging
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.measure_recall_vs_expert_list import grams, load_detected, locate  # noqa: E402
from scripts.parse_kiddushin_list import parse as parse_expert_table  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s %(levelname)s [triage-price] %(message)s',
    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'), logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

SHIPPED = {
    'ketubot': ['results/v10/wave4_notrim/ketubot_v10_2-60_notrim.json',
                'results/v10/wave4_notrim/ketubot_v10_61-112_notrim.json'],
    'kiddushin': ['results/v10/wave4_notrim/kiddushin_v10_notrim.json'],
}
TRIAGE_CACHE = {
    'ketubot': ['results/v7/event_triage_2-60.json', 'results/v7/event_triage_61-112.json'],
    'kiddushin': ['results/v7/event_triage_kiddushin.json'],
}
AB_TRIAGED = 'results/v7/ketubot_v7_2-60.json'
AB_NO_TRIAGE = 'results/v7/ablation_v7_no_triage.json'


def daf(ref):
    """('Ketubot 19b') -> (19, 1). Sort key and range filter."""
    n = int(re.search(r'(\d+)', ref).group(1))
    return n, 0 if ref.rstrip()[-1] == 'a' else 1


# ------------------------------------------------------------------ 1 ceiling

def ceiling(tractate):
    """What re-examining every discarded page could return, at most."""
    rows = json.loads((PROJECT_ROOT / f'results/recall/{tractate}_jeff2005_matches.json').read_text())
    pages = skipped = unexamined = 0
    for path in SHIPPED[tractate]:
        for page in json.loads((PROJECT_ROOT / path).read_text())['pages']:
            pages += 1
            if page.get('skipped_by_triage'):
                skipped += 1
                unexamined += len(page.get('segments', []))

    died = [s for s in rows if not s['survived_triage']]
    lived = [s for s in rows if s['survived_triage']]
    # Partition the survivors by what happened next, and assert it (Lesson 21).
    found = [s for s in lived if s['in_detector'] and not s['only_rejected']]
    rejected = [s for s in lived if s['only_rejected']]
    silent = [s for s in lived if not s['in_detector']]
    assert len(found) + len(rejected) + len(silent) == len(lived), 'survivor buckets do not partition'
    assert len(died) + len(lived) == len(rows), 'triage buckets do not partition'

    return {
        'tractate': tractate, 'expert_stories': len(rows),
        'pages': pages, 'pages_skipped': skipped, 'skip_rate': round(skipped / pages, 3),
        'unexamined_segments': unexamined,
        'died_in_triage': len(died),
        'triage_recall': round(len(lived) / len(rows), 4),
        'survived_then_found': len(found),
        'survived_then_rejected': len(rejected),
        'survived_then_nothing_proposed': len(silent),
        'calls_per_story_ceiling': round(skipped / len(died), 1) if died else None,
        'max_recall_gain_pts': round(100 * len(died) / len(rows), 1),
        'lost_refs': sorted({r for s in died for r in s['pages_touched']}, key=daf),
        'lost_stories': [{'ref': s['ref'], 'pages_touched': s['pages_touched'],
                          'words': s['words'], 'coverage': s['coverage']} for s in died],
    }


# -------------------------------------------------------------------- 2 audit

def ablation_audit():
    """Is `ablation_v7_no_triage.json` the experiment this item asks for?

    Location is computed once, on the corpus the two runs share, so the only
    thing that differs between the two columns is which spans were proposed.
    Turning triage OFF can only ever add pages to examine, so it cannot subtract
    a story found on a page that was examined either way. Any such loss is proof
    the ablation changed something other than which pages were seen.
    """
    expert, comments = parse_expert_table(PROJECT_ROOT / 'jeff comms/b.ketubot (1).doc', 'Ketubot')
    assert len(expert) == 149, f'expert list regression: {len(expert)}'
    assert not comments, 'Ketubot list should carry no review comments'

    units_on, spans_on, _, triage_on, rej_on, acc_on = load_detected([PROJECT_ROOT / AB_TRIAGED])
    units_off, spans_off, _, triage_off, rej_off, acc_off = load_detected([PROJECT_ROOT / AB_NO_TRIAGE])
    assert [(r, i) for r, i, _ in units_on] == [(r, i) for r, i, _ in units_off], \
        'the two runs must cover the same segments or the comparison is not an A/B'
    assert len(triage_on.skipped) == 78 and len(triage_off.skipped) == 0, \
        'expected the triage-on/off pair, got %d/%d skipped' % (len(triage_on.skipped), len(triage_off.skipped))

    index = defaultdict(set)
    for i, (_, _, gs) in enumerate(units_on):
        for g in gs:
            index[g].add(i)

    in_range = [s for s in expert if daf(s['ref'])[0] <= 60]
    rows, unplaced = [], []
    for story in in_range:
        cov, start, end = locate(grams(story['text']), units_on, index)
        window = [(units_on[i][0], units_on[i][1]) for i in range(start, end + 1)] if start is not None else []
        # An expert story the aligner cannot place is not evidence either way.
        # It is its own bucket, reported, never silently scored as a miss.
        if cov < 0.5:
            unplaced.append({'ref': story['ref'], 'coverage': round(cov, 3), 'words': story['words']})
            continue
        covered = lambda table: any(lo <= ix <= hi for ref, ix in window for lo, hi in table.get(ref, []))
        pages_touched = sorted({r for r, _ in window}, key=daf)
        rows.append({
            'ref': story['ref'], 'coverage': round(cov, 3), 'pages_touched': pages_touched,
            'survived_triage': any(r in triage_on.examined for r in pages_touched),
            'found_with_triage': covered(spans_on), 'found_without_triage': covered(spans_off),
            'accepted_with_triage': covered(acc_on), 'accepted_without_triage': covered(acc_off),
        })

    assert len(rows) + len(unplaced) == len(in_range), 'placement buckets do not partition'
    recovered = [r for r in rows if r['found_without_triage'] and not r['found_with_triage']]
    lost = [r for r in rows if r['found_with_triage'] and not r['found_without_triage']]
    killed = [r for r in rows if not r['survived_triage']]
    killed_recovered = [r for r in killed if r['found_without_triage']]

    # The impossible bucket: a story lost on a page BOTH runs examined.
    impossible = [r for r in lost if r['survived_triage']]
    prop_on = sum(len(v) for v in spans_on.values())
    prop_off = sum(len(v) for v in spans_off.values())
    cls_on = Counter(s.get('classification')
                     for p in json.loads((PROJECT_ROOT / AB_TRIAGED).read_text())['pages']
                     for s in p.get('stories', []))
    cls_off = Counter(s.get('classification')
                      for p in json.loads((PROJECT_ROOT / AB_NO_TRIAGE).read_text())['pages']
                      for s in p.get('stories', []))
    return {
        'range': 'Ketubot 2a-60b', 'detector': 'v7', 'pages': 118,
        'expert_in_range': len(in_range), 'placed': len(rows), 'unplaced': unplaced,
        'extra_stage2_calls': len(triage_on.skipped),
        'proposals_with_triage': prop_on, 'proposals_without_triage': prop_off,
        'classification_with_triage': dict(cls_on), 'classification_without_triage': dict(cls_off),
        'found_with_triage': sum(r['found_with_triage'] for r in rows),
        'found_without_triage': sum(r['found_without_triage'] for r in rows),
        'recovered': recovered, 'regressed': lost,
        'killed_by_triage': len(killed), 'killed_and_recovered': len(killed_recovered),
        'lost_on_pages_examined_by_both': len(impossible),
        'verdict': (
            'CONTAMINATED — not a no-triage run. skip_triage=True stamps every segment '
            'DELIBERATION (story_detector_v7.py:658-664), which Stage 2 renders into its '
            'prompt (:75) and post-processing rule 3 reads as "0 NARRATIVE_EVENTs on this '
            f'page". {len(impossible)} stories found by the triaged run were lost on pages both '
            'runs examined, which no change to the page set can cause; NOT_A_STORY went '
            f'{cls_on.get("NOT_A_STORY", 0)} -> {cls_off.get("NOT_A_STORY", 0)} of '
            f'{prop_on} -> {prop_off} proposals. Use it for neither recall nor precision.'
        ) if impossible else 'clean — the two runs differ only in which pages were examined',
    }


# --------------------------------------------------------------- 3 rule price

SHIPPED_RULE = lambda n, v: n >= 2 or (n >= 1 and v >= 2)  # noqa: E731
RULES = {
    'shipped    narrative>=2 or (narrative>=1 and verbal>=2)': (SHIPPED_RULE, False),
    'relax-A    narrative>=1': (lambda n, v: n >= 1, False),
    'relax-B    narrative>=2 or (narrative>=1 and verbal>=1)': (lambda n, v: n >= 2 or (n >= 1 and v >= 1), False),
    'relax-C    narrative>=1 or verbal>=3': (lambda n, v: n >= 1 or v >= 3, False),
    'neighbour  shipped, plus the daf either side of every kept page': (SHIPPED_RULE, True),
    'off        examine everything': (lambda n, v: True, False),
}


def with_neighbours(examined, all_refs):
    """Every kept page drags in the daf on either side of it.

    Aimed at the structure the diagnosis exposes: a story straddling a daf
    boundary needs BOTH of its pages kept, so it faces two independent chances
    of being discarded, and the half that carries the narrative opener is not
    always the half that trips the threshold.
    """
    order = sorted(all_refs, key=daf)
    pos = {ref: i for i, ref in enumerate(order)}
    out = set(examined)
    for ref in examined:
        i = pos[ref]
        out.update(order[max(0, i - 1):i + 2])
    return out


def rule_price(tractate):
    """Every relaxation of the keep-condition, priced from the cached labels."""
    labels = {}
    for path in TRIAGE_CACHE[tractate]:
        labels.update(json.loads((PROJECT_ROOT / path).read_text())['triage_results'])

    counts = {ref: (Counter(evs)['NARRATIVE_EVENT'], Counter(evs)['VERBAL_ACT'])
              for ref, evs in labels.items()}
    rows = json.loads((PROJECT_ROOT / f'results/recall/{tractate}_jeff2005_matches.json').read_text())
    died = [s for s in rows if not s['survived_triage']]

    shipped_examined = set()
    for path in SHIPPED[tractate]:
        for page in json.loads((PROJECT_ROOT / path).read_text())['pages']:
            if not page.get('skipped_by_triage'):
                shipped_examined.add(page['ref'])

    # How many of the killed stories straddle a daf boundary? That is the
    # structure the neighbour rule is aimed at, so state it rather than imply it.
    cross_page = [s for s in died if len(s['pages_touched']) > 1]

    out = []
    for name, (keep, neighbours) in RULES.items():
        examined = {ref for ref, (n, v) in counts.items() if keep(n, v)}
        if neighbours:
            examined = with_neighbours(examined, set(counts))
        # A story is recoverable under a rule only if EVERY page its text sits on
        # is examined -- a story split across a daf boundary needs both halves.
        recoverable = [s for s in died if all(r in examined for r in s['pages_touched'])]
        extra = len(examined - shipped_examined)
        out.append({
            'rule': name, 'examined': len(examined), 'of_pages': len(counts),
            'examine_rate': round(len(examined) / len(counts), 3),
            'extra_calls_vs_shipped': extra,
            'stories_recovered': len(recoverable),
            'refs_recovered': [s['ref'] for s in recoverable],
            'calls_per_story': round(extra / len(recoverable), 1) if recoverable else None,
        })

    # The cache is the raw Stage 1 decision; the shipped run applies the Wave 1
    # lexical override on top, so shipped must be a superset. Assert it rather
    # than assume it -- if it is not, the two are not the same triage.
    cache_shipped_rule = {ref for ref, (n, v) in counts.items() if SHIPPED_RULE(n, v)}
    override = sorted(shipped_examined - cache_shipped_rule, key=daf)
    assert not (cache_shipped_rule - shipped_examined), \
        'cache keeps pages the shipped run skipped -- not the same triage decision'
    return {'tractate': tractate, 'rules': out,
            'died_in_triage': len(died), 'died_spanning_two_dapim': len(cross_page),
            'wave1_override_pages': len(override), 'wave1_override_refs': override}


# ---------------------------------------------------------------- 4 diagnosis

def diagnose(tractate):
    """The cached Stage 1 labels on every page that killed a story.

    A threshold miss and a labelling miss look identical in the recall number
    and need opposite fixes, so separate them: a page sitting one narrative
    event below the bar is a threshold that can be moved, and a page scored with
    ZERO narrative events is a labeller that did not see what is on it.
    """
    labels = {}
    for path in TRIAGE_CACHE[tractate]:
        labels.update(json.loads((PROJECT_ROOT / path).read_text())['triage_results'])
    rows = json.loads((PROJECT_ROOT / f'results/recall/{tractate}_jeff2005_matches.json').read_text())

    pages, near_bar = [], 0
    for s in (r for r in rows if not r['survived_triage']):
        for ref in s['pages_touched']:
            c = Counter(labels.get(ref, []))
            n, v = c['NARRATIVE_EVENT'], c['VERBAL_ACT']
            pages.append({'story': s['ref'], 'page': ref, 'words': s['words'],
                          'narrative': n, 'verbal': v, 'deliberation': c['DELIBERATION'],
                          'habitual': c['HABITUAL'], 'segments': sum(c.values()),
                          'kind': 'threshold' if n >= 1 else 'labelling'})
            near_bar += n >= 1
    return {'tractate': tractate, 'killer_pages': len(pages),
            'threshold_misses': near_bar, 'labelling_misses': len(pages) - near_bar,
            'pages': pages}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', default='results/v11/triage_recall/')
    args = ap.parse_args()
    out = PROJECT_ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)

    report = {'ceiling': [ceiling(t) for t in ('ketubot', 'kiddushin')],
              'ablation_audit': ablation_audit(),
              'rule_price': [rule_price(t) for t in ('ketubot', 'kiddushin')],
              'diagnosis': [diagnose(t) for t in ('ketubot', 'kiddushin')]}

    for c in report['ceiling']:
        log.info('%s CEILING: %d stories died in triage over %d skipped pages (%d segments) '
                 '-> at most 1 story per %s calls, +%.1f pts',
                 c['tractate'], c['died_in_triage'], c['pages_skipped'], c['unexamined_segments'],
                 c['calls_per_story_ceiling'], c['max_recall_gain_pts'])
    log.info('ABLATION AUDIT: %s', report['ablation_audit']['verdict'])
    for rp in report['rule_price']:
        log.info('%s RULE PRICE (%d of %d killed stories span two dapim):',
                 rp['tractate'], rp['died_spanning_two_dapim'], rp['died_in_triage'])
        for row in rp['rules']:
            log.info('  %-56s examine %3d/%3d (%3.0f%%)  +%3d calls  +%d stories  %s',
                     row['rule'], row['examined'], row['of_pages'], 100 * row['examine_rate'],
                     row['extra_calls_vs_shipped'], row['stories_recovered'],
                     f"1 per {row['calls_per_story']}" if row['calls_per_story'] else '-')
    for d in report['diagnosis']:
        log.info('%s DIAGNOSIS: of %d pages that killed a story, %d sat below the bar with '
                 'narrative>=1 (threshold), %d were scored with ZERO narrative events (labelling)',
                 d['tractate'], d['killer_pages'], d['threshold_misses'], d['labelling_misses'])

    (out / 'triage_trade.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    log.info('wrote %s', out / 'triage_trade.json')


if __name__ == '__main__':
    main()
