#!/usr/bin/env python3
"""
The prompt must carry the rules the expert stated — and say so where it does.

R-C3 (Jeff, 2026-09-01, on Gittin 57a): "clearly a story. After the custom you have the
one time event — One day the emperor's daughter…" A habitual opening is often the FRAME
of a story rather than a disqualifier.

R-C4 (same reply, on Gittin 38b): a dictum can contain a story — R. Yoḥanan's two
families, uprooted, inside Rabba's saying.

WHAT THESE TESTS DO NOT CLAIM. Putting a rule in the prompt is not the same as the model
following it: measured on the full tractate, this wording moved neither strict recall
(108/112 before and after) nor the four known misses, and the run-to-run churn it did
produce is indistinguishable from the noise floor without a same-code repeat (Lesson 22).
The rule is right and the mechanism is unresolved. These tests exist so the wording is
not quietly dropped while that is still true, and so the next person can tell a rule that
failed to work from a rule that was never tried.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ground_truth import EventType                        # noqa: E402
from src.story_detector_v11 import V7StoryDetector            # noqa: E402

SEGMENTS = [{'index': i, 'english': f'e{i}', 'hebrew': f'h{i}'} for i in range(3)]


@pytest.fixture(scope='module')
def prompt():
    d = V7StoryDetector.__new__(V7StoryDetector)
    d.api_key = d.client = d.ground_truth_db = None
    d.model_name, d.thinking_level = 'stub', None
    return d.build_detection_prompt('Gittin 57a', SEGMENTS,
                                    [EventType.HABITUAL] * len(SEGMENTS))


def test_a_habitual_opening_is_named_as_a_frame_not_a_disqualifier(prompt):
    assert 'היה רגיל' in prompt, 'the habitual disqualifier itself must still be there'
    assert 'FRAME' in prompt
    assert 'Do not stop reading at the frame.' in prompt


def test_the_rule_carries_the_case_and_the_date(prompt):
    """A rule with no provenance cannot be defended when a number moves."""
    assert '2026-09-01' in prompt and '57a' in prompt


def test_speech_only_still_disqualifies_but_not_when_it_quotes_a_story(prompt):
    assert 'Speech alone is not a story' in prompt
    assert 'UNLESS a story is quoted' in prompt
    assert '38b' in prompt


def test_the_six_criteria_and_the_other_disqualifiers_are_untouched(prompt):
    for anchor in ('IDENTIFIABLE_CHARACTERS', 'MULTIPLE_EVENTS', 'CAUSAL_CHAIN',
                   'Hypothetical case', 'Biblical narrative', 'Mishna section'):
        assert anchor in prompt, anchor
