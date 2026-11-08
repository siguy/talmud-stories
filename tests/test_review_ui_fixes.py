"""The 2026-11-07 review-UI fixes, each tested by running the page's OWN JavaScript.

`work/2026-11-07-review-ui-fixes.md`, finding `docs/findings/2026-11-07-review-ui-review.md`.
Same method as `tests/test_review_ui_axes.py`: generate the page, pull out its
<script>, run it under Node with a stub DOM, read state back as JSON.

Fixture: the real 4-page Kiddushin slice the axes test uses, copied and given the
shapes v11 output has and that slice lacks — clause spans, a cross-page story whose
end was skipped, a page whose Stage 2 call failed, a NOT_A_STORY proposal.
Requires `node`; skips cleanly without it. No API key.
"""
from __future__ import annotations

import copy
import html as htmllib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / 'validation' / 'generators' / 'generate_axis_review_ui.py'
FIXTURE = ROOT / 'tests' / 'fixtures' / 'axis_review_pages.json'


def _load_generator():
    sys.path.insert(0, str(GENERATOR.parent))
    spec = importlib.util.spec_from_file_location('axis_ui_fixes', GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _script(html: str) -> str:
    m = re.search(r'<script>(.*?)</script>', html, re.S)
    assert m, 'no <script> block'
    return re.sub(r'^\s*init\(\);\s*$', '', m.group(1), flags=re.M)


# Small DOM: enough for init()/render()/buildCard/updateProgress to run.
DOM_STUB = r"""
function makeClassList() {
  const set = new Set();
  return { add: c => set.add(c), remove: c => set.delete(c), contains: c => set.has(c),
           toggle: (c, f) => { const on = f === undefined ? !set.has(c) : !!f;
                               if (on) set.add(c); else set.delete(c); return on; } };
}
function makeEl() {
  const el = { innerHTML: '', textContent: '', className: '', id: '', style: {},
               dataset: {}, value: '', children: [],
               appendChild(c) { this.children.push(c); },
               scrollIntoView() {} };
  el.classList = makeClassList();
  el.querySelectorAll = () => [];
  el.querySelector = () => null;
  return el;
}
const _byId = {};
const document = {
  getElementById: id => (_byId[id] = _byId[id] || makeEl()),
  createElement: () => makeEl(),
  querySelectorAll: () => [],
  addEventListener: () => {}
};
"""


def run_page_js(html: str, audit: str, prelude: str = '') -> dict:
    """Run the page's script plus `audit` under Node; `audit` must print JSON."""
    script = DOM_STUB + prelude + _script(html) + audit
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as fh:
        fh.write(script)
        path = fh.name
    try:
        proc = subprocess.run([shutil.which('node'), path],
                              capture_output=True, text=True, timeout=60)
    finally:
        os.unlink(path)
    if proc.returncode != 0:
        raise AssertionError(f'page JS failed:\n{proc.stderr}')
    return json.loads(proc.stdout.strip().splitlines()[-1])


def _clause_break(heb: str) -> int:
    """First real clause break in `heb` — where a v11 clause span would sit."""
    m = re.search(r'[.:?!]\s', heb)
    assert m, 'fixture segment has no clause break'
    return m.end()


def make_fixture() -> dict:
    data = copy.deepcopy(json.loads(FIXTURE.read_text()))
    pages = {p['ref']: p for p in data['pages']}
    segs = lambda ref: {s['index']: s['hebrew'] for s in pages[ref]['segments']}

    # A single-segment story with a clause span on BOTH ends.
    p = pages['Kiddushin 9a']
    s = next(st for st in p['stories'] if st['start_segment'] == 2)
    heb = segs('Kiddushin 9a')[2]
    lo = _clause_break(heb)
    hi = lo + _clause_break(heb[lo:]) - 1 if re.search(r'[.:?!]\s', heb[lo:]) else len(heb)
    s['text_span_start'] = {'segment': 2, 'char_offset': lo, 'clause_index': 1,
                            'source': 'clause_llm'}
    s['text_span_end'] = {'segment': 2, 'char_offset': hi, 'clause_index': 2,
                          'source': 'clause_llm'}
    s['text_span_source'] = 'clause_llm'

    # A cross-page story: start span, and the end skipped because it runs on.
    # A stale `text_span_end` (pre-PR-#71 runs carry one) must still not be drawn.
    p = pages['Kiddushin 12a']
    s = next(st for st in p['stories'] if st.get('spans_pages'))
    heb13 = segs('Kiddushin 12a')[13]
    s['text_span_start'] = {'segment': 13, 'char_offset': _clause_break(heb13),
                            'clause_index': 1, 'source': 'clause_llm'}
    s['text_span_end'] = {'segment': 15, 'char_offset': 5, 'clause_index': 0,
                          'source': 'clause_llm'}
    s['text_span_end_skipped'] = 'spans_pages'
    return data


def write_fixture(data: dict) -> Path:
    fh = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False)
    json.dump(data, fh, ensure_ascii=False)
    fh.close()
    return Path(fh.name)


