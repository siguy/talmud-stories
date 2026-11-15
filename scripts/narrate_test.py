#!/usr/bin/env python3
"""The narrate test: is writing a summary a judge of story-ness and of story borders?

work/2026-11-14-narrate-test.md. A narrator (src/prompts/narrate_v1.md -- deliberately WITHOUT
docs/STORY_RULES.md) is shown a passage with 3 segments of context each side and says whether it can
retell it as a story (`can_narrate` yes|partial|no) and which segments it needed (`needed_segments`).

Two sets, mixed in the same batches so the narrator cannot tell them apart:
  CLS  the 300-span calibration manifest (results/shas_run/low_pool/calibration/manifest.json).
       `can_narrate` is scored against Jeff (borderline = not a story, the site rule) and cross-tabbed
       against the rule-based grader's two passes. C1 is CIRCULAR, C2 (Eruvin/Yevamot) is BLIND.
  BND  one unit per detector story (results/v10/wave4_notrim) that covers a blind 2005 boundary target
       (tests/expert_boundary_targets_2005{,_kiddushin}.json). Predicted start/end = min/max of
       `needed_segments`. Scored by scripts/score_boundary_targets.py's own score() beside the
       detector, on the SAME targets. BLIND throughout.

    python3 scripts/narrate_test.py build
    python3 scripts/narrate_test.py export --pass pass1 --seed 1 --batch 20
    #  narrators write <pass>/answers/<NNN>.json  ({"01": {...}, "02": {...}})
    python3 scripts/narrate_test.py import --pass pass1 --model <what ran>
    python3 scripts/narrate_test.py score

No model is ever called here. Never reads STORY_RULES.md; span ids live only in keys/.
"""
import argparse
import hashlib
import json
import logging
import random
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
sys.path.insert(0, str(PROJECT_ROOT))
import calibrate_low_pool_grader as cal  # noqa: E402  (also points j.TEXT_SOURCES at Eruvin/Yevamot)
import judge_labelled_spans as j  # noqa: E402
import score_boundary_targets as sbt  # noqa: E402

log = logging.getLogger('narrate-test')
OUT = PROJECT_ROOT / 'results/shas_run/narrate_test'
PROMPT_PATH = PROJECT_ROOT / 'src/prompts/narrate_v1.md'
CONTEXT = 3
CAN = ('yes', 'partial', 'no')
RUNS = {  # the detector's own honest outputs (CLAUDE.md: results/v10/wave4_notrim)
    'ketubot': ['results/v10/wave4_notrim/ketubot_v10_2-60_notrim.json',
                'results/v10/wave4_notrim/ketubot_v10_61-112_notrim.json'],
    'kiddushin': ['results/v10/wave4_notrim/kiddushin_v10_notrim.json']}
TARGETS = {'ketubot': 'tests/expert_boundary_targets_2005.json',
           'kiddushin': 'tests/expert_boundary_targets_2005_kiddushin.json'}


def system_prompt():
    return PROMPT_PATH.read_text()


def prompt_sha():
    return hashlib.sha256(system_prompt().encode()).hexdigest()[:12]


# ---- pure logic (tested) -------------------------------------------------------

def window(text, cells, context=CONTEXT):
    """(shown cells, {bracket number: cell}, passage numbers) for a passage with `context` cells each side."""
    cells = [tuple(c) for c in cells]
    a, b = text.pos[cells[0]], text.pos[cells[-1]]
    lo, hi = max(0, a - context), min(len(text.cells) - 1, b + context)
    shown = text.cells[lo:hi + 1]
    numbered = {n: c for n, c in enumerate(shown, start=1)}
    passage = {n for n, c in numbered.items() if text.pos[c] >= a and text.pos[c] <= b}
    return shown, numbered, passage


def user_prompt(text, cells):
    shown, numbered, passage = window(text, cells)
    parts = []
    for n, cell in numbered.items():
        seg = text.seg[cell]
        role = 'PASSAGE' if n in passage else 'CONTEXT'
        parts.append(f'[{n}] {role} -- {cell[0]}\nHebrew/Aramaic: {seg.get("hebrew", "").strip()}\n'
                     f'English: {seg.get("english", "").strip()}')
    head = (f'The PASSAGE is segments [{min(passage)}] to [{max(passage)}] below; the rest is CONTEXT. '
            f'Answer `needed_segments` with these bracketed numbers.')
    return head + '\n\n' + '\n\n'.join(parts), passage, sorted(numbered)


