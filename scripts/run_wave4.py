#!/usr/bin/env python3
"""
Apply Wave 4 (LLM-side text-span emission) to Wave 3 outputs.

Wave 4 replaces the regex `edit_text_internal_boundaries` post-processor
with `V7StoryDetector.extract_text_spans_via_llm`. Text spans are
score-neutral (the evaluation harness reads only start_segment /
end_segment), so this fast path lets us emit the new spans without
re-running Stages 1-3.

Inputs:
  results/v9/wave3/kiddushin_v9.json
  results/v9/wave3/ketubot_v9_2-60.json
  results/v9/wave3/ketubot_v9_61-112.json

Outputs:
  results/v10/wave4/<same filenames with v9 → v10>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.story_detector_v10 import V7StoryDetector  # noqa: E402

IN_DIR = ROOT / 'results' / 'v9' / 'wave3'
OUT_DIR = ROOT / 'results' / 'v10' / 'wave4'

INPUTS = {
    'kiddushin_v9.json': 'kiddushin_v10.json',
    'ketubot_v9_2-60.json': 'ketubot_v10_2-60.json',
    'ketubot_v9_61-112.json': 'ketubot_v10_61-112.json',
}


def _strip_v9_spans(pages: List[Dict]) -> None:
    """Remove text_span_start/end/source so Wave 4 emits cleanly."""
    for page in pages:
        for story in page.get('stories', []):
            story.pop('text_span_start', None)
            story.pop('text_span_end', None)
            story.pop('text_span_source', None)


def process(in_path: Path, out_path: Path, detector: V7StoryDetector,
            dry_run: bool = False) -> Dict:
    with in_path.open() as f:
        data = json.load(f)

    pages = data.get('pages', [])
    real_stories = sum(
        1 for p in pages for s in p.get('stories', [])
        if s.get('classification') != 'NOT_A_STORY'
    )
    print(f"\n{in_path.name}: {len(pages)} pages, {real_stories} real stories")

    _strip_v9_spans(pages)

    if dry_run:
        print("  [dry-run] skipping LLM calls")
        return {'file': in_path.name, 'dry_run': True}

    t0 = time.time()
    counts = detector.extract_text_spans_via_llm(pages)
    elapsed = time.time() - t0

    total = counts['llm'] + counts['llm_kept_full'] + counts['skipped']
    skipped_pct = (counts['skipped'] / total * 100) if total else 0.0

    print(f"  Wave 4 spans in {elapsed:.0f}s: "
          f"llm={counts['llm']} "
          f"kept_full={counts['llm_kept_full']} "
          f"skipped={counts['skipped']} "
          f"({skipped_pct:.1f}% skipped)")

    data['version'] = 'v10'
    data['wave4_stats'] = {
        'text_span_counts': counts,
        'elapsed_seconds': round(elapsed, 1),
        'skipped_rate_pct': round(skipped_pct, 2),
        'model': detector.model_name,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open('w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  → {out_path.relative_to(ROOT)}")

    return {
        'file': in_path.name,
        'counts': counts,
        'skipped_pct': skipped_pct,
        'elapsed_seconds': round(elapsed, 1),
    }


def check_keep_full_gate(out_dir: Path) -> Dict:
    """Hardened ship-gate check: zero KEEP_FULL trims in production output."""
    KEEP_FULL_KEYS = [
        ('Kiddushin 8b', 2, 2),
        ('Kiddushin 9a', 1, 1),
        ('Kiddushin 9a', 2, 2),
        ('Kiddushin 13a', 3, 3),
        ('Kiddushin 31b', 4, 4),
        ('Kiddushin 33a', 15, 15),
    ]
    kid_path = out_dir / 'kiddushin_v10.json'
    if not kid_path.exists():
        return {'ran': False, 'reason': 'no kiddushin_v10.json yet'}

    with kid_path.open() as f:
        data = json.load(f)
    violations = []
    for ref, s_idx, e_idx in KEEP_FULL_KEYS:
        for page in data.get('pages', []):
            if page.get('ref') != ref:
                continue
            for story in page.get('stories', []):
                if (story.get('start_segment') == s_idx
                        and story.get('end_segment') == e_idx):
                    tss = story.get('text_span_start')
                    if tss and tss.get('source') == 'llm' \
                            and tss.get('char_offset', 0) > 0:
                        violations.append({
                            'key': f"{ref}_{s_idx}-{e_idx}",
                            'char_offset': tss.get('char_offset'),
                        })
                    break
    return {
        'ran': True,
        'checked': len(KEEP_FULL_KEYS),
        'violations': violations,
        'pass': len(violations) == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', choices=list(INPUTS.keys()),
                        help='Process only one input file')
    parser.add_argument('--dry-run', action='store_true',
                        help='Strip and report, no LLM calls')
    args = parser.parse_args()

    if not args.dry_run and not os.getenv('GOOGLE_API_KEY'):
        print('ERROR: GOOGLE_API_KEY not set', file=sys.stderr)
        return 2

    detector = V7StoryDetector()
    if not args.dry_run and not detector.client:
        print('ERROR: Gemini client not initialized', file=sys.stderr)
        return 2

    print(f"Wave 4 runner — model={detector.model_name}")

    inputs = [args.only] if args.only else list(INPUTS.keys())
    summaries = []
    for name in inputs:
        in_path = IN_DIR / name
        out_path = OUT_DIR / INPUTS[name]
        summaries.append(process(in_path, out_path, detector,
                                 dry_run=args.dry_run))

    if args.dry_run:
        return 0

    # Aggregate
    print("\n" + "=" * 60)
    print("  Wave 4 totals")
    print("=" * 60)
    total = {'llm': 0, 'llm_kept_full': 0, 'skipped': 0}
    for s in summaries:
        for k in total:
            total[k] += s['counts'][k]
    total_stories = sum(total.values())
    skipped_pct = (total['skipped'] / total_stories * 100) if total_stories else 0
    print(f"  llm={total['llm']} "
          f"kept_full={total['llm_kept_full']} "
          f"skipped={total['skipped']} "
          f"({skipped_pct:.2f}% skipped)")

    # Hardened ship-gate check
    print("\n--- KEEP_FULL production gate ---")
    gate = check_keep_full_gate(OUT_DIR)
    if gate['ran']:
        if gate['pass']:
            print(f"  PASS: 0 violations in {gate['checked']} keep-full cases")
        else:
            print(f"  FAIL: {len(gate['violations'])} violations:")
            for v in gate['violations']:
                print(f"    {v['key']} trimmed at char_offset={v['char_offset']}")
            return 1
    else:
        print(f"  skipped: {gate['reason']}")

    if skipped_pct > 2.0:
        print(f"\n  WARN: skipped rate {skipped_pct:.2f}% exceeds 2% threshold")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
