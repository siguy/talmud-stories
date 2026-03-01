#!/usr/bin/env python3
"""
Cross-page merge regression tests.

Tests the interaction between merge stages 4b, 4c, and 4d to prevent
the bug where 4c overwrites correct 4b merges.

Root cause: 4b correctly merges a NOT_A_STORY fragment at seg 0-1 on page N+1,
but then 4c runs, sees the continuation flag still set, grabs a completely
different story further down on page N+1, and overwrites the page2 segments.

Real cases from Jeff's v8 feedback:
- 84b→85a: 4b merged NOT_A_STORY at seg 0, 4c overwrote with seg 3-4 (Avimi story)
- 69a→69b: 4c merged seg 10-12 (independent story)
- 85b→86a: 4c merged seg 4 (independent story)
- 105b→106a: 4c merged seg 3 (independent story)
- 111b→112a: 4c merged seg 3 (independent story)
"""

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ground_truth import EventType
from src.story_detector_v7 import merge_cross_page_stories_v7, merge_cross_page_stories


# ---------------------------------------------------------------------------
# Helpers to build synthetic page data
# ---------------------------------------------------------------------------

def make_page(ref, stories, num_segments=15):
    """Build a minimal page dict with segments and stories."""
    segments = [{'index': i, 'english': f'Segment {i} text', 'hebrew': f'seg {i} heb'}
                for i in range(num_segments)]
    return {
        'ref': ref,
        'segments': segments,
        'stories': copy.deepcopy(stories),
    }


def make_story(start, end, classification='YES', continues_to=False, continues_from=False,
               summary='A story'):
    """Build a minimal story dict."""
    cont = {}
    if continues_to:
        cont['continues_to_next_page'] = True
    if continues_from:
        cont['continues_from_previous_page'] = True
    return {
        'start_segment': start,
        'end_segment': end,
        'classification': classification,
        'continuation': cont,
        'one_sentence_summary': summary,
    }


def make_triage(ref, events_list):
    """Build triage dict for a page. events_list is list of EventType values."""
    return {ref: events_list}


# ---------------------------------------------------------------------------
# Test: 4c must NOT overwrite a merge already done by 4b
# Pattern: 84b→85a, 69a→69b, 85b→86a, 105b→106a, 111b→112a
# ---------------------------------------------------------------------------

class TestNoDoubleMerge:
    """After 4b merges a NOT_A_STORY fragment at seg 0, 4c must skip that story."""

    def _build_scenario(self):
        """
        Page N: story at end with continues_to_next_page.
        Page N+1: NOT_A_STORY at seg 0-1, then a real story at seg 3-4.

        4b should merge the NOT_A_STORY fragment into page N's story.
        4c should NOT then overwrite with the seg 3-4 story.
        """
        story_n = make_story(8, 14, 'YES', continues_to=True, summary='Story on page N')
        not_a_story_n1 = make_story(0, 1, 'NOT_A_STORY', continues_from=True,
                                     summary='Fragment at top')
        real_story_n1 = make_story(3, 4, 'YES', summary='Avimi story (independent)')

        page_n = make_page('Ketubot 84b', [story_n])
        page_n1 = make_page('Ketubot 85a', [not_a_story_n1, real_story_n1])

        # Triage: narrative events at boundary
        triage = {}
        triage['Ketubot 84b'] = [EventType.DELIBERATION] * 14 + [EventType.NARRATIVE_EVENT]
        triage['Ketubot 85a'] = ([EventType.NARRATIVE_EVENT] * 2 +
                                  [EventType.DELIBERATION] +
                                  [EventType.NARRATIVE_EVENT] * 2 +
                                  [EventType.DELIBERATION] * 10)
        return [page_n, page_n1], triage

    def test_4b_merges_fragment(self):
        """4b should merge the NOT_A_STORY fragment at seg 0-1."""
        pages, triage = self._build_scenario()
        pages = merge_cross_page_stories_v7(pages, triage)

        last_story = pages[0]['stories'][-1]
        assert last_story.get('spans_pages') == ['Ketubot 84b', 'Ketubot 85a']
        assert last_story.get('start_segment_page2') == 0
        assert last_story.get('end_segment_page2') == 1
        assert last_story.get('cross_page_merge_v7') is True

    def test_4c_does_not_overwrite(self):
        """After 4b merge, 4c must NOT overwrite page2 segments."""
        pages, triage = self._build_scenario()

        # Run 4b first
        pages = merge_cross_page_stories_v7(pages, triage)

        # Snapshot what 4b set
        last_story = pages[0]['stories'][-1]
        assert last_story.get('spans_pages') is not None, "4b should have merged"
        original_start_p2 = last_story['start_segment_page2']
        original_end_p2 = last_story['end_segment_page2']

        # Run 4c
        pages = merge_cross_page_stories(pages)

        # 4c must NOT have changed the page2 segments
        last_story = pages[0]['stories'][-1]
        assert last_story['start_segment_page2'] == original_start_p2, \
            f"4c overwrote start_segment_page2: {original_start_p2} → {last_story['start_segment_page2']}"
        assert last_story['end_segment_page2'] == original_end_p2, \
            f"4c overwrote end_segment_page2: {original_end_p2} → {last_story['end_segment_page2']}"

    def test_independent_story_survives(self):
        """The real story at seg 3-4 on page N+1 must still exist after both passes."""
        pages, triage = self._build_scenario()
        pages = merge_cross_page_stories_v7(pages, triage)
        pages = merge_cross_page_stories(pages)

        # The independent story at seg 3-4 should still be on page N+1
        n1_stories = pages[1]['stories']
        assert len(n1_stories) >= 1, "Independent story on page N+1 was eaten"
        found = any(s.get('start_segment') == 3 and s.get('end_segment') == 4
                    for s in n1_stories)
        assert found, f"Avimi story (seg 3-4) missing from page N+1. Stories: {n1_stories}"


