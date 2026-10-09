"""Does widening `borderline` (judge_register_v2.md + R-C7) move partial stories off `not`?

work/done/2026-10-09-borderline-definition-test.md. No model calls. On the 287 units in
results/consensus/phase1/borderline_test_ids.txt -- his borderlines, his `no`s, and the
passages Gemini called a story and Claude `not` in v3 -- compares, per judge:

    v3 = full_v3_{gemini,claude}.json  (judge_register_v1: borderline = R-C2 only)
    v4 = bl_v4_{gemini,claude}.json    (judge_register_v2: borderline = R-C7)

Same register text otherwise, except that v4's carries R-C7. Labels are his, with his
2026-10-07 verdicts applied. Units R-C7 or his 2026-10-07 answers quote are excluded
(the judge is shown their answer).

What success looks like: his `yes`/`borderline` move from `not` to `borderline`; his `no`s
stay `not`. Output: results/consensus/phase1/compare_borderline_test.json + markdown.
"""
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
from compare_consensus_1b import verdicts, M  # noqa: E402
from compare_consensus_v3 import current_labels, RULED  # noqa: E402
import judge_labelled_spans as j  # noqa: E402

P = j.OUT_DIR
# Passages R-C7 quotes by name (docs/STORY_RULES.md).
QUOTED_IN_RC7 = {'review:Ketubot 10a_9-10', 'review:Ketubot 60b_5-6', 'review:Ketubot 85a_13-14',
                 'review:Gittin 20a_9-9', 'review:Ketubot 50b_9-10', 'review:Ketubot 51a_1-2',
                 'review:Ketubot 77a_8-8', 'corrected:Ketubot 14b_11-11', 'review:Ketubot 50b_6-6',
                 'review:Ketubot 100b_17-18'}


def main():
    ids = set((P / 'borderline_test_ids.txt').read_text().splitlines()) - {''}   # ids contain spaces
    v3, rows = verdicts('full_v3_gemini.json', 'full_v3_claude.json')
    v4, _ = verdicts('bl_v4_gemini.json', 'bl_v4_claude.json')
    lab = current_labels(rows)
    quoted = (QUOTED_IN_RC7 | set(RULED)) & ids
    scored = sorted(ids - quoted)
    out = {'units': len(ids), 'excluded_quoted': sorted(quoted), 'scored': len(scored), 'by_model': {}}
    md = [f'{len(scored)} scored ({len(quoted)} quoted in the rules excluded)']
    for m in M:
        tab = {}
        for run, v in (('v3', v3), ('v4', v4)):
            tab[run] = {l: dict(Counter(v[i][m] for i in scored if lab[i] == l))
                        for l in ('yes', 'borderline', 'no')}
        moved = Counter((v3[i][m], v4[i][m]) for i in scored if v3[i][m] != v4[i][m])
        out['by_model'][m] = {'table': tab, 'moved': {f'{a}->{b}': n for (a, b), n in moved.most_common()}}
        md += [f'\n**{m}** — his label → judge verdict', '| his | v3 (old borderline) | v4 (R-C7) |', '|---|---|---|']
        md += [f"| {l} | {tab['v3'][l]} | {tab['v4'][l]} |" for l in ('yes', 'borderline', 'no')]
        md.append(f"moved: {out['by_model'][m]['moved']}")
    # the consensus criteria on this subset
    agreed = lambda v, i: v[i]['gemini'] if v[i]['gemini'] and v[i]['gemini'] == v[i]['claude'] else None
    for run, v in (('v3', v3), ('v4', v4)):
        both = [i for i in scored if v[i]['gemini'] and v[i]['claude']]
        pos = lambda x: x in ('story', 'borderline')
        agree_pos = sum(1 for i in both if pos(v[i]['gemini']) == pos(v[i]['claude']))
        out[run] = {'agree_story_vs_not': f'{agree_pos}/{len(both)}',
                    'both_not_on_his_yes_or_borderline': sum(1 for i in scored if lab[i] in ('yes', 'borderline')
                                                             and agreed(v, i) == 'not'),
                    'both_story_or_borderline_on_his_no': sum(1 for i in scored if lab[i] == 'no'
                                                              and pos(v[i]['gemini'] or '') and pos(v[i]['claude'] or ''))}
        md.append(f'\n**{run}** {out[run]}')
    (P / 'compare_borderline_test.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print('\n'.join(md))


if __name__ == '__main__':
    main()
