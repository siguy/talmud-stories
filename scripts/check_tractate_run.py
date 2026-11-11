#!/usr/bin/env python3
"""The gates of the Shas run (docs/history/2026-11-09-PLAN-shas-run.md §2.2). READ-ONLY.

A gate is an automatic check that stops one tractate going further if it fails. Each gate
returns one result:  green (go on)  /  amber (go on, but Simon or Claude should look)  /
red (stop this tractate).  Nothing here calls Gemini or writes a file.

    python3 scripts/check_tractate_run.py --tractate berakhot --gate g3
    python3 scripts/check_tractate_run.py --tractate yevamot --gate all --json

  g1  text     after the fetch
  g2  triage   after Stage 1
  g3  run      each run (run1 and run2)
  g4  pair     the two runs agree
  g5  density  stories per examined page; Gemini's out-of-scope rate
  g6  judges   each judge's answers are complete and valid; Claude covers every
               unit Gemini called out_of_scope

Lesson 21 / 38: a missing or unreadable input is RED with the reason, never an empty pass.
With `--gate all`, a gate whose inputs do not exist yet is 'pending', not red.
"""
import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
from tractates import Paths  # noqa: E402

# ---- the numbers the gates use (each from plan §2.2, with the measurement behind it) ----
VOWEL_MIN = 0.95                 # G1: share of Hebrew segments carrying vowel points
MAX_ADDITION_FAILURES = 3        # G3: pass2 / twin / stage4 failures (they only lose additions)
MAX_EMPTY = 2                    # G3: empty responses
MAX_SPAN_REPAIRS = 3             # G3
DETECTOR = 'src.story_detector_v14'
MODEL = 'gemini-3-flash-preview'
KEPT_TOLERANCE = 0.10            # G4: kept-story counts within 10%
# G4: measured 2026-11-09 on the two finished v14 tractates (docs plan §2.2): passages that are
# definite (YES/HIGH in stories[]) in either run, and definite in both: Berakhot 116/126 = 92.1%,
# Yevamot 83/90 = 92.2%. The gate stays at 90%, just under both (n = 2: indicated, not measured).
DEFINITE_BOTH_MIN = 0.90
JUDGE_PROMPT_SHA = '84bfb33fd32a'   # judge_register_v2
DEFINITE = ('YES', 'HIGH_CONFIDENCE')
NIKUD = re.compile('[ְ-ׇ]')
# G5 baselines, measured: kept stories per examined page 1.8 (Berakhot), 1.5 (Yevamot); Gemini
# out-of-scope units 7/224 and 10/184. The two are read from disk, these are only the fallback.
OUT_OF_SCOPE_BASELINES = ('berakhot', 'yevamot')
DECISIONS = 'results/shas_run/decisions.json'   # Simon's rulings on red gates (G4, G6); see the file


def decisions(root):
    """(g4_accepted tractates, {tractate: [unit ids Claude decides alone]}, {tractate: [unit ids hand-flagged
    biblical]}) from Simon's rulings file."""
    p = Path(root) / DECISIONS
    if not p.exists():
        return set(), {}, {}
    d = json.loads(p.read_text())
    return (set(d['g4_accepted']['tractates']), d['claude_alone']['units'],
            d.get('biblical_flag', {}).get('units', {}))


def claude_alone(P):
    return set(decisions(P.root)[1].get(P.slug, []))
DENSITY_LOW, DENSITY_HIGH = 0.5, 2.0   # amber outside [0.5 x lowest, 2 x highest] of run tractates


class Result:
    def __init__(self, gate, slug):
        self.gate, self.slug, self.status = gate, slug, 'green'
        self.failures, self.warnings, self.notes, self.measured = [], [], [], {}

    def red(self, msg):
        self.status = 'red'
        self.failures.append(msg)

    def amber(self, msg):
        if self.status == 'green':
            self.status = 'amber'
        self.warnings.append(msg)

    def note(self, msg):
        self.notes.append(msg)

    def pending(self, why):
        self.status = 'pending'
        self.notes.append(why)
        return self

    def to_dict(self):
        return {'gate': self.gate, 'tractate': self.slug, 'status': self.status, 'failures': self.failures,
                'warnings': self.warnings, 'notes': self.notes, 'measured': self.measured}


def sha1_of(path):
    return hashlib.sha1(Path(path).read_bytes()).hexdigest()


