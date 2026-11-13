#!/usr/bin/env python3
"""Grade the whole low-confidence pool with the calibrated Claude grader, and pick what both passes call a story.

work/2026-11-13-low-pool-grader-calibration.md, step 2. Calibration (calibrate_low_pool_grader.py,
docs/findings/2026-11-13-low-pool-grader-calibration.md) measured "both passes say story" at 32/33 against
Jeff. Simon approved grading the pool with the same grader and the same prompt (JUDGE_PROMPT_SHA).

The pool, written to results/shas_run/low_pool/pool/manifest.json: every v14 unit (results/consensus/<t>/units.json)
in pools P1-P4 of measure_site_misses.py -- definite/LOW, definite/NOT, LOW/LOW, LOW/NOT across the two runs --
whose cells touch nothing on the site (site/data/<t>.json stories AND out_of_scope, so the biblical passages
the site moved out of scope stay out) and nothing removed by septimus_site_decisions.json. The same filter as
measure_site_misses.pool() and calibrate_low_pool_grader.c2_rows().

NOT in the pool: the golden LOW stories of the reviewed tractates (Ketubot / Kiddushin / Gittin). The 1,259 the
calibration was approved for never counted them; Jeff has ruled on most of them himself, and the ones on his
own list have their own route (Rule 0 of docs/findings/2026-11-13-how-many-stories-we-miss.md).

Reuse: a pool unit graded in calibration C2 (Eruvin / Yevamot) with identical cells AND a byte-identical prompt
carries `reuse` and is not exported again; select reads its two calibration verdicts (pass1 -> pass1,
pass2 -> pass2). `build` checks the prompt bytes against the calibration keys and refuses reuse otherwise.

    JUDGE_PROMPT=src/prompts/judge_register_v2.md python3 scripts/grade_low_pool.py build
    JUDGE_PROMPT=... python3 scripts/grade_low_pool.py export --pass pass1 --seed 1
    JUDGE_PROMPT=... python3 scripts/grade_low_pool.py export --pass pass2 --seed 2
    #  graders write <pass>/answers/<NNN>.json -- exactly as in calibration
    JUDGE_PROMPT=... python3 scripts/grade_low_pool.py import --pass pass1 --model <what ran>
    JUDGE_PROMPT=... python3 scripts/grade_low_pool.py import --pass pass2 --model <what ran>
    JUDGE_PROMPT=... python3 scripts/grade_low_pool.py select
    JUDGE_PROMPT=... python3 scripts/grade_low_pool.py sample          # seeded 60 for Simon to read

No model is ever called here.
"""
import argparse
import json
import logging
import os
import random
import sys
import time
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
import calibrate_low_pool_grader as cal  # noqa: E402  (also sets Eruvin/Yevamot text sources)
import judge_labelled_spans as j  # noqa: E402
import tractates as T  # noqa: E402

log = logging.getLogger('low-pool-grade')
OUT = PROJECT_ROOT / 'results/shas_run/low_pool/pool'
CAL = cal.OUT
PASSES = ('pass1', 'pass2')
SAMPLE_N, SAMPLE_SEED = 60, 20261113


def site_slugs():
    """Tractates the site ships from two v14 runs: a site file that is not `reviewed`, with consensus units."""
    out = []
    for p in sorted((PROJECT_ROOT / 'site/data').glob('*.json')):
        d = json.loads(p.read_text())
        if isinstance(d, dict) and 'stories' in d and not d.get('reviewed') \
                and (PROJECT_ROOT / f'results/consensus/{p.stem}/units.json').exists():
            out.append(p.stem)
    return out


def text_for(slug):
    """The text the Shas judge read for this tractate (judge_detector_spans sets the same)."""
    j.TEXT_SOURCES[T.english(slug)] = [str(T.Paths(slug, PROJECT_ROOT).text.relative_to(PROJECT_ROOT))]
    return j.Text(T.english(slug))


def taken_cells(slug):
    sf = cal.load(f'site/data/{slug}.json')
    taken = {(g['ref'], g['i']) for s in sf['stories'] + sf['out_of_scope'] for g in s['segments']}
    for e in cal.load('results/shas_run/septimus_site_decisions.json')['remove']['passages']:
        if e['tractate'] == slug:
            taken |= {(e['ref'], i) for i in range(int(e['start_segment']), int(e['end_segment']) + 1)}
    return taken


def calibration_prompts():
    """{calibration id: prompt} from the calibration pass1 keys (pass2 holds the same prompts, reshuffled)."""
    out = {}
    for f in sorted((CAL / 'pass1' / 'keys').glob('*.json')):
        for it in json.loads(f.read_text()):
            out[it['id']] = it['prompt']
    return out