def validate(ans, shown_numbers):
    """Answer dict -> (clean dict | None, error | None). A malformed answer is COUNTED, never scored (Lesson 21)."""
    if not isinstance(ans, dict):
        return None, f'not an object: {type(ans).__name__}'
    can = ans.get('can_narrate')
    if can not in CAN:
        return None, f'can_narrate {can!r}'
    need = ans.get('needed_segments')
    if not isinstance(need, list) or not all(isinstance(x, int) and not isinstance(x, bool) for x in need):
        return None, 'needed_segments not a list of ints'
    if any(x not in shown_numbers for x in need):
        return None, f'needed_segments {need} outside shown {shown_numbers[0]}-{shown_numbers[-1]}'
    if can != 'no' and not need:
        return None, f'{can} but no needed_segments'
    for k in ('actor', 'event', 'turn', 'outcome', 'summary', 'missing'):
        if not isinstance(ans.get(k, ''), str):
            return None, f'{k} not a string'
    return {**ans, 'needed_segments': sorted(set(need))}, None


def predicted_span(numbered, need):
    """(first cell, last cell) of the narrator's needed segments -- min and max, as the work item says."""
    return numbered[min(need)], numbered[max(need)]


def verdict_class(narr):
    """Narrator answer -> 'yes' | 'partial' | 'no' | None (invalid)."""
    return narr['answer']['can_narrate'] if narr and narr['outcome'] == 'ok' else None


def combined_rule(grader, narrate_yes):
    """grader story OR (narrate yes AND grader borderline): the second-judge rule of the work item."""
    return grader == 'story' or (narrate_yes and grader == 'borderline')


def grader_class(v1, v2):
    """Rule grader's two passes -> story (both say story) | borderline (not story, either borderline) | not."""
    if v1 == 'story' and v2 == 'story':
        return 'story'
    return 'borderline' if 'borderline' in (v1, v2) else 'not'


def precision_recall(rows):
    """rows: [(called_story: bool, truth)] -> (k, called_known, n_yes_total, unknown_called)."""
    k = sum(c and t == 'yes' for c, t in rows)
    called = sum(c and t in ('yes', 'borderline', 'no') for c, t in rows)
    return k, called, sum(t == 'yes' for _, t in rows), sum(c and t == 'unknown' for c, t in rows)


# ---- boundary units ---------------------------------------------------------------

def detector_stories(slug):
    """[(ref, story, first cell, last cell)] for the detector's non-NOT_A_STORY stories (cross-page aware)."""
    out = []
    for rel in RUNS[slug]:
        for p in json.loads((PROJECT_ROOT / rel).read_text())['pages']:
            for s in p.get('stories', []):
                if s.get('classification') == 'NOT_A_STORY':
                    continue
                multi = s.get('spans_pages') and len(s['spans_pages']) > 1
                last = (s['spans_pages'][-1], s['end_segment_page2']) if multi else (p['ref'], s['end_segment'])
                out.append((p['ref'], s, (p['ref'], s['start_segment']), last))
    return out


def boundary_units(slug, text):
    """One unit per detector story that covers at least one scorable target of the blind list."""
    targets = [t for t in json.loads((PROJECT_ROOT / TARGETS[slug]).read_text())['targets'] if not t.get('needs_human')]
    stories = detector_stories(slug)
    units = {}
    for i, t in enumerate(targets):
        ref, seg = t.get('located_on') or t['ref'], t['segment']
        cover = next((x for x in stories if x[0] == ref and x[1]['start_segment'] <= seg <= x[1]['end_segment']), None)
        if cover is None:
            continue          # the detector found nothing there: N/A for it, and no card to narrate
        cells = text.span_cells(cover[2], cover[3])
        uid = f'B:{slug}:{cover[2][0]}:{cover[2][1]}-{cover[3][0]}:{cover[3][1]}'
        u = units.setdefault(uid, dict(id=uid, set='BND', evidence='BLIND', tractate=text_name(slug),
                                       slug=slug, cells=[list(c) for c in cells], targets=[]))
        u['targets'].append(i)
    log.info('%s: %d scorable targets, %d detector stories to narrate', slug, len(targets), len(units))
    return list(units.values())


