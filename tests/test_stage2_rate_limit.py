"""A rate limit is retried, a crash never loses finished pages, and 4k paces itself.

2026-11-07 review, finding 8:
  (a) HTTP 429 / RESOURCE_EXHAUSTED was not in RETRYABLE_STATUS, so it killed the run;
  (b) when an exception propagated out of the Stage 2 loop the final checkpoint write
      was skipped, losing up to CHECKPOINT_EVERY - 1 pages of spend;
  (c) 4k made one call per story back to back, with no delay.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.event_triage import EventType  # noqa: E402
from src.story_detector_v11 import V7StoryDetector  # noqa: E402

N = EventType.NARRATIVE_EVENT
PAGES = [{'ref': f'X {i}a', 'segments': [{'index': 0, 'hebrew': 'א', 'english': 'a'}]}
         for i in range(1, 6)]
TRIAGE = {p['ref']: [N] for p in PAGES}


def _bare():
    d = V7StoryDetector.__new__(V7StoryDetector)
    d.client = object(); d.model_name = 'test-model'; d.thinking_level = None
    d.ground_truth = None; d.ground_truth_db = None
    d.calls = []
    return d


# -- (a) ------------------------------------------------------------------

class RateLimited(Exception):
    code = 429


class Exhausted(Exception):
    """The google-genai shape: status in the message, no numeric code attribute."""


@pytest.mark.parametrize('exc', [RateLimited('429 Too Many Requests'),
                                 Exhausted('RESOURCE_EXHAUSTED: quota')])
def test_rate_limit_is_retried(monkeypatch, exc):
    d = _bare()
    sleeps = []
    monkeypatch.setattr('time.sleep', lambda s: sleeps.append(s))

    def detect(ref, *a):
        d.calls.append(ref)
        if len(d.calls) == 1:
            raise exc
        return [{'start_segment': 0, 'end_segment': 0, 'classification': 'YES'}]
    d.detect_stories = detect

    stories, err = d._detect_with_retry('X 1a', [], [], None, None)
    assert err is None and stories[0]['classification'] == 'YES'
    assert d.calls == ['X 1a', 'X 1a']
    assert sleeps == [15], 'the existing backoff was not used'


# -- (b) ------------------------------------------------------------------

class Crash(Exception):
    """Not retryable: propagates out of the Stage 2 loop."""


def test_crash_mid_loop_still_writes_finished_pages(monkeypatch, tmp_path):
    d = _bare()
    monkeypatch.setattr('time.sleep', lambda *_: None)
    monkeypatch.setattr(V7StoryDetector, 'CHECKPOINT_EVERY', 1000)

    def detect(ref, *a):
        d.calls.append(ref)
        if ref == 'X 3a':
            raise Crash('unhandled')
        return [{'start_segment': 0, 'end_segment': 0, 'classification': 'YES'}]
    d.detect_stories = detect

    ck = tmp_path / 'run.partial.json'
    with pytest.raises(Crash):
        d.run_pipeline(PAGES, triage_results=TRIAGE, delay=0, checkpoint_path=str(ck))
    assert ck.exists(), 'no checkpoint written when the loop raised'
    assert set(json.loads(ck.read_text())['done']) == {'X 1a', 'X 2a'}


# -- (c) ------------------------------------------------------------------

HEB = 'אחד. שנים. שלשה.'


def test_4k_sleeps_between_calls(monkeypatch):
    d = _bare()
    sleeps = []
    monkeypatch.setattr('time.sleep', lambda s: sleeps.append(s))
    d._llm_clause_span_for_story = lambda *a: (d.calls.append(1) or
                                               {'start_clause': 0, 'end_clause': 2})
    pages = [{'ref': f'X {i}a', 'segments': [{'index': 0, 'hebrew': HEB}],
              'stories': [{'start_segment': 0, 'end_segment': 0, 'classification': 'YES'}]}
             for i in range(3)]
    d.extract_text_spans_via_clauses(pages, delay=0.7)
    assert len(d.calls) == 3
    assert sleeps == [0.7, 0.7, 0.7]


def test_4k_does_not_sleep_when_no_call_is_made(monkeypatch):
    d = _bare()
    sleeps = []
    monkeypatch.setattr('time.sleep', lambda s: sleeps.append(s))
    d._llm_clause_span_for_story = lambda *a: pytest.fail('no call expected')
    pages = [{'ref': 'X 1a', 'segments': [{'index': 0, 'hebrew': 'אחד'}],   # one clause
              'stories': [{'start_segment': 0, 'end_segment': 0, 'classification': 'YES'}]}]
    d.extract_text_spans_via_clauses(pages, delay=0.7)
    assert sleeps == []


def test_run_pipeline_passes_its_delay_to_4k(monkeypatch):
    d = _bare()
    seen = {}
    monkeypatch.setattr('time.sleep', lambda *_: None)
    d.detect_stories = lambda ref, *a: [{'start_segment': 0, 'end_segment': 0,
                                         'classification': 'YES'}]

    def spans(pages, delay=None):
        seen['delay'] = delay
        return {'clause_llm': 0, 'clause_kept_full': 0, 'no_clause_split': 0, 'skipped': 0}
    d.extract_text_spans_via_clauses = spans
    d.run_pipeline(PAGES, triage_results=TRIAGE, delay=2.5)
    assert seen['delay'] == 2.5