def build():
    cal.check_prompt()
    cal_prompts = calibration_prompts()
    spans, n_reuse_refused = [], 0
    for slug in site_slugs():
        text, taken = text_for(slug), taken_cells(slug)
        for u in cal.load(f'results/consensus/{slug}/units.json')['units']:
            cls = {r: (u['calls'].get(r) or {}).get('cls') for r in ('v14_r1', 'v14_r2')}
            pool = cal.POOL.get(tuple(sorted(cal.grade(c) for c in cls.values())))
            cells = {tuple(c) for c in u['cells']}
            if not pool or cells & taken:
                continue
            missing = [c for c in cells if c not in text.seg]
            if missing:
                raise ValueError(f'{u["id"]}: cells outside the text on disk {sorted(missing)[:3]}')
            s = dict(id=u['id'], tractate=u['tractate'], slug=slug, ref=u['cells'][0][0], cells=u['cells'],
                     pool=pool, run1=cls['v14_r1'], run2=cls['v14_r2'],
                     withheld={r: (u['calls'].get(r) or {}).get('withheld') for r in ('v14_r1', 'v14_r2')},
                     summary=u.get('summary'))
            cid = f'C2:{u["id"]}'
            if cid in cal_prompts:
                if j.user_prompt(s, text)[0] == cal_prompts[cid]:
                    s['reuse'] = cid
                else:
                    n_reuse_refused += 1
                    log.warning('%s: calibration prompt differs -- re-exported, not reused', u['id'])
            spans.append(s)
    ids = [s['id'] for s in spans]
    assert len(ids) == len(set(ids)), 'duplicate span ids'
    meta = {'what': __doc__.split('\n\n')[0], 'judge_prompt': str(j.PROMPT_PATH.relative_to(PROJECT_ROOT)),
            'judge_prompt_sha': j.prompt_sha(), 'units': len(spans),
            'by_pool': dict(sorted(Counter(s['pool'] for s in spans).items())),
            'tractates': len({s['slug'] for s in spans}),
            'by_tractate': {t: dict(sorted(Counter(s['pool'] for s in spans if s['slug'] == t).items()))
                            for t in sorted({s['slug'] for s in spans})},
            'reused_from_calibration': sum(bool(s.get('reuse')) for s in spans),
            'reuse_refused_prompt_differs': n_reuse_refused,
            'to_export': sum(not s.get('reuse') for s in spans),
            'built': time.strftime('%Y-%m-%dT%H:%M:%S')}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'manifest.json').write_text(json.dumps({'meta': meta, 'spans': spans}, ensure_ascii=False, indent=1) + '\n')
    log.info('pool manifest: %d units in %d tractates %s; reused %d, to export %d',
             len(spans), meta['tractates'], meta['by_pool'], meta['reused_from_calibration'], meta['to_export'])


# ---- select -----------------------------------------------------------------------

def answers(d):
    """{id: answer} from one imported pass (<d>/claude.json)."""
    return {r['id']: r['answer'] for r in json.loads((d / 'claude.json').read_text())['rows']}


def select_promotions(spans, A):
    """Spans BOTH passes validly call `story`. A = {pass: {id: answer}}; a reused span is looked up by its
    calibration id. A missing or invalid answer in either pass is counted, never promoted (Lesson 21).
    Returns (promotions, counts)."""
    promos, c = [], Counter(scored=0, unscored=0)
    for s in spans:
        key = s.get('reuse') or s['id']
        got = [A[p].get(key) for p in PASSES]
        if any(a is None or a.get('outcome') != 'ok' for a in got):
            c['unscored'] += 1
            continue
        v = tuple(a['verdict'] for a in got)
        c['scored'] += 1
        if v != ('story', 'story'):
            continue
        promos.append({**{k: s[k] for k in ('id', 'tractate', 'slug', 'ref', 'cells', 'pool', 'run1', 'run2',
                                            'summary')},
                       'reused_from_calibration': s.get('reuse'),
                       'grader': {p: {k: a.get(k) for k in ('verdict', 'rules', 'segments', 'reason')}
                                  for p, a in zip(PASSES, got)}})
    c['promoted'] = len(promos)
    return promos, c


