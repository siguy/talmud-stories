"""The Phase B mapping gate: every banked verdict maps to exactly one axis shape.

`work/2026-08-30-review-verdict-axes.md` puts this BEFORE the UI, because the
new vocabulary is worthless if the eight banked rounds cannot be read in it.

Four properties, each bought by a specific past failure:

  A. Every verdict on disk maps. 605 of them, across three vocabularies.
  B. An unknown token RAISES rather than being skipped. A loader that
     `continue`s past what it does not recognise hid a signed 25-verdict round
     for eight months (Lesson 38).
  C. `applies_to` separates base data from already-corrected data. A `correct`
     on corrected data is not a `correct` on base data, and merging them lets
     the canonical round silently undo the correction the earlier round asked
     for (Lesson 3).
  D. `adjust` maps to IS-A-STORY plus a wrong extent. Counting it as a
     rejection is what turned a boundary failure into a fake classification
     problem and made Classification look like the weakest capability for
     months (Lesson 30).

No API key, no network, no Node.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        'map_verdict_vocabularies', ROOT / 'scripts' / 'map_verdict_vocabularies.py')
    mod = importlib.util.module_from_spec(spec)
    sys.modules['map_verdict_vocabularies'] = mod
    spec.loader.exec_module(mod)
    return mod


MOD = _load()


class VerdictVocabularyMap(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rows, cls.unknown = [], []
        for rel, cfg in MOD.ROUND_VOCAB.items():
            path = ROOT / rel
            if not path.exists():
                continue
            pairs, _dropped = MOD._verdicts_in(path, cfg['vocab'])
            for key, token, extra in pairs:
                try:
                    shape = MOD.map_verdict(cfg['vocab'], token, extra)
                except MOD.UnknownVerdict:
                    cls.unknown.append((rel, key, token))
                    continue
                cls.rows.append(dict(round=path.name, key=key,
                                     applies_to=cfg['applies_to'],
                                     old_verdict=token, **shape))

    # A -------------------------------------------------------------------
    def test_every_banked_verdict_maps(self):
        self.assertEqual(self.unknown, [], f"unmapped verdicts: {self.unknown}")
        self.assertGreater(len(self.rows), 500,
                           "the banked rounds hold ~605 verdicts; a sharp drop "
                           "means a round stopped being read")

    def test_every_shape_is_complete(self):
        for r in self.rows:
            for axis in ('is_story', 'extent', 'confidence', 'grouping'):
                self.assertIn(axis, r, f"{r['round']} {r['key']} missing {axis}")
            self.assertIn(r['is_story'], ('yes', 'no', 'borderline'),
                          f"{r['round']} {r['key']} has no story verdict")

    # B -------------------------------------------------------------------
    def test_unknown_verdict_raises_rather_than_skips(self):
        with self.assertRaises(MOD.UnknownVerdict):
            MOD.map_verdict('base_binary', 'banana')
        with self.assertRaises(MOD.UnknownVerdict):
            MOD.map_verdict('no_such_vocabulary', 'correct')

    def test_unknown_length_adjustment_raises(self):
        with self.assertRaises(MOD.UnknownVerdict):
            MOD.map_verdict('january_typed', 'correct',
                            {'length_adjustment': 'sideways'})

    # C -------------------------------------------------------------------
    def test_corrected_data_is_kept_distinct_from_base(self):
        applied = {r['applies_to'] for r in self.rows}
        self.assertEqual(applied, {'base', 'corrected'})
        canonical = [r for r in self.rows
                     if r['round'] == 'canonical_review_anonymous_2026-03-17.json']
        self.assertTrue(canonical, "the canonical round vanished from the map")
        for r in canonical:
            self.assertEqual(r['applies_to'], 'corrected')
        for r in self.rows:
            if r['round'] != 'canonical_review_anonymous_2026-03-17.json':
                self.assertEqual(r['applies_to'], 'base',
                                 f"{r['round']} is not corrected-data")

    # D -------------------------------------------------------------------
    def test_adjust_is_a_story_with_a_wrong_extent(self):
        adjusts = [r for r in self.rows if r['old_verdict'] == 'adjust']
        self.assertTrue(adjusts, "the canonical round's `adjust` verdicts vanished")
        for r in adjusts:
            self.assertEqual(r['is_story'], 'yes',
                             "`adjust` means the passage IS a story (Lesson 30)")
            self.assertTrue(r['extent'], "`adjust` carries an extent complaint")

    def test_removal_tokens_are_not_inverted(self):
        self.assertEqual(MOD.map_verdict('delta_removal', 'confirm_remove')['is_story'], 'no')
        self.assertEqual(MOD.map_verdict('delta_removal', 'reject_remove')['is_story'], 'yes')

    def test_structured_extent_complaints_survive(self):
        """January's `length_adjustment` is the only structured extent field any
        round ever had. It must reach the extent axis, not the residue."""
        got = MOD.map_verdict('january_typed', 'correct', {'length_adjustment': 'shrink'})
        self.assertEqual(got['is_story'], 'yes')
        self.assertEqual(got['extent'], 'wrong_unspecified')
        self.assertFalse(got['lossy'])
        recovered = [r for r in self.rows if r['extent']]
        self.assertGreaterEqual(len(recovered), 14)

    def test_bare_incorrect_is_marked_lossy_not_guessed(self):
        """FRAMEWORK §7: residue is reported, never guessed into a bucket."""
        got = MOD.map_verdict('base_binary', 'incorrect')
        self.assertTrue(got['lossy'])
        self.assertIsNone(got['extent'])
        self.assertIsNone(got['confidence'])
        self.assertIsNone(got['grouping'])


if __name__ == '__main__':
    unittest.main()
