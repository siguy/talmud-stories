#!/usr/bin/env python3
"""Draft the Septimus site's background notes with Claude Code subagents (work/2026-11-15-shas-background-notes.md).

    python3 scripts/draft_site_notes.py export --run shas1 [--batch 20] [--ids-file f] [--only <tractate> ...]
    #  ... one subagent per batches/<NNN>/ directory writes answers/<NNN>.json ...
    python3 scripts/draft_site_notes.py import --run shas1
    python3 scripts/build_site_notes.py results/site_notes/shas1/parts

Same shape as scripts/judge_via_subagents.py: no API key; each subagent reads the prompt
(src/prompts/site_note_v2.md) and one plain-text file per story, and writes one JSON file
of answers keyed by file number ("01", "02", ...). Story ids live in keys/, never shown to
an agent. Each story file carries the story's segments (STORY) plus CONTEXT segments of the
surrounding discussion (BEFORE / AFTER), which the `why` field needs.

A missing or invalid answer is counted and named, never written as a note (Lesson 21);
the builder then reports that story as still missing a note.
"""
import argparse
import hashlib
import json
import logging
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
DATA = ROOT / "site" / "data"
PROMPT = ROOT / "src" / "prompts" / "site_note_v2.md"
WORK = ROOT / "results" / "site_notes"
CONTEXT = 3            # segments of discussion shown before and after the story
log = logging.getLogger("draft-site-notes")


def prompt_sha():
    return hashlib.sha256(PROMPT.read_bytes()).hexdigest()[:12]


def site_tractates():
    return [t["tractate"] for t in json.loads((DATA / "index.json").read_text())["tractates"]]


def flat_segments(tractate):
    """Every segment of the tractate in reading order, from the run the site exports, as (ref, index, he, en)."""
    import build_site_data as B   # imported here: its import reads every source on disk
    pages = json.loads((ROOT / B.SOURCES[tractate]["runs"][0]).read_text())["pages"]
    return [(p["ref"], g.get("index", k), B.clean(g.get("hebrew")), B.clean(g.get("english")))
            for p in pages for k, g in enumerate(p["segments"])]


def story_file(story, flat, pos):
    """The text one subagent reads for one story."""
    keys = [(g["ref"], g["i"]) for g in story["segments"]]
    first, last = pos[keys[0]], pos[keys[-1]]
    lines = [f"Story at {story['ref']}.", ""]
    n = 0
    for k in range(max(0, first - CONTEXT), first):
        n += 1
        lines += [f"[{n}] BEFORE ({flat[k][0]})", flat[k][3], ""]
    for g in story["segments"]:
        n += 1
        lines += [f"[{n}] STORY ({g['ref']})", g["he"], g["en"], ""]
    for k in range(last + 1, min(len(flat), last + 1 + CONTEXT)):
        n += 1
        lines += [f"[{n}] AFTER ({flat[k][0]})", flat[k][3], ""]
    return "\n".join(lines)


