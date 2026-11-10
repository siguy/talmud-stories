#!/usr/bin/env python3
"""The consensus judge on DETECTOR spans — for a tractate with no expert list.

judge_labelled_spans.py judges only spans Jeff labelled. This feeds the spans our
detector runs proposed through the SAME system prompt (`system_prompt()`), the SAME
per-span user prompt (`user_prompt()`, one context segment each side, ids never shown)
and the SAME answer validation (`ask()`). A failed or invalid answer is COUNTED, never
scored (Lesson 21). Written for docs/findings/2026-11-08-v14-vs-v11-berakhot.md.

UNITS. Every span any run proposed — `stories[]` AND `mishnah_stories[]`, any
classification including NOT_A_STORY — is a list of (ref, segment) cells; cross-page
stories carry their second page. Spans that share a cell are merged (transitively), and a
unit is the contiguous run of cells from the first to the last. Each unit is judged ONCE.
What each run said about a unit is the strongest call among its spans overlapping it:
YES/HIGH -> story, LOW -> borderline, NOT_A_STORY or not proposed -> not.
`mishnah_stories[]` (Stage 4g withheld it) is read, and reported as WITHHELD — it is not in
the catalogue, so for agreement it counts as `not`, separately flagged (CLAUDE.md table).

    JUDGE_PROMPT=src/prompts/judge_register_v2.md python3 scripts/judge_detector_spans.py units
    ... gemini --dry-run / gemini
    ... export --seed 1 --batch 20      # Claude Code subagents answer answers/<batch>.json
    ... import --model <what ran>
    ... report

Output under results/consensus/<tractate>/ (JUDGE_TRACTATE, default Berakhot). No Claude API call is ever made here.
"""
import argparse
import hashlib
import json
import logging
import os
import random
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
sys.path.insert(0, str(PROJECT_ROOT))
import judge_labelled_spans as j  # noqa: E402

log = logging.getLogger('judge-detector-spans')
# JUDGE_TRACTATE picks the tractate (default Berakhot, so the 2026-11-08 run reproduces). Any Bavli
# tractate works by convention (scripts/tractates.py): 'berakhot', 'Bava Batra' or 'bava_batra'.
# Text, runs and the output directory come from tractates.Paths; the two v14 runs are the judged
# versions. Berakhot also carries its v11 run, the comparison the 2026-11-08 finding reported.
# Eruvin was refused (held for Jeff) until Simon's 2026-11-09 decision to put it on the site.
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
import tractates as T  # noqa: E402


def tractate_config(name):
    """{'text', 'out', 'runs'} (repo-relative paths) for a tractate name or slug."""
    slug = T.resolve(name)
    P = T.Paths(slug, PROJECT_ROOT)
    rel = lambda p: str(p.relative_to(PROJECT_ROOT))
    runs = {'v14_r1': rel(P.run(1)), 'v14_r2': rel(P.run(2))}
    if slug == 'berakhot':
        runs = {'v11': 'results/v11/berakhot/berakhot_v11.json', **runs}
    return {'text': rel(P.text), 'out': rel(P.consensus), 'runs': runs}


_slug = T.resolve(os.environ.get('JUDGE_TRACTATE', 'Berakhot'))
TRACTATE = T.english(_slug)           # English name: it is in every ref and in every unit
TRACTATES = {TRACTATE: tractate_config(_slug)}
j.TEXT_SOURCES[TRACTATE] = [TRACTATES[TRACTATE]['text']]
OUT = PROJECT_ROOT / TRACTATES[TRACTATE]['out']
RUNS = TRACTATES[TRACTATE]['runs']
CALL = {'YES': 'story', 'HIGH_CONFIDENCE': 'story', 'LOW_CONFIDENCE': 'borderline', 'NOT_A_STORY': 'not'}
RANK = {'not': 0, 'borderline': 1, 'story': 2}
GEMINI_USD = {'input': 0.50, 'output': 3.00}   # per M tokens, docs/technical/shas-finder-plan.md
GEMINI_CAP_USD = 10.0


# ---- spans ----------------------------------------------------------------

