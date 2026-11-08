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


# ---------------------------------------------------------------------------
# 2. Verdicts survive a reload: localStorage keyed by tractate + detector version.
# ---------------------------------------------------------------------------
STORAGE_STUB = r"""
const _store = (typeof SEED !== 'undefined') ? Object.assign({}, SEED) : {};
const localStorage = {
  getItem: k => (k in _store ? _store[k] : null),
  setItem: (k, v) => { _store[k] = String(v); },
  removeItem: k => { delete _store[k]; }
};
"""

PERSIST_AUDIT_FIRST = r"""
init();
const s0 = STORIES[0], s1 = STORIES[1];
setAxis(s0.key, 'is_story', 'yes', 0);
setAxis(s1.key, 'extent', 'ends_wrong', 1);
setField(s1.key, 'quote_end', 'QEND');
setNotes(s1.key, 'a note');
console.log(JSON.stringify({ store: _store,
  saved: document.getElementById('savedCount').textContent }));
"""

PERSIST_AUDIT_RELOAD = r"""
init();
const s0 = STORIES[0], s1 = STORIES[1];
console.log(JSON.stringify({
  v0: verdicts[s0.key] || null, v1: verdicts[s1.key] || null,
  saved: document.getElementById('savedCount').textContent,
  exported: Object.keys(buildExport().reviews)
}));
"""

PERSIST_AUDIT_BROKEN = r"""
init();
setAxis(STORIES[0].key, 'is_story', 'yes', 0);
console.log(JSON.stringify({ ok: isComplete(verdicts[STORIES[0].key]) }));
"""


class VerdictsSurviveAReload(unittest.TestCase):
    """Finding P1-2: `const verdicts = {}` and nothing else. A reload, a crash or a
    closed tab lost every answer; Eruvin is ~150 cards over several evenings."""

    @classmethod
    def setUpClass(cls):
        _need_node()
        gen = _load_generator()
        stories, version = gen.build_data([FIXTURE])
        cls.version = version
        cls.html = gen.generate_html('Kiddushin', stories, version)
        cls.first = run_page_js(cls.html, PERSIST_AUDIT_FIRST, STORAGE_STUB)
        seed = 'const SEED = ' + json.dumps(cls.first['store']) + ';\n'
        cls.reload = run_page_js(cls.html, PERSIST_AUDIT_RELOAD, seed + STORAGE_STUB)

    def test_every_change_is_written_under_tractate_and_version(self):
        keys = list(self.first['store'])
        self.assertEqual(len(keys), 1, f'expected one storage key, got {keys}')
        self.assertIn('Kiddushin', keys[0])
        self.assertIn(self.version, keys[0],
                      'a verdict belongs to the version it judged (Lesson 36): two '
                      'versions of one tractate must not share saved answers')

    def test_a_reload_restores_every_field(self):
        self.assertEqual(self.reload['v0']['is_story'], 'yes')
        v1 = self.reload['v1']
        self.assertEqual(v1['extent'], 'ends_wrong')
        self.assertEqual(v1['quote_end'], 'QEND')
        self.assertEqual(v1['notes'], 'a note')
        self.assertEqual(len(self.reload['exported']), 1,
                         'the restored complete verdict must reach the export')

    def test_the_header_says_how_many_are_saved(self):
        self.assertIn('1', self.first['saved'])
        self.assertIn('saved locally', self.reload['saved'])

    def test_a_page_without_storage_still_works(self):
        broken = 'const localStorage = { getItem() { throw new Error("blocked"); },' \
                 ' setItem() { throw new Error("blocked"); } };\n'
        got = run_page_js(self.html, PERSIST_AUDIT_BROKEN, broken)
        self.assertTrue(got['ok'], 'blocked storage must not break answering')


# ---------------------------------------------------------------------------
# 3. Pages whose Stage 2 call failed are named, and refuse the build by default.
# ---------------------------------------------------------------------------
def _with_failed_page() -> dict:
    data = copy.deepcopy(json.loads(FIXTURE.read_text()))
    page = data['pages'][2]                       # Kiddushin 50b
    page['stories'] = []
    page['mishnah_stories'] = []
    page['stage2_error'] = 'ResourceExhausted: 429'
    return data


