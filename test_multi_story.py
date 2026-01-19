#!/usr/bin/env python3
"""
Quick test of the improved multi-story detection on a few sample pages.
Tests pages that Jeffrey identified as having multiple stories.
"""

import os
import sys
import json
from find_talmud_stories import NarrativeAnalyzer, SefariaStoryFinder

# Test pages from Jeffrey's feedback that should have multiple stories
TEST_PAGES = [
    {
        "ref": "Ketubot 10b",
        "expected_stories": 3,
        "note": "Jeffrey identified 3 separate stories"
    },
    {
        "ref": "Ketubot 62b",
        "expected_stories": 2,
        "note": "Jeffrey identified 2 separate stories"
    },
    {
        "ref": "Ketubot 67b",
        "expected_stories": 4,
        "note": "Jeffrey identified 4 separate stories"
    }
]

def test_multi_story_detection():
    """Test the improved prompt on pages with multiple stories"""

    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not set")
        print("Run: export ANTHROPIC_API_KEY='your-key'")
        sys.exit(1)

    print("=" * 80)
    print("Testing Multi-Story Detection on Sample Pages")
    print("=" * 80)
    print()

    # Initialize
    analyzer = NarrativeAnalyzer(api_key=api_key, model="claude-3-5-haiku-20241022")
    finder = SefariaStoryFinder(analyzer, use_windowing=False)

    results = []

    for test_case in TEST_PAGES:
        ref = test_case["ref"]
        expected = test_case["expected_stories"]
        note = test_case["note"]

        print(f"Testing: {ref}")
        print(f"Expected: {expected} stories ({note})")
        print("-" * 80)

        # Fetch text
        text_data = finder.get_text(ref)
        if not text_data:
            print(f"❌ Could not fetch text for {ref}")
            print()
            continue

        # Extract text
        english_text = text_data.get('text', '')
        if isinstance(english_text, list):
            english_text = ' '.join(str(t) for t in english_text if t)

        hebrew_text = text_data.get('he', '')
        if isinstance(hebrew_text, list):
            hebrew_text = ' '.join(str(t) for t in hebrew_text if t)

        # Truncate if needed
        if len(english_text) > 2500:
            english_text = english_text[:2500] + "..."
        if len(hebrew_text) > 2500:
            hebrew_text = hebrew_text[:2500] + "..."

        # Analyze with improved prompt
        analysis = analyzer.analyze_narrative_structure(english_text, ref, hebrew_text)

        # Check results
        total_stories = analysis.get('total_stories', 0)
        stories_found = analysis.get('stories_found', [])

        print(f"AI found: {total_stories} {'story' if total_stories == 1 else 'stories'}")
        print()

        if total_stories == expected:
            print(f"✅ CORRECT - Found expected {expected} stories")
        elif total_stories > expected:
            print(f"⚠️  OVER-DETECTION - Found {total_stories} but expected {expected}")
        else:
            print(f"⚠️  UNDER-DETECTION - Found {total_stories} but expected {expected}")

        print()

        # Show each story summary
        for i, story in enumerate(stories_found, 1):
            confidence = story.get('confidence', 0)
            summary = story.get('one_sentence_summary', 'No summary')
            story_type = story.get('story_type', 'unknown')

            start_eng = story.get('story_start_english', '')[:40]
            end_eng = story.get('story_end_english', '')[:40]

            print(f"Story {i}:")
            print(f"  Type: {story_type}")
            print(f"  Confidence: {confidence}%")
            print(f"  Summary: {summary}")
            print(f"  Starts: '{start_eng}...'")
            print(f"  Ends: '{end_eng}...'")

            # Test extraction
            extracted = finder.extract_story_text(
                english_text,
                story.get('story_start_english', ''),
                story.get('story_end_english', ''),
                language="english"
            )

            if extracted:
                print(f"  ✓ Extraction: {len(extracted)} chars")
            else:
                print(f"  ⚠️  Extraction failed")
            print()

        results.append({
            "ref": ref,
            "expected": expected,
            "found": total_stories,
            "correct": total_stories == expected,
            "stories": stories_found
        })

        print("=" * 80)
        print()

    # Summary
    print("SUMMARY")
    print("=" * 80)
    correct = sum(1 for r in results if r['correct'])
    total = len(results)
    print(f"Accuracy: {correct}/{total} pages had correct story count")
    print()

    for r in results:
        status = "✅" if r['correct'] else "⚠️ "
        print(f"{status} {r['ref']}: Expected {r['expected']}, found {r['found']}")

    print()

    # Save results
    with open('test_multi_story_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("Results saved to: test_multi_story_results.json")


if __name__ == "__main__":
    test_multi_story_detection()
