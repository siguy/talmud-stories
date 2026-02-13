#!/usr/bin/env python3
"""
V7 Regression Test: Compare v7 results against Jeff's 128 labeled answers.
Side-by-side comparison with v6.

Extends v6_regression_test.py with v7 lookup and comparison.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# --- Reuse from v6 regression test ---

def parse_feedback_key(key: str) -> dict:
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
    page = page_ref.replace('Ketubot ', '')
    return f'Ketubot {page}_{start_seg}-{end_seg}'


def is_story_positive(cls: str) -> bool:
    return cls in ('YES', 'HIGH_CONFIDENCE', 'LOW_CONFIDENCE')


def jeff_wanted_story(verdict, note, v5_cls) -> str:
    if verdict == 'correct':
        return 'STORY' if is_story_positive(v5_cls) else 'NOT_A_STORY'
    elif verdict == 'incorrect':
        return 'NOT_A_STORY' if is_story_positive(v5_cls) else 'STORY'
    elif verdict is None:
        note_lower = (note or '').lower()
        if 'definitely a story' in note_lower or 'high confidence story' in note_lower:
            return 'STORY'
        return 'SKIP'
    return 'SKIP'


# --- Build lookup for any version ---

def build_version_lookup(data: dict) -> dict:
    """Build lookup from feedback key -> classification info."""
    lookup = {}
    for page in data.get('pages', []):
        ref = page.get('ref', '')
        for story in page.get('stories', []):
            cls = story.get('classification', 'UNKNOWN')
            key = make_story_key(ref, story['start_segment'], story['end_segment'])
            lookup[key] = {
                'classification': cls,
                'start_segment': story['start_segment'],
                'end_segment': story['end_segment'],
                'page_ref': ref,
                'spans_pages': story.get('spans_pages'),
            }

            # Cross-page merged stories: also index by page 2
            if story.get('spans_pages') and 'start_segment_page2' in story:
                page2_ref = story['spans_pages'][1] if len(story['spans_pages']) > 1 else ref
                key2 = make_story_key(page2_ref, story['start_segment_page2'],
                                      story['end_segment_page2'])
                lookup[key2] = {
                    'classification': cls,
                    'start_segment': story['start_segment_page2'],
                    'end_segment': story['end_segment_page2'],
                    'page_ref': page2_ref,
                    'spans_pages': story['spans_pages'],
                    'merged_into': key,
                }

    return lookup


def find_match(feedback_key: str, parsed: dict, lookup: dict) -> dict:
    """Find matching story in a version's lookup. Tries exact then overlapping."""
    if feedback_key in lookup:
        return lookup[feedback_key]

    target_ref = parsed['ref']
    target_start = parsed['start_seg']
    target_end = parsed['end_seg']
    target_len = target_end - target_start + 1

    best_match = None
    best_ratio = 0

    for key, info in lookup.items():
        if info['page_ref'] != target_ref:
            continue
        v_start = info['start_segment']
        v_end = info['end_segment']
        overlap_start = max(target_start, v_start)
        overlap_end = min(target_end, v_end)
        if overlap_start <= overlap_end:
            overlap = overlap_end - overlap_start + 1
            ratio = overlap / target_len
            if ratio >= 0.5 and ratio > best_ratio:
                best_ratio = ratio
                best_match = dict(info)
                best_match['match_type'] = 'overlap'

    return best_match


def get_cls_label(match) -> str:
    """Get classification label from a match."""
    if match is None:
        return 'NOT_A_STORY (no match)'
    cls = match['classification']
    mt = match.get('match_type', 'exact')
    merged = f" [merged→{match['merged_into']}]" if match.get('merged_into') else ""
    return f"{cls} ({mt}){merged}"


# --- Main ---

