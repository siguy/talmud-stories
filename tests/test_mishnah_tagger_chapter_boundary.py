"""The Mishnah tagger must not read a chapter boundary as a mid-Mishnah page.

`_tag_mishnah_segments()` decides which segments are Mishnah; anything tagged
Mishnah end-to-end is moved out of `stories` by `filter_mishnah_only_stories()`,
where **no harness can see it** — neither `evaluate_golden.py` nor
`measure_recall_vs_expert_list.py` reads `mishnah_stories`.

The defect: a page may legitimately open mid-Mishnah (the Mishnah began on the
previous page), detected by גמ׳ being the page's first marker. But at a chapter
boundary Sefaria opens the new chapter's first Mishnah with the chapter incipit
in `<big><strong>` — `אף על פי` on Ketubot 54b seg 5 — *instead of* מתני׳. The
old two-marker vocabulary therefore saw גמ׳ first, concluded "mid-Mishnah page",
and back-tagged everything before it: the previous chapter's Gemara tail plus
the הדרן formula. 7 pages were affected, and it silently deleted two stories the
golden accepts — Ketubot 54b segs 1-3 (also in Jeff's blind 2005 list) and
Ketubot 95b seg 0, plain Gemara (`דההוא גברא דמישכן ליה פרדיסא`).

Fixture is real Sefaria text, verbatim (Lesson 9 — fixture != production), and
covers both directions: the boundary pages that were wrong, and a page that
genuinely does open mid-Mishnah, which must keep working.

Run directly:  python3 tests/test_mishnah_tagger_chapter_boundary.py
Or via pytest: pytest tests/test_mishnah_tagger_chapter_boundary.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.story_detector_v11 import (  # noqa: E402
    _tag_mishnah_segments,
    filter_mishnah_only_stories,
)

FIXTURE = ROOT / 'tests' / 'fixtures' / 'mishnah_tagger_chapter_boundary.json'
PAGES = json.loads(FIXTURE.read_text(encoding='utf-8'))['pages']


def tags(ref):
    return _tag_mishnah_segments(PAGES[ref])


def test_chapter_break_mid_page_does_not_backtag_the_previous_gemara():
    """Ketubot 54b: הדרן at seg 4 ends the chapter; segs 0-3 are its Gemara tail."""
    t = tags('Ketubot 54b')
    for i in range(0, 4):
        assert t[i] is False, f'seg {i} is the previous chapter\'s Gemara, not Mishnah'
    assert t[4] is False, 'the הדרן formula itself is not Mishnah'
    for i in (5, 6):
        assert t[i] is True, f'seg {i} opens the new chapter\'s Mishnah (incipit אף על פי)'
    for i in range(7, 11):
        assert t[i] is False, f'seg {i} follows גמ׳ and is Gemara'


def test_chapter_break_late_on_page_leaves_the_whole_gemara_alone():
    """Ketubot 95b: הדרן at seg 13. Everything before it is Gemara, incl. seg 0."""
    t = tags('Ketubot 95b')
    for i in range(0, 14):
        assert t[i] is False, f'seg {i} precedes the chapter break and is Gemara'
    assert t[14] is True, 'seg 14 is the new chapter\'s opening Mishnah (אלמנה ניזונת)'
    for i in (15, 16):
        assert t[i] is False, f'seg {i} follows גמ׳ (seg 15) and is Gemara'


def test_chapter_incipit_opening_a_page_is_read_as_mishnah():
    """Ketubot 2a: the chapter opens at seg 0 with the incipit, not מתני׳."""
    t = tags('Ketubot 2a')
    assert t[0] is True, 'the chapter incipit opens the first Mishnah'
    for i in range(1, 11):
        assert t[i] is False, f'seg {i} follows גמ׳ (seg 1) and is Gemara'


def test_a_page_that_really_does_open_mid_mishnah_still_works():
    """Ketubot 42a: no chapter break — the Mishnah began on 41b and closes at seg 0.

    This is the case the continuation rule exists for. Guards against fixing the
    boundary bug by simply deleting the rule.
    """
    t = tags('Ketubot 42a')
    assert t[0] is True, 'seg 0 is the tail of the Mishnah carried over from 41b'
    for i in range(1, 9):
        assert t[i] is False, f'seg {i} follows גמ׳ (seg 1) and is Gemara'


def test_the_two_golden_stories_survive_the_mishnah_filter():
    """End to end: neither story may be moved into `mishnah_stories`.

    Both are accepted stories in the golden; 54b segs 1-3 is also in Jeff's
    detector-blind 2005 list.
    """
    pages = [
        {'ref': 'Ketubot 54b', 'segments': PAGES['Ketubot 54b'],
         'stories': [{'start_segment': 1, 'end_segment': 3, 'classification': 'YES'}]},
        {'ref': 'Ketubot 95b', 'segments': PAGES['Ketubot 95b'],
         'stories': [{'start_segment': 0, 'end_segment': 0,
                      'classification': 'LOW_CONFIDENCE'}]},
    ]
    moved = filter_mishnah_only_stories(pages)
    assert moved == 0, f'{moved} Gemara stories were filtered as Mishnah'
    for page in pages:
        assert len(page['stories']) == 1, f"{page['ref']} lost its story"
        assert page['mishnah_stories'] == []


def test_a_real_mishnah_only_story_is_still_filtered():
    """The filter must keep working: a story inside the 54b opening Mishnah goes."""
    pages = [{'ref': 'Ketubot 54b', 'segments': PAGES['Ketubot 54b'],
              'stories': [{'start_segment': 5, 'end_segment': 6,
                           'classification': 'YES'}]}]
    assert filter_mishnah_only_stories(pages) == 1
    assert pages[0]['stories'] == []


if __name__ == '__main__':
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith('test_') and callable(fn):
            try:
                fn()
                print(f'  PASS  {name}')
            except AssertionError as exc:
                failures += 1
                print(f'  FAIL  {name}: {exc}')
    print(f'\n{failures} failure(s)')
    sys.exit(1 if failures else 0)
