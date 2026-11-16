"""scripts/review_site_boundaries.py -- the full boundary review (plan docs/history/2026-11-15-PLAN-full-boundary-review.md).

Display only, and nothing done silently: every decision `apply` will not carry out is refused by name. Each test builds
a tiny fake site (one tractate, 30 segments on one page) in tmp_path, so nothing here reads or writes the real site."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import review_site_boundaries as R  # noqa: E402

REF = "Tt 2a"
FLAT = [(REF, i, f"he{i}", f"en{i}") for i in range(30)]


def card(sid, lo, hi, shown=None):
    a, z = shown or (lo, hi)
    return {"id": sid, "tractate": "tt", "ref": REF, "span": [{"ref": REF, "start": lo, "end": hi}],
            "segments": [{"ref": REF, "i": i, "he": f"he{i}", "en": f"en{i}"} for i in range(a, z + 1)],
            "extended": None}


@pytest.fixture
def site(tmp_path, monkeypatch):
    """A: 2-4. B: 5-6 (next to A). C: 8-12 shown 9-12 (start_trim 1). M: 18-21 + 23-24 merged (M absorbs N).
    F: 26-27, two segments after the merged card."""
    data = tmp_path / "data"
    (data / "notes").mkdir(parents=True)
    cards = [card("tt-a", 2, 4), card("tt-b", 5, 6), card("tt-c", 8, 12, shown=(9, 12)),
             dict(card("tt-m", 18, 24), span=[{"ref": REF, "start": 18, "end": 24}]), card("tt-f", 26, 27)]
    (data / "index.json").write_text(json.dumps({"tractates": [{"tractate": "tt"}]}))
    (data / "tt.json").write_text(json.dumps({"stories": cards}))
    (data / "notes" / "tt.json").write_text(json.dumps({"tractate": "tt", "notes": {
        c["id"]: {"note": "old", "why": "", "people": [], "terms": [], "approved": True} for c in cards}}))
    ext = data / "boundary_extensions.json"
    ext.write_text(json.dumps({"tt-c": {"start_back": 0, "end_forward": 0, "start_trim": 1, "end_trim": 0, "reason": "x"}}))
    dec = tmp_path / "decisions.json"
    dec.write_text(json.dumps({"merge": {"groups": [{"tractate": "tt", "keep": "tt-m", "members": [
        {"ref": REF, "start_segment": 18, "end_segment": 21, "card": "tt-m"},
        {"ref": REF, "start_segment": 23, "end_segment": 24, "card": "tt-n"}]}]}}))
    flags = tmp_path / "flags.json"
    flags.write_text(json.dumps({"tt-b": "cut off at the end"}))
    for name, val in (("DATA", data), ("EXT", ext), ("DECISIONS", dec), ("WORK", tmp_path / "work"), ("FLAGS", flags)):
        monkeypatch.setattr(R, name, val)
    monkeypatch.setattr(R, "_FLAT", {"tt": (FLAT, {(r, i): k for k, (r, i, _, _) in enumerate(FLAT)})})
    return tmp_path


def decide(tmp_path, run, decisions, after=()):
    d = tmp_path / "work" / run
    d.mkdir(parents=True, exist_ok=True)
    (d / "manifest.json").write_text(json.dumps({"run": run, "after": list(after)}))
    (d / "decisions.json").write_text(json.dumps({k: {"tractate": "tt", "reason": "r", **v} for k, v in decisions.items()}))


def ext(tmp_path):
    return json.loads((tmp_path / "data" / "boundary_extensions.json").read_text())


def refused_ids(refused):
    return {i for i, _ in refused}


# --------------------------------------------------------------------------------------------------------- export

def test_export_takes_every_site_story_once_minus_the_skip_list_and_names_what_it_skipped(site):
    decide(site, "bfix0", {"tt-a": {"action": "keep"}})
    files, skipped = R.export("r1", after=("bfix0",))
    assert sorted(f["id"] for f in files) == ["tt-b", "tt-c", "tt-f"]
    assert skipped == {"decided in bfix0": ["tt-a"], "part of a merge (no display change is possible on it)": ["tt-m"]}
    keys = json.loads((site / "work" / "r1" / "keys" / "000.json").read_text())
    assert [k["id"] for k in keys] == ["tt-b", "tt-c", "tt-f"]
    with pytest.raises(SystemExit):
        R.export("r1")   # a run name is exported once


def test_flags_narrow_the_export_and_the_concern_line_appears_only_when_there_is_one(site):
    files, _ = R.export("r1")
    by = {f["id"]: f["text"] for f in files}
    assert "Drafter's concern: cut off at the end" in by["tt-b"]
    assert "Drafter's concern" not in by["tt-a"]
    files, _ = R.export("r2", flags_file=str(site / "flags.json"))
    assert [f["id"] for f in files] == ["tt-b"]


def test_the_story_file_window_comes_from_the_source_span_and_states_the_limits(site):
    files, _ = R.export("r1")
    c = next(f for f in files if f["id"] == "tt-c")
    # source 8-12, shown 9-12: the file reaches 8-2-EXTRA .. 12+6+EXTRA, and states 6 .. 18 as the limits
    assert min(c["numbers"].values()) == 8 - R.MAX_BACK - R.EXTRA and max(c["numbers"].values()) == 12 + R.MAX_FWD + R.EXTRA
    num = {k: n for n, k in c["numbers"].items()}
    assert f"You may start no earlier than [{num[6]}] and end no later than [{num[18]}]." in c["text"]
    assert f"[{num[8]}] BEFORE" in c["text"] and f"[{num[9]}] STORY" in c["text"]   # trimmed segment shows as BEFORE
    assert "(site story tt-b)" in c["text"]


def test_the_limits_are_imported_from_the_site_build_not_repeated():
    import build_site_data as B
    assert (R.MAX_BACK, R.MAX_FWD, R.MERGE_MAX_GAP) == (B.MAX_BACK, B.MAX_FWD, B.MERGE_MAX_GAP)


def test_import_rejects_an_adjust_beyond_the_limits_line(site):
    files, _ = R.export("r1")
    num = {f["id"]: {k: n for n, k in f["numbers"].items()} for f in files}
    n = {f["id"]: k for k, f in enumerate(files, start=1)}
    answers = {f"{n['tt-c']:02d}": {"code": R.code("r1", "tt-c"), "action": "adjust",
                                    "first": num["tt-c"][5], "last": num["tt-c"][12]},          # 3 back: too far
               f"{n['tt-f']:02d}": {"code": R.code("r1", "tt-f"), "action": "adjust",
                                    "first": num["tt-f"][26], "last": num["tt-f"][26]},
               f"{n['tt-a']:02d}": {"code": "WRONG", "action": "keep"}}
    (site / "work" / "r1" / "answers" / "000.json").write_text(json.dumps(answers))
    out, bad = R.import_("r1")
    assert out["tt-f"] == {"action": "adjust", "first_pos": 26, "last_pos": 26, "reason": "", "tractate": "tt"}
    assert {b[0] for b in bad} == {"tt-a", "tt-b", "tt-c"}


# ---------------------------------------------------------------------------------------------------------- apply

def test_an_adjust_back_to_the_original_span_deletes_the_entry(site):
    decide(site, "r1", {"tt-c": {"action": "adjust", "first_pos": 8, "last_pos": 12}})
    R.apply("r1")
    assert "tt-c" not in ext(site)
    rec = json.loads((site / "work" / "r1" / "applied.json").read_text())["changes"]["tt-c"]
    assert rec["kind"] == "delete" and rec["before"]["start_trim"] == 1


def test_a_trim_is_written_and_every_changed_note_is_marked_for_redraft(site):
    decide(site, "r1", {"tt-f": {"action": "adjust", "first_pos": 26, "last_pos": 26}, "tt-a": {"action": "keep"}})
    R.apply("r1")
    assert ext(site)["tt-f"]["end_trim"] == 1 and "tt-a" not in ext(site)
    notes = json.loads((site / "data" / "notes" / "tt.json").read_text())["notes"]
    assert notes["tt-f"]["drafted"] == "boundary-changed" and notes["tt-f"]["approved"] is False
    assert notes["tt-a"]["approved"] is True and "drafted" not in notes["tt-a"]
    assert (site / "work" / "r1" / "changed.txt").read_text().split() == ["tt-f"]


def test_an_adjust_on_a_merged_card_is_refused_by_name(site):
    decide(site, "r1", {"tt-m": {"action": "adjust", "first_pos": 19, "last_pos": 24}})
    changes, refused = R.plan("r1")
    assert not changes and "part of a merge" in dict(refused)["tt-m"]


def test_a_merge_with_a_trimmed_card_is_refused_unless_the_second_reader_upheld_it(site):
    decide(site, "r1", {"tt-b": {"action": "merge", "merge_with": "tt-c"}})
    changes, refused = R.plan("r1")
    assert not changes and "display trim" in dict(refused)["tt-b"]
    changes, refused = R.plan("r1", confirmed={"tt-b"})
    assert [c["kind"] for c in changes] == ["merge"] and changes[0]["dropped_ext"]["tt-c"]["start_trim"] == 1


def test_a_merge_the_other_card_disagreed_with_is_refused(site):
    decide(site, "r1", {"tt-a": {"action": "merge", "merge_with": "tt-b"}, "tt-b": {"action": "keep"}})
    changes, refused = R.plan("r1")
    assert not changes and "DISAGREEMENT" in dict(refused)["tt-a"]


def test_a_merge_agreed_from_both_sides_is_one_group_and_redirects_nothing_twice(site):
    decide(site, "r1", {"tt-a": {"action": "merge", "merge_with": "tt-b"}, "tt-b": {"action": "merge", "merge_with": "tt-a"}})
    R.apply("r1")
    groups = json.loads((site / "decisions.json").read_text())["merge"]["groups"]
    assert len(groups) == 2 and groups[-1]["keep"] == "tt-a" and [m["card"] for m in groups[-1]["members"]] == ["tt-a", "tt-b"]


def test_a_merge_joining_a_third_card_to_an_existing_pair_is_refused(site):
    decide(site, "r1", {"tt-f": {"action": "merge", "merge_with": "tt-m"}})
    changes, refused = R.plan("r1")
    assert not changes and "third card" in dict(refused)["tt-f"]


def test_overlapping_ranges_are_refused_against_every_card_in_the_tractate(site):
    # A reaching into B's first segment; F reaching back into the merged card M (decided by nobody this run)
    decide(site, "r1", {"tt-a": {"action": "adjust", "first_pos": 2, "last_pos": 5},
                        "tt-f": {"action": "adjust", "first_pos": 24, "last_pos": 27}})
    changes, refused = R.plan("r1")
    assert not changes
    assert "tt-b" in dict(refused)["tt-a"] and "tt-m" in dict(refused)["tt-f"]


def test_held_ids_are_left_out(site):
    decide(site, "r1", {"tt-f": {"action": "adjust", "first_pos": 26, "last_pos": 26}})
    changes, refused = R.plan("r1", hold={"tt-f"})
    assert not changes and refused_ids(refused) == {"tt-f"}


def test_dry_run_writes_nothing(site):
    decide(site, "r1", {"tt-f": {"action": "adjust", "first_pos": 26, "last_pos": 26}})
    before = ext(site)
    changes, _ = R.apply("r1", dry_run=True)
    assert changes and ext(site) == before and not (site / "work" / "r1" / "applied.json").exists()


def test_a_second_apply_changes_nothing_and_does_not_overwrite_applied_json(site):
    decide(site, "r1", {"tt-f": {"action": "adjust", "first_pos": 26, "last_pos": 26}})
    R.apply("r1")
    applied, e = (site / "work" / "r1" / "applied.json").read_text(), ext(site)
    groups = (site / "decisions.json").read_text()
    with pytest.raises(SystemExit):
        R.apply("r1")
    assert (site / "work" / "r1" / "applied.json").read_text() == applied and ext(site) == e
    assert (site / "decisions.json").read_text() == groups


# ------------------------------------------------------------------------------------------------------ calibrate

def targets(tmp_path, stories):
    f = tmp_path / "targets.json"
    f.write_text(json.dumps({"tractate": "Tt", "targets": [
        {"review_key": k, "direction": d, "located_on": REF, "segment": seg}
        for k, (a, z) in stories.items() for d, seg in (("start", a), ("end", z))]}))
    return str(f)


def test_calibrate_counts_starts_ends_left_alone_benefit_and_merges(site, monkeypatch):
    monkeypatch.setattr(R, "slug_of", lambda name: name.lower())
    # J1 = A exactly (kept); J2 = F's first segment only (F trims its 2nd: benefit 1);
    # J3 = 9-11 inside C (C is cut to 9-10: his end lost); J4 = B 5-6 exactly, merged into A: two Jeff stories joined
    tf = targets(site, {"j1": (2, 4), "j2": (26, 26), "j3": (9, 11), "j4": (5, 6)})
    decide(site, "r1", {"tt-a": {"action": "merge", "merge_with": "tt-b"},
                        "tt-f": {"action": "adjust", "first_pos": 26, "last_pos": 26},
                        "tt-c": {"action": "adjust", "first_pos": 9, "last_pos": 10}})
    report, cut_ends, cases = R.calibrate("r1", [tf])
    r = report["tt"]
    assert r["measurable"] == 3                      # j4 sits in B, which this run did not decide
    assert r["A_starts_kept"] == 3 and r["B_ends_kept"] == 2
    assert [c["key"] for c in cut_ends] == ["tt:j3"] and r["B_cut_unsorted"] == 1
    assert r["C_exact"] == 1 and r["C_left_alone"] == 0     # A merged, so lengthened past his end
    assert r["D_extra"] == 1 + 1 and r["D_removed"] == 1 + 1     # F's 27 and C's 12 removed
    assert r["E_merge_of_two_jeff_stories"] == 1 and cases["E_merge_of_two"][0]["jeff"] == ["j1", "j4"]
    sf = site / "sorted.json"
    sf.write_text(json.dumps({"tt:j3": "lost"}))
    report, _, _ = R.calibrate("r1", [tf], str(sf))
    assert report["tt"]["narrative_lost"] == 1 and report["tt"]["narrative_lost_pct"] == round(100 / 3, 1)


# --------------------------------------------------------------------------------------------------- second reader

def test_second_reader_reads_every_merge_and_big_trim_and_its_rejections_become_the_hold_list(site):
    decide(site, "r1", {"tt-f": {"action": "adjust", "first_pos": 26, "last_pos": 26},       # removes half: read
                        "tt-a": {"action": "merge", "merge_with": "tt-b"},                    # merge: read
                        "tt-b": {"action": "keep"},                                           # disagreement
                        "tt-c": {"action": "keep"}})
    why = R.second_export("r1", sample=0, keeps=0)
    assert why == {"tt-f": "trim removes half or more",
                   "tt-a": "merge refused: merge with tt-b: DISAGREEMENT, that card's own review said keep "
                           "(second reader decides)"}
    keys = json.loads((site / "work" / "r1" / "second" / "keys" / "000.json").read_text())
    text = (site / "work" / "r1" / "second" / "batches" / "000" / "01.txt").read_text()
    assert "KEPT" in text and keys[0]["id"] == "tt-a"
    ans = {"01": {"code": R.second_code("r1", "tt-a"), "verdict": "agree"},
           "02": {"code": R.second_code("r1", "tt-f"), "verdict": "disagree"}}
    (site / "work" / "r1" / "second" / "answers" / "000.json").write_text(json.dumps(ans))
    R.second_import("r1")
    d = site / "work" / "r1" / "second"
    assert (d / "hold.txt").read_text().split() == ["tt-f"] and (d / "confirmed.txt").read_text().split() == ["tt-a"]
    changes, _ = R.plan("r1", hold={"tt-f"}, confirmed={"tt-a"})
    assert [(c["kind"], c["ids"]) for c in changes] == [("merge", ["tt-a", "tt-b"])]
