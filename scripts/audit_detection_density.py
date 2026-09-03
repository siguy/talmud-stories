#!/usr/bin/env python3
"""
Does Detection miss MORE on dapim that hold more stories?

The standing hypothesis after two dead ends. R-C3/R-C4 rewrote the criteria and measured
no effect; the translator screen came back null. Both point away from "how a candidate is
judged" and toward "whether it is offered at all" -- Gittin 57a Beitar is not proposed
even as NOT_A_STORY, so no wording change can reach it.

The sharpest cheap version of that claim: **Stage 2 sees one page at a time and proposes
from it, so a daf holding four of Jeff's stories asks more of it than a daf holding one.**
If recall falls as story density rises, the constraint is attention per page, and the fix
is a second pass over the page rather than better criteria. If recall is flat in density,
the misses are about the passages themselves and density is a red herring -- which is
equally worth knowing, and would send the next attempt somewhere else entirely.

No API calls. Uses the same strict test as the rulers, imported from the same module.

Usage:
  python3 scripts/audit_detection_density.py
  python3 scripts/audit_detection_density.py --tractate Ketubot --show 12
"""

import argparse
import importlib.util
import json
import logging
import statistics
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [density] %(message)s',
                    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

_spec = importlib.util.spec_from_file_location(
    'recall', PROJECT_ROOT / 'scripts' / 'measure_recall_vs_expert_list.py')
recall = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(recall)

_kid_spec = importlib.util.spec_from_file_location(
    'kid', PROJECT_ROOT / 'scripts' / 'parse_kiddushin_list.py')
kid = importlib.util.module_from_spec(_kid_spec)
_kid_spec.loader.exec_module(kid)

TRACTATES = {
    'Ketubot': {'expert_doc': 'jeff comms/b.ketubot (1).doc',
                'runs': ['results/v10/wave4_notrim/ketubot_v10_2-60_notrim.json',
                         'results/v10/wave4_notrim/ketubot_v10_61-112_notrim.json']},
    'Kiddushin': {'expert': 'results/expert_lists/kiddushin_2005.json',
                  'runs': ['results/v10/wave4_notrim/kiddushin_v10_notrim.json']},
    'Gittin': {'expert': 'results/expert_lists/gittin_2005.json',
               'runs': ['results/v11/gittin/gittin_v11.json']},
}


