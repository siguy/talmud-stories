"""Consensus v3 vs v2: what Jeff's 2026-10-07 rulings did to the two judges.

work/2026-10-09-consensus-v3-after-jeff-rulings.md. Reads run outputs on disk only (no
model calls).

    v2 = full_v2_gemini.json + full_v2_claude.json   (register as of 2026-09-28)
    v3 = full_v3_gemini.json + full_v3_claude.json   (register + his 2026-10-07 rulings)

Same prompt file, same labels.json, same models, same subagent batch seed -- only the
register differs. Each run is scored twice:

  labels-as-run  the labels both runs were built against (labels.json, unchanged);
  current        the same labels with his 2026-10-07 verdicts applied: three 2005-list
                 entries he now calls `not`, and 50a:10 (his February `no`) now
                 `borderline`. A list `not` is scored as a `no`.

Caveat printed with every number: the passages he ruled on are now QUOTED in the
register (rule-informed), so a judge answering them right is partly reading the answer.
Criteria are also reported with those passages excluded.

Output: results/consensus/phase1/compare_v3.json, and markdown on stdout.
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
from compare_consensus_1b import verdicts, agreed, M  # noqa: E402

log = logging.getLogger('consensus-v3')
P = j.OUT_DIR

# His 2026-10-07 answers, by judge unit id (results/consensus/contrast_pairs.json).
RULED = {
    'list:kiddushin_085': ('1A', 'borderline'),
    'list:yevamot_072': ('1B', 'no'),
    'list:ketubot_015': ('2A', 'no'),
    'list:ketubot_033': ('2B', 'no'),
    'review:Ketubot 50b_4-5': ('3A', 'no'),
    'review:Ketubot 50a_10-10': ('3B', 'borderline'),
    'list:ketubot_050': ('4A', 'yes'),
    'list:ketubot_076': ('4B', None),          # blank -- not scored as changed
}


def current_labels(rows):
    lab = {i: r['label'] for i, r in rows.items()}
    for i, (_, new) in RULED.items():
        if new and i in lab:
            lab[i] = new
    return lab


def criteria(v, rows, lab, skip=()):
    """The plan's §4 criteria (compare_consensus_1b.criteria), with labels passed in so a
    list story he has since called `no` is scored as one."""
    ids = [i for i in rows if i not in skip]
    review = [i for i in ids if rows[i]['kind'] == 'review']
    both = [i for i in review if v[i]['gemini'] and v[i]['claude']]
    agree = [i for i in both if agreed(v[i])]
    # review (and, under current labels, list) units only -- as compare_consensus_1b, which
    # leaves `corrected` units out of this criterion.
    story_on_no = [i for i in ids if rows[i]['kind'] != 'corrected' and lab[i] == 'no'
                   and agreed(v[i]) == 'story']
    lst = [i for i in ids if rows[i]['kind'] == 'list' and lab[i] in ('yes', 'borderline')]
    lst_both = [i for i in lst if v[i]['gemini'] and v[i]['claude']]
    list_not = [i for i in lst if agreed(v[i]) == 'not']
    return {
        'agreement': {'k': len(agree), 'n': len(both), 'rate': round(len(agree) / len(both), 3) if both else 0,
                      'wilson': j.wilson(len(agree), len(both))},
        'agreed_story_on_his_no': {'n': len(story_on_no), 'ids': story_on_no},
        'list_called_not_by_both': {'n': len(list_not), 'of': len(lst_both), 'ids': list_not},
    }


def tally(v, rows, lab):
    """Whole-set picture: both right (loose: story~borderline), strict, split, both wrong."""
    def ok(l, x, strict):
        if x is None:
            return False
        if strict:
            return x == {'yes': 'story', 'borderline': 'borderline', 'no': 'not', 'out_of_scope': 'out_of_scope'}[l]
        return (l in ('yes', 'borderline') and x in ('story', 'borderline')) or \
               (l in ('no', 'out_of_scope') and x in ('not', 'out_of_scope'))
    c = Counter()
    for i in rows:
        a, b = v[i]['gemini'], v[i]['claude']
        if a is None or b is None:
            c['missing'] += 1
            continue
        if ok(lab[i], a, False) and ok(lab[i], b, False):
            c['both_right_loose'] += 1
            c['both_right_strict'] += ok(lab[i], a, True) and ok(lab[i], b, True)
        elif ok(lab[i], a, False) != ok(lab[i], b, False):
            c['split'] += 1
        else:
            c['both_wrong'] += 1
    return dict(c)


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [consensus-v3] %(message)s',
                        handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'), logging.StreamHandler(sys.stderr)])
    v2, rows = verdicts('full_v2_gemini.json', 'full_v2_claude.json')
    v3, rows3 = verdicts('full_v3_gemini.json', 'full_v3_claude.json')
    assert set(rows) == set(rows3), 'v2 and v3 judged different units'
    log.info('rows v2=%d v3=%d', len(v2), len(v3))
    old = {i: r['label'] for i, r in rows.items()}
    cur = current_labels(rows)
    ruled = set(RULED)

    out = {}
    for run, v in (('v2', v2), ('v3', v3)):
        out[run] = {
            'labels_as_run': criteria(v, rows, old),
            'current': criteria(v, rows, cur),
            'current_excl_ruled': criteria(v, rows, cur, skip=ruled),
            'tally_current': tally(v, rows, cur),
            'per_model_verdicts': {m: dict(Counter(v[i][m] for i in rows)) for m in M},
        }
    out['ruled_passages'] = [{'q': q, 'id': i, 'his_now': new, 'v2': v2[i], 'v3': v3[i]}
                             for i, (q, new) in RULED.items()]
    moved = Counter()
    for i in rows:
        for m in M:
            if v2[i][m] and v3[i][m] and v2[i][m] != v3[i][m]:
                moved[(m, v2[i][m], v3[i][m])] += 1
    out['moved'] = [{'model': m, 'from': a, 'to': b, 'n': n} for (m, a, b), n in moved.most_common()]
    (P / 'compare_v3.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')

    md = []
    for std in ('labels_as_run', 'current', 'current_excl_ruled'):
        md += [f'\n**{std}**', '| | v2 | v3 |', '|---|---|---|']
        for key, fmt in (('agreement', lambda c: f"{c['k']}/{c['n']} = {100 * c['rate']:.1f}%"),
                         ('agreed_story_on_his_no', lambda c: str(c['n'])),
                         ('list_called_not_by_both', lambda c: f"{c['n']} of {c['of']}")):
            md.append(f"| {key} | {fmt(out['v2'][std][key])} | {fmt(out['v3'][std][key])} |")
    md += ['\n**tally (current labels)**', f"- v2 {out['v2']['tally_current']}", f"- v3 {out['v3']['tally_current']}"]
    md += ['\n**the eight passages**', '| q | id | his now | v2 G/C | v3 G/C |', '|---|---|---|---|---|']
    md += [f"| {x['q']} | {x['id']} | {x['his_now']} | {x['v2']['gemini']}/{x['v2']['claude']} | "
           f"{x['v3']['gemini']}/{x['v3']['claude']} |" for x in out['ruled_passages']]
    md += ['\n**moved v2 -> v3**'] + [f"- {x['model']}: {x['from']} -> {x['to']}: {x['n']}" for x in out['moved']]
    md += [f"\n**v3 verdicts** {out['v3']['per_model_verdicts']}"]
    print('\n'.join(md))


if __name__ == '__main__':
    main()
