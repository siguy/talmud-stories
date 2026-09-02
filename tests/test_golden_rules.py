#!/usr/bin/env python3
"""
The golden carries the rule that shaped it, and never loses an expert judgment.

The golden set is the product: as a rule is settled it should be applied, because the
whole point is a corpus under today's criteria rather than a snapshot of 2005. What it
must not do is change silently, or drop what an expert affirmed.

So R-C1 — a story inside a Mishnah belongs with the stories of the Mishnah, and the
Talmud's quotation of it is Talmudic (Jeff, 2026-09-01) — is applied by MARKING each
entry `corpus: talmud|mishnah`, never by removing one. Ketubot 14b and 77a are the cases
that matter: he marked both correct in review, and under R-C1 they stop counting as
Talmud false negatives while remaining in the file with his verdict intact.

`GOLDEN_COUNTS` in test_bookkeeping.py therefore still holds, which is the point: a rule
application that quietly changed the counts would be indistinguishable from data loss.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

GOLDENS = {'ketubot': ROOT / 'results/canonical/ketubot_canonical.json',
           'kiddushin': ROOT / 'results/canonical/kiddushin_canonical.json'}


def entries(path):
    return [s for p in json.loads(path.read_text())['pages'] for s in (p.get('stories') or [])]


@pytest.mark.parametrize('tractate', sorted(GOLDENS))
def test_every_entry_says_which_corpus_it_belongs_to(tractate):
    for s in entries(GOLDENS[tractate]):
        assert s.get('corpus') in ('talmud', 'mishnah'), s.get('one_sentence_summary')


@pytest.mark.parametrize('tractate', sorted(GOLDENS))
def test_every_entry_records_the_rule_that_marked_it(tractate):
    for s in entries(GOLDENS[tractate]):
        assert 'R-C1' in (s.get('rules') or [])


def test_the_two_ketubot_cases_he_affirmed_are_marked_not_deleted():
    """14b and 77a are the passages the Mishnah filter removes and he marked correct.
    Under R-C1 they are Mishnah stories — still here, still carrying his verdict."""
    data = json.loads(GOLDENS['ketubot'].read_text())
    found = {}
    for page in data['pages']:
        for s in page.get('stories') or []:
            if page['ref'] in ('Ketubot 14b', 'Ketubot 77a') and s.get('corpus') == 'mishnah':
                found[page['ref']] = s
    assert set(found) == {'Ketubot 14b', 'Ketubot 77a'}
    for s in found.values():
        assert s.get('classification') != 'NOT_A_STORY', 'his verdict must survive the rule'


@pytest.mark.parametrize('tractate', sorted(GOLDENS))
def test_applying_the_rule_did_not_change_how_many_entries_there_are(tractate):
    """Counts are the guard against silent loss (CLAUDE.md rule 5). A rule marks;
    only a human decision removes."""
    import importlib.util
    spec = importlib.util.spec_from_file_location('bk', ROOT / 'tests' / 'test_bookkeeping.py')
    bk = importlib.util.module_from_spec(spec); spec.loader.exec_module(bk)
    assert len(entries(GOLDENS[tractate])) == bk.GOLDEN_COUNTS[tractate]['entries']
