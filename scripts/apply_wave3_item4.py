#!/usr/bin/env python3
"""
Apply Wave 3 Item 4 (text-internal boundary post-processor) to Wave 2 outputs.

Item 4 is pure Python and score-neutral by design (the evaluation harness
reads only start_segment/end_segment, never text_span_*). This script lets
us audit the new field without re-billing the LLM.

Inputs:
  results/v8/wave2/kiddushin_v8.json
  results/v8/wave2/ketubot_v8_2-60.json
  results/v8/wave2/ketubot_v8_61-112.json

Outputs:
  results/v9/wave3_item4/<same filenames>
"""

import json
from pathlib import Path

from src.story_detector_v9 import edit_text_internal_boundaries

ROOT = Path(__file__).parent.parent
IN_DIR = ROOT / 'results' / 'v8' / 'wave2'
OUT_DIR = ROOT / 'results' / 'v9' / 'wave3_item4'

INPUTS = [
    'kiddushin_v8.json',
    'ketubot_v8_2-60.json',
    'ketubot_v8_61-112.json',
]


def process(in_path: Path, out_path: Path):
    with open(in_path) as f:
        data = json.load(f)
    modified = edit_text_internal_boundaries(data['pages'])
    data['wave3_item4_stats'] = {'text_span_edits': modified}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"{in_path.name:40s} text_span_edits={modified}")


def main():
    print(f"Applying Wave 3 Item 4 to {len(INPUTS)} files\n")
    for name in INPUTS:
        process(IN_DIR / name, OUT_DIR / name)
    print(f"\nOutputs in {OUT_DIR.relative_to(ROOT)}")


if __name__ == '__main__':
    main()
