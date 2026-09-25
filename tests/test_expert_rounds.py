"""Only the expert's verdicts are ground truth — and every reader asks the same question.

Until 2026-09-25 the board excluded non-expert rounds by filename (`"Simon" in p.name`,
case-sensitive) and the ruler did not exclude them at all. Simon's pre-screen,
`..._simon_prescreen_...` with `reviewer: simon` inside, got past both: the ruler folded
its verdicts into every expert figure on regeneration, and the board listed it as "a
round Jeff gave us" that no ruler reads. These pin the property, not a filename.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('expert_rounds', ROOT / 'scripts/expert_rounds.py')
er = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(er)

PRESCREEN = ROOT / 'validation/feedback/review_2026-09-15_bundle_simon_prescreen_2026-09-16.json'


def test_a_declared_non_expert_is_not_ground_truth():
    assert er.declared_non_expert({'reviewer': 'simon'}) == 'simon'
    assert er.declared_non_expert({'reviewer_name': 'Simon - Test'}) == 'Simon - Test'
    # case does not matter — the filename check that failed was case-sensitive
    assert er.declared_non_expert({'reviewer': 'SIMON'}) == 'SIMON'


def test_jeffs_rounds_are_ground_truth_under_every_name_he_has_used():
    for who in ('anonymous', 'Jeffrey Rubenstein', 'jeff', 'Jeff R.'):
        assert er.declared_non_expert({'reviewer': who}) is None, who
        assert er.declared_non_expert({'reviewer_name': who}) is None, who


def test_an_undeclared_round_is_kept_not_dropped():
    """Every legacy round declares nobody and is Jeff's by provenance. Dropping them is
    Lesson 38 — the January round's 25 verdicts, skipped for eight months."""
    assert er.declared_non_expert({'reviews': {}}) is None
    assert er.declared_non_expert({'reviewer': ''}) is None
    assert er.declared_non_expert(['not', 'a', 'dict']) is None


def test_the_real_prescreen_file_is_recognised_by_its_contents():
    assert er.declared_non_expert(json.loads(PRESCREEN.read_text())) == 'simon'


def test_every_banked_expert_round_on_disk_still_counts():
    """The rule must not have dropped anything Jeff gave us."""
    dropped = []
    for p in sorted((ROOT / 'validation/feedback').glob('*.json')) + \
             sorted((ROOT / 'jeff comms').glob('*.json')):
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        who = er.declared_non_expert(d)
        if who and 'simon' not in who.lower():
            dropped.append((p.name, who))
    assert not dropped, f'a non-Simon round was classed non-expert: {dropped}'


def test_the_ruler_skips_the_prescreen_and_says_so(tmp_path):
    out = tmp_path / 'ketubot_ruler.json'
    r = subprocess.run([sys.executable, 'scripts/build_ruler.py', '--tractate', 'Ketubot',
                        '--out', str(out)], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert 'SKIPPED review_2026-09-15_bundle_simon_prescreen' in r.stdout + r.stderr
    rounds = json.loads(out.read_text())['review_rounds']
    assert not any('prescreen' in name for name in rounds), rounds


def test_the_board_does_not_call_the_prescreen_a_lost_expert_round():
    state = (ROOT / 'STATE.md').read_text()
    section = state.split('Expert verdicts on disk that no ruler reads', 1)
    if len(section) == 2:
        assert 'prescreen' not in section[1].split('## ', 1)[0]