def per_daf(tractate, cfg):
    """For each daf: how many of his stories sit there, and how many we found strictly."""
    runs = [str(PROJECT_ROOT / r) for r in cfg['runs']]
    for r in runs:
        if not Path(r).exists():
            log.warning('%s: missing run %s — SKIPPED, not counted as zero', tractate, r)
            return None

    if 'expert_doc' in cfg:
        parsed, _ = kid.parse(PROJECT_ROOT / cfg['expert_doc'], tractate)
        stories = [{'id': s.get('id') or f'{tractate.lower()}_{i:03d}', 'text': s['text']}
                   for i, s in enumerate(parsed, 1) if not s.get('duplicate_of')]
    else:
        stories = recall.load_expert_json(str(PROJECT_ROOT / cfg['expert']), 'recall')

    units, _, _, _, _, _ = recall.load_detected(runs)
    index = defaultdict(set)
    for i, (_, _, gs) in enumerate(units):
        for g in gs:
            index[g].add(i)

    spans = defaultdict(list)
    examined = set()
    for run in runs:
        data = json.loads(Path(run).read_text())
        pages = data['pages'] if isinstance(data, dict) else data
        for page in pages:
            if not page.get('skipped_by_triage'):
                examined.add(page['ref'])
            for st in page.get('stories', []):
                a, b = st.get('start_segment'), st.get('end_segment')
                if a is not None and b is not None:
                    spans[page['ref']].append((a, b))

    # Anchor each expert story to the daf its own segments land on, and ask whether any
    # proposal overlaps those segments. Density is counted on the ANCHORED daf, never on
    # the label in his list -- a label can name a daf the text does not sit on, and
    # crediting density to the wrong daf would fabricate the very correlation being tested.
    daf = defaultdict(lambda: {'expert': 0, 'found': 0, 'missed': []})
    rows, unanchored = [], 0
    for s in stories:
        gs = recall.grams(s['text'])
        _, lo, hi = recall.locate(gs, units, index)
        if lo is None:
            unanchored += 1
            continue
        tight = [(units[i][0], units[i][1]) for i in range(lo, hi + 1)
                 if max(recall.overlap_frac(units[i][2], gs),
                        recall.overlap_frac(gs, units[i][2])) > 0.50]
        if not tight:
            unanchored += 1
            continue
        ref = tight[0][0]
        hit = any(a <= seg <= b for r, seg in tight for a, b in spans.get(r, []))
        daf[ref]['expert'] += 1
        daf[ref]['found'] += hit
        rows.append({'ref': ref, 'hit': hit, 'words': len(s['text'].split())})
        if not hit:
            daf[ref]['missed'].append(s['id'])
    for r in rows:
        r['density'] = daf[r['ref']]['expert']
    return daf, unanchored, examined, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tractate', choices=sorted(TRACTATES))
    ap.add_argument('--show', type=int, default=8)
    ap.add_argument('--out')
    args = ap.parse_args()

    names = [args.tractate] if args.tractate else sorted(TRACTATES)
    combined = defaultdict(lambda: {'expert': 0, 'found': 0})
    report, all_rows = {}, []

    for t in names:
        got = per_daf(t, TRACTATES[t])
        if not got:
            continue
        daf, unanchored, examined, rows = got
        all_rows.extend(rows)
        buckets = defaultdict(lambda: {'expert': 0, 'found': 0, 'dapim': 0})
        for ref, d in daf.items():
            n = d['expert']
            key = n if n <= 3 else '4+'
            buckets[key]['expert'] += n
            buckets[key]['found'] += d['found']
            buckets[key]['dapim'] += 1
            combined[key]['expert'] += n
            combined[key]['found'] += d['found']

        log.info('')
        log.info('=== %s — %d dapim carry a story; %d expert stories could not be anchored '
                 '(excluded, not counted as missed)', t, len(daf), unanchored)
        log.info('  stories on the daf │ dapim │ his stories │ we found │ recall')
        for key in [1, 2, 3, '4+']:
            b = buckets.get(key)
            if not b:
                continue
            log.info('  %-18s │ %5d │ %11d │ %8d │ %.1f%%', key, b['dapim'],
                     b['expert'], b['found'], 100 * b['found'] / b['expert'])
        worst = sorted((d for d in daf.items() if d[1]['missed']),
                       key=lambda kv: (-kv[1]['expert'], kv[0]))[:args.show]
        if worst:
            log.info('  dapim with a miss, densest first:')
            for ref, d in worst:
                log.info('    %-16s %d of his stories, we found %d — missed %s',
                         ref, d['expert'], d['found'], ','.join(d['missed']))
        report[t] = {k if isinstance(k, str) else str(k): v for k, v in buckets.items()}

    log.info('')
    log.info('=== ALL THREE TRACTATES POOLED')
    log.info('  stories on the daf │ his stories │ we found │ recall')
    for key in [1, 2, 3, '4+']:
        b = combined.get(key)
        if not b:
            continue
        log.info('  %-18s │ %11d │ %8d │ %.1f%%', key, b['expert'], b['found'],
                 100 * b['found'] / b['expert'])
    # --- the confound, tested rather than waved at -------------------------------
    # A daf with one story may simply be a daf whose one story is thin -- in which case
    # the profile above is about story length and not about isolation at all. Length is
    # the obvious alternative explanation, so it is measured here rather than dismissed
    # in prose (Lesson 18: the rate first, then the theory).
    if all_rows:
        found = [r['words'] for r in all_rows if r['hit']]
        miss = [r['words'] for r in all_rows if not r['hit']]
        log.info('')
        log.info('=== IS IT JUST LENGTH?')
        log.info('  expert stories we found:  median %.0f words (n=%d)',
                 statistics.median(found), len(found))
        log.info('  expert stories we missed: median %.0f words (n=%d)',
                 statistics.median(miss), len(miss))
        log.info('  -> if these are close, we are not simply missing short stories.')
        log.info('')
        log.info('  recall inside one length band, so length cannot explain the gap:')
        for name, keep in (('short (<=25 words)', lambda w: w <= 25),
                           ('long  (> 25 words)', lambda w: w > 25)):
            band = [r for r in all_rows if keep(r['words'])]
            lo = [r for r in band if r['density'] == 1]
            hi = [r for r in band if r['density'] >= 4]
            if lo and hi:
                log.info('    %-20s alone on the daf %.0f%% (n=%d)  vs  4+ stories %.0f%% (n=%d)',
                         name, 100 * sum(r['hit'] for r in lo) / len(lo), len(lo),
                         100 * sum(r['hit'] for r in hi) / len(hi), len(hi))

    log.info('')
    log.info('  A recall that FALLS as density rises means the constraint is attention per')
    log.info('  page, and the fix is a second pass over the daf. A FLAT profile means the')
    log.info('  misses are about the passages themselves and density is a red herring.')
    log.info('  Either way the next attempt goes somewhere different, which is the point.')

    if args.out:
        Path(args.out).write_text(json.dumps(
            {'pooled': {str(k): v for k, v in combined.items()}, 'per_tractate': report},
            indent=2, ensure_ascii=False) + '\n')
        log.info('wrote %s', args.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
