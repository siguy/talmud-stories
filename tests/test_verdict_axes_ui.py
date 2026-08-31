"""The review UI must record WHICH thing is wrong, and must not let a verdict lie.

Regression guard for Phase B of `work/2026-08-30-review-verdict-axes.md`. Like
`tests/test_review_ui_symmetry.py`, this executes the page's ACTUAL JavaScript under Node
against a real fixture rather than asserting on the Python source -- a guard that reads
the generator instead of running it cannot catch a page that is broken in the browser.

The four properties, each bought by a measured failure:

  A. ONE CLICK. Pressing `Yes` writes a complete record with every axis at `right`.
     Review is the bottleneck -- weeks per tractate -- and it holds the only DERIVED gate
     in FRAMEWORK. Any design that adds a click to the common case is rejected on that
     ground alone, so the common case is tested.

  B. A VERDICT CANNOT CONTRADICT ITSELF. Answering "not a story" hides AND clears the
     extent / confidence / grouping axes, which presuppose the passage IS a story. Two of
     the 34 hand-sorted notes affirm and reject at once -- `Ketubot 62a_4-4`, "This is
     clearly a story. Keep as a 'Yes'", recorded as a rejection and counted against
     precision. Under this shape it is unrecordable.

  C. DIRECTION IS RECORDED. `incorrect` has meant two opposite things: "you wrongly called
     this a story" and "you wrongly called this NOT a story". Phase A had to recover the
     label under review by re-indexing five old runs. Every saved verdict now carries it,
     and the direction derived from it.

  D. THE SAVED FILE IS STILL READABLE BY THE HARNESSES. A round saved in a shape nothing
     reads scores exactly like a round that never happened (Lesson 27). Each record
     projects onto the existing verdict vocabulary, with an extent complaint mapping to
     `adjust` -- which `build_ruler.py` already treats as accepted, because it means the
     story is real and the boundary is wrong.

Requires `node` on PATH; skips cleanly if absent. No API key, no network.

Run:  pytest tests/test_verdict_axes_ui.py -v
"""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / 'validation' / 'generators' / 'generate_verdict_axes_review_ui.py'
FIXTURE = ROOT / 'tests' / 'fixtures' / 'review_ui_symmetry_stories.json'


