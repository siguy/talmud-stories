#!/usr/bin/env python3
"""
Which of our proposals are really covered by the expert's list, and which only look it.

Recall asks: did we find HIS stories? This asks the mirror question, which nothing else
does: for each of OUR proposals, is there really an expert story there?

Why it matters. The recall aligner locates an expert story by Hebrew 4-grams and returns a
search WINDOW that can run to fourteen segments. Any proposal inside that window is
credited. That is right for recall -- a wide window is a generous test of "did we find
it" -- and it is wrong the moment the same association is read backwards as "this proposal
is on his list", because the window routinely spans neighbouring stories on the same daf.

Found on Gittin 2026-09-02, building the golden: `results/recall/gittin_listed_keys.json`
credited 57b:0-4 (Nebuzaradan and Zechariah's blood) to his entry for the 400 captive
children, and 68a:7-12 (Solomon and Ashmedai) to his entry for Resh Galuta and Rav Sheshet.
Both of ours are famous aggadot and neither is on his list. They were therefore left out of
the unlisted screen and never sent to him -- and an email told him every one of our
top-confidence proposals was on his list.

This script asks whether that is a Gittin accident or a corpus-wide pattern. Two proposals
is not a rate (Lesson 18).

Three buckets, and the middle one is the finding:

  strict    the proposal overlaps the expert story's OWN segments
  loose     it sits in the window but overlaps no expert story strictly
            -- treated as "on his list" by anything reading the loose association
  unlisted  no expert story's window reaches it

Usage:
  python3 scripts/audit_proposal_credit.py
  python3 scripts/audit_proposal_credit.py --tractate Gittin --show 20
"""

import argparse
import importlib.util
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [credit] %(message)s',
                    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

_spec = importlib.util.spec_from_file_location(
    'recall', PROJECT_ROOT / 'scripts' / 'measure_recall_vs_expert_list.py')
recall = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(recall)

# The same runs the rulers score, so a number here is comparable to one there.
# Ketubot's list has no JSON — it is parsed from the .doc, the same way build_ruler.py
# does it, so the two agree by construction rather than by coincidence.
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


def classify(tractate, cfg, show):
    source = cfg.get('expert') or cfg['expert_doc']
    expert_path = PROJECT_ROOT / source
    if not expert_path.exists():
        log.warning('%s: no expert list at %s — skipped, NOT counted as zero',
                    tractate, source)
        return None
    runs = [str(PROJECT_ROOT / r) for r in cfg['runs']]
    for r in runs:
        if not Path(r).exists():
            log.warning('%s: missing run %s — skipped, NOT counted as zero', tractate, r)
            return None

    if 'expert_doc' in cfg:
        parsed, _ = kid.parse(expert_path, tractate)
        stories = [{'id': s.get('id') or f'{tractate.lower()}_{i:03d}', 'text': s['text']}
                   for i, s in enumerate(parsed, 1) if not s.get('duplicate_of')]
    else:
        stories = recall.load_expert_json(str(expert_path), 'recall')
    units, _, _, _, _, _ = recall.load_detected(runs)
    index = defaultdict(set)
    for i, (_, _, gs) in enumerate(units):
        for g in gs:
            index[g].add(i)

    proposals = []
    for run in runs:
        data = json.loads(Path(run).read_text())
        pages = data['pages'] if isinstance(data, dict) else data
        for page in pages:
            for st in page.get('stories', []):
                a, b = st.get('start_segment'), st.get('end_segment')
                if a is None or b is None:
                    continue
                proposals.append({'ref': page['ref'], 'a': a, 'b': b,
                                  'cls': st.get('classification'),
                                  'summary': (st.get('one_sentence_summary') or '')[:70]})

    strict_hits, loose_hits = defaultdict(list), defaultdict(list)
    for s in stories:
        gs = recall.grams(s['text'])
        _, lo, hi = recall.locate(gs, units, index)
        if lo is None:
            continue
        window = {(units[i][0], units[i][1]) for i in range(lo, hi + 1)}
        tight = {(units[i][0], units[i][1]) for i in range(lo, hi + 1)
                 if max(recall.overlap_frac(units[i][2], gs),
                        recall.overlap_frac(gs, units[i][2])) > 0.50}
        for p in proposals:
            key = (p['ref'], p['a'], p['b'])
            cells = {(p['ref'], i) for i in range(p['a'], p['b'] + 1)}
            if cells & tight:
                strict_hits[key].append(s['id'])
            elif cells & window:
                loose_hits[key].append(s['id'])

    only_loose = []
    for p in proposals:
        key = (p['ref'], p['a'], p['b'])
        p['bucket'] = ('strict' if key in strict_hits
                       else 'loose' if key in loose_hits else 'unlisted')
        if p['bucket'] == 'loose':
            p['credited_to'] = loose_hits[key]
            only_loose.append(p)

    n = len(proposals)
    counts = {b: sum(1 for p in proposals if p['bucket'] == b)
              for b in ('strict', 'loose', 'unlisted')}
    log.info('%-10s %3d proposals — strict %3d · LOOSE-ONLY %3d · unlisted %3d',
             tractate, n, counts['strict'], counts['loose'], counts['unlisted'])

    top = [p for p in only_loose if p['cls'] in ('YES', 'HIGH_CONFIDENCE')]
    if top:
        log.info('%-10s   of those, %d are top-confidence — the Nebuzaradan class:',
                 tractate, len(top))
        for p in top[:show]:
            log.info('%-10s     %s %d-%d  %-16s credited to %s | %s',
                     tractate, p['ref'], p['a'], p['b'], p['cls'],
                     ','.join(p['credited_to']), p['summary'])
    elif only_loose:
        log.info('%-10s   none of them top-confidence', tractate)
    return {'tractate': tractate, 'proposals': n, **counts,
            'loose_only': [{k: v for k, v in p.items() if k != 'summary'}
                           for p in only_loose]}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tractate', choices=sorted(TRACTATES))
    ap.add_argument('--show', type=int, default=10)
    ap.add_argument('--out')
    args = ap.parse_args()

    names = [args.tractate] if args.tractate else sorted(TRACTATES)
    out = [r for r in (classify(t, TRACTATES[t], args.show) for t in names) if r]

    log.info('')
    log.info('LOOSE-ONLY is the population that reads as "on his list" and is not.')
    log.info('It is not an error in the recall figure — recall is a question about HIS')
    log.info('stories, and a wide window is the right generosity there. It is an error')
    log.info('anywhere the same association is read backwards.')
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
        log.info('wrote %s', args.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
