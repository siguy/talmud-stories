"""4k must not cut the end of a story that continues onto the next page.

2026-11-07 review, finding 11: extract_text_spans_via_clauses asked where the story
ends inside page 1's last segment while the story runs on into page 2 (`spans_pages`).
Measured on 10 shipped cases, e.g. Gittin 72a: end clause 5 of 7, then 72b 0-6. The
start side is still a real question, so only the end side is skipped.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.story_detector_v11 import V7StoryDetector  # noqa: E402

# Three clauses per segment, so the model has something to choose between.
HEB = 'אחד. שנים. שלשה.'


def _detector(answer):
    d = V7StoryDetector.__new__(V7StoryDetector)
    d.client = object()
    d.calls = 0

    def fake(story, start_clauses, end_clauses):
        d.calls += 1
        return answer
    d._llm_clause_span_for_story = fake
    return d


def _page(story):
    return {'ref': 'Gittin 72a',
            'segments': [{'index': i, 'hebrew': HEB} for i in range(3)],
            'stories': [story]}


def test_cross_page_story_gets_no_end_span_but_keeps_start():
    story = {'start_segment': 1, 'end_segment': 2, 'classification': 'YES',
             'spans_pages': ['Gittin 72a', 'Gittin 72b'],
             'start_segment_page2': 0, 'end_segment_page2': 6}
    d = _detector({'start_clause': 1, 'end_clause': 0})
    d.extract_text_spans_via_clauses([_page(story)])

    assert 'text_span_end' not in story
    assert story['text_span_start']['clause_index'] == 1
    assert story['text_span_source'] == 'clause_llm'
    assert story['text_span_end_skipped'] == 'spans_pages'


def test_cross_page_story_with_end_only_trim_is_kept_full():
    story = {'start_segment': 1, 'end_segment': 2, 'classification': 'YES',
             'spans_pages': ['Gittin 72a', 'Gittin 72b']}
    d = _detector({'start_clause': 0, 'end_clause': 0})
    d.extract_text_spans_via_clauses([_page(story)])

    assert 'text_span_end' not in story and 'text_span_start' not in story
    assert story['text_span_source'] == 'clause_kept_full'


def test_single_page_story_still_gets_end_span():
    story = {'start_segment': 1, 'end_segment': 2, 'classification': 'YES'}
    d = _detector({'start_clause': 0, 'end_clause': 1})
    d.extract_text_spans_via_clauses([_page(story)])

    assert story['text_span_end']['clause_index'] == 1
    assert 'text_span_end_skipped' not in story
