#!/usr/bin/env python3
"""
Audit `results/v7/ablation_v7_no_triage.json` — the 2026-02-13 "triage vs no triage" run.

That file is the sole evidence for the claim in `docs/capabilities/1_triage.md` that
**triage is the single largest accuracy driver** (87.4% with, 83.5% without). It is not a
no-triage run. `tests/ablation_test.py:196` produced it with `run_pipeline(skip_triage=True)`,
and that flag does not bypass Stage 1 — it stamps every segment `DELIBERATION`
(`story_detector_v7.py:658-664`), which Stage 2 renders into its own prompt as
`[DELIBERATION] Seg N:` (`:75`) and post-processing's `rule3_v6_ensemble` reads as
"0 NARRATIVE_EVENTs on this page".

`docs/findings/2026-08-31-triage-recall-price.md` knew to route around the flag when
pricing the trade. This script is the other half: proving the archived run built ON it
cannot be read, so the conclusion drawn from it can be retracted on evidence rather than
on suspicion.

**The proof does not depend on reading the code.** Turning triage off can only ever ADD
pages to examine, so it cannot subtract a story found on a page that was examined either
way. Any such loss is arithmetically impossible for the change the file claims to be.
This scores both arms against Jeff's 2005 list (BLIND) and counts them.

No API calls. Both arms are v7, the same era, over the same 1,485 segments.

Usage:
  python3 scripts/audit_no_triage_ablation.py --out results/v11/ablation_audit/
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
    level=logging.INFO, format='%(asctime)s %(levelname)s [ablation-audit] %(message)s',
    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'), logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

TRIAGED = 'results/v7/ketubot_v7_2-60.json'          # v7, triage ON  — 78 of 118 skipped
NO_TRIAGE = 'results/v7/ablation_v7_no_triage.json'  # v7, "triage OFF" — 0 skipped
EXPERT_DOC = 'jeff comms/b.ketubot (1).doc'
MIN_COVERAGE = 0.5


def daf(ref):
    n = int(re.search(r'(\d+)', ref).group(1))
    return n, 0 if ref.rstrip()[-1] == 'a' else 1


def audit():
    expert, comments = parse_expert_table(PROJECT_ROOT / EXPERT_DOC, 'Ketubot')
    assert len(expert) == 149, f'expert list regression: {len(expert)}'
    assert not comments, 'the Ketubot list carries no review comments'

    units_on, spans_on, _, triage_on, _, _ = load_detected([PROJECT_ROOT / TRIAGED])
    units_off, spans_off, _, triage_off, _, _ = load_detected([PROJECT_ROOT / NO_TRIAGE])
    assert [(r, i) for r, i, _ in units_on] == [(r, i) for r, i, _ in units_off], \
        'the two arms must cover the same segments or this is not an A/B'
    assert len(triage_on.skipped) == 78 and len(triage_off.skipped) == 0, \
        f'expected the 78/0 pair, got {len(triage_on.skipped)}/{len(triage_off.skipped)}'

    # Location is computed once, on the corpus both arms share, so the only thing that
    # differs between the two columns is which spans each arm proposed.
    index = defaultdict(set)
    for i, (_, _, gs) in enumerate(units_on):
        for g in gs:
            index[g].add(i)

    in_range = [s for s in expert if daf(s['ref'])[0] <= 60]
    rows, unplaced = [], []
    for story in in_range:
        cov, start, end = locate(grams(story['text']), units_on, index)
        window = [(units_on[i][0], units_on[i][1]) for i in range(start, end + 1)] if start is not None else []
        if cov < MIN_COVERAGE:
            # An expert story the aligner cannot place is evidence for neither arm.
            unplaced.append({'ref': story['ref'], 'coverage': round(cov, 3)})
            continue
        covered = lambda t: any(lo <= ix <= hi for ref, ix in window for lo, hi in t.get(ref, []))
        pages = sorted({r for r, _ in window}, key=daf)
        rows.append({'ref': story['ref'], 'coverage': round(cov, 3), 'pages_touched': pages,
                     'examined_by_both': all(p in triage_on.examined for p in pages),
                     'found_with_triage': covered(spans_on),
                     'found_without_triage': covered(spans_off)})
    assert len(rows) + len(unplaced) == len(in_range), 'placement buckets do not partition'

    # THE IMPOSSIBLE BUCKET. Removing a filter cannot un-find a story on a page the
    # filtered arm already examined.
    impossible = [r for r in rows
                  if r['found_with_triage'] and not r['found_without_triage'] and r['examined_by_both']]
    cls = {}
    for name, path in (('with_triage', TRIAGED), ('without_triage', NO_TRIAGE)):
        pages = json.loads((PROJECT_ROOT / path).read_text())['pages']
        cls[name] = dict(Counter(s.get('classification') for p in pages for s in p.get('stories', [])))

    return {
        'range': 'Ketubot 2a-60b', 'detector': 'v7', 'pages': 118,
        'expert_in_range': len(in_range), 'placed': len(rows), 'unplaced': unplaced,
        'pages_examined_with_triage': len(triage_on.examined),
        'pages_examined_without_triage': len(triage_off.examined),
        'proposals_with_triage': sum(len(v) for v in spans_on.values()),
        'proposals_without_triage': sum(len(v) for v in spans_off.values()),
        'classification': cls,
        'found_with_triage': sum(r['found_with_triage'] for r in rows),
        'found_without_triage': sum(r['found_without_triage'] for r in rows),
        'impossible_losses': impossible,
        'verdict': (
            'CONTAMINATED — not a no-triage run, and not usable for recall or precision. '
            f'{len(impossible)} stories found by the triaged arm are missing from the '
            '"no triage" arm on pages BOTH arms examined, which removing a filter cannot '
            f'cause. NOT_A_STORY went {cls["with_triage"].get("NOT_A_STORY", 0)} -> '
            f'{cls["without_triage"].get("NOT_A_STORY", 0)}. Cause: skip_triage=True stamps '
            'every segment DELIBERATION (story_detector_v7.py:658-664), which Stage 2 renders '
            'into its prompt (:75) and post-processing rule 3 reads as an empty page.'
        ) if impossible else 'CLEAN — the two arms differ only in which pages were examined',
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', default='results/v11/ablation_audit/')
    args = ap.parse_args()
    out = PROJECT_ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)

    report = audit()
    log.info('pages examined: %d with triage, %d without',
             report['pages_examined_with_triage'], report['pages_examined_without_triage'])
    log.info("Jeff's stories found (of %d placed): %d with triage, %d without",
             report['placed'], report['found_with_triage'], report['found_without_triage'])
    for r in report['impossible_losses']:
        log.info('  IMPOSSIBLE: %s lost on %s — examined by both arms',
                 r['ref'], '+'.join(r['pages_touched']))
    log.info('VERDICT: %s', report['verdict'])

    (out / 'no_triage_ablation_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    log.info('wrote %s', out / 'no_triage_ablation_audit.json')


if __name__ == '__main__':
    main()