def load_json(path, res, what):
    """Read a JSON input; an absent or unreadable one is red, with the reason."""
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        res.red(f'{what} missing: {path}')
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        res.red(f'{what} unreadable ({e}): {path}')
    return None


def daf_number(ref):
    m = re.search(r'(\d+)([ab])$', ref)
    return int(m.group(1)) * 2 + (m.group(2) == 'b') if m else None


def examined(page):
    return not page.get('skipped_by_triage')


def kept_stories(run):
    """Stories in stories[] that are not NOT_A_STORY (the count the plan's baselines use)."""
    return sum(1 for p in run['pages'] for s in p.get('stories', []) if s.get('classification') != 'NOT_A_STORY')


def story_cells(pages, i, s):
    """Cells (ref, segment index) of one story, cross-page aware (build_site_data.pieces)."""
    p = pages[i]
    a, b = int(s['start_segment']), int(s['end_segment'])
    cells = {(p['ref'], k) for k in range(a, b + 1)}
    if s.get('spans_pages') and s.get('end_segment_page2') is not None and i + 1 < len(pages):
        q = pages[i + 1]
        cells |= {(q['ref'], k) for k in range(int(s.get('start_segment_page2') or 0), int(s['end_segment_page2']) + 1)}
    return cells


def definite_spans(run):
    pages = run['pages']
    return [story_cells(pages, i, s) for i, p in enumerate(pages) for s in p.get('stories', [])
            if s.get('classification') in DEFINITE]


