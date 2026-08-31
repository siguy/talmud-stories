#!/usr/bin/env python3
"""Turn a verdict-axes review round into boundary targets the scorer already reads.

Phase B of `work/2026-08-30-review-verdict-axes.md`, boundary half.

WHY THIS EXISTS
---------------
Capability 4 is measured in clauses: `scripts/score_boundary_targets.py` asks *"is the
run's boundary at the target clause"* and scores HIT / NEAR / MISS. Until now the only
way to get such a target was to align Jeff's verbatim 2005 story text against Sefaria and
infer which clause his text stopped at -- 294 Ketubot targets, every one carrying an
`align_fraction` and `anchor_verified: false`, and 2 of his 149 stories that would not
align at all.

The review page now captures the clause directly: he clicks it. That is exact rather than
inferred, it works on stories his 2005 list does not contain, and it costs one click.

TWO KINDS, WRITTEN TO TWO FILES, NEVER POOLED (Lesson 24)
---------------------------------------------------------
    corrections   he said the extent was wrong, our span was on screen, he pointed at
                  the right clause. CIRCULAR: our span anchored the answer. Answers
                  "did we fix known failures" and cannot catch a regression (Lesson 23).

    blind         on a sample, the page asked where the story runs BEFORE our span was
                  shown at all -- no highlight, no verdict buttons. Our extent had no
                  part in the answer, so the target is blind FOR THE BOUNDARY QUESTION.

**The blindness claim, stated so it can be argued with.** We chose which passage he saw;
we did not choose the boundary he marked. Those are different influences. Choosing the
passage biases *which* boundaries get measured -- toward passages the detector finds,
which is also the population the shipped database has boundaries for. It cannot bias the
answer *within* a passage, which is what the metric reads. This is the same distinction
`results/expert_lists/kiddushin_2005.json` already draws between `blind` and
`counts_for_recall`: circularity matters in the direction that flatters, and this one
cannot flatter.

Two residual anchors, recorded on every target rather than argued away:

  * the one-sentence English summary is on the card, so he knows *which* story is meant.
    It names the story; it does not state its edges.
  * the displayed window is centred on our span (widened to +/-4 segments for the blind
    pass for exactly this reason), so it tells him roughly where to look. At clause
    resolution that leaves tens of clauses of freedom.

Neither is nothing. `blind_basis` says so on every target, so nobody has to reconstruct
the argument from a commit message.

Usage:
  python3 scripts/build_boundary_targets_from_review.py --review <round.json>
  python3 scripts/build_boundary_targets_from_review.py --review <round.json> --out-dir tests/
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [btargets] %(message)s',
                    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

SCHEMA = 'verdict_axes_v1'

KINDS = {
    'blind': {
        'file': 'expert_boundary_targets_review_blind.json',
        'comment': ('Boundaries the expert marked BEFORE our span was shown -- no '
                    'highlight and no verdict buttons on the card. Blind for the '
                    'boundary question; see scripts/build_boundary_targets_from_review.py. '
                    'Report SEPARATELY from the corrections set (Lesson 24).'),
    },
    'corrections': {
        'file': 'expert_boundary_targets_review_corrections.json',
        'comment': ('Boundaries the expert corrected with our span on screen. CIRCULAR: '
                    'answers "did we fix known failures" and cannot catch a regression '
                    '(Lesson 23). Report SEPARATELY from the blind set (Lesson 24).'),
    },
}


def targets_from(review: dict):
    """(blind targets, correction targets) in the shape score_boundary_targets.py reads."""
    if review.get('schema') != SCHEMA:
        raise SystemExit(f"not a {SCHEMA} review file (schema={review.get('schema')!r})")
    round_name = review.get('source_round') or 'verdict_axes_review'
    out = {'blind': [], 'corrections': []}
    for key, rec in review.get('reviews', {}).items():
        for mark in rec.get('boundary_marks') or []:
            kind = 'blind' if mark.get('blind') else 'corrections'
            out[kind].append({
                'ref': rec['page_ref'],
                'located_on': rec['page_ref'],
                'direction': mark['direction'],
                'segment': mark['segment'],
                'clause': mark['clause'],
                'n_clauses': mark.get('n_clauses'),
                # The clicked clause is text to KEEP -- the story runs to it, not past it.
                'quote_polarity': 'include',
                'source_round': round_name,
                'review_key': key,
                # Provenance travels with the target, not with the commit message.
                'boundary_blind': bool(mark.get('blind')),
                'blind_basis': mark.get('blind_basis'),
                'classification_shown': rec.get('classification_shown'),
                'is_story': rec.get('is_story'),
                # He clicked it; there is no alignment step and nothing to verify.
                'anchor_verified': True,
                'exact_clause_edge': True,
            })
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--review', required=True, help='a verdict_axes_v1 review JSON')
    ap.add_argument('--out-dir', default='tests')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    review = json.loads(Path(args.review).read_text())
    kinds = targets_from(review)
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = PROJECT_ROOT / out_dir
    rel = lambda q: q.relative_to(PROJECT_ROOT) if q.is_relative_to(PROJECT_ROOT) else q

    for kind, targets in kinds.items():
        n_dirs = Counter(t['direction'] for t in targets)
        log.info('%-12s %3d targets  %s', kind, len(targets), dict(n_dirs) or '')
        if args.dry_run or not targets:
            continue
        path = out_dir / KINDS[kind]['file']
        path.write_text(json.dumps({
            '_comment': KINDS[kind]['comment'],
            'generated_from': Path(args.review).name,
            'generated_by': 'scripts/build_boundary_targets_from_review.py',
            'kind': 'BLIND' if kind == 'blind' else 'CIRCULAR',
            'n_targets': len(targets),
            'targets': targets,
        }, ensure_ascii=False, indent=1) + '\n')
        log.info('  wrote %s', rel(path))

    if kinds['blind']:
        log.info('score them apart, never pooled:')
        log.info('  python3 scripts/score_boundary_targets.py --runs cur=<run.json> \\')
        log.info('      --targets tests/%s --by-source', KINDS['blind']['file'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
