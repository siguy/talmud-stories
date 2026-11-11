"""audit_miss_anatomy and stamp_superseded_recall must follow board.TRACTATES (finding 16)."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_audit_paths_for_a_tractate_with_no_hardcoded_entry():
    audit = _load('audit_miss_anatomy')
    assert audit.runs_for('eruvin') == ['results/v11/eruvin/eruvin_v11.json']
    assert audit.triage_for('eruvin') == ['results/triage/eruvin.json']
    assert audit.runs_for('gittin') == ['results/v11/gittin/gittin_v11.json']  # unchanged


def test_audit_skips_and_logs_a_tractate_with_no_files(caplog):
    audit = _load('audit_miss_anatomy')
    with caplog.at_level('WARNING'):
        got = audit.available(['gittin', 'nonesuch'])
    assert got == ['gittin']                       # no run for it: skipped, no KeyError
    assert any('nonesuch' in r.getMessage() for r in caplog.records)


def test_audit_default_covers_every_board_tractate_that_has_files():
    audit = _load('audit_miss_anatomy')
    import board
    assert set(audit.available(board.TRACTATES)) <= set(board.TRACTATES)
    assert 'yevamot' in audit.available(board.TRACTATES)


def test_stamp_lists_tractates_from_the_board_and_skips_missing(caplog, monkeypatch):
    stamp = _load('stamp_superseded_recall')
    monkeypatch.setattr(stamp.board, 'TRACTATES', list(stamp.board.TRACTATES) + ['nonesuch'])
    with caplog.at_level('WARNING'):
        got = stamp.tractates_with_matches()
    assert 'Yevamot' in got and 'Gittin' in got
    assert 'Eruvin' in got                         # scored 2026-11-08
    assert 'Nonesuch' not in got                   # no matches file: skipped and logged
    assert any('Nonesuch' in r.getMessage() for r in caplog.records)