# ---------------------------------------------------------------------------
# Test: 4c must block gap merges (first story on N+1 starts at seg >= 1)
# Pattern: 69a→69b (seg 10), 84b→85a (seg 3), 105b→106a (seg 3)
# ---------------------------------------------------------------------------

class TestGapMergeBlocking:
    """4c should not merge when the first story on N+1 starts far from seg 0."""

    def test_blocks_high_segment_merge(self):
        """When first story on N+1 starts at seg 10, 4c must not merge."""
        story_n = make_story(8, 14, 'YES', continues_to=True)
        story_n1 = make_story(10, 12, 'YES', continues_from=True)

        pages = [
            make_page('Ketubot 69a', [story_n]),
            make_page('Ketubot 69b', [story_n1]),
        ]

        pages = merge_cross_page_stories(pages)

        last_story = pages[0]['stories'][-1]
        assert last_story.get('spans_pages') is None, \
            "4c should not merge when N+1's first story starts at seg 10"

        # Story on N+1 must survive
        assert len(pages[1]['stories']) == 1

    def test_blocks_seg3_merge(self):
        """When first story on N+1 starts at seg 3, 4c must not merge."""
        story_n = make_story(10, 14, 'HIGH_CONFIDENCE', continues_to=True)
        story_n1 = make_story(3, 5, 'YES')

        pages = [
            make_page('Ketubot 105b', [story_n]),
            make_page('Ketubot 106a', [story_n1]),
        ]

        pages = merge_cross_page_stories(pages)

        last_story = pages[0]['stories'][-1]
        assert last_story.get('spans_pages') is None, \
            "4c should not merge when N+1's first story starts at seg 3"

    def test_blocks_seg4_merge(self):
        """When first story on N+1 starts at seg 4, 4c must not merge."""
        story_n = make_story(5, 14, 'YES', continues_to=True)
        story_n1 = make_story(4, 6, 'YES')

        pages = [
            make_page('Ketubot 85b', [story_n]),
            make_page('Ketubot 86a', [story_n1]),
        ]

        pages = merge_cross_page_stories(pages)

        last_story = pages[0]['stories'][-1]
        assert last_story.get('spans_pages') is None, \
            "4c should not merge when N+1's first story starts at seg 4"

    def test_allows_seg0_merge(self):
        """When first story on N+1 starts at seg 0 with continuation, 4c CAN merge."""
        story_n = make_story(8, 14, 'YES', continues_to=True)
        story_n1 = make_story(0, 2, 'HIGH_CONFIDENCE', continues_from=True)

        pages = [
            make_page('Ketubot 78b', [story_n]),
            make_page('Ketubot 79a', [story_n1]),
        ]

        pages = merge_cross_page_stories(pages)

        last_story = pages[0]['stories'][-1]
        assert last_story.get('spans_pages') == ['Ketubot 78b', 'Ketubot 79a'], \
            "4c should merge when N+1's first story starts at seg 0"


# ---------------------------------------------------------------------------
# Test: Correct merges are preserved
# Pattern: 78b→79a (seg 0), 94b→95a (seg 0), 103a→103b (seg 0)
# ---------------------------------------------------------------------------

