#!/usr/bin/env python3
"""
Stage 2 must survive a crash, and must never cache a failure as a judgment.

THE DEFECT, from docs/findings/2026-09-03-yevamot-first-run.md. `run_pipeline()` walked
every examined page making Stage 2 calls and held the lot in memory until the tractate
finished. One raise discarded the whole spend. It did twice on 2026-09-03 — the second
time at page 35 of 106, on a PROHIBITED_CONTENT response with `parts=None`.

The fix is a checkpoint: the detector hands each completed page to a callback, the
runner persists it, and a re-run passes what it has back in as `resume_stories`.

Two properties carry the whole design, and both are tested here.

  1. **A resumed run must reproduce an uninterrupted one exactly.** Stage 4 runs over the
     whole tractate after Stage 2 and reads neighbouring pages' results — cross-page
     merge, stitching, the Mishnah filter, snap/trim, clause spans. If a resume perturbs
     any Stage 4 input the output changes silently. It does not: a cached page
     contributes exactly the stories and span repairs the original call produced, and
     every other Stage 4 input is recomputed from `pages` / `triage_results`, never read
     back from Stage 2's output. The one deliberate difference is `stage2_summary`,
     which says the run was resumed — provenance, and it must differ.

  2. **A page the model failed on is never cached** (Lesson 21). An empty response and an
     unreadable one both return `[]` to the caller, which is exactly what a page holding
     no stories returns. Caching that would let a resume inherit a silence from a page
     nobody ever read — the same disguise as the all-DELIBERATION triage default and the
     wave 5b `clause_kept_full` stamp.

These tests were written first and watched fail. No API key, no network, no model.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.ground_truth import EventType                       # noqa: E402
from src.story_detector_v11 import V7StoryDetector           # noqa: E402

FIXTURE = ROOT / 'tests' / 'fixtures' / 'wave5b_runner_pages.json'


def _runner():
    spec = importlib.util.spec_from_file_location(
        'run_new_tractate', ROOT / 'scripts' / 'run_new_tractate.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pages():
    """The real 4-page Kiddushin slice, ref + segments only."""
    doc = json.loads(FIXTURE.read_text())
    return [{'ref': p['ref'], 'segments': copy.deepcopy(p['segments'])}
            for p in doc['pages']]


def triage(pgs):
    """Labels that keep every page, so Stage 2 walks all four."""
    return {p['ref']: [EventType.NARRATIVE_EVENT] * len(p['segments']) for p in pgs}


def detector():
    """A detector with no client: Stage 3, 4d, 4f and the clause-span calls all
    short-circuit, so everything after Stage 2 is deterministic."""
    d = V7StoryDetector.__new__(V7StoryDetector)
    d.api_key, d.model_name, d.ground_truth_db, d.client = None, 'stub-model', None, None
    d.thinking_level = None
    d.span_repairs, d.empty_responses, d.parse_failures = [], [], []
    return d


def stories_for(ref, segments):
    """Deterministic, plausible Stage 2 output: one story per page."""
    return [{'start_segment': 0, 'end_segment': min(1, len(segments) - 1),
             'classification': 'HIGH_CONFIDENCE', 'summary': f'story on {ref}',
             'identifiable_characters': {'evidence': f'a sage on {ref}'}}]


class Boom(RuntimeError):
    pass


def stage2(d, crash_on=None, calls=None, empty_on=None):
    """Attach a fake Stage 2 to `d`. `crash_on` raises; `empty_on` simulates the
    Yevamot failure — the model returns nothing, the detector records it and hands
    back `[]`, which is indistinguishable from 'no stories here'."""
    def detect_stories(ref, segments, event_types, prev_ctx=None, next_ctx=None):
        if calls is not None:
            calls.append(ref)
        if crash_on and ref == crash_on:
            raise Boom(f'PROHIBITED_CONTENT on {ref}')
        if empty_on and ref == empty_on:
            d.empty_responses.append('PROHIBITED_CONTENT')
            return []
        return stories_for(ref, segments)
    d.detect_stories = detect_stories          # type: ignore[method-assign]
    return d


def run(d, pgs, **kw):
    return d.run_pipeline(pgs, triage_results=triage(pgs), delay=0,
                          tractate='Kiddushin', **kw)


def collector():
    """Stands in for the runner's on-disk cache."""
    cache = {}

    def on_page(ref, digest, stories, span_repairs):
        cache[ref] = {'digest': digest, 'stories': copy.deepcopy(stories),
                      'span_repairs': copy.deepcopy(span_repairs)}
    return cache, on_page