def text_name(slug):
    return {'ketubot': 'Ketubot', 'kiddushin': 'Kiddushin'}[slug]


def build():
    cm = json.loads((PROJECT_ROOT / 'results/shas_run/low_pool/calibration/manifest.json').read_text())['spans']
    cls = [dict(id=s['id'], set='CLS', cal_set=s['set'], evidence=s['evidence'], tractate=s['tractate'],
                cells=s['cells'], truth=s['truth'], tags=s['tags']) for s in cm]
    units = list(cls)
    for slug in ('ketubot', 'kiddushin'):
        units += boundary_units(slug, j.Text(text_name(slug)))
    ids = [u['id'] for u in units]
    assert len(ids) == len(set(ids)), 'duplicate unit ids'
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {'what': __doc__.split('\n\n')[0], 'prompt': 'src/prompts/narrate_v1.md', 'prompt_sha': prompt_sha(),
            'context_segments': CONTEXT, 'counts': dict(Counter(u['set'] for u in units)),
            'built': time.strftime('%Y-%m-%dT%H:%M:%S')}
    (OUT / 'manifest.json').write_text(json.dumps({'meta': meta, 'units': units}, ensure_ascii=False, indent=1) + '\n')
    log.info('manifest: %s', meta['counts'])


def load_manifest():
    return json.loads((OUT / 'manifest.json').read_text())['units']


_TEXTS = {}


def text_for(tractate):
    if tractate not in _TEXTS:
        _TEXTS[tractate] = j.Text(tractate)
    return _TEXTS[tractate]


# ---- export / import ----------------------------------------------------------------

def export(pass_name, seed, batch):
    units = load_manifest()
    d = OUT / pass_name
    if (d / 'keys').exists():
        raise SystemExit(f'{d} already holds an export')
    for sub in ('batches', 'keys', 'answers'):
        (d / sub).mkdir(parents=True, exist_ok=True)
    (d / 'system_prompt.md').write_text(system_prompt())
    order = list(units)
    random.Random(seed).shuffle(order)
    sizes, n = {}, 0
    for i in range(0, len(order), batch):
        items = []
        for u in order[i:i + batch]:
            prompt, passage, shown = user_prompt(text_for(u['tractate']), u['cells'])
            items.append({'id': u['id'], 'passage': sorted(passage), 'shown': shown, 'prompt': prompt})
        (d / 'keys' / f'{n:03d}.json').write_text(json.dumps(items, ensure_ascii=False, indent=1))
        sd = d / 'batches' / f'{n:03d}'
        sd.mkdir(exist_ok=True)
        for k, it in enumerate(items, start=1):
            (sd / f'{k:02d}.txt').write_text(it['prompt'] + '\n')
            sizes[f'{n:03d}/{k:02d}'] = len(it['prompt'].encode())
        n += 1
    (d / 'export_manifest.json').write_text(json.dumps({
        'pass': pass_name, 'seed': seed, 'batch': batch, 'batches': n, 'units': len(order),
        'prompt_sha': prompt_sha(), 'largest_file_bytes': max(sizes.values()),
        'files_over_30kb': {k: v for k, v in sizes.items() if v > 30_000},
        'exported': time.strftime('%Y-%m-%dT%H:%M:%S')}, indent=1))
    log.info('%s: %d units in %d batches; largest %d bytes', pass_name, len(order), n, max(sizes.values()))


