"""
The Gittin, Yevamot and Eruvin ground-truth lists, and the parser that reads all five.

These three lists are the only PRISTINE ground truth the project has: no detector has been
run on those tractates, so nothing of ours can have been merged into them (Lesson 29). What
they were missing was a parse — `--expert-json` is the only input the recall and boundary
harnesses accept for a list that is not the Ketubot `.doc` (Lesson 28).

The parser reads the .doc's real table, so the column ORDER is a property of each document
rather than a constant. `eruvin.doc` stores its columns right-to-left; assuming the usual
order there pairs every story with a neighbouring row's location cell, and it also drops
the first story entirely, because in the flattened stream that story precedes any location
cell at all. That is why Eruvin holds **74** stories and not the 73 previously recorded.

The guard that matters is that generalising the parser did not change what it thinks a
story IS: Ketubot must still parse to 149 and Kiddushin to 95, with its recall denominator
still 90.

→ docs/findings/2026-09-01-new-tractate-expert-lists.md
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.parse_kiddushin_list import (LISTS, column_map, parse,  # noqa: E402
                                          read_doc, table_rows)
from scripts.measure_recall_vs_expert_list import text_units  # noqa: E402

# Established counts. Ketubot's 149 and Kiddushin's 95 are the regression guard; the other
# three are what this work measured. Eruvin was recorded as 73 until the reversed columns
# were read — the missing entry is its very first story.
STORIES = {'Ketubot': 149, 'Kiddushin': 95, 'Gittin': 112, 'Yevamot': 102, 'Eruvin': 74}
NEW_LISTS = ['Gittin', 'Yevamot', 'Eruvin']
# Jeff's own labels that disagree with where the text sits — reported, never corrected,
# because an unambiguous label is his statement and not ours to move.
MAX_REF_DISAGREEMENTS = {'Gittin': 1, 'Yevamot': 3, 'Eruvin': 1}


def doc_for(tractate):
    path = ROOT / LISTS[tractate]['doc']
    if not path.exists():
        pytest.skip(f'{path.name} not present')
    return path


def units_for(tractate):
    caches = [ROOT / c for c in LISTS[tractate].get('sefaria', [])]
    if not caches or not all(c.is_file() for c in caches):
        pytest.skip(f'{tractate} page cache not present')
    return text_units([p for c in caches for p in json.loads(c.read_text())['pages']])


# ------------------------------------------------------------------ column order


@pytest.mark.parametrize('tractate', sorted(STORIES))
def test_column_order_is_read_from_the_document_not_assumed(tractate):
    rows = table_rows(read_doc(doc_for(tractate))[0])
    cols, header_row = column_map(rows)
    assert header_row is not None, 'every list has a column header row'
    assert set(cols) == {'location', 'text', 'parallels', 'notes'}


def test_eruvin_stores_its_columns_right_to_left():
    """The whole reason column order is detected. Reading it as the usual order pairs each
    story with a neighbouring row's location cell — a parse that looks entirely healthy."""
    cols, _ = column_map(table_rows(read_doc(doc_for('Eruvin'))[0]))
    assert cols['location'] > cols['text']


@pytest.mark.parametrize('tractate', ['Ketubot', 'Kiddushin', 'Gittin', 'Yevamot'])
def test_the_other_four_store_location_first(tractate):
    cols, _ = column_map(table_rows(read_doc(doc_for(tractate))[0]))
    assert cols['location'] < cols['text']


# ----------------------------------------------------------------------- counts


@pytest.mark.parametrize('tractate,expected', sorted(STORIES.items()))
def test_story_counts(tractate, expected):
    stories, _ = parse(doc_for(tractate), tractate)
    assert len(stories) == expected


