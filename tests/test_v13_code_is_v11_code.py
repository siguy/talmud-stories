"""v13 is v11's code with new prompt wording — so v11's behaviour tests cover v13.

The pre-Eruvin fixes (PRs #69-#71) are pinned by tests that import v11. v13 was copied
from that fixed v11 on 2026-11-07 and changed only its prompt text, its version string
and two dead features. This test makes that claim checkable: every function and method
in v13 has v11's exact source, except the ones named here with the reason. A code change
to v13 that is not listed fails here, and the v11 tests no longer vouch for it.
"""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# name -> why it may differ from v11
ALLOWED = {
    'build_detection_prompt': 'v12 wording + 2026-10-25 rulings; SERIES_RULE splice removed',
    '_twin_prompt': 'v12 wording + 2026-10-25 rulings',
    '_find_additional_stories': 'SERIES_RULE second-pass clause removed',
    '_stage2_fingerprint': 'SERIES_RULE strings no longer hashed (they do not exist)',
    'run_pipeline': "'version': 'v13'; deprecated skip_triage alias removed",
}


def _functions(path):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    src = path.read_text(encoding='utf-8')
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.setdefault(node.name, []).append(ast.get_source_segment(src, node))
    return out


def test_v13_functions_match_v11_except_the_listed_ones():
    v11 = _functions(ROOT / 'src/story_detector_v11.py')
    v13 = _functions(ROOT / 'src/story_detector_v13.py')
    assert set(v11) == set(v13), set(v11) ^ set(v13)
    differ = {n for n in v11 if v11[n] != v13[n]}
    assert differ <= set(ALLOWED), f'v13 code drifted from v11 in {differ - set(ALLOWED)}'
    stale = set(ALLOWED) - differ
    assert not stale, f'listed as different but identical — drop from ALLOWED: {stale}'


def test_the_runner_imports_v13():
    src = (ROOT / 'scripts/run_new_tractate.py').read_text(encoding='utf-8')
    assert 'story_detector_v11' not in src.replace("'src.story_detector_v11' -> 'v11'", '')
    assert src.count('story_detector_v13') == 2
