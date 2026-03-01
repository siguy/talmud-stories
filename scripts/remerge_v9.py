#!/usr/bin/env python3
"""
Remerge Script: Apply v9 fixes to existing results.

Hybrid approach — patches existing v7/v8 results locally, then makes only the
~10 LLM calls needed for the improved stitch prompt (Fix D).

Steps:
  1. Load existing results, triage data, and raw page data
  2. Undo wrong merges — any merge where start_segment_page2 >= 1:
     - Strip merge fields from page N's story
     - Recreate the wrongly-popped story on page N+1
  3. Run only 4d stitch (the fixed version with improved prompt)
  4. Save as v9

Usage:
  python scripts/remerge_v9.py              # Full run (undo + re-stitch)
  python scripts/remerge_v9.py --dry-run    # Show what would change, no LLM calls
"""

import copy
import json
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

from src.ground_truth import GroundTruthDB, EventType
from src.story_detector_v7 import V7StoryDetector

# Configuration
MODEL = "gemini-3-flash-preview"

# Paths
RESULTS_DIR = PROJECT_ROOT / 'results' / 'v7'
INPUT_PATH = RESULTS_DIR / 'ketubot_v7_61-112.json'
TRIAGE_PATH = RESULTS_DIR / 'event_triage_61-112.json'
PAGES_PATH = RESULTS_DIR / 'ketubot_pages_61-112.json'
OUTPUT_PATH = RESULTS_DIR / 'ketubot_v9_61-112.json'


def load_triage_results() -> dict:
    """Load pre-computed triage results as string values (for stitch prompt)."""
    with open(TRIAGE_PATH) as f:
        data = json.load(f)
    return {
        ref: [EventType(s) for s in events]
        for ref, events in data.get('triage_results', {}).items()
    }


def find_bad_merges(pages: list[dict]) -> list[dict]:
    """Find all merges where start_segment_page2 >= 1 (wrong merges to undo)."""
    bad = []
    for page in pages:
        for story in page.get('stories', []):
            if story.get('spans_pages') and story.get('start_segment_page2', 0) >= 1:
                bad.append({
                    'page_n_ref': page['ref'],
                    'page_n1_ref': story['spans_pages'][1],
                    'start_segment_page2': story['start_segment_page2'],
                    'end_segment_page2': story.get('end_segment_page2'),
                    'classification': story['classification'],
                    'summary': story.get('one_sentence_summary', ''),
                })
    return bad


def undo_merge(pages: list[dict], page_n_ref: str, page_n1_ref: str) -> bool:
    """
    Undo a single cross-page merge:
    - Strip merge fields from page N's story
    - Recreate the popped story on page N+1 at position 0

    Returns True if successful.
    """
    # Find page N and the merged story
    page_n = None
    page_n1 = None
    for p in pages:
        if p['ref'] == page_n_ref:
            page_n = p
        elif p['ref'] == page_n1_ref:
            page_n1 = p

    if not page_n or not page_n1:
        print(f"  ERROR: Could not find pages {page_n_ref} / {page_n1_ref}")
        return False

    # Find the merged story on page N
    merged_story = None
    for story in page_n.get('stories', []):
        if (story.get('spans_pages') and
            len(story['spans_pages']) == 2 and
            story['spans_pages'][1] == page_n1_ref):
            merged_story = story
            break

    if not merged_story:
        print(f"  ERROR: No merged story found on {page_n_ref} → {page_n1_ref}")
        return False

    # Extract the page N+1 story info before stripping
    start_p2 = merged_story.get('start_segment_page2')
    end_p2 = merged_story.get('end_segment_page2')
    was_merge_v7 = merged_story.get('cross_page_merge_v7', False)
    original_cls = merged_story.get('classification', 'LOW_CONFIDENCE')

    # Recreate the popped story for page N+1
    # The merged story's summary may have been combined — we can't perfectly
    # recover the original N+1 summary, but the segments are what matter.
    #
    # IMPORTANT: Do NOT set continues_from_previous_page=True here.
    # The stitch function (stitch_cross_page_continuation) skips stories
    # where next page's first story has that flag, assuming the merge already
    # handled it. We want the stitch to fire so it can find the real
    # continuation at the TOP of the page (seg 0-1), separate from this
    # restored story which sits further down.
    restored_story = {
        'start_segment': start_p2,
        'end_segment': end_p2,
        'classification': original_cls,
        'one_sentence_summary': f'[Restored from {page_n_ref} merge]',
        'continuation': {
            'continues_from_previous_page': False,
            'continues_to_next_page': False,
        },
        'restored_from_merge': True,
    }

    # Insert at position 0 of page N+1's stories
    if 'stories' not in page_n1:
        page_n1['stories'] = []
    page_n1['stories'].insert(0, restored_story)

    # Strip merge fields from page N's story
    for field in ['spans_pages', 'start_segment_page2', 'end_segment_page2',
                  'cross_page_merge_v7', 'cross_page_stitched']:
        merged_story.pop(field, None)

    # The continuation flag on page N should still say continues_to_next_page=True
    # (it was set during detection, before the merge)

    print(f"  Undone: {page_n_ref} → {page_n1_ref} "
          f"(restored seg {start_p2}-{end_p2} on {page_n1_ref})")

    return True


