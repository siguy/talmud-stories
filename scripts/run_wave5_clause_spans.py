#!/usr/bin/env python3
"""
Wave 5: apply clause-anchored text spans to an existing detector output.

Takes a no-trim result file, splits each story's boundary segments into
punctuation-delimited clauses, asks the model which clause the story starts and
ends at, and snaps the boundary to that clause's real position.

No re-detection happens — spans ride the existing segment boundaries, so this is
score-neutral (the harness reads only start_segment/end_segment) and the result
is directly comparable to its input.

The model and thinking level are recorded in the output so runs stay attributable
(roadmap 5.3: pin and record external versions).

Usage:
  python3 scripts/run_wave5_clause_spans.py \
      --in results/v10/wave4_notrim/kiddushin_v10_notrim.json \
      --out results/v11/wave5/kiddushin_v11_g37high.json \
      --model gemini-3.7-flash --thinking high
"""
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.model_config import default_model

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [wave5] %(message)s',
    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'), logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)


def load_env():
    env = PROJECT_ROOT / '.env'
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip() and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--out', dest='out', required=True)
    ap.add_argument('--model', default=default_model())
    ap.add_argument('--thinking', default=None,
                    help="thinking level for Gemini 3.x: low|medium|high (ignored on 2.x)")
    args = ap.parse_args()

    load_env()
    from src.story_detector_v11 import V7StoryDetector

    data = json.loads(Path(args.inp).read_text())
    detector = V7StoryDetector(model_name=args.model, thinking_level=args.thinking)
    if not detector.client:
        log.error('no Gemini client — check GOOGLE_API_KEY'); return 1

    log.info('model=%s thinking=%s  input=%s', args.model, args.thinking, Path(args.inp).name)
    t0 = time.time()
    counts = detector.extract_text_spans_via_clauses(data['pages'])
    elapsed = time.time() - t0

    data['version'] = f"{data.get('version', '?')}-wave5-clause"
    data['wave5_stats'] = {
        'clause_span_counts': counts,
        'model': args.model,
        'thinking_level': args.thinking,
        'elapsed_seconds': round(elapsed, 1),
        'mechanism': 'clause_selection',
    }
    data.pop('text_span_policy', None)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(data, ensure_ascii=False, indent=1))
    log.info('%s | %s | %.0fs -> %s', args.model, counts, elapsed, Path(args.out).name)
    return 0


if __name__ == '__main__':
    sys.exit(main())
