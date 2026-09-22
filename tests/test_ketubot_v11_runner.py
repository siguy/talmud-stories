"""Ketubot on the v11 runner: cross-tractate few-shots, and inputs that match the sources.

Three properties, all of which failed silently before this item existed:

  - **No tractate is ever scored on its own labels.** Critical Rule #2 / Lesson 2. The
    runner must *raise*, not warn and fall back: a fallback to Ketubot labels on a
    Ketubot run produces a plausible, wrong, CIRCULAR number with nothing to flag it.
  - **The property is tested, never the filename.** `db.tractates` is read off the
    entries, because a filename comparison would have called the blind Kiddushin
    boundary set a corrections set.
  - **The consolidated caches still hold what the sources hold.** Asserted by digest and
    by count, never by a composite (Critical Rule #5).
"""
import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

runner = importlib.import_module('scripts.run_new_tractate')
from src.ground_truth import GroundTruthDB  # noqa: E402


# --- the few-shot guard --------------------------------------------------

def test_every_known_tractate_has_a_source_and_it_is_never_itself():
    for tractate in runner.KNOWN:
        source = runner.FEW_SHOT_SOURCE.get(tractate)
        assert source, f'{tractate} has no declared few-shot source'
        assert source != tractate, f'{tractate} would be scored on its own labels'


def test_ketubot_reads_kiddushin_labels_and_none_are_ketubot():
    db = runner.load_ground_truth(GroundTruthDB, 'ketubot')
    assert db.entries, 'no Kiddushin few-shot entries loaded'
    assert db.tractates == {'kiddushin'}
    assert 'ketubot' not in db.tractates


def test_other_tractates_still_read_ketubot_labels():
    for tractate in ('gittin', 'yevamot', 'eruvin'):
        db = runner.load_ground_truth(GroundTruthDB, tractate)
        assert db.tractates == {'ketubot'}
        assert tractate not in db.tractates


def test_a_same_tractate_source_raises_rather_than_falling_back(monkeypatch):
    monkeypatch.setitem(runner.FEW_SHOT_SOURCE, 'ketubot', 'ketubot')
    with pytest.raises(SystemExit):
        runner.load_ground_truth(GroundTruthDB, 'ketubot')


def test_an_undeclared_tractate_raises(monkeypatch):
    monkeypatch.delitem(runner.FEW_SHOT_SOURCE, 'ketubot')
    with pytest.raises(SystemExit):
        runner.load_ground_truth(GroundTruthDB, 'ketubot')


def test_labels_that_leak_the_run_tractate_raise(monkeypatch):
    """Even with the map right, entries from the scored tractate must stop the run."""
    def leaky(db):
        db.load_from_canonical(str(ROOT / 'results' / 'canonical' /
                                   'kiddushin_canonical.json'))
        db.entries['Ketubot 5a_0-1'] = next(iter(db.entries.values()))
        db.entries['Ketubot 5a_0-1'].tractate = 'Ketubot'
        return True
    monkeypatch.setitem(runner._LABEL_LOADERS, 'kiddushin', leaky)
    with pytest.raises(SystemExit):
        runner.load_ground_truth(GroundTruthDB, 'ketubot')


# --- key parsing ---------------------------------------------------------

def test_keys_parse_for_every_tractate_not_only_ketubot():
    db = GroundTruthDB()
    db.load_from_canonical(str(ROOT / 'results' / 'canonical' /
                               'kiddushin_canonical.json'))
    unparsed = [k for k, e in db.entries.items() if e.page_ref is None]
    assert not unparsed, f'{len(unparsed)} Kiddushin keys did not parse: {unparsed[:5]}'
    assert all(e.tractate == 'Kiddushin' for e in db.entries.values())


# --- the consolidated inputs --------------------------------------------

def test_consolidated_ketubot_matches_its_sources():
    """`--check` rebuilds from the v5/v7 files and compares digests."""
    r = subprocess.run([sys.executable, 'scripts/consolidate_legacy_pages.py', '--tractate', 'ketubot', '--check'],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_ketubot_pages_and_triage_line_up():
    pages = json.loads((ROOT / 'results' / 'sefaria' / 'ketubot.json').read_text())['pages']
    triage = json.loads(
        (ROOT / 'results' / 'triage' / 'ketubot.json').read_text())['triage_results']
    refs = [p['ref'] for p in pages]
    assert len(refs) == 222, f'{len(refs)} pages, expected 222'
    assert len(set(refs)) == len(refs), 'duplicate refs'
    assert set(refs) == set(triage), 'triage and pages cover different refs'
    assert all(p['segments'] for p in pages), 'a page came through with no segments'
    # A label list longer than the page means the caches disagree about the text.
    assert not [r for r in refs
                if len(triage[r]) > len(next(p for p in pages if p['ref'] == r)['segments'])]


def test_ketubot_is_runnable_and_dry_run_spends_nothing(monkeypatch):
    monkeypatch.delenv('GOOGLE_API_KEY', raising=False)
    assert 'ketubot' in runner.KNOWN
    r = subprocess.run([sys.executable, 'scripts/run_new_tractate.py',
                        '--tractate', 'ketubot', '--dry-run'],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert 'DRY RUN' in r.stdout
    assert 'cross-tractate for ketubot' in r.stdout
