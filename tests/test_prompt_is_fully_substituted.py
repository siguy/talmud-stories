"""The detection prompt must never reach the model with a placeholder in it.

On 2026-09-08 a one-line splice into the prompt — inserting a gated clause — turned the
tail of an f-string into a plain string. `{cross_page}` and `{few_shot_section}` were
then sent to the model literally, so **every call lost its few-shot examples and its
cross-page context**. Recall on a 20-page Yevamot slice fell 83.3% -> 50.7% and the
symptom read as model drift: it was blamed on a preview endpoint, on thinking levels and
on run-to-run variance across two nights before the prompt was diffed.

Nothing failed. The prompt was still a valid prompt.
"""
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import src.story_detector_v14 as detector_module  # noqa: E402  (the live detector)
from src.event_triage import EventType  # noqa: E402

PLACEHOLDER = re.compile(r'\{[a-z_]{3,}\}')


def _prompt():
    V7StoryDetector = detector_module.V7StoryDetector
    pages = json.loads(Path('results/sefaria/yevamot.json').read_text())
    pages = pages['pages'] if isinstance(pages, dict) else pages
    page = next(p for p in pages if p['ref'] == 'Yevamot 121b')
    triage = json.loads(Path('results/triage/yevamot.json').read_text())
    labels = triage.get('triage_results', triage)['Yevamot 121b']
    detector = V7StoryDetector.__new__(V7StoryDetector)
    detector.ground_truth = None
    detector.ground_truth_db = None
    return V7StoryDetector.build_detection_prompt(
        detector, 'Yevamot 121b', page['segments'],
        [EventType(l) for l in labels], None, None)


def test_no_unsubstituted_placeholder_reaches_the_model():
    leftover = PLACEHOLDER.findall(_prompt())
    assert not leftover, (
        f'unsubstituted placeholder(s) in the prompt: {leftover} — an f-string was '
        'almost certainly split by a concatenation')


def test_live_detector_has_one_prompt_and_no_series_gate(monkeypatch):
    """v13 dropped SERIES_RULE (off, unmeasured, superseded by the twin pass). Setting
    the old env var must change nothing — v11 keeps the gate, frozen."""
    assert not hasattr(detector_module, '_SERIES_RULE')
    off = _prompt()
    monkeypatch.setenv('SERIES_RULE', '1')
    assert _prompt() == off
    assert 'SERIES OF PARALLEL INCIDENTS' not in off
