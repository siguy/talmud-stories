#!/usr/bin/env python3
"""
Strip LLM character-offset text spans from a detector output (Wave 5, step 0).

WHY: Wave 4's `extract_text_spans_via_llm` asks Gemini for a character offset
into the boundary segment. Audited 2026-08-28 across all three v10 outputs:
55% of emitted cuts sever a word and 96% land mid-clause (see
scripts/audit_text_spans.py). Of the 9 trimmed stories Jeff Rubenstein
reviewed on 2026-07-06, 9 were marked incorrect; of the 6 untrimmed ones,
4 were correct. The mechanism has no observed successes.

Removing the spans restores segment-level boundaries, which are recoverable by
a human reader; a mid-word cut is not. The evaluation harness reads only
start_segment/end_segment, so this is score-neutral (proven, not assumed:
run scripts/evaluate_golden.py before and after).

Does NOT modify the detector or the v10 outputs in place (see memory
`feedback_detector_versioning.md`). Writes a new file.

Usage:
  python3 scripts/strip_text_spans.py --in RESULTS.json --out OUT.json
"""
import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SPAN_FIELDS = ('text_span_start', 'text_span_end', 'text_span_source')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [strip_text_spans] %(message)s',
    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
              logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


def strip(data):
    """Remove span fields from every story. Returns (stories, stories_stripped)."""
    total = stripped = 0
    for page in data.get('pages', []):
        for story in page.get('stories', []):
            total += 1
            present = [f for f in SPAN_FIELDS if f in story]
            if any(f in story for f in SPAN_FIELDS[:2]):
                stripped += 1
            for f in present:
                del story[f]
    return total, stripped


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--out', dest='out', required=True)
    args = ap.parse_args()

    src = Path(args.inp)
    data = json.loads(src.read_text())
    total, stripped = strip(data)

    data['version'] = f"{data.get('version', 'unknown')}-notrim"
    data['text_span_policy'] = {
        'policy': 'segment_level_only',
        'reason': 'Wave 4 LLM char-offsets unreliable (55% mid-word cuts); '
                  'reverted 2026-08-28 pending Wave 5 clause-anchored spans',
        'reverted_from': src.name,
    }
    Path(args.out).write_text(json.dumps(data, ensure_ascii=False, indent=1))
    log.info('%s -> %s | stories=%d spans_removed_from=%d',
             src.name, Path(args.out).name, total, stripped)


if __name__ == '__main__':
    main()
