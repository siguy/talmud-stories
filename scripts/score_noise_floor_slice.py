#!/usr/bin/env python3
"""Score repeated runs over a fixed page slice: mean recall, SPREAD, span repairs.

The spread across repeats of the *same* config is the noise floor. Before 2026-09-08 this
project had never run the same code twice in one day, so every detector delta it published
was compared against a floor nobody had measured.

Reports `span_repairs` beside recall deliberately: on 2026-09-08 that count separated
three conditions (0 / 90 / 237) that recall alone read as noise, and it is free.

    python3 scripts/score_noise_floor_slice.py results/v11/noise_floor
"""
import collections
import glob
import json
import os
import statistics
import subprocess
import sys
from pathlib import Path


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else 'results/v11/noise_floor')
    page_slice = set((root / 'slice.txt').read_text().split(','))
    runs = collections.defaultdict(list)

    for path in sorted(glob.glob(str(root / '*_r?.json'))):
        config = Path(path).name.rsplit('_r', 1)[0]
        scored = Path(path).with_suffix('.score.json')
        if not scored.exists():
            subprocess.run([
                'python3', 'scripts/measure_recall_vs_expert_list.py',
                '--expert-json', 'results/expert_lists/yevamot_2005.json',
                '--expert-filter', 'recall', '--detected', path,
                '--tractate', 'yevamot', '--matcher', 'exact', '--out', str(scored),
            ], capture_output=True, check=True)
        expert = json.loads(scored.read_text())
        # WHICH stories count is fixed by the FULL-tractate location map, never by the
        # run being scored. A 20-page run's artifact contains only those 20 dapim, so the
        # matcher anchors every expert story somewhere inside them and the slice filter
        # silently admits all 102 (found 2026-09-08, one scoring pass before it was
        # quoted). Membership comes from the canonical map, keyed on the story text.
        canon = json.loads(Path(
            'results/recall/yevamot_jeff2005_matches.json').read_text())
        member = {s['text'] for s in canon
                  if s.get('located') and s['located'][0][0] in page_slice}
        in_slice = [s for s in expert if s['text'] in member]
        found = sum(1 for s in in_slice if s.get('in_detector'))
        run = json.loads(Path(path).read_text())
        proposals = sum(len(p.get('stories') or []) + len(p.get('mishnah_stories') or [])
                        for p in run['pages'])
        runs[config].append({
            'recall': 100 * found / len(in_slice),
            'found': found, 'denominator': len(in_slice),
            'proposals': proposals, 'repairs': len(run.get('span_repairs') or []),
        })

    print(f"{'config':28}{'mean recall':>14}{'range':>16}{'SPREAD':>9}"
          f"{'proposals':>11}{'repairs':>9}")
    for config, v in runs.items():
        r = [x['recall'] for x in v]
        print(f"  {config:26}{statistics.mean(r):9.1f}%"
              f"{min(r):10.1f}-{max(r):.1f}{max(r) - min(r):9.1f}"
              f"{statistics.mean(x['proposals'] for x in v):11.1f}"
              f"{statistics.mean(x['repairs'] for x in v):9.1f}   n={len(v)}")
    print(f"\n  denominator: {v[0]['denominator']} expert stories on "
          f"{len(page_slice)} dapim")


if __name__ == '__main__':
    main()