def payload(result):
    """Everything except the provenance block that says the run was resumed."""
    return {k: v for k, v in result.items() if k != 'stage2_summary'}


# ---------------------------------------------------------------------------
# 1. Resume reproduces an uninterrupted run
# ---------------------------------------------------------------------------

def test_resume_after_crash_is_byte_identical_except_the_field_that_says_it_resumed():
    pgs = pages()
    crash_ref = pgs[2]['ref']

    whole_cache, whole_cb = collector()
    whole = run(stage2(detector()), pages(), on_page_detected=whole_cb)

    # The run that dies on page 3 of 4.
    part_cache, part_cb = collector()
    with pytest.raises(Boom):
        run(stage2(detector(), crash_on=crash_ref), pages(), on_page_detected=part_cb)
    assert list(part_cache) == [p['ref'] for p in pgs[:2]], part_cache

    # The re-run. Its Stage 2 refuses to answer for anything already cached, so if the
    # resume silently re-detected a page this would raise instead of passing.
    calls = []
    d = detector()

    def only_new(ref, segments, event_types, prev_ctx=None, next_ctx=None):
        calls.append(ref)
        assert ref not in part_cache, f'{ref} was cached and was re-detected anyway'
        return stories_for(ref, segments)
    d.detect_stories = only_new                # type: ignore[method-assign]
    resumed_cache, resumed_cb = collector()
    resumed = run(d, pages(), resume_stories=dict(part_cache),
                  on_page_detected=resumed_cb)

    assert calls == [p['ref'] for p in pgs[2:]]
    assert (json.dumps(payload(whole), sort_keys=True, ensure_ascii=False)
            == json.dumps(payload(resumed), sort_keys=True, ensure_ascii=False))

    # The one difference, and it is the honest one.
    assert whole['stage2_summary']['resumed_from_cache'] == 0
    assert resumed['stage2_summary']['resumed_from_cache'] == 2
    assert whole['stage2_summary']['examined'] == resumed['stage2_summary']['examined']


def test_the_buckets_are_exclusive_and_sum_to_the_pages_stage_2_walked():
    pgs = pages()
    cache, cb = collector()
    r = run(stage2(detector(), empty_on=pgs[1]['ref']), pages(), on_page_detected=cb)
    s = r['stage2_summary']
    assert s['detected'] + s['resumed_from_cache'] + s['failed'] == s['examined']
    assert s == {'examined': 4, 'detected': 3, 'resumed_from_cache': 0, 'failed': 1,
                 'failed_refs': [pgs[1]['ref']]}


def test_a_cached_page_is_reused_only_for_the_identical_prompt():
    pgs = pages()
    cache, cb = collector()
    run(stage2(detector()), pages(), on_page_detected=cb)
    assert len(cache) == 4

    # Change one page's triage labels. The prompt renders the label per segment AND
    # renders the neighbouring dapim's labels as cross-page context, so the digest must
    # move on that page and on both its neighbours — and only there. That neighbour
    # sensitivity is the point of hashing the built prompt rather than the page.
    changed = pgs[1]['ref']
    labels = triage(pgs)
    labels[changed] = [EventType.DELIBERATION] * len(pgs[1]['segments'])
    calls = []
    d = stage2(detector(), calls=calls)
    d.run_pipeline(pages(), triage_results=labels, delay=0, tractate='Kiddushin',
                   resume_stories=dict(cache))
    assert calls == [pgs[0]['ref'], pgs[1]['ref'], pgs[2]['ref']], calls


def test_a_cache_entry_survives_stage_4_mutating_the_stories_it_handed_over():
    """Stage 4 edits stories in place. If it wrote through into the cache, the second
    resume would replay a story Stage 4 had already trimmed once."""
    cache, cb = collector()
    run(stage2(detector()), pages(), on_page_detected=cb)
    before = copy.deepcopy(cache)
    run(stage2(detector()), pages(), resume_stories=cache)
    assert cache == before


