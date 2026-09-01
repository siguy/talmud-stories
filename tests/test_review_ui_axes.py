"""The per-axis review UI, tested by running the page's OWN JavaScript.

Phase B of `work/2026-08-30-review-verdict-axes.md`. Asserting on the Python
source proves nothing about what the reviewer's browser does, and one of the
tests written on 2026-08-31 passed vacuously for exactly that reason. So this
executes the generated page's script under Node, clicks its real buttons by
evaluating their own `onclick` attributes, and reads the state back out.

Each test is a gate the item names, and each was confirmed to FAIL when the
defect it guards is reintroduced (see the finding). The properties:

  A. ONE CLICK completes a correct entry. Review is the bottleneck -- his last
     two rounds returned 1 verdict and 15 -- so any design that adds a click to
     the common case is rejected whatever it buys. Clicking `Yes` and nothing
     else must produce a complete, exportable verdict.
  B. Axes 2-4 are CLOSED until the reviewer opens them. That is what makes four
     axes affordable.
  C. The extent axis is reachable while `is_story` is `yes`. A passage can be a
     story AND be mis-bounded -- `adjust` already meant exactly this, and
     gating extent behind a `No` would throw away the commonest correction we
     get (Lesson 30).
  D. Every exported verdict carries the DETECTOR VERSION it judged (Lesson 36).
  E. `display_problem` is its own field, never prose in `notes` (Lesson 25).
  F. An unanswered card is ABSENT from the export, not exported as a null
     verdict -- "not asked" and "answered nothing" are different facts.
  G. An unset axis exports as null, never as `right`. FRAMEWORK §7: residue is
     reported, not guessed.
  H. The Hebrew quote box appears only once the extent is said to be WRONG, and
     its polarity is STATED. Every quote we hold was typed into a generic notes
     box and mined out by regex afterwards, which leaves 16 of the 70 boundary
     targets in `expert_boundary_targets_v2.json` `mixed` or `unclear`.

Fixture is a real 4-page slice of the shipped Kiddushin output (Lesson 9 --
fixture != production), covering a cross-page story, a Mishnah-withheld story
and plain ones. Requires `node`; skips cleanly without it. No API key.
"""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / 'validation' / 'generators' / 'generate_axis_review_ui.py'
FIXTURE = ROOT / 'tests' / 'fixtures' / 'axis_review_pages.json'


