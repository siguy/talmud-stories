#!/usr/bin/env python3
"""
A proposed span must lie inside its page — and a repair must be counted, not swallowed.

THE DEFECT. Stage 2 proposed `Ketubot 112b, start_segment -2, end_segment 0`
(docs/findings/2026-08-31-triage-recall-price.md, hit again by the 2026-09-01 proposal
screen). Nothing anywhere in the pipeline checked it. Python does not raise on a negative
index: every Stage 4 post-processor slices `segments[start:end + 1]`, so `-2` silently
means *the second segment from the END of the page* — a story whose text is taken from
the wrong place, with no error, no warning and no trace in the output.

The one that reached us was on a triage-discarded page, so it reached no published
number. That is luck, not a property of the code, and on a virgin tractate there is no
prior run to diff against.

Two halves, both required:

  1. The span is repaired — clamped when it overlaps the page, dropped when it does not.
  2. The repair is **counted and named** in the run output (Lesson 38). A loader that
     `continue`s past what it does not recognise, without saying what it dropped, is how
     a 25-verdict expert round stayed invisible for eight months. A silent clamp is the
     same shape: it turns a model defect into a boundary defect that reads as ours.

Written first and watched fail. No API key, no network, no model.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.story_detector_v11 import (                              # noqa: E402
    V7StoryDetector,
    validate_story_spans,
)

SEGS = [{"index": i, "english": f"e{i}", "hebrew": f"h{i}"} for i in range(10)]


def story(a, b, **kw):
    return dict(start_segment=a, end_segment=b,
                classification=kw.pop("classification", "HIGH_CONFIDENCE"), **kw)


# ---------------------------------------------------------------- the unit

def test_valid_span_is_untouched_and_reports_nothing():
    kept, repairs = validate_story_spans("Ketubot 2a", [story(3, 5)], 10)
    assert repairs == []
    assert (kept[0]["start_segment"], kept[0]["end_segment"]) == (3, 5)
    assert "span_repair" not in kept[0]


def test_the_112b_case_is_clamped_not_dropped():
    """`-2..0` overlaps the page. The proposal is real; only its start is wrong."""
    kept, repairs = validate_story_spans("Ketubot 112b", [story(-2, 0)], 10)
    assert (kept[0]["start_segment"], kept[0]["end_segment"]) == (0, 0)
    assert [r["action"] for r in repairs] == ["clamped"]
    assert repairs[0]["original"] == [-2, 0]
    assert repairs[0]["ref"] == "Ketubot 112b"
    # and the story itself carries the fact, so the output file is self-describing
    assert kept[0]["span_repair"]["original"] == [-2, 0]


def test_span_running_past_the_last_segment_is_clamped():
    kept, repairs = validate_story_spans("Ketubot 2a", [story(8, 14)], 10)
    assert (kept[0]["start_segment"], kept[0]["end_segment"]) == (8, 9)
    assert repairs[0]["action"] == "clamped"


def test_span_entirely_outside_the_page_is_dropped():
    kept, repairs = validate_story_spans("Ketubot 2a", [story(12, 15)], 10)
    assert kept == []
    assert repairs[0]["action"] == "dropped"
    assert "outside" in repairs[0]["reason"]


def test_reversed_span_keeps_the_end_the_model_got_right():
    """`Ketubot 22a` proposes `10..0` on an 11-segment page, with a summary describing
    a real story. Deleting it spends a Detection miss to avoid a Boundaries error.
    Swapping the ends would be a guess presented as a judgment (Lesson 21), so it
    collapses to the valid start and is marked for review."""
    kept, repairs = validate_story_spans("Ketubot 22a", [story(10, 0)], 11)
    assert (kept[0]["start_segment"], kept[0]["end_segment"]) == (10, 10)
    assert kept[0]["needs_review"] is True
    assert repairs[0]["action"] == "clamped"


def test_reversed_span_with_no_valid_end_is_dropped():
    kept, repairs = validate_story_spans("Ketubot 2a", [story(14, 2)], 10)
    assert kept == []
    assert repairs[0]["action"] == "dropped"


@pytest.mark.parametrize("a,b", [(None, 3), (3, None), ("2", 4), (2.5, 4), (True, 3)])
def test_non_integer_span_is_dropped(a, b):
    kept, repairs = validate_story_spans("Ketubot 2a", [story(a, b)], 10)
    assert kept == []
    assert repairs[0]["action"] == "dropped"


def test_empty_page_drops_everything_and_says_so():
    kept, repairs = validate_story_spans("Ketubot 2a", [story(0, 0)], 0)
    assert kept == []
    assert len(repairs) == 1


# ------------------------------------------------- failure injection, end to end

def _detector_returning(bad_stories):
    """A detector whose Stage 2 call returns exactly `bad_stories`. No client used."""
    d = V7StoryDetector.__new__(V7StoryDetector)
    d.api_key, d.model_name, d.ground_truth_db = None, "stub", None
    d.client = object()          # detect_stories refuses to run without one
    d.thinking_level = None
    d.span_repairs = []
    d._call_stage2 = lambda ref, prompt: [dict(s) for s in bad_stories]   # type: ignore
    d.build_detection_prompt = lambda *a, **k: "prompt"                   # type: ignore
    d._find_additional_stories = lambda *a, **k: []                       # type: ignore
    return d


def test_a_malformed_span_never_leaves_stage_2():
    d = _detector_returning([story(-2, 0), story(3, 4)])
    out = d.detect_stories("Ketubot 112b", SEGS, [])
    assert all(s["start_segment"] >= 0 for s in out)
    assert all(s["end_segment"] < len(SEGS) for s in out)
    assert len(out) == 2                       # clamped, not thrown away


def test_the_repair_is_recorded_on_the_detector_for_the_run_output():
    d = _detector_returning([story(-2, 0), story(99, 100)])
    d.detect_stories("Ketubot 112b", SEGS, [])
    actions = sorted(r["action"] for r in d.span_repairs)
    assert actions == ["clamped", "dropped"]
    assert all(r["ref"] == "Ketubot 112b" for r in d.span_repairs)


def test_a_clean_page_records_no_repairs():
    d = _detector_returning([story(0, 2), story(4, 9)])
    d.detect_stories("Ketubot 2a", SEGS, [])
    assert d.span_repairs == []
