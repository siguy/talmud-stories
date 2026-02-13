#!/usr/bin/env python3
"""
Phase 3: Gemini Model Comparison

Runs the winning pipeline (v7 + triage + post-processing) with different models.
Reuses pre-computed triage to isolate the effect of model quality on detection.

Usage:
  python tests/model_comparison.py --model gemini-3-flash-preview
  python tests/model_comparison.py --model gemini-3-pro-preview
  python tests/model_comparison.py --score  # Score all existing results
"""

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.event_triage import EventTriager
from src.ground_truth import GroundTruthDB, EventType
from src.post_processing import PostProcessor
from src.story_detector_v7 import (
    V7StoryDetector,
    load_pages_from_results,
    load_triage_results,
    merge_cross_page_stories_v7,
    merge_cross_page_stories,
    refine_boundaries_with_event_tags,
    detect_duplicate_stories,
)

PROJECT_ROOT = Path(__file__).parent.parent
V5_PATHS = [
    str(PROJECT_ROOT / 'results' / 'ketubot' / 'v5' / 'pages_2-39.json'),
    str(PROJECT_ROOT / 'results' / 'ketubot' / 'v5' / 'pages_40-60.json'),
]
TRIAGE_PATH = str(PROJECT_ROOT / 'results' / 'v7' / 'event_triage_2-60.json')
V6_RESULTS = str(PROJECT_ROOT / 'results' / 'v6' / 'ketubot_v6_2-60.json')
FEEDBACK_PATH = str(PROJECT_ROOT / 'validation' / 'feedback' /
                    'v5_1_feedback_anonymous_2026-02-05 (1).json')


def model_slug(model_name: str) -> str:
    """Convert model name to short filename slug."""
    # gemini-3-flash-preview -> g3flash
    # gemini-3-pro-preview -> g3pro
    # gemini-2.5-flash -> g25flash
    # gemini-2.0-flash -> g20flash
    name = model_name.lower()
    if 'gemini-3' in name:
        if 'pro' in name:
            return 'g3pro'
        return 'g3flash'
    if 'gemini-2.5' in name:
        if 'pro' in name:
            return 'g25pro'
        return 'g25flash'
    if 'gemini-2.0' in name:
        return 'g20flash'
    return name.replace('-', '').replace('.', '')


def run_detection(model_name: str, delay: float = 0.5):
    """
    Run v7 detection with a specific model on triage-kept pages.
    Reuses pre-computed triage (from gemini-2.0-flash).
    """
    slug = model_slug(model_name)
    print("=" * 70)
    print(f"  MODEL COMPARISON: {model_name} ({slug})")
    print("=" * 70)

    # Load data
    pages = load_pages_from_results(V5_PATHS)
    triage = load_triage_results(TRIAGE_PATH)
    print(f"  Loaded {len(pages)} pages, triage for {len(triage)} refs")

    # Load ground truth for few-shot examples
    db = GroundTruthDB()
    db.load_from_feedback(FEEDBACK_PATH, V5_PATHS)

    # Create detector with specified model
    detector = V7StoryDetector(ground_truth_db=db, model_name=model_name)
    if not detector.client:
        print("  ERROR: No API key. Set GOOGLE_API_KEY.")
        return None

    print(f"  Using model: {detector.model_name}")

    # Run pipeline with pre-computed triage
    results = detector.run_pipeline(pages, triage_results=triage, delay=delay)

    # Save raw results
    raw_path = PROJECT_ROOT / 'results' / 'v7' / f'ketubot_{slug}_2-60.json'
    with open(raw_path, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  Raw results saved to {raw_path}")

    # Apply post-processing
    pp = PostProcessor(
        v6_results_path=V6_RESULTS,
        triage_results_path=TRIAGE_PATH,
    )
    processed, pp_stats = pp.apply(results)

    pp_path = PROJECT_ROOT / 'results' / 'v7' / f'ketubot_{slug}_2-60_pp.json'
    with open(pp_path, 'w') as f:
        json.dump(processed, f, indent=2, ensure_ascii=False)
    print(f"  Post-processed results saved to {pp_path}")
    print(f"  Post-processing: {pp_stats['total_demotions']} demotions")

    return str(raw_path), str(pp_path)


def run_scorecard(paths_and_labels):
    """Run regression test on multiple result files and print comparison."""
    test_dir = Path(__file__).parent
    sys.path.insert(0, str(test_dir))
    from v7_regression_test import run_regression_test

    print("\n" + "=" * 70)
    print("  MODEL COMPARISON SCORECARD")
    print("=" * 70)

    results = []
    for path, label in paths_and_labels:
        if path and Path(path).exists():
            agrees, total = run_regression_test(v7_results_path=path, label=label)
            results.append((label, agrees, total))
            print()

    if len(results) > 1:
        print("-" * 70)
        print("COMPARISON:")
        for label, agrees, total in results:
            pct = 100 * agrees / total if total > 0 else 0
            print(f"  {label:25s}: {agrees}/{total} ({pct:.1f}%)")
        print("-" * 70)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Phase 3: Gemini Model Comparison')
    parser.add_argument('--model', type=str,
                        help='Model name (e.g., gemini-3-flash-preview)')
    parser.add_argument('--delay', type=float, default=0.5,
                        help='Delay between API calls')
    parser.add_argument('--score', action='store_true',
                        help='Score all existing model comparison results')
    args = parser.parse_args()

    # Build scorecard paths - always include baselines
    paths_and_labels = []

    v7_path = str(PROJECT_ROOT / 'results' / 'v7' / 'ketubot_v7_2-60.json')
    v7pp_path = str(PROJECT_ROOT / 'results' / 'v7' / 'ketubot_v7_2-60_pp.json')
    paths_and_labels.append((v7_path, 'v7 (g2.0-flash)'))
    paths_and_labels.append((v7pp_path, 'v7+pp (g2.0-flash)'))

    if args.model:
        result = run_detection(args.model, delay=args.delay)
        if result:
            raw_path, pp_path = result
            slug = model_slug(args.model)
            paths_and_labels.append((raw_path, f'v7 ({slug})'))
            paths_and_labels.append((pp_path, f'v7+pp ({slug})'))

    if args.score or not args.model:
        # Score all existing model results
        for slug_name in ['g3flash', 'g3pro', 'g25flash', 'g25pro']:
            raw = PROJECT_ROOT / 'results' / 'v7' / f'ketubot_{slug_name}_2-60.json'
            pp = PROJECT_ROOT / 'results' / 'v7' / f'ketubot_{slug_name}_2-60_pp.json'
            if raw.exists():
                paths_and_labels.append((str(raw), f'v7 ({slug_name})'))
            if pp.exists():
                paths_and_labels.append((str(pp), f'v7+pp ({slug_name})'))

    run_scorecard(paths_and_labels)
