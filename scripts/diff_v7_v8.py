#!/usr/bin/env python3
"""Compare v7 and v8 results to identify what changed for Jeff's focused review."""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def load_v7_from_git():
    """Load v7 results from git history (before v8 changes)."""
    result = subprocess.run(
        ['git', 'show', 'HEAD~7:results/v7/ketubot_v7_61-112.json'],
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    return json.loads(result.stdout)


def load_v8():
    """Load current v8 results."""
    with open(PROJECT_ROOT / 'results' / 'v7' / 'ketubot_v7_61-112.json') as f:
        return json.load(f)


def build_lookup(results):
    """Build story lookup keyed by ref_start-end."""
    lookup = {}
    for page in results.get('pages', []):
        ref = page.get('ref', '')
        for story in page.get('stories', []):
            cls = story.get('classification', 'NOT_A_STORY')
            key = f"{ref}_{story.get('start_segment', '?')}-{story.get('end_segment', '?')}"
            lookup[key] = {
                'ref': ref,
                'classification': cls,
                'start': story.get('start_segment'),
                'end': story.get('end_segment'),
                'summary': story.get('one_sentence_summary', ''),
                'spans_pages': story.get('spans_pages'),
                'start_p2': story.get('start_segment_page2'),
                'end_p2': story.get('end_segment_page2'),
            }
    return lookup


def find_overlap(story_data, lookup, min_overlap=0.5):
    """Find overlapping story in lookup by ref + segment overlap."""
    ref = story_data['ref']
    s_range = set(range(story_data['start'] or 0, (story_data['end'] or 0) + 1))
    for key, other in lookup.items():
        if other['ref'] != ref:
            continue
        o_range = set(range(other['start'] or 0, (other['end'] or 0) + 1))
        union = len(s_range | o_range)
        if union == 0:
            continue
        overlap = len(s_range & o_range) / union
        if overlap >= min_overlap:
            return key, other
    return None, None


def compare():
    v7 = load_v7_from_git()
    v8 = load_v8()

    v7_stories = build_lookup(v7)
    v8_stories = build_lookup(v8)

    unchanged = []
    modified = []
    new_in_v8 = []
    removed_in_v8 = []

    # Track which v7 stories we've matched
    matched_v7_keys = set()

    for key, v8s in v8_stories.items():
        # Try exact key match first
        if key in v7_stories:
            v7s = v7_stories[key]
            matched_v7_keys.add(key)
            same_cls = v7s['classification'] == v8s['classification']
            same_spans = v7s['spans_pages'] == v8s['spans_pages']
            same_p2 = (v7s['start_p2'] == v8s['start_p2'] and
                       v7s['end_p2'] == v8s['end_p2'])
            if same_cls and same_spans and same_p2:
                unchanged.append(key)
            else:
                modified.append({
                    'key': key,
                    'v7_key': key,
                    'v7_cls': v7s['classification'],
                    'v8_cls': v8s['classification'],
                    'v7_spans': v7s['spans_pages'],
                    'v8_spans': v8s['spans_pages'],
                    'v7_summary': v7s['summary'][:100],
                    'v8_summary': v8s['summary'][:100],
                })
        else:
            # Try overlap match
            v7_key, v7s = find_overlap(v8s, v7_stories)
            if v7s and v7_key not in matched_v7_keys:
                matched_v7_keys.add(v7_key)
                same_cls = v7s['classification'] == v8s['classification']
                same_spans = v7s['spans_pages'] == v8s['spans_pages']
                if same_cls and same_spans:
                    unchanged.append(key)
                else:
                    modified.append({
                        'key': key,
                        'v7_key': v7_key,
                        'v7_cls': v7s['classification'],
                        'v8_cls': v8s['classification'],
                        'v7_spans': v7s['spans_pages'],
                        'v8_spans': v8s['spans_pages'],
                        'v7_summary': v7s['summary'][:100],
                        'v8_summary': v8s['summary'][:100],
                    })
            else:
                new_in_v8.append({
                    'key': key,
                    'cls': v8s['classification'],
                    'spans': v8s['spans_pages'],
                    'summary': v8s['summary'][:100],
                })

    # Find v7 stories not matched to any v8 story
    for key, v7s in v7_stories.items():
        if key in matched_v7_keys:
            continue
        removed_in_v8.append({
            'key': key,
            'cls': v7s['classification'],
            'spans': v7s['spans_pages'],
            'summary': v7s['summary'][:100],
        })

    # Print results
    total_v7_real = sum(1 for s in v7_stories.values()
                        if s['classification'] != 'NOT_A_STORY')
    total_v8_real = sum(1 for s in v8_stories.values()
                        if s['classification'] != 'NOT_A_STORY')

    print(f'=== V7 → V8 COMPARISON (pages 61-112) ===')
    print(f'  V7 stories: {len(v7_stories)} ({total_v7_real} real)')
    print(f'  V8 stories: {len(v8_stories)} ({total_v8_real} real)')
    print()
    print(f'  Unchanged (skip re-review):  {len(unchanged)}')
    print(f'  Modified (needs re-review):  {len(modified)}')
    print(f'  New in v8 (needs review):    {len(new_in_v8)}')
    print(f'  Removed from v8 (confirm):   {len(removed_in_v8)}')
    print(f'  ---')
    print(f'  TOTAL FOR JEFF: {len(modified) + len(new_in_v8) + len(removed_in_v8)} '
          f'(down from {len(v8_stories)})')
    print()

    if modified:
        print('MODIFIED STORIES (re-review):')
        for m in modified:
            cls_change = f'{m["v7_cls"]} → {m["v8_cls"]}'
            spans_note = ''
            if m['v7_spans'] != m['v8_spans']:
                v7s = m['v7_spans'] or 'single-page'
                v8s = m['v8_spans'] or 'single-page'
                spans_note = f'  | spans: {v7s} → {v8s}'
            print(f'  {m["key"]}: {cls_change}{spans_note}')
            if m['v8_summary']:
                print(f'    {m["v8_summary"]}')
        print()

    if new_in_v8:
        print('NEW IN V8 (needs review):')
        for n in new_in_v8:
            spans = f' (spans {n["spans"]})' if n['spans'] else ''
            print(f'  {n["key"]}: {n["cls"]}{spans}')
            if n['summary']:
                print(f'    {n["summary"]}')
        print()

    if removed_in_v8:
        print('REMOVED IN V8 (confirm removal is correct):')
        for r in removed_in_v8:
            print(f'  {r["key"]}: was {r["cls"]}')
            if r['summary']:
                print(f'    {r["summary"]}')
        print()

    # Summary of what Jeff needs to do
    review_count = len(modified) + len(new_in_v8) + len(removed_in_v8)
    print(f'=== JEFF\'S WORKLOAD ===')
    print(f'  Previously reviewed: ~109 stories')
    print(f'  Now needs to review: {review_count} stories')
    print(f'  Reduction: {100 * (1 - review_count / max(len(v8_stories), 1)):.0f}%')

    return {
        'unchanged': unchanged,
        'modified': modified,
        'new_in_v8': new_in_v8,
        'removed_in_v8': removed_in_v8,
    }


if __name__ == '__main__':
    compare()
