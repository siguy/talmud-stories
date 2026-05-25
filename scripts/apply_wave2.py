#!/usr/bin/env python3
"""
Apply Wave 2 post-processors to Wave 1 outputs (no LLM re-call).

Wave 2 is deterministic — three pure-Python filters on the existing detector
output. Re-running the LLM-driven stages would re-introduce nondeterministic
drift (Lesson 11). Instead we read Wave 1 JSON, run the three filters, and
write Wave 2 JSON.

Outputs:
  results/v8/wave2/kiddushin_v8.json
  results/v8/wave2/ketubot_v8_2-60.json
  results/v8/wave2/ketubot_v8_61-112.json
"""

import json
from pathlib import Path

from src.story_detector_v8 import (
    snap_start_to_introducer,
    trim_trailing_stam_segments,
    filter_biblical_actor_stories,
)

ROOT = Path(__file__).parent.parent
WAVE1 = ROOT / 'results' / 'v8' / 'wave1'
WAVE2 = ROOT / 'results' / 'v8' / 'wave2'

INPUTS = [
    'kiddushin_v8.json',
    'ketubot_v8_2-60.json',
    'ketubot_v8_61-112.json',
]


def process(in_path: Path, out_path: Path):
    with open(in_path) as f:
        data = json.load(f)
    pages = data['pages']
    snapped = snap_start_to_introducer(pages)
    trimmed = trim_trailing_stam_segments(pages)
    demoted = filter_biblical_actor_stories(pages)
    data['wave'] = 'wave2'
    data['wave2_stats'] = {
        'start_snaps': snapped,
        'end_trims': trimmed,
        'biblical_demotions': demoted,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"{in_path.name:40s} snaps={snapped:3d} trims={trimmed:3d} bib={demoted:3d}")


def main():
    print(f"Applying Wave 2 post-processors to {len(INPUTS)} files\n")
    for name in INPUTS:
        process(WAVE1 / name, WAVE2 / name)
    print(f"\nOutputs in {WAVE2.relative_to(ROOT)}")


if __name__ == '__main__':
    main()
