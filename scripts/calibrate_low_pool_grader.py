#!/usr/bin/env python3
"""Calibrate the Claude story grader on spans Jeff has ruled on, before it may promote LOW proposals.

work/2026-11-13-low-pool-grader-calibration.md. The question: when the Claude grader (the consensus
judge's prompt, src/prompts/judge_register_v2.md, the sha pinned as JUDGE_PROMPT_SHA in
check_tractate_run.py) calls a detector-LOW span a `story`, is Jeff's answer yes often enough to ship
it on the Septimus site (definite stories only)? Jeff `borderline` counts as NOT a story here.

The set, written to results/shas_run/low_pool/calibration/manifest.json:
  C1  CIRCULAR -- Ketubot / Kiddushin / Gittin passages the detector SHOWED Jeff as LOW_CONFIDENCE; truth is
      his last verdict on each (the same reading as measure_site_misses.ruler_low_verdicts). Plus the golden
      LOW stories that carry a counted story on his 2005 list the site misses for that grade (the "60" of
      docs/findings/2026-11-13-how-many-stories-we-miss.md), tagged `golden_low_on_list`; truth = the list
      (yes), or his verdict where he gave one on that very span.
  C2  BLIND -- Eruvin + Yevamot v14 units (results/consensus/<t>/units.json) that are LOW in at least one run
      or split between runs, and not already on the site (pools P1-P4 of measure_site_misses). Truth from his
      2005 list as annotated by superseded_by_rule.json: overlaps a counted story -> yes; a story he has since
      ruled borderline -> borderline; one he ruled not -> no; nothing -> unknown (a lower bound only).

Prompts are built by the judge's own user_prompt() / system_prompt() and answers validated by its ask(),
in the batch layout of judge_via_subagents.py (that script's export reads only labels.json, which has
neither Eruvin nor detector units, so this one writes the same layout itself). Span ids never reach a
grader: batches/ holds numbered text files only; keys/ maps numbers back to ids.

    JUDGE_PROMPT=src/prompts/judge_register_v2.md python3 scripts/calibrate_low_pool_grader.py build
    JUDGE_PROMPT=... python3 scripts/calibrate_low_pool_grader.py export --pass pass1 --seed 1 --batch 20
    JUDGE_PROMPT=... python3 scripts/calibrate_low_pool_grader.py export --pass pass2 --seed 2 --batch 20
    #  graders write <pass>/answers/<NNN>.json
    JUDGE_PROMPT=... python3 scripts/calibrate_low_pool_grader.py import --pass pass1 --model <what ran>
    JUDGE_PROMPT=... python3 scripts/calibrate_low_pool_grader.py score

No model is ever called here.
"""
import argparse
import hashlib
import json
import logging
import math
import os
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
sys.path.insert(0, str(PROJECT_ROOT))
import judge_labelled_spans as j  # noqa: E402
import tractates as T  # noqa: E402
from check_tractate_run import JUDGE_PROMPT_SHA  # noqa: E402

log = logging.getLogger('low-pool-calibration')
OUT = PROJECT_ROOT / 'results/shas_run/low_pool/calibration'
DEFINITE = ('YES', 'HIGH_CONFIDENCE')
LOWISH = ('LOW_CONFIDENCE', 'BORDERLINE')
SHIP_PRECISION, SHIP_WILSON_LOW = 0.90, 0.80

# C2 text is what the Shas judge read (judge_detector_spans sets the same), so a C2 prompt here is
# byte-identical to the one the Shas run sent for that unit.
for _slug in ('eruvin', 'yevamot'):
    j.TEXT_SOURCES[T.english(_slug)] = [str(T.Paths(_slug, PROJECT_ROOT).text.relative_to(PROJECT_ROOT))]


def load(rel):
    return json.loads((PROJECT_ROOT / rel).read_text())


def key_cells(key):
    ref, rng = key.rsplit('_', 1)
    lo, hi = (int(x) for x in rng.split('-'))
    return [(ref, i) for i in range(lo, hi + 1)]


