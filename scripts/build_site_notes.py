#!/usr/bin/env python3
"""Merge drafted learning notes into site/data/notes/<tractate>.json (Phase 4, Septimus viewer).

    python3 scripts/build_site_notes.py <parts_dir>        # merge + validate
    python3 scripts/approve_notes.py --tractate ketubot    # mark reviewed notes shippable

Parts are `<tractate>.<a>-<b>.json`, lists of {id, note, people, terms, flag}. Every note is
written `approved: false`; the site shows unapproved notes only with ?notes=draft, so nothing
AI-drafted reaches the family unreviewed. Re-merging keeps an existing `approved` flag only if
the note text is unchanged. Flags (the drafter thought it is not a story / cut off / garbled)
go to docs/findings/2026-10-12-septimus-note-flags.md for the project team, never to the site.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "site" / "data"
OUT = DATA / "notes"
TRACTATES = ["ketubot", "kiddushin", "gittin", "yevamot"]
TAG = re.compile(r"<[^>]+>")


def clean(s, n):
    return TAG.sub("", str(s or "")).strip()[:n]


def norm(rec):
    return {
        "note": clean(rec.get("note"), 800),
        "people": [{"name": clean(p.get("name"), 80), "about": clean(p.get("about"), 160)}
                   for p in (rec.get("people") or [])[:5] if clean(p.get("name"), 80)],
        "terms": [{"term": clean(t.get("term"), 80), "meaning": clean(t.get("meaning"), 300)}
                  for t in (rec.get("terms") or [])[:4] if clean(t.get("term"), 80) and clean(t.get("meaning"), 300)],
    }


def main(parts_dir):
    parts = Path(parts_dir)
    OUT.mkdir(parents=True, exist_ok=True)
    flags, warns, problems = [], [], []
    for t in TRACTATES:
        stories = json.loads((DATA / f"{t}.json").read_text())["stories"]
        by_id = {}
        for f in sorted(parts.glob(f"{t}.*.json")):
            for rec in json.loads(f.read_text()):
                by_id[rec["id"]] = rec
        missing = [s["id"] for s in stories if s["id"] not in by_id]
        extra = sorted(set(by_id) - {s["id"] for s in stories})
        if missing or extra:
            problems.append(f"{t}: missing {len(missing)} {missing[:3]}, unknown {len(extra)} {extra[:3]}")
        prev = {}
        pf = OUT / f"{t}.json"
        if pf.exists():
            prev = json.loads(pf.read_text())["notes"]
        notes = {}
        for s in stories:
            rec = by_id.get(s["id"])
            if not rec or not clean(rec.get("note"), 800):
                continue
            n = norm(rec)
            english = TAG.sub(" ", " ".join(g["en"] for g in s["segments"])).lower()
            for p in n["people"]:  # a named person must actually be in the passage
                key = re.sub(r"^(rabbi|rav|rabbah|rabba|reish|rabban|r\.)\s+", "", p["name"].lower()).split()
                if key and key[0] not in english:
                    warns.append(f"{s['id']}: person '{p['name']}' not found in the English")
            n["approved"] = bool(prev.get(s["id"], {}).get("approved")) and prev[s["id"]].get("note") == n["note"]
            notes[s["id"]] = n
            if rec.get("flag"):
                flags.append((t, s["ref"], s["id"], s["tier"], clean(rec["flag"], 300)))
        pf.write_text(json.dumps({"tractate": t, "notes": notes}, ensure_ascii=False, indent=1))
        print(f"{t:10} notes={len(notes)}/{len(stories)} approved={sum(n['approved'] for n in notes.values())}")
    lines = ["# Septimus viewer: drafter flags", "",
             "Passages the note-drafter thought are not stories, are cut off, or look garbled. For the project team; not shown on the site. Indicated, not measured.", ""]
    lines += [f"- **{t} {ref}** (`{i}`, {tier}): {fl}" for t, ref, i, tier, fl in flags] or ["(none)"]
    (ROOT / "docs/findings/2026-10-12-septimus-note-flags.md").write_text("\n".join(lines) + "\n")
    print(f"flags={len(flags)} person-warnings={len(warns)}")
    for w in warns[:15]:
        print("  warn:", w)
    if problems:
        print("PROBLEMS:", *problems, sep="\n  ")
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1])
