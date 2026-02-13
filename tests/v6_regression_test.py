#!/usr/bin/env python3
"""
V6 Regression Test: Compare v6 results against Jeff's 128 labeled answers from v5.1.

Jeff reviewed 128 passages from v5.1 (pages 2-60):
  - 107 marked "correct" (v5.1 got it right)
  - 18 marked "incorrect" (v5.1 got it wrong — these are the bugs v6 was built to fix)
  - 3 marked null (with notes — 2 have actionable info, 1 skip)

This script loads v6 results and compares against Jeff's ground truth to produce a scorecard.
"""

import json
import re
import sys
from pathlib import Path


# --- Data Loading ---

def load_v6_results(path: str) -> dict:
    """Load v6 analysis results."""
    with open(path) as f:
        return json.load(f)


def load_jeff_feedback(path: str) -> dict:
    """Load Jeff's feedback JSON."""
    with open(path) as f:
        return json.load(f)


def load_v5_results(paths: list) -> dict:
    """Load v5.1 results for reference (to know what v5.1 classified each passage as)."""
    all_pages = []
    for path in paths:
        with open(path) as f:
            data = json.load(f)
            all_pages.extend(data.get('pages', []))
    return all_pages


# --- Key Parsing ---

def parse_feedback_key(key: str) -> dict:
    """Parse 'Ketubot 40b_11-11' into components."""
    match = re.match(r'Ketubot (\d+[ab])_(\d+)-(\d+)', key)
    if not match:
        return None
    return {
        'page': match.group(1),
        'start_seg': int(match.group(2)),
        'end_seg': int(match.group(3)),
        'ref': f'Ketubot {match.group(1)}',
    }


def make_story_key(page_ref: str, start_seg: int, end_seg: int) -> str:
    """Build a feedback-style key from page ref and segment indices."""
    # Extract page number like "2a" from "Ketubot 2a"
    page = page_ref.replace('Ketubot ', '')
    return f'Ketubot {page}_{start_seg}-{end_seg}'


# --- V5.1 Lookup ---

def build_v5_lookup(v5_pages: list) -> dict:
    """Build a lookup from feedback key -> v5.1 classification."""
    lookup = {}
    for page in v5_pages:
        ref = page.get('ref', '')
        for story in page.get('stories', []):
            key = make_story_key(ref, story['start_segment'], story['end_segment'])
            lookup[key] = story.get('classification', 'UNKNOWN')
    return lookup


# --- V6 Lookup ---

def build_v6_lookup(v6_data: dict) -> dict:
    """
    Build lookup from feedback key -> v6 classification.

    Handles:
    - Normal stories: keyed by page ref + segments
    - Cross-page merged stories: keyed by BOTH the original page keys
    """
    lookup = {}

    for page in v6_data.get('pages', []):
        ref = page.get('ref', '')
        for story in page.get('stories', []):
            cls = story.get('classification', 'UNKNOWN')

            # Normal story
            key = make_story_key(ref, story['start_segment'], story['end_segment'])
            lookup[key] = {
                'classification': cls,
                'start_segment': story['start_segment'],
                'end_segment': story['end_segment'],
                'spans_pages': story.get('spans_pages'),
                'page_ref': ref,
            }

            # Cross-page merged story: also index by page 2 segments
            if story.get('spans_pages') and 'start_segment_page2' in story:
                page2_ref = story['spans_pages'][1] if len(story['spans_pages']) > 1 else ref
                key2 = make_story_key(page2_ref, story['start_segment_page2'], story['end_segment_page2'])
                lookup[key2] = {
                    'classification': cls,
                    'start_segment': story['start_segment_page2'],
                    'end_segment': story['end_segment_page2'],
                    'spans_pages': story['spans_pages'],
                    'page_ref': page2_ref,
                    'merged_into': key,
                }

    return lookup


