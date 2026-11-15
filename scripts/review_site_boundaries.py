#!/usr/bin/env python3
"""Fix the boundaries of site stories the note-drafters flagged (Simon 2026-11-15).

    python3 scripts/review_site_boundaries.py export --run bfix1 [--batch 20]
    #  ... one subagent per batches/<NNN>/ writes answers/<NNN>.json ...
    python3 scripts/review_site_boundaries.py import --run bfix1     # writes decisions.json, prints the plan
    python3 scripts/review_site_boundaries.py apply --run bfix1      # boundary_extensions.json + merge groups
    python3 scripts/build_site_data.py

Simon's rules: the site does not need the legal argument around a story, so a story may be TRIMMED to the narrative;
a story cut off may be EXTENDED (at most 2 segments back, 4 forward, as before); two site cards that are really one
story are MERGED (septimus_site_decisions.json `merge`); two different stories that share a background are fine.

Every change is display only: boundary_extensions.json and the merge list. Goldens, runs and story ids are untouched;
a merge redirects the absorbed id (story_ids.py). The flagged list is results/site_notes/passage_flags.json.
A missing or invalid answer is counted and named, never applied (Lesson 21).
"""
import argparse
import hashlib
import json
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import draft_site_notes as D  # noqa: E402  (flat segments of the run the site exports; story codes)

DATA = ROOT / "site" / "data"
EXT = DATA / "boundary_extensions.json"
DECISIONS = ROOT / "results" / "shas_run" / "septimus_site_decisions.json"
FLAGS = ROOT / "results" / "site_notes" / "passage_flags.json"
WORK = ROOT / "results" / "site_notes" / "boundaries"
CONTEXT = 5
MAX_BACK, MAX_FWD = 2, 4
MAX_GAP = 2   # segments a merge may bridge between two halves
log = logging.getLogger("review-site-boundaries")

PROMPT = """You are fixing where stories start and end on a family website for reading the stories of the Babylonian
Talmud. Readers want the story itself: the events, told from beginning to end. They do NOT need the legal argument
around it -- the Gemara's questions, proofs and rulings that come before or after the events.

Each file shows one story (segments marked STORY) with the discussion around it (BEFORE / AFTER). A segment that
belongs to another story already on the site is marked "(site story <id>)". The line "Drafter's concern:" says why
this story was flagged. Its segment numbers refer to an earlier view of the
text; use only the numbers in this file.

Decide ONE of:
- "keep": the STORY segments are right as they are (or two different stories sharing one background, which is fine).
- "adjust": give new first and last segment numbers. You may DROP segments of legal argument at either end, and you
  may ADD segments to finish a story that is cut off -- at most 2 segments before the current first STORY segment and
  at most 4 after the current last one. Never include a segment that belongs to another site story.
- "merge": this story and the adjacent site story <id> are really ONE story split in two. Only when that other story
  is directly next to this one (no segment between them), and only if they are the same events, not two stories.

Answer with ONE JSON object per file:
{"code": "<the Story code on the first line>", "action": "keep" | "adjust" | "merge",
 "first": <segment number, for adjust>, "last": <segment number, for adjust>,
 "merge_with": "<site story id, for merge>", "reason": "<one sentence>"}

Prefer the smallest change that leaves a complete story with the legal argument removed. A segment that mixes the
end of the story with the start of the argument stays in (segments cannot be cut in the middle).
"""


def code(run, sid):
    return hashlib.sha256(f"bfix:{run}:{sid}".encode()).hexdigest()[:6].upper()


def load_site():
    out = {}
    for t in D.site_tractates():
        for s in json.loads((DATA / f"{t}.json").read_text())["stories"]:
            out[s["id"]] = s
    return out


def source_bounds(story, pos):
    """Positions of the story's SOURCE first and last segment (its span, before any display extension)."""
    sp = story["span"]
    return pos[(sp[0]["ref"], sp[0]["start"])], pos[(sp[-1]["ref"], sp[-1]["end"])]


