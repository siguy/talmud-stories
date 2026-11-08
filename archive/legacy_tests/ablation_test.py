#!/usr/bin/env python3
"""
Ablation Tests: Identify which v7 pipeline components matter.

Test A: v6 Detection + Triage + v7 Cross-Page Merge + Post-Processing
  Question: Is v7's constrained prompt needed, or does v6+triage do the same?
  Cost: ~$0.05 (40 pages × v6 prompt)

Test B: v7 Without Triage (all 118 pages)
  Question: Is triage improving accuracy or just saving API cost?
  Cost: ~$0.11 (118 pages × v7 prompt)

Both tests apply v7's cross-page merge and post-processing rules,
then run the regression test for comparison.
"""

import json
import os
import re
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
from src.story_detector_v6 import CategoricalStoryClassifier


PROJECT_ROOT = Path(__file__).parent.parent
V5_PATHS = [
    str(PROJECT_ROOT / 'results' / 'ketubot' / 'v5' / 'pages_2-39.json'),
    str(PROJECT_ROOT / 'results' / 'ketubot' / 'v5' / 'pages_40-60.json'),
]
TRIAGE_PATH = str(PROJECT_ROOT / 'results' / 'v7' / 'event_triage_2-60.json')
V6_RESULTS = str(PROJECT_ROOT / 'results' / 'v6' / 'ketubot_v6_2-60.json')
FEEDBACK_PATH = str(PROJECT_ROOT / 'validation' / 'feedback' /
                    'v5_1_feedback_anonymous_2026-02-05 (1).json')


def load_setup():
    """Load pages and triage data shared by both tests."""
    pages = load_pages_from_results(V5_PATHS)
    triage = load_triage_results(TRIAGE_PATH)
    return pages, triage


def get_kept_pages(pages, triage):
    """Return list of (page, event_types) for pages not skipped by triage."""
    kept = []
    for page in pages:
        ref = page.get('ref', '')
        events = triage.get(ref, [])
        if not EventTriager.should_skip_page(events):
            kept.append((page, events))
    return kept


def apply_merge_and_pp(all_results, triage, output_path):
    """Apply v7 merge, boundary refinement, duplicate detection, and post-processing."""
    # Boundary refinement
    boundary_changes = refine_boundaries_with_event_tags(all_results, triage)
    print(f"  Boundary refinement: {boundary_changes} stories trimmed")

    # Cross-page merge (v7 style)
    all_results = merge_cross_page_stories_v7(all_results, triage)

    # Legacy cross-page merge
    all_results = merge_cross_page_stories(all_results)

    # Duplicate detection
    all_results = detect_duplicate_stories(all_results)

    # Build full result dict
    result = {
        'tractate': 'Ketubot',
        'version': 'ablation',
        'pages': all_results,
        'triage_summary': EventTriager.summarize_triage(triage),
    }

    # Apply post-processing
    pp = PostProcessor(
        v6_results_path=V6_RESULTS,
        triage_results_path=TRIAGE_PATH,
    )
    processed, pp_stats = pp.apply(result)

    # Save
    with open(output_path, 'w') as f:
        json.dump(processed, f, indent=2, ensure_ascii=False)
    print(f"  Saved to {output_path}")
    print(f"  Post-processing: {pp_stats['total_demotions']} demotions")

    return processed


def run_test_a(pages, triage, delay=0.5):
    """
    Test A: v6 Detection + Triage + v7 Merge + Post-Processing

    Uses v6's CategoricalStoryClassifier on the 40 triage-kept pages.
    Then applies v7's cross-page merge and post-processing.
    """
    print("=" * 70)
    print("  TEST A: v6 Detection + Triage + v7 Merge + PP")
    print("=" * 70)

    kept = get_kept_pages(pages, triage)
    print(f"  {len(pages)} total pages, {len(kept)} kept by triage")

    classifier = CategoricalStoryClassifier()
    if not classifier.client:
        print("  ERROR: No API key. Set GOOGLE_API_KEY.")
        return None

    all_results = []
    for i, (page, events) in enumerate(kept):
        ref = page['ref']
        segments = page['segments']

        # Build cross-page context (same as v6 does)
        page_idx = next((j for j, p in enumerate(pages) if p.get('ref') == ref), None)
        prev_segs = None
        next_segs = None
        if page_idx is not None:
            if page_idx > 0:
                prev_segs = pages[page_idx - 1].get('segments', [])[-3:]
            if page_idx < len(pages) - 1:
                next_segs = pages[page_idx + 1].get('segments', [])[:3]

        print(f"  [{i+1}/{len(kept)}] v6 classify {ref}...")
        result = classifier.classify_page(ref, segments, prev_segs, next_segs)

        all_results.append({
            'ref': ref,
            'segments': segments,
            'stories': result.get('stories', []),
        })

        if delay > 0 and i < len(kept) - 1:
            time.sleep(delay)

    # Add skipped pages
    kept_refs = {page['ref'] for page, _ in kept}
    for page in pages:
        if page['ref'] not in kept_refs:
            all_results.append({
                'ref': page['ref'],
                'segments': page.get('segments', []),
                'stories': [],
                'skipped_by_triage': True,
            })

    # Sort by page order
    page_order = {p['ref']: i for i, p in enumerate(pages)}
    all_results.sort(key=lambda r: page_order.get(r['ref'], 999))

    output = PROJECT_ROOT / 'results' / 'v7' / 'ablation_v6_triage_merge.json'
    processed = apply_merge_and_pp(all_results, triage, str(output))

    return str(output)


