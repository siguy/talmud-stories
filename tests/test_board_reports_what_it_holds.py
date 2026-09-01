"""
`board.py` must report what an artifact HOLDS, not what its loader happened to recognise.

Three defects found on 2026-09-01, all in the generated board, none visible to
`board.py --check` or `test_bookkeeping.py` — both of which passed throughout:

1. two Kiddushin files collided on a dict key, so the 95-story blind list was
   **overwritten** by a comment harvest and never appeared in STATE.md at all;
2. the comment harvest was then sized with the story-list formula and printed as
   `0 parsed · 0 blind · 0 count for recall` — absence, not "different shape";
3. an expert verdict with `feedback_type: null` was dropped from the round's count,
   so the inventory said 24 where the file holds 25.

Each test fails against the pre-fix code. Lesson 31: verify a guard by simulating the
failure it guards against, not by asserting the fixed behaviour in the abstract.
"""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _board():
    spec = importlib.util.spec_from_file_location("board", ROOT / "scripts/board.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


board = _board()


# ---------------------------------------------------------------- key collision

def test_every_expert_list_gets_its_own_row():
    """
    The bug: `f.stem.split("_")[0]` keyed BOTH `kiddushin_2005.json` and
    `kiddushin_comments_harvested.json` as 'kiddushin', so the second silently replaced
    the first. STATE.md's "Ground truth on hand" table therefore never showed the
    Kiddushin blind list — the denominator behind every Kiddushin recall number on the
    board — and showed a row of zeros in its place.
    """
    on_disk = sorted(p.stem for p in (ROOT / "results/expert_lists").glob("*.json"))
    assert sorted(board.expert_lists()) == on_disk, (
        "an expert list on disk is missing from the board — two files collided on a key")


def test_the_kiddushin_blind_list_is_present_and_is_not_the_comment_harvest():
    """The specific regression: the row that vanished."""
    rows = board.expert_lists()
    assert "kiddushin_2005" in rows
    assert rows["kiddushin_2005"]["shape"] == "story_list"
    assert rows["kiddushin_2005"]["parsed"] > 0, "the blind list rendered as empty"


# ---------------------------------------------------------------- shape, not zero

def test_a_comment_harvest_is_sized_in_remarks_not_in_stories():
    rows = board.expert_lists()
    h = rows["kiddushin_comments_harvested"]
    assert h["shape"] == "comment_harvest"
    assert h["remarks"] == 11
    size = board._expert_list_size(h)
    assert "remarks" in size
    assert "0 parsed" not in size, "a comment harvest is still being sized as a story list"


def test_an_unrecognised_shape_is_named_never_sized_at_zero(tmp_path, monkeypatch):
    """
    Zero because the file is empty and zero because the loader did not recognise it are
    different facts and must print as different facts (Lesson 38).
    """
    d = tmp_path / "results/expert_lists"
    d.mkdir(parents=True)
    (d / "gittin_something_new.json").write_text(json.dumps({"passages": [1, 2, 3]}))
    monkeypatch.setattr(board, "ROOT", tmp_path)

    row = board.expert_lists()["gittin_something_new"]
    assert row["shape"] == "unrecognised"
    size = board._expert_list_size(row)
    assert "not recognised" in size
    assert "passages" in size, "the unknown shape must name its keys so it reads as unsorted"
    assert not size.startswith("0 "), "an unrecognised file must never render as a zero count"


# ---------------------------------------------------------------- flag counting

def test_the_expert_list_size_matches_the_harness_denominator():
    """
    The board and `measure_recall_vs_expert_list.load_expert()` must agree about the size
    of the same set. The harness drops `duplicate_of` entries BEFORE applying the flag,
    giving 90; counting the flag over the raw list gives 91.
    """
    raw = json.loads((ROOT / "results/expert_lists/kiddushin_2005.json").read_text())["stories"]
    harness = [s for s in raw
               if s.get("duplicate_of") is None and s.get("counts_for_recall")]
    assert board.expert_lists()["kiddushin_2005"]["counts_for_recall"] == len(harness)

    ruler = json.loads((ROOT / "results/rulers/kiddushin_ruler.json").read_text())
    assert ruler["metrics"]["detection"]["denominator"] == len(harness), (
        "the ruler's denominator and the board's count for recall have drifted apart")


# ---------------------------------------------------------------- verdict counting

def test_a_null_verdict_with_a_note_still_counts():
    """
    Ketubot 17a in the 2026-01-08 round carries `feedback_type: null` and a note in which
    Jeff states the English and Aramaic do not correlate and then quotes the Hebrew of the
    story the excerpt contains. Counting truthily dropped it: the single richest verdict in
    the round was the one the inventory could not see.
    """
    f = ROOT / "validation/feedback/ketubot_review_Jeffrey_Rubenstein_2026-01-08.json"
    data = json.loads(f.read_text())
    assert data["reviewed_count"] == 25, "fixture changed"
    assert board._verdict_count(f) == data["reviewed_count"] == len(data["feedback"])


def test_the_file_s_own_reviewed_count_is_what_the_board_prints():
    """A round that states its own size must never be re-derived to a smaller number."""
    for f, n in board.unfolded_verdict_files():
        data = json.loads((ROOT / "validation/feedback" / f).read_text())
        if isinstance(data.get("reviewed_count"), int):
            assert n == data["reviewed_count"], f"{f}: board says {n}, file says its own size"


@pytest.mark.parametrize("entry,why", [
    ({"ref": "Ketubot 17a", "feedback_type": None, "notes": "there is a story here"},
     "null type with a note — the exact 17a shape"),
    ({"ref": "Ketubot 5a", "feedback_type": "correct"}, "an ordinary typed verdict"),
    ({"ref": "Ketubot 5a", "verdict": "NOT_A_STORY"}, "the other rounds' vocabulary"),
    ({"ref": "Ketubot 5a", "notes": "boundary is wrong"}, "prose only, no dropdown"),
])
def test_every_shape_of_expert_judgement_is_counted(entry, why):
    assert board._is_verdict(entry), why


def test_a_row_carrying_no_judgement_at_all_is_not_counted():
    """The counter must still exclude filler, or every empty row inflates a round."""
    assert not board._is_verdict({"ref": "Ketubot 5a"})
    assert not board._is_verdict({})
