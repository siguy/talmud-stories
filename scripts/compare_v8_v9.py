#!/usr/bin/env python3
"""
Side-by-side metric comparison: v8 (Wave 2) vs v9 (Wave 3) on both
tractates, vs canonical golden datasets.
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent


def score(detected, golden, out):
    cmd = ['python3', str(ROOT / 'scripts' / 'evaluate_golden.py'),
           '--detected'] + [str(p) for p in detected] + [
           '--golden', str(golden), '--output', str(out), '--quiet']
    subprocess.run(cmd, check=True,
                   env={'PYTHONPATH': str(ROOT),
                        'PATH': '/usr/bin:/usr/local/bin:/opt/homebrew/bin'})
    return json.load(open(out))


def fmt(metric):
    return f"{metric:.4f}" if isinstance(metric, (int, float)) else str(metric)


def row(label, w2, w3):
    delta = w3 - w2
    arrow = '↑' if delta > 0 else ('↓' if delta < 0 else '·')
    print(f"  {label:20s}  v8 {fmt(w2)}  →  v9 {fmt(w3)}  ({arrow} {delta:+.4f})")


def compare(tractate, v8, v9, golden):
    print(f"\n=== {tractate} ===")
    s8 = score(v8, golden, Path(f'/tmp/cmp_{tractate.lower()}_v8.json'))
    s9 = score(v9, golden, Path(f'/tmp/cmp_{tractate.lower()}_v9.json'))
    row('Classification F1', s8['classification']['f1'], s9['classification']['f1'])
    row('  precision',       s8['classification']['precision'], s9['classification']['precision'])
    row('  recall',          s8['classification']['recall'], s9['classification']['recall'])
    row('  FP count',        s8['classification']['fp'], s9['classification']['fp'])
    row('  FN count',        s8['classification']['fn'], s9['classification']['fn'])
    row('Boundary IoU',      s8['boundary']['mean_iou'], s9['boundary']['mean_iou'])
    row('Merge F1',          s8['merge']['f1'], s9['merge']['f1'])
    row('Composite',         s8['composite'], s9['composite'])


def main():
    compare('Kiddushin',
            [ROOT / 'results' / 'v8' / 'wave2' / 'kiddushin_v8.json'],
            [ROOT / 'results' / 'v9' / 'wave3' / 'kiddushin_v9.json'],
            ROOT / 'results' / 'canonical' / 'kiddushin_canonical.json')
    compare('Ketubot',
            [ROOT / 'results' / 'v8' / 'wave2' / 'ketubot_v8_2-60.json',
             ROOT / 'results' / 'v8' / 'wave2' / 'ketubot_v8_61-112.json'],
            [ROOT / 'results' / 'v9' / 'wave3' / 'ketubot_v9_2-60.json',
             ROOT / 'results' / 'v9' / 'wave3' / 'ketubot_v9_61-112.json'],
            ROOT / 'results' / 'canonical' / 'ketubot_canonical.json')


if __name__ == '__main__':
    main()
