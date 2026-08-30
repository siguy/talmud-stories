"""The review UI must never show Hebrew and English at different extents.

This is the regression guard for `tasks/NEXT/04`. The Wave 4 review UI shipped
two display asymmetries, and BOTH of them cost Jeff Rubenstein real attention in
the 2026-07-06 round — he wrote "the Hebrew doesn't match" notes about bugs in
our own rendering, not about detector output:

  1. The Hebrew was cut at the detector's char-offsets (struck through and
     faded) while the English was rendered in full. A reviewer saw a Hebrew
     passage stopping early beside an English one that did not.
     -> Kiddushin 9a seg 2: "English right, Hebrew doesn't match"
  2. Cross-page stories got an "English (continued)" block with no Hebrew
     counterpart, so the Hebrew appeared to stop dead at the page break.
     -> Kiddushin 8b seg 14: "English right but Hebrew cut off; continues to
        seg 0 of next page". 35 stories across the three outputs were affected.

The fix is structural rather than careful: a segment is rendered ONCE, into a
single row that carries both its English and its Hebrew, so no code path can
emit one language without the other.

This test executes the generator's ACTUAL display JavaScript under Node against
real story data, rather than asserting on the Python source. The invariants:

  A. every text block has equal English and Hebrew cell counts
  B. the full source text of every story segment is present, in BOTH languages
     (nothing is trimmed, hidden, faded or struck through)
  C. a cross-page story produces two blocks, each carrying both languages
  D. no strikethrough / v10-trim styling survives anywhere

Fixture is a real slice of the Kiddushin Wave 4 output (Lesson 9 -- fixture !=
production), chosen to cover every shape: a plain multi-segment story, a story
with a Hebrew span annotation, a story whose span severs a Hebrew word, and the
cross-page story Jeff flagged.

Requires `node` on PATH; skips cleanly if absent. No API key, no network.

Run directly:  python3 -m tests.test_review_ui_symmetry
Or via pytest: pytest tests/test_review_ui_symmetry.py -v
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
GENERATOR = ROOT / 'validation' / 'generators' / 'generate_wave4_review_ui.py'
FIXTURE = ROOT / 'tests' / 'fixtures' / 'review_ui_symmetry_stories.json'


def _load_generator():
    spec = importlib.util.spec_from_file_location('wave4_ui', GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _extract_script(html: str) -> str:
    """The page's <script> body, with the DOM-dependent entry point removed.

    Everything else in that script is function declarations plus three inert
    consts, so it evaluates cleanly in Node with no DOM.
    """
    match = re.search(r'<script>(.*?)</script>', html, re.S)
    assert match, 'no <script> block in generated page'
    body = match.group(1)
    body = re.sub(r'^\s*init\(\);\s*$', '', body, flags=re.M)
    return body


# Renders each fixture story through the page's own buildTextDisplay() and
# reports the structure back as JSON.
AUDIT_JS = r"""
const norm = s => String(s || '').replace(/<[^>]*>/g, '')
                                 .replace(/&amp;/g, '&').replace(/&lt;/g, '<')
                                 .replace(/&gt;/g, '>').replace(/&mdash;/g, '—')
                                 .replace(/&#9888;/g, '⚠')
                                 .replace(/\s+/g, ' ').trim();

const results = STORIES.map(story => {
  const html = buildTextDisplay(story);

  // Split into text blocks and count each language's cells per block.
  const blocks = html.split('<div class="text-block">').slice(1).map(b => ({
    en: (b.match(/class="seg-en"/g) || []).length,
    he: (b.match(/class="seg-he"/g) || []).length,
  }));

  // Pull the rendered text of every row, keyed by segment number.
  const rows = {};
  const rowRe = /<div class="seg-row[^"]*">\s*<div class="seg-num">(\d+)<\/div>\s*<div class="seg-en">([\s\S]*?)<\/div>\s*<div class="seg-he">([\s\S]*?)<\/div>\s*<\/div>/g;
  let m;
  while ((m = rowRe.exec(html)) !== null) {
    if (rows[m[1]] === undefined) rows[m[1]] = { en: norm(m[2]), he: norm(m[3]) };
  }

  // Every story segment must appear in full, in both languages.
  const truncated = [];
  const segs = story.page_segments || [];
  for (let i = story.start_segment; i <= story.end_segment; i++) {
    const seg = segs.find(s => s.index === i);
    if (!seg) continue;
    const row = rows[String(i)];
    if (!row) { truncated.push('seg ' + i + ': row missing'); continue; }
    if (row.he !== norm(seg.hebrew)) truncated.push('seg ' + i + ': HEBREW truncated');
    if (row.en !== norm(seg.english)) truncated.push('seg ' + i + ': ENGLISH truncated');
  }

  return {
    key: story.key,
    blocks,
    truncated,
    crossPage: !!(story.spans_pages && story.page2_segments),
    strikethrough: /line-through|v10-trim|v10-kept/.test(html),
    englishOnlyBlock: /English \(continued\)/.test(html),
    marks: (html.match(/<mark class="span-in">/g) || []).length,
  };
});
console.log(JSON.stringify(results));
"""


class ReviewUiSymmetryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if shutil.which('node') is None:
            raise unittest.SkipTest('node not on PATH')
        cls.stories = json.loads(FIXTURE.read_text())
        html = _load_generator().generate_html('Kiddushin', cls.stories)
        script = _extract_script(html) + AUDIT_JS
        proc = subprocess.run([shutil.which('node'), '-e', script],
                              capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            raise AssertionError(f'display JS failed to run:\n{proc.stderr}')
        cls.audit = {r['key']: r for r in json.loads(proc.stdout)}

    def test_fixture_covers_every_shape(self):
        keys = set(self.audit)
        self.assertIn('Kiddushin 9a_2-2', keys, 'span-annotation case missing')
        self.assertIn('Kiddushin 8b_14-14', keys, 'cross-page case missing')
        self.assertTrue(any(r['crossPage'] for r in self.audit.values()))
        self.assertTrue(any(r['marks'] > 0 for r in self.audit.values()),
                        'no span annotation rendered — the marking path is untested')

    def test_A_every_block_pairs_the_two_languages(self):
        for key, r in self.audit.items():
            self.assertTrue(r['blocks'], f'{key}: no text block rendered')
            for n, block in enumerate(r['blocks']):
                self.assertEqual(
                    block['en'], block['he'],
                    f'{key} block {n}: {block["en"]} English cells vs '
                    f'{block["he"]} Hebrew cells — the languages have diverged')

    def test_B_no_story_text_is_hidden_in_either_language(self):
        for key, r in self.audit.items():
            self.assertEqual([], r['truncated'],
                             f'{key}: text hidden from the reviewer — {r["truncated"]}')

    def test_C_cross_page_continuation_carries_both_languages(self):
        cross = {k: r for k, r in self.audit.items() if r['crossPage']}
        self.assertTrue(cross, 'fixture has no cross-page story')
        for key, r in cross.items():
            self.assertEqual(2, len(r['blocks']),
                             f'{key}: expected a continuation block, got {len(r["blocks"])}')
            self.assertGreater(r['blocks'][1]['he'], 1,
                               f'{key}: continuation block has no Hebrew — this is the '
                               f'exact bug Jeff hit on Kiddushin 8b seg 14')
            self.assertGreater(r['blocks'][1]['en'], 1,
                               f'{key}: continuation block has no English')

    def test_D_nothing_is_struck_through_or_english_only(self):
        for key, r in self.audit.items():
            self.assertFalse(r['strikethrough'],
                             f'{key}: trimming styles are back — the story must be '
                             f'HIGHLIGHTED inside the full text, never cut')
            self.assertFalse(r['englishOnlyBlock'],
                             f'{key}: an English-only block is back')


if __name__ == '__main__':
    unittest.main(verbosity=2)