def list_stories(slug, text):
    """[(cells set, truth)] for every located story on his 2005 list, truth read through his later rulings."""
    out = []
    for s in load(f'results/recall/{slug}_jeff2005_matches.json'):
        if not s.get('located'):
            continue
        ruling = (s.get('superseded_by_rule') or {}).get('ruling')
        truth = ('no' if not s.get('counts_for_recall', True) else 'borderline' if ruling == 'borderline' else 'yes')
        out.append((set(text.span_cells(*[tuple(c) for c in s['located']])), truth, s.get('id')))
    return out


def list_truth(cells, stories):
    hit = [(t, i) for c, t, i in stories if c & cells]
    for t in ('yes', 'borderline', 'no'):
        if any(x == t for x, _ in hit):
            return t, sorted(i for x, i in hit if x == t)
    return 'unknown', []


# ---- C1 -------------------------------------------------------------------

def c1_rows():
    """Jeff's last verdict on each passage he was shown as LOW_CONFIDENCE (measure_site_misses.ruler_low_verdicts)."""
    rows = {}
    for slug in ('ketubot', 'kiddushin', 'gittin'):
        for e in load(f'results/rulers/{slug}_ruler.json')['entries']:
            vs = []
            for v in e.get('verdicts', []):
                if 'simon' in v.get('round', ''):
                    continue
                shown = v.get('shown') or ((e.get('detector_classification') or [None])[0]
                                           if v.get('applies_to') == 'base' else None)
                if shown == 'LOW_CONFIDENCE':
                    vs.append(v)
            if not vs:
                continue
            v = vs[-1]
            truth = {'out_of_scope': 'no'}.get(v['read_as'], v['read_as'])
            if truth not in ('yes', 'no', 'borderline', 'unknown'):
                raise ValueError(f'{slug} {v["key"]}: unreadable verdict {v["read_as"]!r}')
            tags = ['jeff_shown_low'] + (['out_of_scope'] if v['read_as'] == 'out_of_scope' else []) \
                + (['expert_listed'] if e.get('expert_listed') else [])
            rows[v['key']] = dict(id=f'C1:{v["key"]}', tractate=T.english(slug), ref=v['key'].rsplit('_', 1)[0],
                                  cells=[list(c) for c in key_cells(v['key'])], set='C1', evidence='CIRCULAR',
                                  truth=truth, truth_source=f'Jeff verdict {v["verdict"]!r} ({v["round"]})',
                                  detector_confidence={'shown_to_jeff': 'LOW_CONFIDENCE'}, tags=tags)
    return rows


def golden_low_rows(c1, texts):
    """Golden LOW stories carrying a counted list story the site misses at that grade (the finding's 60)."""
    misses = load('results/shas_run/accuracy/site_misses.json')['stages']
    rows, n_list = {}, Counter()
    for slug in ('ketubot', 'kiddushin'):
        text = texts[T.english(slug)]
        stories = list_stories(slug, text)
        low = []
        for p in load(f'results/canonical/{slug}_canonical.json')['pages']:
            for s in p.get('stories', []):
                if s.get('classification') != 'LOW_CONFIDENCE':
                    continue
                first = (p['ref'], s['start_segment'])
                last = ((s['spans_pages'][-1], s['end_segment_page2'])
                        if s.get('spans_pages') and len(s['spans_pages']) > 1 else (p['ref'], s['end_segment']))
                low.append(text.span_cells(first, last))
        for m in misses[slug]['misses']:
            if m['site'] != 'site filter: LOW (or BORDERLINE) wherever proposed':
                continue
            w = {tuple(c) for c in m['cells']}
            hits = [cs for cs in low if set(cs) & w]
            if not hits:
                continue                      # BORDERLINE in the golden: his own answer, stays off (finding)
            n_list[slug] += 1
            for cs in hits:
                k = f'{cs[0][0]}_{cs[0][1]}-{cs[-1][1]}' if cs[0][0] == cs[-1][0] else None
                if k and k in c1:
                    if 'golden_low_on_list' not in c1[k]['tags']:
                        c1[k]['tags'].append('golden_low_on_list')
                    continue
                uid = f'C1:golden:{cs[0][0]}:{cs[0][1]}-{cs[-1][0]}:{cs[-1][1]}'
                if uid in rows:
                    continue
                truth, ids = list_truth(set(cs), stories)
                rows[uid] = dict(id=uid, tractate=T.english(slug), ref=cs[0][0], cells=[list(c) for c in cs],
                                 set='C1', evidence='CIRCULAR', truth=truth,
                                 truth_source=f'2005 list {ids} (through superseded_by_rule)',
                                 detector_confidence={'golden': 'LOW_CONFIDENCE'},
                                 tags=['golden_low_on_list', 'expert_listed'])
    log.info('golden LOW on list: %s list stories -> %d new spans', dict(n_list), len(rows))
    return rows, dict(n_list)


