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
        # docs/technical/septimus-story-filter.md: YES/HIGH in stories[] with Jeff's evidence -- never
        # BORDERLINE, LOW_CONFIDENCE, NOT_A_STORY or mishnah_stories[]. A golden YES/HIGH he never
        # answered (Ketubot 17a:3) is the only gap allowed between the two counts.
        n = sum(1 for p in g["pages"] for s in p.get("stories", []) if s.get("classification") in ("YES", "HIGH_CONFIDENCE"))
        assert n - len(d["stories"]) == {"ketubot": 1}.get(t, 0), t
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
    index = json.loads((ROOT / "site/data/index.json").read_text())["tractates"]
    by_id = {s["id"]: s for r in index for s in json.loads((ROOT / f"site/data/{r['tractate']}.json").read_text())["stories"]}
    assert ext
    # an extension whose story the filter does not ship is inert, and kept
    for i, e in ((i, e) for i, e in ext.items() if i in by_id):
        assert 0 <= e["start_back"] <= 2 and 0 <= e["end_forward"] <= 4, i
        assert by_id[i]["extended"] and by_id[i]["extended"]["end_forward"] <= 4, i
    # the golden itself is never rewritten: ids still encode the golden's own range
    assert all(s["id"].count("-") == 3 for s in by_id.values())


# Plan §2 (docs/technical/septimus-signup-plan.md): English words per tractate on the shipped list.
# A change here is a change to the list; update §2 in the same commit. These are the five tractates
# shipped before the Shas run, pinned so any change to them is noticed. A tractate added by the Shas
# run has no pin here (its total is checked against its own stories below); add one when it ships.
SITE_WORDS = {"ketubot": 23755, "kiddushin": 11861, "gittin": 25149, "yevamot": 18329, "berakhot": 25213}  # yevamot +4, berakhot +7: low-pool promotions (Simon 2026-11-14)


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
        assert row["words"] == sum(s["words"] for s in stories), t
        if t in SITE_WORDS:
            assert row["words"] == SITE_WORDS[t], t
        assert row["minutes"] == sum(s["minutes"] for s in stories), t


def _included(s):
    """True when the story is a passage named in septimus_site_decisions.json `include` (who and when are there; the
    site data deliberately carries no provenance field -- Simon 2026-11-13, 'just count it as a regular story')."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_site_data as b
    cells = {(g["ref"], g["i"]) for g in s["segments"]}
    return any(cells & b.decision_cells(e) for e in b.site_decisions()[2].get(s["tractate"], []))


def _promoted(s):
    """True when the story was added by a `promote` rule of septimus_site_decisions.json (Simon 2026-11-14): it says so
    in `included_by`, and its id is on that rule's list."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_site_data as b
    return any(s.get("included_by") == r["included_by"] for r, _ in b.promotion_rules())


def test_no_low_confidence_or_not_a_story_ships():
    """Only definite stories reach the site (Simon, 2026-10-12; again 2026-11-09, Lesson 45).
    A later gate (e.g. the consensus judges on Berakhot) may narrow this, never promote past it."""
    index = json.loads((ROOT / "site/data/index.json").read_text())
    for row in index["tractates"]:
        for s in json.loads((ROOT / f"site/data/{row['tractate']}.json").read_text())["stories"]:
            # the one exception is a passage named in septimus_site_decisions.json `include`, which says who and when
            # ... or a story added by a `promote` rule, which carries `included_by` (Simon 2026-11-14)
            assert s["classification"] in ("YES", "HIGH_CONFIDENCE") or _included(s) or _promoted(s), s["id"]
            assert s["tier"] == "story" and not s["in_mishnah"], s["id"]


