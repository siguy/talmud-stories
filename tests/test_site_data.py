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
        # docs/technical/septimus-story-filter.md: his YES/HIGH in stories[] only -- never BORDERLINE,
        # LOW_CONFIDENCE, NOT_A_STORY or mishnah_stories[]
        n = sum(1 for p in g["pages"] for s in p.get("stories", []) if s.get("classification") in ("YES", "HIGH_CONFIDENCE"))
        assert len(d["stories"]) == n, t
        assert all(s["reviewed"] and not s["in_mishnah"] for s in d["stories"]), t
        assert all(g["he"] and g["en"] for s in d["stories"] for g in s["segments"])
    y = json.loads((ROOT / "site/data/yevamot.json").read_text())
    assert y["stories"] and not any(s["reviewed"] for s in y["stories"])
    b = json.loads((ROOT / "site/data/berakhot.json").read_text())
    assert b["stories"] and not any(s["reviewed"] for s in b["stories"])


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
        # every shipped story has a note; notes for stories the filter drops are kept (drafted work)
        assert {s["id"] for s in stories} <= set(notes), t
        assert all(len(n["note"]) <= 800 and "<" not in n["note"] for n in notes.values()), t


def test_boundary_extensions_are_display_only_and_bounded():
    ext = json.loads((ROOT / "site/data/boundary_extensions.json").read_text())
    by_id = {s["id"]: s for t in (*GOLDEN_COUNTS, "yevamot", "berakhot") for s in json.loads((ROOT / f"site/data/{t}.json").read_text())["stories"]}
    assert ext
    # an extension whose story the filter does not ship is inert, and kept
    for i, e in ((i, e) for i, e in ext.items() if i in by_id):
        assert 0 <= e["start_back"] <= 2 and 0 <= e["end_forward"] <= 4, i
        assert by_id[i]["extended"] and by_id[i]["extended"]["end_forward"] <= 4, i
    # the golden itself is never rewritten: ids still encode the golden's own range
    assert all(s["id"].count("-") == 3 for s in by_id.values())


# Plan §2 (docs/technical/septimus-signup-plan.md): English words per tractate on the shipped list.
# A change here is a change to the list; update §2 in the same commit.
SITE_WORDS = {"ketubot": 23819, "kiddushin": 11861, "gittin": 25149, "yevamot": 10938, "berakhot": 17934}


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
            assert s["classification"] in ("YES", "HIGH_CONFIDENCE"), s["id"]
            assert s["tier"] == "story" and not s["in_mishnah"], s["id"]


def test_unreviewed_stories_are_definite_in_every_run_and_to_both_judges():
    """Lesson 45: the detector is not deterministic, so a shipped story from an unreviewed tractate
    must be YES/HIGH in EVERY listed run, and both judges must call it a story."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_site_data as b
    unreviewed = [t for t, src in b.SOURCES.items() if not src["reviewed"]]
    assert unreviewed
    for t in unreviewed:
        assert len(b.SOURCES[t]["runs"]) >= 2 and b.SOURCES[t]["consensus"], t
        strong = b.strong_yes_cells(t)
        runs = [b.definite_cells(q) for q in b.SOURCES[t]["runs"]]
        for s in json.loads((ROOT / f"site/data/{t}.json").read_text())["stories"]:
            cells = {(g["ref"], g["i"]) for g in s["segments"]}
            assert cells & strong, s["id"]
            assert all(cells & r for r in runs), s["id"]
