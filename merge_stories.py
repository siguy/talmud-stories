#!/usr/bin/env python3
"""
Merge stories from 'a' pages and 'b' pages into a single comprehensive file.
This combines ketubot_stories.json (a pages) with ketubot_stories_b_pages.json (b pages).
"""

import json
import sys
from datetime import datetime


def load_json(filename):
    """Load JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: File not found: {filename}")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {filename}: {e}")
        return None


def merge_stories(a_file, b_file, output_file):
    """Merge two story files, removing duplicates and sorting by reference"""

    # Load both files
    a_data = load_json(a_file)
    b_data = load_json(b_file)

    if not a_data or not b_data:
        print("Cannot merge - one or both files are missing or invalid")
        return False

    # Extract stories
    a_stories = a_data.get('stories', [])
    b_stories = b_data.get('stories', [])

    print(f"Loaded {len(a_stories)} stories from {a_file}")
    print(f"Loaded {len(b_stories)} stories from {b_file}")

    # Combine stories
    all_stories = a_stories + b_stories

    # Remove duplicates (by reference)
    seen_refs = set()
    unique_stories = []

    for story in all_stories:
        ref = story.get('ref', '')
        if ref not in seen_refs:
            seen_refs.add(ref)
            unique_stories.append(story)
        else:
            print(f"  Skipping duplicate: {ref}")

    print(f"\nTotal unique stories: {len(unique_stories)}")

    # Sort by reference (page number)
    def get_sort_key(story):
        """Extract page number for sorting (e.g., '62b-63a' -> 62.5)"""
        ref = story.get('ref', '')
        parts = ref.split()
        if len(parts) < 2:
            return 0

        page_part = parts[1]  # e.g., "62b-63a" or "17a"

        # Handle multi-page references (e.g., "62b-63a")
        if '-' in page_part:
            page_part = page_part.split('-')[0]  # Use first page for sorting

        # Extract number and side
        try:
            if page_part[-1] in ['a', 'b']:
                page_num = int(page_part[:-1])
                side = page_part[-1]
                # 'a' = .0, 'b' = .5
                return page_num + (0.5 if side == 'b' else 0.0)
            else:
                return int(page_part)
        except (ValueError, IndexError):
            return 0

    unique_stories.sort(key=get_sort_key)

    # Create merged output
    merged_output = {
        "total_stories": len(unique_stories),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "definition": "Literary Stories - any narrative arc with beginning, middle, and end",
        "note": "Combined stories from both 'a' and 'b' pages of Ketubot",
        "sources": [a_file, b_file],
        "stories": unique_stories
    }

    # Save merged file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_output, f, indent=2, ensure_ascii=False)

    print(f"\nMerged {len(unique_stories)} stories saved to: {output_file}")

    # Print summary statistics
    full_narratives = [s for s in unique_stories if s['analysis']['story_type'] == 'full_narrative']
    dialogue_vignettes = [s for s in unique_stories if s['analysis']['story_type'] == 'dialogue_vignette']
    brief_anecdotes = [s for s in unique_stories if s['analysis']['story_type'] == 'brief_anecdote']
    multi_page = [s for s in unique_stories if s.get('spans_multiple_pages')]

    print("\nSUMMARY")
    print("=" * 60)
    print(f"Total stories: {len(unique_stories)}")
    print(f"  Single-page: {len(unique_stories) - len(multi_page)}")
    print(f"  Multi-page: {len(multi_page)}")
    print(f"\nBy type:")
    print(f"  Full narratives: {len(full_narratives)}")
    print(f"  Dialogue vignettes: {len(dialogue_vignettes)}")
    print(f"  Brief anecdotes: {len(brief_anecdotes)}")

    if unique_stories:
        avg_confidence = sum(s['analysis']['confidence'] for s in unique_stories) / len(unique_stories)
        high_conf = [s for s in unique_stories if s['analysis']['confidence'] >= 90]
        print(f"\nAverage confidence: {avg_confidence:.1f}%")
        print(f"High confidence stories (90%+): {len(high_conf)}")

    return True


def main():
    # Default file names
    a_file = "ketubot_stories.json"
    b_file = "ketubot_stories_b_pages.json"
    output_file = "ketubot_stories_complete.json"

    # Allow command line arguments
    if len(sys.argv) >= 2:
        a_file = sys.argv[1]
    if len(sys.argv) >= 3:
        b_file = sys.argv[2]
    if len(sys.argv) >= 4:
        output_file = sys.argv[3]

    print("=" * 60)
    print("Merging Talmud Story Files")
    print("=" * 60)
    print(f"A pages file: {a_file}")
    print(f"B pages file: {b_file}")
    print(f"Output file: {output_file}")
    print()

    success = merge_stories(a_file, b_file, output_file)

    if success:
        print("\n✓ Merge complete!")
        print(f"\nYou can now use review_stories.html with {output_file}")
        print("Just update the fetch() URL in review_stories.html to load the merged file.")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
