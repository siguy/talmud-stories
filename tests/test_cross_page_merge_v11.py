"""Cross-page merge, against the detector that actually runs (v11).

`tests/test_cross_page_merge.py` pins v7's merge functions; v11's are what
`run_new_tractate.py` calls. These tests pin the two defects the 2026-11-07
pre-Eruvin review found (docs/findings/2026-11-07-pre-eruvin-code-review.md):

  Finding 1 -- 4c (`merge_cross_page_stories`) bridged a story that ends MID-PAGE to
    the next page's first story whenever either side carried a continuation flag, and
    deleted that story. Shipped case: Gittin 36a, a one-segment story at seg 2 of 14.
  Finding 2 -- with the twin pass on, stories are appended, so the story that touches
    the page break is not always list-last; 4b/4c took `stories[-1]` / `stories[0]`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.event_triage import EventType  # noqa: E402
from src.story_detector_v11 import (  # noqa: E402
    merge_cross_page_stories, merge_cross_page_stories_v7)

N, D = EventType.NARRATIVE_EVENT, EventType.DELIBERATION


def page(ref, stories, n=14):
    return {'ref': ref,
            'segments': [{'index': i, 'hebrew': 'א', 'english': 'a'} for i in range(n)],
            'stories': stories}


def story(a, b, cls='HIGH_CONFIDENCE', to_next=False, from_prev=False, summary=''):
    return {'start_segment': a, 'end_segment': b, 'classification': cls,
            'one_sentence_summary': summary,
            'continuation': {'continues_to_next_page': to_next,
                             'continues_from_previous_page': from_prev}}


# --- Finding 1 -------------------------------------------------------------------

def test_4c_does_not_merge_a_mid_page_story_gittin_36a_shape():
    """A one-segment story at seg 2 of 14; page 2's first story at seg 0 flags
    continuation. Nothing of page 1's story touches the break -> no merge."""
    p1 = page('G 36a', [story(2, 2)])
    p2 = page('G 36b', [story(0, 3, from_prev=True, summary='its own story')])
    merge_cross_page_stories([p1, p2])
    assert 'spans_pages' not in p1['stories'][0]
    assert len(p2['stories']) == 1, "page 2's first story was deleted"


def test_4c_still_merges_a_story_that_reaches_the_break():
    p1 = page('G 36a', [story(10, 13, to_next=True)])
    p2 = page('G 36b', [story(0, 3)])
    merge_cross_page_stories([p1, p2])
    merged = p1['stories'][0]
    assert merged['spans_pages'] == ['G 36a', 'G 36b']
    assert merged['cross_page_merge_legacy'] is True, 'a 4c merge must be findable'
    assert p2['stories'] == []


def test_4b_case_4_still_merges_the_flagged_seg0_case():
    """The case 4c used to be the only cover for: both real, page 2 starts at seg 0,
    one side flags continuation. 4b case 4 handles it; it must keep doing so."""
    p1 = page('G 36a', [story(10, 13)])
    p2 = page('G 36b', [story(0, 3, from_prev=True)])
    triage = {'G 36a': [D] * 13 + [N], 'G 36b': [N] + [D] * 13}
    merge_cross_page_stories_v7([p1, p2], triage)
    assert p1['stories'][0]['spans_pages'] == ['G 36a', 'G 36b']
    assert p2['stories'] == []
