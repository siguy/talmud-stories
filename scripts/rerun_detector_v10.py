#!/usr/bin/env python3
"""
Re-run the detector with improved prompts (v10 ground truth + legal disqualifiers).

Uses existing pre-computed triage results and cached pages to avoid re-fetching.
Saves to results/v10/ to preserve baseline results in results/v7/.

Usage:
  python3 scripts/rerun_detector_v10.py              # Full run (2-60 + 61-112)
  python3 scripts/rerun_detector_v10.py --pages 2-60  # Only pages 2-60
  python3 scripts/rerun_detector_v10.py --pages 61-112
"""

import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

from src.event_triage import EventTriager
from src.ground_truth import GroundTruthDB, EventType
from src.story_detector_v7 import (
    V7StoryDetector,
    merge_cross_page_stories_v7,
    merge_cross_page_stories,
    refine_boundaries_with_event_tags,
    load_triage_results,
)

MODEL = "gemini-3-flash-preview"
DELAY = 0.5

# Output directory
V10_DIR = PROJECT_ROOT / 'results' / 'v10'

# Existing resources (pages, triage)
V7_DIR = PROJECT_ROOT / 'results' / 'v7'


def load_ground_truth():
    """Load full ground truth with canonical review."""
    db = GroundTruthDB()

    feedback_path = PROJECT_ROOT / 'validation' / 'feedback' / 'v5_1_feedback_anonymous_2026-02-05 (1).json'
    v5_paths = [
        str(PROJECT_ROOT / 'results' / 'ketubot' / 'v5' / 'pages_2-39.json'),
        str(PROJECT_ROOT / 'results' / 'ketubot' / 'v5' / 'pages_40-60.json'),
    ]

    if feedback_path.exists():
        db.load_from_feedback(str(feedback_path), v5_paths)
        print(f"  v5.1 feedback: {len(db.entries)} entries")

    canonical_path = PROJECT_ROOT / 'validation' / 'feedback' / 'canonical_review_anonymous_2026-03-17.json'
    canonical_results = PROJECT_ROOT / 'results' / 'canonical' / 'ketubot_canonical.json'
    if canonical_path.exists():
        added = db.load_canonical_review(
            str(canonical_path),
            str(canonical_results) if canonical_results.exists() else None
        )
        print(f"  Canonical review: +{added} entries (total: {len(db.entries)})")

    return db


def load_pages_from_json(path):
    """Load pages from a results JSON file (handles both dict and list formats)."""
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get('pages', [])


def run_detection(pages, triage_results, db, delay=0.5):
    """Run detection pipeline on pages."""
    detector = V7StoryDetector(ground_truth_db=db, model_name=MODEL)
    if not detector.client:
        print("ERROR: No API key. Set GOOGLE_API_KEY in .env")
        sys.exit(1)

    results = detector.run_pipeline(pages, triage_results=triage_results, delay=delay)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pages', choices=['2-60', '61-112', 'all'], default='all')
    args = parser.parse_args()

    print("=" * 60)
    print("  RE-RUN DETECTOR WITH V10 IMPROVEMENTS")
    print("=" * 60)

    V10_DIR.mkdir(parents=True, exist_ok=True)

    # Load ground truth
    print("\n--- Loading ground truth ---")
    db = load_ground_truth()

    if args.pages in ('2-60', 'all'):
        print("\n--- Running pages 2-60 ---")

        # Load pages from existing v7 results
        v7_path = V7_DIR / 'ketubot_v7_2-60.json'
        pages = load_pages_from_json(v7_path)
        print(f"  Loaded {len(pages)} pages from {v7_path}")

        # Load pre-computed triage
        triage_path = V7_DIR / 'event_triage_2-60.json'
        triage_results = None
        if triage_path.exists():
            triage_results = load_triage_results(str(triage_path))
            print(f"  Loaded triage from {triage_path}")

        # Run detection
        results = run_detection(pages, triage_results, db, delay=DELAY)

        # Save
        output_path = V10_DIR / 'ketubot_v10_2-60.json'
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"  Saved to {output_path}")

        # Count stories
        story_count = sum(
            1 for p in results.get('pages', [])
            for s in p.get('stories', [])
            if s.get('classification') != 'NOT_A_STORY'
        )
        print(f"  Stories detected: {story_count}")

    if args.pages in ('61-112', 'all'):
        print("\n--- Running pages 61-112 ---")

        # Load pages from existing results or cache
        cache_path = V7_DIR / 'ketubot_pages_61-112.json'
        v9_path = V7_DIR / 'ketubot_v9_61-112.json'

        if cache_path.exists():
            pages = load_pages_from_json(cache_path)
            print(f"  Loaded {len(pages)} pages from cache")
        elif v9_path.exists():
            pages = load_pages_from_json(v9_path)
            print(f"  Loaded {len(pages)} pages from v9 results")
        else:
            print("  ERROR: No pages cache found for 61-112")
            sys.exit(1)

        # Load pre-computed triage
        triage_path = V7_DIR / 'event_triage_61-112.json'
        triage_results = None
        if triage_path.exists():
            triage_results = load_triage_results(str(triage_path))
            print(f"  Loaded triage from {triage_path}")

        # Run detection
        results = run_detection(pages, triage_results, db, delay=DELAY)

        # Save
        output_path = V10_DIR / 'ketubot_v10_61-112.json'
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"  Saved to {output_path}")

        story_count = sum(
            1 for p in results.get('pages', [])
            for s in p.get('stories', [])
            if s.get('classification') != 'NOT_A_STORY'
        )
        print(f"  Stories detected: {story_count}")

    # Evaluate
    print("\n--- Evaluating ---")
    v10_paths = []
    for name in ['ketubot_v10_2-60.json', 'ketubot_v10_61-112.json']:
        p = V10_DIR / name
        if p.exists():
            v10_paths.append(str(p))

    if v10_paths:
        from scripts.evaluate_golden import load_golden, load_detected, evaluate
        golden = load_golden(str(PROJECT_ROOT / 'results' / 'canonical' / 'ketubot_canonical.json'))
        detected = load_detected([Path(p) for p in v10_paths])
        results = evaluate(detected, golden)

        print(f"\n  Classification F1: {results['classification']['f1']}")
        print(f"  Boundary IoU:      {results['boundary']['mean_iou']}")
        print(f"  Merge F1:          {results['merge']['f1']}")
        print(f"  COMPOSITE:         {results['composite']}")
        print(f"  (Baseline was:     0.9308)")

        # Save
        eval_path = PROJECT_ROOT / 'docs' / 'golden' / 'post_improvement_ketubot.json'
        save = {k: v for k, v in results.items() if k != 'per_story'}
        with open(eval_path, 'w') as f:
            json.dump(save, f, indent=2)
        print(f"\n  Saved evaluation to {eval_path}")


if __name__ == '__main__':
    main()
