"""Background notes for the Septimus site (work/2026-11-15-shas-background-notes.md).

The merge must never let unreviewed text replace a note Simon approved, never ship a held
draft as approved, and never count a missing or invalid subagent answer as a note."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_site_notes as B  # noqa: E402
import draft_site_notes as D  # noqa: E402

STORY = {"id": "t-2a-1-1", "ref": "T 2a", "tier": "story",
         "segments": [{"ref": "T 2a", "i": 1, "he": "", "en": "<b>Rav Huna</b> went to the market."}]}
OLD = {"note": "Rav Huna goes to the market.", "why": "", "people": [], "terms": [], "approved": True}


def draft(**kw):
    return {"id": STORY["id"], "note": "A new draft.", "why": "The Gemara has just ruled on markets.",
            "people": [{"name": "Rav Huna", "about": "a sage"}], "terms": [], "flag": "", **kw}


def run(prev, rec, held):
    notes, ev = B.merge([STORY], prev, {STORY["id"]: rec} if rec else {}, held)
    return notes.get(STORY["id"]), ev


def test_an_approved_note_keeps_its_text_and_gains_only_the_why():
    n, _ = run({STORY["id"]: OLD}, draft(), {})
    assert n["note"] == OLD["note"] and n["approved"] is True
    assert n["why"] == "The Gemara has just ruled on markets."


def test_an_unapproved_unheld_note_keeps_its_text_and_is_not_approved_by_the_merge():
    n, _ = run({STORY["id"]: {**OLD, "approved": False}}, draft(), {})
    assert n["note"] == OLD["note"] and n["approved"] is False


def test_a_held_note_is_redrafted_whole_and_its_hold_cleared():
    held = {STORY["id"]: "October: cut off"}
    n, ev = run({STORY["id"]: {**OLD, "approved": False}}, draft(), held)
    assert n["note"] == "A new draft." and n["approved"] is False
    assert STORY["id"] not in held and ev["drafted"] == 1


def test_a_flagged_draft_is_held():
    held = {}
    n, _ = run({}, draft(flag="Not a story: a legal ruling only."), held)
    assert n["approved"] is False and held[STORY["id"]].startswith("Not a story")


def test_a_person_not_in_the_story_holds_the_draft():
    held = {}
    run({}, draft(people=[{"name": "Rabbi Akiva", "about": "x"}]), held)
    assert "Rabbi Akiva" in held[STORY["id"]]


def test_a_bad_why_on_an_approved_note_is_dropped_and_the_note_still_ships():
    held = {}
    n, _ = run({STORY["id"]: OLD}, draft(why="x" * 400), held)
    assert n["why"] == "" and n["approved"] is True and held[STORY["id"]].startswith("why dropped")


def test_hebrew_in_a_draft_holds_it():
    held = {}
    run({}, draft(note="He said שלום."), held)
    assert "Hebrew" in held[STORY["id"]]


def test_a_story_with_no_note_and_no_draft_is_reported_missing():
    n, ev = run({}, None, {})
    assert n is None and ev["missing"] == [STORY["id"]]


def test_an_invalid_subagent_answer_is_never_a_note():
    assert D.validate("not json")[0] is None
    assert D.validate({"note": "", "why": ""})[0] is None
    assert D.validate({"note": "ok", "people": "Rav Huna"})[0] is None
    assert D.validate(json.dumps({"note": "ok", "why": "", "people": [], "terms": [], "flag": ""}))[0]


def test_the_why_renders_inside_the_background_box():
    js = (ROOT / "site/app.js").read_text()
    box = js[js.index("function noteMarkup"):js.index("function feedbackMarkup")]
    assert "n.why" in box and box.index("n.why") < box.index("Written with the help of AI")


def test_no_held_note_is_approved_unless_simon_approved_it_in_october():
    held = json.loads((ROOT / "results/site_notes/held.json").read_text()) if (ROOT / "results/site_notes/held.json").exists() else {}
    approved_held = []
    for f in (ROOT / "site/data/notes").glob("*.json"):
        approved_held += [i for i, n in json.loads(f.read_text())["notes"].items()
                          if n.get("approved") and i in held and not held[i].startswith("why dropped")]
    assert not approved_held, approved_held[:5]