def find_v6_match(feedback_key: str, parsed: dict, v6_lookup: dict) -> dict:
    """
    Find v6 story matching a feedback key. Tries:
    1. Exact match (same page and same segments)
    2. Overlapping segments on same page (at least 50% of target segments covered)

    Does NOT do loose cross-page matching — cross-page stories are already indexed
    by both their page 1 and page 2 keys in build_v6_lookup.
    """
    # 1. Exact match
    if feedback_key in v6_lookup:
        return v6_lookup[feedback_key]

    # 2. Overlapping match on same page (require >=50% of target covered)
    target_ref = parsed['ref']
    target_start = parsed['start_seg']
    target_end = parsed['end_seg']
    target_len = target_end - target_start + 1

    best_match = None
    best_overlap_ratio = 0

    for key, info in v6_lookup.items():
        if info['page_ref'] != target_ref:
            continue

        # Calculate overlap
        v6_start = info['start_segment']
        v6_end = info['end_segment']
        overlap_start = max(target_start, v6_start)
        overlap_end = min(target_end, v6_end)

        if overlap_start <= overlap_end:
            overlap = overlap_end - overlap_start + 1
            overlap_ratio = overlap / target_len
            if overlap_ratio >= 0.5 and overlap_ratio > best_overlap_ratio:
                best_overlap_ratio = overlap_ratio
                best_match = dict(info)  # copy to avoid mutating
                best_match['match_type'] = 'overlap'

    return best_match


# --- Classification Helpers ---

def is_story_positive(cls: str) -> bool:
    """Is this a positive story classification (YES, HIGH, or LOW)?"""
    return cls in ('YES', 'HIGH_CONFIDENCE', 'LOW_CONFIDENCE')


def is_not_a_story(cls: str) -> bool:
    """Is this NOT_A_STORY?"""
    return cls == 'NOT_A_STORY'


def jeff_wanted_story(feedback_key: str, verdict: str, note: str, v5_cls: str) -> str:
    """
    Determine what Jeff wanted the classification to be.

    Returns: 'STORY' (any positive), 'NOT_A_STORY', or 'SKIP'
    """
    if verdict == 'correct':
        # Jeff agreed with v5.1's classification
        if is_story_positive(v5_cls):
            return 'STORY'
        else:
            return 'NOT_A_STORY'

    elif verdict == 'incorrect':
        # Jeff disagreed — v5.1 was wrong, so Jeff wants the opposite
        if is_story_positive(v5_cls):
            return 'NOT_A_STORY'  # v5.1 said story, Jeff says not
        else:
            return 'STORY'  # v5.1 said not story, Jeff says it is

    elif verdict is None:
        # Null verdicts with notes
        note_lower = (note or '').lower()
        if 'definitely a story' in note_lower or 'high confidence story' in note_lower:
            return 'STORY'
        return 'SKIP'

    return 'SKIP'


# --- Main Test ---

