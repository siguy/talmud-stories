#!/usr/bin/env python3
"""
Analyze v5.1 test results and compare with Jeff's v4.1 validation.
"""

import json
import sys

def main():
    # Load v5.1 results
    with open('results/v5/ketubot_v5.1_test.json', 'r') as f:
        data = json.load(f)

    # Extract all classified stories
    stories = []
    for page in data.get('pages', []):
        page_ref = page.get('ref', '')
        for story in page.get('stories', []):
            classification = story.get('classification', '')

            if classification in ['YES', 'HIGH_CONFIDENCE', 'LOW_CONFIDENCE']:
                # Count criteria met
                criteria = story.get('criteria', {})
                criteria_met = [k for k, v in criteria.items() if isinstance(v, dict) and v.get('met', False)]

                stories.append({
                    'page': page_ref,
                    'segments': f"{story.get('start_segment', '?')}-{story.get('end_segment', '?')}",
                    'classification': classification,
                    'summary': story.get('one_sentence_summary', ''),
                    'criteria_met': criteria_met,
                    'criteria_count': story.get('criteria_met_count', 0),
                    'weakeners': story.get('weakeners_found', []),
                    'disqualifiers': story.get('disqualifiers_found', []),
                    'reasoning': story.get('classification_reasoning', '')
                })

    # Print summary
    print("=" * 70)
    print("V5.1 STORIES FOUND (HIGH_CONFIDENCE and LOW_CONFIDENCE only)")
    print("=" * 70)
    print()

    high_conf = [s for s in stories if s['classification'] == 'HIGH_CONFIDENCE']
    low_conf = [s for s in stories if s['classification'] == 'LOW_CONFIDENCE']

    print(f"HIGH_CONFIDENCE: {len(high_conf)}")
    print(f"LOW_CONFIDENCE: {len(low_conf)}")
    print(f"TOTAL: {len(stories)}")
    print()

    # Print HIGH_CONFIDENCE stories
    if high_conf:
        print("=" * 70)
        print("HIGH_CONFIDENCE STORIES")
        print("=" * 70)
        for i, story in enumerate(high_conf, 1):
            print(f"\n{i}. {story['page']} (Segments {story['segments']})")
            print(f"   Summary: {story['summary']}")
            print(f"   Criteria: {story['criteria_count']}/6 ({', '.join(story['criteria_met'])})")
            if story['weakeners']:
                print(f"   Weakeners: {', '.join(story['weakeners'])}")
            if story['reasoning']:
                print(f"   Reasoning: {story['reasoning'][:200]}...")

    # Print LOW_CONFIDENCE stories
    if low_conf:
        print("\n" + "=" * 70)
        print("LOW_CONFIDENCE STORIES")
        print("=" * 70)
        for i, story in enumerate(low_conf, 1):
            print(f"\n{i}. {story['page']} (Segments {story['segments']})")
            print(f"   Summary: {story['summary']}")
            print(f"   Criteria: {story['criteria_count']}/6 ({', '.join(story['criteria_met'])})")
            if story['weakeners']:
                print(f"   Weakeners: {', '.join(story['weakeners'])}")
            if story['reasoning']:
                print(f"   Reasoning: {story['reasoning'][:200]}...")

    print("\n" + "=" * 70)
    print("COMPARISON WITH JEFF'S V4.1 VALIDATION")
    print("=" * 70)
    print()
    print("Jeff's validation covered Ketubot pages 2-39 with 30 stories:")
    print("  - 15 TRUE stories (correct)")
    print("  - 15 FALSE positives (should have been rejected)")
    print()
    print("Key false positive patterns Jeff identified:")
    print("  1. Rabbi stating legal opinion (mistaken as character)")
    print("  2. Sequential events without causation")
    print("  3. Simple reports without change/transformation")
    print("  4. Ceremonial actions without narrative arc")
    print()
    print("V5.1 improvements should catch these patterns via:")
    print("  - New disqualifier: rabbi_legal_opinion")
    print("  - Stricter causality test (causal vs sequential)")
    print("  - Stricter change test (transformation vs report)")
    print("  - New weakeners: simple_report, minimal_causality, minimal_change")
    print()

    # Check for specific pages Jeff validated
    print("Stories found in Jeff's validation pages:")
    jeff_pages = set()
    for story in stories:
        page_num = int(story['page'].split()[1].replace('a', '').replace('b', ''))
        if 2 <= page_num <= 10:  # Our test range
            jeff_pages.add(story['page'])

    for page in sorted(jeff_pages):
        page_stories = [s for s in stories if s['page'] == page]
        print(f"  {page}: {len(page_stories)} story/stories")
        for s in page_stories:
            print(f"    - {s['classification']}: {s['summary'][:80]}...")

if __name__ == '__main__':
    main()