def spans(run_path, text):
    """Every proposal in a run as a dict with its cells (a set of (ref, idx))."""
    d = json.loads((PROJECT_ROOT / run_path).read_text())
    out = []
    for p in d['pages']:
        for key in ('stories', 'mishnah_stories'):
            for s in p.get(key, []):
                first = (p['ref'], s['start_segment'])
                if s.get('spans_pages') and len(s['spans_pages']) > 1:
                    last = (s['spans_pages'][-1], s['end_segment_page2'])
                else:
                    last = (p['ref'], s['end_segment'])
                out.append(dict(ref=p['ref'], a=s['start_segment'], b=s['end_segment'],
                                cells=set(text.span_cells(first, last)),
                                call=CALL.get(s.get('classification'), '?'),
                                cls=s.get('classification'), withheld=key == 'mishnah_stories',
                                summary=s.get('one_sentence_summary', '')))
    return out


def run_call(unit_cells, run_spans):
    """(call, withheld?) of a run on a unit: the strongest overlapping span; none -> 'not'."""
    hit = [s for s in run_spans if s['cells'] & unit_cells]
    if not hit:
        return 'not', False, 'absent'
    kept = [s for s in hit if not s['withheld']]
    if kept:
        best = max(kept, key=lambda s: RANK[s['call']])
        return best['call'], False, best['cls']
    return 'not', True, 'WITHHELD'