def import_(pass_name, model):
    d = OUT / pass_name
    man = json.loads((d / 'export_manifest.json').read_text())
    if man['prompt_sha'] != prompt_sha():
        raise SystemExit('prompt changed since export -- re-export')
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
            if key not in raw:
                rows.append({'id': it['id'], 'outcome': 'missing', 'error': 'no answer', 'answer': None})
                continue
            clean, err = validate(raw[key], it['shown'])
            rows.append({'id': it['id'], 'outcome': 'ok' if clean else 'invalid', 'error': err, 'answer': clean})
    meta = {'pass': pass_name, 'prompt_sha': man['prompt_sha'],
            'backend': {'model': model, 'via': 'Claude Code subagent (Agent tool), not the API',
                        'seed': man['seed'], 'batch': man['batch']},
            'missing_batches': missing, 'outcomes': dict(Counter(r['outcome'] for r in rows)),
            'imported': time.strftime('%Y-%m-%dT%H:%M:%S')}
    (d / 'narrate.json').write_text(json.dumps({'meta': meta, 'rows': rows}, ensure_ascii=False, indent=1) + '\n')
    log.info('%s: %s; missing batches %s', pass_name, meta['outcomes'], missing)


# ---- score: classification -------------------------------------------------------------

def narrations(pass_name):
    rows = json.loads((OUT / pass_name / 'narrate.json').read_text())['rows']
    return {r['id']: r for r in rows}


def grader_classes():
    G = {}
    for p in ('pass1', 'pass2'):
        rows = json.loads((cal.OUT / p / 'claude.json').read_text())['rows']
        G[p] = {r['id']: (r['answer']['verdict'] if r['answer']['outcome'] == 'ok' else None) for r in rows}
    return {i: grader_class(G['pass1'].get(i), G['pass2'].get(i)) for i in G['pass1']}


def fmt(k, n):
    w = cal.wilson(k, n)
    return f'{k}/{n} = {k / n:.3f} wilson {w}' if n else f'{k}/{n}'


def score_classification(passes, units, res, lines):
    cls = [u for u in units if u['set'] == 'CLS']
    grader = grader_classes()
    groups = {'all known': lambda u: True, 'C1 CIRCULAR': lambda u: u['cal_set'] == 'C1',
              'C1 jeff_shown_low': lambda u: 'jeff_shown_low' in u['tags'],
              'C1 golden_low_on_list': lambda u: 'golden_low_on_list' in u['tags'],
              'C2 BLIND': lambda u: u['cal_set'] == 'C2'}
    N = {p: narrations(p) for p in passes}
    cn = {p: {u['id']: verdict_class(N[p].get(f'{u["id"]}')) for u in cls} for p in passes}
    cn_both = ({u['id']: ('yes' if all(cn[p][u['id']] == 'yes' for p in passes) else 'other') for u in cls}
               if len(passes) == 2 else None)
    arms = {}
    for p in passes:
        arms[f'{p} yes'] = lambda u, p=p: cn[p][u['id']] == 'yes'
        arms[f'{p} yes|partial'] = lambda u, p=p: cn[p][u['id']] in ('yes', 'partial')
    if cn_both:
        arms['both passes yes'] = lambda u: cn_both[u['id']] == 'yes'
    arms['GRADER story (both passes)'] = lambda u: grader[u['id']] == 'story'
    for p in passes:
        arms[f'COMBINED {p}'] = lambda u, p=p: combined_rule(grader[u['id']], cn[p][u['id']] == 'yes')
    if cn_both:
        arms['COMBINED both'] = lambda u: combined_rule(grader[u['id']], cn_both[u['id']] == 'yes')
    res['classification'] = {}
    for arm, f in arms.items():
        for g, gf in groups.items():
            sel = [u for u in cls if gf(u)]
            k, called, n_yes, unk = precision_recall([(f(u), u['truth']) for u in sel])
            prec = round(k / called, 3) if called else None
            res['classification'].setdefault(arm, {})[g] = {
                'story_called_known': called, 'jeff_yes': k, 'precision': prec, 'wilson95': cal.wilson(k, called),
                'recall_of_jeff_yes': f'{k}/{n_yes}', 'recall_wilson95': cal.wilson(k, n_yes),
                'called_story_unknown_truth': unk}
            lines.append(f'{arm:28s} {g:22s} precision {fmt(k, called)}; recall {fmt(k, n_yes)}; +{unk} unknown')
    # cross-tab narrate (pass) x grader class x truth, on all known spans
    res['crosstab'] = {}
    for p in passes:
        tab = Counter((grader[u['id']], cn[p][u['id']] or 'invalid', u['truth']) for u in cls)
        res['crosstab'][p] = {f'{a}|{b}|{c}': n for (a, b, c), n in sorted(tab.items())}
        # the borderline-grader rescue: of grader-borderline spans, what does narrating do
        bl = [u for u in cls if grader[u['id']] == 'borderline']
        for want in ('yes', 'partial', 'no'):
            sub = [u for u in bl if cn[p][u['id']] == want]
            c = Counter(u['truth'] for u in sub)
            lines.append(f'{p} grader-borderline & narrate {want:7s}: {len(sub)} spans; truth {dict(c)}')
    res['invalid'] = {p: dict(Counter(r['outcome'] for i, r in N[p].items() if i in {u['id'] for u in cls}))
                      for p in passes}
    if len(passes) == 2:
        both = [u['id'] for u in cls if cn['pass1'][u['id']] and cn['pass2'][u['id']]]
        res['stability_cls'] = {'n': len(both), 'same_can_narrate': sum(cn['pass1'][i] == cn['pass2'][i] for i in both),
                                'same_yes_or_not': sum((cn['pass1'][i] == 'yes') == (cn['pass2'][i] == 'yes') for i in both)}
        lines.append(f'classification stability: {res["stability_cls"]}')