def select():
    man = json.loads((OUT / 'manifest.json').read_text())
    for p in PASSES:
        exp = json.loads((OUT / p / 'claude.json').read_text())['meta']
        if exp['prompt_sha'] != man['meta']['judge_prompt_sha']:
            raise SystemExit(f'{p} graded on prompt {exp["prompt_sha"]}, manifest built on {man["meta"]["judge_prompt_sha"]}')
    A = {p: {**answers(CAL / p), **answers(OUT / p)} for p in PASSES}
    promos, c = select_promotions(man['spans'], A)
    res = {'meta': {'rule': 'both passes say story (calibrated 32/33 = 0.97 vs Jeff)',
                    'judge_prompt_sha': man['meta']['judge_prompt_sha'], **dict(c),
                    'pool_units': len(man['spans']),
                    'by_pool': dict(sorted(Counter(x['pool'] for x in promos).items())),
                    'by_tractate': dict(sorted(Counter(x['slug'] for x in promos).items())),
                    'selected': time.strftime('%Y-%m-%dT%H:%M:%S')},
           'promotions': promos}
    (OUT / 'promotions.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    log.info('promotions: %d of %d (%s unscored); by pool %s', c['promoted'], len(man['spans']), c['unscored'],
             res['meta']['by_pool'])


# ---- sample -----------------------------------------------------------------------

def bracket_cells(cells, text):
    """[cell] in the order the prompt numbers them [1], [2], ... (user_prompt's own layout)."""
    a, b = text.pos[tuple(cells[0])], text.pos[tuple(cells[-1])]
    return text.cells[max(a - 1, 0):b + 2]


def sample():
    promos = json.loads((OUT / 'promotions.json').read_text())['promotions']
    pick = random.Random(SAMPLE_SEED).sample(promos, min(SAMPLE_N, len(promos)))
    texts, rows = {}, []
    for p in pick:
        text = texts.get(p['slug']) or texts.setdefault(p['slug'], text_for(p['slug']))
        numbered = bracket_cells(p['cells'], text)
        chose = {tuple(numbered[n - 1]) for n in p['grader']['pass1']['segments'] if 0 < n <= len(numbered)}
        rows.append({'id': p['id'], 'ref': p['ref'], 'tractate': p['tractate'], 'pool': p['pool'],
                     'run1': p['run1'], 'run2': p['run2'], 'detector_summary': p['summary'],
                     'segments': [{'ref': c[0], 'i': c[1], 'hebrew': text.seg[tuple(c)].get('hebrew', '').strip(),
                                   'english': text.seg[tuple(c)].get('english', '').strip(),
                                   'grader_pass1_chose': tuple(c) in chose} for c in p['cells']],
                     'grader_reason': {k: v['reason'] for k, v in p['grader'].items()},
                     'grader_rules': {k: v['rules'] for k, v in p['grader'].items()},
                     'simon_verdict': None})
    meta = {'what': 'a seeded random sample of promotions for Simon to read; nothing ships unless >= 54 of 60 are real',
            'seed': SAMPLE_SEED, 'n': len(rows), 'of': len(promos),
            'by_pool': dict(sorted(Counter(r['pool'] for r in rows).items())),
            'drawn': time.strftime('%Y-%m-%dT%H:%M:%S')}
    (OUT / 'review_sample.json').write_text(json.dumps({'meta': meta, 'rows': rows}, ensure_ascii=False, indent=1) + '\n')
    log.info('review sample: %d of %d promotions, seed %d', len(rows), len(promos), SAMPLE_SEED)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('build')
    e = sub.add_parser('export')
    e.add_argument('--pass', dest='pass_name', required=True, choices=PASSES)
    e.add_argument('--seed', type=int, required=True)
    e.add_argument('--batch', type=int, default=20)
    i = sub.add_parser('import')
    i.add_argument('--pass', dest='pass_name', required=True, choices=PASSES)
    i.add_argument('--model', required=True)
    sub.add_parser('select')
    sub.add_parser('sample')
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [low-pool-grade] %(message)s',
                        handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'), logging.StreamHandler(sys.stdout)])
    if 'JUDGE_PROMPT' not in os.environ:
        raise SystemExit('set JUDGE_PROMPT=src/prompts/judge_register_v2.md (the module default is v1)')
    if args.cmd in ('export', 'import'):
        for slug in sorted({s['slug'] for s in json.loads((OUT / 'manifest.json').read_text())['spans']}):
            j.TEXT_SOURCES[T.english(slug)] = [str(T.Paths(slug, PROJECT_ROOT).text.relative_to(PROJECT_ROOT))]
    if args.cmd == 'export':
        cal.export(args.pass_name, args.seed, args.batch, out=OUT)
    elif args.cmd == 'import':
        cal.import_(args.pass_name, args.model, out=OUT)
    else:
        {'build': build, 'select': select, 'sample': sample}[args.cmd]()


if __name__ == '__main__':
    main()