def _load_generator():
    sys.path.insert(0, str(GENERATOR.parent))
    spec = importlib.util.spec_from_file_location('axis_ui', GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _extract_script(html: str) -> str:
    match = re.search(r'<script>(.*?)</script>', html, re.S)
    assert match, 'no <script> block in generated page'
    return re.sub(r'^\s*init\(\);\s*$', '', match.group(1), flags=re.M)


# A DOM small enough to read, real enough to drive the page: buildCard writes
# into `innerHTML`, and the handlers look their card up by id and toggle
# classes on it. Nothing here interprets the page's intent -- it just records.
DOM_STUB = r"""
function makeClassList(el) {
  const set = new Set();
  return {
    add: c => set.add(c), remove: c => set.delete(c),
    contains: c => set.has(c),
    toggle: (c, force) => {
      const on = (force === undefined) ? !set.has(c) : !!force;
      if (on) set.add(c); else set.delete(c);
      return on;
    },
    _set: set
  };
}
function makeEl() {
  const el = { innerHTML: '', className: '', id: '', style: {}, dataset: {},
               children: [], appendChild(c) { this.children.push(c); } };
  el.classList = makeClassList(el);
  el.querySelectorAll = sel => queryCard(el, sel);
  el.querySelector = sel => queryCard(el, sel)[0] || null;
  return el;
}
// The handlers only ever query buttons by [data-axis="..."]; we serve those out
// of the card's own rendered HTML so a mis-wired data attribute really fails.
function queryCard(el, sel) {
  const m = /\[data-axis="([^"]+)"\]/.exec(sel);
  if (!m) return [];
  const out = [];
  const re = /<button[^>]*>/g; let b;
  while ((b = re.exec(el.innerHTML)) !== null) {
    const tag = b[0];
    const axis = (/data-axis="([^"]*)"/.exec(tag) || [])[1];
    if (axis !== m[1]) continue;
    const value = (/data-value="([^"]*)"/.exec(tag) || [])[1];
    const fake = { dataset: { axis: axis, value: value } };
    fake.classList = makeClassList(fake);
    out.push(fake);
  }
  return out;
}
const _byId = {};
const document = {
  getElementById: id => (_byId[id] = _byId[id] || makeEl()),
  createElement: () => makeEl(),
  querySelectorAll: () => []
};
"""

AUDIT_JS = r"""
// Click a button the way a browser would: find it in the card's own HTML and
// evaluate its own onclick attribute. A button wired to the wrong axis, or to
// nothing, fails here rather than passing on a Python-side assertion.
function clickIn(html, pred) {
  const re = /<button[^>]*>/g; let m, clicks = 0;
  while ((m = re.exec(html)) !== null) {
    const tag = m[0];
    if (!pred(tag)) continue;
    const on = (/onclick="([^"]*)"/.exec(tag) || [])[1];
    if (!on) continue;
    eval(on.replace(/&#39;/g, "'").replace(/&quot;/g, '"').replace(/&amp;/g, '&'));
    clicks++;
  }
  return clicks;
}
const byAxisValue = (axis, value) => tag =>
  new RegExp('data-axis="' + axis + '"').test(tag) &&
  (value === undefined || new RegExp('data-value="' + value + '"').test(tag));

const report = { cards: [] };

STORIES.forEach((story, idx) => {
  const html = buildCard(story, idx).innerHTML;
  report.cards.push({
    key: story.key,
    moreAxesClosed: /class="more-axes" data-role="more-axes"/.test(html),
    hasDiscloseButton: /data-role="disclose"/.test(html),
    hasDisplayFlag: /data-axis="display_problem"/.test(html),
    isStoryButtons: (html.match(/data-axis="is_story"/g) || []).length,
    extentButtons: (html.match(/data-axis="extent"/g) || []).length,
    mishnahBadge: /badge mishnah/.test(html),
  });
});

// --- A: one click completes a verdict -------------------------------------
const s0 = STORIES[0];
const card0 = buildCard(s0, 0).innerHTML;
document.getElementById('card-0').innerHTML = card0;
const clicksNeeded = clickIn(card0, byAxisValue('is_story', 'yes'));
report.oneClick = { clicks: clicksNeeded, complete: isComplete(verdicts[s0.key]),
                    exported: Object.keys(buildExport().reviews).length };

// --- C: extent is reachable while is_story === 'yes' ----------------------
clickIn(card0, byAxisValue('extent', 'starts_wrong'));
report.extentOnAStory = { is_story: verdicts[s0.key].is_story,
                          extent: verdicts[s0.key].extent };

// --- E: display_problem is its own field ----------------------------------
clickIn(card0, byAxisValue('display_problem'));
report.displayFlag = { field: verdicts[s0.key].display_problem,
                       notes: verdicts[s0.key].notes };

// --- B: disclosure actually opens the block -------------------------------
const cardEl = document.getElementById('card-0');
cardEl.querySelector = sel => (sel === '[data-role="more-axes"]' ? moreStub : null);
const moreStub = { classList: makeClassList({}) };
toggleAxes(0, null);
report.disclosureOpens = moreStub.classList.contains('open');

// --- H: the quote box -------------------------------------------------------
const s1 = STORIES[1];
const card1 = buildCard(s1, 1).innerHTML;
document.getElementById('card-1').innerHTML = card1;
report.quoteClosedBeforeExtent = /class="quote-box" data-role="quote"/.test(card1);
clickIn(card1, byAxisValue('is_story', 'no'));
clickIn(card1, byAxisValue('extent', 'right'));
report.quoteShutOnExtentRight = !isExtentWrong(verdicts[s1.key].extent);
clickIn(card1, byAxisValue('extent', 'ends_wrong'));
report.quoteOpensOnWrongExtent = isExtentWrong(verdicts[s1.key].extent);
setQuote(s1.key, '\u05d0\u05d1\u05dc \u05d7\u05db\u05de\u05d9\u05dd \u05d0\u05d5\u05de\u05e8\u05d9\u05dd');
clickIn(card1, byAxisValue('quote_polarity', 'include'));
report.quote = { text: verdicts[s1.key].quote,
                 polarity: verdicts[s1.key].quote_polarity,
                 notes: verdicts[s1.key].notes };

// --- D/F/G: the export ------------------------------------------------------
const exported = buildExport();
report.export = {
  detector_version: exported.detector_version,
  schema_version: exported.schema_version,
  applies_to: exported.applies_to,
  reviewed: exported.reviewed,
  total: exported.total_stories,
  rows: Object.values(exported.reviews).map(r => ({
    key: r.page_ref + '_' + r.start_segment + '-' + r.end_segment,
    detector_version: r.detector_version,
    is_story: r.is_story, extent: r.extent,
    confidence: r.confidence, grouping: r.grouping,
    display_problem: r.display_problem,
    quote: r.quote, quote_polarity: r.quote_polarity,
    keys: Object.keys(r)
  }))
};
console.log(JSON.stringify(report));
"""


class AxisReviewUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which('node') is None:
            raise unittest.SkipTest('node not on PATH')
        gen = _load_generator()
        stories, version = gen.build_data([FIXTURE])
        cls.stories, cls.version = stories, version
        html = gen.generate_html('Kiddushin', stories, version)
        cls.html = html
        script = DOM_STUB + _extract_script(html) + AUDIT_JS
        proc = subprocess.run([shutil.which('node'), '-e', script],
                              capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            raise AssertionError(f'axis JS failed to run:\n{proc.stderr}')
        cls.report = json.loads(proc.stdout)

    def test_fixture_covers_every_shape(self):
        self.assertGreaterEqual(len(self.stories), 4)
        self.assertTrue(any(s.get('spans_pages') for s in self.stories),
                        'fixture has no cross-page story')
        self.assertTrue(any(s.get('mishnah_withheld') for s in self.stories),
                        'fixture has no Mishnah-withheld story')

    # A ---------------------------------------------------------------------
    def test_A_a_correct_entry_is_one_click(self):
        one = self.report['oneClick']
        self.assertEqual(one['clicks'], 1,
                         'exactly one button on the card answers "is it a story?" with yes')
        self.assertTrue(one['complete'],
                        'clicking Yes and nothing else must be a COMPLETE verdict — '
                        'anything more makes the common case cost the reviewer more, '
                        'and review is the bottleneck')
        self.assertEqual(one['exported'], 1,
                         'a one-click verdict must reach the export')

    # B ---------------------------------------------------------------------
    def test_B_axes_2_to_4_are_closed_until_opened(self):
        for card in self.report['cards']:
            self.assertTrue(card['moreAxesClosed'],
                            f"{card['key']}: the extra axes are open by default — "
                            f"that is the throughput constraint broken")
            self.assertTrue(card['hasDiscloseButton'],
                            f"{card['key']}: no way to open the extra axes")

    def test_B_disclosure_opens_the_block(self):
        self.assertTrue(self.report['disclosureOpens'],
                        'the disclose button does not open the axes — they would be '
                        'unreachable, which is worse than always-open')

    # C ---------------------------------------------------------------------
    def test_C_extent_is_reachable_on_a_story(self):
        got = self.report['extentOnAStory']
        self.assertEqual(got['is_story'], 'yes')
        self.assertEqual(got['extent'], 'starts_wrong',
                         '"it IS a story and the boundary is wrong" must be sayable — '
                         'it is the commonest correction Jeff gives us (Lesson 30)')

    # D ---------------------------------------------------------------------
    def test_D_every_verdict_carries_the_detector_version(self):
        exp = self.report['export']
        self.assertEqual(exp['detector_version'], self.version)
        self.assertTrue(exp['rows'], 'nothing exported')
        for row in exp['rows']:
            self.assertEqual(row['detector_version'], self.version,
                             'a verdict belongs to the version it judged (Lesson 36)')
        self.assertEqual(exp['schema_version'], 'axes-1')
        self.assertEqual(exp['applies_to'], 'base',
                         'base vs corrected data must be stated, never inferred (Lesson 3)')

    # E ---------------------------------------------------------------------
    def test_E_display_problem_is_a_field_not_a_note(self):
        flag = self.report['displayFlag']
        self.assertTrue(flag['field'],
                        'the display flag did not record — a renderer bug would go back '
                        'to being prose in a notes box (Lesson 25)')
        self.assertEqual(flag['notes'], '',
                         'flagging a display problem must not write into notes')
        for card in self.report['cards']:
            self.assertTrue(card['hasDisplayFlag'],
                            f"{card['key']}: no display-problem control")
        for row in self.report['export']['rows']:
            self.assertIn('display_problem', row['keys'])

    # F ---------------------------------------------------------------------
    def test_F_unanswered_cards_are_absent_not_null(self):
        exp = self.report['export']
        self.assertLess(exp['reviewed'], exp['total'],
                        'the audit only answers one card; the rest must stay unanswered')
        self.assertEqual(len(exp['rows']), exp['reviewed'],
                         '"not asked" and "answered nothing" are different facts and '
                         'must not both export as a row')

    # G ---------------------------------------------------------------------
    def test_G_unset_axes_export_as_null_not_right(self):
        row = self.report['export']['rows'][0]
        self.assertIsNone(row['confidence'],
                          "an axis nobody touched must export null, never 'right' — "
                          "guessing residue into a bucket is the failure FRAMEWORK §7 names")
        self.assertIsNone(row['grouping'])

    # H ---------------------------------------------------------------------
    def test_H_quote_box_is_closed_until_the_extent_is_wrong(self):
        self.assertTrue(self.report['quoteClosedBeforeExtent'],
                        'the quote box is open before anything is said to be wrong — '
                        'that is a cost on the common path')
        self.assertTrue(self.report['quoteShutOnExtentRight'],
                        "'right' is an answer, not a complaint: it must not open the box")
        self.assertTrue(self.report['quoteOpensOnWrongExtent'],
                        'a wrong extent must open the box, or the correction has '
                        'nowhere to go but prose')

    def test_H_quote_polarity_is_stated_not_inferred(self):
        q = self.report['quote']
        self.assertTrue(q['text'], 'the quote did not record')
        self.assertEqual(q['polarity'], 'include',
                         'whether the quoted Hebrew BELONGS in the story or should be '
                         'CUT must be a stated field — inferring it from prose leaves '
                         '16 of our 70 boundary targets mixed or unclear')
        self.assertEqual(q['notes'], '',
                         'the quote must not be smuggled into the notes box, which is '
                         'the situation this replaces')

    def test_H_quote_and_polarity_reach_the_export(self):
        rows = self.report['export']['rows']
        quoted = [r for r in rows if r['quote']]
        self.assertTrue(quoted, 'no quoted correction reached the export')
        for r in quoted:
            self.assertIn('quote_polarity', r['keys'])
            self.assertIn(r['quote_polarity'], ('include', 'exclude'),
                          'a quote without a polarity is the ambiguity, not the fix')

    def test_H_a_quote_box_exists_on_every_card(self):
        self.assertIn('data-role="quote-text"', self.html)
        self.assertIn('data-role="grab"', self.html,
                      'no way to capture the highlighted Hebrew — typing it is a '
                      'transcription risk and a chore')

    # The page must still be the shared display core, not a second copy of it.
    def test_display_core_is_shared_not_reimplemented(self):
        self.assertIn('function buildGrid(', self.html)
        self.assertIn('function buildContinuation(', self.html)
        self.assertNotIn('English (continued)', self.html,
                         'the English-only continuation block is back')
        self.assertNotIn('line-through', self.html,
                         'trimming styles are back — text must be highlighted, never cut')


if __name__ == '__main__':
    unittest.main(verbosity=2)