def run_remerge(dry_run: bool = False):
    """Main remerge logic."""
    print("=" * 60)
    print("  REMERGE v9: Undo bad merges + re-stitch")
    print("=" * 60)

    # Load inputs
    print("\n--- Loading data ---")
    with open(INPUT_PATH) as f:
        results = json.load(f)
    print(f"  Loaded results: {INPUT_PATH.name} (v={results.get('version')})")

    # Deep copy so we don't modify the original
    results = copy.deepcopy(results)

    pages_data = json.load(open(PAGES_PATH))
    print(f"  Loaded raw pages: {len(pages_data)} pages")

    triage_results = load_triage_results()
    print(f"  Loaded triage: {len(triage_results)} pages")

    # Step 1: Find bad merges
    print("\n--- Step 1: Identify bad merges (start_segment_page2 >= 1) ---")
    bad_merges = find_bad_merges(results['pages'])
    print(f"  Found {len(bad_merges)} bad merges to undo:")
    for m in bad_merges:
        print(f"    {m['page_n_ref']} → {m['page_n1_ref']} "
              f"(seg {m['start_segment_page2']}-{m['end_segment_page2']})")

    if dry_run:
        print("\n  [DRY RUN] Would undo these merges. No LLM calls made.")

        # Also show correct merges that would be left alone
        print("\n--- Correct merges (start_segment_page2 == 0, left alone) ---")
        for page in results['pages']:
            for story in page.get('stories', []):
                if story.get('spans_pages') and story.get('start_segment_page2', 0) == 0:
                    sp = story['spans_pages']
                    flag = 'stitched' if story.get('cross_page_stitched') else 'merge_v7'
                    print(f"    {sp[0]} → {sp[1]} ({flag})")
        return

    # Step 2: Undo bad merges
    print(f"\n--- Step 2: Undoing {len(bad_merges)} merges ---")
    undone_count = 0
    for m in bad_merges:
        if undo_merge(results['pages'], m['page_n_ref'], m['page_n1_ref']):
            undone_count += 1
    print(f"  Undone: {undone_count}/{len(bad_merges)}")

    # Step 3: Run stitch pass (4d) on the now-unmerged stories
    print(f"\n--- Step 3: Re-stitch via LLM (model={MODEL}) ---")
    detector = V7StoryDetector(model_name=MODEL)
    if not detector.client:
        print("ERROR: No API key. Set GOOGLE_API_KEY in .env")
        sys.exit(1)

    stitch_count = detector.stitch_cross_page_continuation(
        results['pages'], pages_data, triage_results, delay=0.5
    )
    print(f"  Stitched: {stitch_count} stories")

    # Step 3b: Clean up restored stories that are now subsumed by a stitch
    # If a stitch from page N covers seg 0 through X on page N+1, any restored
    # story on N+1 whose start_segment <= X is fully covered and should be removed.
    print(f"\n--- Step 3b: Clean up subsumed restored stories ---")
    removed = 0
    # Build a map: page_ref → stitch_end_segment (from stitches targeting that page)
    stitch_coverage = {}
    for page in results['pages']:
        for story in page.get('stories', []):
            if story.get('spans_pages') and story.get('cross_page_stitched'):
                target_ref = story['spans_pages'][1]
                end_p2 = story.get('end_segment_page2', -1)
                stitch_coverage[target_ref] = max(
                    stitch_coverage.get(target_ref, -1), end_p2
                )

    for page in results['pages']:
        ref = page['ref']
        if ref not in stitch_coverage:
            continue
        stitch_end = stitch_coverage[ref]
        original_stories = page.get('stories', [])
        kept = []
        for story in original_stories:
            if (story.get('restored_from_merge') and
                story.get('start_segment', 999) <= stitch_end):
                print(f"  Removed subsumed restored story: {ref} "
                      f"seg {story['start_segment']}-{story['end_segment']}")
                removed += 1
            else:
                kept.append(story)
        page['stories'] = kept
    print(f"  Removed: {removed} subsumed stories")

    # Step 4: Update version and save
    results['version'] = 'v9'
    results['remerge_info'] = {
        'base_version': 'v8',
        'merges_undone': undone_count,
        'stories_stitched': stitch_count,
        'model': MODEL,
    }

    with open(OUTPUT_PATH, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved to {OUTPUT_PATH}")

    # Summary
    print(f"\n--- Summary ---")
    correct_merges = 0
    stitched_merges = 0
    for page in results['pages']:
        for story in page.get('stories', []):
            if story.get('spans_pages'):
                if story.get('cross_page_stitched'):
                    stitched_merges += 1
                else:
                    correct_merges += 1

    print(f"  Bad merges undone: {undone_count}")
    print(f"  Stories re-stitched: {stitch_count}")
    print(f"  Correct merges preserved: {correct_merges}")
    print(f"  Total cross-page stories: {correct_merges + stitched_merges}")

    # Story count by classification
    by_cls = {}
    for page in results['pages']:
        for story in page.get('stories', []):
            cls = story.get('classification', 'NOT_A_STORY')
            by_cls[cls] = by_cls.get(cls, 0) + 1
    print(f"\n  Stories by classification:")
    for cls in ['YES', 'HIGH_CONFIDENCE', 'LOW_CONFIDENCE', 'NOT_A_STORY']:
        print(f"    {cls}: {by_cls.get(cls, 0)}")


if __name__ == '__main__':
    dry = '--dry-run' in sys.argv
    run_remerge(dry_run=dry)