# ---- C2 -------------------------------------------------------------------

def grade(c):
    return 'D' if c in DEFINITE else 'L' if c in LOWISH else 'N'


POOL = {('D', 'L'): 'P1', ('D', 'N'): 'P2', ('L', 'L'): 'P3', ('L', 'N'): 'P4'}


def c2_rows(texts):
    removals = load('results/shas_run/septimus_site_decisions.json')['remove']['passages']
    rows = {}
    for slug in ('eruvin', 'yevamot'):
        sf = load(f'site/data/{slug}.json')
        taken = {(g['ref'], g['i']) for s in sf['stories'] + sf['out_of_scope'] for g in s['segments']}
        for e in removals:
            if e['tractate'] == slug:
                taken |= {(e['ref'], i) for i in range(int(e['start_segment']), int(e['end_segment']) + 1)}
        stories = list_stories(slug, texts[T.english(slug)])
        for u in load(f'results/consensus/{slug}/units.json')['units']:
            cls = {r: (u['calls'].get(r) or {}).get('cls') for r in ('v14_r1', 'v14_r2')}
            pool = POOL.get(tuple(sorted(grade(c) for c in cls.values())))
            cells = {tuple(c) for c in u['cells']}
            if not pool or cells & taken:
                continue
            truth, ids = list_truth(cells, stories)
            rows[u['id']] = dict(id=f'C2:{u["id"]}', tractate=u['tractate'], ref=u['cells'][0][0], cells=u['cells'],
                                 set='C2', evidence='BLIND', truth=truth,
                                 truth_source=(f'2005 list {ids} (through superseded_by_rule)' if ids
                                               else 'on no list: unknown, lower bound only'),
                                 detector_confidence={**cls, 'pool': pool},
                                 tags=[pool, 'low_in_a_run' if pool != 'P2' else 'split_definite_not']
                                 + (['expert_listed'] if ids else ['unlisted']))
    return rows


def build():
    texts = {t: j.Text(t) for t in ('Ketubot', 'Kiddushin', 'Gittin', 'Eruvin', 'Yevamot')}
    c1 = c1_rows()
    gl, n_list = golden_low_rows(c1, texts)
    c2 = c2_rows(texts)
    spans = list(c1.values()) + list(gl.values()) + list(c2.values())
    for s in spans:                               # every cell must be text the prompt can show
        missing = [c for c in s['cells'] if tuple(c) not in texts[s['tractate']].seg]
        if missing:
            raise ValueError(f'{s["id"]}: cells outside the text on disk {missing[:3]}')
    ids = [s['id'] for s in spans]
    assert len(ids) == len(set(ids)), 'duplicate span ids'
    counts = Counter((s['set'], s['truth']) for s in spans)
    meta = {'what': __doc__.split('\n\n')[0], 'judge_prompt': str(j.PROMPT_PATH.relative_to(PROJECT_ROOT)),
            'judge_prompt_sha': j.prompt_sha(), 'truth_rule': "Jeff borderline = NOT a story (site ships definite only)",
            'golden_low_on_list_list_stories': n_list,
            'counts': {f'{a}|{b}': n for (a, b), n in sorted(counts.items())},
            'built': time.strftime('%Y-%m-%dT%H:%M:%S')}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'manifest.json').write_text(json.dumps({'meta': meta, 'spans': spans}, ensure_ascii=False, indent=1) + '\n')
    log.info('manifest: %d spans %s', len(spans), meta['counts'])


