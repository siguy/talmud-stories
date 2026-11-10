"""Judge prompt v4 vs v2 on Jeff's labelled passages -- Gemini, paired, same day.

work/2026-11-09-judge-register-v4.md. No model calls. Reads four runs on the 287-unit hard
subset (results/consensus/phase1/borderline_test_ids.txt), all with today's register:

    bl_v6_v2{a,b}_gemini.json   judge_register_v2.md (borderline includes "one event, then a ruling")
    bl_v6_v4{a,b}_gemini.json   judge_register_v4.md (that shape removed, per Jeff 2026-10-25)

The a/b pairs are same-prompt repeats: the noise floor (Lesson 22). Labels are
current_labels() (his 2026-10-07 answers and the 2026-10-09 label fixes). Excluded: any
unit the register now quotes (`cited_in_rules`), plus the lists the 2026-10-09 test
excluded -- the judge is shown their answer.

His `borderline` labels predate 10-25 where they are February verdicts; a February
borderline of the withdrawn shape that v4 sends to `not` is the change he asked for, not a
cost. So every yes/borderline that moves to `not` is printed with the judge's reason, to be
read, not just counted.
"""
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
from compare_consensus_v3 import current_labels, RULED  # noqa: E402
from compare_borderline_test import QUOTED_IN_RC7  # noqa: E402
import judge_labelled_spans as j  # noqa: E402

P = j.OUT_DIR
RUNS = ('v2a', 'v2b', 'v4a', 'v4b')
LABELS = ('yes', 'borderline', 'no')


def load(run):
    d = json.load(open(P / f'bl_v6_{run}_gemini.json'))
    rows = {r['id']: r for r in d['rows']}
    v = {i: (r['answers']['gemini']['verdict'] if r['answers'].get('gemini', {}).get('outcome') == 'ok'
             else None) for i, r in rows.items()}
    return d['meta'], rows, v


def main():
    ids = set((P / 'borderline_test_ids.txt').read_text().splitlines()) - {''}
    data = {r: load(r) for r in RUNS}
    rows = data['v2a'][1]
    lab = current_labels(rows)
    quoted = {i for i in ids if str(rows[i].get('cited_in_rules')) == 'True'} | ((QUOTED_IN_RC7 | set(RULED)) & ids)
    failed = {i for i in ids for r in RUNS if data[r][2].get(i) is None}
    scored = sorted(ids - quoted - failed)
    V = {r: data[r][2] for r in RUNS}
    out = {'meta': {r: {k: data[r][0][k] for k in ('prompt', 'prompt_sha', 'rules_sha', 'commit', 'finished')}
                    for r in RUNS},
           'units': len(ids), 'excluded_quoted': len(quoted), 'failed_any_run': len(failed),
           'scored': len(scored), 'table': {}, 'flips': {}}
    md = [f'{len(scored)} scored of {len(ids)} ({len(quoted)} quoted in the register excluded, '
          f'{len(failed)} with a failed call in some run -- counted, not scored)\n',
          '| his label | ' + ' | '.join(RUNS) + ' |', '|---' * (len(RUNS) + 1) + '|']
    for l in LABELS:
        row = {r: dict(Counter(V[r][i] for i in scored if lab[i] == l).most_common()) for r in RUNS}
        out['table'][l] = row
        md.append(f'| {l} ({sum(lab[i] == l for i in scored)}) | ' + ' | '.join(str(row[r]) for r in RUNS) + ' |')

    def flips(a, b):
        return [i for i in scored if V[a][i] != V[b][i]]
    md.append('')
    for a, b in (('v2a', 'v2b'), ('v4a', 'v4b'), ('v2a', 'v4a'), ('v2b', 'v4b')):
        f = flips(a, b)
        out['flips'][f'{a}-{b}'] = {'n': len(f), 'moves': dict(Counter(f'{V[a][i]}->{V[b][i]}' for i in f).most_common())}
        md.append(f'- {a} vs {b}: {len(f)} verdicts differ {out["flips"][f"{a}-{b}"]["moves"]}')

    # consistent movers: borderline in both v2 runs, not in both v4 runs (and the reverse)
    def cons(frm, to):
        return [i for i in scored if V['v2a'][i] == V['v2b'][i] == frm and V['v4a'][i] == V['v4b'][i] == to]
    md.append('\n**Consistent moves (both v2 runs -> both v4 runs), by his label**')
    out['consistent'] = {}
    for frm, to in (('borderline', 'not'), ('story', 'not'), ('not', 'borderline'), ('story', 'borderline'),
                    ('borderline', 'story')):
        c = cons(frm, to)
        out['consistent'][f'{frm}->{to}'] = {l: [i for i in c if lab[i] == l] for l in LABELS}
        md.append(f'- {frm} -> {to}: ' + ', '.join(f'his {l} {sum(lab[i] == l for i in c)}' for l in LABELS))
    md.append('\n**His yes/borderline that v4 consistently sends to `not` -- read each**')
    for i in scored:
        if lab[i] in ('yes', 'borderline') and V['v4a'][i] == V['v4b'][i] == 'not' and 'not' not in (V['v2a'][i], V['v2b'][i]):
            a = data['v4a'][1][i]['answers']['gemini']
            md.append(f'- `{i}` his {lab[i]}; v2 {V["v2a"][i]}/{V["v2b"][i]}; v4: {a["reason"][:260]}')
    (P / 'compare_v2_v4.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print('\n'.join(md))


if __name__ == '__main__':
    main()