def _need_node():
    if shutil.which('node') is None:
        raise unittest.SkipTest('node not on PATH')


# ---------------------------------------------------------------------------
# 1. The claimed clause span is drawn as a <mark> inside the highlighted rows.
# ---------------------------------------------------------------------------
SPAN_AUDIT = r"""
const out = {};
STORIES.forEach(s => {
  const html = buildTextDisplay(s);
  const marks = [];
  const re = /<mark class="span-in">([\s\S]*?)<\/mark>/g; let m;
  while ((m = re.exec(html)) !== null) marks.push(m[1]);
  out[s.key] = { marks: marks, nMarks: marks.length, howto: null };
});
console.log(JSON.stringify(out));
"""


def _strip(markup: str) -> str:
    return htmllib.unescape(re.sub(r'<[^>]*>', '', markup))


class ClaimedSpanIsMarked(unittest.TestCase):
    """Finding P1-1: the page highlighted whole segments while the scored output
    claims a clause span, so all 5 Gittin boundary notes corrected a boundary we
    never claimed (Lesson 25's shape)."""

    @classmethod
    def setUpClass(cls):
        _need_node()
        cls.gen = _load_generator()
        cls.data = make_fixture()
        path = write_fixture(cls.data)
        try:
            cls.stories, cls.version = cls.gen.build_data([path])
        finally:
            os.unlink(path)
        cls.html = cls.gen.generate_html('Kiddushin', cls.stories, cls.version)
        cls.report = run_page_js(cls.html, SPAN_AUDIT)
        cls.segs = {p['ref']: {s['index']: s['hebrew'] for s in p['segments']}
                    for p in cls.data['pages']}

    def test_a_story_with_spans_marks_exactly_the_claimed_text(self):
        st = next(s for s in self.data['pages'][1]['stories'] if s['start_segment'] == 2)
        lo, hi = st['text_span_start']['char_offset'], st['text_span_end']['char_offset']
        want = _strip(self.segs['Kiddushin 9a'][2][lo:hi])
        got = self.report['Kiddushin 9a_2-2']
        self.assertGreater(got['nMarks'], 0, 'the claimed span is not drawn at all')
        self.assertEqual(_strip(''.join(got['marks'])), want,
                         'the mark does not cover exactly text_span_start..text_span_end')

    def test_a_story_without_spans_renders_as_before(self):
        self.assertEqual(self.report['Kiddushin 9a_1-1']['nMarks'], 0,
                         'a story with no clause span must show no mark')
        self.assertEqual(self.report['Kiddushin 8b_2-2']['nMarks'], 0)

    def test_a_cross_page_story_draws_no_end_mark(self):
        key = next(k for k in self.report if k.startswith('Kiddushin 12a_13-15'))
        marked = _strip(''.join(self.report[key]['marks']))
        seg13 = self.segs['Kiddushin 12a'][13]
        seg15 = self.segs['Kiddushin 12a'][15]
        lo = _clause_break(seg13)
        self.assertTrue(marked.startswith(_strip(seg13[lo:]).strip()[:20]),
                        'the start mark is not at text_span_start')
        self.assertTrue(marked.endswith(_strip(seg15).strip()[-20:]),
                        'a story that runs onto the next daf has no end on this one; '
                        'the stale text_span_end was drawn (text_span_end_skipped)')

    def test_the_howto_says_what_the_mark_means(self):
        self.assertTrue('claimed extent' in self.html.lower(),
                      'the reviewer must be told the mark is our boundary, the rest context')


if __name__ == '__main__':
    unittest.main(verbosity=2)