def run_test_b(pages, triage, delay=0.5):
    """
    Test B: v7 Without Triage (all 118 pages)

    Uses v7's constrained detection on ALL pages, skipping triage filtering.
    Then applies cross-page merge and post-processing.
    """
    print("=" * 70)
    print("  TEST B: v7 Detection Without Triage (all pages)")
    print("=" * 70)

    db = GroundTruthDB()
    db.load_from_feedback(FEEDBACK_PATH, V5_PATHS)

    detector = V7StoryDetector(ground_truth_db=db)
    if not detector.client:
        print("  ERROR: No API key. Set GOOGLE_API_KEY.")
        return None

    # Run v7 pipeline with skip_triage=True
    results = detector.run_pipeline(pages, skip_triage=True, delay=delay)

    # Apply post-processing
    output_path = str(PROJECT_ROOT / 'results' / 'v7' / 'ablation_v7_no_triage.json')
    pp = PostProcessor(
        v6_results_path=V6_RESULTS,
        triage_results_path=TRIAGE_PATH,
    )
    processed, pp_stats = pp.apply(results)

    with open(output_path, 'w') as f:
        json.dump(processed, f, indent=2, ensure_ascii=False)
    print(f"  Saved to {output_path}")
    print(f"  Post-processing: {pp_stats['total_demotions']} demotions")

    return output_path


def run_scorecard(paths_and_labels):
    """Run regression test on multiple result files and print comparison."""
    # Import from same directory
    test_dir = Path(__file__).parent
    sys.path.insert(0, str(test_dir))
    from v7_regression_test import run_regression_test

    print("\n" + "=" * 70)
    print("  ABLATION SCORECARD")
    print("=" * 70)

    results = []
    for path, label in paths_and_labels:
        if path and Path(path).exists():
            agrees, total = run_regression_test(v7_results_path=path, label=label)
            results.append((label, agrees, total))
            print()

    if len(results) > 1:
        print("─" * 70)
        print("COMPARISON:")
        for label, agrees, total in results:
            print(f"  {label:20s}: {agrees}/{total} ({100*agrees/total:.1f}%)")
        print("─" * 70)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='v7 Ablation Tests')
    parser.add_argument('--test', choices=['a', 'b', 'both', 'score'],
                        default='score',
                        help='Which test to run (default: score existing)')
    parser.add_argument('--delay', type=float, default=0.5,
                        help='Delay between API calls')
    args = parser.parse_args()

    pages, triage = load_setup()

    paths_and_labels = []

    # Always include baselines
    v7_path = str(PROJECT_ROOT / 'results' / 'v7' / 'ketubot_v7_2-60.json')
    v7pp_path = str(PROJECT_ROOT / 'results' / 'v7' / 'ketubot_v7_2-60_pp.json')
    paths_and_labels.append((v7_path, 'v7'))
    paths_and_labels.append((v7pp_path, 'v7+pp'))

    if args.test in ('a', 'both'):
        path_a = run_test_a(pages, triage, delay=args.delay)
        if path_a:
            paths_and_labels.append((path_a, 'v6+triage+merge'))

    if args.test in ('b', 'both'):
        path_b = run_test_b(pages, triage, delay=args.delay)
        if path_b:
            paths_and_labels.append((path_b, 'v7-no-triage'))

    if args.test == 'score':
        # Score existing ablation results
        ablation_a = str(PROJECT_ROOT / 'results' / 'v7' / 'ablation_v6_triage_merge.json')
        ablation_b = str(PROJECT_ROOT / 'results' / 'v7' / 'ablation_v7_no_triage.json')
        if Path(ablation_a).exists():
            paths_and_labels.append((ablation_a, 'v6+triage+merge'))
        if Path(ablation_b).exists():
            paths_and_labels.append((ablation_b, 'v7-no-triage'))

    run_scorecard(paths_and_labels)
