"""The golden may only grow.

`scripts/build_canonical.py` reconstructs the Ketubot golden from the base runs
plus the 2026-02 feedback and the 2026-03 review. The golden has moved on without
it, so re-running it must never remove a story or change an expert judgment.

An earlier version of this guard tried to DETECT newer work by matching '2026-06'
against keys actually written '2026_06'. It never fired. These tests pin the
replacement, which compares against what is on disk instead of guessing.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


def load_module(tmp_output):
    """Import build_canonical with OUTPUT_PATH pointed somewhere disposable."""
    spec = importlib.util.spec_from_file_location(
        "build_canonical_under_test", PROJECT_ROOT / "scripts" / "build_canonical.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.OUTPUT_PATH = tmp_output
    return mod


def doc(*stories):
    """Build a canonical-shaped doc from (ref, start, end, **fields) tuples."""
    pages = {}
    for ref, lo, hi, *rest in stories:
        extra = rest[0] if rest else {}
        pages.setdefault(ref, {'ref': ref, 'stories': []})
        pages[ref]['stories'].append(
            {'start_segment': lo, 'end_segment': hi, **extra})
    return {'pages': list(pages.values())}


BLIND = {'classification': 'YES', 'source': 'jeff_2005_list',
         'blind': True, 'never_detected': True}


@pytest.fixture
def live(tmp_path):
    """A golden on disk holding one ordinary story and one blind-list story."""
    path = tmp_path / "ketubot_canonical.json"
    path.write_text(json.dumps(doc(
        ('Ketubot 10a', 1, 2, {'classification': 'YES'}),
        ('Ketubot 53a', 11, 11, BLIND),
    )), encoding='utf-8')
    return path


def test_refuses_to_remove_a_story(live, capsys):
    mod = load_module(live)
    rebuild = doc(('Ketubot 10a', 1, 2, {'classification': 'YES'}))  # 53a dropped
    with pytest.raises(SystemExit) as e:
        mod.refuse_unless_purely_additive(rebuild)
    assert e.value.code == 1
    out = capsys.readouterr().out
    assert "REFUSING TO WRITE" in out
    assert "Ketubot 53a seg 11-11" in out
    assert "NOT REGENERABLE" in out          # names why it cannot be recovered


def test_refuses_to_change_an_expert_judgment(live, capsys):
    mod = load_module(live)
    rebuild = doc(
        ('Ketubot 10a', 1, 2, {'classification': 'NOT_A_STORY'}),   # Jeff said YES
        ('Ketubot 53a', 11, 11, BLIND),
    )
    with pytest.raises(SystemExit) as e:
        mod.refuse_unless_purely_additive(rebuild)
    assert e.value.code == 1
    out = capsys.readouterr().out
    assert "expert judgments would be CHANGED" in out
    assert "'YES' -> 'NOT_A_STORY'" in out


def test_allows_a_purely_additive_rebuild(live, capsys):
    mod = load_module(live)
    rebuild = doc(
        ('Ketubot 10a', 1, 2, {'classification': 'YES'}),
        ('Ketubot 53a', 11, 11, BLIND),
        ('Ketubot 77a', 8, 8, {'classification': 'YES'}),           # new
    )
    mod.refuse_unless_purely_additive(rebuild)                       # must not exit
    assert "Purely additive: 1 new stories" in capsys.readouterr().out


def test_allows_writing_when_no_golden_exists_yet(tmp_path):
    mod = load_module(tmp_path / "does_not_exist.json")
    mod.refuse_unless_purely_additive(doc(('Ketubot 10a', 1, 2)))    # must not exit


def test_override_flag_permits_the_loss_but_says_so(live, capsys, monkeypatch):
    mod = load_module(live)
    monkeypatch.setattr(sys, 'argv', ['build_canonical.py', mod.OVERRIDE_FLAG])
    mod.refuse_unless_purely_additive(doc(('Ketubot 10a', 1, 2, {'classification': 'YES'})))
    assert "discarding 1 stories" in capsys.readouterr().out


def test_the_real_golden_would_refuse_a_rebuild_today():
    """End-to-end on the live file: today's golden must not be reconstructible."""
    spec = importlib.util.spec_from_file_location(
        "build_canonical_live", PROJECT_ROOT / "scripts" / "build_canonical.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    live = json.loads(mod.OUTPUT_PATH.read_text(encoding='utf-8'))
    blind = [s for p in live['pages'] for s in p.get('stories', [])
             if s.get('source') == 'jeff_2005_list']
    assert blind, "the golden should still hold Jeff's blind-list stories"
    # A rebuild that lacks them (which is what this script produces) must refuse.
    without = {'pages': [{'ref': p['ref'],
                          'stories': [s for s in p.get('stories', [])
                                      if s.get('source') != 'jeff_2005_list']}
                         for p in live['pages']]}
    with pytest.raises(SystemExit):
        mod.refuse_unless_purely_additive(without)
