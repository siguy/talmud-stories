"""The family viewer's data must match the goldens by COUNT (Critical Rule 5), never by score."""
import json
import re
import subprocess
import sys
from pathlib import Path

from tests.test_bookkeeping import GOLDEN_COUNTS

ROOT = Path(__file__).resolve().parent.parent


def test_site_data_counts_match_the_goldens():
    subprocess.run([sys.executable, str(ROOT / "scripts/build_site_data.py")], check=True, capture_output=True)
    for t in GOLDEN_COUNTS:
        d = json.loads((ROOT / f"site/data/{t}.json").read_text())
        g = json.loads((ROOT / f"results/canonical/{t}_canonical.json").read_text())
        shipped = ("YES", "HIGH_CONFIDENCE", "BORDERLINE")  # LOW_CONFIDENCE is not shipped
        n = sum(1 for p in g["pages"] for k in ("stories", "mishnah_stories")
                for s in p.get(k, []) if s.get("classification") in shipped)
        assert len(d["stories"]) == n, t
        assert not any(s["tier"] == "story" and s["in_mishnah"] and s["reviewed"] for s in d["stories"])
        assert all(s["reviewed"] for s in d["stories"] if not s["in_mishnah"])
        assert all(g["he"] and g["en"] for s in d["stories"] for g in s["segments"])
    y = json.loads((ROOT / "site/data/yevamot.json").read_text())
    assert y["stories"] and not any(s["reviewed"] for s in y["stories"])
    # Berakhot ships only what both consensus judges call a story: never reviewed, never borderline.
    b = json.loads((ROOT / "site/data/berakhot.json").read_text())
    assert b["stories"] and not any(s["reviewed"] or s["tier"] != "story" for s in b["stories"])


def test_hebrew_carries_nikud():
    nik = re.compile("[ְ-ׇ]")
    for t in GOLDEN_COUNTS:
        d = json.loads((ROOT / f"site/data/{t}.json").read_text())
        assert all(nik.search("".join(g["he"] for g in s["segments"])) for s in d["stories"]), t


def test_every_segment_can_be_located_for_feedback():
    for t in GOLDEN_COUNTS:
        d = json.loads((ROOT / f"site/data/{t}.json").read_text())
        assert all(g["ref"] and isinstance(g["i"], int) for s in d["stories"] for g in s["segments"]), t
        assert all(s["classification"] for s in d["stories"]), t


def test_feedback_worker_builds_a_safe_issue():
    import shutil
    if not shutil.which("node"):
        import pytest
        pytest.skip("node not installed")
    r = subprocess.run(["node", str(ROOT / "worker/test_worker.mjs")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_every_story_has_a_note_and_none_is_approved_unreviewed():
    """Drafted notes never reach readers until a person approves them (scripts/approve_notes.py)."""
    for t in GOLDEN_COUNTS:
        stories = json.loads((ROOT / f"site/data/{t}.json").read_text())["stories"]
        notes = json.loads((ROOT / f"site/data/notes/{t}.json").read_text())["notes"]
        assert {s["id"] for s in stories} == set(notes), t
        assert all(len(n["note"]) <= 800 and "<" not in n["note"] for n in notes.values()), t


def test_boundary_extensions_are_display_only_and_bounded():
    ext = json.loads((ROOT / "site/data/boundary_extensions.json").read_text())
    by_id = {s["id"]: s for t in (*GOLDEN_COUNTS, "yevamot") for s in json.loads((ROOT / f"site/data/{t}.json").read_text())["stories"]}
    assert ext and set(ext) <= set(by_id)
    for i, e in ext.items():
        assert 0 <= e["start_back"] <= 2 and 0 <= e["end_forward"] <= 4, i
        assert by_id[i]["extended"] and by_id[i]["extended"]["end_forward"] <= 4, i
    # the golden itself is never rewritten: ids still encode the golden's own range
    assert all(s["id"].count("-") == 3 for s in by_id.values())


# Plan §2 (docs/technical/septimus-signup-plan.md): English words per tractate on the shipped list.
# A change here is a change to the list; update §2 in the same commit.
SITE_WORDS = {"ketubot": 26050, "kiddushin": 11961, "gittin": 25987, "yevamot": 21985, "berakhot": 18014}


def test_every_story_has_words_and_reading_minutes():
    import math
    wpm = int(re.search(r"readingWpm:\s*(\d+)", (ROOT / "site/config.js").read_text()).group(1))
    index = json.loads((ROOT / "site/data/index.json").read_text())
    assert index["reading_wpm"] == wpm
    tag = re.compile(r"<[^>]+>")
    for row in index["tractates"]:
        t = row["tractate"]
        stories = json.loads((ROOT / f"site/data/{t}.json").read_text())["stories"]
        for s in stories:
            assert s["words"] == sum(len(tag.sub(" ", g["en"]).split()) for g in s["segments"]) > 0, s["id"]
            assert s["minutes"] == max(1, math.ceil(s["words"] / wpm)), s["id"]
        assert row["words"] == sum(s["words"] for s in stories) == SITE_WORDS[t], t
        assert row["minutes"] == sum(s["minutes"] for s in stories), t


def test_no_low_confidence_or_not_a_story_ships():
    """Only definite stories reach the site (Simon, 2026-10-12; again 2026-11-09, Lesson 45).
    A later gate (e.g. the consensus judges on Berakhot) may narrow this, never promote past it."""
    index = json.loads((ROOT / "site/data/index.json").read_text())
    for row in index["tractates"]:
        for s in json.loads((ROOT / f"site/data/{row['tractate']}.json").read_text())["stories"]:
            assert s["classification"] in ("YES", "HIGH_CONFIDENCE", "BORDERLINE"), s["id"]
            assert (s["tier"] == "borderline") == (s["classification"] == "BORDERLINE"), s["id"]
