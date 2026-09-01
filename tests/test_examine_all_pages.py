#!/usr/bin/env python3
"""
Bypassing Stage 1 must not fabricate Stage 1's output.

THE DEFECT, proven 2026-09-01 in docs/findings/2026-09-01-contaminated-no-triage-ablation.md.

`run_pipeline(skip_triage=True)` reads as "run without Stage 1". It did not. It replaced
the triage result with `[DELIBERATION] * n_segs` for every page — and DELIBERATION is not
absence, it is a *verdict*: "legal reasoning, nobody is doing anything." Four consumers
then believed it:

  - `detect_stories()` renders the label per segment into Stage 2's prompt as
    `[DELIBERATION] Seg N:`, under a header stating each segment "has been pre-classified
    by event type" — so every page was introduced to the model as containing nothing
    narrative, and then the model was asked to find stories on it.
  - the cross-page context blocks, same rendering for the neighbouring daf.
  - `refine_boundaries_with_event_tags()` and `merge_cross_page_stories_v7()`.
  - post-processing `rule3_v6_ensemble`, which demotes a proposal on a page holding
    "only 0 NARRATIVE_EVENT(s)" — true of every page under the stub.

Worst of the four: the `elif` fired even when the caller had SUPPLIED real triage results,
so passing correct labels alongside the flag silently discarded them.

Measured cost, on the one archived run built with it
(`results/v7/ablation_v7_no_triage.json`): the arm examining 3x the pages found 5 FEWER of
Jeff's blind-list stories, 3 of them on pages both arms examined — arithmetically
impossible for a change that only adds pages. NOT_A_STORY went 2 -> 44 of 74 -> 91.

This is `EventType.TRIAGE_FAILED`'s own docstring one caller over ("It must never be
DELIBERATION, which is a real verdict about a legal passage"), and Lesson 21's shape: an
absence recorded with the value that also means a considered judgment.

These tests were written first and watched fail. No API key, no network, no model.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ground_truth import EventType                       # noqa: E402
from src.story_detector_v11 import V7StoryDetector             # noqa: E402

PAGES = [
    {"ref": "Ketubot 2a", "segments": [{"index": i, "english": f"a{i}", "hebrew": ""} for i in range(4)]},
    {"ref": "Ketubot 2b", "segments": [{"index": i, "english": f"b{i}", "hebrew": ""} for i in range(3)]},
]

# Real labels, of the shape a cache holds: 2a would be SKIPPED by the shipped rule
# (no narrative event), 2b would be kept. The flag must change which pages are
# examined — never what the labels say.
CACHED = {
    "Ketubot 2a": [EventType.DELIBERATION, EventType.VERBAL_ACT,
                   EventType.DELIBERATION, EventType.HABITUAL],
    "Ketubot 2b": [EventType.NARRATIVE_EVENT, EventType.VERBAL_ACT, EventType.DELIBERATION],
}


def detector_that_records_labels(seen):
    """A detector with no client, whose Stage 2 records the labels handed to it."""
    d = V7StoryDetector.__new__(V7StoryDetector)
    d.api_key, d.model_name, d.ground_truth_db, d.client = None, "stub", None, None
    d.thinking_level = None

    def detect_stories(ref, segments, event_types, prev_ctx=None, next_ctx=None):
        seen[ref] = list(event_types)
        return []

    d.detect_stories = detect_stories                     # type: ignore[method-assign]
    return d


def run(examine_all, seen, **kw):
    return detector_that_records_labels(seen).run_pipeline(
        PAGES, triage_results={k: list(v) for k, v in CACHED.items()},
        delay=0, examine_all_pages=examine_all, tractate="Ketubot", **kw)


# ------------------------------------------------------- the defect, stated as a test

def test_supplied_labels_survive_the_bypass():
    """THE regression. Before the fix these came back all-DELIBERATION."""
    seen: dict = {}
    run(True, seen)
    assert seen["Ketubot 2a"] == CACHED["Ketubot 2a"]
    assert seen["Ketubot 2b"] == CACHED["Ketubot 2b"]


def test_the_bypass_never_stamps_deliberation_over_a_real_label():
    """The specific lie: a page of mixed labels must not arrive as uniform DELIBERATION."""
    seen: dict = {}
    run(True, seen)
    for ref, labels in seen.items():
        assert set(labels) != {EventType.DELIBERATION}, (
            f"{ref} arrived at Stage 2 as uniform DELIBERATION — the stub is back")
        assert labels == CACHED[ref]


def test_labels_are_identical_with_and_without_the_bypass():
    """The flag selects pages. It is not an input to how any page is read."""
    on, off = {}, {}
    run(True, on)
    run(False, off)
    for ref in off:                       # 2b is examined either way
        assert on[ref] == off[ref], f"{ref}: the bypass changed the labels, not just the page set"


# --------------------------------------------------------------- what the flag DOES do

def test_the_bypass_examines_the_page_the_rule_would_skip():
    seen: dict = {}
    result = run(True, seen)
    assert set(seen) == {"Ketubot 2a", "Ketubot 2b"}
    assert not [p for p in result["pages"] if p.get("skipped_by_triage")]


def test_without_the_bypass_the_shipped_rule_still_skips():
    seen: dict = {}
    result = run(False, seen)
    assert set(seen) == {"Ketubot 2b"}, "2a has no narrative event; the shipped rule skips it"
    assert [p["ref"] for p in result["pages"] if p.get("skipped_by_triage")] == ["Ketubot 2a"]


def test_the_bypass_only_ever_adds_pages():
    """The property whose violation exposed the original contamination."""
    on, off = {}, {}
    run(True, on)
    run(False, off)
    assert set(off) <= set(on), "turning the filter off removed a page from Stage 2"


# ------------------------------------------------------------------- the old spelling

def test_skip_triage_alias_still_works_and_warns():
    """Callers exist (tests/ablation_test.py:196). The alias keeps them running."""
    seen: dict = {}
    with pytest.warns(DeprecationWarning, match="examine_all_pages"):
        detector_that_records_labels(seen).run_pipeline(
            PAGES, triage_results={k: list(v) for k, v in CACHED.items()},
            delay=0, skip_triage=True, tractate="Ketubot")
    assert set(seen) == {"Ketubot 2a", "Ketubot 2b"}
    assert seen["Ketubot 2a"] == CACHED["Ketubot 2a"], "the alias must not resurrect the stub"


def test_passing_both_spellings_is_refused():
    with pytest.raises(TypeError, match="both"):
        detector_that_records_labels({}).run_pipeline(
            PAGES, triage_results=dict(CACHED), delay=0,
            examine_all_pages=True, skip_triage=True)


# ----------------------------------------------------------- the frozen versions stay put

def test_lower_detector_versions_are_untouched():
    """v7-v10 are frozen ship points (CLAUDE.md). The contaminated ablation is evidence
    for the retraction and must stay reproducible from the code that produced it."""
    root = Path(__file__).resolve().parent.parent
    for v in (7, 8, 9, 10):
        src = (root / f"src/story_detector_v{v}.py").read_text()
        assert "Generate default triage (all DELIBERATION)" in src, (
            f"v{v} is a frozen ship point and still explains the archived ablation — do not fix it")


# ------------------------------------------------- the same lie, one page at a time

def test_a_page_missing_from_triage_arrives_as_unknown_not_deliberation():
    """The Stage 2 loop's own default was `[DELIBERATION] * len(segments)`.

    A page with no triage entry has not been judged deliberative — it has not been
    judged. `[]` renders as `[UNKNOWN] Seg N` via build_prompt's fallback, which is
    what the cross-page context blocks already did.
    """
    seen: dict = {}
    detector_that_records_labels(seen).run_pipeline(
        PAGES, triage_results={"Ketubot 2b": list(CACHED["Ketubot 2b"])},
        delay=0, examine_all_pages=True, tractate="Ketubot")
    assert seen["Ketubot 2a"] == [], "an unjudged page must not arrive labelled DELIBERATION"
    assert seen["Ketubot 2b"] == CACHED["Ketubot 2b"]
