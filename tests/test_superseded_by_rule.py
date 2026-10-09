"""Jeff's later rulings on 2005 list entries: the list keeps its value, the row leaves
the recall denominator only on a `not`, and a ruling that matches nothing is an error.

Source of the rulings: `results/expert_lists/superseded_by_rule.json`.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from measure_recall_vs_expert_list import SUPERSEDED, apply_superseded  # noqa: E402

RULES = json.loads(SUPERSEDED.read_text())["entries"]


@pytest.mark.parametrize("rule", RULES, ids=lambda r: r["ref"])
def test_every_ruling_is_stamped_on_exactly_one_denominator_row(rule):
    rows = json.loads((ROOT / f"results/recall/{rule['tractate'].lower()}_jeff2005_matches.json").read_text())
    hits = [r for r in rows if (r.get("superseded_by_rule") or {}).get("date") == rule["date"]
            and r["ref"] == rule["ref"]]
    assert len(hits) == 1, f"{rule['ref']}: run scripts/stamp_superseded_recall.py"
    assert hits[0]["counts_for_recall"] is rule["counts_for_recall"]
    # The list's own text is never edited -- the ruling sits beside it.
    assert hits[0]["text"].startswith(rule["text_starts"])


def test_only_a_not_leaves_the_denominator():
    for rule in RULES:
        assert rule["counts_for_recall"] is (rule["ruling"] != "not"), rule["ref"]


def test_a_ruling_that_matches_no_row_raises(tmp_path):
    f = tmp_path / "rules.json"
    f.write_text(json.dumps({"entries": [dict(RULES[0], text_starts="nothing like this")]}))
    with pytest.raises(ValueError, match="matched 0"):
        apply_superseded([{"ref": RULES[0]["ref"], "text": "x"}], RULES[0]["tractate"], f)


def test_unruled_rows_still_count():
    rows = apply_superseded([{"ref": "Ketubot 2b", "text": "x"}], "Gittin")
    assert rows[0]["counts_for_recall"] is True and rows[0]["superseded_by_rule"] is None