def test_unreviewed_stories_are_definite_in_every_run():
    """Lesson 45: the detector is not deterministic, so a shipped story from an unreviewed tractate must be
    YES/HIGH in EVERY listed run (unless named in the site decisions' `include`); a passage Gemini calls biblical and
    Claude calls not a story never ships; and every passage the judges call biblical is kept OUT of `stories`, in the
    file's `out_of_scope` list (Simon 2026-11-13, reversing 2026-11-10)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_site_data as b
    unreviewed = [t for t, src in b.SOURCES.items() if not src["reviewed"]]
    assert unreviewed
    for t in unreviewed:
        assert len(b.SOURCES[t]["runs"]) >= 2, t
        runs = [b.definite_cells(q) for q in b.SOURCES[t]["runs"]]
        biblical, drop = b.judge_cells(t)
        if t in b.EXISTING:       # a newer tractate may have no biblical passage at all
            assert biblical, t
        d = json.loads((ROOT / f"site/data/{t}.json").read_text())
        for s in d["stories"]:
            cells = {(g["ref"], g["i"]) for g in s["segments"]}
            assert all(cells & r for r in runs) or _included(s) or _promoted(s), s["id"]
            assert not cells & drop or _included(s), s["id"]
            assert not s["biblical"], s["id"]
            assert not cells & biblical or s["extended"], s["id"]   # only a display extension may reach a biblical cell
        for s in d["out_of_scope"]:
            assert s["biblical"] and s["out_of_scope_reason"].startswith("biblical (R-S1)"), s["id"]


def test_reviewed_stories_carry_jeffs_evidence():
    """The golden carries some detector calls Jeff never answered; only his yes (verdict or 2005 list) ships."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_site_data as b
    for t in (t for t, src in b.SOURCES.items() if src["reviewed"]):
        jeff = b.jeff_evidence_cells(t)
        stories = json.loads((ROOT / f"site/data/{t}.json").read_text())["stories"]
        unbacked = [s["id"] for s in stories if not {(g["ref"], g["i"]) for g in s["segments"]} & jeff]
        assert not unbacked, (t, unbacked)
    assert "ketubot-17a-3-3" not in {s["id"] for s in json.loads((ROOT / "site/data/ketubot.json").read_text())["stories"]}


def test_index_rows_carry_the_names_the_page_shows_and_every_tractate_is_in_the_table():
    """The home page draws from index.json alone (it never opens a tractate file), so each row must carry
    the English and Hebrew names, taken from the one table in scripts/tractates.py."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import tractates as T
    index = json.loads((ROOT / "site/data/index.json").read_text())["tractates"]
    assert index
    for r in index:
        assert r["name"] == T.english(r["tractate"]) and r["he"] == T.hebrew(r["tractate"]), r["tractate"]
        assert "-" not in r["tractate"], "a slug with a hyphen would break story ids (<slug>-<daf>-<a>-<b>)"
    assert [r["tractate"] for r in index[:5]] == ["ketubot", "kiddushin", "gittin", "yevamot", "berakhot"]


def test_site_app_has_no_hard_coded_tractate_list():
    app = (ROOT / "site/app.js").read_text()
    for name in ("Ketubot", "Berakhot", "כתובות"):
        assert name not in app, name
    # the home page must not open the tractate files
    home = app[app.index("function home()"):app.index("function tractate(")]
    assert 'getJSON("data/" +' not in home


def _site():
    index = json.loads((ROOT / "site/data/index.json").read_text())["tractates"]
    return {r["tractate"]: json.loads((ROOT / f"site/data/{r['tractate']}.json").read_text()) for r in index}


def test_biblical_stories_are_retained_out_of_scope_never_shipped():
    """Simon 2026-11-13: biblical stories leave the site's list (consistency with Jeff's R-S1), but are kept in each
    tractate file's `out_of_scope` list so a later filter can surface them. No story is in both."""
    site = _site()
    out = {s["id"] for d in site.values() for s in d["out_of_scope"]}
    shipped = {s["id"] for d in site.values() for s in d["stories"]}
    assert out and not out & shipped
    assert not any(s["biblical"] for d in site.values() for s in d["stories"])
    assert "berakhot-54b-0-0" in out   # the lepers Et and Hev: Jeff, 2026-11-12, out of scope (R-S1)
    assert len(out) == 102             # every story flagged biblical on 2026-11-10; a change here is a decision


