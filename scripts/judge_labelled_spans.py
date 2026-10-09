#!/usr/bin/env python3
"""Consensus phase 1 — do two models, each given Jeff's rule register, agree with him?

work/2026-09-28-consensus-1-test-the-bet.md; plan docs/history/2026-09-28-PLAN-consensus-at-scale.md.

The unit judged is the span Jeff judged, exactly as he saw it -- never a detector
candidate -- plus the stories on his 2005 lists (positives only). One prompt
(src/prompts/judge_register_v1.md) carrying the rule sections of docs/STORY_RULES.md,
two model families, and a failed or invalid answer is COUNTED, never scored (Lesson 21).

LABELS -- what "his verdict" means, and why it needs this much code
-------------------------------------------------------------------
Before the axes UI (2026-09-02) every round asked "is the DETECTOR'S CALL correct?",
not "is this a story?". A `correct` on a span the detector called NOT_A_STORY is his
**no**: 87 of the 128 verdicts in the 2026-02-05 round are exactly that. So every old
verdict is read against the classification he was SHOWN, recovered from the page he
reviewed (the HTML's embedded data, at the commit he saw it) or from the round file:

    correct / approve   on a story call   -> yes     (borderline if HIS note says so, Lesson 42)
    correct / approve   on NOT_A_STORY    -> no
    adjust, reject_remove                 -> yes     (a story; the extent is what is wrong)
    confirm_remove                        -> no
    incorrect + a readable objection:
        classification                    -> the opposite of what he was shown
        boundary / merge / display        -> yes on a story call; unknown on NOT_A_STORY
        confidence                        -> yes (borderline if he says so)
    incorrect, nothing readable           -> UNKNOWN -- it may be a boundary complaint
    axes rounds: is_story yes/no/borderline as given; a `no` whose note says the story
                 is outside the collection's scope -> out_of_scope (R-S1)

"Readable" = build_ruler.classify_objection() on the note, else the hand sort in
results/rulers/unclassified_notes_resolved.json. Neither is re-derived here.

Excluded, and counted: Simon's test round and pre-screen; the January 2026-01-08 round
(keyed per daf, not per span -- see capture_january_round.py); `applies_to: corrected`
rows are judged and reported separately; a span carrying two different labels is
reported and not scored. Every review file on disk must be named in ROUNDS or EXCLUDED,
or the build raises (Lesson 38).

Eruvin is never read. It is the untouched final exam (plan §4a).

    python3 scripts/judge_labelled_spans.py labels
    python3 scripts/judge_labelled_spans.py run --set smoke --backend both --dry-run
    python3 scripts/judge_labelled_spans.py run --set smoke --backend both
    python3 scripts/judge_labelled_spans.py report --set smoke
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import logging
import math
import os
import random
import re
import subprocess
import sys
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
log = logging.getLogger('consensus-judge')

OUT_DIR = PROJECT_ROOT / 'results/consensus/phase1'

# The reading of a verdict -- what he was shown, and what his answer therefore means --
# lives in scripts/verdict_reading.py, shared with build_ruler.py and
# map_verdict_vocabularies.py (moved 2026-09-29; behaviour unchanged).
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
from verdict_reading import (  # noqa: E402
    STORY_CALLS, ROUNDS, EXCLUDED, REVIEW_GLOBS, UnaccountedFile, account_for_review_files,
    SCOPE_NOTE, HAND_LABELS, BORDERLINE_NOTE, label_axes, label_old,
    _embedded, _git_show, _shown_from_pages, shown_v5_2_60, shown_v5_61_112, shown_v8_delta,
    shown_canonical, shown_in_file, shown_run)
PROMPT_PATH = PROJECT_ROOT / 'src/prompts/judge_register_v1.md'
RULES_PATH = PROJECT_ROOT / 'docs/STORY_RULES.md'
ENV_PATH = Path('/Users/simonbrief/talmud-stories/.env')

TRACTATES = ('Ketubot', 'Kiddushin', 'Gittin', 'Yevamot')     # never Eruvin
# CIRCULAR: their labels shaped the detector's prompts. rule-informed: R-C5, R-B4 and
# R-S1 were written from these very verdicts, so a judge carrying the register has
# seen their reasoning (plan §4).
EVIDENCE = {'Ketubot': 'CIRCULAR', 'Kiddushin': 'CIRCULAR',
            'Gittin': 'rule-informed', 'Yevamot': 'rule-informed'}

# Where the segment text comes from. Segmentation is Sefaria's, so every run on a
# tractate carries the same indices; checked against what he saw where that is on disk.
TEXT_SOURCES = {
    'Ketubot': ['results/v10/wave4_notrim/ketubot_v10_2-60_notrim.json',
                'results/v10/wave4_notrim/ketubot_v10_61-112_notrim.json'],
    'Kiddushin': ['results/v10/wave4_notrim/kiddushin_v10_notrim.json'],
    'Gittin': ['results/v11/gittin/gittin_v11.json'],
    'Yevamot': ['results/v11/twin_pass/yevamot_full_twinall.json'],
}
LIST_MATCHES = {t: f'results/recall/{t.lower()}_jeff2005_matches.json' for t in TRACTATES}

VERDICTS = ('story', 'borderline', 'not', 'out_of_scope', 'unsure')
LABEL_TO_VERDICT = {'yes': 'story', 'no': 'not', 'borderline': 'borderline',
                    'out_of_scope': 'out_of_scope'}
RULE_IDS = {'R-S1', 'R-C1', 'R-C2', 'R-C3', 'R-C4', 'R-C5', 'R-B1', 'R-B2', 'R-B3', 'R-B4'}

MODELS = {'gemini': 'gemini-3-flash-preview', 'claude': 'claude-opus-5'}
CLAUDE_EFFORT = 'medium'
# USD per million tokens (claude-api skill, cached 2026-06-24).
CLAUDE_PRICE = {'input': 5.00, 'output': 25.00, 'cache_write': 6.25, 'cache_read': 0.50}
# Raised 2026-09-29 for phase 1b (Simon topped up the account): it counts every earlier
# run's Claude spend in this directory ($8.94 in phase 1), and 1b is a full run plus a
# same-prompt repeat (~997 x $0.022 x 2 = ~$44).
BUDGET_USD = 75.0


# ---------------------------------------------------------------------------
# text
# ---------------------------------------------------------------------------

class Text:
    """Ordered pages of one tractate: (ref, idx) -> segment, and neighbours in order."""

    def __init__(self, tractate):
        self.cells, self.seg = [], {}
        for rel in TEXT_SOURCES[tractate]:
            for p in json.loads((PROJECT_ROOT / rel).read_text())['pages']:
                for s in p['segments']:
                    cell = (p['ref'], s.get('index', len([c for c in self.cells if c[0] == p['ref']])))
                    self.cells.append(cell)
                    self.seg[cell] = s
        self.pos = {c: i for i, c in enumerate(self.cells)}
        self.page_len = Counter(c[0] for c in self.cells)

    def span_cells(self, first, last):
        a, b = self.pos[tuple(first)], self.pos[tuple(last)]
        return self.cells[a:b + 1]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, PROJECT_ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cited_pages():
    """Pages STORY_RULES names as a case. A judge carrying the register has seen them."""
    text = RULES_PATH.read_text()
    out = set()
    for m in re.finditer(r'(Ketubot|Kiddushin|Gittin|Yevamot)\s+((?:\d+[ab])(?:[:\d\-]*)'
                         r'(?:\s*(?:,|and)\s*\d+[ab][:\d\-]*)*)', text):
        for daf in re.findall(r'\d+[ab]', m.group(2)):
            out.add(f'{m.group(1)} {daf}')
    return out


# ---------------------------------------------------------------------------
# labels
# ---------------------------------------------------------------------------

def build_labels():
    """Every labelled unit, with its provenance, and the counts each rule removed."""
    inventory = account_for_review_files()
    ruler = _load('build_ruler', 'scripts/build_ruler.py')
    hand = {(r['round'], r['key']): r for r in json.loads(
        (PROJECT_ROOT / 'results/rulers/unclassified_notes_resolved.json').read_text())['rows']}
    shown = {name: (cfg['shown']() if cfg['shown'] else {}) for name, cfg in ROUNDS.items()}
    cited = cited_pages()
    counts = Counter()
    rows_by_span = defaultdict(list)
    texts = {t: Text(t) for t in TRACTATES}
    per_round = Counter()

    for tractate in TRACTATES:
        reviews, rounds = ruler.load_reviews(tractate)
        for (ref, lo, hi), entries in reviews.items():
            for e in entries:
                per_round[e['round']] += 1
                if e['round'] in EXCLUDED:
                    counts[f"excluded: {e['round']}"] += 1
                    continue
                if e['round'] not in ROUNDS:
                    raise UnaccountedFile(e['round'])
                cfg = ROUNDS[e['round']]
                if 'axes' in e:
                    label, why = label_axes(e['verdict'], e['note'])
                else:
                    cls, heb = shown[e['round']].get(e['key'], (None, None))
                    label, why = label_old(e['verdict'], cls, e['note'],
                                           hand.get((e['round'], e['key'])),
                                           ruler.classify_objection)
                    if heb and label != 'unknown':
                        ours = [texts[tractate].seg.get((ref, i), {}).get('hebrew', '')
                                for i in range(lo, hi + 1)]
                        if [re.sub(r'\s+', ' ', h).strip() for h in heb] != \
                           [re.sub(r'\s+', ' ', h).strip() for h in ours]:
                            label, why = 'unknown', 'the segment text he saw differs from ours'
                if (e['round'], e['key']) in HAND_LABELS:
                    label, why = HAND_LABELS[(e['round'], e['key'])]
                    why = 'hand reading: ' + why
                    counts['hand-read override'] += 1
                if any((ref, i) not in texts[tractate].seg for i in range(lo, hi + 1)):
                    label, why = 'unknown', 'span is outside the text on disk'
                counts[f'{cfg["applies_to"]}: {label}'] += 1
                if label == 'unknown':
                    counts[f'unknown: {why}'] += 1
                rows_by_span[(tractate, ref, lo, hi, cfg['applies_to'])].append(
                    dict(round=e['round'], verdict=e['verdict'], note=e['note'], label=label, why=why))

    units, conflicts, unknown = [], [], []
    for (tractate, ref, lo, hi, applies), rows in sorted(rows_by_span.items()):
        labels = {r['label'] for r in rows} - {'unknown'}
        base = dict(tractate=tractate, cells=[[ref, i] for i in range(lo, hi + 1)],
                    key=f'{ref}_{lo}-{hi}', evidence=EVIDENCE[tractate],
                    cited_in_rules=ref in cited, verdicts=rows)
        if not labels:
            unknown.append(dict(base, label='unknown'))
        elif len(labels) > 1:
            conflicts.append(dict(base, label='conflict', labels=sorted(labels)))
        else:
            kind = 'review' if applies == 'base' else 'corrected'
            units.append(dict(base, id=f'{kind}:{ref}_{lo}-{hi}', kind=kind, label=labels.pop()))

    # 2005 lists: positives only. A list story his later verdict called not-a-story is
    # superseded (his words: the lists were provisional) -- reported, not scored.
    review_no = defaultdict(list)
    for u in units:
        if u['kind'] == 'review' and u['label'] in ('no', 'out_of_scope'):
            for c in u['cells']:
                review_no[tuple(c)].append(u['key'])
    superseded, unlocated = [], 0
    for tractate in TRACTATES:
        for i, s in enumerate(json.loads((PROJECT_ROOT / LIST_MATCHES[tractate]).read_text())):
            if not s.get('located'):
                unlocated += 1
                continue
            cells = [list(c) for c in texts[tractate].span_cells(*s['located'])]
            sid = s.get('id') or f'{tractate.lower()}_{i + 1:03d}'
            u = dict(tractate=tractate, cells=cells, key=sid, id=f'list:{sid}', kind='list',
                     label='yes', evidence='BLIND list' if s.get('blind', True) else 'list (not blind)',
                     list_blind=s.get('blind', True), list_ref=s['ref'],
                     cited_in_rules=any(c[0] in cited for c in cells), verdicts=[])
            hit = sorted({k for c in cells for k in review_no.get(tuple(c), [])})
            if hit:
                superseded.append(dict(u, superseded_by=hit))
            else:
                units.append(u)

    by = Counter((u['kind'], u['tractate'], u['label']) for u in units)
    return dict(inventory=inventory, rows_read_per_round=dict(per_round), rule_counts=dict(counts),
                units=units, conflicts=conflicts, unknown=unknown,
                list_superseded=superseded, list_unlocated=unlocated,
                table={f'{k}|{t}|{l}': n for (k, t, l), n in sorted(by.items())})


# ---------------------------------------------------------------------------
# the judge
# ---------------------------------------------------------------------------

def rules_text():
    text = RULES_PATH.read_text()
    a, b = text.index('## Scope'), text.index('## Triage')
    return text[a:b].strip()


def system_prompt():
    return PROMPT_PATH.read_text().replace('{RULES}', rules_text())


def prompt_sha():
    return hashlib.sha256(system_prompt().encode()).hexdigest()[:12]


def user_prompt(unit, text: Text):
    """The passage with one segment of context each side. Returns (prompt, passage numbers)."""
    cells = [tuple(c) for c in unit['cells']]
    a, b = text.pos[cells[0]], text.pos[cells[-1]]
    shown = [('CONTEXT', text.cells[a - 1])] if a > 0 else []
    shown += [('PASSAGE', c) for c in cells]
    if b + 1 < len(text.cells):
        shown.append(('CONTEXT', text.cells[b + 1]))
    parts, passage = [], set()
    for n, (role, cell) in enumerate(shown, start=1):
        seg = text.seg[cell]
        if role == 'PASSAGE':
            passage.add(n)
        # The page's own segment index is NOT shown: a model shown two numberings
        # answered in the wrong one (2 of the first 32 Gemini answers, 2026-09-28).
        parts.append(f'[{n}] {role} -- {cell[0]}\n'
                     f'Hebrew/Aramaic: {seg.get("hebrew", "").strip()}\n'
                     f'English: {seg.get("english", "").strip()}')
    head = (f'The PASSAGE is segments [{min(passage)}] to [{max(passage)}] below. '
            f'Answer `segments` with these bracketed numbers.')
    return head + '\n\n' + '\n\n'.join(parts), passage


class Refusal(RuntimeError):
    """The model declined. Counted as a failure, never as a verdict."""


ANSWER_SCHEMA = {
    'type': 'object',
    'properties': {
        'verdict': {'type': 'string', 'enum': list(VERDICTS)},
        'rules': {'type': 'array', 'items': {'type': 'string'}},
        'segments': {'type': 'array', 'items': {'type': 'integer'}},
        'reason': {'type': 'string'},
    },
    'required': ['verdict', 'rules', 'segments', 'reason'],
    'additionalProperties': False,
}


def _parse(raw):
    s = (raw or '').strip()
    if s.startswith('```'):
        s = s.strip('`')
        s = s[s.find('{'):]
    a, b = s.find('{'), s.rfind('}')
    if a < 0 or b < a:
        raise ValueError('no JSON object in the answer')
    return json.loads(s[a:b + 1])


def ask(backend, system, user, passage_numbers):
    """One call. Anything but a valid answer is an outcome with NO verdict (Lesson 21)."""
    fail = lambda outcome, why: dict(outcome=outcome, verdict=None, rules=None,
                                     segments=None, reason=None, error=why)
    try:
        raw = backend(system, user)
    except Refusal as e:
        return fail('refused', str(e))
    except Exception as e:  # noqa: BLE001 -- counted, never read as a verdict
        return fail('failed', f'{type(e).__name__}: {e}')
    try:
        ans = _parse(raw)
    except Exception as e:  # noqa: BLE001
        return fail('invalid', f'unparseable: {e}; raw={str(raw)[:200]!r}')
    if not isinstance(ans, dict) or set(ANSWER_SCHEMA['required']) - set(ans):
        return fail('invalid', f'missing fields: {sorted(set(ANSWER_SCHEMA["required"]) - set(ans or {}))}')
    v, segs, rules = ans['verdict'], ans['segments'], ans['rules']
    if v not in VERDICTS:
        return fail('invalid', f'verdict {v!r} outside the vocabulary')
    if not isinstance(segs, list) or not all(isinstance(x, int) and not isinstance(x, bool) for x in segs):
        return fail('invalid', f'segments {segs!r} are not integers')
    if not set(segs) <= set(passage_numbers):
        return fail('invalid', f'segments {segs} outside the passage {sorted(passage_numbers)}')
    if v in ('story', 'borderline', 'out_of_scope') and not segs:
        return fail('invalid', f'a {v} verdict names no segments')
    if not isinstance(rules, list):
        return fail('invalid', 'rules is not a list')
    return dict(outcome='ok', verdict=v, segments=segs,
                rules=[r for r in rules if r in RULE_IDS],
                unknown_rules=[r for r in rules if r not in RULE_IDS],
                reason=ans.get('reason'), error=None)


# ---- backends ----------------------------------------------------------------

def gemini_backend():
    from src.story_detector_v11 import V7StoryDetector
    det = V7StoryDetector(model_name=MODELS['gemini'])
    if det.model_name != MODELS['gemini']:
        raise RuntimeError(f'detector resolved model {det.model_name}')

    def call(system, user):
        out = det._call_google(system + '\n\n---\n\n' + user, max_tokens=2048, json_mode=True)
        if not out:
            raise RuntimeError('empty or truncated response (see _call_google)')
        return out
    return call, {'model': det.model_name, 'thinking_level': det.thinking_level, 'temperature': 0.1}


class ClaudeCost:
    def __init__(self):
        self.lock, self.usage = threading.Lock(), Counter()

    def add(self, u):
        with self.lock:
            self.usage['input'] += u.input_tokens or 0
            self.usage['output'] += u.output_tokens or 0
            self.usage['cache_write'] += getattr(u, 'cache_creation_input_tokens', 0) or 0
            self.usage['cache_read'] += getattr(u, 'cache_read_input_tokens', 0) or 0
            self.usage['calls'] += 1

    def usd(self):
        return sum(self.usage[k] * CLAUDE_PRICE[k] / 1e6 for k in CLAUDE_PRICE)


def claude_backend(cost: ClaudeCost):
    import anthropic
    client = anthropic.Anthropic(max_retries=4)

    def call(system, user):
        # anthropic 0.75.0 predates the typed `output_config`; it goes in extra_body.
        # No server-side fallback: a fallback model answering would silently change
        # which model this arm measures. A refusal is counted instead.
        resp = client.messages.create(
            model=MODELS['claude'], max_tokens=16000,
            system=[{'type': 'text', 'text': system, 'cache_control': {'type': 'ephemeral'}}],
            messages=[{'role': 'user', 'content': user}],
            extra_body={'thinking': {'type': 'adaptive'},
                        'output_config': {'effort': CLAUDE_EFFORT,
                                          'format': {'type': 'json_schema', 'schema': ANSWER_SCHEMA}}},
        )
        cost.add(resp.usage)
        if resp.stop_reason == 'refusal':
            raise Refusal(f'stop_reason=refusal {getattr(resp, "stop_details", None)}')
        if resp.stop_reason == 'max_tokens':
            raise RuntimeError('stop_reason=max_tokens')
        return next((b.text for b in resp.content if b.type == 'text'), '')
    return call, {'model': MODELS['claude'], 'effort': CLAUDE_EFFORT, 'thinking': 'adaptive',
                  'sdk': anthropic.__version__}


# ---------------------------------------------------------------------------
# sets and runs
# ---------------------------------------------------------------------------

def smoke_set(units):
    """10 of his yes + 10 of his no, BLIND-est first: Gittin 2026-09-02, then Yevamot."""
    rng = random.Random(20260928)
    review = [u for u in units if u['kind'] == 'review']

    def rank(u):
        rounds = {v['round'] for v in u['verdicts']}
        return (0 if 'gittin_axes_review_2026-09-02.json' in rounds else
                1 if u['tractate'] == 'Yevamot' else 2)

    picked = []
    for label in ('yes', 'no'):
        pool = [u for u in review if u['label'] == label]
        rng.shuffle(pool)
        pool.sort(key=rank)                   # stable: random within each tier
        picked += pool[:10]
    return picked


def select(set_name, labels):
    units = labels['units']
    if set_name == 'smoke':
        return smoke_set(units)
    if set_name == 'full':
        return units
    raise ValueError(set_name)


def estimate(units, texts, backends):
    sys_chars = len(system_prompt())
    user_chars = [len(user_prompt(u, texts[u['tractate']])[0]) for u in units]
    tok = lambda chars: chars / 2.5          # Hebrew-heavy text: conservative
    out = {'calls_per_backend': len(units), 'system_tokens_est': round(tok(sys_chars))}
    if 'claude' in backends:
        inp = sum(tok(c) for c in user_chars)
        usd = (inp * CLAUDE_PRICE['input'] + len(units) * tok(sys_chars) * CLAUDE_PRICE['cache_read']
               + tok(sys_chars) * CLAUDE_PRICE['cache_write'] + len(units) * 1500 * CLAUDE_PRICE['output']) / 1e6
        out['claude_usd_est'] = round(usd, 2)
        out['claude_assumes'] = '1,500 output tokens/call (thinking+answer), system prompt cached'
        smoke = OUT_DIR / 'smoke.json'
        if smoke.exists():                   # a measured rate beats an assumed one
            m = json.loads(smoke.read_text())['meta']
            if m.get('prompt_sha') == prompt_sha() and m.get('claude_usage', {}).get('calls'):
                per_call = m['claude_usd'] / m['claude_usage']['calls']
                out['claude_usd_est'] = round(per_call * len(units), 2)
                out['claude_assumes'] = f'${per_call:.4f}/call, measured on the smoke run'
    return out


def run(set_name, backend_names, out_path, dry_run, workers):
    labels = json.loads((OUT_DIR / 'labels.json').read_text())
    units = select(set_name, labels)
    texts = {t: Text(t) for t in {u['tractate'] for u in units}}
    est = estimate(units, texts, backend_names)
    log.info('set=%s units=%d backends=%s estimate=%s', set_name, len(units), backend_names, est)
    if dry_run:
        print(json.dumps(est, indent=1))
        return 0
    if est.get('claude_usd_est', 0) > BUDGET_USD:  # the runtime check below also counts the smoke spend
        log.error('projected Claude spend $%.2f exceeds the $%.0f cap -- refusing', est['claude_usd_est'], BUDGET_USD)
        return 3

    load_env()
    system = system_prompt()
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=PROJECT_ROOT,
                            capture_output=True, text=True).stdout.strip()
    prior = json.loads(out_path.read_text()) if out_path.exists() else None
    results = {r['id']: r for r in (prior or {}).get('rows', [])}
    meta = (prior or {}).get('meta') or {
        'set': set_name, 'prompt': str(PROMPT_PATH.relative_to(PROJECT_ROOT)),
        'prompt_sha': prompt_sha(), 'rules_sha': hashlib.sha256(RULES_PATH.read_bytes()).hexdigest()[:12],
        'commit': commit, 'started': time.strftime('%Y-%m-%dT%H:%M:%S'), 'backends': {}}
    if meta['prompt_sha'] != prompt_sha():
        raise RuntimeError('prompt changed since this output was started -- use a new --out')
    cost = ClaudeCost()
    lock = threading.Lock()
    # The cap is for the whole item: every earlier run's Claude spend counts against it.
    # Only run outputs carry a `meta`; other artifacts share the directory
    # (list_misses.json is a list) and are skipped, not crashed on.
    runs = [json.loads(f.read_text()) for f in OUT_DIR.glob('*.json')
            if f.resolve() != out_path.resolve() and f.name != 'labels.json']
    spent = sum(r['meta'].get('claude_usd', 0) for r in runs if isinstance(r, dict) and 'meta' in r)
    cap = BUDGET_USD - spent

    def save():
        with lock:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            meta['claude_usage'] = dict(cost.usage)
            meta['claude_usd'] = round(cost.usd(), 4)
            out_path.write_text(json.dumps({'meta': meta, 'rows': list(results.values())},
                                           ensure_ascii=False, indent=1) + '\n')

    for name in backend_names:
        call, info = gemini_backend() if name == 'gemini' else claude_backend(cost)
        meta['backends'][name] = info
        # Resume: ask again only where no answer exists or the CALL failed (network,
        # billing). `invalid` and `refused` are the model's own answers -- counted, kept.
        todo = [u for u in units
                if results.get(u['id'], {}).get('answers', {}).get(name, {}).get('outcome') in (None, 'failed')]

        def one(u):
            prompt, passage = user_prompt(u, texts[u['tractate']])
            ans = ask(call, system, prompt, passage)
            with lock:
                row = results.setdefault(u['id'], {k: u[k] for k in (
                    'id', 'kind', 'tractate', 'key', 'label', 'evidence', 'cited_in_rules', 'cells')})
                row.setdefault('answers', {})[name] = ans
            log.info('%-7s %-40s his=%-12s -> %s %s', name, u['id'][:40], u['label'],
                     ans['outcome'], ans['verdict'] or ans['error'][:80])
            if name == 'claude' and cost.usd() > cap:
                raise SystemExit(f'Claude spend ${cost.usd():.2f} + ${spent:.2f} already spent '
                                 f'passed the ${BUDGET_USD:.0f} cap')
            return ans

        log.info('%s: %d calls to make', name, len(todo))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for i, _ in enumerate(pool.map(one, todo), start=1):
                if i % 10 == 0:
                    save()
        save()
    meta['finished'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    save()
    log.info('wrote %s; Claude usage %s = $%.2f', out_path, dict(cost.usage), cost.usd())
    return 0


def load_env():
    from dotenv import load_dotenv
    load_dotenv(ENV_PATH)
    load_dotenv(PROJECT_ROOT / '.env')
    missing = [k for k in ('GOOGLE_API_KEY', 'ANTHROPIC_API_KEY') if not os.getenv(k)]
    if missing:
        raise SystemExit(f'missing {missing} -- refusing to run')


# ---------------------------------------------------------------------------
# scoring
# ---------------------------------------------------------------------------

def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round((c - h) / d, 3), round((c + h) / d, 3)]


def _group(rows, models):
    a, b = models
    g = Counter()
    fails = {m: Counter() for m in models}
    splits, rule_cites = Counter(), Counter()
    for r in rows:
        ans = r['answers']
        for m in models:
            o = ans.get(m, {}).get('outcome')
            if o != 'ok':
                fails[m][o or 'missing'] += 1
        g['rows'] += 1
        va = ans.get(a, {}).get('verdict') if ans.get(a, {}).get('outcome') == 'ok' else None
        vb = ans.get(b, {}).get('verdict') if ans.get(b, {}).get('outcome') == 'ok' else None
        his = LABEL_TO_VERDICT.get(r['label'])
        for m, v in ((a, va), (b, vb)):
            if v is not None:
                g[f'{m}_answered'] += 1
                g[f'{m}_matches_him'] += v == his
                if r['label'] == 'no':
                    g[f'{m}_story_on_his_no'] += v == 'story'
                if r['label'] == 'yes':
                    g[f'{m}_not_on_his_yes'] += v == 'not'
                if v != his:
                    for rule in ans[m].get('rules') or ['(none)']:
                        rule_cites[f'{m}:{rule}'] += 1
        if va is None or vb is None:
            continue
        g['both_answered'] += 1
        agree = va == vb and va != 'unsure'
        if agree:
            g['models_agree'] += 1
            g['agreed_matches_him'] += va == his
            g[f'agreed_on_his_{r["label"]}'] += 1
            g[f'agreed_{va}_on_his_{r["label"]}'] += 1
        else:
            if va == his and vb != his:
                splits[a] += 1
            elif vb == his and va != his:
                splits[b] += 1
            else:
                splits['neither' if va != his else 'both'] += 1
    out = {k: 0 for k in ('rows', 'both_answered', 'models_agree', 'agreed_matches_him',
                          'agreed_on_his_no', 'agreed_story_on_his_no', 'agreed_borderline_on_his_no',
                          'agreed_on_his_yes', 'agreed_not_on_his_yes')}
    out.update(g)
    out['failures'] = {m: dict(c) for m, c in fails.items() if c}
    out['splits_side_with_him'] = dict(splits)
    out['rules_cited_when_disagreeing_with_him'] = dict(rule_cites.most_common())
    out['agreement_rate'] = round(g['models_agree'] / g['both_answered'], 3) if g['both_answered'] else None
    out['agreement_wilson'] = wilson(g['models_agree'], g['both_answered'])
    for lab in ('no', 'yes'):
        n = g[f'agreed_on_his_{lab}']
        k = g[f'agreed_{LABEL_TO_VERDICT[lab]}_on_his_{lab}']
        out[f'agreed_right_on_his_{lab}'] = k
        out[f'agreed_right_on_his_{lab}_wilson'] = wilson(k, n)
    return out


def summarise(rows, models=('gemini', 'claude')):
    out = {'pooled': _group(rows, models)}
    for t in TRACTATES:
        sub = [r for r in rows if r['tractate'] == t]
        if sub:
            out[t] = _group(sub, models)
    return out


def merge_runs(paths):
    rows = {}
    for p in paths:
        for r in json.loads(Path(p).read_text())['rows']:
            rows.setdefault(r['id'], dict(r, answers={}))['answers'].update(r['answers'])
    return list(rows.values())


def markdown(out, models=('gemini', 'claude')):
    """The finding's tables, generated so the prose cannot drift from the numbers."""
    pct = lambda k, n: f'{k}/{n} = {100 * k / n:.0f}%' if n else '—'
    ci = lambda w: f'[{100 * w[0]:.0f}–{100 * w[1]:.0f}]' if w else ''
    lines = []
    for name, groups in out.items():
        lines += [f'\n**{name}**\n',
                  '| | both answered | models agree [95%] | agreed on his no: right / story / borderline [95% right] '
                  '| agreed on his yes: right / not [95% right] | splits: ' + ' / '.join(models) + ' / neither sides with him '
                  '| failures |', '|---|---|---|---|---|---|---|']
        for t, g in groups.items():
            fails = '; '.join(f'{m} {sum(c.values())}' for m, c in g['failures'].items()) or '0'
            sp = g['splits_side_with_him']
            lines.append(
                f"| {t} | {g['both_answered']} | {pct(g['models_agree'], g['both_answered'])} {ci(g['agreement_wilson'])} "
                f"| {g['agreed_right_on_his_no']}/{g['agreed_on_his_no']} · {g['agreed_story_on_his_no']} · "
                f"{g['agreed_borderline_on_his_no']} {ci(g['agreed_right_on_his_no_wilson'])} "
                f"| {g['agreed_right_on_his_yes']}/{g['agreed_on_his_yes']} · {g['agreed_not_on_his_yes']} "
                f"{ci(g['agreed_right_on_his_yes_wilson'])} "
                f"| {' / '.join(str(sp.get(m, 0)) for m in models)} / {sp.get('neither', 0)} | {fails} |")
    return '\n'.join(lines)