# ---- export / import --------------------------------------------------------

def check_prompt():
    if j.prompt_sha() != JUDGE_PROMPT_SHA:
        raise SystemExit(f'judge prompt sha {j.prompt_sha()} != pinned {JUDGE_PROMPT_SHA}: '
                         'set JUDGE_PROMPT=src/prompts/judge_register_v2.md')


def export(pass_name, seed, batch):
    check_prompt()
    spans = load(str((OUT / 'manifest.json').relative_to(PROJECT_ROOT)))['spans']
    texts = {t: j.Text(t) for t in {s['tractate'] for s in spans}}
    d = OUT / pass_name
    if (d / 'keys').exists():
        raise SystemExit(f'{d} already holds an export')
    for sub in ('batches', 'keys', 'answers'):
        (d / sub).mkdir(parents=True, exist_ok=True)
    (d / 'system_prompt.md').write_text(j.system_prompt())
    order = list(spans)
    random.Random(seed).shuffle(order)
    sizes, n = {}, 0
    for i in range(0, len(order), batch):
        items = []
        for s in order[i:i + batch]:
            prompt, passage = j.user_prompt(s, texts[s['tractate']])
            items.append({'id': s['id'], 'prompt': prompt, 'passage': sorted(passage)})
        (d / 'keys' / f'{n:03d}.json').write_text(json.dumps(items, ensure_ascii=False, indent=1))
        sd = d / 'batches' / f'{n:03d}'
        sd.mkdir(exist_ok=True)
        for k, it in enumerate(items, start=1):
            (sd / f'{k:02d}.txt').write_text(it['prompt'] + '\n')
            sizes[f'{n:03d}/{k:02d}'] = len((it['prompt'] + '\n').encode())
        n += 1
    over = {k: v for k, v in sizes.items() if v > 30_000}
    (d / 'export_manifest.json').write_text(json.dumps({
        'pass': pass_name, 'seed': seed, 'batch': batch, 'batches': n, 'units': len(order),
        'prompt': str(j.PROMPT_PATH.relative_to(PROJECT_ROOT)), 'prompt_sha': j.prompt_sha(),
        'rules_sha': hashlib.sha256(j.RULES_PATH.read_bytes()).hexdigest()[:12],
        'system_prompt_bytes': len(j.system_prompt().encode()),
        'largest_file_bytes': max(sizes.values()), 'files_over_30kb': over,
        'exported': time.strftime('%Y-%m-%dT%H:%M:%S')}, indent=1))
    log.info('%s: %d spans in %d batches; largest prompt %d bytes; over 30 KB: %s',
             pass_name, len(order), n, max(sizes.values()), over or 'none')


def import_(pass_name, model):
    check_prompt()
    d = OUT / pass_name
    man = json.loads((d / 'export_manifest.json').read_text())
    if man['prompt_sha'] != j.prompt_sha():
        raise SystemExit('prompt changed since export -- re-export')
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
                    raise RuntimeError('no answer from the grader for this span')
            rows.append({'id': it['id'], 'answer': j.ask(backend, system, it['prompt'], set(it['passage']))})
    meta = {'pass': pass_name, 'prompt_sha': man['prompt_sha'], 'rules_sha': man['rules_sha'],
            'backend': {'model': model, 'via': 'Claude Code subagent (Agent tool), not the API',
                        'seed': man['seed'], 'batch': man['batch']},
            'missing_batches': missing, 'outcomes': dict(Counter(r['answer']['outcome'] for r in rows)),
            'imported': time.strftime('%Y-%m-%dT%H:%M:%S')}
    (d / 'claude.json').write_text(json.dumps({'meta': meta, 'rows': rows}, ensure_ascii=False, indent=1) + '\n')
    log.info('%s: wrote claude.json %s; missing batches %s', pass_name, meta['outcomes'], missing)


