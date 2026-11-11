"""measure_strict_recall must score against the same list as the matches file (finding 15):
Jeff's later rulings applied, unless --standard 2005 asks for the list as written."""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location(
    'strict', ROOT / 'scripts' / 'measure_strict_recall.py')
strict = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(strict)


def _yevamot():
    return strict.recall.load_expert_json(
        str(ROOT / 'results/expert_lists/yevamot_2005.json'), 'recall')


def test_current_standard_matches_the_matches_file_denominator():
    rows = json.loads((ROOT / 'results/recall/yevamot_jeff2005_matches.json').read_text())
    expected = sum(1 for r in rows if r['counts_for_recall'] and not r.get('call_failed'))
    got = strict.select_stories(_yevamot(), 'Yevamot', 'current')
    assert len(got) == expected
    assert len(got) < len(_yevamot())            # a ruling really removed one


def test_2005_standard_is_the_list_as_written():
    assert len(strict.select_stories(_yevamot(), 'Yevamot', '2005')) == len(_yevamot())


def test_a_lowercase_tractate_still_applies_jeffs_later_rulings(tmp_path):
    """2026-11-10: `--tractate ketubot` built list refs as "ketubot 21b", so the ruling on "Ketubot 21b"
    matched no row and the harness raised under the default --standard current."""
    import subprocess
    out = tmp_path / 'k.json'
    r = subprocess.run([sys.executable, 'scripts/measure_recall_vs_expert_list.py',
                        '--expert-doc', 'jeff comms/b.ketubot (1).doc', '--tractate', 'ketubot',
                        '--detected', 'results/canonical/ketubot_canonical.json', '--out', str(out)],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-1500:]
    assert sum(1 for row in json.loads(out.read_text()) if row.get('superseded_by_rule')) >= 1
