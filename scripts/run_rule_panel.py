"""Rule panel ("lenses"), a DIAGNOSTIC: nine feature questions per span, the verdict decided in code.

work/2026-10-02-rule-panel-lenses.md. Same 997 units, same passage text and the same full
rule register as the single-question judge (judge_labelled_spans.py) -- the only change is
that the model answers nine narrow questions (src/prompts/judges/panel_v1.md) instead of
"is it a story?", and src/consensus/decide.py turns the answers into a verdict. So any
difference against phase 1b is the question's structure, not new knowledge.

A failed or invalid answer is COUNTED, never decided (Lesson 21). Eruvin is never read.

    python3 scripts/run_rule_panel.py run --backend gemini --out results/consensus/panel/gemini.json --dry-run
    python3 scripts/run_rule_panel.py run --backend gemini --out results/consensus/panel/gemini.json
    python3 scripts/run_rule_panel.py export --run claude --seed 1        # then subagents answer
    python3 scripts/run_rule_panel.py import --run claude --model "..."
    python3 scripts/run_rule_panel.py report
"""
import argparse
import hashlib
import json
import logging
import sys
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
sys.path.insert(0, str(PROJECT_ROOT))
import judge_labelled_spans as j  # noqa: E402
from src.consensus.decide import FEATURES, ANSWERS, decide, blocking  # noqa: E402

log = logging.getLogger('rule-panel')
PROMPT_PATH = PROJECT_ROOT / 'src/prompts/judges/panel_v1.md'
OUT_DIR = PROJECT_ROOT / 'results/consensus/panel'
SUBAGENT_DIR = OUT_DIR / 'subagent'
SINGLE_LENS = ('full_v2_gemini.json', 'full_v2_claude.json')   # phase 1b, in j.OUT_DIR


def system_prompt():
    return PROMPT_PATH.read_text().replace('{RULES}', j.rules_text())   # the same register as 1b


def prompt_sha():
    return hashlib.sha256(system_prompt().encode()).hexdigest()[:12]


def ask_panel(backend, system, user, passage_numbers):
    """One call -> features + the decided verdict, or an outcome with NO verdict."""
    fail = lambda outcome, why: dict(outcome=outcome, verdict=None, features=None, segments=None,
                                     judge=None, rule=None, ours=None, blocking=None, error=why)
    try:
        raw = backend(system, user)
    except Exception as e:  # noqa: BLE001 -- counted, never decided
        return fail('failed', f'{type(e).__name__}: {e}')
    try:
        ans = j._parse(raw) if isinstance(raw, str) else raw
    except Exception as e:  # noqa: BLE001
        return fail('invalid', f'unparseable: {e}; raw={str(raw)[:200]!r}')
    feats = ans.get('features') if isinstance(ans, dict) else None
    if not isinstance(feats, dict) or set(FEATURES) - set(feats):
        return fail('invalid', f'missing features: {sorted(set(FEATURES) - set(feats or {}))}')
    flat = {}
    for k in FEATURES:
        v = feats[k]
        a = v.get('answer') if isinstance(v, dict) else v
        if a not in ANSWERS:
            return fail('invalid', f'{k}: answer {a!r} outside {ANSWERS}')
        flat[k] = a
    segs = ans.get('segments', [])
    if not isinstance(segs, list) or not all(isinstance(x, int) and not isinstance(x, bool) for x in segs):
        return fail('invalid', f'segments {segs!r} are not integers')
    if not set(segs) <= set(passage_numbers):
        return fail('invalid', f'segments {segs} outside the passage {sorted(passage_numbers)}')
    verdict, judge, rule, ours = decide(flat)
    return dict(outcome='ok', verdict=verdict, features=flat, segments=segs, judge=judge, rule=rule,
                ours=ours, blocking=[b[0] for b in blocking(flat)],
                rules=[rule] if verdict != 'story' else [],   # what j.report counts as "rule cited"
                reasons={k: (feats[k].get('reason') if isinstance(feats[k], dict) else None) for k in FEATURES},
                error=None)


