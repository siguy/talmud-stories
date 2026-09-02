#!/usr/bin/env python3
"""
The story starts at the formula that introduces it — Jeff, 2026-09-01.

    "These opening formulae are not technically part of the stories. But they are
     important, as, for example, תניא indicates the Talmud thinks the story is
     Tannaitic... If not too much trouble, we should include them."

WHY THIS RULE IS ALLOWED TO BE DETERMINISTIC. Lesson 15 forbids a post-processor that
decides a text-internal boundary from surface markers, because `אלא` and a rabbi's
name are structure sometimes and story other times. The difference here is provenance:
the expert stated this rule in words, so it is principled rather than fitted to our own
past errors (Lesson 37). It stays one clause wide and only reaches backwards.

WHY IT WAS REJECTED THE DAY BEFORE AND IS NOW SHIPPED. Measured against the 2005
targets as written it scores +10 / -11 — a wash. Every one of those 11 losses is a
target where his own start excludes a formula, which is the population he called
"sloppy and preliminary". Scored against the rule he stated, the same change is
+4 to +5 points on all three measured tractates.

No API key, no network, no model.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.story_detector_v11 import (                              # noqa: E402
    _is_opening_formula,
    extend_start_over_opening_formula,
)

FORMULA = 'אָמַר רַב יְהוּדָה אָמַר רַב:'
STORY = ' מַעֲשֶׂה בְּאִשָּׁה אַחַת שֶׁבָּאתָה לִפְנֵי רַבִּי.'
NARRATIVE = 'הָהוּא גַּבְרָא דַּאֲמַר לְהוּ.'


def page(hebrew, clause_index):
    return {'ref': 'Gittin 58a',
            'segments': [{'index': 0, 'hebrew': hebrew}],
            'stories': [{'start_segment': 0, 'end_segment': 0,
                         'classification': 'HIGH_CONFIDENCE',
                         'text_span_start': {'segment': 0, 'clause_index': clause_index,
                                             'char_offset': 0}}]}


# ------------------------------------------------------------ what counts as one

def test_the_two_formulae_he_named_by_hand():
    assert _is_opening_formula('תַּנְיָא:')
    assert _is_opening_formula(FORMULA)


def test_a_verb_final_attribution_counts_too():
    """`רב חנין משתעי:` puts the verb last, so a prefix test alone misses the whole
    "X related:" family — 2 of the 10 corrected starts are this shape."""
    assert _is_opening_formula('רַב חָנִין מִישְׁתַּעֵי:')


def test_a_long_clause_is_the_story_not_its_frame():
    """`אמר רב יהודה אמר רב: מעשה ב...` is the story itself. Reaching a boundary over
    that would swallow narrative, which is the failure mode Lesson 15 records."""
    assert not _is_opening_formula(FORMULA + STORY)


def test_a_story_opener_is_not_a_formula():
    assert not _is_opening_formula(NARRATIVE)


# ------------------------------------------------------------ what it moves

def test_a_start_after_a_formula_is_extended_back_over_it():
    p = page(FORMULA + STORY, 1)
    counts = extend_start_over_opening_formula([p])
    span = p['stories'][0]['text_span_start']
    assert counts['extended'] == 1
    assert span['clause_index'] == 0
    assert span['char_offset'] == 0
    assert span['opening_formula'].startswith('אמר רב')


def test_it_moves_exactly_one_clause_and_only_backwards():
    """Two formulae in front of the story: the rule takes the nearer one and stops.
    Reaching further is how a boundary rule turns into a sweep."""
    p = page('תַּנְיָא: ' + FORMULA + STORY, 2)
    extend_start_over_opening_formula([p])
    assert p['stories'][0]['text_span_start']['clause_index'] == 1


def test_a_start_already_at_the_formula_is_left_alone():
    p = page(FORMULA + STORY, 0)
    counts = extend_start_over_opening_formula([p])
    assert counts['extended'] == 0 and counts['already_at_formula'] == 1
    assert p['stories'][0]['text_span_start']['clause_index'] == 0


def test_a_start_after_ordinary_narrative_is_left_alone():
    p = page(NARRATIVE + ' ' + 'וַאֲזַל לְבֵיהּ.', 1)
    counts = extend_start_over_opening_formula([p])
    assert counts['extended'] == 0 and counts['no_formula'] == 1
    assert p['stories'][0]['text_span_start']['clause_index'] == 1


def test_a_rejected_proposal_is_not_touched():
    p = page(FORMULA + STORY, 1)
    p['stories'][0]['classification'] = 'NOT_A_STORY'
    assert extend_start_over_opening_formula([p])['extended'] == 0


def test_a_story_with_no_span_is_counted_not_skipped_silently():
    p = page(FORMULA + STORY, 1)
    del p['stories'][0]['text_span_start']
    counts = extend_start_over_opening_formula([p])
    assert counts['extended'] == 0 and counts['no_formula'] == 1
