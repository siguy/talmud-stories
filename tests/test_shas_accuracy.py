"""Guards for scripts/measure_shas_accuracy.py (docs/findings/2026-11-10-shas-accuracy.md)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import measure_shas_accuracy as M  # noqa: E402


def test_window_expands_the_harness_ends_across_a_daf():
    # The harness writes only a located story's FIRST and LAST cell; reading those two as the
    # story's cells undercounted overlaps (Eruvin 11b:11-13 read as {11, 13}, missing 12).
    units = [("X 2a", 0), ("X 2a", 1), ("X 2a", 2), ("X 2b", 0), ("X 2b", 1)]
    order = (units, {u: k for k, u in enumerate(units)})
    story = {"located": [["X 2a", 1], ["X 2b", 0]]}
    assert M.window(story, order) == {("X 2a", 1), ("X 2a", 2), ("X 2b", 0)}


def test_every_grade_is_one_of_three_and_carries_a_reason():
    g = json.loads((ROOT / M.GRADES).read_text())["grades"]
    for slug, rows in g.items():
        assert slug in M.V14_LISTED, slug
        for sid, r in rows.items():
            assert r["grade"] in ("yes", "borderline", "no"), (sid, r)
            assert r["why"].strip(), sid
