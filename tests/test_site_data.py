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
    # worker/feedback-worker.test.mjs: buildIssue on every story id, caps, and the request handler with fetch mocked
    r = subprocess.run(["node", "--test", str(ROOT / "worker/feedback-worker.test.mjs")], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout[-4000:] + r.stderr[-2000:]


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
    # the golden itself is never rewritten: `span` is the source range, and every shown passage contains it
    # (ids are permanent since 2026-11-14 and no longer encode the range -- scripts/story_ids.py)
    for s in by_id.values():
        shown = {(g["ref"], g["i"]) for g in s["segments"]}
        assert {(p["ref"], i) for p in s["span"] for i in range(p["start"], p["end"] + 1)} <= shown, s["id"]
        assert s["extended"] or len(shown) == sum(p["end"] - p["start"] + 1 for p in s["span"]), s["id"]


# Plan §2 (docs/technical/septimus-signup-plan.md): English words per tractate on the shipped list.
# A change here is a change to the list; update §2 in the same commit. These are the five tractates
# shipped before the Shas run, pinned so any change to them is noticed. A tractate added by the Shas
# run has no pin here (its total is checked against its own stories below); add one when it ships.
SITE_WORDS = {"ketubot": 23680, "kiddushin": 11861, "gittin": 25149, "yevamot": 18055, "berakhot": 24919}  # yevamot +4, berakhot +7: low-pool promotions; then -1 each: twin-pass removals (Simon 2026-11-14); ketubot -75: 106a back to 3-3 (b43deb2, Jeff segment numbering), id kept; second twin-pass pass: yevamot -1, berakhot -2


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
            assert not s["in_mishnah"], s["id"]


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
            assert not cells & biblical or s["extended"], s["id"]   # only a display extension may reach a biblical cell
        for s in d["out_of_scope"]:
            assert s["out_of_scope_reason"].startswith("biblical (R-S1)"), s["id"]


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
    assert all(s["out_of_scope_reason"].startswith("biblical (R-S1)") for d in site.values() for s in d["out_of_scope"])
    assert "berakhot-54b-0-0" in out   # the lepers Et and Hev: Jeff, 2026-11-12, out of scope (R-S1)
    assert len(out) == 102             # every story flagged biblical on 2026-11-10; a change here is a decision


def test_jeffs_not_and_borderline_passages_do_not_ship():
    """Jeff 2026-11-12, Simon 2026-11-13 (results/shas_run/septimus_site_decisions.json `remove`), by OVERLAP."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_site_data as b
    _, removals, _ = b.site_decisions()
    # 12 from Jeff's 2026-11-12 verdicts; 17 + 33 twin-pass cards Simon removed 2026-11-14 on a rules triage (no Jeff
    # verdict): the second pass's 32 SURE_REMOVE and one duplicate allusion (chagigah-13a-10-10)
    assert sum(len(v) for v in removals.values()) == 62
    site = _site()
    for t, entries in removals.items():
        for e in entries:
            assert e["decided_by"] and e["source"] and e["rule"], e
            if "jeff" in e:
                assert e["jeff"] in ("not", "borderline"), e
            else:
                assert "Simon 2026-11-14" in e["decided_by"] and e["reason"] and e["card"], e
            for s in site[t]["stories"] + site[t]["out_of_scope"]:
                if e.get("exact"):   # only the card with exactly this span; an overlapping card may stay
                    assert {(p["ref"], i) for p in s["span"] for i in range(p["start"], p["end"] + 1)} != \
                        b.decision_cells(e), (s["id"], e["ref"])
                    continue
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
    assert not s["reviewed"] and not site["sanhedrin"]["reviewed"]
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
        assert s["summary"] not in reasons, s["id"]


# --- the data contract (docs/technical/septimus-viewer-plan.md §3) -------------------------------------------------

SCHEMA = ROOT / "site/data/schema/story.schema.json"
REMOVED_FIELDS = ("tier", "biblical", "biblical_reason")   # Simon 2026-11-14: constant on every story, so dropped


def _validators():
    import jsonschema
    from referencing import Registry, Resource
    schema = json.loads(SCHEMA.read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    registry = Registry().with_resource(schema["$id"], Resource.from_contents(schema))
    tractate = jsonschema.Draft202012Validator(schema)
    index = jsonschema.Draft202012Validator({"$ref": schema["$id"] + "#/$defs/index"}, registry=registry)
    return tractate, index


def test_every_site_data_file_matches_the_schema():
    """Every tractate file and index.json validate against site/data/schema/story.schema.json; the schema forbids
    unknown story fields, so a removed field (tier, biblical, biblical_reason) cannot quietly come back."""
    tractate, index = _validators()
    rows = json.loads((ROOT / "site/data/index.json").read_text())
    errors = [e.message for e in index.iter_errors(rows)]
    for r in rows["tractates"]:
        d = json.loads((ROOT / f"site/data/{r['tractate']}.json").read_text())
        errors += [f"{r['tractate']} {list(e.absolute_path)[:3]}: {e.message[:200]}" for e in tractate.iter_errors(d)]
        assert d["tractate"] == r["tractate"] and r["story"] == len(d["stories"]) and r["out_of_scope"] == len(d["out_of_scope"])
        for s in d["stories"] + d["out_of_scope"]:
            assert s["tractate"] == r["tractate"] and s["id"].startswith(r["tractate"] + "-"), s["id"]
            assert not set(REMOVED_FIELDS) & set(s), s["id"]
    assert not errors, errors[:10]
    # the schema really is strict: a story carrying a removed field is rejected
    d = json.loads((ROOT / "site/data/ketubot.json").read_text())
    d["stories"][0]["tier"] = "story"
    assert not tractate.is_valid(d)


def test_viewer_never_shows_the_detector_grade():
    """Simon 2026-11-14: 'No reason for the septimus viewer to show this.' The grade stays in the data (feedback triage,
    analysis scripts), but app.js never reads it, nor `tier`, and the feedback payload does not carry it."""
    app = (ROOT / "site/app.js").read_text()
    for field in ("classification", "tier", "biblical", "HIGH_CONFIDENCE", "LOW_CONFIDENCE"):
        assert field not in app, field
    worker = (ROOT / "worker/feedback-worker.js").read_text()
    assert "classification" not in worker and "p.tier" not in worker


WRITTEN = ROOT / "results/shas_run/site_summaries_written.json"


def test_written_summaries_fill_only_empty_summaries():
    """results/shas_run/site_summaries_written.json is the last-resort summary source: used only where a story has no
    reader-facing detector/golden summary, never over an existing one. Checked by rebuilding each affected tractate
    with the file switched off and comparing story by story."""
    import pytest
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_site_data as b
    if not WRITTEN.exists():
        assert b.WRITTEN == {}
        pytest.skip("results/shas_run/site_summaries_written.json not written yet")
    written = {k: v.strip() for k, v in json.loads(WRITTEN.read_text())["summaries"].items()}
    assert b.WRITTEN == {k: v for k, v in written.items() if v}
    site = _site()
    shipped = {s["id"] for d in site.values() for s in d["stories"] + d["out_of_scope"]}
    assert set(written) <= shipped, sorted(set(written) - shipped)[:5]   # a summary keyed to no story is a stale id
    saved = b.WRITTEN
    try:
        b.WRITTEN = {}
        bare = {t: b.build(t) for t in {k.split("-")[0] for k in written}}
    finally:
        b.WRITTEN = saved
    for t, (stories, out) in bare.items():
        now = {s["id"]: s["summary"] for s in site[t]["stories"] + site[t]["out_of_scope"]}
        for s in stories + out:
            expected = s["summary"] or written.get(s["id"], "")
            assert now[s["id"]] == expected, s["id"]


def test_no_shipped_story_has_an_empty_summary_once_written_summaries_exist():
    import pytest
    if not WRITTEN.exists():
        pytest.skip("results/shas_run/site_summaries_written.json not written yet")
    empty = [s["id"] for d in _site().values() for s in d["stories"] if not s["summary"].strip()]
    assert not empty, empty


# ---- permanent story ids: site/data/story_ids.json (scripts/story_ids.py; viewer plan §3.1) -----------------------

def _ids():
    sys.path.insert(0, str(ROOT / "scripts"))
    import story_ids
    return story_ids


def test_story_id_registry_matches_the_site_data():
    """Every story (shipped or out of scope) holds an ACTIVE registry id recording its exact span; redirects.json is
    the registry's own derivation and validates against the schema; a redirect never points at a dead id."""
    import copy
    import jsonschema
    from referencing import Registry, Resource
    IDS = _ids()
    reg = IDS.load()
    seen = set()
    for t, d in _site().items():
        for s in d["stories"] + d["out_of_scope"]:
            e = reg["ids"].get(s["id"])
            assert e and e["status"] == "active" and e["tractate"] == t and e["span"] == s["span"], s["id"]
            assert s["id"] not in seen, s["id"]
            seen.add(s["id"])
        # rebuilding gives identical ids: matching today's stories against the committed registry changes nothing
        r, stories = copy.deepcopy(reg), copy.deepcopy(d["stories"] + d["out_of_scope"])
        rep = IDS.assign(r, t, stories)
        assert not (rep["minted"] or rep["retired"] or rep["redirected"] or rep["moved"] or rep["revived"]), (t, rep)
        assert r == reg and [s["id"] for s in stories] == [s["id"] for s in d["stories"] + d["out_of_scope"]], t
    red = json.loads((ROOT / "site/data/redirects.json").read_text())
    assert red == IDS.redirects(reg)
    assert all(v is None or reg["ids"][v]["status"] == "active" for v in red.values())
    schema = json.loads(SCHEMA.read_text())
    v = jsonschema.Draft202012Validator({"$ref": schema["$id"] + "#/$defs/redirects"},
                                        registry=Registry().with_resource(schema["$id"], Resource.from_contents(schema)))
    assert v.is_valid(red) and v.is_valid({"ketubot-2a-1-3": None, "ketubot-2a-4-5-v2": "ketubot-2a-1-3"})
    assert not v.is_valid({"not an id": None})


def _story(t, *pieces):
    """A synthetic story: pieces are (ref, start, end); `id` is its span id, as build() hands it to assign()."""
    IDS = _ids()
    segs = [{"ref": r, "i": i} for r, a, b in pieces for i in range(a, b + 1)]
    span = IDS.span_of(segs)
    return {"id": IDS.span_id(t, span), "span": span}


def test_story_id_registry_round_trip(tmp_path):
    """Boundary shift keeps the id; a split keeps one and mints one; a merge keeps one and redirects the other; a
    removal retires (never reused); a tie is refused; building twice changes no byte."""
    import copy
    import pytest
    IDS = _ids()
    P = "Ketubot 2a"
    reg = IDS.empty()
    st = lambda *p: _story("ketubot", *p)

    # first build mints today's span ids; a second identical build changes nothing, to the byte
    first = [st((P, 1, 3)), st((P, 5, 8)), st((P, 10, 12), ("Ketubot 2b", 0, 2))]
    IDS.assign(reg, "ketubot", first)
    assert [s["id"] for s in first] == ["ketubot-2a-1-3", "ketubot-2a-5-8", "ketubot-2a-10-12"]
    IDS.save(reg, tmp_path / "a.json")
    again = [st((P, 1, 3)), st((P, 5, 8)), st((P, 10, 12), ("Ketubot 2b", 0, 2))]
    rep = IDS.assign(reg, "ketubot", again)
    IDS.save(reg, tmp_path / "b.json")
    assert [s["id"] for s in again] == [s["id"] for s in first] and not rep["minted"] and not rep["moved"]
    assert (tmp_path / "a.json").read_bytes() == (tmp_path / "b.json").read_bytes()
    assert IDS.load(tmp_path / "a.json") == reg

    # boundary shift: 1-3 -> 1-4 keeps its id; the recorded span follows
    shifted = [st((P, 1, 4)), st((P, 5, 8)), st((P, 10, 12), ("Ketubot 2b", 0, 2))]
    rep = IDS.assign(reg, "ketubot", shifted)
    assert shifted[0]["id"] == "ketubot-2a-1-3" and rep["moved"] == {"ketubot-2a-1-3"} and not rep["minted"]
    assert reg["ids"]["ketubot-2a-1-3"]["span"] == [{"ref": P, "start": 1, "end": 4}]

    # split: 5-8 -> 5-7 + 8-8. The larger part keeps the id, the other mints one
    split = [st((P, 1, 4)), st((P, 5, 7)), st((P, 8, 8)), st((P, 10, 12), ("Ketubot 2b", 0, 2))]
    rep = IDS.assign(reg, "ketubot", split)
    assert [s["id"] for s in split][1:3] == ["ketubot-2a-5-8", "ketubot-2a-8-8"] and rep["minted"] == ["ketubot-2a-8-8"]

    # merge: 1-4 + 5-7 -> 1-7. It keeps the id it overlaps most; the other redirects to it
    merged = [st((P, 1, 7)), st((P, 8, 8)), st((P, 10, 12), ("Ketubot 2b", 0, 2))]
    rep = IDS.assign(reg, "ketubot", merged)
    assert merged[0]["id"] == "ketubot-2a-1-3" and rep["redirected"] == {"ketubot-2a-5-8": "ketubot-2a-1-3"}
    assert IDS.redirects(reg) == {"ketubot-2a-5-8": "ketubot-2a-1-3"}

    # a tie is a judgement for a person: 8-8 and the cross-page story merged into one span overlapping... equally
    tie_reg = copy.deepcopy(reg)
    tie_reg["ids"]["ketubot-2a-8-8"]["span"] = [{"ref": P, "start": 8, "end": 9}]
    tie = [st((P, 1, 7)), st((P, 8, 11))]   # overlaps 8-9 by 2 and 10-12 by 2
    with pytest.raises(IDS.IdConflict, match="ambiguous"):
        IDS.assign(tie_reg, "ketubot", tie)

    # removal: the cross-page story disappears -> retired, and redirects say so (null)
    removed = [st((P, 1, 7)), st((P, 8, 8))]
    rep = IDS.assign(reg, "ketubot", removed)
    assert rep["retired"] == ["ketubot-2a-10-12"] and reg["ids"]["ketubot-2a-10-12"]["status"] == "retired"
    assert IDS.redirects(reg)["ketubot-2a-10-12"] is None
    # ... and never reused for another story: a new passage born with the same span STRING (the retired id's span
    # had moved on) gets a -v2, not the retired id
    reg["ids"]["ketubot-2a-10-12"]["span"] = [{"ref": P, "start": 20, "end": 22}]
    fresh = [st((P, 1, 7)), st((P, 8, 8)), st((P, 10, 12))]
    rep = IDS.assign(reg, "ketubot", fresh)
    assert fresh[2]["id"] == "ketubot-2a-10-12-v2" and reg["ids"]["ketubot-2a-10-12"]["status"] == "retired"
    # the same passage coming back revives its own id (a reader's checkmark comes back with it)
    back = [st((P, 1, 7)), st((P, 8, 8)), st((P, 10, 12)), st((P, 20, 22))]
    rep = IDS.assign(reg, "ketubot", back)
    assert back[3]["id"] == "ketubot-2a-10-12" and rep["revived"] == ["ketubot-2a-10-12"]
    assert "ketubot-2a-10-12" not in IDS.redirects(reg)

    # a chain is followed: a redirect onto an id that later retires resolves to null
    reg["ids"]["ketubot-2a-1-3"]["status"] = "retired"
    assert IDS.redirects(reg)["ketubot-2a-5-8"] is None

    # another tractate's entries are never touched by this tractate's build
    other = IDS.empty()
    IDS.assign(other, "gittin", [_story("gittin", ("Gittin 2a", 0, 1))])
    snap = copy.deepcopy(other["ids"])
    IDS.assign(other, "ketubot", [st((P, 0, 1))])
    assert {k: v for k, v in other["ids"].items() if v["tractate"] == "gittin"} == snap


def test_viewer_resolves_old_ids_through_redirects():
    """site/app.js follows redirects.json for a story link and migrates a merged id's read-checkmark."""
    js = (ROOT / "site/app.js").read_text()
    assert 'getJSON("data/redirects.json")' in js and "location.replace(\"#/s/\" + to)" in js
    assert "function migrateRead()" in js and "!(id in REDIRECTS)" in js


# ---- `merge`, `keep` and summary `overrides` (Simon 2026-11-14, second twin-pass triage pass) ----------------------

def _decisions():
    return json.loads((ROOT / "results/shas_run/septimus_site_decisions.json").read_text())


def test_merge_decisions_join_cards_and_redirect_the_absorbed_ids():
    """A `merge` group ships as ONE card under its `keep` id, over exactly the members' segments (contiguous); every
    other member's id redirects to it; its summary is the one written for `keep` (a member's own covers only its part)."""
    site, reg = _site(), _ids().load()
    red = json.loads((ROOT / "site/data/redirects.json").read_text())
    written = json.loads(WRITTEN.read_text())["summaries"]
    groups = _decisions()["merge"]["groups"]
    assert len(groups) == 3
    for g in groups:
        assert g["decided_by"] and g["reason"] and g["source"] and g["keep"] in [m["card"] for m in g["members"]], g
        cells = {(m["ref"], i) for m in g["members"] for i in range(m["start_segment"], m["end_segment"] + 1)}
        [s] = [s for s in site[g["tractate"]]["stories"] if {(x["ref"], x["i"]) for x in s["segments"]} & cells]
        assert s["id"] == g["keep"] and s["extended"] is None
        assert {(x["ref"], x["i"]) for x in s["segments"]} == cells
        assert reg["ids"][g["keep"]]["status"] == "active" and reg["ids"][g["keep"]]["span"] == s["span"]
        assert s["summary"] == written[g["keep"]].strip()
        for m in g["members"]:
            if m["card"] != g["keep"]:
                assert reg["ids"][m["card"]]["status"] == "redirect" and red[m["card"]] == g["keep"], m["card"]
                assert m["card"] not in written   # no summary keyed to a story that does not ship


def test_keep_decisions_ship_and_a_remove_that_would_undo_one_is_refused(tmp_path, monkeypatch):
    """Simon's `keep` list is read for one thing: a `remove` overlapping a kept card stops the build, by name."""
    import pytest
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_site_data as b
    site, d = _site(), _decisions()
    keep = d["keep"]["passages"]
    assert {k["card"] for k in keep} == {"pesachim-49a-15-15", "ketubot-86a-4-4", "rosh_hashanah-18a-7-7",
                                         "yevamot-105a-13-13"}
    for k in keep:
        assert k["decided_by"] and k["simon"] and k["card"] in {s["id"] for s in site[k["tractate"]]["stories"]}, k
    bad = dict(d, remove=dict(d["remove"], passages=d["remove"]["passages"] + [
        {k: keep[0][k] for k in ("tractate", "ref", "start_segment", "end_segment")}]))
    f = tmp_path / "decisions.json"
    f.write_text(json.dumps(bad))
    monkeypatch.setattr(b, "SITE_DECISIONS", str(f))
    with pytest.raises(SystemExit, match=keep[0]["card"]):
        b.site_decisions()


def test_summary_overrides_replace_only_the_named_cards():
    """site_summaries_written.json `overrides` replace a summary that is wrong as shown (Eruvin 53b:24 said it twice)."""
    over = json.loads(WRITTEN.read_text()).get("overrides", {})
    shown = {s["id"]: s["summary"] for d in _site().values() for s in d["stories"] + d["out_of_scope"]}
    assert over and set(over) <= set(shown)
    assert all(shown[k] == v.strip() for k, v in over.items())