def run_regression_test():
    project_root = Path(__file__).parent.parent

    # Load feedback
    feedback_path = project_root / 'validation' / 'feedback' / \
        'v5_1_feedback_anonymous_2026-02-05 (1).json'
    with open(feedback_path) as f:
        feedback_data = json.load(f)

    # Load v5.1
    v5_pages = []
    for fname in ['pages_2-39.json', 'pages_40-60.json']:
        with open(project_root / 'results' / 'ketubot' / 'v5' / fname) as f:
            v5_pages.extend(json.load(f).get('pages', []))
    v5_lookup = {}
    for page in v5_pages:
        ref = page.get('ref', '')
        for story in page.get('stories', []):
            k = make_story_key(ref, story['start_segment'], story['end_segment'])
            v5_lookup[k] = story.get('classification', 'UNKNOWN')

    # Load v6
    v6_path = project_root / 'results' / 'v6' / 'ketubot_v6_2-60.json'
    v6_lookup = {}
    if v6_path.exists():
        with open(v6_path) as f:
            v6_data = json.load(f)
        v6_lookup = build_version_lookup(v6_data)

    # Load v7
    v7_path = project_root / 'results' / 'v7' / 'ketubot_v7_2-60.json'
    if not v7_path.exists():
        print(f"ERROR: V7 results not found at {v7_path}")
        print("Run: PYTHONPATH=. python3 src/story_detector_v7.py")
        sys.exit(1)
    with open(v7_path) as f:
        v7_data = json.load(f)
    v7_lookup = build_version_lookup(v7_data)

    # Counters
    feedback = feedback_data.get('feedback', {})
    total = 0
    v6_agrees = 0
    v7_agrees = 0
    v6_regressions = []
    v7_regressions = []
    v7_fixes_from_v6 = []
    v7_regressions_from_v6 = []
    skipped = []

    # Detailed
    incorrect_details = []

    for key, entry in feedback.items():
        parsed = parse_feedback_key(key)
        if not parsed:
            continue

        verdict = entry.get('verdict')
        note = entry.get('note', '')
        v5_cls = v5_lookup.get(key, 'UNKNOWN')
        jeff_want = jeff_wanted_story(verdict, note, v5_cls)

        if jeff_want == 'SKIP':
            skipped.append(key)
            continue

        total += 1

        # V6 match
        v6_match = find_match(key, parsed, v6_lookup) if v6_lookup else None
        v6_cls = v6_match['classification'] if v6_match else 'NOT_A_STORY'
        v6_is_story = is_story_positive(v6_cls)
        v6_ok = (jeff_want == 'STORY' and v6_is_story) or \
                (jeff_want == 'NOT_A_STORY' and not v6_is_story)
        if v6_ok:
            v6_agrees += 1

        # V7 match
        v7_match = find_match(key, parsed, v7_lookup)
        v7_cls = v7_match['classification'] if v7_match else 'NOT_A_STORY'
        v7_is_story = is_story_positive(v7_cls)
        v7_ok = (jeff_want == 'STORY' and v7_is_story) or \
                (jeff_want == 'NOT_A_STORY' and not v7_is_story)
        if v7_ok:
            v7_agrees += 1

        # Track regressions from v5→v7
        if verdict == 'correct' and not v7_ok:
            v7_regressions.append({
                'key': key, 'v5_cls': v5_cls,
                'v7_cls': get_cls_label(v7_match),
                'jeff_want': jeff_want, 'note': note[:80],
            })

        # Track v6→v7 changes
        if v6_ok and not v7_ok:
            v7_regressions_from_v6.append({
                'key': key, 'v6_cls': get_cls_label(v6_match),
                'v7_cls': get_cls_label(v7_match),
                'jeff_want': jeff_want, 'note': note[:80],
            })
        if not v6_ok and v7_ok:
            v7_fixes_from_v6.append({
                'key': key, 'v6_cls': get_cls_label(v6_match),
                'v7_cls': get_cls_label(v7_match),
                'jeff_want': jeff_want, 'note': note[:80],
            })

        # Track incorrect entries
        if verdict in ('incorrect', None):
            incorrect_details.append({
                'key': key, 'verdict': verdict, 'v5_cls': v5_cls,
                'v6_cls': get_cls_label(v6_match),
                'v7_cls': get_cls_label(v7_match),
                'jeff_want': jeff_want, 'note': note[:80],
                'v6_ok': v6_ok, 'v7_ok': v7_ok,
            })

    # --- Scorecard ---
    print("=" * 70)
    print("  V7 REGRESSION TEST — SIDE-BY-SIDE WITH V6")
    print("=" * 70)

    print(f"\nOVERALL ({total} entries, {len(skipped)} skipped):")
    if v6_lookup:
        print(f"  v6 agrees with Jeff: {v6_agrees}/{total} ({100*v6_agrees/total:.1f}%)")
    print(f"  v7 agrees with Jeff: {v7_agrees}/{total} ({100*v7_agrees/total:.1f}%)")
    net = v7_agrees - v6_agrees if v6_lookup else 0
    print(f"  Net change v6→v7:    {'+' if net >= 0 else ''}{net}")

    print(f"\nv7 REGRESSIONS FROM v5.1 (was correct, now wrong): {len(v7_regressions)}")
    for r in v7_regressions:
        print(f"  {r['key']}: v5.1={r['v5_cls']} → v7={r['v7_cls']} (Jeff wants {r['jeff_want']})")
        if r['note']:
            print(f"    Jeff: \"{r['note']}\"")

    if v6_lookup:
        print(f"\nv6→v7 FIXES (v6 wrong, v7 correct): {len(v7_fixes_from_v6)}")
        for f in v7_fixes_from_v6:
            print(f"  {f['key']}: v6={f['v6_cls']} → v7={f['v7_cls']} (Jeff wants {f['jeff_want']})")

        print(f"\nv6→v7 REGRESSIONS (v6 correct, v7 wrong): {len(v7_regressions_from_v6)}")
        for r in v7_regressions_from_v6:
            print(f"  {r['key']}: v6={r['v6_cls']} → v7={r['v7_cls']} (Jeff wants {r['jeff_want']})")
            if r['note']:
                print(f"    Jeff: \"{r['note']}\"")

    # Detailed incorrect entries
    print(f"\n{'─' * 70}")
    print(f"DETAILED: Jeff's incorrect/null entries")
    print(f"{'─' * 70}")
    for d in sorted(incorrect_details, key=lambda x: x['key']):
        v6_status = "v6=OK" if d['v6_ok'] else "v6=WRONG"
        v7_status = "v7=OK" if d['v7_ok'] else "v7=WRONG"
        print(f"  {d['key']}: Jeff wants {d['jeff_want']}")
        print(f"    v5.1={d['v5_cls']} | v6={d['v6_cls']} | v7={d['v7_cls']} [{v6_status}, {v7_status}]")
        if d['note']:
            print(f"    Jeff: \"{d['note']}\"")

    # Triage info
    triage_summary = v7_data.get('triage_summary', {})
    if triage_summary:
        print(f"\n{'─' * 70}")
        print(f"TRIAGE SUMMARY:")
        print(f"  Pages: {triage_summary.get('total_pages', '?')} total, "
              f"{triage_summary.get('skipped', '?')} skipped, "
              f"{triage_summary.get('kept', '?')} kept "
              f"({triage_summary.get('skip_rate', '?')})")

    print(f"\n{'=' * 70}")

    return 1 if v7_regressions else 0


if __name__ == '__main__':
    sys.exit(run_regression_test())
