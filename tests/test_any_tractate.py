"""Every reader works for any Bavli tractate by convention (Shas pre-flight item 5), and the five
tractates that already existed keep exactly the paths and names they had."""
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT))

import tractates as T  # noqa: E402
from tests.test_check_tractate_run import build, _run, HE  # noqa: E402
import check_tractate_run as C  # noqa: E402


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_runner_paths_follow_the_convention_and_keep_the_legacy_ones():
    r = _load('run_new_tractate')
    assert r.source_paths('bava_batra') == (ROOT / 'results/sefaria/bava_batra.json', ROOT / 'results/triage/bava_batra.json')
    assert r.source_paths('Bava Batra')[0].name == 'bava_batra.json'
    assert r.source_paths('berakhot')[0] == ROOT / 'results/sefaria/berakhot.json'
    assert r.source_paths('kiddushin')[0] == ROOT / 'results/v7/kiddushin_pages.json'


def test_fetch_writes_the_slug_file_and_saves_sefaria_shape(tmp_path, monkeypatch):
    f = _load('fetch_tractate_pages')
    monkeypatch.setattr(f, 'OUT_DIR', tmp_path)
    refs = ['Bava Batra 2a', 'Bava Batra 2b']
    monkeypatch.setattr(f, 'get_shape', lambda t: (refs, {r: 2 for r in refs}))
    monkeypatch.setattr(f, 'get_page_with_segments',
                        lambda ref: {'ref': ref, 'segments': [{'index': i, 'hebrew': HE, 'english': 'x'} for i in range(2)]})
    monkeypatch.setattr(f.time, 'sleep', lambda s: None)
    pages, expected, out = f.fetch('Bava Batra', 0, False)
    assert out.name == 'bava_batra.json' and not (tmp_path / 'bava batra.json').exists()
    saved = json.loads(out.read_text())
    assert saved['sefaria_shape'] == {r: 2 for r in refs} and saved['tractate'] == 'Bava Batra'
    # and gate G1 accepts it, offline, against that saved shape
    P = T.Paths('bava_batra', tmp_path.parent)
    P.text = out
    r = C.g1_text(P)
    assert r.status == 'green', (r.failures, r.warnings)


def test_judge_config_by_convention_matches_the_hand_written_one_for_the_two_old_tractates(monkeypatch):
    monkeypatch.setenv('JUDGE_PROMPT', 'src/prompts/judge_register_v2.md')
    j = _load('judge_detector_spans')
    assert j.tractate_config('berakhot') == {
        'text': 'results/sefaria/berakhot.json', 'out': 'results/consensus/berakhot',
        'runs': {'v11': 'results/v11/berakhot/berakhot_v11.json', 'v14_r1': 'results/v14/berakhot/run1.json',
                 'v14_r2': 'results/v14/berakhot/run2.json'}}
    assert j.tractate_config('Yevamot') == {
        'text': 'results/sefaria/yevamot.json', 'out': 'results/consensus/yevamot',
        'runs': {'v14_r1': 'results/v11/v14_yevamot/run1.json', 'v14_r2': 'results/v11/v14_yevamot/run2.json'}}
    c = j.tractate_config('Bava Batra')
    assert c['out'] == 'results/consensus/bava_batra' and c['runs']['v14_r2'] == 'results/v14/bava_batra/run2.json'
    assert j.tractate_config('eruvin')['out'] == 'results/consensus/eruvin'   # unheld 2026-11-09 (Simon)


def test_judge_module_takes_a_multi_word_tractate_from_the_environment(monkeypatch):
    monkeypatch.setenv('JUDGE_TRACTATE', 'bava_batra')
    j = _load('judge_detector_spans')
    assert j.TRACTATE == 'Bava Batra' and j.OUT == ROOT / 'results/consensus/bava_batra'
    assert j.j.TEXT_SOURCES['Bava Batra'] == ['results/sefaria/bava_batra.json']


def test_site_build_finds_a_new_tractate_only_when_runs_and_judge_are_there(tmp_path, monkeypatch):
    import build_site_data as b
    build(tmp_path, slug='tamid')
    monkeypatch.setattr(b, 'ROOT', tmp_path)
    src, skipped = b.discover()
    assert 'tamid' in src and src['tamid']['reviewed'] is False
    assert src['tamid']['scope_judges'] == 'results/consensus/tamid' and not skipped
    (tmp_path / 'results/consensus/tamid/gemini.json').unlink()
    src, skipped = b.discover()
    assert 'tamid' not in src and skipped == ['tamid']          # named, never silently dropped
    assert list(src)[:5] == ['ketubot', 'kiddushin', 'gittin', 'yevamot', 'berakhot']


def test_site_build_picks_up_eruvin_since_simons_2026_11_09_decision(tmp_path, monkeypatch):
    import build_site_data as b
    assert 'eruvin' not in b.SITE_HELD
