#!/usr/bin/env python3
"""
Analyze v5.1 results for Ketubot 40-60 (fresh validation range).
Compare with pages 2-39 to test extrapolation.
"""

import json
from collections import defaultdict

def load_results(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def analyze_results(data, label):
    """Analyze results for a given range"""
    print(f"\n{'='*80}")
    print(f"{label}")
    print(f"{'='*80}\n")

    # Basic stats
    print(f"Pages analyzed: {len(data['pages'])}")
    print(f"YES: {data['summary']['yes']}")
    print(f"HIGH_CONFIDENCE: {data['summary']['high_confidence']}")
    print(f"LOW_CONFIDENCE: {data['summary']['low_confidence']}")
    print(f"NOT_A_STORY: {data['summary']['not_a_story']}")

    total_stories = data['summary']['yes'] + data['summary']['high_confidence'] + data['summary']['low_confidence']
    total_segments = sum(len(p['stories']) for p in data['pages'])

    print(f"\nTotal stories found (YES+HIGH+LOW): {total_stories}")
    print(f"Total segments analyzed: {total_segments}")
    print(f"Story rate: {total_stories/total_segments*100:.1f}%")
    print(f"Rejection rate: {data['summary']['not_a_story']/total_segments*100:.1f}%")

    # Disqualifier stats
    disq_counts = defaultdict(int)
    weak_counts = defaultdict(int)

    for page in data['pages']:
        for story in page['stories']:
            for disq in story.get('disqualifiers_found', []):
                disq_counts[disq] += 1
            for weak in story.get('weakeners_found', []):
                weak_counts[weak] += 1

    print(f"\n{'='*80}")
    print("DISQUALIFIER PERFORMANCE")
    print(f"{'='*80}")
    for disq, count in sorted(disq_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {disq}: {count} times")

    print(f"\n{'='*80}")
    print("WEAKENER PERFORMANCE")
    print(f"{'='*80}")
    for weak, count in sorted(weak_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {weak}: {count} times")

    # Extract stories
    yes_stories = []
    high_stories = []
    low_stories = []

    for page in data['pages']:
        for story in page['stories']:
            story_data = {
                'page': page['ref'],
                'segments': f"{story['start_segment']}-{story['end_segment']}",
                'summary': story['one_sentence_summary'],
                'criteria': story['criteria_met_count']
            }

            if story['classification'] == 'YES':
                yes_stories.append(story_data)
            elif story['classification'] == 'HIGH_CONFIDENCE':
                high_stories.append(story_data)
            elif story['classification'] == 'LOW_CONFIDENCE':
                low_stories.append(story_data)

    # Print YES stories
    if yes_stories:
        print(f"\n{'='*80}")
        print(f"YES STORIES ({len(yes_stories)})")
        print(f"{'='*80}")
        for i, s in enumerate(yes_stories, 1):
            print(f"\n{i}. {s['page']} (Segs {s['segments']}) - {s['criteria']}/6 criteria")
            print(f"   {s['summary']}")

    # Print HIGH stories
    if high_stories:
        print(f"\n{'='*80}")
        print(f"HIGH_CONFIDENCE STORIES ({len(high_stories)})")
        print(f"{'='*80}")
        for i, s in enumerate(high_stories, 1):
            print(f"\n{i}. {s['page']} (Segs {s['segments']}) - {s['criteria']}/6 criteria")
            print(f"   {s['summary']}")

    # Print LOW stories
    if low_stories:
        print(f"\n{'='*80}")
        print(f"LOW_CONFIDENCE STORIES ({len(low_stories)})")
        print(f"{'='*80}")
        for i, s in enumerate(low_stories, 1):
            print(f"\n{i}. {s['page']} (Segs {s['segments']}) - {s['criteria']}/6 criteria")
            print(f"   {s['summary']}")

    return {
        'total_stories': total_stories,
        'story_rate': total_stories/total_segments*100,
        'disqualifiers': dict(disq_counts),
        'weakeners': dict(weak_counts)
    }

def main():
    # Load both datasets
    data_2_39 = load_results('results/v5/ketubot_v5.1_full_validation_2-39.json')
    data_40_60 = load_results('results/v5/ketubot_v5.1_full_validation_40-60.json')

    # Analyze each
    stats_2_39 = analyze_results(data_2_39, "KETUBOT 2-39 (Jeff's Validation Range)")
    stats_40_60 = analyze_results(data_40_60, "KETUBOT 40-60 (Fresh Validation Range)")

    # Comparison
    print(f"\n{'='*80}")
    print("COMPARISON: EXTRAPOLATION TEST")
    print(f"{'='*80}\n")

    print("Story Rate Consistency:")
    print(f"  Pages 2-39:  {stats_2_39['story_rate']:.1f}%")
    print(f"  Pages 40-60: {stats_40_60['story_rate']:.1f}%")
    diff = abs(stats_2_39['story_rate'] - stats_40_60['story_rate'])
    print(f"  Difference:  {diff:.1f}% {'✓ Consistent' if diff < 5 else '⚠️ Significant variance'}")

    print("\nDisqualifier Usage:")
    print(f"  Pages 2-39:  rabbi_legal_opinion applied {stats_2_39['disqualifiers'].get('rabbi_legal_opinion', 0)} times")
    print(f"  Pages 40-60: rabbi_legal_opinion applied {stats_40_60['disqualifiers'].get('rabbi_legal_opinion', 0)} times")

    print("\nWeakener Usage:")
    common_weakeners = set(stats_2_39['weakeners'].keys()) & set(stats_40_60['weakeners'].keys())
    for weak in sorted(common_weakeners):
        print(f"  {weak}:")
        print(f"    Pages 2-39:  {stats_2_39['weakeners'][weak]}")
        print(f"    Pages 40-60: {stats_40_60['weakeners'][weak]}")

    print(f"\n{'='*80}")
    print("ASSESSMENT")
    print(f"{'='*80}\n")

    if diff < 5:
        print("✅ GOOD: Story rate consistent between ranges")
        print("   v5.1 appears to extrapolate well to unseen content")
    else:
        print("⚠️  CAUTION: Story rate varies significantly between ranges")
        print("   May need to investigate why")

    print("\nReady for Jeff's validation on pages 40-60 (completely fresh content).")

if __name__ == '__main__':
    main()
