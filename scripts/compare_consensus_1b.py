"""Consensus 1b vs phase 1: the §4 decision on the corrected register, and what moved, case by case.

work/2026-09-28-consensus-1b-corrected-register.md. Reads only run outputs already on disk
(no model calls); every table in the finding's §10 comes from here.

    v1  = results/consensus/phase1/full.json            (old register; Claude via the API, 403 answered)
    v2  = full_v2_gemini.json + full_v2_claude.json      (corrected register; Claude via subagents)
    rep = full_v2_gemini_repeat.json + full_v2_claude_repeat.json

Output: results/consensus/phase1/compare_1b.json, and the markdown printed to stdout.
"""
import json
import logging
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
sys.path.insert(0, str(PROJECT_ROOT))
import judge_labelled_spans as j  # noqa: E402

log = logging.getLogger('consensus-1b')
P = j.OUT_DIR
M = ('gemini', 'claude')


def verdicts(*files):
    """id -> {model: verdict or None (not ok)} merged across files; plus the row."""
    rows = j.merge_runs([P / f for f in files])
    v = {r['id']: {m: (r['answers'].get(m, {}).get('verdict')
                       if r['answers'].get(m, {}).get('outcome') == 'ok' else None) for m in M}
         for r in rows}
    return v, {r['id']: r for r in rows}


def agreed(d):
    a, b = d.get('gemini'), d.get('claude')
    return a if a is not None and a == b and a != 'unsure' else None


def criteria(v, rows):
    """The plan's §4 table, fixed in advance -- never moved here."""
    review = [i for i, r in rows.items() if r['kind'] == 'review']
    both = [i for i in review if v[i]['gemini'] and v[i]['claude']]
    agree = [i for i in both if agreed(v[i])]
    story_on_no = [i for i in review if rows[i]['label'] == 'no' and agreed(v[i]) == 'story']
    lst = [i for i, r in rows.items() if r['kind'] == 'list']
    lst_both = [i for i in lst if v[i]['gemini'] and v[i]['claude']]
    list_not = [i for i in lst if agreed(v[i]) == 'not']
    c1 = len(agree) / len(both) if both else 0
    return {
        'agreement': {'k': len(agree), 'n': len(both), 'rate': round(c1, 3), 'wilson': j.wilson(len(agree), len(both)),
                      'pass': c1 >= 0.80},
        'agreed_story_on_his_no': {'n': len(story_on_no), 'ids': story_on_no, 'pass': len(story_on_no) <= 2},
        'list_called_not_by_both': {'n': len(list_not), 'of': len(lst_both), 'ids': list_not,
                                    'wilson': j.wilson(len(list_not), len(lst_both)), 'pass': len(list_not) <= 2},
        'list_called_not_by_each': {m: sum(v[i][m] == 'not' for i in lst) for m in M},
        'list_answered_by_each': {m: sum(v[i][m] is not None for i in lst) for m in M},
    }