# ---- score --------------------------------------------------------------------

def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(mid - half, 3), round(mid + half, 3)]


def verdicts(pass_name):
    rows = json.loads((OUT / pass_name / 'claude.json').read_text())['rows']
    return {r['id']: (r['answer']['verdict'] if r['answer']['outcome'] == 'ok' else None) for r in rows}


def score():
    spans = load(str((OUT / 'manifest.json').relative_to(PROJECT_ROOT)))['spans']
    passes = [p for p in ('pass1', 'pass2') if (OUT / p / 'claude.json').exists()]
    V = {p: verdicts(p) for p in passes}
    groups = {'all known': lambda s: True, 'C1': lambda s: s['set'] == 'C1',
              'C1 jeff_shown_low': lambda s: 'jeff_shown_low' in s['tags'],
              'C1 golden_low_on_list': lambda s: 'golden_low_on_list' in s['tags'],
              'C2 (BLIND)': lambda s: s['set'] == 'C2'}
    res, lines = {'passes': passes}, []
    for p in passes + (['both passes story'] if len(passes) == 2 else []):
        for g, f in groups.items():
            n = Counter()
            for s in filter(f, spans):
                v = (V[p].get(s['id']) if p in V else
                     'story' if all(V[q].get(s['id']) == 'story' for q in passes) else 'other')
                n[(v == 'story', s['truth'])] += 1
                n[('scored', v is not None)] += 1
            k, called = n[(True, 'yes')], sum(n[(True, t)] for t in ('yes', 'borderline', 'no'))
            unk = n[(True, 'unknown')]
            prec = round(k / called, 3) if called else None
            wl = wilson(k, called)
            ok = bool(prec is not None and prec >= SHIP_PRECISION and wl[0] >= SHIP_WILSON_LOW)
            yes_all = sum(n[(b, 'yes')] for b in (True, False))
            res.setdefault(p, {})[g] = {'called_story_known': called, 'jeff_yes': k, 'precision': prec,
                                        'wilson95': wl, 'meets_bar': ok, 'called_story_unknown_truth': unk,
                                        'recall_of_jeff_yes': f'{k}/{yes_all}',
                                        'unscored': n[('scored', False)]}
            lines.append(f'{p:18s} {g:22s} story->yes {k}/{called} = {prec} wilson {wl} '
                         f'{"MEETS" if ok else "below"} bar; +{unk} unknown-truth; recall {k}/{yes_all}; '
                         f'unscored {n[("scored", False)]}')
    if len(passes) == 2:
        both = [s['id'] for s in spans if V['pass1'].get(s['id']) and V['pass2'].get(s['id'])]
        same = sum(V['pass1'][i] == V['pass2'][i] for i in both)
        st = sum((V['pass1'][i] == 'story') == (V['pass2'][i] == 'story') for i in both)
        res['stability'] = {'n': len(both), 'same_verdict': same, 'same_story_or_not': st}
        lines.append(f'stability: same verdict {same}/{len(both)}; same story-or-not {st}/{len(both)}')
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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [low-pool-calibration] %(message)s',
                        handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'), logging.StreamHandler(sys.stdout)])
    if 'JUDGE_PROMPT' not in os.environ:
        raise SystemExit('set JUDGE_PROMPT=src/prompts/judge_register_v2.md (the module default is v1)')
    {'build': build, 'score': score}.get(args.cmd, lambda: None)()
    if args.cmd == 'export':
        export(args.pass_name, args.seed, args.batch)
    elif args.cmd == 'import':
        import_(args.pass_name, args.model)


if __name__ == '__main__':
    main()
