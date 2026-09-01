#!/usr/bin/env python3
"""
A failed triage call must never be recorded as "we looked and found nothing."

THE DEFECT, found 2026-08-30 while writing docs/capabilities/1_triage.md.

`triage_page()` returned `[DELIBERATION] * n` when the model's response would not parse,
under the comment *"Default: all DELIBERATION (safest — won't skip pages incorrectly)."*
The comment is backwards. All-DELIBERATION gives `narrative_count == 0`, which fails both
keep-conditions in `should_skip_page()`, so a failed call **silently discarded the page**
— in the one stage of the pipeline whose errors leave no trace downstream
(FRAMEWORK §1.1: *"a page never examined produces no record of what was lost"*).

This is Lesson 21's shape: a failure recorded with the value that also means a considered
judgment. It is worse here than where Lesson 21 was learned, because there is no harness
that can see it. Triage recall is only measurable against an external blind list, and only
for the tractates that have one.

These tests were written first and watched fail. No API key, no network, no model.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.event_triage import EventTriager          # noqa: E402
from src.ground_truth import EventType             # noqa: E402

SEGMENTS = [{"index": i, "english": f"segment {i}", "hebrew": ""} for i in range(6)]


def triager_whose_model_returns(payload: str) -> EventTriager:
    """An EventTriager wired to a stub. `payload` is whatever the model 'replies'."""
    t = EventTriager.__new__(EventTriager)
    t.api_key, t.model_name, t.ground_truth_db = "stub", "stub", None
    t.client = object()                       # only truthiness is checked
    t._call_google = lambda prompt: payload   # type: ignore[method-assign]
    return t


# ---------------------------------------------------------------- the defect

def test_a_page_is_not_discarded_because_the_triage_call_failed():
    """The one that matters. An unparseable response must not cost us the page."""
    events = triager_whose_model_returns("not json at all").triage_page("Ketubot 20a", SEGMENTS)
    assert not EventTriager.should_skip_page(events), (
        "a failed triage call caused the page to be SKIPPED. Stage 1 discards are "
        "invisible and permanent, so this loses a page with no trace anywhere.")


def test_a_failure_is_distinguishable_from_a_judgment():
    """Lesson 21: a failure must never carry the value that also means a real verdict.

    'Every segment is DELIBERATION' is a legitimate thing for the model to say about a
    purely legal page. If a crash says the same thing, no reader can tell them apart.
    """
    failed = triager_whose_model_returns("garbage").triage_page("Ketubot 20a", SEGMENTS)
    assert set(failed) == {EventType.TRIAGE_FAILED}, (
        f"a failed call produced {set(failed)}, which is indistinguishable from a "
        f"considered judgment about a legal page")


def test_failures_are_counted_and_reported():
    """An error rate nobody counts is an error rate nobody notices."""
    good = [EventType.NARRATIVE_EVENT, EventType.NARRATIVE_EVENT, EventType.DELIBERATION]
    summary = EventTriager.summarize_triage({
        "Ketubot 2a": good,
        "Ketubot 2b": [EventType.TRIAGE_FAILED] * 3,
        "Ketubot 3a": [EventType.TRIAGE_FAILED] * 5,
    })
    assert summary.get("failed") == 2, f"failed pages not counted: {summary}"
    assert "Ketubot 2b" in summary.get("failed_refs", []), (
        "a failed page must be nameable, not just tallied — you cannot re-run what you "
        "cannot identify")


# ---------------------------------------------------------------- no regression

def test_a_genuinely_legal_page_is_still_skipped():
    """The fix must not turn triage off. This is the whole point of Stage 1."""
    assert EventTriager.should_skip_page([EventType.DELIBERATION] * 6)
    assert EventTriager.should_skip_page(
        [EventType.DELIBERATION, EventType.DELIBERATION, EventType.VERBAL_ACT])


@pytest.mark.parametrize("events,keep", [
    ([EventType.NARRATIVE_EVENT] * 2 + [EventType.DELIBERATION], True),
    ([EventType.NARRATIVE_EVENT, EventType.VERBAL_ACT, EventType.VERBAL_ACT], True),
    # Was False until 2026-08-31, when the corroboration clause was removed and a
    # single NARRATIVE_EVENT became sufficient. This row is the one that moved;
    # it is kept here rather than deleted so the change stays visible from the
    # fail-open tests, whose own behaviour is untouched.
    ([EventType.NARRATIVE_EVENT, EventType.DELIBERATION, EventType.DELIBERATION], True),
    ([], False),
])
def test_the_keep_rule_still_requires_a_narrative_event(events, keep):
    assert (not EventTriager.should_skip_page(events)) is keep


def test_a_successful_response_still_parses_normally():
    payload = ('{"segment_events": ['
               '{"index": 0, "event_type": "NARRATIVE_EVENT"},'
               '{"index": 1, "event_type": "VERBAL_ACT"},'
               '{"index": 2, "event_type": "NARRATIVE_EVENT"}]}')
    events = triager_whose_model_returns(payload).triage_page("Ketubot 10b", SEGMENTS)
    assert events[0] == EventType.NARRATIVE_EVENT
    assert events[1] == EventType.VERBAL_ACT
    assert events[2] == EventType.NARRATIVE_EVENT
    assert EventType.TRIAGE_FAILED not in events
    assert not EventTriager.should_skip_page(events)


def test_the_cached_triage_files_still_deserialize():
    """Adding an enum member must not break the caches the shipped numbers rest on."""
    import json
    root = Path(__file__).resolve().parent.parent
    for name in ("event_triage_2-60.json", "event_triage_61-112.json",
                 "event_triage_kiddushin.json"):
        raw = json.loads((root / "results/v7" / name).read_text())
        results = raw.get("triage_results", raw)
        for ref, values in list(results.items())[:25]:
            for v in values:
                EventType(v)   # raises ValueError if a member disappeared
