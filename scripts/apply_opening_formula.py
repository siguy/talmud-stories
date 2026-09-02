#!/usr/bin/env python3
"""
Move each story's start back over the formula that introduces it (Jeff, 2026-09-01).

Runs on a finished detector output, so it costs nothing and is directly comparable
to its input: only `text_span_start` moves, never a segment boundary.

    python3 scripts/apply_opening_formula.py --in RUN.json --out OUT.json

Why a deterministic post-processor is allowed here, when Lesson 15 forbids exactly
that for text-internal decisions: this rule was stated by the expert in words —
"these opening formulae... are important... we should include them" — rather than
fitted to our own past errors. It stays one clause wide and only ever reaches
backwards. See docs/findings/2026-09-02-jeff-answers-gittin.md.
"""
import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s [opening-formula] %(message)s',
                    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

from src.story_detector_v11 import extend_start_over_opening_formula  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--out', dest='out', required=True)
    ap.add_argument('--dry-run', action='store_true', help='report, write nothing')
    args = ap.parse_args()

    data = json.loads(Path(args.inp).read_text())
    counts = extend_start_over_opening_formula(data['pages'])
    moved = [(p['ref'], s['start_segment'], s['text_span_start'].get('opening_formula'))
             for p in data['pages'] for s in p.get('stories', [])
             if (s.get('text_span_start') or {}).get('opening_formula')]
    log.info('%s: %s', Path(args.inp).name, counts)
    for ref, seg, formula in moved:
        log.info('  extended %s seg %s over %r', ref, seg, formula)
    if args.dry_run:
        log.info('dry run — nothing written')
        return 0
    data['opening_formula'] = {'counts': counts,
                               'moved': [{'ref': r, 'segment': s, 'formula': f}
                                         for r, s, f in moved]}
    data['version'] = f"{data.get('version', '?')}-formula"
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(data, indent=2, ensure_ascii=False))
    log.info('wrote %s', args.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