def test_jeffs_not_and_borderline_passages_do_not_ship():
    """Jeff 2026-11-12, Simon 2026-11-13 (results/shas_run/septimus_site_decisions.json `remove`), by OVERLAP."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_site_data as b
    _, removals, _ = b.site_decisions()
    assert sum(len(v) for v in removals.values()) == 12
    site = _site()
    for t, entries in removals.items():
        for e in entries:
            assert e["decided_by"] and e["source"] and e["jeff"] in ("not", "borderline"), e
            for s in site[t]["stories"] + site[t]["out_of_scope"]:
                assert not {(g["ref"], g["i"]) for g in s["segments"]} & b.decision_cells(e), (s["id"], e["ref"])


def test_sanhedrin_52b_4_ships_as_a_regular_story():
    """Jeff 2026-11-12 'I would include it'; Simon 2026-11-13 'Include this', then 'just count it as a regular story'.
    LOW in both runs, so only the explicit per-passage decision puts it on the site; on the site it reads exactly like
    any story of an unreviewed tractate -- no `reviewed`, no provenance field. Who decided stays in the decisions file."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_site_data as b
    site = _site()
    s = {s["id"]: s for s in site["sanhedrin"]["stories"]}["sanhedrin-52b-4-4"]
    regular = next(x for x in site["sanhedrin"]["stories"] if x["id"] != s["id"] and "included_by" not in x)
    assert set(s) == set(regular) and "included_by" not in s
    assert not s["reviewed"] and s["tier"] == "story" and not site["sanhedrin"]["reviewed"]
    entries = b.site_decisions()[2]["sanhedrin"]
    assert len(entries) == 1 and "Jeff" in entries[0]["decided_by"] and "Simon" in entries[0]["decided_by"]
    included = [x["id"] for d in site.values() for x in d["stories"] if _included(x)]
    assert included == ["sanhedrin-52b-4-4"]


# Pipeline reasoning a card must never show as a summary. Short on purpose, and each marker is the vocabulary of a
# prompt that writes reasoning, not summaries: the twin-pass question names its two passages "PASSAGE A" / "PASSAGE B"
# and asks whether B is a "separate_incident" / "same_story" (story_detector_v14._twin_prompt). The structural check
# below catches the rest of that class (a twin reason that happens to avoid these words), so this list need not grow.
REASONING_MARKERS = re.compile(r"\bPassages? [AB]\b|\bseparate_incident\b|\bsame_story\b|\bnot_a_story\b")


def test_no_card_summary_is_pipeline_reasoning():
    """2026-11-13: 78 cards showed the twin judge's argument ("Passage B describes a distinct historical incident ...")
    because v14 copies that `reason` into a twin-pass story's one_sentence_summary. A card shows a reader-facing
    summary or none (never invented)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_site_data as b
    site = _site()
    leaks = [s["id"] for d in site.values() for s in d["stories"] if REASONING_MARKERS.search(s["summary"])]
    assert not leaks, leaks
    # structural: no shipped summary is a twin-pass `reason` from any run of its tractate
    for t, d in site.items():
        reasons = {s.get("reasoning") for q in b.SOURCES[t]["runs"] for p in json.loads((ROOT / q).read_text())["pages"]
                   for s in p.get("stories", []) if s.get("source") == "twin_pass"} - {None, ""}
        bad = [s["id"] for s in d["stories"] if s["summary"] in reasons]
        assert not bad, (t, bad)


def test_low_pool_promotions_carry_provenance_and_match_the_decision():
    """Simon 2026-11-14 ('I suggest we add them at this point'): the passages both Claude grader passes call `story`
    ship as a RULE recorded in septimus_site_decisions.json `promote`. Every one carries `included_by`, so the batch
    can be filtered or removed in one step; the count on the site is the record's count minus the drops the build
    names; none is in a reviewed tractate; no card shows the grader's reasoning; and nothing else carries the tag."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_site_data as b
    site = _site()
    rules = b.promotion_rules()
    assert [r["included_by"] for r, _ in rules] == ["low-pool-grader-2026-11-13"]
    r, ps = rules[0]
    assert r["decided_by"] == "Simon 2026-11-14" and r["judge_prompt_sha"] == "88e8fff62716"
    assert r["count"] == len(r["ids"]) == len(ps) == 80
    assert r["review_bar"]["completed"] is False          # the 54/60 bar was waived, and the record says so
    tagged = [s for d in site.values() for s in d["stories"] + d["out_of_scope"] if "included_by" in s]
    assert all(s["included_by"] == r["included_by"] for s in tagged)
    assert not any(site[t]["reviewed"] for t in {s["tractate"] for s in tagged})
    assert len(tagged) == 80, len(tagged)                 # 0 dropped on 2026-11-14; a drop is named on stderr
    by_cells = {frozenset(tuple(c) for c in p["cells"]): p for p in ps}
    for s in tagged:
        p = by_cells[frozenset((g["ref"], g["i"]) for g in s["segments"])]   # bounded by the unit's detector span
        reasons = {p["grader"][k]["reason"] for k in ("pass1", "pass2")}
        assert s["summary"] not in reasons and s["tier"] == "story" and not s["biblical"], s["id"]