# ---- score: boundaries -------------------------------------------------------------------

def write_detector_run(slug, path):
    pages = []
    for rel in RUNS[slug]:
        pages += json.loads((PROJECT_ROOT / rel).read_text())['pages']
    Path(path).write_text(json.dumps({'pages': pages}, ensure_ascii=False))
    return pages


def narrator_run(slug, pages, units, nar):
    """A run file in the detector's own shape: one story per usable narration, start/end = min/max needed."""
    last_seg = {p['ref']: max(s['index'] for s in p['segments']) for p in pages}
    stories = {p['ref']: [] for p in pages}
    for u in units:
        r = nar.get(u['id'])
        if verdict_class(r) in (None, 'no'):
            continue
        _, numbered, _ = window(text_for(text_name(slug)), u['cells'])
        a, b = predicted_span(numbered, r['answer']['needed_segments'])
        # Mirrors how the detector's cross-page stories are stored: the first page carries the story and the
        # second page's end is not a covering story, so a target there is N/A for both runs, not scored.
        end = b[1] if a[0] == b[0] else last_seg[a[0]]
        stories[a[0]].append({'start_segment': a[1], 'end_segment': end, 'classification': 'YES'})
    return {'pages': [{'ref': p['ref'], 'segments': p['segments'], 'stories': stories[p['ref']]} for p in pages]}