def _load_generator():
    spec = importlib.util.spec_from_file_location('axes_ui', GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _extract_script(html: str) -> str:
    match = re.search(r'<script>(.*?)</script>', html, re.S)
    assert match, 'no <script> block in generated page'
    return re.sub(r'^\s*init\(\);\s*$', '', match.group(1), flags=re.M)


# A DOM stub thin enough to be obviously inert and thick enough that the page's real
# save path runs. Nothing here reimplements page logic.
DOM_STUB = r"""
const _els = {};
globalThis.document = {
  getElementById(id) {
    if (!_els[id]) _els[id] = {
      value: '', innerHTML: '', outerHTML: '', style: {},
      classList: { add() {}, remove() {}, toggle() {} },
      scrollIntoView() {}, appendChild() {},
    };
    return _els[id];
  },
  addEventListener() {},
  querySelectorAll() { return []; },
  createElement() { return { classList: { add() {}, remove() {} }, style: {} }; },
};
"""

PROBE_JS = r"""
const out = {};
const K = STORIES[0].key;             // classification: a story label
const K2 = STORIES[1].key;

// --- A. one click ----------------------------------------------------------
answer(K, 'yes', 0);
out.one_click = JSON.parse(JSON.stringify(verdicts[K]));
out.one_click_legacy = legacyVerdict(verdicts[K]);
out.one_click_answered = answered(STORIES[0]);

// --- B. "not a story" clears the axes that presuppose one ------------------
answer(K2, 'yes', 1);
setAxis(K2, 'extent', 'ends_wrong', 1);
setQuote(K2, 'HEBREW QUOTE');
setAxis(K2, 'confidence', 'too_high', 1);
setAxis(K2, 'grouping', 'should_split', 1);
out.before_no = JSON.parse(JSON.stringify(verdicts[K2]));
out.card_with_detail = buildCard(STORIES[1], 1);
answer(K2, 'no', 1);
out.after_no = JSON.parse(JSON.stringify(verdicts[K2]));
out.card_after_no = buildCard(STORIES[1], 1);

// --- C. direction ----------------------------------------------------------
const asStory = { classification: 'YES' };
const asRejected = { classification: 'NOT_A_STORY' };
out.direction = {
  over_call:  direction(asStory,    { is_story: 'no' }),
  under_call: direction(asRejected, { is_story: 'yes' }),
  under_call_borderline: direction(asRejected, { is_story: 'borderline' }),
  agrees:     direction(asStory,    { is_story: 'yes' }),
  unanswered: direction(asStory,    { is_story: null }),
};

// --- D. legacy projection --------------------------------------------------
out.legacy = {
  yes_clean:     legacyVerdict({ is_story: 'yes', extent: 'right' }),
  yes_extent:    legacyVerdict({ is_story: 'yes', extent: 'ends_wrong' }),
  borderline:    legacyVerdict({ is_story: 'borderline', extent: 'right' }),
  no:            legacyVerdict({ is_story: 'no', extent: 'right' }),
  unanswered:    legacyVerdict({ is_story: null, extent: 'right' }),
};

// --- the display axis is independent of axis 1 -----------------------------
toggleDisplay(K2, 1);
out.display_after_no = verdicts[K2].display_broken;

// --- the saved file --------------------------------------------------------
answer(STORIES[2].key, 'borderline', 2);
setAxis(STORIES[2].key, 'extent', 'starts_wrong', 2);
saveResults();
out.saved = JSON.parse(document.getElementById('exportData').value);

console.log(JSON.stringify(out));
"""


class VerdictAxesUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which('node') is None:
            raise unittest.SkipTest('node not on PATH')
        cls.stories = json.loads(FIXTURE.read_text())
        cls.html = _load_generator().generate_html('Kiddushin', cls.stories, ['fixture.json'])
        script = DOM_STUB + _extract_script(cls.html) + PROBE_JS
        proc = subprocess.run([shutil.which('node'), '-e', script],
                              capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            raise AssertionError(f'page JS failed to run:\n{proc.stderr}')
        cls.p = json.loads(proc.stdout)

    # ---- A ----------------------------------------------------------------
    def test_A_yes_alone_writes_a_complete_record(self):
        """The throughput gate. One click must produce a full, correct verdict."""
        v = self.p['one_click']
        self.assertTrue(self.p['one_click_answered'], 'one click did not count as answered')
        self.assertEqual('yes', v['is_story'])
        for axis in ('extent', 'confidence', 'grouping'):
            self.assertEqual('right', v[axis],
                             f'{axis} was not defaulted -- a correct entry now needs a '
                             f'second click, which the brief rejects on throughput grounds')
        self.assertFalse(v['display_broken'])
        self.assertEqual('correct', self.p['one_click_legacy'])

    def test_A_the_page_offers_the_keyboard_path(self):
        """batch_review.html built Y/N/S in Jan 2026 and it was never reused."""
        self.assertIn('function onKey', self.html)
        for key in ('Y', 'B', 'N'):
            self.assertIn(f'<span class="k">{key}</span>', self.html,
                          f'no visible {key} shortcut hint')

    # ---- B ----------------------------------------------------------------
    def test_B_not_a_story_clears_the_axes_that_presuppose_one(self):
        before, after = self.p['before_no'], self.p['after_no']
        self.assertEqual('ends_wrong', before['extent'], 'fixture setup failed')
        self.assertEqual('HEBREW QUOTE', before['extent_quote'])
        self.assertEqual('no', after['is_story'])
        self.assertEqual('right', after['extent'],
                         'an extent complaint survived "this is not a story" -- that is the '
                         'contradiction this shape exists to make unrecordable')
        self.assertEqual('right', after['confidence'])
        self.assertEqual('right', after['grouping'])
        self.assertEqual('', after['extent_quote'])

    def test_B_not_a_story_hides_the_axes_in_the_rendered_card(self):
        self.assertIn('axes-more', self.p['card_with_detail'],
                      'a story with detail should render the extra axes')
        self.assertNotIn('axes-more', self.p['card_after_no'],
                         'the extra axes are still on the card after "not a story"')

    def test_B_the_display_axis_is_not_gated_by_axis_1(self):
        """A page bug can co-occur with any verdict, including a rejection."""
        self.assertTrue(self.p['display_after_no'])
        self.assertIn('the page is showing this wrong', self.p['card_after_no'])

    # ---- C ----------------------------------------------------------------
    def test_C_direction_is_derived_from_the_label_under_review(self):
        d = self.p['direction']
        self.assertEqual('over_call', d['over_call'])
        self.assertEqual('under_call', d['under_call'],
                         'overturning a NOT_A_STORY is a false NEGATIVE and must not be '
                         'pooled with false positives')
        self.assertEqual('under_call_borderline', d['under_call_borderline'])
        self.assertEqual('agrees', d['agrees'])
        self.assertIsNone(d['unanswered'])

    def test_C_every_saved_record_carries_the_label_under_review(self):
        """Phase A had to recover this by re-indexing five old runs. Never again."""
        saved = self.p['saved']['reviews']
        self.assertTrue(saved, 'nothing was saved')
        for key, rec in saved.items():
            self.assertIn('classification_shown', rec, f'{key}: no label under review')
            self.assertTrue(rec['classification_shown'], f'{key}: empty label under review')
            self.assertIn('direction', rec, f'{key}: no direction')

    # ---- D ----------------------------------------------------------------
    def test_D_legacy_projection_covers_every_answer(self):
        lg = self.p['legacy']
        self.assertEqual('correct', lg['yes_clean'])
        self.assertEqual('adjust', lg['yes_extent'],
                         "an extent complaint must project to `adjust` -- build_ruler.py "
                         "reads that as ACCEPTED, which is what a boundary failure is")
        self.assertEqual('correct', lg['borderline'])
        self.assertEqual('incorrect', lg['no'])
        self.assertIsNone(lg['unanswered'])

    def test_D_saved_records_only_use_declared_axis_values(self):
        doc = self.p['saved']
        axes = doc['axes']
        self.assertEqual('verdict_axes_v1', doc['schema'])
        for key, rec in doc['reviews'].items():
            for axis in ('is_story', 'extent', 'confidence', 'grouping'):
                self.assertIn(rec[axis], axes[axis],
                              f'{key}: {axis}={rec[axis]!r} is not a declared value')
            self.assertIsInstance(rec['display_broken'], bool)

    def test_D_an_unanswered_entry_is_not_saved_as_a_verdict(self):
        """A blank is not a judgment. Seven of the 34 banked notes were empty and were
        counted as rejections anyway; a missing answer must simply be absent."""
        saved = self.p['saved']['reviews']
        self.assertEqual(3, len(saved), f'expected the 3 answered entries, got {len(saved)}')
        self.assertEqual(3, self.p['saved']['reviewed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
