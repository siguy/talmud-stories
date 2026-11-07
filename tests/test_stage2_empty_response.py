"""An empty or truncated Stage 2 response is a FAILED call, never "no stories".

`_call_google` returns "" for no candidates, empty parts and MAX_TOKENS. Before the
2026-11-07 fix `_call_stage2` turned two of those into `[]`, `_detect_with_retry`
saw no exception, and the page was written `stories: []` with no `stage2_error` --
Lesson 21 in its purest form (finding 3 of
docs/findings/2026-11-07-pre-eruvin-code-review.md). The run must carry the page,
marked, so the scorer can keep it out of Detection's denominator.
"""
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.event_triage import EventType  # noqa: E402
from src.story_detector_v11 import V7StoryDetector  # noqa: E402

N = EventType.NARRATIVE_EVENT
PAGES = [{'ref': f'X {i}a', 'segments': [{'index': 0, 'hebrew': 'א', 'english': 'a'}]}
         for i in range(3)]
TRIAGE = {p['ref']: [N] for p in PAGES}


def _detector(monkeypatch, empty_on):
    d = V7StoryDetector.__new__(V7StoryDetector)
    d.client = object(); d.model_name = 'test-model'; d.thinking_level = None
    d.ground_truth = None; d.ground_truth_db = None
    d.calls = []
    monkeypatch.setattr(d, 'build_detection_prompt', lambda ref, *a, **k: ref)

    def call_google(prompt, *a, **k):
        d.calls.append(prompt)
        if prompt == empty_on:
            return ''
        return '{"stories": []}'      # a real, parseable "nothing here"
    monkeypatch.setattr(d, '_call_google', call_google)
    monkeypatch.setattr('time.sleep', lambda *_: None)
    return d


def test_two_empty_responses_are_recorded_as_a_failed_call(monkeypatch):
    d = _detector(monkeypatch, empty_on='X 1a')
    out = d.run_pipeline(PAGES, triage_results=TRIAGE, delay=0)
    page = next(p for p in out['pages'] if p['ref'] == 'X 1a')
    assert page.get('stage2_error'), 'an empty response was written as "no stories"'
    assert page['stories'] == []
    assert d.stage2_errors == ['X 1a']
    assert d.calls.count('X 1a') == 2, 'one retry, as before'
    # a parseable empty answer is a judgment, not a failure
    for ref in ('X 0a', 'X 2a'):
        assert 'stage2_error' not in next(p for p in out['pages'] if p['ref'] == ref)


def test_no_candidates_is_counted_like_empty_parts():
    d = V7StoryDetector.__new__(V7StoryDetector)
    d.model_name = 'test-model'; d.thinking_level = None
    d.client = SimpleNamespace(models=SimpleNamespace(
        generate_content=lambda **k: SimpleNamespace(candidates=[])))
    assert d._call_google('p') == ''
    assert len(getattr(d, 'empty_responses', [])) == 1