def spread(a_file, b_file, m):
    a, _ = verdicts(a_file)
    b, rows = verdicts(b_file)
    out = Counter()
    moved = []
    for i in a:
        x, y = a[i][m], b.get(i, {}).get(m)
        if x is None or y is None:
            out[f'{rows[i]["kind"]}_unpaired'] += 1
            continue
        out[f'{rows[i]["kind"]}_paired'] += 1
        if x != y:
            out[f'{rows[i]["kind"]}_moved'] += 1
            moved.append((i, x, y))
    return dict(out), moved


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [consensus-1b] %(message)s',
                        handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'), logging.StreamHandler(sys.stderr)])
    v1, rows1 = verdicts('full.json')
    v2, rows = verdicts('full_v2_gemini.json', 'full_v2_claude.json')
    vr, _ = verdicts('full_v2_gemini_repeat.json', 'full_v2_claude_repeat.json')
    log.info('rows v1=%d v2=%d repeat=%d', len(v1), len(v2), len(vr))
    cat = json.loads((P / 'list_misses_categories.json').read_text())['categories']
    cat_of = {i: c.split(' (')[0] for c, ids in cat.items() for i in ids}
    misses = json.loads((P / 'list_misses.json').read_text())

    out = {'criteria_v2': criteria(v2, rows), 'criteria_repeat': criteria(vr, rows)}
    out['spread'] = {m: spread(f'full_v2_{m}.json', f'full_v2_{m}_repeat.json', m)[0] for m in M}

    # The 47 list stories Gemini called `not` in phase 1, one by one.
    out['list_misses'] = [{
        'id': x['id'], 'ref': x['ref'], 'shape': cat_of.get(x['id'], '?'),
        'v1_gemini': v1[f"list:{x['id']}"]['gemini'],
        'v2_gemini': v2[f"list:{x['id']}"]['gemini'], 'v2_claude': v2[f"list:{x['id']}"]['claude'],
        'rep_gemini': vr[f"list:{x['id']}"]['gemini'], 'rep_claude': vr[f"list:{x['id']}"]['claude'],
        'v2_rules': {m: (rows[f"list:{x['id']}"]['answers'][m].get('rules') or []) for m in M},
    } for x in misses]

    # The 10 of his reviewed `yes`es both models called `not` in phase 1.
    ten = [i for i, r in rows1.items() if r['kind'] == 'review' and r['label'] == 'yes'
           and agreed(v1[i]) == 'not']
    out['v1_agreed_not_on_yes'] = [{'id': i, 'v2_gemini': v2[i]['gemini'], 'v2_claude': v2[i]['claude'],
                                    'rep_gemini': vr[i]['gemini'], 'rep_claude': vr[i]['claude']} for i in ten]

    # The cost of the correction: did any of his `no`s move to `story`?
    out['his_no_to_story'] = [{
        'id': i, 'tractate': r['tractate'], 'cited_in_rules': r['cited_in_rules'],
        'v1': v1[i], 'v2': v2[i], 'rep': vr[i],
        'v2_rules': {m: (r['answers'][m].get('rules') or []) for m in M},
        'v2_reason': {m: r['answers'][m].get('reason') for m in M}}
        for i, r in rows.items() if r['kind'] == 'review' and r['label'] == 'no'
        and ('story' in v2[i].values() or 'story' in vr[i].values())]
    out['his_no_story_per_model'] = {
        run: {m: sum(1 for i, r in rows.items() if r['kind'] == 'review' and r['label'] == 'no'
                     and vv[i][m] == 'story') for m in M}
        for run, vv in (('v1', v1), ('v2', v2), ('repeat', vr))}

    (P / 'compare_1b.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')

    md = []
    for name in ('criteria_v2', 'criteria_repeat'):
        c = out[name]
        md += [f'\n**{name}**', f"- agreement {c['agreement']['k']}/{c['agreement']['n']} = "
               f"{100 * c['agreement']['rate']:.0f}% {c['agreement']['wilson']} pass={c['agreement']['pass']}",
               f"- agreed story on his no: {c['agreed_story_on_his_no']['n']} {c['agreed_story_on_his_no']['ids']}",
               f"- list called not by both: {c['list_called_not_by_both']['n']} of {c['list_called_not_by_both']['of']} "
               f"{c['list_called_not_by_both']['wilson']} {c['list_called_not_by_both']['ids']}",
               f"- list called not by each: {c['list_called_not_by_each']} (answered {c['list_answered_by_each']})"]
    md.append(f"\n**spread** {out['spread']}")
    md += ['\n**47 list misses**', '| id | ref | shape | v1 G | v2 G | v2 C | rep G | rep C |', '|---|---|---|---|---|---|---|---|']
    md += [f"| {x['id']} | {x['ref']} | {x['shape']} | {x['v1_gemini']} | {x['v2_gemini']} | {x['v2_claude']} | "
           f"{x['rep_gemini']} | {x['rep_claude']} |" for x in out['list_misses']]
    md += ['\n**v1 agreed not on his yes**', '| id | v2 G | v2 C | rep G | rep C |', '|---|---|---|---|---|']
    md += [f"| {x['id']} | {x['v2_gemini']} | {x['v2_claude']} | {x['rep_gemini']} | {x['rep_claude']} |"
           for x in out['v1_agreed_not_on_yes']]
    md += [f"\n**his no -> story per model** {out['his_no_story_per_model']}"]
    md += [f"- {x['id']} v1={x['v1']} v2={x['v2']} rep={x['rep']} rules={x['v2_rules']}" for x in out['his_no_to_story']]
    print('\n'.join(md))


if __name__ == '__main__':
    main()
