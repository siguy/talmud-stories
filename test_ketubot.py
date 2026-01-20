#!/usr/bin/env python3
"""
Quick test: Run story finder on Tractate Ketubot
"""

import os
import sys

from find_talmud_stories import NarrativeAnalyzer, SefariaStoryFinder

def main():
    print("=" * 70)
    print("Testing Story Finder on Tractate Ketubot")
    print("=" * 70)
    print()

    # Choose provider
    print("Select AI Provider:")
    print("  1. Anthropic Claude (default)")
    print("  2. Google Gemini (recommended - cheaper & faster)")
    provider_choice = input("Choice (1 or 2, default=2): ").strip() or "2"

    if provider_choice == "2":
        # Google Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("\n❌ ERROR: GOOGLE_API_KEY not found!")
            print("Please set your API key:")
            print("  export GOOGLE_API_KEY='your-key-here'")
            print("\nGet your key from: https://aistudio.google.com/app/apikey")
            print("Or run: pip install google-generativeai")
            sys.exit(1)

        print("\nInitializing AI analyzer (Gemini 3 Flash Preview)...")
        analyzer = NarrativeAnalyzer(
            api_key=api_key,
            model="gemini-3-flash-preview",
            provider="google"
        )
        print("✅ Using Google Gemini 3 Flash Preview (fast & cheap)")
    else:
        # Anthropic Claude
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("\n❌ ERROR: ANTHROPIC_API_KEY not found!")
            print("Please set your API key:")
            print("  export ANTHROPIC_API_KEY='your-key-here'")
            print("\nGet your key from: https://console.anthropic.com/")
            sys.exit(1)

        print("\nInitializing AI analyzer (Claude 3.5 Haiku)...")
        analyzer = NarrativeAnalyzer(
            api_key=api_key,
            model="claude-3-5-haiku-20241022",
            provider="anthropic"
        )
        print("✅ Using Anthropic Claude 3.5 Haiku")

    finder = SefariaStoryFinder(analyzer, use_windowing=True)

    print("Multi-page story detection: ENABLED")
    print("Bilingual analysis (Hebrew + English): ENABLED")
    print()

    # Search Ketubot with sample_rate=1 (analyze all sections)
    # Change to sample_rate=2 for every other section (faster, cheaper)
    sample_rate = int(input("Sample rate (1=all sections, 2=every other, default=1): ").strip() or "1")

    stories = finder.search_tractate_systematically("Ketubot", "Test", sample_rate=sample_rate)

    # Save results
    finder.save_results(stories, filename="ketubot_stories.json")

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total stories found: {len(stories)}")

    multi_page = [s for s in stories if s.get('spans_multiple_pages')]
    single_page = [s for s in stories if not s.get('spans_multiple_pages')]

    print(f"  Single-page stories: {len(single_page)}")
    print(f"  Multi-page stories: {len(multi_page)}")

    # Breakdown by type
    full_narratives = [s for s in stories if s['analysis']['story_type'] == 'full_narrative']
    dialogue_vignettes = [s for s in stories if s['analysis']['story_type'] == 'dialogue_vignette']
    brief_anecdotes = [s for s in stories if s['analysis']['story_type'] == 'brief_anecdote']

    print(f"\nBy type:")
    print(f"  Full narratives: {len(full_narratives)}")
    print(f"  Dialogue vignettes: {len(dialogue_vignettes)}")
    print(f"  Brief anecdotes: {len(brief_anecdotes)}")

    # Average confidence
    avg_confidence = sum(s['analysis']['confidence'] for s in stories) / len(stories) if stories else 0
    print(f"\nAverage confidence: {avg_confidence:.1f}%")

    # High confidence stories (90+)
    high_conf = [s for s in stories if s['analysis']['confidence'] >= 90]
    print(f"High confidence stories (90%+): {len(high_conf)}")

    print("\n" + "=" * 70)
    print("Top 5 Stories by Confidence:")
    print("=" * 70)

    sorted_stories = sorted(stories, key=lambda x: x['analysis']['confidence'], reverse=True)
    for i, story in enumerate(sorted_stories[:5], 1):
        analysis = story['analysis']
        print(f"\n{i}. {story['ref']} - {analysis['confidence']}%")
        print(f"   Type: {analysis['story_type']}")
        if analysis.get('one_sentence_summary'):
            print(f"   Summary: {analysis['one_sentence_summary']}")
        preview = story['text'][:150] + "..." if len(story['text']) > 150 else story['text']
        print(f"   Preview: {preview}")
        if story.get('spans_multiple_pages'):
            print(f"   ⚠️  SPANS MULTIPLE PAGES")

    print("\n" + "=" * 70)
    print(f"Full results saved to: ketubot_stories.json")
    print("=" * 70)

if __name__ == "__main__":
    main()
