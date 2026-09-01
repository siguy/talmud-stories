"""
Per-daf attribution in the line-based expert-list parser.

Two defects, both silent, both fixed 2026-09-01:

1. **Two-amud headers.** `parse_expert_doc` matched only single-amud headers
   (`סה ע"ב`), so a story Jeff headed with a span (`סה ע"ב-סו ע"א`) never reset the
   current daf and inherited the PRECEDING header — 16 stories in Gittin, 8 in Yevamot,
   3 in Eruvin, and 15 such headers in Ketubot. The header is now read, and the story is
   anchored to the daf its own text starts on, which is an objective fact about where the
   passage sits in the Talmud rather than a judgement about what counts as a story — so
   the list stays as blind as it was.

2. **Reversed columns.** `textutil` flattens a table in stream order, so the parser only
   aligns a story with its own location cell while the location column comes first. In
   `eruvin.doc` it comes last, and every story took the PREVIOUS row's daf: only 20 of 73
   entries touched the daf their header named. That parse still returns the right *number*
   of stories, so nothing downstream looks wrong (Lesson 38). It now raises.

The counts are the guard that matters: a fix here must not change what the parser thinks
a story IS. Ketubot must still parse to 149 — the count the whole recall pipeline rests on.

→ work/done/2026-08-30-two-amud-header-parser.md
"""

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.measure_recall_vs_expert_list import (  # noqa: E402
    DAF_HEADER, SPAN_HEADER, anchor_span_refs, gram_index, grams, locate,
    parse_expert_doc, require_location_column_first, span_refs, text_units)

DOCS = {
    'Ketubot': ROOT / 'jeff comms' / 'b.ketubot (1).doc',
    'Gittin': ROOT / 'jeff comms' / '8-30-2026' / 'b.gittin.doc',
    'Yevamot': ROOT / 'jeff comms' / '8-30-2026' / 'b. yebamot.doc',
    'Eruvin': ROOT / 'jeff comms' / '8-30-2026' / 'eruvin.doc',
}
SEFARIA = ROOT / 'results' / 'sefaria'

# Established counts. These are the regression guard: the attribution fix must move refs
# and nothing else, so a count change means it altered what counts as a story.
ENTRIES = {'Ketubot': 149, 'Gittin': 112, 'Yevamot': 102}


def needs(path):
    return pytest.mark.skipif(not path.exists(), reason=f'{path.name} not present')


# --------------------------------------------------------------- header patterns


def test_span_header_matches_the_forms_the_documents_actually_use():
    assert SPAN_HEADER.match('סה ע"ב-סו ע"א')          # two dapim
    assert SPAN_HEADER.match('יד ע"א-ע"ב')             # second daf elided
    assert SPAN_HEADER.match('נה ע"ב- נו ע"א')         # space after the dash
    assert SPAN_HEADER.match('יד ע"ד-טו ע"א')          # Yerushalmi amud dalet


def test_span_header_does_not_swallow_a_parallel_in_another_tractate():
    """A parallel is prefixed with its tractate name, so requiring a numeral at ^ excludes it."""
    assert not SPAN_HEADER.match('ב"מ יח ע"ב-יט ע"א')


def test_plain_and_span_headers_do_not_both_match_one_line():
    for line in ('סה ע"ב-סו ע"א', 'יד ע"א-ע"ב'):
        assert not DAF_HEADER.match(line), 'a span would be read as a single daf'


def test_span_refs_names_both_dapim_in_document_order():
    assert span_refs(SPAN_HEADER.match('סה ע"ב-סו ע"א'), 'Gittin') == ['Gittin 65b', 'Gittin 66a']
    assert span_refs(SPAN_HEADER.match('יד ע"א-ע"ב'), 'Gittin') == ['Gittin 14a', 'Gittin 14b']


def test_yerushalmi_amud_maps_onto_the_dafs_second_half():
    """Amud gimel/dalet is a four-column Yerushalmi form with no Bavli equivalent. It is
    resolved by anchoring, so this only has to be a sane provisional label, not a ruling."""
    assert span_refs(SPAN_HEADER.match('יד ע"ד-טו ע"א'), 'Gittin') == ['Gittin 14b', 'Gittin 15a']