def run(backend_name, out_path, dry_run, workers):
    labels = json.loads((j.OUT_DIR / 'labels.json').read_text())
    units = j.select('full', labels)
    texts = {t: j.Text(t) for t in {u['tractate'] for u in units}}
    log.info('set=full units=%d backend=%s prompt=%s system_chars=%d',
             len(units), backend_name, prompt_sha(), len(system_prompt()))
    if dry_run:
        print(json.dumps({'calls': len(units), 'prompt_sha': prompt_sha(),
                          'system_tokens_est': round(len(system_prompt()) / 2.5)}, indent=1))
        return 0
    if backend_name != 'gemini':
        raise SystemExit('only gemini runs through the API here; Claude goes through export/import')
    j.load_env()
    system = system_prompt()
    prior = json.loads(out_path.read_text()) if out_path.exists() else None
    results = {r['id']: r for r in (prior or {}).get('rows', [])}
    meta = (prior or {}).get('meta') or {'prompt': str(PROMPT_PATH.relative_to(PROJECT_ROOT)),
                                          'prompt_sha': prompt_sha(), 'started': time.strftime('%Y-%m-%dT%H:%M:%S')}
    if meta['prompt_sha'] != prompt_sha():
        raise RuntimeError('prompt changed since this output was started -- use a new --out')
    call, info = j.gemini_backend()
    meta['backends'] = {'gemini': info}
    lock = threading.Lock()
    todo = [u for u in units if results.get(u['id'], {}).get('answers', {}).get('gemini', {}).get('outcome') in (None, 'failed')]

    def save():
        with lock:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps({'meta': meta, 'rows': list(results.values())}, ensure_ascii=False, indent=1) + '\n')

    def one(u):
        prompt, passage = j.user_prompt(u, texts[u['tractate']])
        ans = ask_panel(call, system, prompt, passage)
        with lock:
            results[u['id']] = {**{k: u[k] for k in ('id', 'kind', 'tractate', 'key', 'label', 'evidence',
                                                     'cited_in_rules', 'cells')}, 'answers': {'gemini': ans}}
        log.info('gemini %-40s his=%-12s -> %s %s %s', u['id'][:40], u['label'], ans['outcome'],
                 ans['verdict'], ans['judge'] or (ans['error'] or '')[:80])
    log.info('gemini: %d calls to make', len(todo))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for i, _ in enumerate(pool.map(one, todo), start=1):
            if i % 25 == 0:
                save()
    meta['finished'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    save()
    log.info('wrote %s: %s', out_path, dict(Counter(r['answers']['gemini']['outcome'] for r in results.values())))
    return 0


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

def _load(path, model):
    rows = json.loads(path.read_text())['rows']
    return {r['id']: r for r in rows}, model


def report():
    import compare_consensus_1b as c
    g, _ = _load(OUT_DIR / 'gemini.json', 'gemini')
    cl, _ = _load(OUT_DIR / 'claude.json', 'claude')
    ids = sorted(set(g) & set(cl))
    pv = {i: {'gemini': g[i]['answers']['gemini'], 'claude': cl[i]['answers']['claude']} for i in ids}
    rows = {i: g[i] for i in ids}
    ok = lambda a: a.get('outcome') == 'ok'
    vv = {i: {m: (pv[i][m]['verdict'] if ok(pv[i][m]) else None) for m in ('gemini', 'claude')} for i in ids}
    single, _ = c.verdicts(*SINGLE_LENS)
    out = {'outcomes': {m: dict(Counter(pv[i][m]['outcome'] for i in ids)) for m in ('gemini', 'claude')},
           'criteria_panel': c.criteria(vv, rows), 'criteria_single_lens_1b': c.criteria(single, rows)}

    # Per model: errors against his label, and the judge that decided each.
    LBL = j.LABEL_TO_VERDICT
    attr = {}
    for m in ('gemini', 'claude'):
        a = defaultdict(Counter)
        for i in ids:
            r, ans = rows[i], pv[i][m]
            if r['kind'] not in ('review', 'list') or not ok(ans):
                continue
            his = LBL.get(r['label'])
            if r['label'] in ('yes',) and ans['verdict'] in ('not',):
                a['his_yes_called_not'][f"{ans['judge']}{' (ours)' if ans['ours'] else ''}"] += 1
            if r['label'] == 'no' and ans['verdict'] == 'story':
                a['his_no_called_story']['(no row fired: every feature read as story)'] += 1
                for k in ('actual', 'event_beyond_speech', 'response_or_consequence'):
                    a['his_no_called_story_features_yes'][k] += ans['features'][k] == 'yes'
            a['matches_him'][str(ans['verdict'] == his)] += 1
        attr[m] = {k: dict(v.most_common()) for k, v in a.items()}
    out['attribution'] = attr

    # Agreed errors, with the deciding judges of both arms.
    agreed = {'his_yes_both_not': [], 'his_no_both_story': []}
    for i in ids:
        r = rows[i]
        if vv[i]['gemini'] and vv[i]['gemini'] == vv[i]['claude']:
            if r['label'] == 'yes' and vv[i]['gemini'] == 'not':
                agreed['his_yes_both_not'].append((i, pv[i]['gemini']['judge'], pv[i]['claude']['judge']))
            if r['label'] == 'no' and vv[i]['gemini'] == 'story':
                agreed['his_no_both_story'].append((i,))
    out['agreed_errors'] = agreed

    # Where the arms split: how many features differ? One differing feature = one question settles it.
    split_nfeat = Counter()
    feat_disagree = Counter()
    split_feats = Counter()
    for i in ids:
        if not (ok(pv[i]['gemini']) and ok(pv[i]['claude'])):
            continue
        fg, fc = pv[i]['gemini']['features'], pv[i]['claude']['features']
        diff = [k for k in FEATURES if fg[k] != fc[k]]
        for k in diff:
            feat_disagree[k] += 1
        if vv[i]['gemini'] != vv[i]['claude']:
            # only the features on either arm's decision path matter
            path = {pv[i]['gemini']['judge'], pv[i]['claude']['judge']} - {None}
            dpath = [k for k in diff if k in path] or diff
            split_nfeat[len(dpath)] += 1
            for k in dpath:
                split_feats[k] += 1
    out['feature_answers_differ_between_arms'] = dict(feat_disagree.most_common())
    out['splits_by_number_of_deciding_features_that_differ'] = dict(sorted(split_nfeat.items()))
    out['splits_deciding_feature'] = dict(split_feats.most_common())
    out['split_count'] = sum(split_nfeat.values())

    # Single lens vs panel, same model: which verdicts moved.
    moved = {}
    for m in ('gemini', 'claude'):
        mv = Counter()
        for i in ids:
            a, b = single.get(i, {}).get(m), vv[i][m]
            if a and b and a != b:
                mv[f'{rows[i]["kind"]}:{a}->{b}'] += 1
        moved[m] = dict(mv.most_common())
    out['single_to_panel_moved'] = moved
    (OUT_DIR / 'report.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(out, ensure_ascii=False, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run')
    r.add_argument('--backend', choices=('gemini',), required=True)
    r.add_argument('--out', required=True)
    r.add_argument('--dry-run', action='store_true')
    r.add_argument('--workers', type=int, default=6)
    e = sub.add_parser('export')
    e.add_argument('--run', required=True)
    e.add_argument('--seed', type=int, required=True)
    e.add_argument('--batch', type=int, default=25)
    i = sub.add_parser('import')
    i.add_argument('--run', required=True)
    i.add_argument('--model', required=True)
    sub.add_parser('report')
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [rule-panel] %(message)s',
                        handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'), logging.StreamHandler(sys.stdout)])
    for noisy in ('httpx', 'google_genai'):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    import judge_via_subagents as jv
    if args.cmd == 'run':
        return run(args.backend, Path(args.out), args.dry_run, args.workers)
    if args.cmd == 'export':
        return jv.export(args.run, args.seed, args.batch, system=system_prompt(), sha=prompt_sha(), work_dir=SUBAGENT_DIR)
    if args.cmd == 'import':
        return jv.import_(args.run, args.model, system=system_prompt(), sha=prompt_sha(), work_dir=SUBAGENT_DIR,
                          out_path=OUT_DIR / f'{args.run}.json', asker=ask_panel,
                          prompt_name=str(PROMPT_PATH.relative_to(PROJECT_ROOT)))
    if args.cmd == 'report':
        return report()


if __name__ == '__main__':
    sys.exit(main())
