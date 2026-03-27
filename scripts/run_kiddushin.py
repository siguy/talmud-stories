#!/usr/bin/env python3
"""
Run the story detection pipeline on Kiddushin (2a-82b).

First new tractate after Ketubot golden dataset (0.93 composite).
Tests generalization of the detector trained on Ketubot examples.

Usage:
  python scripts/run_kiddushin.py               # Full run (triage + detection)
  python scripts/run_kiddushin.py --triage-only  # Just triage (to check skip rate)
  python scripts/run_kiddushin.py --resume       # Resume from saved triage
"""

import json
import os
import re
import sys
import time
import requests
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

from src.event_triage import EventTriager
from src.ground_truth import GroundTruthDB, EventType
from src.story_detector_v7 import (
    V7StoryDetector,
    merge_cross_page_stories_v7,
    merge_cross_page_stories,
    refine_boundaries_with_event_tags,
    detect_duplicate_stories,
)

# Configuration
MODEL = "gemini-3-flash-preview"
TRACTATE = "Kiddushin"
START_PAGE = 2
END_PAGE = 82
DELAY = 0.5  # seconds between API calls

# Output paths
RESULTS_DIR = PROJECT_ROOT / 'results' / 'kiddushin'
TRIAGE_PATH = RESULTS_DIR / 'event_triage_kiddushin.json'
RESULTS_PATH = RESULTS_DIR / 'kiddushin_v7.json'
PAGES_CACHE_PATH = RESULTS_DIR / 'kiddushin_pages.json'

# Sefaria API
SEFARIA_API = "https://www.sefaria.org/api"


def get_page_with_segments(ref: str) -> dict | None:
    """Fetch page from Sefaria with segments preserved."""
    url = f"{SEFARIA_API}/texts/{ref}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        text_segments = data.get('text', [])
        hebrew_segments = data.get('he', [])

        # Handle nested lists
        if text_segments and isinstance(text_segments[0], list):
            text_segments = [item for sublist in text_segments for item in sublist]
            hebrew_segments = [item for sublist in hebrew_segments for item in sublist]

        min_len = min(len(text_segments), len(hebrew_segments))

        return {
            'ref': ref,
            'segments': [
                {
                    'index': i,
                    'english': str(text_segments[i]) if text_segments[i] else '',
                    'hebrew': str(hebrew_segments[i]) if hebrew_segments[i] else ''
                }
                for i in range(min_len)
            ]
        }
    except Exception as e:
        print(f"  Error fetching {ref}: {e}")
        return None


def fetch_all_pages() -> list[dict]:
    """Fetch all Kiddushin pages 2a-82b from Sefaria (or load from cache)."""
    if PAGES_CACHE_PATH.exists():
        print(f"Loading cached pages from {PAGES_CACHE_PATH}")
        with open(PAGES_CACHE_PATH) as f:
            return json.load(f)

    print(f"\n--- Fetching {TRACTATE} {START_PAGE}a-{END_PAGE}b from Sefaria ---")
    pages = []
    for page_num in range(START_PAGE, END_PAGE + 1):
        for side in ['a', 'b']:
            ref = f"{TRACTATE} {page_num}{side}"
            page_data = get_page_with_segments(ref)
            if page_data:
                pages.append(page_data)
                n_segs = len(page_data['segments'])
                print(f"  Fetched {ref}: {n_segs} segments")
            else:
                print(f"  MISSING {ref}")
            time.sleep(0.3)  # Be nice to Sefaria API

    # Cache for re-runs
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(PAGES_CACHE_PATH, 'w') as f:
        json.dump(pages, f, ensure_ascii=False)
    print(f"\nCached {len(pages)} pages to {PAGES_CACHE_PATH}")
    return pages


def save_triage_results(triage_results: dict[str, list[EventType]]):
    """Save triage results to JSON."""
    serializable = {
        'triage_results': {
            ref: [et.value for et in events]
            for ref, events in triage_results.items()
        }
    }
    with open(TRIAGE_PATH, 'w') as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)
    print(f"Triage results saved to {TRIAGE_PATH}")


def load_triage_results() -> dict[str, list[EventType]]:
    """Load pre-computed triage results."""
    with open(TRIAGE_PATH) as f:
        data = json.load(f)
    return {
        ref: [EventType(s) for s in events]
        for ref, events in data.get('triage_results', {}).items()
    }


def run_triage(pages: list[dict]) -> dict[str, list[EventType]]:
    """Run event triage on all pages."""
    print(f"\n--- Stage 1: Event Triage ({len(pages)} pages, model={MODEL}) ---")
    triager = EventTriager(model_name=MODEL)
    if not triager.client:
        print("ERROR: No API key. Set GOOGLE_API_KEY.")
        sys.exit(1)

    triage_results = triager.triage_all_pages(pages, delay=DELAY)
    save_triage_results(triage_results)

    # Print summary
    skipped = sum(1 for events in triage_results.values()
                  if EventTriager.should_skip_page(events))
    kept = len(triage_results) - skipped
    print(f"\n  Triage summary: {len(triage_results)} pages, "
          f"{skipped} skipped, {kept} kept ({100*skipped/len(triage_results):.0f}% skip rate)")
    return triage_results