def export(run, batch, ids=None, only=None):
    d = WORK / run
    if (d / "manifest.json").exists():
        raise SystemExit(f"{d} already exported; pick a new --run")
    for sub in ("batches", "keys", "answers", "parts"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    (d / "prompt.md").write_text(PROMPT.read_text())
    todo = []
    for t in site_tractates():
        if only and t not in only:
            continue
        stories = [s for s in json.loads((DATA / f"{t}.json").read_text())["stories"] if not ids or s["id"] in ids]
        if not stories:
            continue
        flat = flat_segments(t)
        pos = {(r, i): k for k, (r, i, _, _) in enumerate(flat)}
        missing = [s["id"] for s in stories if any((g["ref"], g["i"]) not in pos for g in s["segments"])]
        if missing:
            raise SystemExit(f"{t}: {len(missing)} story segments not found in the source run: {missing[:5]}")
        todo += [(s["id"], story_file(s, flat, pos)) for s in stories]
        log.info("%s: %d stories", t, len(stories))
    if ids and len(todo) != len(ids):
        raise SystemExit(f"--ids-file names {len(ids)} ids, {len(todo)} are on the site")
    n = 0
    for i in range(0, len(todo), batch):
        chunk = todo[i:i + batch]
        (d / "keys" / f"{n:03d}.json").write_text(json.dumps([sid for sid, _ in chunk], indent=1))
        bd = d / "batches" / f"{n:03d}"
        bd.mkdir(exist_ok=True)
        for k, (_, text) in enumerate(chunk, start=1):
            (bd / f"{k:02d}.txt").write_text(text + "\n")
        n += 1
    (d / "manifest.json").write_text(json.dumps({
        "run": run, "batch": batch, "batches": n, "stories": len(todo), "prompt_sha": prompt_sha(),
        "context": CONTEXT, "exported": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1))
    log.info("exported %d stories into %d batches under %s (prompt %s)", len(todo), n, d, prompt_sha())


FIELDS = {"note": str, "why": str, "people": list, "terms": list, "flag": str}


def validate(ans):
    """The answer as a dict, or a reason it is not one."""
    if isinstance(ans, str):
        try:
            ans = json.loads(ans)
        except json.JSONDecodeError as e:
            return None, f"not JSON: {e}"
    if not isinstance(ans, dict):
        return None, "not an object"
    for k, typ in FIELDS.items():
        if not isinstance(ans.get(k, "" if typ is str else []), typ):
            return None, f"{k} is not a {typ.__name__}"
    if not str(ans.get("note", "")).strip():
        return None, "empty note"
    if not all(isinstance(p, dict) for p in ans.get("people", [])) or not all(isinstance(t, dict) for t in ans.get("terms", [])):
        return None, "people/terms entries are not objects"
    return ans, None


def import_(run):
    d = WORK / run
    man = json.loads((d / "manifest.json").read_text())
    if man["prompt_sha"] != prompt_sha():
        raise SystemExit("prompt changed since export -- re-export")
    by_t, bad, missing_batches = {}, [], []
    for kf in sorted((d / "keys").glob("*.json")):
        ids = json.loads(kf.read_text())
        af = d / "answers" / kf.name
        raw = {}
        if not af.exists():
            missing_batches.append(kf.stem)
        else:
            try:
                raw = json.loads(af.read_text())
            except json.JSONDecodeError as e:
                log.warning("batch %s answers unreadable: %s", kf.stem, e)
        for k, sid in enumerate(ids, start=1):
            key = f"{k:02d}"
            if key not in raw:
                bad.append((sid, "no answer"))
                continue
            ans, why_bad = validate(raw[key])
            if why_bad:
                bad.append((sid, why_bad))
                continue
            by_t.setdefault(sid.split("-")[0], []).append({"id": sid, **{f: ans.get(f, "" if t is str else []) for f, t in FIELDS.items()}})
    for t, recs in by_t.items():
        (d / "parts" / f"{t}.{run}.json").write_text(json.dumps(recs, ensure_ascii=False, indent=1))
    log.info("imported %d answers (%s); %d invalid or missing; missing batches %s", sum(map(len, by_t.values())),
             dict(Counter({t: len(r) for t, r in by_t.items()})), len(bad), missing_batches)
    for sid, why in bad[:20]:
        log.warning("  no note: %s (%s)", sid, why)
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("--run", required=True)
    e.add_argument("--batch", type=int, default=20)
    e.add_argument("--ids-file", help="one story id per line; default every story on the site")
    e.add_argument("--only", nargs="*", help="tractate slugs")
    i = sub.add_parser("import")
    i.add_argument("--run", required=True)
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [draft-site-notes] %(message)s",
                        handlers=[logging.FileHandler(ROOT / "project.log"), logging.StreamHandler(sys.stdout)])
    if a.cmd == "export":
        ids = set(Path(a.ids_file).read_text().split()) if a.ids_file else None
        export(a.run, a.batch, ids, set(a.only) if a.only else None)
    else:
        import_(a.run)


if __name__ == "__main__":
    main()
