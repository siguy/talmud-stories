#!/usr/bin/env python3
"""
Run a single autoresearch experiment.

1. Run the current detector on all Ketubot pages
2. Evaluate against the golden dataset
3. Compare to previous best score
4. Print result and exit with code 0 (improved) or 1 (not improved)

Usage:
  python3 scripts/autoresearch/run_experiment.py [--skip-detect]

  --skip-detect: Skip running detector, just re-evaluate existing results
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

GOLDEN_PATH = PROJECT_ROOT / 'results' / 'canonical' / 'ketubot_canonical.json'
BASELINE_PATH = PROJECT_ROOT / 'docs' / 'golden' / 'baseline_ketubot.json'
BEST_SCORE_PATH = PROJECT_ROOT / 'docs' / 'golden' / 'best_experiment_score.json'

# Detection result paths
DETECTED_V7 = PROJECT_ROOT / 'results' / 'v7' / 'ketubot_v7_2-60.json'
DETECTED_V9 = PROJECT_ROOT / 'results' / 'v7' / 'ketubot_v9_61-112.json'

# Import evaluate
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
from evaluate_golden import load_golden, load_detected, evaluate


def load_best_score():
    """Load the best score so far, defaulting to baseline."""
    if BEST_SCORE_PATH.exists():
        with open(BEST_SCORE_PATH) as f:
            return json.load(f)
    if BASELINE_PATH.exists():
        with open(BASELINE_PATH) as f:
            return json.load(f)
    return {'composite': 0}


def save_best_score(results):
    """Save new best score."""
    save = {k: v for k, v in results.items() if k != 'per_story'}
    with open(BEST_SCORE_PATH, 'w') as f:
        json.dump(save, f, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-detect', action='store_true',
                        help='Skip running detector')
    args = parser.parse_args()

    print("=" * 60)
    print("  AUTORESEARCH EXPERIMENT")
    print("=" * 60)

    # Step 1: Run detector (if not skipping)
    if not args.skip_detect:
        print("\n--- Running detector on Ketubot pages ---")
        print("  (This step requires running the detector scripts)")
        print("  TODO: Implement detector run automation")
        print("  For now, use --skip-detect and run detector manually first")
        # Future: subprocess.run(['python3', 'scripts/run_ketubot_2_60.py'])
        # Future: subprocess.run(['python3', 'scripts/run_ketubot_61_112.py'])

    # Step 2: Evaluate
    print("\n--- Evaluating against golden dataset ---")
    golden = load_golden(str(GOLDEN_PATH))
    detected = load_detected([DETECTED_V7, DETECTED_V9])
    results = evaluate(detected, golden)

    # Step 3: Compare to best
    best = load_best_score()
    best_composite = best.get('composite', 0)
    current_composite = results['composite']
    improvement = current_composite - best_composite

    print(f"\n{'=' * 60}")
    print(f"  RESULTS")
    print(f"{'=' * 60}")
    print(f"  Current composite: {current_composite}")
    print(f"  Best composite:    {best_composite}")
    print(f"  Improvement:       {improvement:+.4f}")
    print(f"\n  Classification F1: {results['classification']['f1']}")
    print(f"  Boundary IoU:      {results['boundary']['mean_iou']}")
    print(f"  Merge F1:          {results['merge']['f1']}")

    # Check constraints
    if results['classification']['f1'] < 0.85:
        print("\n  ⚠ CONSTRAINT VIOLATION: Classification F1 below 0.85!")
        print("  Recommendation: REVERT this change")
        sys.exit(2)

    if current_composite < 0.90:
        print("\n  ⚠ CONSTRAINT VIOLATION: Composite below 0.90!")
        print("  Recommendation: REVERT this change")
        sys.exit(2)

    if improvement > 0:
        print(f"\n  ✓ IMPROVED by {improvement:+.4f}")
        save_best_score(results)
        print(f"  Saved new best score to {BEST_SCORE_PATH}")
        sys.exit(0)
    elif improvement == 0:
        print("\n  = NO CHANGE")
        sys.exit(1)
    else:
        print(f"\n  ✗ REGRESSION by {improvement:.4f}")
        print("  Recommendation: REVERT this change")
        sys.exit(1)


if __name__ == '__main__':
    main()