# ---------------------------------------------------------------------------
# 2. Failure injection — a failed call is never cached (Lesson 21)
# ---------------------------------------------------------------------------

def test_a_page_whose_call_raises_is_not_cached():
    pgs = pages()
    cache, cb = collector()
    with pytest.raises(Boom):
        run(stage2(detector(), crash_on=pgs[1]['ref']), pages(), on_page_detected=cb)
    assert pgs[1]['ref'] not in cache
    assert list(cache) == [pgs[0]['ref']]


def test_a_page_the_model_returned_nothing_for_is_not_cached_as_no_stories():
    """The Yevamot crash's quieter sibling: the response has no parts, the call
    returns `[]`, and `[]` is also what a page with no stories returns."""
    pgs = pages()
    empty_ref = pgs[2]['ref']
    cache, cb = collector()
    r = run(stage2(detector(), empty_on=empty_ref), pages(), on_page_detected=cb)

    assert empty_ref not in cache, 'a failed call was persisted as a judgment'
    assert set(cache) == {p['ref'] for p in pgs} - {empty_ref}
    assert r['stage2_summary']['failed_refs'] == [empty_ref]

    # And the resume re-asks for it rather than inheriting the silence.
    calls = []
    run(stage2(detector(), calls=calls), pages(), resume_stories=dict(cache))
    assert calls == [empty_ref]


def test_an_unreadable_json_response_is_recorded_as_a_failure_not_an_empty_page():
    """`_call_stage2` returns `[]` when neither attempt parses. Before this change
    nothing counted that, so it read as a page with no stories."""
    d = detector()          # model_name 'stub-model' -> plain-text mode
    d._call_google = lambda prompt, **kw: 'not json at all'   # type: ignore[method-assign]
    assert d._call_stage2('Kiddushin 7b', 'prompt') == []
    assert d.parse_failures == ['Kiddushin 7b']


# ---------------------------------------------------------------------------
# 3. The cache file itself
# ---------------------------------------------------------------------------

def header(mod, **over):
    h = mod.stage2_header('kiddushin', 'Kiddushin', 'stub-model', None,
                          'story_detector_v11')
    h.update(over)
    return h


def test_a_partial_write_is_never_readable_as_a_complete_cache(tmp_path):
    """The writer is atomic: it renders whole, fsyncs a temp file and os.replaces.
    A write that dies mid-flight leaves the previous complete cache in place."""
    mod = _runner()
    path = tmp_path / 'kiddushin.json'
    h = header(mod)
    mod.write_stage2_cache(path, h, {'Kiddushin 7b': {'digest': 'a', 'stories': []}})
    good = path.read_text()

    class Unserializable:
        pass
    with pytest.raises(TypeError):
        mod.write_stage2_cache(path, h, {'Kiddushin 8b': Unserializable()})

    assert path.read_text() == good
    assert json.loads(good)['pages'] == {'Kiddushin 7b': {'digest': 'a', 'stories': []}}
    assert not list(tmp_path.glob('*.tmp')), 'a temp file was left where a reader can find it'


def test_a_cache_from_another_model_or_detector_is_refused_not_blended(tmp_path):
    mod = _runner()
    path = tmp_path / 'kiddushin.json'
    mod.write_stage2_cache(path, header(mod, model='gemini-3-pro-preview'), {})
    with pytest.raises(SystemExit) as e:
        mod.load_stage2_cache(path, header(mod))
    assert 'gemini-3-pro-preview' in str(e.value)
    assert path.exists(), 'the refusal must not delete anything under results/'


def test_a_matching_cache_loads(tmp_path):
    mod = _runner()
    path = tmp_path / 'kiddushin.json'
    entries = {'Kiddushin 7b': {'digest': 'a', 'stories': [], 'span_repairs': []}}
    mod.write_stage2_cache(path, header(mod), entries)
    assert mod.load_stage2_cache(path, header(mod)) == entries
    assert mod.load_stage2_cache(tmp_path / 'absent.json', header(mod)) == {}
