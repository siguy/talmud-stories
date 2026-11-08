"""4i must not trim page 1's last segment off a story that continues onto page 2.

2026-11-07 review, finding 12. Measured: Yevamot 87a in
results/v11/series_rule_experiment/yevamot_B.json -- a story 13-15 continuing to 87b
seg 0 had seg 15 trimmed (it opens `ואיצטריך`, which prefix-matches the `ואי`
marker), leaving a hole between 87a:14 and 87b:0. The Hebrew below is that page's.
"""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.story_detector_v11 import (  # noqa: E402
    snap_start_to_introducer, trim_trailing_stam_segments)

SEG13 = 'מָקוֹם שֶׁעָשָׂה וָלָד מִן הָרִאשׁוֹן כְּוָלָד מִן הַשֵּׁנִי'
SEG14 = 'לָא, מָה לִי עָשָׂה עוּבָּר כְּיָלוּד לְעִנְיַן יִיבּוּם'
SEG15 = 'וְאִיצְטְרִיךְ לְמִכְתַּב מְעוּבֶּרֶת'


def _page(story):
    segs = [{'index': i, 'hebrew': 'טקסט'} for i in range(13)]
    segs += [{'index': 13, 'hebrew': SEG13}, {'index': 14, 'hebrew': SEG14},
             {'index': 15, 'hebrew': SEG15}]
    return {'ref': 'Yevamot 87a', 'segments': segs, 'stories': [story]}


def _story(**extra):
    return {'start_segment': 13, 'end_segment': 15, 'classification': 'YES', **extra}


def test_cross_page_story_is_not_trimmed():
    story = _story(spans_pages=['Yevamot 87a', 'Yevamot 87b'],
                   start_segment_page2=0, end_segment_page2=0)
    assert trim_trailing_stam_segments([_page(story)]) == 0
    assert story['end_segment'] == 15
    assert 'end_segment_pre_trim' not in story


def test_single_page_story_is_still_trimmed():
    # The same shape without spans_pages: the trim still fires, so the guard is the
    # only thing that changed.
    story = _story()
    assert trim_trailing_stam_segments([_page(story)]) == 1
    assert story['end_segment'] == 14


def test_4h_never_moves_the_page2_side():
    # 4h only moves page-1 starts; the page-2 fields come through untouched.
    story = _story(spans_pages=['Yevamot 87a', 'Yevamot 87b'],
                   start_segment_page2=0, end_segment_page2=0)
    before = copy.deepcopy(story)
    snap_start_to_introducer([_page(story)])
    assert ({k: story.get(k) for k in ('start_segment_page2', 'end_segment_page2')}
            == {k: before[k] for k in ('start_segment_page2', 'end_segment_page2')})
