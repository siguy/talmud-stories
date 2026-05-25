#!/usr/bin/env python3
"""
Compare v8 Wave 1 vs Wave 2 scores on both tractates.

Scores both wave outputs against their respective golden datasets and
prints a per-metric delta table. Exits 0 if both tractates pass the
"composite >= wave1" gate, 1 otherwise.

Per Lesson 11, do not compare against historical frozen baselines —
both wave1 and wave2 are scored fresh in the same run.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
EVAL = ROOT / 'scripts' / 'evaluate_golden.py'

KID_GOLD = ROOT / 'results' / 'canonical' / 'kiddushin_canonical.json'
KET_GOLD = ROOT / 'results' / 'canonical' / 'ketubot_canonical.json'

WAVES = {
    'wave1': ROOT / 'results' / 'v8' / 'wave1',
    'wave2': ROOT / 'results' / 'v8' / 'wave2',
}

RUNS = [
    ('Kiddushin', KID_GOLD, ['kiddushin_v8.json']),
    ('Ketubot',   KET_GOLD, ['ketubot_v8_2-60.json', 'ketubot_v8_61-112.json']),
]


def score(detected_paths, golden):
    subprocess.run(
        ['python3', str(EVAL),
         '--detected', *[str(p) for p in detected_paths],
         '--golden', str(golden),
         '--output', '/tmp/_cmp_score.json', '--quiet'],
        check=True, capture_output=True)
    return json.load(open('/tmp/_cmp_score.json'))


def main():
    results = {}
    for tract, golden, fnames in RUNS:
        results[tract] = {}
        for wave_name, wave_dir in WAVES.items():
            paths = [wave_dir / f for f in fnames]
            results[tract][wave_name] = score(paths, golden)

    print('=' * 78)
    print('  Wave 1 vs Wave 2 — fresh today against current canonical')
    print('=' * 78)
    all_pass = True
    for tract in results:
        w1, w2 = results[tract]['wave1'], results[tract]['wave2']
        c1, c2 = w1['composite'], w2['composite']
        delta = c2 - c1
        gate = '✓' if c2 >= c1 else '✗'
        if c2 < c1:
            all_pass = False
        print(f'\n  {tract}')
        print(f'    {"Metric":18} {"Wave 1":>10} {"Wave 2":>10} {"Δ":>10}')
        print(f'    {"-"*18} {"-"*10} {"-"*10} {"-"*10}')
        for label, key in [('Classification F1', ('classification', 'f1')),
                           ('Boundary mean IoU', ('boundary', 'mean_iou')),
                           ('Merge F1',          ('merge', 'f1'))]:
            v1 = w1[key[0]][key[1]]
            v2 = w2[key[0]][key[1]]
            print(f'    {label:18} {v1:10.4f} {v2:10.4f} {v2-v1:+10.4f}')
        print(f'    {"COMPOSITE":18} {c1:10.4f} {c2:10.4f} {delta:+10.4f}  {gate}')

    print('\n' + '=' * 78)
    print(f'  Gate (both composites >= wave1): {"PASS" if all_pass else "FAIL"}')
    print('=' * 78)
    sys.exit(0 if all_pass else 1)


if __name__ == '__main__':
    main()