def build_units():
    text = j.Text(TRACTATE)
    P = {k: spans(v, text) for k, v in RUNS.items()}
    allsp = [s for k in P for s in P[k]]
    # union-find on shared cells
    parent = list(range(len(allsp)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    owner = {}
    for i, s in enumerate(allsp):
        for c in s['cells']:
            if c in owner:
                parent[find(i)] = find(owner[c])
            else:
                owner[c] = i
    groups = {}
    for i in range(len(allsp)):
        groups.setdefault(find(i), []).append(i)
    units = []
    for idxs in groups.values():
        pos = [text.pos[c] for i in idxs for c in allsp[i]['cells']]
        cells = text.cells[min(pos):max(pos) + 1]
        cs = set(cells)
        calls = {}
        for k in P:
            c, w, cls = run_call(cs, P[k])
            calls[k] = {'call': c, 'withheld': w, 'cls': cls}
        first, last = cells[0], cells[-1]
        uid = f'{first[0]}:{first[1]}-' + (f'{last[1]}' if last[0] == first[0] else f'{last[0]}:{last[1]}')
        units.append({'id': uid, 'tractate': TRACTATE, 'cells': [list(c) for c in cells], 'calls': calls,
                      'summary': next((allsp[i]['summary'] for i in idxs if allsp[i]['summary']), '')})
    units.sort(key=lambda u: text.pos[tuple(u['cells'][0])])
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {'runs': RUNS, 'spans': {k: len(v) for k, v in P.items()}, 'units': len(units),
            'built': time.strftime('%Y-%m-%dT%H:%M:%S')}
    (OUT / 'units.json').write_text(json.dumps({'meta': meta, 'units': units}, ensure_ascii=False, indent=1) + '\n')
    log.info('units: %s spans -> %d units (source %s, %d records)', meta['spans'], len(units), TRACTATE, len(units))
    return units


def load_units():
    return json.loads((OUT / 'units.json').read_text())['units']


def prompt_meta():
    return {'prompt': str(j.PROMPT_PATH.relative_to(PROJECT_ROOT)), 'prompt_sha': j.prompt_sha(),
            'rules_sha': hashlib.sha256(j.RULES_PATH.read_bytes()).hexdigest()[:12]}


# ---- Gemini arm -------------------------------------------------------------

def gemini(dry_run, workers):
    units, text = load_units(), j.Text(TRACTATE)
    system = j.system_prompt()
    chars = [len(system) + len(j.user_prompt(u, text)[0]) for u in units]
    tok_in = sum(c / 2.5 for c in chars)           # Hebrew-heavy: conservative, as in estimate()
    usd = (tok_in * GEMINI_USD['input'] + len(units) * 400 * GEMINI_USD['output']) / 1e6
    est = {'calls': len(units), 'input_tokens_est': round(tok_in), 'usd_est': round(usd, 2), **prompt_meta()}
    log.info('gemini estimate %s', est)
    if dry_run:
        print(json.dumps(est, indent=1))
        return 0
    if usd > GEMINI_CAP_USD:
        log.error('projected $%.2f over the $%.0f cap -- refusing', usd, GEMINI_CAP_USD)
        return 3
    from dotenv import load_dotenv
    load_dotenv(j.ENV_PATH)
    call, info = j.gemini_backend()
    out_path = OUT / 'gemini.json'
    prior = json.loads(out_path.read_text()) if out_path.exists() else {}
    if prior and prior['meta']['prompt_sha'] != j.prompt_sha():
        raise RuntimeError('prompt changed since this output was started')
    rows = {r['id']: r for r in prior.get('rows', [])}
    todo = [u for u in units if rows.get(u['id'], {}).get('answer', {}).get('outcome') in (None, 'failed', 'invalid')]   # plan G6: one resume re-asks both
    log.info('gemini: %d calls to make', len(todo))

    def one(u):
        prompt, passage = j.user_prompt(u, text)
        return u, j.ask(call, system, prompt, passage)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for u, ans in pool.map(one, todo):
            rows[u['id']] = {'id': u['id'], 'answer': ans}
            log.info('gemini %-28s -> %s %s', u['id'], ans['outcome'], ans['verdict'] or ans['error'][:80])
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=PROJECT_ROOT, capture_output=True, text=True).stdout.strip()
    meta = {**prompt_meta(), 'backend': info, 'commit': commit, 'finished': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'outcomes': dict(Counter(r['answer']['outcome'] for r in rows.values()))}
    out_path.write_text(json.dumps({'meta': meta, 'rows': list(rows.values())}, ensure_ascii=False, indent=1) + '\n')
    log.info('wrote %s %s', out_path, meta['outcomes'])
    return 0


# ---- Claude arm (subagents; same layout as judge_via_subagents.py) -----------

def gemini_out_of_scope_ids():
    """Ids of the units Gemini answered `out_of_scope` (outcome ok). Refuses unless Gemini's answers
    are COMPLETE and valid: the Claude subset is only the whole story if Gemini's answers are final
    (a unit Gemini failed on would silently drop out of the subset and ship as 'not biblical')."""
    from check_tractate_run import g6_judge
    P = T.Paths(T.resolve(TRACTATE), PROJECT_ROOT)
    P.consensus = OUT                         # the directory this module is working in
    res = g6_judge(P, 'gemini')
    if res.status == 'red':
        raise SystemExit('refusing to export a Claude subset: the Gemini answers are not final (gate g6 red):\n  '
                         + '\n  '.join(res.failures))
    rows = json.loads((OUT / 'gemini.json').read_text())['rows']
    from check_tractate_run import claude_alone      # Simon's 2026-11-10 ruling: no valid Gemini answer -> Claude decides
    return ({r['id'] for r in rows if r['answer'].get('outcome') == 'ok' and r['answer'].get('verdict') == 'out_of_scope'}
            | claude_alone(P))


def export(seed, batch, only_gemini_out_of_scope=False):
    units, text = load_units(), j.Text(TRACTATE)
    d = OUT / 'subagent'
    if only_gemini_out_of_scope:
        # Claude's answer can change the site only where Gemini already said out_of_scope (a passage is
        # removed when BOTH do), so only those units go to the subagents: ~10 per tractate, not ~200.
        # It is exact only with Gemini's answers final and EVERY flagged unit answered: gate g6 and the
        # site build both refuse otherwise.
        if any((d / 'keys').glob('*.json')):
            raise SystemExit(f'{d / "keys"} already holds an export: move subagent/ aside first, a subset export '
                             'must not mix with an old one')
        flagged = gemini_out_of_scope_ids()
        units = [u for u in units if u['id'] in flagged]
        log.info('subset export: %d unit(s) Gemini called out_of_scope', len(units))
    order = list(units)
    random.Random(seed).shuffle(order)
    for sub in ('batches', 'keys', 'answers'):
        (d / sub).mkdir(parents=True, exist_ok=True)
    (d / 'system_prompt.md').write_text(j.system_prompt())
    n = 0
    sizes = []
    for i in range(0, len(order), batch):
        items = []
        for u in order[i:i + batch]:
            prompt, passage = j.user_prompt(u, text)
            items.append({'id': u['id'], 'prompt': prompt, 'passage': sorted(passage)})
        (d / 'keys' / f'{n:03d}.json').write_text(json.dumps(items, ensure_ascii=False, indent=1))
        sd = d / 'batches' / f'{n:03d}'
        sd.mkdir(exist_ok=True)
        for k, it in enumerate(items, start=1):     # numbered only: the id is never shown
            (sd / f'{k:02d}.txt').write_text(it['prompt'] + '\n')
            sizes.append(len((it['prompt'] + '\n').encode()))
        n += 1
    (d / 'manifest.json').write_text(json.dumps({
        'seed': seed, 'batch': batch, 'batches': n, 'units': len(order), **prompt_meta(),
        'only_gemini_out_of_scope': only_gemini_out_of_scope,
        'largest_file_bytes': max(sizes, default=0), 'files_over_30kb': sum(s > 30_000 for s in sizes),
        'exported': time.strftime('%Y-%m-%dT%H:%M:%S')}, indent=1))
    log.info('exported %d units into %d batches; largest file %d bytes', len(order), n, max(sizes, default=0))


def import_(model):
    d = OUT / 'subagent'
    man = json.loads((d / 'manifest.json').read_text())
    if man['prompt_sha'] != j.prompt_sha():
        raise RuntimeError('prompt changed since export -- re-export')
    system = j.system_prompt()
    rows, missing = [], []
    for bf in sorted((d / 'keys').glob('*.json')):
        items = json.loads(bf.read_text())
        af = d / 'answers' / bf.name
        raw = {}
        if af.exists():
            try:
                raw = json.loads(af.read_text())
            except json.JSONDecodeError as e:
                log.warning('batch %s unreadable (%s) -- every item counted invalid', bf.name, e)
                raw = {f'{k:02d}': f'<<unreadable: {e}>>' for k in range(1, len(items) + 1)}
        else:
            missing.append(bf.name)
        for k, it in enumerate(items, start=1):
            key = f'{k:02d}'
            if key in raw:
                a = raw[key]
                backend = lambda _s, _u, a=a: a if isinstance(a, str) else json.dumps(a, ensure_ascii=False)
            else:
                def backend(_s, _u):
                    raise RuntimeError('no answer from the subagent for this span')
            rows.append({'id': it['id'], 'answer': j.ask(backend, system, it['prompt'], set(it['passage']))})
    meta = {**prompt_meta(), 'backend': {'model': model, 'via': 'Claude Code subagent (Agent tool), not the API',
                                         'seed': man['seed'], 'batch': man['batch']},
            'subset': 'gemini_out_of_scope' if man.get('only_gemini_out_of_scope') else None,
            'missing_batches': missing, 'outcomes': dict(Counter(r['answer']['outcome'] for r in rows)),
            'imported': time.strftime('%Y-%m-%dT%H:%M:%S')}
    (OUT / 'claude.json').write_text(json.dumps({'meta': meta, 'rows': rows}, ensure_ascii=False, indent=1) + '\n')
    log.info('wrote claude.json %s; missing batches %s', meta['outcomes'], missing)


# ---- report -------------------------------------------------------------------

def judged(path):
    """id -> 'story'|'borderline'|'not', or None when the answer is not scoreable.
    out_of_scope -> 'not' (not in the catalogue, R-S1); unsure and failures -> None."""
    rows = json.loads(path.read_text())['rows']
    out = {}
    for r in rows:
        a = r['answer']
        v = a['verdict'] if a['outcome'] == 'ok' else None
        out[r['id']] = {'out_of_scope': 'not', 'unsure': None}.get(v, v)
    return out, Counter(r['answer']['outcome'] if r['answer']['outcome'] != 'ok' or r['answer']['verdict'] != 'unsure'
                        else 'unsure' for r in rows), {r['id']: r['answer'] for r in rows}


def report():
    units = {u['id']: u for u in load_units()}
    G, gout, gans = judged(OUT / 'gemini.json')
    C, cout, cans = judged(OUT / 'claude.json')
    res = {'units': len(units), 'outcomes': {'gemini': dict(gout), 'claude': dict(cout)}, **prompt_meta()}
    lines = [f"units {len(units)}; gemini outcomes {dict(gout)}; claude outcomes {dict(cout)}"]
    # per-version agreement, 3-way and kept-vs-not
    for run in RUNS:
        for name, J in (('gemini', G), ('claude', C)):
            ids = [i for i in units if J.get(i)]
            eq3 = sum(J[i] == units[i]['calls'][run]['call'] for i in ids)
            kept = lambda v: v != 'not'
            eq2 = sum(kept(J[i]) == kept(units[i]['calls'][run]['call']) for i in ids)
            conf = Counter((units[i]['calls'][run]['call'], J[i]) for i in ids)
            res.setdefault('agreement', {}).setdefault(run, {})[name] = {
                'n': len(ids), 'three_way': eq3, 'kept_vs_not': eq2,
                'confusion_version_to_judge': {f'{a}->{b}': n for (a, b), n in sorted(conf.items())}}
            lines.append(f"{run:7s} vs {name:6s}: 3-way {eq3}/{len(ids)} = {100*eq3/len(ids):.1f}%  "
                         f"kept-vs-not {eq2}/{len(ids)} = {100*eq2/len(ids):.1f}%  {dict(sorted(conf.items()))}")
    both = [i for i in units if G.get(i) and C.get(i)]
    jj = sum(G[i] == C[i] for i in both)
    jj2 = sum((G[i] != 'not') == (C[i] != 'not') for i in both)
    res['judges_agree'] = {'n': len(both), 'three_way': jj, 'kept_vs_not': jj2}
    lines.append(f"judges agree 3-way {jj}/{len(both)}; kept-vs-not {jj2}/{len(both)}")
    # judges agree with each other, disagree with a version (kept-vs-not)
    for run in RUNS:
        dis = [i for i in both if G[i] == C[i] and (G[i] != 'not') != (units[i]['calls'][run]['call'] != 'not')]
        res.setdefault('judges_vs_version', {})[run] = dis
        lines.append(f"== both judges agree, {run} differs (kept-vs-not): {len(dis)}")
        for i in dis:
            u = units[i]
            lines.append(f"  {i:26s} {run}={u['calls'][run]['cls']:15s} judges={G[i]}  "
                         f"G:{gans[i]['rules']} C:{cans[i]['rules']} | {u['summary'][:90]}")
    # moved passages (v11 vs v14 -- only where a v11 run was judged, i.e. Berakhot)
    moved = []
    for i, u in (units.items() if 'v11' in RUNS else ()):
        k11 = u['calls']['v11']['call'] != 'not'
        k14 = [u['calls'][r]['call'] != 'not' for r in ('v14_r1', 'v14_r2')]
        if k11 and not any(k14):
            moved.append((i, 'v11-only'))
        elif all(k14) and not k11:
            moved.append((i, 'v14-only'))
    lines.append(f"== moved passages: {len(moved)}")
    side = Counter()
    for i, tag in moved:
        u = units[i]
        for name, J in (('gemini', G), ('claude', C)):
            v = J.get(i)
            if v is None:
                side[(name, 'unscored')] += 1
            else:
                kept = v != 'not'
                side[(name, 'v11' if kept == (tag == 'v11-only') else 'v14')] += 1
        lines.append(f"  {i:26s} {tag:9s} v11={u['calls']['v11']['cls']} v14={u['calls']['v14_r1']['cls']},"
                     f"{u['calls']['v14_r2']['cls']}  gemini={G.get(i)} {gans.get(i, {}).get('rules')}  "
                     f"claude={C.get(i)} {cans.get(i, {}).get('rules')} | {u['summary'][:80]}")
    res['moved'] = [{'id': i, 'tag': t, 'gemini': G.get(i), 'claude': C.get(i),
                     'gemini_reason': gans.get(i, {}).get('reason'), 'claude_reason': cans.get(i, {}).get('reason')}
                    for i, t in moved]
    res['moved_sides'] = {f'{a}:{b}': n for (a, b), n in sorted(side.items())}
    lines.append(f"judges side with: {res['moved_sides']}")
    (OUT / 'report.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    (OUT / 'report.txt').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('units')
    g = sub.add_parser('gemini')
    g.add_argument('--dry-run', action='store_true')
    g.add_argument('--workers', type=int, default=6)
    e = sub.add_parser('export')
    e.add_argument('--seed', type=int, required=True)
    e.add_argument('--batch', type=int, default=20)
    e.add_argument('--only-gemini-out-of-scope', action='store_true',
                   help='export only the units Gemini called out_of_scope (needs final Gemini answers)')
    i = sub.add_parser('import')
    i.add_argument('--model', required=True)
    sub.add_parser('report')
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [judge-detector-spans] %(message)s',
                        handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'), logging.StreamHandler(sys.stdout)])
    if 'JUDGE_PROMPT' not in os.environ:
        raise SystemExit('set JUDGE_PROMPT explicitly (the module default is v1, kept for reproducibility)')
    if args.cmd == 'units':
        build_units()
    elif args.cmd == 'gemini':
        return gemini(args.dry_run, args.workers)
    elif args.cmd == 'export':
        export(args.seed, args.batch, args.only_gemini_out_of_scope)
    elif args.cmd == 'import':
        import_(args.model)
    else:
        report()


if __name__ == '__main__':
    sys.exit(main())
