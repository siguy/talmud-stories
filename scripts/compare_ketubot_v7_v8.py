#!/usr/bin/env python3
"""
Compare v8 vs v7 on Ketubot golden dataset.

Runs `scripts/evaluate_golden.py` programmatically against both versions and
reports the deltas. PASS criterion: v8 composite >= v7 composite (no regression).
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
EVAL = ROOT / 'scripts' / 'evaluate_golden.py'
GOLDEN = ROOT / 'results' / 'canonical' / 'ketubot_canonical.json'

# Use v7_fresh as the baseline, not the historical v7 file. The historical
# baseline scored 0.93 against canonical labels but is not reproducible today —
# Gemini output has drifted (Lesson 11). For a fair Wave 1 regression check we
# must compare two runs taken on the same day in the same model conditions.
V7_2_60 = ROOT / 'results' / 'v7_fresh' / 'ketubot_v7_2-60.json'
V7_61_112 = ROOT / 'results' / 'v7_fresh' / 'ketubot_v7_61-112.json'
V8_2_60 = ROOT / 'results' / 'v8' / 'ketubot_v8_2-60.json'
V8_61_112 = ROOT / 'results' / 'v8' / 'ketubot_v8_61-112.json'


def run_eval(detected_a, detected_b, label):
    """Invoke evaluate_golden.py and capture the printed composite + subscores."""
    cmd = [
        sys.executable, str(EVAL),
        '--detected', str(detected_a), str(detected_b),
        '--golden', str(GOLDEN),
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return out.stdout


def load_saved_baseline():
    p = ROOT / 'docs' / 'golden' / 'baseline_ketubot.json'
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return None


def parse_scores(text):
    """Extract numeric subscores from evaluate_golden output text."""
    import re
    fields = {}
    patterns = {
        'precision': r'Precision:\s+([0-9.]+)',
        'recall': r'Recall:\s+([0-9.]+)',
        'f1': r'F1:\s+([0-9.]+)',
        'iou_mean': r'Mean:\s+([0-9.]+)',
        'iou_above_0.8': r'>0\.8:\s+([0-9.]+)',
        'merge_f1': r'Merge Accuracy:[\s\S]*?F1:\s+([0-9.]+)',
        'composite': r'COMPOSITE SCORE:\s+([0-9.]+)',
    }
    for k, pat in patterns.items():
        m = re.search(pat, text)
        if m:
            fields[k] = float(m.group(1))
    return fields


def main():
    print('=' * 70)
    print('  Ketubot Wave 1 regression check: v7 baseline vs v8')
    print('=' * 70)

    print('\n--- v7 baseline ---')
    v7_text = run_eval(V7_2_60, V7_61_112, 'v7')
    v7 = parse_scores(v7_text)
    print(f"  Composite: {v7.get('composite')}")
    print(f"  F1: {v7.get('f1')}  IoU mean: {v7.get('iou_mean')}  Merge F1: {v7.get('merge_f1')}")

    print('\n--- v8 (Wave 1 fixes) ---')
    v8_text = run_eval(V8_2_60, V8_61_112, 'v8')
    v8 = parse_scores(v8_text)
    print(f"  Composite: {v8.get('composite')}")
    print(f"  F1: {v8.get('f1')}  IoU mean: {v8.get('iou_mean')}  Merge F1: {v8.get('merge_f1')}")

    print('\n--- Delta (v8 − v7) ---')
    for k in ('composite', 'f1', 'iou_mean', 'merge_f1'):
        if k in v7 and k in v8:
            d = v8[k] - v7[k]
            sign = '+' if d >= 0 else ''
            print(f"  {k}: {sign}{d:.4f}")

    pass_ = v8.get('composite', 0) >= v7.get('composite', 0)
    print('\n' + ('PASS — no Ketubot regression' if pass_
                  else 'FAIL — Ketubot regressed; do NOT commit'))
    sys.exit(0 if pass_ else 1)


if __name__ == '__main__':
    main()
