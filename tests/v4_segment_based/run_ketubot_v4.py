#!/usr/bin/env python3
"""
Ketubot Analysis - Version 4 (Segment-Based)
Runs segment-based story detection on Ketubot tractate.

Usage:
    python run_ketubot_v4.py [start_page] [end_page]

Examples:
    python run_ketubot_v4.py 2 39      # First 1/3 of Ketubot
    python run_ketubot_v4.py 2 112     # Full Ketubot
    python run_ketubot_v4.py           # Default: first 1/3
"""

import sys
import os
import json
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from find_talmud_stories import (
    NarrativeAnalyzer, SefariaStoryFinder,
    preprocess_segments, detect_continuations, build_story_groups
)

# Version info
VERSION = "v4.0"
VERSION_NAME = "segment-based"
VERSION_DATE = "2025-01-20"


def generate_page_refs(tractate: str, start_page: int, end_page: int):
    """Generate all page references for a range."""
    refs = []
    for page in range(start_page, end_page + 1):
        refs.append(f"{tractate} {page}a")
        refs.append(f"{tractate} {page}b")
    return refs


def run_analysis(start_page: int = 2, end_page: int = 39):
    """Run segment-based analysis on Ketubot pages."""

    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: Set GOOGLE_API_KEY environment variable")
        return None

    # Initialize
    analyzer = NarrativeAnalyzer(
        api_key=api_key,
        model="gemini-2.0-flash",
        provider="google"
    )
    finder = SefariaStoryFinder(analyzer)

    # Generate page references
    refs = generate_page_refs("Ketubot", start_page, end_page)

    print("=" * 70)
    print(f"KETUBOT ANALYSIS - VERSION {VERSION} ({VERSION_NAME})")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Pages: {start_page}a - {end_page}b ({len(refs)} pages)")
    print(f"Model: gemini-2.0-flash")
    print("=" * 70)

    results = {
        "version": VERSION,
        "version_name": VERSION_NAME,
        "version_date": VERSION_DATE,
        "run_timestamp": datetime.now().isoformat(),
        "tractate": "Ketubot",
        "page_range": f"{start_page}a-{end_page}b",
        "total_pages_analyzed": 0,
        "total_stories_found": 0,
        "pages": []
    }

    story_count = 0

    for i, ref in enumerate(refs):
        print(f"\n[{i+1}/{len(refs)}] {ref}")

        try:
            # Get page with segments
            page_data = finder.get_page_with_segments(ref)
            if not page_data:
                print(f"  SKIP: Could not fetch page")
                continue

            print(f"  Segments: {page_data['total_segments']}")

            # Pre-process segments
            processed = preprocess_segments(page_data['segments'])

            # Show marker info
            high_segs = [s['index'] for s in processed if s['story_likelihood'] == 'HIGH']
            med_segs = [s['index'] for s in processed if s['story_likelihood'] == 'MEDIUM']
            if high_segs:
                print(f"  HIGH likelihood: {high_segs}")
            if med_segs:
                print(f"  MEDIUM likelihood: {med_segs}")

            # Detect continuations
            continuations = detect_continuations(processed)
            if continuations:
                print(f"  Continuations: {continuations}")

            # Build story groups
            story_groups = build_story_groups(processed, continuations)

            # Run AI analysis
            analysis = analyzer.analyze_segments(
                ref, processed, continuations, story_groups
            )

            stories = analysis.get('stories', [])
            print(f"  Stories found: {len(stories)}")

            # Build page result
            page_result = {
                "ref": ref,
                "he_ref": page_data.get('he_ref', ''),
                "total_segments": page_data['total_segments'],
                "segments": page_data['segments'],
                "processed_segments": [
                    {
                        "index": s['index'],
                        "story_likelihood": s['story_likelihood'],
                        "markers": s['all_markers']
                    }
                    for s in processed
                ],
                "continuations": continuations,
                "story_groups": story_groups,
                "analysis": analysis,
                "stories_on_page": len(stories)
            }

            # Add story details
            for story in stories:
                story_count += 1
                start_seg = story.get('start_segment', 0)
                end_seg = story.get('end_segment', start_seg)

                # Extract story text from segments
                story_english = []
                story_hebrew = []
                for seg in page_data['segments']:
                    if start_seg <= seg['index'] <= end_seg:
                        story_english.append(seg['english'])
                        story_hebrew.append(seg['hebrew'])

                story['story_text_english'] = ' '.join(story_english)
                story['story_text_hebrew'] = ' '.join(story_hebrew)
                story['page_ref'] = ref

                print(f"    Story {story.get('start_segment')}-{story.get('end_segment')}: "
                      f"{story.get('story_type', 'unknown')} ({story.get('confidence', 0)}%)")
                summary = story.get('one_sentence_summary', '')[:50]
                print(f"      {summary}...")

            results['pages'].append(page_result)
            results['total_pages_analyzed'] += 1

            time.sleep(0.5)  # Rate limiting

        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    results['total_stories_found'] = story_count

    # Calculate stats
    story_types = {}
    confidence_sum = 0
    confidence_count = 0

    for page in results['pages']:
        for story in page['analysis'].get('stories', []):
            stype = story.get('story_type', 'unknown')
            story_types[stype] = story_types.get(stype, 0) + 1
            if 'confidence' in story:
                confidence_sum += story['confidence']
                confidence_count += 1

    results['stats'] = {
        'story_types': story_types,
        'avg_confidence': round(confidence_sum / confidence_count, 1) if confidence_count > 0 else 0,
        'pages_with_stories': sum(1 for p in results['pages'] if p['stories_on_page'] > 0),
        'pages_without_stories': sum(1 for p in results['pages'] if p['stories_on_page'] == 0)
    }

    # Save results
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'results', 'v4')
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'ketubot_{start_page}-{end_page}_{VERSION}_{timestamp}.json')

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Also save as latest
    latest_file = os.path.join(output_dir, 'ketubot_latest.json')
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"Pages analyzed: {results['total_pages_analyzed']}")
    print(f"Stories found: {results['total_stories_found']}")
    print(f"Average confidence: {results['stats']['avg_confidence']}%")
    print(f"Story types: {results['stats']['story_types']}")
    print(f"\nResults saved to:")
    print(f"  {output_file}")
    print(f"  {latest_file}")
    print("=" * 70)

    return results


if __name__ == "__main__":
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 39  # First 1/3 of Ketubot

    run_analysis(start, end)
