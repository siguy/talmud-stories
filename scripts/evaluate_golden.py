#!/usr/bin/env python3
"""
Evaluate Detection Results Against the Golden Dataset.

IMMUTABLE after creation — do not modify this file during autoresearch.

Scores detection results against Jeff Rubenstein's golden Ketubot labels using:
  1. Classification F1: story vs. not-story binary classification
  2. Boundary IoU: segment overlap for correctly-classified stories
  3. Merge Accuracy: cross-page merge detection precision/recall
  4. Composite Score: 0.4 * F1 + 0.4 * IoU + 0.2 * merge

Usage:
  python3 scripts/evaluate_golden.py [--detected PATH] [--golden PATH]

  Defaults:
    --detected: results from running detector on all Ketubot pages
    --golden: results/canonical/ketubot_canonical.json

Output: JSON with all subscores, composite, and per-story details.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

DEFAULT_GOLDEN = PROJECT_ROOT / 'results' / 'canonical' / 'ketubot_canonical.json'
DEFAULT_DETECTED_V7 = PROJECT_ROOT / 'results' / 'v7' / 'ketubot_v7_2-60.json'
DEFAULT_DETECTED_V9 = PROJECT_ROOT / 'results' / 'v7' / 'ketubot_v9_61-112.json'


# ========== Data Loading ==========

def load_golden(path):
    """Load golden dataset and extract story labels per page."""
    with open(path) as f:
        data = json.load(f)

    golden = {}  # {page_ref: [story_dict, ...]}
    for page in data.get('pages', []):
        ref = page['ref']
        stories = []
        for s in page.get('stories', []):
            cls = s.get('classification', '')
            # Binary: is_story if not NOT_A_STORY
            is_story = cls not in ('NOT_A_STORY', 'NEEDS_REVIEW')
            stories.append({
                'start': s['start_segment'],
                'end': s['end_segment'],
                'classification': cls,
                'is_story': is_story,
                'spans_pages': s.get('spans_pages'),
                'p2_start': s.get('start_segment_page2'),
                'p2_end': s.get('end_segment_page2'),
            })
        golden[ref] = stories
    return golden


def load_detected(paths):
    """Load detected results (v7 + v9 or single file)."""
    detected = {}
    for path in paths:
        with open(path) as f:
            data = json.load(f)
        for page in data.get('pages', []):
            ref = page['ref']
            stories = []
            for s in page.get('stories', []):
                cls = s.get('classification', '')
                is_story = cls not in ('NOT_A_STORY', 'NEEDS_REVIEW')
                stories.append({
                    'start': s['start_segment'],
                    'end': s['end_segment'],
                    'classification': cls,
                    'is_story': is_story,
                    'spans_pages': s.get('spans_pages'),
                    'p2_start': s.get('start_segment_page2'),
                    'p2_end': s.get('end_segment_page2'),
                })
            detected[ref] = stories
    return detected


# ========== Matching ==========

def segment_overlap(s1_start, s1_end, s2_start, s2_end):
    """Compute overlap between two segment ranges."""
    intersection = max(0, min(s1_end, s2_end) - max(s1_start, s2_start) + 1)
    return intersection


def segment_iou(s1_start, s1_end, s2_start, s2_end):
    """Compute Intersection over Union for two segment ranges."""
    intersection = max(0, min(s1_end, s2_end) - max(s1_start, s2_start) + 1)
    union = (s1_end - s1_start + 1) + (s2_end - s2_start + 1) - intersection
    return intersection / union if union > 0 else 0.0


def match_stories(golden_stories, detected_stories, iou_threshold=0.3):
    """
    Match golden stories to detected stories using IoU.

    Returns list of (golden_story, detected_story_or_None, iou) tuples.
    """
    used_detected = set()
    matches = []

    for g in golden_stories:
        best_d = None
        best_iou = 0

        for j, d in enumerate(detected_stories):
            if j in used_detected:
                continue
            iou = segment_iou(g['start'], g['end'], d['start'], d['end'])
            if iou > best_iou:
                best_iou = iou
                best_d = (j, d)

        if best_d and best_iou >= iou_threshold:
            used_detected.add(best_d[0])
            matches.append((g, best_d[1], best_iou))
        else:
            matches.append((g, None, 0.0))

    # Unmatched detected stories (false positives)
    unmatched_detected = [
        detected_stories[j] for j in range(len(detected_stories))
        if j not in used_detected
    ]

    return matches, unmatched_detected


# ========== Scoring ==========

def compute_classification_scores(golden, detected):
    """
    Compute classification F1 (story vs. not-story).

    For each page: match golden stories to detected stories.
    True positive: golden is_story AND matched detected is_story
    False positive: detected is_story with no golden match
    False negative: golden is_story with no detected match
    """
    tp = 0
    fp = 0
    fn = 0
    tn = 0
    per_story = []

    for page_ref in golden:
        g_stories = golden[page_ref]
        d_stories = detected.get(page_ref, [])

        matches, unmatched_d = match_stories(g_stories, d_stories)

        for g, d, iou in matches:
            if g['is_story']:
                if d and d['is_story']:
                    tp += 1
                    per_story.append({
                        'page': page_ref,
                        'golden': f"{g['start']}-{g['end']}",
                        'detected': f"{d['start']}-{d['end']}",
                        'iou': round(iou, 3),
                        'result': 'TP',
                    })
                else:
                    fn += 1
                    per_story.append({
                        'page': page_ref,
                        'golden': f"{g['start']}-{g['end']}",
                        'detected': f"{d['start']}-{d['end']}" if d else None,
                        'iou': round(iou, 3),
                        'result': 'FN',
                        'reason': 'not detected' if not d else 'classified as not-story',
                    })
            else:
                # Golden says NOT_A_STORY
                if d and d['is_story']:
                    fp += 1
                    per_story.append({
                        'page': page_ref,
                        'golden': f"{g['start']}-{g['end']}",
                        'detected': f"{d['start']}-{d['end']}",
                        'iou': round(iou, 3),
                        'result': 'FP',
                        'reason': 'golden says NOT_A_STORY',
                    })
                else:
                    tn += 1

        # Unmatched detected stories count as false positives
        for d in unmatched_d:
            if d['is_story']:
                fp += 1
                per_story.append({
                    'page': page_ref,
                    'detected': f"{d['start']}-{d['end']}",
                    'result': 'FP',
                    'reason': 'no golden match',
                })

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'f1': round(f1, 4),
        'tp': tp,
        'fp': fp,
        'fn': fn,
        'tn': tn,
    }, per_story


def compute_boundary_iou(golden, detected):
    """
    Compute mean Boundary IoU for correctly-classified (TP) stories.
    """
    ious = []

    for page_ref in golden:
        g_stories = [g for g in golden[page_ref] if g['is_story']]
        d_stories = detected.get(page_ref, [])

        matches, _ = match_stories(g_stories, d_stories)

        for g, d, iou in matches:
            if d and d['is_story'] and iou > 0:
                ious.append(iou)

    if not ious:
        return {
            'mean_iou': 0,
            'median_iou': 0,
            'pct_above_0.8': 0,
            'count': 0,
        }

    ious_sorted = sorted(ious)
    median = ious_sorted[len(ious_sorted) // 2]
    above_80 = sum(1 for x in ious if x >= 0.8) / len(ious)

    return {
        'mean_iou': round(sum(ious) / len(ious), 4),
        'median_iou': round(median, 4),
        'pct_above_0.8': round(above_80, 4),
        'count': len(ious),
    }


def compute_merge_accuracy(golden, detected):
    """
    Compute precision/recall for cross-page merge detection.
    """
    golden_merges = set()
    detected_merges = set()

    for page_ref, stories in golden.items():
        for s in stories:
            if s.get('spans_pages'):
                golden_merges.add((page_ref, s['start'], s['end']))

    for page_ref, stories in detected.items():
        for s in stories:
            if s.get('spans_pages'):
                detected_merges.add((page_ref, s['start'], s['end']))

    # Match merges by page + overlap
    tp = 0
    for gm in golden_merges:
        g_ref, g_start, g_end = gm
        for dm in detected_merges:
            d_ref, d_start, d_end = dm
            if g_ref == d_ref and segment_overlap(g_start, g_end, d_start, d_end) > 0:
                tp += 1
                break

    precision = tp / len(detected_merges) if detected_merges else 0
    recall = tp / len(golden_merges) if golden_merges else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'f1': round(f1, 4),
        'golden_merges': len(golden_merges),
        'detected_merges': len(detected_merges),
        'matched': tp,
    }


def evaluate(detected, golden):
    """
    Full evaluation: classification F1, boundary IoU, merge accuracy, composite.
    """
    cls_scores, per_story = compute_classification_scores(golden, detected)
    boundary_scores = compute_boundary_iou(golden, detected)
    merge_scores = compute_merge_accuracy(golden, detected)

    composite = (
        0.4 * cls_scores['f1'] +
        0.4 * boundary_scores['mean_iou'] +
        0.2 * merge_scores['f1']
    )

    return {
        'classification': cls_scores,
        'boundary': boundary_scores,
        'merge': merge_scores,
        'composite': round(composite, 4),
        'per_story': per_story,
    }


# ========== Main ==========

def main():
    parser = argparse.ArgumentParser(description='Evaluate detection against golden dataset')
    parser.add_argument('--detected', nargs='+',
                        help='Path(s) to detected results JSON')
    parser.add_argument('--golden', default=str(DEFAULT_GOLDEN),
                        help='Path to golden dataset JSON')
    parser.add_argument('--output', help='Output path for results JSON')
    parser.add_argument('--quiet', action='store_true', help='Suppress terminal output')
    args = parser.parse_args()

    # Load data
    golden = load_golden(args.golden)

    detected_paths = args.detected
    if not detected_paths:
        detected_paths = [str(DEFAULT_DETECTED_V7), str(DEFAULT_DETECTED_V9)]
    detected = load_detected([Path(p) for p in detected_paths])

    # Evaluate
    results = evaluate(detected, golden)

    # Print summary
    if not args.quiet:
        print("=" * 60)
        print("  EVALUATION RESULTS")
        print("=" * 60)
        print(f"\n  Classification:")
        print(f"    Precision: {results['classification']['precision']}")
        print(f"    Recall:    {results['classification']['recall']}")
        print(f"    F1:        {results['classification']['f1']}")
        print(f"    TP={results['classification']['tp']} "
              f"FP={results['classification']['fp']} "
              f"FN={results['classification']['fn']} "
              f"TN={results['classification']['tn']}")

        print(f"\n  Boundary IoU:")
        print(f"    Mean:      {results['boundary']['mean_iou']}")
        print(f"    Median:    {results['boundary']['median_iou']}")
        print(f"    >0.8:      {results['boundary']['pct_above_0.8']} ({results['boundary']['count']} stories)")

        print(f"\n  Merge Accuracy:")
        print(f"    Precision: {results['merge']['precision']}")
        print(f"    Recall:    {results['merge']['recall']}")
        print(f"    F1:        {results['merge']['f1']}")
        print(f"    Golden: {results['merge']['golden_merges']} "
              f"Detected: {results['merge']['detected_merges']} "
              f"Matched: {results['merge']['matched']}")

        print(f"\n  COMPOSITE SCORE: {results['composite']}")

        # Show false negatives (missed stories)
        fns = [s for s in results['per_story'] if s['result'] == 'FN']
        if fns:
            print(f"\n  False Negatives ({len(fns)} missed stories):")
            for fn in fns[:10]:
                print(f"    {fn['page']} seg {fn['golden']}: {fn.get('reason', '')}")

        # Show false positives
        fps = [s for s in results['per_story'] if s['result'] == 'FP']
        if fps:
            print(f"\n  False Positives ({len(fps)} extra detections):")
            for fp in fps[:10]:
                page = fp.get('page', '?')
                det = fp.get('detected', '?')
                print(f"    {page} seg {det}: {fp.get('reason', '')}")

    # Save output
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = PROJECT_ROOT / 'docs' / 'golden' / 'baseline_ketubot.json'

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove per-story from saved output (too large), keep just summary
    save_results = {k: v for k, v in results.items() if k != 'per_story'}
    save_results['per_story_count'] = len(results['per_story'])

    with open(output_path, 'w') as f:
        json.dump(save_results, f, indent=2)

    if not args.quiet:
        print(f"\n  Saved to: {output_path}")

    return results


if __name__ == '__main__':
    main()
