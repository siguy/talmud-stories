"""Compare v14 (2 runs) with v11 (3 runs) on full Yevamot: list stories and proposals.

No model calls. Reads the five runs and their recall files (written by
measure_recall_vs_expert_list.py --expert-filter recall --matcher exact) from
results/v11/v14_yevamot/. A proposal "moved" only if it is kept (not NOT_A_STORY) in every
run of one arm and in no run of the other; anything one-sided but not consistent is
printed as noise. Finding: docs/findings/2026-11-08-v14-vs-v11-yevamot.md
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / 'results/v11/v14_yevamot'
RUNS = {
    'v11_twin2_r1': 'results/v11/twin_pass/yevamot_full_twin2.json',
    'v11_twin2_r2': 'results/v11/twin_pass/yevamot_full_twin2_r2.json',
    'v11_twinall': 'results/v11/twin_pass/yevamot_full_twinall.json',
    'v14_r1': 'results/v11/v14_yevamot/run1.json',
    'v14_r2': 'results/v11/v14_yevamot/run2.json',
}
V11 = [k for k in RUNS if k.startswith('v11')]
V14 = [k for k in RUNS if k.startswith('v14')]
AB = {'YES': 'Y', 'HIGH_CONFIDENCE': 'H', 'LOW_CONFIDENCE': 'L', 'NOT_A_STORY': 'N'}

# ---- list stories ------------------------------------------------------
scores = {k: {e['id']: e for e in json.load(open(OUT / f'{k}.score.json'))} for k in RUNS}
ids = list(scores['v11_twinall'])
print('== recall (counts_for_recall)')
for k in RUNS:
    es = [e for e in scores[k].values() if e['counts_for_recall']]
    found = sum(e['in_detector'] for e in es)
    surv = [e for e in es if e['survived_triage']]
    fs = sum(e['in_detector'] for e in surv)
    print(f'{k:14s} end-to-end {found}/{len(es)} = {100*found/len(es):.1f}%   given-triage {fs}/{len(surv)}')
print('== list stories that differ between runs')
for i in ids:
    row = {k: scores[k][i]['in_detector'] for k in RUNS}
    if not scores['v11_twinall'][i]['counts_for_recall']:
        continue
    if len(set(row.values())) > 1:
        e = scores['v11_twinall'][i]
        print(i, e['ref'], e['located'][0], e['located'][-1], ' '.join(f'{k}={int(v)}' for k, v in row.items()),
              '| rejected-only:', {k: scores[k][i]['only_rejected'] for k in RUNS}, '|', e['text'][:90])

# ---- proposals ---------------------------------------------------------
def props(path):
    d = json.load(open(path))
    out = []
    for p in d['pages']:
        for key in ('stories', 'mishnah_stories'):
            for s in p.get(key, []):
                out.append(dict(ref=p['ref'], a=s['start_segment'], b=s['end_segment'],
                                c=AB.get(s.get('classification'), '?') + ('m' if key == 'mishnah_stories' else ''),
                                dq=s.get('disqualifiers_found') or [], summ=s.get('one_sentence_summary', '')))
    return out

P = {k: props(ROOT / v) for k, v in RUNS.items()}

def kept(x):
    return not x['c'].startswith('N')

def match(x, run):
    """Overlapping proposals in `run` on the same page."""
    return [y for y in P[run] if y['ref'] == x['ref'] and y['a'] <= x['b'] and x['a'] <= y['b']]

def cell(x, run):
    m = match(x, run)
    return ','.join(f"{y['c']}" for y in m) or '-'

seen = set()
rows = []
for k in RUNS:
    for x in P[k]:
        key = (x['ref'], x['a'], x['b'])
        if key in seen:
            continue
        seen.add(key)
        cells = {r: cell(x, r) for r in RUNS}
        kept_in = {r: any(kept(y) for y in match(x, r)) for r in RUNS}
        v14k = [kept_in[r] for r in V14]
        v11k = [kept_in[r] for r in V11]
        if all(v14k) and not any(v11k):
            tag = 'V14-ONLY (both v14, no v11)'
        elif all(v11k) and not any(v14k):
            tag = 'V11-ONLY (all v11, no v14)'
        elif any(v14k) != any(v11k):
            tag = 'noise (one-sided, not consistent)'
        else:
            # same kept-ness; record grade drift only if consistent
            g14 = {cells[r] for r in V14}; g11 = {cells[r] for r in V11}
            tag = 'grade' if len(g14) == 1 and len(g11) == 1 and g14 != g11 else None
        if tag:
            rows.append((tag, x, cells))

order = ['V14-ONLY (both v14, no v11)', 'V11-ONLY (all v11, no v14)', 'grade', 'noise (one-sided, not consistent)']
for t in order:
    rs = [r for r in rows if r[0] == t]
    print(f'== {t}: {len(rs)}')
    for _, x, cells in sorted(rs, key=lambda r: (r[1]['ref'], r[1]['a'])):
        print(f"  {x['ref']}:{x['a']}-{x['b']}  " + ' '.join(f'{r[4:] if r.startswith("v11") else r}={cells[r]}' for r in RUNS)
              + f"  dq={x['dq']}  | {x['summ'][:110]}")
