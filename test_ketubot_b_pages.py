#!/usr/bin/env python3
"""
Test script to analyze ONLY the 'b' pages of Tractate Ketubot for narrative stories.
Use this to complete analysis if you've already run the 'a' pages.
"""

import os
import sys
import json
from datetime import datetime
from find_talmud_stories import NarrativeAnalyzer, SefariaStoryFinder


def main():
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Run: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    print("=" * 60)
    print("Analyzing Ketubot (B PAGES ONLY) for narrative structure...")
    print("Using multi-page windowing to detect stories spanning pages")
    print("=" * 60)

    # Initialize
    analyzer = NarrativeAnalyzer(api_key=api_key, model="claude-3-5-haiku-20241022")
    finder = SefariaStoryFinder(analyzer, use_windowing=True)

    # Get sample rate
    sample_input = input("Sample rate (1=all b pages, 2=every other b page, default=1): ").strip()
    sample_rate = int(sample_input) if sample_input else 1

    # Get all references for Ketubot
    all_refs = finder.get_tractate_structure("Ketubot")

    # Filter to ONLY 'b' pages
    b_refs = [ref for ref in all_refs if ref.endswith('b')]

    # Apply sample rate to b pages
    b_refs_to_analyze = b_refs[::sample_rate]

    print(f"\n  Total 'b' pages in Ketubot: {len(b_refs)}")
    print(f"  Analyzing {len(b_refs_to_analyze)} 'b' pages (sample_rate={sample_rate})")
    print()

    # Analyze only b pages
    stories = []
    for i, ref in enumerate(b_refs_to_analyze):
        # Get text
        text_data = finder.get_text(ref)
        if not text_data:
            continue

        # Extract text
        english_text = text_data.get('text', '')
        if isinstance(english_text, list):
            english_text = ' '.join(str(t) for t in english_text if t)

        hebrew_text = text_data.get('he', '')
        if isinstance(hebrew_text, list):
            hebrew_text = ' '.join(str(t) for t in hebrew_text if t)

        if not english_text.strip():
            continue

        # Analyze
        analysis = analyzer.analyze_narrative_structure(english_text, ref, hebrew_text)

        if analysis['is_story']:
            story_entry = {
                "ref": ref,
                "book": "Ketubot",
                "text": english_text,
                "hebrew_text": hebrew_text,
                "analysis": analysis,
                "spans_multiple_pages": False
            }
            stories.append(story_entry)

            # Print found story
            story_type = analysis['story_type']
            confidence = analysis['confidence']
            print(f"  ✓ {ref} - {story_type} (confidence: {confidence}%)")

        # Progress update every 10 sections
        if (i + 1) % 10 == 0:
            print(f"    ... analyzed {i + 1}/{len(b_refs_to_analyze)} b pages")

    # Check for multi-page stories spanning from b to next a
    # (e.g., story starting on 5b and continuing to 6a)
    print("\n  Checking for stories spanning b→a pages...")
    multi_page_stories = []

    for i, ref in enumerate(b_refs_to_analyze):
        if not ref.endswith('b'):
            continue

        # Get the next 'a' page
        page_num = int(ref.split()[1][:-1])  # Extract page number
        next_ref = f"Ketubot {page_num + 1}a"

        # Get combined text
        combined_data = finder.get_combined_text([ref, next_ref])
        if not combined_data:
            continue

        combined_english = combined_data.get('text', '')
        combined_hebrew = combined_data.get('he', '')
        combined_ref = f"{ref.split()[1]}-{next_ref.split()[1]}"

        if not combined_english.strip():
            continue

        # Analyze combined
        combined_analysis = analyzer.analyze_narrative_structure(
            combined_english,
            f"Ketubot {combined_ref}",
            combined_hebrew
        )

        if combined_analysis['is_story'] and combined_analysis['confidence'] >= 70:
            # Check if this is better than individual page analysis
            story_entry = {
                "ref": f"Ketubot {combined_ref}",
                "book": "Ketubot",
                "text": combined_english,
                "hebrew_text": combined_hebrew,
                "analysis": combined_analysis,
                "spans_multiple_pages": True
            }
            multi_page_stories.append(story_entry)

            story_type = combined_analysis['story_type']
            confidence = combined_analysis['confidence']
            print(f"  ✓✓ Ketubot {combined_ref} - MULTI-PAGE {story_type} (confidence: {confidence}%)")

    # Combine all stories
    all_stories = stories + multi_page_stories

    # Sort by confidence
    all_stories.sort(key=lambda x: x['analysis']['confidence'], reverse=True)

    # Save results
    output_file = "ketubot_stories_b_pages.json"
    output = {
        "total_stories": len(all_stories),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "definition": "Literary Stories - any narrative arc with beginning, middle, and end",
        "note": "This file contains ONLY stories from 'b' pages of Ketubot",
        "stories": all_stories
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total stories found on b pages: {len(all_stories)}")
    print(f"  Single-page stories: {len(stories)}")
    print(f"  Multi-page stories (b→a): {len(multi_page_stories)}")

    # By type
    full_narratives = [s for s in all_stories if s['analysis']['story_type'] == 'full_narrative']
    dialogue_vignettes = [s for s in all_stories if s['analysis']['story_type'] == 'dialogue_vignette']
    brief_anecdotes = [s for s in all_stories if s['analysis']['story_type'] == 'brief_anecdote']

    print(f"\nBy type:")
    print(f"  Full narratives: {len(full_narratives)}")
    print(f"  Dialogue vignettes: {len(dialogue_vignettes)}")
    print(f"  Brief anecdotes: {len(brief_anecdotes)}")

    # Confidence stats
    if all_stories:
        avg_confidence = sum(s['analysis']['confidence'] for s in all_stories) / len(all_stories)
        high_conf = [s for s in all_stories if s['analysis']['confidence'] >= 90]

        print(f"\nAverage confidence: {avg_confidence:.1f}%")
        print(f"High confidence stories (90%+): {len(high_conf)}")

        # Top stories
        print(f"\nTop 5 B-page Stories by Confidence:")
        for i, story in enumerate(all_stories[:5], 1):
            ref = story['ref']
            conf = story['analysis']['confidence']
            story_type = story['analysis']['story_type']
            summary = story['analysis'].get('one_sentence_summary', 'No summary')[:80]

            print(f"{i}. {ref} - {conf}%")
            print(f"   Type: {story_type}")
            print(f"   Summary: {summary}...")

    print(f"\nResults saved to: {output_file}")
    print("\nNext step: Merge with ketubot_stories.json (from 'a' pages) using merge script")


if __name__ == "__main__":
    main()