def definite_agreement(run_a, run_b):
    """(passages, passages definite in both). A passage is a group of definite spans from the two
    runs that share a cell (transitively); it is 'in both' if both runs contribute a span."""
    spans = [(0, c) for c in definite_spans(run_a)] + [(1, c) for c in definite_spans(run_b)]
    parent = list(range(len(spans)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    owner = {}
    for i, (_, cells) in enumerate(spans):
        for c in cells:
            if c in owner:
                parent[find(i)] = find(owner[c])
            else:
                owner[c] = i
    groups = {}
    for i, (which, _) in enumerate(spans):
        groups.setdefault(find(i), set()).add(which)
    return len(groups), sum(1 for w in groups.values() if len(w) == 2)


# ---- G1 ---------------------------------------------------------------------------------

def g1_text(P, shape=None):
    """shape: {ref: segment count} from Sefaria, or None to use the one the fetch saved."""
    r = Result('g1', P.slug)
    d = load_json(P.text, r, 'text')
    if d is None:
        return r
    pages = d.get('pages') or []
    if not pages:
        r.red('no pages in the text file')
        return r
    refs = [p['ref'] for p in pages]
    shape = shape or d.get('sefaria_shape')
    if shape:
        # An amud Sefaria's index counts as 0 segments is blank in the source (Nazir 33b):
        # its absence is expected, noted by name, not a missing page.
        blank = sorted(r for r in shape if not shape[r] and r not in set(refs))
        missing = sorted(r for r in set(shape) - set(refs) if shape[r])
        extra = sorted(set(refs) - set(shape))
        if blank:
            r.note(f'blank in the source (index counts 0 segments), not fetched: {blank}')
        if missing or extra:
            r.red(f'pages differ from the Sefaria index: missing {missing[:8]}, extra {extra[:8]}')
        diffs = {p['ref']: (shape[p['ref']], len(p['segments'])) for p in pages
                 if p['ref'] in shape and shape[p['ref']] != len(p['segments'])}
        if diffs:
            r.note(f'segment counts differ from the index on {len(diffs)} page(s): {dict(list(diffs.items())[:6])}')
    else:
        r.amber('Sefaria shape index not available (older fetch): page count NOT checked against Sefaria')
    nums = [daf_number(x) for x in refs]
    # Amudim blank in the source are an expected gap, not a missing page.
    blank_nums = {daf_number(x) for x in (shape or {}) if not shape[x]} - {None}
    if None in nums:
        r.red(f'unparseable refs: {[x for x, n in zip(refs, nums) if n is None][:5]}')
    elif nums != sorted(nums) or len(set(nums)) != len(nums):
        r.red('refs out of order or repeated')
    else:
        gaps = sorted(set(range(nums[0], nums[-1] + 1)) - set(nums) - blank_nums)
        if gaps:
            r.red(f'refs not contiguous (daf numbers missing: {gaps[:10]}) or out of order')
    empty_pages = [p['ref'] for p in pages if not p.get('segments')]
    if empty_pages:
        r.red(f'pages with no segments: {empty_pages[:8]}')
    segs = [(p['ref'], g) for p in pages for g in p.get('segments', [])]
    no_he = [f"{ref}:{g.get('index')}" for ref, g in segs if not (g.get('hebrew') or '').strip()]
    if no_he:
        r.red(f'{len(no_he)} segment(s) with no Hebrew: {no_he[:8]}')
    he = [g for _, g in segs if (g.get('hebrew') or '').strip()]
    share = sum(1 for g in he if NIKUD.search(g['hebrew'])) / max(len(he), 1)
    if share < VOWEL_MIN:
        r.red(f'vowel points on only {100 * share:.1f}% of Hebrew segments (need {100 * VOWEL_MIN:.0f}%)')
    no_en = [f"{ref}:{g.get('index')}" for ref, g in segs if not (g.get('english') or '').strip()]
    r.measured = {'pages': len(pages), 'segments': len(segs), 'vowel_share': round(share, 4),
                  'empty_english': len(no_en)}
    if no_en:
        r.note(f'{len(no_en)} segment(s) with empty English (counted, not a failure): {no_en[:12]}')
    return r


# ---- G2 ---------------------------------------------------------------------------------

def g2_triage(P):
    r = Result('g2', P.slug)
    text = load_json(P.text, r, 'text')
    tri = load_json(P.triage, r, 'triage cache')
    if text is None or tri is None:
        return r
    labels = tri.get('triage_results') or {}
    refs = [p['ref'] for p in text['pages']]
    unlabelled = [x for x in refs if not labels.get(x)]
    if unlabelled:
        r.red(f'{len(unlabelled)} page(s) with no triage label: {unlabelled[:8]}')
    failed = [x for x in refs if labels.get(x) and all(v == 'TRIAGE_FAILED' for v in labels[x])]
    if failed:
        r.red(f'{len(failed)} page(s) whose labels are all TRIAGE_FAILED (read from the cache file): {failed[:8]}')
    extra = sorted(set(labels) - set(refs))
    if extra:
        r.note(f'{len(extra)} label(s) for pages not in the text: {extra[:5]}')
    r.measured = {'pages': len(refs), 'labelled': len(refs) - len(unlabelled), 'triage_sha1': sha1_of(P.triage)}
    return r


# ---- G3 ---------------------------------------------------------------------------------

def g3_run(P, n):
    r = Result(f'g3:run{n}', P.slug)
    run = load_json(P.run(n), r, f'run {n}')
    text = load_json(P.text, r, 'text')
    if run is None or text is None:
        return r
    m = run.get('run_meta') or {}
    out_refs = [p['ref'] for p in run.get('pages', [])]
    miss = sorted(set(p['ref'] for p in text['pages']) - set(out_refs))
    if miss:
        r.red(f'{len(miss)} fetched page(s) missing from the run output: {miss[:8]}')
    if m.get('stage2_errors'):
        r.red(f"stage2_errors = {len(m['stage2_errors'])}: {m['stage2_errors'][:4]}")
    if m.get('truncated_responses'):
        r.red(f"truncated_responses = {m['truncated_responses']}")
    tokens = m.get('tokens') or {}
    if not tokens.get('stage2_and_4', {}).get('calls'):
        r.red('no token meter for Stage 2+4 (run_meta.tokens): cost and failures cannot be read')
    for stage, t in tokens.items():
        if t.get('unmetered'):
            r.red(f"tokens.{stage}.unmetered = {t['unmetered']}")
        if t.get('retries_exhausted'):
            r.note(f"{stage}: {t['retries_exhausted']} call(s) still failing after every retry (see the counters below)")
    lists = {'pass2_failures': m.get('pass2_failures') or [], 'twin_failures': m.get('twin_failures') or [],
             'stage4_call_failures': run.get('stage4_call_failures') or []}
    for name, items in lists.items():
        if len(items) > MAX_ADDITION_FAILURES:
            r.red(f'{name} = {len(items)} (limit {MAX_ADDITION_FAILURES}): {items[:5]}')
        elif items:
            r.note(f'{name} = {len(items)} (within the limit, only lose additions): {items}')
    empties = m.get('empty_responses') or 0
    if empties > MAX_EMPTY:
        r.red(f'empty_responses = {empties} (limit {MAX_EMPTY})')
    elif empties:
        r.note(f'empty_responses = {empties} (within the limit)')
    repairs = len(run.get('span_repairs') or [])
    if repairs > MAX_SPAN_REPAIRS:
        r.red(f'span_repairs = {repairs} (limit {MAX_SPAN_REPAIRS})')
    elif repairs:
        r.note(f'span_repairs = {repairs}')
    if m.get('detector_module') != DETECTOR or run.get('version') != 'v14':
        r.red(f"detector {m.get('detector_module')} / version {run.get('version')}, expected {DETECTOR}")
    if m.get('model') != MODEL:
        r.red(f"model {m.get('model')}, expected {MODEL}")
    if m.get('thinking_level') not in (None, '', 'off', 'none', 'minimal'):
        r.red(f"thinking_level {m.get('thinking_level')!r}, expected off")
    if m.get('twin_trigger') != 'all':
        r.red(f"twin_trigger {m.get('twin_trigger')!r}, expected 'all'")
    if m.get('triage_failed', {}).get('count'):
        r.note(f"triage_failed pages carried into the run: {m['triage_failed']['refs'][:5]}")
    recorded = m.get('triage_sha1')
    if not Path(P.triage).exists():
        r.red('triage cache missing, cannot confirm the run did not re-triage')
    elif recorded is None:
        r.amber('run_meta has no triage_sha1 (run predates item 3): cannot confirm the run did not re-triage')
    elif recorded != sha1_of(P.triage):
        r.red(f'triage cache changed since the run read it (run {recorded[:8]}, now {sha1_of(P.triage)[:8]}): it re-triaged')
    if m.get('resumed_pages'):
        r.amber(f"{m['resumed_pages']} page(s) resumed from a checkpoint: failure counters cover only the part after the crash")
    ex = sum(1 for p in run.get('pages', []) if examined(p))
    r.measured = {'pages': len(out_refs), 'examined': ex, 'kept_stories': kept_stories(run),
                  'elapsed_seconds': m.get('elapsed_seconds'), 'fingerprint': m.get('stage2_fingerprint'),
                  'retries': {s: t.get('retries', 0) for s, t in tokens.items()}, 'tokens': tokens}
    return r


# ---- G4 ---------------------------------------------------------------------------------

def g4_pair(P):
    r = Result('g4', P.slug)
    a = load_json(P.run(1), r, 'run 1')
    b = load_json(P.run(2), r, 'run 2')
    if a is None or b is None:
        return r
    ma, mb = a.get('run_meta') or {}, b.get('run_meta') or {}
    fa, fb = ma.get('stage2_fingerprint'), mb.get('stage2_fingerprint')
    if not fa or fa != fb:
        r.red(f'stage2_fingerprint differs or is missing: {fa} vs {fb}')
    ha, hb = ma.get('detector_sha1'), mb.get('detector_sha1')
    if ha is None or hb is None:
        r.amber('run_meta has no detector_sha1 (run predates item 3): detector code identity NOT confirmed')
    elif ha != hb:
        r.red(f'the two runs used different detector code ({ha[:8]} vs {hb[:8]})')
    ta, tb = ma.get('triage_sha1'), mb.get('triage_sha1')
    if ta is None or tb is None:
        r.amber('run_meta has no triage_sha1 (run predates item 3): triage identity NOT confirmed')
    elif ta != tb:
        r.red(f'the two runs read different triage caches ({ta[:8]} vs {tb[:8]})')
    ka, kb = kept_stories(a), kept_stories(b)
    spread = abs(ka - kb) / max(ka, kb, 1)
    if spread > KEPT_TOLERANCE:
        r.red(f'kept-story counts {ka} vs {kb} differ by {100 * spread:.1f}% (limit {100 * KEPT_TOLERANCE:.0f}%)')
    passages, both = definite_agreement(a, b)
    share = both / passages if passages else 0.0
    if not passages:
        r.red('no definite passage in either run')
    elif share < DEFINITE_BOTH_MIN and P.slug in decisions(P.root)[0]:
        r.amber(f'{100 * share:.1f}% of passages definite in either run are definite in both ({both}/{passages}; '
                f'under {100 * DEFINITE_BOTH_MIN:.0f}%): shipped by Simon\'s 2026-11-10 ruling ({DECISIONS})')
    elif share < DEFINITE_BOTH_MIN:
        r.red(f'only {100 * share:.1f}% of passages definite in either run are definite in both '
              f'({both}/{passages}; need {100 * DEFINITE_BOTH_MIN:.0f}%)')
    r.measured = {'kept': [ka, kb], 'definite_passages': passages, 'definite_in_both': both,
                  'definite_both_share': round(share, 4)}
    return r


# ---- G5 ---------------------------------------------------------------------------------

def gemini_out_of_scope_rate(P):
    """(out_of_scope units, units) from this tractate's Gemini answers, or None if not judged yet."""
    if not (Path(P.consensus) / 'gemini.json').exists() or not (Path(P.consensus) / 'units.json').exists():
        return None
    rows = json.loads((Path(P.consensus) / 'gemini.json').read_text())['rows']
    n = len(json.loads((Path(P.consensus) / 'units.json').read_text())['units'])
    return sum(1 for x in rows if x['answer'].get('outcome') == 'ok' and x['answer'].get('verdict') == 'out_of_scope'), n


def g5_density(P):
    r = Result('g5', P.slug)
    run = load_json(P.run(1), r, 'run 1')
    if run is None:
        return r
    ex = sum(1 for p in run['pages'] if examined(p))
    dens = kept_stories(run) / ex if ex else 0.0
    # Compared with the two pre-run baselines only (plan §2.2: Berakhot 1.8, Yevamot 1.5 per examined page). Against
    # every other run tractate the range widened as the run grew: Keritot's 0.30 unflagged Zevachim's 0.54 (2026-11-10).
    others = {}
    for t in (P.sibling(b) for b in OUT_OF_SCOPE_BASELINES if b != P.slug):
        try:
            o = json.loads(Path(t.run(1)).read_text())
            e = sum(1 for p in o['pages'] if examined(p))
            if e:
                others[t.slug] = kept_stories(o) / e
        except (OSError, json.JSONDecodeError, KeyError):
            continue
    r.measured = {'stories_per_examined_page': round(dens, 3), 'examined': ex,
                  'compared_with': {k: round(v, 3) for k, v in sorted(others.items())}}
    if not ex:
        r.red('no examined page in run 1')
    elif others:
        lo, hi = DENSITY_LOW * min(others.values()), DENSITY_HIGH * max(others.values())
        r.measured['range'] = [round(lo, 3), round(hi, 3)]
        if not lo <= dens <= hi:
            r.amber(f'{dens:.2f} stories per examined page is outside {lo:.2f}-{hi:.2f}: Simon reads 10 random stories')
    else:
        r.note('no other run tractate to compare density with')
    oos = gemini_out_of_scope_rate(P)
    if oos is None:
        r.note('Gemini out-of-scope rate: pending (the Gemini judge has not run)')
    else:
        base = []
        for slug in OUT_OF_SCOPE_BASELINES:
            b = gemini_out_of_scope_rate(P.sibling(slug))
            if b and b[1]:
                base.append(b[0] / b[1])
        rate = oos[0] / oos[1] if oos[1] else 0.0
        r.measured['gemini_out_of_scope'] = {'units': oos[1], 'out_of_scope': oos[0], 'rate': round(rate, 4)}
        if base and rate > max(base) and P.slug not in OUT_OF_SCOPE_BASELINES:
            r.amber(f'Gemini calls {100 * rate:.1f}% of units out of scope, above the baselines '
                    f'({", ".join(f"{100 * x:.1f}%" for x in base)}): the biblical list needs a close look')
    return r


# ---- G6 ---------------------------------------------------------------------------------

def g6_judge(P, who):
    r = Result(f'g6:{who}', P.slug)
    units = load_json(Path(P.consensus) / 'units.json', r, 'units.json')
    d = load_json(Path(P.consensus) / f'{who}.json', r, f'{who}.json')
    if units is None or d is None:
        return r
    unit_ids = [u['id'] for u in units['units']]
    rows = d.get('rows') or []
    ids = [x['id'] for x in rows]
    if len(ids) != len(set(ids)):
        r.red(f'{len(ids) - len(set(ids))} duplicate row id(s)')
    extra = sorted(set(ids) - set(unit_ids))
    if extra:
        r.red(f'{len(extra)} row(s) for units that do not exist: {extra[:5]}')
    if (d.get('meta') or {}).get('prompt_sha') != JUDGE_PROMPT_SHA:
        r.red(f"judge prompt sha {(d.get('meta') or {}).get('prompt_sha')}, expected {JUDGE_PROMPT_SHA}")
    alone = claude_alone(P) if who == 'gemini' else set()
    ruled = sorted(x['id'] for x in rows if x['answer'].get('outcome') != 'ok' and x['id'] in alone)
    if ruled:
        r.amber(f'{len(ruled)} unit(s) with no valid Gemini answer, decided by Claude alone '
                f'(Simon, 2026-11-10, {DECISIONS}): {ruled}')
    bad = Counter(x['answer'].get('outcome') for x in rows if x['answer'].get('outcome') != 'ok' and x['id'] not in alone)
    if bad:
        r.red(f'{sum(bad.values())} row(s) not ok: {dict(bad)}')
    if (d.get('meta') or {}).get('missing_batches'):
        r.red(f"missing batches: {d['meta']['missing_batches']}")
    ok_ids = {x['id'] for x in rows if x['answer'].get('outcome') == 'ok'}
    if who == 'gemini':
        absent = sorted(set(unit_ids) - set(ids))
        if absent:
            r.red(f'{len(absent)} unit(s) with no Gemini answer at all: {absent[:5]}')
    else:
        g = load_json(Path(P.consensus) / 'gemini.json', r, 'gemini.json (Claude is judged against it)')
        if g is not None:
            flagged = {x['id'] for x in g['rows'] if x['answer'].get('outcome') == 'ok'
                       and x['answer'].get('verdict') == 'out_of_scope'} | claude_alone(P)
            unanswered = sorted(flagged - ok_ids)
            if unanswered:
                r.red(f'{len(unanswered)} unit(s) Gemini called out_of_scope have no Claude answer with outcome ok '
                      f'(the site would ship them as "not biblical"): {unanswered[:6]}')
            r.measured['gemini_out_of_scope_units'] = len(flagged)
            if len(ids) < len(unit_ids):
                r.note(f'Claude answered a subset: {len(ids)} of {len(unit_ids)} units')
    r.measured.update({'units': len(unit_ids), 'rows': len(rows), 'outcomes': dict(Counter(x['answer'].get('outcome') for x in rows))})
    return r


# ---- driver ------------------------------------------------------------------------------

def run_gate(P, gate):
    """Results for one gate name (g1..g6), each pending if its inputs are not there yet."""
    if gate == 'g1':
        return [g1_text(P)]
    if gate == 'g2':
        return [g2_triage(P)]
    if gate == 'g3':
        return [g3_run(P, n) for n in (1, 2)]
    if gate == 'g4':
        return [g4_pair(P)]
    if gate == 'g5':
        return [g5_density(P)]
    if gate == 'g6':
        return [g6_judge(P, w) for w in ('gemini', 'claude')]
    raise SystemExit(f'unknown gate {gate!r}')


NEEDS = {'g1': lambda P: [P.text], 'g2': lambda P: [P.triage], 'g3': lambda P: [P.run(1)],
         'g4': lambda P: [P.run(1), P.run(2)], 'g5': lambda P: [P.run(1)],
         'g6': lambda P: [Path(P.consensus) / 'gemini.json']}


def run_all(P):
    out = []
    for g in ('g1', 'g2', 'g3', 'g4', 'g5', 'g6'):
        if all(Path(x).exists() for x in NEEDS[g](P)):
            out += run_gate(P, g)
        else:
            out.append(Result(g, P.slug).pending('inputs not there yet'))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tractate', required=True, help='slug, e.g. berakhot or bava_batra')
    ap.add_argument('--gate', default='all', choices=['g1', 'g2', 'g3', 'g4', 'g5', 'g6', 'all'])
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    P = Paths(args.tractate, PROJECT_ROOT)
    results = run_all(P) if args.gate == 'all' else run_gate(P, args.gate)
    if args.json:
        print(json.dumps([x.to_dict() for x in results], indent=1, ensure_ascii=False))
    else:
        for x in results:
            print(f'{x.gate:10s} {x.status.upper():7s} {x.slug}')
            for label, items in (('RED', x.failures), ('AMBER', x.warnings), ('note', x.notes)):
                for it in items:
                    print(f'    {label}: {it}')
            if x.measured:
                print(f'    measured: {json.dumps({k: v for k, v in x.measured.items() if k != "tokens"}, ensure_ascii=False)}')
    return 1 if any(x.status == 'red' for x in results) else 0


if __name__ == '__main__':
    sys.exit(main())
