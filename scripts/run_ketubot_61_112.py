#!/usr/bin/env python3
"""
Phase 4: Run winning pipeline on Ketubot 61-112 (unseen pages).

Tests generalization on pages the pipeline has never seen.
Uses Gemini 3 Flash (winning model from Phase 3) with full v7 pipeline.

Usage:
  python scripts/run_ketubot_61_112.py               # Full run (triage + detection)
  python scripts/run_ketubot_61_112.py --triage-only  # Just triage (to check skip rate)
  python scripts/run_ketubot_61_112.py --resume       # Resume from saved triage
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
TRACTATE = "Ketubot"
START_PAGE = 61
END_PAGE = 112
DELAY = 0.5  # seconds between API calls

# Output paths
RESULTS_DIR = PROJECT_ROOT / 'results' / 'v7'
TRIAGE_PATH = RESULTS_DIR / 'event_triage_61-112.json'
RESULTS_PATH = RESULTS_DIR / 'ketubot_v7_61-112.json'
PAGES_CACHE_PATH = RESULTS_DIR / 'ketubot_pages_61-112.json'

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
    """Fetch all Ketubot pages 61a-112b from Sefaria (or load from cache)."""
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
    # Load ground truth for few-shot examples (from pages 2-60)
    feedback_path = str(PROJECT_ROOT / 'validation' / 'feedback' /
                        'v5_1_feedback_anonymous_2026-02-05 (1).json')
    v5_paths = [
        str(PROJECT_ROOT / 'results' / 'v5' / 'pages_2-39.json'),
        str(PROJECT_ROOT / 'results' / 'v5' / 'pages_40-60.json'),
    ]

    db = GroundTruthDB()
    if Path(feedback_path).exists():
        db.load_from_feedback(feedback_path, v5_paths)
        print(f"  Loaded ground truth for few-shot examples")
    else:
        print(f"  WARNING: No ground truth found, running without few-shot examples")

    # Create detector
    detector = V7StoryDetector(ground_truth_db=db, model_name=MODEL)
    if not detector.client:
        print("ERROR: No API key. Set GOOGLE_API_KEY.")
        sys.exit(1)

    # Run pipeline with pre-computed triage
    results = detector.run_pipeline(pages, triage_results=triage_results, delay=DELAY)

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
    for page in pages:
        for story in page.get('stories', []):
            cls = story.get('classification', 'NOT_A_STORY')
            stories_by_class[cls] = stories_by_class.get(cls, 0) + 1

    total_stories = stories_by_class['YES'] + stories_by_class['HIGH_CONFIDENCE'] + stories_by_class['LOW_CONFIDENCE']

    print(f"\n{'='*60}")
    print(f"  PHASE 4 RESULTS: {TRACTATE} {START_PAGE}-{END_PAGE}")
    print(f"{'='*60}")
    print(f"  Pages: {total_pages} total, {skipped} skipped by triage, {processed} processed")
    print(f"  Stories found: {total_stories}")
    print(f"    YES:             {stories_by_class['YES']}")
    print(f"    HIGH_CONFIDENCE: {stories_by_class['HIGH_CONFIDENCE']}")
    print(f"    LOW_CONFIDENCE:  {stories_by_class['LOW_CONFIDENCE']}")
    print(f"    NOT_A_STORY:     {stories_by_class['NOT_A_STORY']}")
    print(f"  Model: {MODEL}")
    print(f"{'='*60}")


def generate_review_ui(results: dict):
    """Generate review UI HTML for Jeff's review."""
    ui_path = PROJECT_ROOT / 'validation' / 'ui' / 'ketubot_61-112.html'

    # The existing generate_review_ui.py expects a 'summary' key
    # Add it for compatibility
    if 'summary' not in results:
        stories_by_class = {'yes': 0, 'high_confidence': 0, 'low_confidence': 0, 'not_a_story': 0}
        for page in results.get('pages', []):
            for story in page.get('stories', []):
                cls = story.get('classification', 'NOT_A_STORY')
                key = cls.lower()
                stories_by_class[key] = stories_by_class.get(key, 0) + 1
        results['summary'] = stories_by_class

    # Import and use the existing generator
    sys.path.insert(0, str(PROJECT_ROOT / 'validation' / 'generators'))
    from generate_review_ui import generate_html

    generate_html(results, str(ui_path))
    print(f"  Review UI saved to {ui_path}")

    # Count stories for Jeff review
    story_count = sum(
        1 for page in results.get('pages', [])
        for story in page.get('stories', [])
        if story.get('classification') != 'NOT_A_STORY'
    )
    print(f"  Stories for review: {story_count}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Phase 4: Ketubot 61-112')
    parser.add_argument('--triage-only', action='store_true',
                        help='Only run triage (no detection)')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from saved triage results')
    parser.add_argument('--skip-ui', action='store_true',
                        help='Skip review UI generation')
    args = parser.parse_args()

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

    # Step 3: Detection
    results = run_detection(pages, triage_results)

    # Step 4: Summary
    print_summary(results)

    # Step 5: Review UI
    if not args.skip_ui:
        generate_review_ui(results)
