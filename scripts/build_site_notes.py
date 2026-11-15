#!/usr/bin/env python3
"""Merge drafted background notes into site/data/notes/<tractate>.json (Septimus viewer).

    python3 scripts/build_site_notes.py <parts_dir> [<parts_dir> ...]   # merge + check
    python3 scripts/build_site_notes.py --report                        # coverage only, writes nothing
    python3 scripts/approve_notes.py --all --unflagged                  # approve every note not held

Parts are `<tractate>.<anything>.json`, lists of {id, note, why, people, terms, flag}
(scripts/draft_site_notes.py writes them). Every tractate in site/data/index.json is read.

Merge rule, per story (work/2026-11-15-shas-background-notes.md):
  * a note that is APPROVED, or that has no hold on it, KEEPS its text; a new draft only adds
    its `why` (Simon reviewed these in October -- the text he read is the text that ships);
  * a note that is HELD (the October drafter flagged it) or missing takes the new draft whole.
A note keeps `approved` only while its `note` text is unchanged.

Holds live in results/site_notes/held.json, {id: reason}: never on the site. A note is held
when its drafter raised a flag or it fails a check below; approve_notes.py --unflagged skips
held notes. On first run the file is seeded from the October flags list. The flags list,
docs/findings/2026-10-12-septimus-note-flags.md, is regenerated from it.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "site" / "data"
OUT = DATA / "notes"
HELD = ROOT / "results" / "site_notes" / "held.json"
PASSAGE_FLAGS = ROOT / "results" / "site_notes" / "passage_flags.json"
FLAGS_DOC = ROOT / "docs" / "findings" / "2026-10-12-septimus-note-flags.md"
TAG = re.compile(r"<[^>]+>")
HEBREW = re.compile(r"[֐-׿]")
LIMITS = {"note": 800, "why": 300}


def fold(s):
    """Lowercase, no diacritics/apostrophes: 'Naḥman' must match 'Nahman'."""
    s = unicodedata.normalize("NFD", str(s).lower())
    return re.sub(r"[^a-z ]", "", "".join(c for c in s if not unicodedata.combining(c)))


def clean(s, n):
    return TAG.sub("", str(s or "")).strip()[:n]


def norm(rec):
    return {
        "note": clean(rec.get("note"), LIMITS["note"]),
        "why": clean(rec.get("why"), LIMITS["why"]),
        "people": [{"name": clean(p.get("name"), 80), "about": clean(p.get("about"), 160)}
                   for p in (rec.get("people") or [])[:5] if clean(p.get("name"), 80)],
        "terms": [{"term": clean(t.get("term"), 80), "meaning": clean(t.get("meaning"), 300)}
                  for t in (rec.get("terms") or [])[:4] if clean(t.get("term"), 80) and clean(t.get("meaning"), 300)],
    }


def site_tractates():
    return [t["tractate"] for t in json.loads((DATA / "index.json").read_text())["tractates"]]


def problems_with(rec, story):
    """Reasons a drafted note must not ship unreviewed. Checked on the RAW draft, before truncation."""
    out = []
    for f, n in LIMITS.items():
        if len(TAG.sub("", str(rec.get(f) or "")).strip()) > n:
            out.append(f"{f} longer than {n} characters")
        if HEBREW.search(str(rec.get(f) or "")):
            out.append(f"{f} contains Hebrew")
    english = fold(TAG.sub(" ", " ".join(g["en"] for g in story["segments"])))
    for p in rec.get("people") or []:   # a named person must actually be in the story
        key = re.sub(r"^(rabbi|rav|rabbah|rabba|reish|rabban|r)\s+", "", fold(p.get("name", ""))).split()
        if key and key[0] not in english:
            out.append(f"person '{clean(p.get('name'), 80)}' not found in the English")
    return out


def seed_held():
    """The October flags list, as {id: reason}, for notes Simon has not approved."""
    held = {}
    if FLAGS_DOC.exists():
        for m in re.finditer(r"\(`([^`]+)`, [^)]*\): (.*)", FLAGS_DOC.read_text()):
            held[m.group(1)] = m.group(2).strip()
    approved = set()
    for f in OUT.glob("*.json"):
        approved |= {i for i, n in json.loads(f.read_text())["notes"].items() if n.get("approved")}
    return {i: r for i, r in held.items() if i not in approved}


def load_parts(dirs):
    by_id = {}
    for d in dirs:
        for f in sorted(Path(d).glob("*.json")):
            for rec in json.loads(f.read_text()):
                by_id[rec["id"]] = rec     # a later part wins
    return by_id


def merge(stories, prev, parts, held, passage_flags):
    """(notes, events) for one tractate. Mutates `held` and `passage_flags`.

    A drafter's flag is about the PASSAGE (not a story, cut off, garbled), so it is always recorded in
    `passage_flags` for the team to check the story's boundaries. It also holds the note back from
    approval unless Simon already approved that note's text (Simon 2026-11-15)."""
    notes, ev = {}, {"kept": 0, "why_added": 0, "drafted": 0, "held": 0, "missing": []}
    for s in stories:
        sid, old, rec = s["id"], prev.get(s["id"]), parts.get(s["id"])
        keep_text = old is not None and (old.get("approved") or sid not in held)
        if rec is None:
            if old is not None:
                notes[sid] = {**old, "why": old.get("why", "")}
                ev["kept"] += 1
            else:
                ev["missing"].append(sid)
            continue
        flag = clean(rec.get("flag"), 300)
        if flag:
            passage_flags[sid] = flag
        else:
            passage_flags.pop(sid, None)    # the latest reader's view of the passage
        if keep_text:
            n = {**old, "why": clean(rec.get("why"), LIMITS["why"])}
            if str(held.get(sid, "")).startswith("why dropped"):
                held.pop(sid)     # a new `why` replaces the one that failed
            bad =problems_with({"why": rec.get("why")}, s)
            if bad:      # the reviewed text still ships; a `why` that fails a check does not
                n["why"] = ""
                bad = ["why dropped: " + "; ".join(bad)]
            if flag and not old.get("approved"):    # never reviewed, and a fresh reader doubts the passage
                bad.insert(0, flag)
            ev["why_added"] += 1
        else:
            n = norm(rec)
            bad = problems_with(rec, s)
            if flag:
                bad.insert(0, flag)
            held.pop(sid, None)    # a fresh draft replaces the old hold; its own problems set the new one
            ev["drafted"] += 1
        if bad:
            held[sid] = "; ".join(bad)
            ev["held"] += 1
        n["approved"] = bool(old and old.get("approved")) and old.get("note") == n["note"]
        notes[sid] = n
    return notes, ev


