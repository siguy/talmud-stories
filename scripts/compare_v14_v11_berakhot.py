"""Compare v14 (2 runs) with v11 (1 run) on Berakhot: proposals only — no expert list exists.

No model calls. Adapted from compare_v14_v11_yevamot.py, with one change: spans are
matched by shared (ref, segment) CELLS, so a cross-page story overlaps what it covers on
its second page too (the Yevamot script matched on the first page only).

A proposal "moved" only if it is kept (not NOT_A_STORY) in every run of one version and in
no run of the other; one-sided but inconsistent = noise. `mishnah_stories[]` is read and
marked `m` (withheld by Stage 4g); a withheld span does not count as kept.
For each moved passage the English of its segments is printed (results/sefaria/berakhot.json).
Finding: docs/findings/2026-11-08-v14-vs-v11-berakhot.md
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import judge_detector_spans as jd  # noqa: E402  (shares the span reader and the text)

RUNS = jd.RUNS
V11 = [k for k in RUNS if k.startswith('v11')]
V14 = [k for k in RUNS if k.startswith('v14')]
AB = {'YES': 'Y', 'HIGH_CONFIDENCE': 'H', 'LOW_CONFIDENCE': 'L', 'NOT_A_STORY': 'N'}

text = jd.j.Text(jd.TRACTATE)
P = {k: jd.spans(v, text) for k, v in RUNS.items()}


def code(s):
    return AB.get(s['cls'], '?') + ('m' if s['withheld'] else '')


def kept(s):
    return not s['withheld'] and s['cls'] != 'NOT_A_STORY'


def match(x, run):
    return [y for y in P[run] if y['cells'] & x['cells']]


def english(cells):
    t = ' '.join(text.seg[c].get('english', '') for c in sorted(cells, key=text.pos.get))
    return re.sub(r'<[^>]+>', '', t)


print('== proposals per run (kept = stories[] not NOT_A_STORY)')
for k in RUNS:
    print(f"{k:7s} spans {len(P[k])}  kept {sum(kept(s) for s in P[k])}  "
          f"NOT_A_STORY {sum(s['cls'] == 'NOT_A_STORY' and not s['withheld'] for s in P[k])}  "
          f"withheld {sum(s['withheld'] for s in P[k])}")

seen, rows = set(), []
for k in RUNS:
    for x in P[k]:
        key = frozenset(x['cells'])
        if key in seen:
            continue
        seen.add(key)
        cells = {r: ','.join(code(y) for y in match(x, r)) or '-' for r in RUNS}
        kin = {r: any(kept(y) for y in match(x, r)) for r in RUNS}
        k14, k11 = [kin[r] for r in V14], [kin[r] for r in V11]
        if all(k14) and not any(k11):
            tag = 'V14-ONLY'
        elif all(k11) and not any(k14):
            tag = 'V11-ONLY'
        elif any(k14) != any(k11):
            tag = 'noise'
        else:
            g14 = {cells[r] for r in V14}
            g11 = {cells[r] for r in V11}
            tag = 'grade' if len(g14) == 1 and len(g11) == 1 and g14 != g11 else None
        if tag:
            rows.append((tag, x, cells))

for t in ('V14-ONLY', 'V11-ONLY', 'grade', 'noise'):
    rs = sorted([r for r in rows if r[0] == t], key=lambda r: text.pos[min(r[1]['cells'], key=text.pos.get)])
    # one row per passage: drop a row whose cells are inside an earlier row's of the same tag
    uniq = []
    for r in rs:
        if not any(r[1]['cells'] <= u[1]['cells'] or r[1]['cells'] & u[1]['cells'] for u in uniq):
            uniq.append(r)
    print(f'\n== {t}: {len(uniq)} passages ({len(rs)} spans)')
    for _, x, cells in uniq:
        last = max(x['cells'], key=text.pos.get)
        end = f"{last[1]}" if last[0] == x['ref'] else f"{last[0].split()[-1]}:{last[1]}"
        print(f"  {x['ref']}:{x['a']}-{end}  " + ' '.join(f'{r}={cells[r]}' for r in RUNS)
              + f"  | {x['summary'][:120]}")
        if t in ('V14-ONLY', 'V11-ONLY'):
            print(f"      EN: {english(x['cells'])[:400]}")