def export(run, batch):
    d = WORK / run
    if (d / "manifest.json").exists():
        raise SystemExit(f"{d} already exported; pick a new --run")
    for sub in ("batches", "keys", "answers"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    (d / "prompt.md").write_text(PROMPT)
    flags = json.loads(FLAGS.read_text())
    site = load_site()
    todo, flats = [], {}
    for sid, concern in sorted(flags.items()):
        s = site.get(sid)
        if not s:
            continue
        t = s["tractate"]
        if t not in flats:
            flat = D.flat_segments(t)
            owner = {(g["ref"], g["i"]): x["id"] for x in site.values() if x["tractate"] == t for g in x["segments"]}
            flats[t] = (flat, {(r, i): k for k, (r, i, _, _) in enumerate(flat)}, owner)
        flat, pos, owner = flats[t]
        shown = [pos[(g["ref"], g["i"])] for g in s["segments"]]
        lo, hi = max(0, shown[0] - CONTEXT), min(len(flat) - 1, shown[-1] + CONTEXT)
        lines, numbers = [f"Story code: {code(run, sid)}", f"Story at {s['ref']}.", f"Drafter's concern: {concern}", ""], {}
        for n, k in enumerate(range(lo, hi + 1), start=1):
            r, i, he, en = flat[k]
            numbers[n] = k
            role = "STORY" if k in shown else ("BEFORE" if k < shown[0] else "AFTER")
            other = owner.get((r, i))
            tag = f" (site story {other})" if other and other != sid else ""
            lines += [f"[{n}] {role} ({r}){tag}", he if role == "STORY" else "", en, ""]
        todo.append({"id": sid, "numbers": numbers, "text": "\n".join(lines)})
    for b in range(0, len(todo), batch):
        chunk = todo[b:b + batch]
        n = b // batch
        (d / "keys" / f"{n:03d}.json").write_text(json.dumps([{"id": c["id"], "numbers": c["numbers"]} for c in chunk]))
        bd = d / "batches" / f"{n:03d}"
        bd.mkdir(exist_ok=True)
        for k, c in enumerate(chunk, start=1):
            (bd / f"{k:02d}.txt").write_text(c["text"] + "\n")
    (d / "manifest.json").write_text(json.dumps({"run": run, "stories": len(todo), "batches": -(-len(todo) // batch),
                                                 "exported": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1))
    log.info("exported %d flagged stories into %s", len(todo), d)


def import_(run):
    """decisions.json: {id: {action, first_pos, last_pos | merge_with, reason}} with positions in the flat run."""
    d = WORK / run
    site = load_site()
    out, bad = {}, []
    for kf in sorted((d / "keys").glob("*.json")):
        keys = json.loads(kf.read_text())
        af = d / "answers" / kf.name
        raw = json.loads(af.read_text()) if af.exists() else {}
        for k, item in enumerate(keys, start=1):
            sid, numbers = item["id"], {int(a): b for a, b in item["numbers"].items()}
            a = raw.get(f"{k:02d}")
            if not isinstance(a, dict) or str(a.get("code", "")).upper() != code(run, sid):
                bad.append((sid, "missing answer or wrong code"))
                continue
            act = a.get("action")
            if act == "keep":
                out[sid] = {"action": "keep", "reason": a.get("reason", "")}
            elif act == "adjust":
                try:
                    first, last = numbers[int(a["first"])], numbers[int(a["last"])]
                except (KeyError, ValueError, TypeError):
                    bad.append((sid, f"adjust with bad segment numbers {a.get('first')}..{a.get('last')}"))
                    continue
                if first > last:
                    bad.append((sid, "adjust: first after last"))
                    continue
                out[sid] = {"action": "adjust", "first_pos": first, "last_pos": last, "reason": a.get("reason", "")}
            elif act == "merge" and a.get("merge_with") in site and a["merge_with"] != sid:
                out[sid] = {"action": "merge", "merge_with": a["merge_with"], "reason": a.get("reason", "")}
            else:
                bad.append((sid, f"unknown action {act!r} or merge target {a.get('merge_with')!r}"))
    (d / "decisions.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    from collections import Counter
    log.info("decisions: %s; invalid %d", dict(Counter(v["action"] for v in out.values())), len(bad))
    for sid, why in bad:
        log.warning("  not decided: %s (%s)", sid, why)
    return out, bad


def apply(run):
    """Write the decisions as display extensions / trims and merge groups. Re-running replaces this run's entries."""
    d = WORK / run
    decisions = json.loads((d / "decisions.json").read_text())
    site = load_site()
    ext = json.loads(EXT.read_text())
    dec = json.loads(DECISIONS.read_text())
    groups = [g for g in dec["merge"]["groups"] if g.get("source") != f"boundary review {run}"]
    flats, changed, refused = {}, [], []
    for sid, v in sorted(decisions.items()):
        s = site[sid]
        t = s["tractate"]
        if t not in flats:
            flat = D.flat_segments(t)
            flats[t] = {(r, i): k for k, (r, i, _, _) in enumerate(flat)}
        pos = flats[t]
        a, z = source_bounds(s, pos)
        if v["action"] == "adjust":
            back, fwd = a - v["first_pos"], v["last_pos"] - z
            if back > MAX_BACK or fwd > MAX_FWD:
                refused.append((sid, f"beyond the extension limits (back {back}, forward {fwd})"))
                continue
            e = {"start_back": max(back, 0), "end_forward": max(fwd, 0),
                 "start_trim": max(-back, 0), "end_trim": max(-fwd, 0),
                 "reason": v["reason"][:300], "decided_by": f"boundary review {run} (Simon 2026-11-15: no legal argument)"}
            if any((e["start_back"], e["end_forward"], e["start_trim"], e["end_trim"])):
                ext[sid] = e
                changed.append(sid)
        elif v["action"] == "merge":
            o = site[v["merge_with"]]
            if o["tractate"] != t:
                refused.append((sid, "merge across tractates"))
                continue
            pair = sorted([s, o], key=lambda x: source_bounds(x, pos)[0])
            gap = source_bounds(pair[1], pos)[0] - source_bounds(pair[0], pos)[1] - 1
            if not 0 <= gap <= MAX_GAP:   # a merge may bridge a short gap (build_site_data.apply_merges fills it)
                refused.append((sid, f"merge with {o['id']}: {gap} segments apart in the source"))
                continue
            if any(g for g in groups if {m["card"] for m in g["members"]} & {sid, o["id"]}):
                continue   # the pair was decided from the other side already
            for x in pair:
                ext.pop(x["id"], None)   # a merge is the union of the source spans; an extension cannot ride along
            groups.append({"tractate": t, "keep": pair[0]["id"],
                           "members": [{"ref": x["span"][0]["ref"], "start_segment": x["span"][0]["start"],
                                        "end_segment": x["span"][0]["end"], "card": x["id"]} for x in pair],
                           "rule": "boundary", "reason": v["reason"][:300],
                           "decided_by": "Simon 2026-11-15: 'if this is actually 1 story, then make it 1'",
                           "source": f"boundary review {run}"})
            changed += [x["id"] for x in pair]
    dec["merge"]["groups"] = groups
    EXT.write_text(json.dumps(ext, ensure_ascii=False, indent=1) + "\n")
    DECISIONS.write_text(json.dumps(dec, ensure_ascii=False, indent=1) + "\n")
    (d / "changed.txt").write_text("\n".join(sorted(set(changed))) + "\n")
    log.info("applied: %d stories changed; %d refused", len(set(changed)), len(refused))
    for sid, why in refused:
        log.warning("  refused: %s (%s)", sid, why)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("--run", required=True)
    e.add_argument("--batch", type=int, default=20)
    for name in ("import", "apply"):
        sub.add_parser(name).add_argument("--run", required=True)
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [review-site-boundaries] %(message)s",
                        handlers=[logging.FileHandler(ROOT / "project.log"), logging.StreamHandler(sys.stdout)])
    {"export": lambda: export(a.run, a.batch), "import": lambda: import_(a.run), "apply": lambda: apply(a.run)}[a.cmd]()


if __name__ == "__main__":
    main()
