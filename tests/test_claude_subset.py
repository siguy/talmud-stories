"""Claude judges only the units Gemini called out_of_scope (plan §2.5), and the site refuses to build if one
of those units lacks a valid Claude answer. Failure injection: a missing, failed or invalid Claude answer
must stop the build, never read as 'not biblical' (Lesson 21 / 38)."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT))

from tests.test_check_tractate_run import build  # noqa: E402


@pytest.fixture
def jd(monkeypatch, tmp_path):
    monkeypatch.setenv('JUDGE_TRACTATE', 'tamid')
    monkeypatch.setenv('JUDGE_PROMPT', 'src/prompts/judge_register_v2.md')
    spec = importlib.util.spec_from_file_location('jd_under_test', ROOT / 'scripts' / 'judge_detector_spans.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    P = build(tmp_path, slug='tamid')
    monkeypatch.setattr(m, 'OUT', Path(P.consensus))
    # judge_labelled_spans is imported once per process and reads JUDGE_PROMPT at import: pin v2 here
    monkeypatch.setattr(m.j, 'PROMPT_PATH', ROOT / 'src/prompts/judge_register_v2.md')
    monkeypatch.setitem(m.j.TEXT_SOURCES, 'Tamid', [str(P.text)])          # absolute: PROJECT_ROOT / absolute == absolute
    return m


def _export(jd, **kw):
    jd.export(1, 20, only_gemini_out_of_scope=True, **kw)
    return json.loads((jd.OUT / 'subagent/manifest.json').read_text())


def test_export_sends_only_the_units_gemini_called_out_of_scope(jd):
    man = _export(jd)
    assert man['units'] == 1 and man['only_gemini_out_of_scope'] is True
    keys = json.loads((jd.OUT / 'subagent/keys/000.json').read_text())
    assert [k['id'] for k in keys] == ['Tamid 25a:0-1']            # the other unit was `story`


def test_full_export_still_sends_everything(jd):
    jd.export(1, 20)
    assert json.loads((jd.OUT / 'subagent/manifest.json').read_text())['units'] == 2


def test_subset_export_refuses_when_gemini_is_not_final(jd):
    g = jd.OUT / 'gemini.json'
    d = json.loads(g.read_text())
    d['rows'][1]['answer'] = {'outcome': 'failed', 'verdict': None}
    g.write_text(json.dumps(d))
    with pytest.raises(SystemExit) as e:
        _export(jd)
    assert 'not final' in str(e.value)
    assert not (jd.OUT / 'subagent/keys').exists()


def test_subset_export_refuses_to_mix_with_an_old_export(jd):
    jd.export(1, 20)                         # a full export is already there
    with pytest.raises(SystemExit):
        _export(jd)


def test_subset_import_marks_claude_json_as_a_subset_and_gate_g6_goes_green(jd):
    import check_tractate_run as C
    from tractates import Paths
    _export(jd)
    key = json.loads((jd.OUT / 'subagent/keys/000.json').read_text())[0]
    (jd.OUT / 'subagent/answers').mkdir(parents=True, exist_ok=True)
    (jd.OUT / 'subagent/answers/000.json').write_text(json.dumps(
        {'01': {'verdict': 'out_of_scope', 'segments': [key['passage'][0]], 'rules': ['R-S1'], 'reason': 'biblical'}}))
    jd.import_('claude-test')
    d = json.loads((jd.OUT / 'claude.json').read_text())
    assert d['meta']['subset'] == 'gemini_out_of_scope' and [r['answer']['outcome'] for r in d['rows']] == ['ok']
    r = C.g6_judge(Paths('tamid', jd.OUT.parents[2]), 'claude')
    assert r.status == 'green', r.failures


def test_site_build_refuses_a_flagged_unit_with_no_claude_answer(tmp_path, monkeypatch):
    import build_site_data as b
    build(tmp_path, slug='tamid')
    monkeypatch.setattr(b, 'ROOT', tmp_path)
    monkeypatch.setitem(b.SOURCES, 'tamid', b.unreviewed_source('tamid'))
    assert b.judge_cells('tamid')[0]                                  # complete: fine, and the unit is flagged
    c = tmp_path / 'results/consensus/tamid/claude.json'
    d = json.loads(c.read_text())
    for bad in (None, {'outcome': 'invalid', 'verdict': None}, {'outcome': 'failed', 'verdict': None}):
        rows = [r for r in d['rows'] if r['id'] != 'Tamid 25a:0-1']
        if bad:
            rows.append({'id': 'Tamid 25a:0-1', 'answer': bad})
        c.write_text(json.dumps({**d, 'rows': rows}))
        with pytest.raises(SystemExit) as e:
            b.judge_cells('tamid')
        assert 'Tamid 25a:0-1' in str(e.value)


def test_a_subset_claude_file_is_enough_for_the_site(tmp_path, monkeypatch):
    """Unflagged units need no Claude answer: they ship whatever Claude says."""
    import build_site_data as b
    build(tmp_path, slug='tamid')
    monkeypatch.setattr(b, 'ROOT', tmp_path)
    monkeypatch.setitem(b.SOURCES, 'tamid', b.unreviewed_source('tamid'))
    c = tmp_path / 'results/consensus/tamid/claude.json'
    d = json.loads(c.read_text())
    c.write_text(json.dumps({**d, 'rows': [r for r in d['rows'] if r['id'] == 'Tamid 25a:0-1']}))
    assert b.judge_cells('tamid') == ({('Tamid 25a', 0), ('Tamid 25a', 1)}, set())


def test_site_build_stops_on_a_red_gate_for_an_unreviewed_tractate(tmp_path, monkeypatch):
    import build_site_data as b

    def m(f):
        f['results/v14/tamid/run1.json']['run_meta']['stage2_errors'] = ['Tamid 25a: boom']
    build(tmp_path, m, slug='tamid')
    monkeypatch.setattr(b, 'ROOT', tmp_path)
    monkeypatch.setitem(b.SOURCES, 'tamid', b.unreviewed_source('tamid'))
    for t in [t for t in b.SOURCES if t != 'tamid']:
        monkeypatch.delitem(b.SOURCES, t)
    with pytest.raises(SystemExit) as e:
        b.check_unreviewed_gates()
    assert 'tamid g3:run1' in str(e.value)


def test_biblical_flags_and_ships_and_only_gemini_biblical_plus_claude_not_drops(tmp_path, monkeypatch):
    """Simon 2026-11-10: biblical stories ship, flagged for Jeff's catalogue; a passage Gemini calls biblical and
    Claude calls not a story is dropped."""
    import build_site_data as b
    build(tmp_path, slug='tamid')
    monkeypatch.setattr(b, 'ROOT', tmp_path)
    monkeypatch.setitem(b.SOURCES, 'tamid', b.unreviewed_source('tamid'))
    c = tmp_path / 'results/consensus/tamid/claude.json'
    d = json.loads(c.read_text())
    for r in d['rows']:
        if r['id'] == 'Tamid 25a:0-1':
            r['answer'] = {'outcome': 'ok', 'verdict': 'not'}
    c.write_text(json.dumps(d))
    assert b.judge_cells('tamid') == (set(), {('Tamid 25a', 0), ('Tamid 25a', 1)})


def test_site_reads_the_grade_from_before_the_biblical_actor_filter():
    import build_site_data as b
    s = {'classification': 'NOT_A_STORY', 'filtered_as_biblical': True, 'classification_pre_biblical_filter': 'YES'}
    assert b.site_classification(s) == 'YES'
    assert b.site_classification({'classification': 'BORDERLINE'}) == 'BORDERLINE'
