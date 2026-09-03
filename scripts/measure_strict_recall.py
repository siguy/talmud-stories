#!/usr/bin/env python3
"""
Strict recall: was the expert's story proposed, or merely something near it?

`measure_recall_vs_expert_list.py` credits a proposal anywhere in the aligner's
search window, which runs up to 14 segments wide. That window is right for asking
"did we look here at all" and far too loose for "did we find THIS story" — on
Kiddushin it credited a different passage on the same daf in 2 of 6 cases checked
by name, so the loose figure is an upper bound and STATUS says to read it as one.

This applies the ruler's own narrowing (`build_ruler.py`), without needing a
golden or a review round — so a tractate with no expert verdicts yet can still be
measured strictly on the day it is first run:

    a segment belongs to the story if either side is mostly the other, and a
    proposal counts only if it overlaps one of those segments.

Reports loose and strict side by side. Quote them together or neither.

Usage:
  python3 scripts/measure_strict_recall.py \
      --expert-json results/expert_lists/gittin_2005.json \
      --detected results/v11/gittin/gittin_v11.json --tractate Gittin
"""
import argparse
import importlib.util
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [strict] %(message)s',
                    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

_spec = importlib.util.spec_from_file_location(
    'recall', PROJECT_ROOT / 'scripts' / 'measure_recall_vs_expert_list.py')
recall = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(recall)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument('--expert-json')
    source.add_argument('--expert-doc',
                        help='the Ketubot .doc, parsed by parse_expert_doc — a different '
                             'path from the three JSON lists, so it is checked separately')
    ap.add_argument('--detected', nargs='+', required=True)
    ap.add_argument('--tractate', required=True)
    ap.add_argument('--matcher', default='fuzzy', choices=['fuzzy', 'exact'],
                    help='see measure_recall_vs_expert_list.locate_exact')
    ap.add_argument('--expert-filter', default='recall', choices=['recall', 'blind', 'all'])
    ap.add_argument('--out')
    ap.add_argument('--show', type=int, default=10, help='how many loose-only cases to print')
    args = ap.parse_args()

    stories = (recall.load_expert_json(args.expert_json, args.expert_filter)
               if args.expert_json else recall.parse_expert_doc(args.expert_doc, args.tractate))
    units, spans, withheld, triage, rejected, accepted = recall.load_detected(args.detected)
    index = recall.build_index(units) if hasattr(recall, 'build_index') else None
    if index is None:
        from collections import defaultdict
        index = defaultdict(set)
        for i, (_, _, gs) in enumerate(units):
            for g in gs:
                index[g].add(i)

    corpus = recall.word_corpus(args.detected, units)
    locator, fell_back = recall.make_locator(args.matcher, units, index, corpus)

    rows, loose, strict = [], 0, 0
    for s in stories:
        gs = recall.grams(s['text'])
        cov, lo, hi = locator(s)
        window = [(units[i][0], units[i][1]) for i in range(lo, hi + 1)] if lo is not None else []
        tight = [(units[i][0], units[i][1]) for i in range(lo, hi + 1)
                 if max(recall.overlap_frac(units[i][2], gs),
                        recall.overlap_frac(gs, units[i][2])) > 0.50] if lo is not None else []
        hit = lambda cells: any(ref == r and a <= ix <= b
                                for ref, ix in cells for r in [ref]
                                for a, b in spans.get(ref, []))
        in_loose, in_strict = hit(window), hit(tight)
        loose += in_loose
        strict += in_strict
        rows.append({'id': s.get('id'), 'ref': window[0][0] if window else s.get('ref'),
                     'coverage': round(cov, 3) if cov else cov,
                     'window_segments': len(window), 'tight_segments': len(tight),
                     'loose': in_loose, 'strict': in_strict, 'matcher': args.matcher,
                     'text': s['text'][:120]})

    n = len(stories)
    log.info('%s: %d expert stories (--expert-filter %s, --matcher %s)',
             args.tractate, n, args.expert_filter, args.matcher)
    if args.matcher == 'exact' and fell_back:
        log.warning('%d story(s) had no corpus-unique phrase and fell back to the 4-gram '
                    'aligner: %s', len(fell_back), ', '.join(map(str, fell_back)))
    log.info('LOOSE  recall: %d/%d = %.1f%%  — proposal anywhere in the search window',
             loose, n, 100 * loose / n)
    log.info('STRICT recall: %d/%d = %.1f%%  — proposal overlapping the story\'s own segments',
             strict, n, 100 * strict / n)
    only_loose = [r for r in rows if r['loose'] and not r['strict']]
    log.info('%d story(s) credited by the loose test only — check these by name before '
             'quoting the loose figure', len(only_loose))
    for r in only_loose[:args.show]:
        log.info('  loose-only %s %s (window %d segs, tight %d): %s',
                 r['id'], r['ref'], r['window_segments'], r['tight_segments'], r['text'][:70])
    missed = [r for r in rows if not r['loose']]
    for r in missed[:args.show]:
        log.info('  MISSED %s %s: %s', r['id'], r['ref'], r['text'][:70])

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(
            {'tractate': args.tractate, 'denominator': n, 'matcher': args.matcher,
             'recall_loose': round(loose / n, 4), 'recall_strict': round(strict / n, 4),
             'stories': rows}, indent=2, ensure_ascii=False))
        log.info('wrote %s', args.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