def test_eruvins_first_story_is_not_lost():
    """It precedes any location cell in the flattened stream, so the line-based parser
    dropped it silently — the 73rd entry that was never there."""
    stories, _ = parse(doc_for('Eruvin'), 'Eruvin')
    first = stories[0]
    assert first['text'].startswith('מעשה באדם אחד מבקעת בית חורתן')
    assert first['ref'] == 'Eruvin 11a'


def test_kiddushins_recall_denominator_is_unchanged_by_the_generalisation():
    stories, comments = parse(doc_for('Kiddushin'), 'Kiddushin',
                              ROOT / LISTS['Kiddushin']['missed'])
    assert len(comments) == 10
    assert len([s for s in stories if s['blind'] and not s['duplicate_of']]) == 89
    assert len([s for s in stories
                if s['counts_for_recall'] and not s['duplicate_of']]) == 90


# ------------------------------------------------------------------- blindness


@pytest.mark.parametrize('tractate', NEW_LISTS)
def test_the_new_lists_are_wholly_blind(tractate):
    """No detector has been run on these tractates, so no entry can be ours. This asserts
    the property rather than the filename (FRAMEWORK §3): every entry blind, every entry in
    the recall denominator, no appendix, and no review remarks from Jeff."""
    stories, comments = parse(doc_for(tractate), tractate)
    assert all(s['blind'] for s in stories)
    assert all(s['counts_for_recall'] for s in stories)
    assert not any(s['in_appendix'] for s in stories)
    assert comments == []


# ------------------------------------------------------- references vs the text


@pytest.mark.parametrize('tractate', NEW_LISTS)
def test_references_agree_with_where_the_text_actually_sits(tractate):
    stories, _ = parse(doc_for(tractate), tractate, None, units_for(tractate))
    disagree = [s for s in stories if s['ref_in_text_window'] is False]
    unlocated = [s for s in stories if s['ref_in_text_window'] is None]
    assert not unlocated, f'{tractate}: {len(unlocated)} entries not found in the text'
    assert len(disagree) <= MAX_REF_DISAGREEMENTS[tractate], (
        f'{tractate}: {len(disagree)} references disagree with their own text')


@pytest.mark.parametrize('tractate', NEW_LISTS)
def test_an_ambiguous_row_is_resolved_by_the_text_and_says_so(tractate):
    """A multi-label row cannot be resolved from the document alone. Anchoring reads the
    daf off Sefaria, which is a fact about the Talmud rather than a judgement about what
    counts as a story, so the list stays blind — and every such entry is marked."""
    stories, _ = parse(doc_for(tractate), tractate, None, units_for(tractate))
    for story in stories:
        if story['ref_source'] == 'text_anchored':
            assert story['ref_ambiguous']
            assert story['ref_coverage'] >= 0.6
        elif story['ref_ambiguous']:
            assert story['ref_source'] in {'row_label', 'row_label_inherited'}


def test_an_unambiguous_label_is_never_moved():
    """Jeff's single-label reference is his statement about where a passage belongs. A
    disagreement with the text is reported to him, not silently resolved by us."""
    stories, _ = parse(doc_for('Yevamot'), 'Yevamot', None, units_for('Yevamot'))
    for story in stories:
        if not story['ref_ambiguous']:
            assert story['ref_source'] != 'text_anchored'
            assert 'ref_before_anchoring' not in story


# --------------------------------------------------------- the committed output


@pytest.mark.parametrize('tractate', NEW_LISTS)
def test_the_committed_json_matches_a_fresh_parse(tractate):
    out = ROOT / 'results' / 'expert_lists' / f'{tractate.lower()}_2005.json'
    if not out.exists():
        pytest.skip(f'{out.name} not generated')
    data = json.loads(out.read_text())
    stories, _ = parse(doc_for(tractate), tractate, None, units_for(tractate))
    assert data['counts']['stories'] == len(stories) == STORIES[tractate]
    assert data['counts']['recall_denominator'] == STORIES[tractate]
    assert [s['ref'] for s in data['stories']] == [s['ref'] for s in stories]