class PagesNotExaminedAreNamed(unittest.TestCase):
    """Finding P2-3: a page whose call failed emitted no card and no count, so it
    looked exactly like a page with no stories — one Jeff would 'confirm'."""

    @classmethod
    def setUpClass(cls):
        cls.gen = _load_generator()
        cls.path = write_fixture(_with_failed_page())
        cls.out = Path(tempfile.mkdtemp()) / 'page.html'

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.path)

    def test_failed_pages_are_counted(self):
        self.assertEqual(self.gen.failed_pages([self.path]), ['Kiddushin 50b'])
        self.assertEqual(self.gen.failed_pages([FIXTURE]), [])

    def test_the_build_refuses_without_allow_failed(self):
        rc = self.gen.main(['--run', str(self.path), '--title', 'Kiddushin',
                            '--out', str(self.out)])
        self.assertNotEqual(rc, 0, 'a run with failed pages must not build silently')
        self.assertFalse(self.out.exists())

    def test_with_allow_failed_the_header_names_them(self):
        rc = self.gen.main(['--run', str(self.path), '--title', 'Kiddushin',
                            '--out', str(self.out), '--allow-failed'])
        self.assertEqual(rc, 0)
        html = self.out.read_text()
        self.assertTrue('1 page not examined (call failed): Kiddushin 50b' in html,
                        'the header must name the pages nobody examined')

    def test_a_clean_run_has_no_such_line(self):
        stories, version = self.gen.build_data([FIXTURE])
        self.assertFalse('not examined' in self.gen.generate_html('K', stories, version))


class OutAnywhere(unittest.TestCase):
    """Finding P3: `--out` outside validation/ui/ wrote the file then crashed on
    `out.relative_to(ROOT)`."""

    def test_out_outside_the_repo_builds_and_returns_0(self):
        gen = _load_generator()
        out = Path(tempfile.mkdtemp()) / 'scratch.html'
        rc = gen.main(['--run', str(FIXTURE), '--title', 'Kiddushin', '--out', str(out)])
        self.assertEqual(rc, 0)
        self.assertTrue(out.exists())


# ---------------------------------------------------------------------------
# 5. Save warns about cards with something said but no "is it a story" answer.
# ---------------------------------------------------------------------------
DROPPED_AUDIT = r"""
init();
const [a, b, c, d] = STORIES;
setAxis(a.key, 'is_story', 'yes', 0);           // complete
setAxis(b.key, 'extent', 'ends_wrong', 1);      // extent only
setNotes(c.key, 'only a note');                 // note only
setAxis(d.key, 'is_story', 'no', 3); setAxis(d.key, 'is_story', 'no', 3);  // set then cleared
saveResults();
console.log(JSON.stringify({
  warning: document.getElementById('exportWarning').textContent,
  exported: Object.keys(buildExport().reviews),
  b: b.page_ref + ' seg ' + b.start_segment + '-' + b.end_segment,
  c: c.page_ref + ' seg ' + c.start_segment + '-' + c.end_segment,
  d: d.page_ref + ' seg ' + d.start_segment + '-' + d.end_segment
}));
"""


class SaveWarnsAboutUnansweredCards(unittest.TestCase):
    """Finding P2-5: a note, extent or quote with no `is_story` click is absent
    from the export (by design — F), and nothing said so."""

    @classmethod
    def setUpClass(cls):
        _need_node()
        gen = _load_generator()
        stories, version = gen.build_data([FIXTURE])
        html = gen.generate_html('Kiddushin', stories, version)
        cls.r = run_page_js(html, DROPPED_AUDIT)

    def test_the_warning_names_each_card_with_unexported_answers(self):
        w = self.r['warning']
        self.assertIn('2 ', w)
        self.assertIn(self.r['b'], w)
        self.assertIn(self.r['c'], w)
        self.assertNotIn(self.r['d'], w, 'a cleared answer is not an answer')

    def test_the_export_itself_is_unchanged(self):
        self.assertEqual(len(self.r['exported']), 1,
                         'unanswered cards stay ABSENT from the export (property F)')
