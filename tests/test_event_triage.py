#!/usr/bin/env python3
"""
Tests for Event Triage (Increment 2).

Tests:
- Unit tests (no API): prompt building, skip logic, parsing
- Integration tests (with API): triage known pages, verify expectations from Jeff's notes

Run:
  PYTHONPATH=. python3 tests/test_event_triage.py          # unit tests only
  PYTHONPATH=. python3 tests/test_event_triage.py --live    # unit + API tests
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ground_truth import GroundTruthDB, EventType
from src.event_triage import EventTriager


# --- Jeff's expectations for event triage ---
# Based on Jeff's notes, these pages should/shouldn't be skipped

JEFF_EVENT_EXPECTATIONS = {
    # Pages Jeff marked as PURE LEGAL → should have <2 NARRATIVE_EVENT → skip
    'Ketubot 2a': {'should_skip': True, 'reason': 'All legal discussion about wedding timing'},
    'Ketubot 4a': {'should_skip': True, 'reason': 'Legal rulings, not stories'},
    'Ketubot 12b': {'should_skip': True, 'reason': 'Legal rulings and hypotheticals'},
    'Ketubot 57b': {'should_skip': True, 'reason': 'Entire page is legal Mishna discussion'},

    # Pages with confirmed stories → should have ≥2 NARRATIVE_EVENT → keep
    'Ketubot 2b': {'should_skip': False, 'reason': 'Contains confirmed story (certain man)'},
    'Ketubot 10b': {'should_skip': False, 'reason': '3 confirmed stories (Jeff: definitely stories)'},
    'Ketubot 8b': {'should_skip': False, 'reason': 'Contains Reish Lakish mourning story'},
    'Ketubot 59b': {'should_skip': False, 'reason': 'Contains multiple confirmed stories'},
    'Ketubot 60a': {'should_skip': False, 'reason': 'Contains confirmed story'},

    # Pages Jeff said were legal misidentifications → should skip
    'Ketubot 42b': {'should_skip': True, 'reason': 'Jeff: legal difficulty/resolution, not events'},
    'Ketubot 55a': {'should_skip': True, 'reason': 'Jeff: legal debate between academies'},
    'Ketubot 56a': {'should_skip': True, 'reason': 'Jeff: legal debate with setting, just debate'},
    'Ketubot 40b': {'should_skip': True, 'reason': 'Jeff: rabbis making legal arguments'},
}


def get_db():
    project_root = Path(__file__).parent.parent
    feedback_path = str(project_root / 'validation' / 'feedback' /
                        'v5_1_feedback_anonymous_2026-02-05 (1).json')
    v5_paths = [
        str(project_root / 'results' / 'v5' / 'pages_2-39.json'),
        str(project_root / 'results' / 'v5' / 'pages_40-60.json'),
    ]
    db = GroundTruthDB()
    db.load_from_feedback(feedback_path, v5_paths)
    return db


def load_pages():
    """Load all v5.1 page data (which has the segments)."""
    project_root = Path(__file__).parent.parent
    all_pages = []
    for fname in ['pages_2-39.json', 'pages_40-60.json']:
        path = project_root / 'results' / 'v5' / fname
        with open(path) as f:
            data = json.load(f)
            all_pages.extend(data.get('pages', []))
    return all_pages


# ============================================================
# UNIT TESTS (no API required)
# ============================================================

def test_should_skip_logic():
    """should_skip_page works correctly."""
    # All deliberation → skip
    assert EventTriager.should_skip_page([
        EventType.DELIBERATION, EventType.DELIBERATION, EventType.VERBAL_ACT
    ]) == True

    # 1 narrative + 0 verbal → KEEP since 2026-08-31. Both of these used to be
    # skips; they were the corroboration clause, measured as the richest seam of
    # missed stories in the corpus (6 real stories on the 8 pages it discarded,
    # Ketubot 51a among them). See tests/test_triage_single_narrative.py.
    assert EventTriager.should_skip_page([
        EventType.NARRATIVE_EVENT, EventType.DELIBERATION, EventType.DELIBERATION
    ]) == False

    # 1 narrative + 1 verbal → KEEP since 2026-08-31 (was: "need 2 verbal")
    assert EventTriager.should_skip_page([
        EventType.NARRATIVE_EVENT, EventType.VERBAL_ACT, EventType.DELIBERATION
    ]) == False

    # 1 narrative + 2 verbal → keep (story with dialogue)
    assert EventTriager.should_skip_page([
        EventType.NARRATIVE_EVENT, EventType.VERBAL_ACT, EventType.VERBAL_ACT
    ]) == False

    # 2 narrative events → keep
    assert EventTriager.should_skip_page([
        EventType.NARRATIVE_EVENT, EventType.DELIBERATION, EventType.NARRATIVE_EVENT
    ]) == False

    # 3 narrative events → keep
    assert EventTriager.should_skip_page([
        EventType.NARRATIVE_EVENT, EventType.NARRATIVE_EVENT, EventType.NARRATIVE_EVENT
    ]) == False

    # Empty → skip
    assert EventTriager.should_skip_page([]) == True

    print("PASS: should_skip_page logic correct")


def test_prompt_building():
    """Prompt builds without errors and contains required elements."""
    db = get_db()
    triager = EventTriager(api_key="dummy", ground_truth_db=db)
    triager.client = None  # Don't need real client for prompt building

    segments = [
        {'index': 0, 'english': 'This is a test segment.', 'hebrew': 'טקסט לדוגמא'},
        {'index': 1, 'english': 'Another segment here.', 'hebrew': 'קטע נוסף'},
    ]

    prompt = triager.build_event_triage_prompt('Ketubot 2a', segments)

    assert 'NARRATIVE_EVENT' in prompt
    assert 'VERBAL_ACT' in prompt
    assert 'DELIBERATION' in prompt
    assert 'HABITUAL' in prompt
    assert 'Ketubot 2a' in prompt
    assert 'Segment 0' in prompt
    assert 'Segment 1' in prompt
    assert 'legal debate' in prompt.lower() or 'legal discussion' in prompt.lower()

    print(f"PASS: Prompt builds correctly ({len(prompt)} chars)")


def test_summarize():
    """summarize_triage works correctly."""
    results = {
        'Page A': [EventType.NARRATIVE_EVENT, EventType.NARRATIVE_EVENT, EventType.DELIBERATION],
        'Page B': [EventType.DELIBERATION, EventType.DELIBERATION],
        'Page C': [EventType.NARRATIVE_EVENT, EventType.VERBAL_ACT, EventType.NARRATIVE_EVENT],
    }
    summary = EventTriager.summarize_triage(results)
    assert summary['total_pages'] == 3
    assert summary['skipped'] == 1  # Page B
    assert summary['kept'] == 2
    assert summary['total_segments'] == 8

    print("PASS: summarize_triage correct")


# ============================================================
# INTEGRATION TESTS (require API)
# ============================================================

def run_live_triage(pages):
    """Run triage on real pages and check against Jeff's expectations."""
    db = get_db()
    triager = EventTriager(ground_truth_db=db)

    if not triager.client:
        print("SKIP: No Gemini API configured (set GOOGLE_API_KEY)")
        return

    # Build page lookup
    page_lookup = {p['ref']: p for p in pages}

    # Triage the expected pages
    passed = 0
    failed = 0
    false_skips = []

    for ref, expectation in JEFF_EVENT_EXPECTATIONS.items():
        page = page_lookup.get(ref)
        if not page:
            print(f"  WARNING: Page {ref} not found in data")
            continue

        event_types = triager.triage_page(ref, page['segments'])
        skip = EventTriager.should_skip_page(event_types)
        ne_count = sum(1 for et in event_types if et == EventType.NARRATIVE_EVENT)

        expected_skip = expectation['should_skip']
        if skip == expected_skip:
            print(f"  OK: {ref} skip={skip} (expected), NE={ne_count}")
            passed += 1
        else:
            print(f"  MISMATCH: {ref} skip={skip} (expected {expected_skip}), "
                  f"NE={ne_count} — {expectation['reason']}")
            failed += 1
            if skip and not expected_skip:
                false_skips.append(ref)

    print(f"\nExpectation results: {passed}/{passed+failed} match")
    if false_skips:
        print(f"  FALSE SKIPS (stories Jeff confirmed that got skipped): {false_skips}")
    return passed, failed, false_skips