def run_regression_test():
    project_root = Path(__file__).parent.parent

    # Load data
    v6_path = project_root / 'results' / 'v6' / 'ketubot_v6_2-60.json'
    if not v6_path.exists():
        print(f"ERROR: V6 results not found at {v6_path}")
        print("Run: cd src && python3 story_detector_v6.py 2 60")
        sys.exit(1)

    feedback_path = project_root / 'validation' / 'feedback' / 'v5_1_feedback_anonymous_2026-02-05 (1).json'
    if not feedback_path.exists():
        print(f"ERROR: Jeff's feedback not found at {feedback_path}")
        sys.exit(1)

    v5_paths = [
        project_root / 'results' / 'ketubot' / 'v5' / 'pages_2-39.json',
        project_root / 'results' / 'ketubot' / 'v5' / 'pages_40-60.json',
    ]

    v6_data = load_v6_results(str(v6_path))
    feedback_data = load_jeff_feedback(str(feedback_path))
    v5_pages = load_v5_results([str(p) for p in v5_paths])

    v6_lookup = build_v6_lookup(v6_data)
    v5_lookup = build_v5_lookup(v5_pages)

    # Counters
    total = 0
    agrees = 0
    regressions = []
    fixes = []
    still_broken = []
    skipped = []
    no_v6_match = []

    # Detailed results for the 18 incorrect + 3 null
    detailed_incorrect = []
    detailed_null = []

    feedback = feedback_data.get('feedback', {})

    for key, entry in feedback.items():
        parsed = parse_feedback_key(key)
        if not parsed:
            continue

        verdict = entry.get('verdict')
        note = entry.get('note', '')
        v5_cls = v5_lookup.get(key, 'UNKNOWN')

        # Determine what Jeff wanted
        jeff_want = jeff_wanted_story(key, verdict, note, v5_cls)

        if jeff_want == 'SKIP':
            skipped.append(key)
            continue

        total += 1

        # Find v6 match
        v6_match = find_v6_match(key, parsed, v6_lookup)

        if v6_match is None:
            # v6 didn't find any story at these segments
            v6_cls = 'NOT_A_STORY'
            v6_label = 'NOT_A_STORY (no match)'
        else:
            v6_cls = v6_match['classification']
            match_type = v6_match.get('match_type', 'exact')
            merged = f" [merged into {v6_match['merged_into']}]" if v6_match.get('merged_into') else ""
            v6_label = f"{v6_cls} ({match_type}){merged}"

        # Compare v6 against Jeff's ground truth
        v6_is_story = is_story_positive(v6_cls)
        v6_agrees = (jeff_want == 'STORY' and v6_is_story) or (jeff_want == 'NOT_A_STORY' and not v6_is_story)

        if v6_agrees:
            agrees += 1

        if verdict == 'correct':
            # Was correct in v5.1 — regression if v6 now wrong
            if not v6_agrees:
                regressions.append({
                    'key': key,
                    'v5_cls': v5_cls,
                    'v6_cls': v6_label,
                    'jeff_want': jeff_want,
                    'note': note,
                })

        elif verdict == 'incorrect':
            # Was wrong in v5.1 — fix if v6 now correct
            detail = {
                'key': key,
                'v5_cls': v5_cls,
                'v6_cls': v6_label,
                'jeff_want': jeff_want,
                'note': note[:80] if note else '',
                'fixed': v6_agrees,
            }
            detailed_incorrect.append(detail)
            if v6_agrees:
                fixes.append(detail)
            else:
                still_broken.append(detail)

        elif verdict is None:
            detail = {
                'key': key,
                'v5_cls': v5_cls,
                'v6_cls': v6_label,
                'jeff_want': jeff_want,
                'note': note[:80] if note else '',
                'fixed': v6_agrees,
            }
            detailed_null.append(detail)
            if not v6_agrees:
                still_broken.append(detail)
            else:
                fixes.append(detail)

    # --- Scorecard ---

    print("=" * 65)
    print("  V6 REGRESSION TEST AGAINST JEFF'S 128 ANSWERS")
    print("=" * 65)

    print(f"\nOVERALL:")
    print(f"  Total entries tested:           {total}")
    print(f"  Skipped (null, no note):        {len(skipped)}")
    print(f"  v6 agrees with Jeff:            {agrees}/{total} ({100*agrees/total:.1f}%)")
    print(f"  Regressions (was correct, now wrong): {len(regressions)}")
    print(f"  Fixes (was wrong, now correct):       {len(fixes)}/{len(detailed_incorrect)+len(detailed_null)}")
    print(f"  Still broken:                         {len(still_broken)}/{len(detailed_incorrect)+len(detailed_null)}")

    net_change = len(fixes) - len(regressions)
    print(f"\n  Net improvement: {'+' if net_change >= 0 else ''}{net_change} entries")

    # Detailed: The 18 incorrect entries
    print(f"\n{'─' * 65}")
    print(f"DETAILED: Jeff's 'incorrect' entries ({len(detailed_incorrect)} bugs v6 aimed to fix)")
    print(f"{'─' * 65}")
    for d in detailed_incorrect:
        status = "FIX" if d['fixed'] else "STILL_BROKEN"
        arrow = "should be" if not d['fixed'] else "now"
        print(f"  {d['key']}: v5.1={d['v5_cls']} -> Jeff wants {d['jeff_want']} -> v6={d['v6_cls']}  [{status}]")
        if d['note']:
            print(f"    Jeff: \"{d['note']}\"")

    # Detailed: The null-with-notes entries
    if detailed_null:
        print(f"\n{'─' * 65}")
        print(f"DETAILED: Jeff's null-with-notes entries ({len(detailed_null)})")
        print(f"{'─' * 65}")
        for d in detailed_null:
            status = "FIX" if d['fixed'] else "STILL_BROKEN"
            print(f"  {d['key']}: v5.1={d['v5_cls']} -> Jeff wants {d['jeff_want']} -> v6={d['v6_cls']}  [{status}]")
            if d['note']:
                print(f"    Jeff: \"{d['note']}\"")

    # Regressions
    if regressions:
        print(f"\n{'─' * 65}")
        print(f"REGRESSIONS ({len(regressions)} entries Jeff marked correct in v5.1 that v6 now gets wrong)")
        print(f"{'─' * 65}")
        for r in regressions:
            print(f"  {r['key']}: v5.1={r['v5_cls']} (Jeff=correct) -> v6={r['v6_cls']} -> Jeff wants {r['jeff_want']}")
            if r['note']:
                print(f"    Jeff: \"{r['note'][:80]}\"")
    else:
        print(f"\n  No regressions detected.")

    print(f"\n{'=' * 65}")

    # Return exit code: 0 if no regressions and all 18 fixed
    if regressions or still_broken:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(run_regression_test())
