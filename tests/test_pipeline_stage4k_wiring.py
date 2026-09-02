#!/usr/bin/env python3
"""
v11's pipeline must call a span mechanism v11 actually has.

THE DEFECT, found 2026-08-31 while preparing the first run on a new tractate.
`run_pipeline()` Stage 4k called `self.extract_text_spans_via_llm(...)`. That is
Wave 4's character-offset mechanism, deleted from v11 when Wave 5's clause
selection replaced it — the module docstring says so at the top of the file. v11
has the replacement and not the original, so with a live client the pipeline
raised `AttributeError` at Stage 4k.

Where it raised is the expensive part: Stage 4k runs *after* Stage 1 triage, all
of Stage 2, and the Stage 4d/4f stitching calls. On a 178-page tractate that is
the entire spend of the run, thrown away at the last step.

It survived because v11 has only ever been driven by `run_wave5_clause_spans.py`,
which calls `extract_text_spans_via_clauses()` directly on an existing output.
Nothing had run v11 end to end — so nothing had reached line 4k with a client
attached, and no test asserted the pipeline's own wiring.

The tests below need no API key, no network and no model: the client is a
sentinel object, and every method the pipeline would call on it is stubbed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ground_truth import EventType                         # noqa: E402
from src.story_detector_v11 import V7StoryDetector             # noqa: E402

PAGES = [{"ref": f"Gittin {n}", "segments": [
    {"index": i, "english": f"e{i}", "hebrew": "אָמַר רַב. מַעֲשֶׂה בְּאֶחָד."}
    for i in range(3)]} for n in ("2a", "2b")]

TRIAGE = {p["ref"]: [EventType.NARRATIVE_EVENT] * 3 for p in PAGES}


def test_the_span_method_the_pipeline_names_exists():
    """The whole defect in one line: 4k named a method v11 does not have."""
    assert hasattr(V7StoryDetector, 'extract_text_spans_via_clauses')
    assert not hasattr(V7StoryDetector, 'extract_text_spans_via_llm'), \
        "Wave 4's char-offset mechanism was removed in v11 (Lesson 16) — " \
        "the pipeline must not call it"


def _detector(calls):
    d = V7StoryDetector.__new__(V7StoryDetector)
    d.api_key, d.model_name, d.ground_truth_db = None, "stub", None
    d.thinking_level, d.span_repairs = None, []
    d.client = object()                    # a client IS attached: the 4k branch runs
    d.detect_stories = lambda ref, segs, ev, p=None, n=None: [        # type: ignore
        {'start_segment': 0, 'end_segment': 1, 'classification': 'HIGH_CONFIDENCE'}]
    d.stitch_cross_page_continuation = lambda *a, **k: 0              # type: ignore
    d.continuation_check = lambda *a, **k: 0                          # type: ignore

    def spans(pages):
        calls.append('clauses')
        return {'clause_llm': 1, 'clause_kept_full': 0,
                'no_clause_split': 0, 'skipped': 0}
    d.extract_text_spans_via_clauses = spans                          # type: ignore
    return d


def test_run_pipeline_reaches_the_end_with_a_client_attached():
    calls = []
    out = _detector(calls).run_pipeline(PAGES, triage_results=TRIAGE, delay=0,
                                        tractate='Gittin')
    assert calls == ['clauses'], "Stage 4k must call the clause mechanism"
    assert len(out['pages']) == 2
    assert out['span_repairs'] == []


def test_the_span_counts_are_reported_under_their_own_keys():
    """The Wave 4 print read `llm` / `llm_kept_full`; Wave 5 returns
    `clause_llm` / `clause_kept_full`. Reporting a run by a key it does not have
    is a KeyError one line after the fix — so pin the keys too."""
    out = _detector([]).run_pipeline(PAGES, triage_results=TRIAGE, delay=0,
                                     tractate='Gittin')
    assert set(out['span_stats']) == {'clause_llm', 'clause_kept_full',
                                      'no_clause_split', 'skipped'}