# ------------------------------------------------------------- the reversed-column guard


def test_reversed_columns_raise_rather_than_mis_attributing():
    lines = ['מסכת עירובין', 'הערות', 'מקבילות', 'טקסט', 'מיקום']
    with pytest.raises(ValueError, match='PREVIOUS'):
        require_location_column_first(lines, Path('eruvin.doc'))


def test_location_column_first_is_accepted():
    require_location_column_first(['מסכת גיטין', 'מיקום', 'טקסט', 'מקבילות', 'הערות'],
                                  Path('b.gittin.doc'))


def test_a_document_with_no_column_header_row_is_not_refused():
    """The guard fires on evidence of the wrong order, never on the absence of evidence."""
    require_location_column_first(['מסכת כתובות', 'ה ע"ב'], Path('x.doc'))


@needs(DOCS['Eruvin'])
def test_eruvin_is_refused_by_name():
    with pytest.raises(ValueError, match='parse_kiddushin_list'):
        parse_expert_doc(DOCS['Eruvin'], 'Eruvin')


# --------------------------------------------------------------------- the real documents


@pytest.mark.parametrize('tractate,expected', sorted(ENTRIES.items()))
def test_entry_counts_do_not_move(tractate, expected):
    if not DOCS[tractate].exists():
        pytest.skip(f'{DOCS[tractate].name} not present')
    assert len(parse_expert_doc(DOCS[tractate], tractate)) == expected


@pytest.mark.parametrize('tractate', ['Gittin', 'Yevamot'])
def test_every_span_header_story_is_anchored_inside_its_own_header(tractate):
    """The defect, measured end to end: 0 stories may be credited to a daf outside the
    span their header names, and none may fail to anchor."""
    doc, cache = DOCS[tractate], SEFARIA / f'{tractate.lower()}.json'
    if not doc.exists() or not cache.exists():
        pytest.skip('source document or Sefaria cache not present')
    import json
    stories = parse_expert_doc(doc, tractate)
    under_span = [s for s in stories if s['ref_source'] == 'span_header']
    assert under_span, 'this tractate is here because it has two-amud headers'
    units = text_units(json.loads(cache.read_text())['pages'])
    anchored, unresolved, outside = anchor_span_refs(stories, units, gram_index(units))
    assert not unresolved and not outside
    assert len(anchored) == len(under_span)
    assert all(s['ref'] in s['ref_candidates'] for s in anchored)


@pytest.mark.parametrize('tractate', ['Gittin', 'Yevamot'])
def test_the_header_daf_is_in_the_located_window_for_almost_every_story(tractate):
    """After the fix the parsed ref should agree with where the text actually sits. Two
    Gittin entries and one Yevamot entry still disagree by several dapim — Jeff's own
    labels, pointing at a parallel rather than the passage — so this asserts a rate, and
    names the ceiling rather than hiding it."""
    doc, cache = DOCS[tractate], SEFARIA / f'{tractate.lower()}.json'
    if not doc.exists() or not cache.exists():
        pytest.skip('source document or Sefaria cache not present')
    import json
    stories = parse_expert_doc(doc, tractate)
    units = text_units(json.loads(cache.read_text())['pages'])
    index = gram_index(units)
    anchor_span_refs(stories, units, index)
    agree = 0
    for story in stories:
        cov, start, end = locate(grams(story['text']), units, index)
        if start is not None and story['ref'] in {units[i][0] for i in range(start, end + 1)}:
            agree += 1
    assert agree >= len(stories) - 5, f'{tractate}: {len(stories) - agree} refs disagree with the text'


@needs(DOCS['Ketubot'])
def test_ketubot_stories_still_carry_the_fields_the_pipeline_reads():
    story = parse_expert_doc(DOCS['Ketubot'], 'Ketubot')[0]
    assert {'ref', 'text', 'words'} <= set(story)
    assert story['ref'].startswith('Ketubot ')
    assert story['ref_source'] in {'daf_header', 'span_header'}
