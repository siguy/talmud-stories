"""A failed 4d / 4f call is counted and written to the output, not only printed.

2026-11-07 review, P3: the stitch (4d) and continuation-check (4f) LLM failures were
printed and nothing else -- a run whose every 4f call failed read the same as one
where no story continued (Lesson 38's shape). They now accumulate in
`stage4_call_failures` as (stage, ref) and the result dict carries the list.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.event_triage import EventType  # noqa: E402
from src.story_detector_v11 import V7StoryDetector  # noqa: E402

N = EventType.NARRATIVE_EVENT


def _pages():
    segs = [{'index': i, 'hebrew': 'א', 'english': 'a'} for i in range(3)]
    return [{'ref': 'X 2a', 'segments': segs}, {'ref': 'X 2b', 'segments': segs},
            {'ref': 'X 3a', 'segments': segs}]


def _detector(monkeypatch, call_google):
    d = V7StoryDetector.__new__(V7StoryDetector)
    d.client = object(); d.model_name = 'test-model'; d.thinking_level = None
    d.ground_truth = None; d.ground_truth_db = None
    monkeypatch.setattr('time.sleep', lambda *_: None)
    d._call_google = call_google

    def detect(ref, *a):
        # 2a: a story reaching the page end and flagged as continuing (4d's case).
        # 2b: a story reaching the page end with no flag (4f's case).
        if ref == 'X 2a':
            return [{'start_segment': 1, 'end_segment': 2, 'classification': 'YES',
                     'continuation': {'continues_to_next_page': True}}]
        if ref == 'X 2b':
            return [{'start_segment': 1, 'end_segment': 2, 'classification': 'YES'}]
        return []
    d.detect_stories = detect
    return d


def _run(d):
    pages = _pages()
    return d.run_pipeline(pages, triage_results={p['ref']: [N, N, N] for p in pages},
                          delay=0)


def _boom(*a, **k):
    raise RuntimeError('503 UNAVAILABLE')


@pytest.mark.parametrize('call_google', [_boom, lambda *a, **k: ''],
                         ids=['exception', 'empty-response'])
def test_failed_4d_and_4f_calls_are_in_the_result(monkeypatch, call_google):
    d = _detector(monkeypatch, call_google)
    out = _run(d)
    assert ('4d', 'X 2a') in out['stage4_call_failures']
    assert ('4f', 'X 2b') in out['stage4_call_failures']


def test_key_is_written_when_nothing_failed(monkeypatch):
    d = _detector(monkeypatch, lambda *a, **k: '{"continues_on_page": false, "continues": false}')
    out = _run(d)
    assert out['stage4_call_failures'] == []


def test_result_names_this_detector(monkeypatch):
    # run_pipeline said 'v10' -- the runner overwrote it with a literal (P3).
    d = _detector(monkeypatch, lambda *a, **k: '{"continues_on_page": false, "continues": false}')
    assert _run(d)['version'] == 'v11'