class TestCorrectMergesPreserved:
    """Merges that were correct in v8 must still work."""

    def test_v7_merge_at_seg0(self):
        """4b Case 4: two real stories at boundary, seg 0, with continuation."""
        story_n = make_story(10, 14, 'YES', continues_to=True)
        story_n1 = make_story(0, 2, 'HIGH_CONFIDENCE', continues_from=True)

        pages = [
            make_page('Ketubot 78b', [story_n]),
            make_page('Ketubot 79a', [story_n1]),
        ]

        triage = {
            'Ketubot 78b': [EventType.DELIBERATION] * 14 + [EventType.NARRATIVE_EVENT],
            'Ketubot 79a': [EventType.NARRATIVE_EVENT] * 3 + [EventType.DELIBERATION] * 12,
        }

        pages = merge_cross_page_stories_v7(pages, triage)

        last_story = pages[0]['stories'][-1]
        assert last_story.get('spans_pages') == ['Ketubot 78b', 'Ketubot 79a']
        assert last_story.get('start_segment_page2') == 0
        assert last_story.get('cross_page_merge_v7') is True

    def test_not_a_story_at_seg0_merges(self):
        """4b Case 2: real story on N, NOT_A_STORY fragment at seg 0 on N+1."""
        story_n = make_story(10, 14, 'YES', continues_to=True)
        fragment_n1 = make_story(0, 0, 'NOT_A_STORY', continues_from=True)
        other_story_n1 = make_story(3, 5, 'YES', summary='Different story')

        pages = [
            make_page('Ketubot 103a', [story_n]),
            make_page('Ketubot 103b', [fragment_n1, other_story_n1]),
        ]

        triage = {
            'Ketubot 103a': [EventType.DELIBERATION] * 14 + [EventType.NARRATIVE_EVENT],
            'Ketubot 103b': ([EventType.NARRATIVE_EVENT] +
                             [EventType.DELIBERATION] * 2 +
                             [EventType.NARRATIVE_EVENT] * 3 +
                             [EventType.DELIBERATION] * 9),
        }

        pages = merge_cross_page_stories_v7(pages, triage)

        last_story = pages[0]['stories'][-1]
        assert last_story.get('spans_pages') is not None
        assert last_story.get('start_segment_page2') == 0
        assert last_story.get('end_segment_page2') == 0

        # Other story must survive
        assert len(pages[1]['stories']) == 1
        assert pages[1]['stories'][0]['start_segment'] == 3


# ---------------------------------------------------------------------------
# Test: 4b Case 4 tightened to seg == 0 only (Fix C)
# Pattern: 61a→61b where seg 1 story is actually different
# ---------------------------------------------------------------------------

class TestCase4GuardTightened:
    """4b Case 4 should only merge when first_story_n1 starts at seg 0, not seg 1."""

    def test_blocks_seg1_merge(self):
        """When first story on N+1 starts at seg 1, 4b Case 4 should NOT merge."""
        story_n = make_story(10, 14, 'YES', continues_to=True)
        story_n1 = make_story(1, 3, 'YES', continues_from=True)

        pages = [
            make_page('Ketubot 61a', [story_n]),
            make_page('Ketubot 61b', [story_n1]),
        ]

        triage = {
            'Ketubot 61a': [EventType.DELIBERATION] * 14 + [EventType.NARRATIVE_EVENT],
            'Ketubot 61b': ([EventType.DELIBERATION] +
                            [EventType.NARRATIVE_EVENT] * 3 +
                            [EventType.DELIBERATION] * 11),
        }

        pages = merge_cross_page_stories_v7(pages, triage)

        last_story = pages[0]['stories'][-1]
        # Should NOT have merged via Case 4 (seg 1 is a different story)
        assert last_story.get('cross_page_merge_v7') is not True, \
            "4b Case 4 should not merge when N+1's first story starts at seg 1"

    def test_allows_seg0_merge(self):
        """When first story on N+1 starts at seg 0, 4b Case 4 should merge."""
        story_n = make_story(10, 14, 'YES', continues_to=True)
        story_n1 = make_story(0, 2, 'YES', continues_from=True)

        pages = [
            make_page('Ketubot 78b', [story_n]),
            make_page('Ketubot 79a', [story_n1]),
        ]

        triage = {
            'Ketubot 78b': [EventType.DELIBERATION] * 14 + [EventType.NARRATIVE_EVENT],
            'Ketubot 79a': [EventType.NARRATIVE_EVENT] * 3 + [EventType.DELIBERATION] * 12,
        }

        pages = merge_cross_page_stories_v7(pages, triage)

        last_story = pages[0]['stories'][-1]
        assert last_story.get('cross_page_merge_v7') is True, \
            "4b Case 4 should merge when N+1's first story starts at seg 0"
        assert last_story.get('start_segment_page2') == 0