def write_flags_doc(held, passage_flags, ref_of):
    lines = ["# Septimus viewer: notes held back", "",
             "Notes that are not approved automatically: the drafter thought the passage is not a story, is cut off "
             "or garbled, or the note failed a check (length, Hebrew, a person not in the story). For the project team; "
             "never shown on the site. Indicated, not measured. Generated by `scripts/build_site_notes.py` from "
             "`results/site_notes/held.json`; edit that file, not this one.", ""]
    lines += [f"- **{ref_of.get(i, '?')}** (`{i}`): {r}"
              for i, r in sorted(held.items())] or ["(none)"]
    lines += ["", "## Passages to check", "",
              "Every passage whose latest note-drafter flagged it (not a story, cut off, two passages joined, garbled), "
              "approved note or not. A question about the story's boundaries, for the team; from "
              "`results/site_notes/passage_flags.json`.", ""]
    lines += [f"- **{ref_of.get(i, '?')}** (`{i}`): {r}" for i, r in sorted(passage_flags.items())] or ["(none)"]
    FLAGS_DOC.write_text("\n".join(lines) + "\n")


def main(argv):
    report = "--report" in argv
    dirs = [a for a in argv if not a.startswith("--")]
    held = json.loads(HELD.read_text()) if HELD.exists() else seed_held()
    # Seeded from the October holds, which were all drafter flags on the passage.
    passage_flags = (json.loads(PASSAGE_FLAGS.read_text()) if PASSAGE_FLAGS.exists()
                     else {i: r for i, r in held.items() if not r.startswith("why dropped")})
    parts = load_parts(dirs)
    known, ref_of, total = set(), {}, {"stories": 0, "notes": 0, "approved": 0, "with_why": 0}
    for t in site_tractates():
        stories = json.loads((DATA / f"{t}.json").read_text())["stories"]
        known |= {s["id"] for s in stories}
        ref_of.update({s["id"]: s["ref"] for s in stories})
        pf = OUT / f"{t}.json"
        prev = json.loads(pf.read_text())["notes"] if pf.exists() else {}
        notes, ev = merge(stories, prev, parts, held, passage_flags)
        stale = sorted(set(prev) - {s["id"] for s in stories})
        for i in stale:      # off the site today; kept so a story that returns keeps its reviewed note
            notes[i] = prev[i]
        if not report and (notes or pf.exists()):
            pf.write_text(json.dumps({"tractate": t, "notes": notes}, ensure_ascii=False, indent=1))
        on_site = [notes[s["id"]] for s in stories if s["id"] in notes]
        total["stories"] += len(stories)
        total["notes"] += len(on_site)
        total["approved"] += sum(bool(n.get("approved")) for n in on_site)
        total["with_why"] += sum(bool(n.get("why")) for n in on_site)
        print(f"{t:14} notes={len(on_site):4}/{len(stories):<4} approved={sum(bool(n.get('approved')) for n in on_site):4} "
              f"why={sum(bool(n.get('why')) for n in on_site):4} drafted={ev['drafted']} why_added={ev['why_added']} "
              f"held_now={ev['held']} missing={len(ev['missing'])} stale_kept={len(stale)}")
    unknown = sorted(set(parts) - known)
    print("TOTAL", total, f"held={sum(i in known for i in held)}")
    if not report:
        HELD.parent.mkdir(parents=True, exist_ok=True)
        HELD.write_text(json.dumps(dict(sorted(held.items())), ensure_ascii=False, indent=1))
        PASSAGE_FLAGS.write_text(json.dumps(dict(sorted(passage_flags.items())), ensure_ascii=False, indent=1))
        write_flags_doc({i: r for i, r in held.items() if i in known},
                        {i: r for i, r in passage_flags.items() if i in known}, ref_of)
    if unknown:
        print(f"PROBLEM: {len(unknown)} drafted ids are not on the site: {unknown[:5]}")
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