def run_detection(pages: list[dict], triage_results: dict[str, list[EventType]]) -> dict:
    """Run v7 detection pipeline with Gemini 3 Flash."""
    # Load ground truth from v5.1 feedback ONLY (Ketubot examples = cross-tractate, no contamination)
    feedback_path = str(PROJECT_ROOT / 'validation' / 'feedback' /
                        'v5_1_feedback_anonymous_2026-02-05 (1).json')
    v5_paths = [
        str(PROJECT_ROOT / 'results' / 'ketubot' / 'v5' / 'pages_2-39.json'),
        str(PROJECT_ROOT / 'results' / 'ketubot' / 'v5' / 'pages_40-60.json'),
    ]

    db = GroundTruthDB()
    if Path(feedback_path).exists():
        db.load_from_feedback(feedback_path, v5_paths)
        print(f"  Loaded ground truth: {len(db.entries)} entries (Ketubot, cross-tractate)")
    else:
        print(f"  WARNING: No ground truth found, running without few-shot examples")

    # Create detector
    detector = V7StoryDetector(ground_truth_db=db, model_name=MODEL)
    if not detector.client:
        print("ERROR: No API key. Set GOOGLE_API_KEY.")
        sys.exit(1)

    # Run pipeline with pre-computed triage and tractate name
    results = detector.run_pipeline(
        pages,
        triage_results=triage_results,
        delay=DELAY,
        tractate=TRACTATE,
    )

    # Save results
    with open(RESULTS_PATH, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {RESULTS_PATH}")

    return results


def print_summary(results: dict):
    """Print detection summary."""
    pages = results.get('pages', [])
    total_pages = len(pages)
    skipped = sum(1 for p in pages if p.get('skipped_by_triage'))
    processed = total_pages - skipped

    stories_by_class = {'YES': 0, 'HIGH_CONFIDENCE': 0, 'LOW_CONFIDENCE': 0, 'NOT_A_STORY': 0}
    cross_page_count = 0
    continuation_check_count = 0
    for page in pages:
        for story in page.get('stories', []):
            cls = story.get('classification', 'NOT_A_STORY')
            stories_by_class[cls] = stories_by_class.get(cls, 0) + 1
            if story.get('spans_pages'):
                cross_page_count += 1
            if story.get('continuation_check_extended'):
                continuation_check_count += 1

    total_stories = stories_by_class['YES'] + stories_by_class['HIGH_CONFIDENCE'] + stories_by_class['LOW_CONFIDENCE']

    print(f"\n{'='*60}")
    print(f"  RESULTS: {TRACTATE} {START_PAGE}a-{END_PAGE}b")
    print(f"{'='*60}")
    print(f"  Pages: {total_pages} total, {skipped} skipped by triage, {processed} processed")
    print(f"  Stories found: {total_stories}")
    print(f"    YES:             {stories_by_class['YES']}")
    print(f"    HIGH_CONFIDENCE: {stories_by_class['HIGH_CONFIDENCE']}")
    print(f"    LOW_CONFIDENCE:  {stories_by_class['LOW_CONFIDENCE']}")
    print(f"    NOT_A_STORY:     {stories_by_class['NOT_A_STORY']}")
    print(f"  Cross-page stories: {cross_page_count}")
    print(f"    Via continuation check (4f): {continuation_check_count}")
    print(f"  Model: {MODEL}")
    print(f"{'='*60}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=f'{TRACTATE} Story Detection')
    parser.add_argument('--triage-only', action='store_true',
                        help='Only run triage (no detection)')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from saved triage results')
    args = parser.parse_args()

    print(f"{'='*60}")
    print(f"  {TRACTATE} Story Detection Pipeline")
    print(f"  Pages: {START_PAGE}a-{END_PAGE}b (164 pages)")
    print(f"  Model: {MODEL}")
    print(f"{'='*60}")

    # Step 1: Fetch pages from Sefaria
    pages = fetch_all_pages()
    print(f"  Total pages: {len(pages)}")

    # Step 2: Triage
    if args.resume and TRIAGE_PATH.exists():
        print(f"\nResuming from saved triage: {TRIAGE_PATH}")
        triage_results = load_triage_results()
        skipped = sum(1 for events in triage_results.values()
                      if EventTriager.should_skip_page(events))
        kept = len(triage_results) - skipped
        print(f"  {len(triage_results)} pages, {skipped} skipped, {kept} kept")
    else:
        triage_results = run_triage(pages)

    if args.triage_only:
        print("\nTriage-only mode. Done.")
        sys.exit(0)

    # Step 3: Detection (includes Stage 4f continuation check)
    results = run_detection(pages, triage_results)

    # Step 4: Summary
    print_summary(results)
