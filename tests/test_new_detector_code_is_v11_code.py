"""v13 and v14 are v11's code with new prompt wording — so v11's behaviour tests cover them.

v14 (2026-11-07) is v13 plus three prompt sentences; it differs from v11 in exactly the
same functions, for the same reasons, so the same ALLOWED list applies to both.


The pre-Eruvin fixes (PRs #69-#71) are pinned by tests that import v11. v13 was copied
from that fixed v11 on 2026-11-07 and changed only its prompt text, its version string
and two dead features. This test makes that claim checkable: every function and method
in v13 has v11's exact source, except the ones named here with the reason. A code change
to v13 that is not listed fails here, and the v11 tests no longer vouch for it.
"""
import ast
import sys

import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# name -> why it may differ from v11 (v14's three edits sit inside build_detection_prompt)
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


@pytest.mark.parametrize('version', ['v13', 'v14'])
def test_functions_match_v11_except_the_listed_ones(version):
    v11 = _functions(ROOT / 'src/story_detector_v11.py')
    new = _functions(ROOT / f'src/story_detector_{version}.py')
    assert set(v11) == set(new), set(v11) ^ set(new)
    differ = {n for n in v11 if v11[n] != new[n]}
    assert differ <= set(ALLOWED), f'{version} code drifted from v11 in {differ - set(ALLOWED)}'
    stale = set(ALLOWED) - differ
    assert not stale, f'listed as different but identical — drop from ALLOWED: {stale}'


def test_the_runner_imports_v11():
    """v13 and v14 were measured on the Yevamot slice and not adopted (2026-11-07):
    neither found as many list stories as v11, and both kept Gemara commentary as a
    story. Moving the runner is a detector decision, so it is pinned here."""
    src = (ROOT / 'scripts/run_new_tractate.py').read_text(encoding='utf-8')
    imports = [l for l in src.splitlines() if 'import' in l and 'story_detector_v' in l]
    assert len(imports) == 2 and all('story_detector_v11' in l for l in imports), imports