def run_full_triage(pages):
    """Run triage on all pages 2-60 and report skip rate."""
    db = get_db()
    triager = EventTriager(ground_truth_db=db)

    if not triager.client:
        print("SKIP: No Gemini API configured")
        return

    triage_results = triager.triage_all_pages(pages, delay=0.5)
    summary = EventTriager.summarize_triage(triage_results)

    print(f"\nFull triage summary (pages 2-60):")
    print(f"  Total pages: {summary['total_pages']}")
    print(f"  Skipped: {summary['skipped']} ({summary['skip_rate']})")
    print(f"  Kept: {summary['kept']}")
    print(f"  Event type counts: {summary['event_type_counts']}")

    # Save results for later use
    project_root = Path(__file__).parent.parent
    output_path = project_root / 'results' / 'v7' / 'event_triage_2-60.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert EventType to string for JSON serialization
    serializable = {}
    for ref, events in triage_results.items():
        serializable[ref] = [et.value for et in events]

    with open(output_path, 'w') as f:
        json.dump({
            'version': 'v7_event_triage',
            'summary': summary,
            'triage_results': serializable,
        }, f, indent=2)
    print(f"  Saved to {output_path}")

    # Verify: no Jeff-confirmed stories should be skipped
    db_entries = db.entries
    jeff_story_pages = set()
    for key, entry in db_entries.items():
        if entry.jeff_wants == 'STORY' and entry.page_ref:
            jeff_story_pages.add(entry.page_ref)

    false_skips = []
    for ref in jeff_story_pages:
        events = triage_results.get(ref, [])
        if events and EventTriager.should_skip_page(events):
            false_skips.append(ref)

    if false_skips:
        print(f"\n  WARNING: False skips (pages with Jeff-confirmed stories that got skipped):")
        for ref in sorted(false_skips):
            print(f"    {ref}")
    else:
        print(f"\n  No false skips detected!")

    return triage_results


if __name__ == '__main__':
    live = '--live' in sys.argv

    print("=" * 60)
    print("  EVENT TRIAGE TESTS (Increment 2)")
    print("=" * 60)

    # Unit tests (always run)
    print("\n--- Unit Tests ---")
    test_should_skip_logic()
    test_prompt_building()
    test_summarize()

    if live:
        print("\n--- Live API Tests ---")
        pages = load_pages()
        print(f"Loaded {len(pages)} pages")
        run_live_triage(pages)
        print("\n--- Full Triage Run ---")
        run_full_triage(pages)
    else:
        print("\n(Skipping live API tests — run with --live to enable)")

    print("\nDone.")
