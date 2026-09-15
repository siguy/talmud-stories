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

import importlib  # noqa: E402

import src.story_detector_v11 as detector_module  # noqa: E402
from src.event_triage import EventType  # noqa: E402

PLACEHOLDER = re.compile(r'\{[a-z_]{3,}\}')


def _prompt(monkeypatch, series_rule):
    # `_SERIES_RULE` is read at import time, so the env var must be set BEFORE the
    # module is (re)loaded. Setting it afterwards silently changes nothing — which is
    # also true of a real run, where the flag comes from the process environment.
    monkeypatch.setenv('SERIES_RULE', series_rule)
    importlib.reload(detector_module)
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


@pytest.mark.parametrize('series_rule', ['0', '1'])
def test_no_unsubstituted_placeholder_reaches_the_model(monkeypatch, series_rule):
    prompt = _prompt(monkeypatch, series_rule)
    leftover = PLACEHOLDER.findall(prompt)
    assert not leftover, (
        f'unsubstituted placeholder(s) in the prompt with SERIES_RULE={series_rule}: '
        f'{leftover} — an f-string was almost certainly split by a concatenation')


def test_the_gated_clause_changes_nothing_else(monkeypatch):
    """Off must be byte-identical to on-minus-the-clause.

    A gated experiment arm is only a control if the control path is the same prompt.
    """
    off = _prompt(monkeypatch, '0')
    on = _prompt(monkeypatch, '1')
    assert len(on) > len(off), 'SERIES_RULE=1 did not add the clause'
    assert 'SERIES OF PARALLEL INCIDENTS' in on
    assert 'SERIES OF PARALLEL INCIDENTS' not in off
    # Removing the clause text from the treatment prompt must give back the control.
    start = on.index('### A SERIES OF PARALLEL INCIDENTS')
    end = on.index('## EMBEDDED STORIES')
    assert on[:start] + on[end:] == off, (
        'the gate changes the prompt beyond the clause itself — whitespace included')