# ---------------------------------------------------------------------------
# Test: Blocked stories are eligible for stitch (4d)
# After 4c blocks a merge, the story should still have continues_to_next_page
# and NOT have spans_pages, so 4d can handle it.
# ---------------------------------------------------------------------------

class TestBlockedStoriesEligibleForStitch:
    """Stories blocked by 4c guards should remain candidates for 4d stitch."""

    def test_blocked_story_has_no_spans_pages(self):
        """Story blocked by 4c should NOT have spans_pages set."""
        story_n = make_story(8, 14, 'YES', continues_to=True)
        story_n1 = make_story(3, 5, 'YES')  # starts at seg 3 → blocked

        pages = [
            make_page('Ketubot 111b', [story_n]),
            make_page('Ketubot 112a', [story_n1]),
        ]

        pages = merge_cross_page_stories(pages)

        last_story = pages[0]['stories'][-1]
        assert last_story.get('spans_pages') is None, \
            "Blocked story should not have spans_pages"

    def test_blocked_story_keeps_continuation_flag(self):
        """Story blocked by 4c should still have continues_to_next_page."""
        story_n = make_story(8, 14, 'YES', continues_to=True)
        story_n1 = make_story(3, 5, 'YES')

        pages = [
            make_page('Ketubot 111b', [story_n]),
            make_page('Ketubot 112a', [story_n1]),
        ]

        pages = merge_cross_page_stories(pages)

        last_story = pages[0]['stories'][-1]
        assert last_story.get('continuation', {}).get('continues_to_next_page') is True, \
            "Blocked story should keep its continuation flag for 4d stitch"


# ---------------------------------------------------------------------------
# Test: Independent stories on N+1 survive both merge passes
# Pattern: 85a seg 3-4 (Avimi), 69b seg 10-12, 106a seg 3
# ---------------------------------------------------------------------------

class TestIndependentStoriesSurvive:
    """Stories that Jeff confirmed are independent must not be eaten by merges."""

    def test_multiple_stories_on_n1_survive(self):
        """
        Page N has a continuing story. Page N+1 has:
        - NOT_A_STORY fragment at seg 0 (merged by 4b)
        - Independent story at seg 3-4 (must survive)
        - Another story at seg 8-10 (must survive)

        Both independent stories must survive both merge passes.
        """
        story_n = make_story(8, 14, 'YES', continues_to=True)
        fragment = make_story(0, 1, 'NOT_A_STORY', continues_from=True)
        independent1 = make_story(3, 4, 'YES', summary='Avimi story')
        independent2 = make_story(8, 10, 'HIGH_CONFIDENCE', summary='Another story')

        pages = [
            make_page('Ketubot 84b', [story_n]),
            make_page('Ketubot 85a', [fragment, independent1, independent2]),
        ]

        triage = {
            'Ketubot 84b': [EventType.DELIBERATION] * 14 + [EventType.NARRATIVE_EVENT],
            'Ketubot 85a': ([EventType.NARRATIVE_EVENT] * 2 +
                            [EventType.DELIBERATION] +
                            [EventType.NARRATIVE_EVENT] * 2 +
                            [EventType.DELIBERATION] * 3 +
                            [EventType.NARRATIVE_EVENT] * 3 +
                            [EventType.DELIBERATION] * 4),
        }

        # Run both merge passes
        pages = merge_cross_page_stories_v7(pages, triage)
        pages = merge_cross_page_stories(pages)

        n1_stories = pages[1]['stories']
        start_segs = [s['start_segment'] for s in n1_stories]

        assert 3 in start_segs, \
            f"Independent story at seg 3 eaten. Remaining: {start_segs}"
        assert 8 in start_segs, \
            f"Independent story at seg 8 eaten. Remaining: {start_segs}"

    def test_solo_story_on_n1_not_merged_with_gap(self):
        """
        Page N continues, but page N+1 only has a story at seg 10.
        4c should not merge it (gap too large).
        """
        story_n = make_story(12, 14, 'YES', continues_to=True)
        story_n1 = make_story(10, 12, 'YES')

        pages = [
            make_page('Ketubot 69a', [story_n]),
            make_page('Ketubot 69b', [story_n1]),
        ]

        pages = merge_cross_page_stories(pages)

        assert len(pages[1]['stories']) == 1, "Solo story at seg 10 should survive"
        assert pages[0]['stories'][-1].get('spans_pages') is None
