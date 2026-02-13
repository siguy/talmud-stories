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

def run_regression_test(v7_results_path=None, label="v7"):
    """
    Run regression test comparing results against Jeff's 128 labels.

    Args:
        v7_results_path: Path to results JSON to score (default: results/v7/ketubot_v7_2-60.json)
        label: Label for the results in output (e.g. "v7", "v7+pp", "ablation_A")
    """
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

    # Load v7 (or specified results)
    v7_path = Path(v7_results_path) if v7_results_path else \
        project_root / 'results' / 'v7' / 'ketubot_v7_2-60.json'
    if not v7_path.exists():
        print(f"ERROR: Results not found at {v7_path}")
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
    print(f"  {label.upper()} REGRESSION TEST — SIDE-BY-SIDE WITH V6")
    print("=" * 70)

    print(f"\nOVERALL ({total} entries, {len(skipped)} skipped):")
    if v6_lookup:
        print(f"  v6 agrees with Jeff: {v6_agrees}/{total} ({100*v6_agrees/total:.1f}%)")
    print(f"  {label} agrees with Jeff: {v7_agrees}/{total} ({100*v7_agrees/total:.1f}%)")
    net = v7_agrees - v6_agrees if v6_lookup else 0
    print(f"  Net change v6→{label}:    {'+' if net >= 0 else ''}{net}")

    print(f"\n{label} REGRESSIONS FROM v5.1 (was correct, now wrong): {len(v7_regressions)}")
    for r in v7_regressions:
        print(f"  {r['key']}: v5.1={r['v5_cls']} → {label}={r['v7_cls']} (Jeff wants {r['jeff_want']})")
        if r['note']:
            print(f"    Jeff: \"{r['note']}\"")

    if v6_lookup:
        print(f"\nv6→{label} FIXES (v6 wrong, {label} correct): {len(v7_fixes_from_v6)}")
        for f in v7_fixes_from_v6:
            print(f"  {f['key']}: v6={f['v6_cls']} → {label}={f['v7_cls']} (Jeff wants {f['jeff_want']})")

        print(f"\nv6→{label} REGRESSIONS (v6 correct, {label} wrong): {len(v7_regressions_from_v6)}")
        for r in v7_regressions_from_v6:
            print(f"  {r['key']}: v6={r['v6_cls']} → {label}={r['v7_cls']} (Jeff wants {r['jeff_want']})")
            if r['note']:
                print(f"    Jeff: \"{r['note']}\"")

    # Detailed incorrect entries
    print(f"\n{'─' * 70}")
    print(f"DETAILED: Jeff's incorrect/null entries")
    print(f"{'─' * 70}")
    for d in sorted(incorrect_details, key=lambda x: x['key']):
        v6_status = "v6=OK" if d['v6_ok'] else "v6=WRONG"
        v7_status = f"{label}=OK" if d['v7_ok'] else f"{label}=WRONG"
        print(f"  {d['key']}: Jeff wants {d['jeff_want']}")
        print(f"    v5.1={d['v5_cls']} | v6={d['v6_cls']} | {label}={d['v7_cls']} [{v6_status}, {v7_status}]")
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

    # Post-processing info
    pp_info = v7_data.get('post_processing', {})
    if pp_info:
        pp_stats = pp_info.get('stats', {})
        print(f"\n{'─' * 70}")
        print(f"POST-PROCESSING:")
        print(f"  Total demotions: {pp_stats.get('total_demotions', 0)}")
        for rule in ['rule1_single_event', 'rule2_duplicate', 'rule3_v6_ensemble']:
            rs = pp_stats.get(rule, {})
            if rs.get('demoted', 0) > 0:
                print(f"  {rule}: {rs['demoted']} demotions")
                for d in rs.get('details', []):
                    print(f"    {d}")

    print(f"\n{'=' * 70}")

    return v7_agrees, total


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='V7 Regression Test')
    parser.add_argument('--results', '-r', type=str, default=None,
                        help='Path to results JSON to score')
    parser.add_argument('--label', '-l', type=str, default='v7',
                        help='Label for the results (default: v7)')
    parser.add_argument('--post-process', '-pp', action='store_true',
                        help='Apply post-processing before scoring')
    args = parser.parse_args()

    if args.post_process and not args.results:
        # Apply post-processing to default v7 results, save to temp file
        from src.post_processing import apply_post_processing, print_stats
        project_root = Path(__file__).parent.parent
        v7_path = str(project_root / 'results' / 'v7' / 'ketubot_v7_2-60.json')
        v6_path = str(project_root / 'results' / 'v6' / 'ketubot_v6_2-60.json')
        triage_path = str(project_root / 'results' / 'v7' / 'event_triage_2-60.json')
        pp_path = str(project_root / 'results' / 'v7' / 'ketubot_v7_2-60_pp.json')

        processed, stats = apply_post_processing(v7_path, v6_path, triage_path, pp_path)
        print_stats(stats)
        print()

        args.results = pp_path
        if args.label == 'v7':
            args.label = 'v7+pp'

    agrees, total = run_regression_test(
        v7_results_path=args.results,
        label=args.label,
    )
    sys.exit(0 if agrees > 0 else 1)