def score_boundaries(passes, units, res, lines):
    res['boundaries'] = {}
    for slug in ('ketubot', 'kiddushin'):
        targets = [t for t in json.loads((PROJECT_ROOT / TARGETS[slug]).read_text())['targets']
                   if not t.get('needs_human')]
        bu = [u for u in units if u['set'] == 'BND' and u['slug'] == slug]
        with tempfile.TemporaryDirectory() as tmp:
            det_path = str(Path(tmp) / 'det.json')
            pages = write_detector_run(slug, det_path)
            all_idx = sorted({i for u in bu for i in u['targets']})
            scored_sets = {'detector, all covered targets': (det_path, all_idx)}
            for p in passes:
                nar = narrations(p)
                usable = sorted({i for u in bu if verdict_class(nar.get(u['id'])) not in (None, 'no')
                                 for i in u['targets']})
                npath = str(Path(tmp) / f'{p}.json')
                Path(npath).write_text(json.dumps(narrator_run(slug, pages, bu, nar), ensure_ascii=False))
                scored_sets[f'{p} narrator'] = (npath, usable)
                scored_sets[f'{p} detector, same targets'] = (det_path, usable)
                scored_sets[f'{p} narrator, all covered (no-narrate = N/A)'] = (npath, all_idx)
            out = {}
            for name, (path, idx) in scored_sets.items():
                c, rows = sbt.score(path, [targets[i] for i in idx])
                per = {}
                for d in ('start', 'end'):
                    cc = Counter(r[5] for r in rows if r[2] == d)
                    s = cc['HIT'] + cc['NEAR'] + cc['MISS']
                    per[d] = {'scored': s, 'HIT': cc['HIT'], 'NEAR': cc['NEAR'], 'MISS': cc['MISS'], 'N/A': cc['N/A'],
                              'hit_rate': round(cc['HIT'] / s, 3) if s else None,
                              'hit_near_rate': round((cc['HIT'] + cc['NEAR']) / s, 3) if s else None,
                              'hit_wilson95': cal.wilson(cc['HIT'], s)}
                    lines.append(f'{slug:9s} {name:50s} {d:5s} scored {s:3d} HIT {cc["HIT"]:3d} NEAR {cc["NEAR"]:3d} '
                                 f'MISS {cc["MISS"]:3d} N/A {cc["N/A"]:3d} hit {per[d]["hit_rate"]} '
                                 f'hit+near {per[d]["hit_near_rate"]}')
                out[name] = per
                if name.endswith('narrator') or name.endswith('same targets'):
                    out.setdefault('_rows', {})[name] = [(r[0], r[1], r[2], r[5]) for r in rows]
            # movement: of the targets both runs score, who flips (narrator vs detector on the same targets)
            for p in passes:
                dr = {(r[0], r[1], r[2]): r[3] for r in out['_rows'][f'{p} detector, same targets']}
                nr = {(r[0], r[1], r[2]): r[3] for r in out['_rows'][f'{p} narrator']}
                for d in ('start', 'end'):
                    mv = Counter((dr[k], nr[k]) for k in dr if k[2] == d and k in nr)
                    out.setdefault('movement', {}).setdefault(p, {})[d] = {f'{a}->{b}': n for (a, b), n in sorted(mv.items())}
                    lines.append(f'{slug:9s} {p} {d} detector->narrator on same targets: '
                                 f'{dict(sorted(mv.items()))}')
            out.pop('_rows')
            # ceiling: how many targets lie inside the window at all (the narrator cannot reach outside it)
            tx = text_for(text_name(slug))
            inside = Counter()
            for u in bu:
                _, numbered, _ = window(tx, u['cells'])
                cells = set(numbered.values())
                for i in u['targets']:
                    t = targets[i]
                    inside[t['direction'], (t.get('located_on') or t['ref'], t['segment']) in cells] += 1
            out['target_inside_window'] = {f'{d}|{k}': n for (d, k), n in sorted(inside.items())}
            res['boundaries'][slug] = out
            lines.append(f'{slug:9s} target inside the +-{CONTEXT} window: {out["target_inside_window"]}')
        usable_n = {p: Counter(verdict_class(narrations(p).get(u['id'])) for u in bu) for p in passes}
        res['boundaries'][slug]['narration_outcomes'] = {p: {str(k): v for k, v in c.items()} for p, c in usable_n.items()}
        lines.append(f'{slug:9s} units {len(bu)}; narration outcomes {res["boundaries"][slug]["narration_outcomes"]}')


def score():
    units = load_manifest()
    passes = [p for p in ('pass1', 'pass2') if (OUT / p / 'narrate.json').exists()]
    res, lines = {'passes': passes}, []
    score_classification(passes, units, res, lines)
    score_boundaries(passes, units, res, lines)
    (OUT / 'score.json').write_text(json.dumps(res, indent=1) + '\n')
    print('\n'.join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('build')
    e = sub.add_parser('export')
    e.add_argument('--pass', dest='pass_name', required=True, choices=('pass1', 'pass2'))
    e.add_argument('--seed', type=int, required=True)
    e.add_argument('--batch', type=int, default=20)
    i = sub.add_parser('import')
    i.add_argument('--pass', dest='pass_name', required=True, choices=('pass1', 'pass2'))
    i.add_argument('--model', required=True)
    sub.add_parser('score')
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [narrate-test] %(message)s',
                        handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'), logging.StreamHandler(sys.stdout)])
    if args.cmd == 'build':
        build()
    elif args.cmd == 'export':
        export(args.pass_name, args.seed, args.batch)
    elif args.cmd == 'import':
        import_(args.pass_name, args.model)
    else:
        score()


if __name__ == '__main__':
    main()
