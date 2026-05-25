#!/usr/bin/env python3
"""
Wave 1 re-run of Kiddushin pipeline using the v8 detector.

v8 = v7 + Jeff's 2026-04-23 fixes (Issues #1, #2, #5, #7). Identical Stage 2
prompt — only Stage 1 gating and Stage 4 post-processing differ.

Reuses cached pages and triage results — only re-runs detection + post-proc.
Output: results/kiddushin/kiddushin_v8.json

Revert path: this script imports from src.story_detector_v8 explicitly. To
revert to v7, change the import and rerun.
"""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

from src.event_triage import EventTriager
from src.ground_truth import GroundTruthDB, EventType
from src.story_detector_v8 import V7StoryDetector

MODEL = "gemini-3-flash-preview"
TRACTATE = "Kiddushin"
DELAY = 0.5

CACHE_DIR = PROJECT_ROOT / 'results' / 'v7'  # Sefaria + triage caches live here
OUT_DIR = PROJECT_ROOT / 'results' / 'v8'
PAGES_CACHE_PATH = CACHE_DIR / 'kiddushin_pages.json'
TRIAGE_PATH = CACHE_DIR / 'event_triage_kiddushin.json'
OUTPUT_PATH = OUT_DIR / 'wave1' / 'kiddushin_v8.json'


def main():
    if not PAGES_CACHE_PATH.exists():
        sys.exit(f"ERROR: pages cache missing at {PAGES_CACHE_PATH}")
    if not TRIAGE_PATH.exists():
        sys.exit(f"ERROR: triage cache missing at {TRIAGE_PATH}")

    print("=" * 60)
    print("  Kiddushin v8 run (Wave 1 fixes)")
    print("  Detector: src.story_detector_v8")
    print("  Reusing cached pages + triage")
    print("=" * 60)

    with open(PAGES_CACHE_PATH) as f:
        pages = json.load(f)
    with open(TRIAGE_PATH) as f:
        triage_raw = json.load(f)['triage_results']
    triage_results = {
        ref: [EventType(s) for s in evs]
        for ref, evs in triage_raw.items()
    }
    skipped = sum(1 for ev in triage_results.values()
                  if EventTriager.should_skip_page(ev))
    print(f"  Triage: {len(triage_results)} pages, {skipped} skip-able "
          f"(introducer override may move some into processing)")

    feedback_path = PROJECT_ROOT / 'validation' / 'feedback' / \
        'v5_1_feedback_anonymous_2026-02-05 (1).json'
    v5_paths = [
        str(PROJECT_ROOT / 'results' / 'v5' / 'pages_2-39.json'),
        str(PROJECT_ROOT / 'results' / 'v5' / 'pages_40-60.json'),
    ]
    db = GroundTruthDB()
    if feedback_path.exists():
        db.load_from_feedback(str(feedback_path), v5_paths)
        print(f"  Loaded ground truth: {len(db.entries)} entries (Ketubot)")

    detector = V7StoryDetector(ground_truth_db=db, model_name=MODEL)
    if not detector.client:
        sys.exit("ERROR: No API key. Set GOOGLE_API_KEY.")

    results = detector.run_pipeline(
        pages, triage_results=triage_results, delay=DELAY, tractate=TRACTATE,
    )
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved to: {OUTPUT_PATH}")

    # Summary
    total = 0
    by_cls = {}
    cross = 0
    mishnah = 0
    for p in results.get('pages', []):
        for s in p.get('stories', []):
            cls = s.get('classification', 'NOT_A_STORY')
            if cls == 'NOT_A_STORY':
                continue
            total += 1
            by_cls[cls] = by_cls.get(cls, 0) + 1
            if s.get('spans_pages'):
                cross += 1
        mishnah += len(p.get('mishnah_stories', []))
    print(f"\n  Stories: {total} (cross-page: {cross}, mishnah filtered: {mishnah})")
    for cls, n in sorted(by_cls.items()):
        print(f"    {cls}: {n}")


if __name__ == '__main__':
    main()