def report(paths, models=('gemini', 'claude')):
    rows = merge_runs(paths)
    out = {}
    for name, pred in (('review', lambda r: r['kind'] == 'review'),
                       ('review_not_cited', lambda r: r['kind'] == 'review' and not r['cited_in_rules']),
                       ('review_cited', lambda r: r['kind'] == 'review' and r['cited_in_rules']),
                       ('list', lambda r: r['kind'] == 'list'),
                       ('corrected', lambda r: r['kind'] == 'corrected'),
                       ('all_scored', lambda r: r['kind'] in ('review', 'list'))):
        sub = [r for r in rows if pred(r)]
        if sub:
            out[name] = summarise(sub, models)
    return out, rows


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('labels')
    r = sub.add_parser('run')
    r.add_argument('--set', choices=('smoke', 'full'), required=True)
    r.add_argument('--backend', choices=('gemini', 'claude', 'both'), required=True)
    r.add_argument('--out', required=True)
    r.add_argument('--dry-run', action='store_true')
    r.add_argument('--workers', type=int, default=6)
    p = sub.add_parser('report')
    p.add_argument('inputs', nargs='+')
    p.add_argument('--models', default='gemini,claude')
    p.add_argument('--out')
    p.add_argument('--markdown', action='store_true')
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [consensus-judge] %(message)s',
                        handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                                  logging.StreamHandler(sys.stdout)])
    for noisy in ('httpx', 'google_genai', 'anthropic'):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    if args.cmd == 'labels':
        labels = build_labels()
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / 'labels.json').write_text(json.dumps(labels, ensure_ascii=False, indent=1) + '\n')
        log.info('review files: %s', json.dumps(labels['inventory'], indent=1))
        log.info('verdict rows read per round: %s', json.dumps(labels['rows_read_per_round'], indent=1))
        log.info('what each rule did: %s', json.dumps(labels['rule_counts'], indent=1, ensure_ascii=False))
        log.info('units kind|tractate|label: %s', json.dumps(labels['table'], indent=1))
        log.info('conflicts (not scored): %d  unknown spans: %d  list superseded: %d  list unlocated: %d',
                 len(labels['conflicts']), len(labels['unknown']), len(labels['list_superseded']),
                 labels['list_unlocated'])
        return 0
    if args.cmd == 'run':
        backends = ['gemini', 'claude'] if args.backend == 'both' else [args.backend]
        return run(args.set, backends, Path(args.out), args.dry_run, args.workers)
    if args.cmd == 'report':
        models = tuple(args.models.split(','))
        out, _ = report(args.inputs, models)
        text = markdown(out, models) if args.markdown else json.dumps(out, indent=1)
        if args.out:
            Path(args.out).write_text(text + '\n')
        print(text)
        return 0


if __name__ == '__main__':
    sys.exit(main())
