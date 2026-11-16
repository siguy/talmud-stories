#!/usr/bin/env python3
"""Review where every site story starts and ends (Simon 2026-11-15; plan docs/history/2026-11-15-PLAN-full-boundary-review.md).

    python3 scripts/review_site_boundaries.py export --run bfull1 --after bfix1 [--only ketubot] [--ids-file f]
                                                     [--flags [FILE]] [--batch 20]
    #  ... one subagent per batches/<NNN>/ writes answers/<NNN>.json ...
    python3 scripts/review_site_boundaries.py import --run bfull1            # decisions.json; invalid answers named
    python3 scripts/review_site_boundaries.py calibrate --run bfull1 --targets tests/expert_boundary_targets_2005.json
    python3 scripts/review_site_boundaries.py second-export --run bfull1 [--targets ...]   # the second reader
    python3 scripts/review_site_boundaries.py second-import --run bfull1    # second/second.json, hold.txt
    python3 scripts/review_site_boundaries.py sample-html --run bfull1 --n 20   # before/after pairs for Simon
    python3 scripts/review_site_boundaries.py apply --run bfull1 --dry-run
    python3 scripts/review_site_boundaries.py apply --run bfull1 --hold <run>/second/hold.txt
    python3 scripts/build_site_data.py

Which stories `export` takes: every site story, unless `--flags`, `--ids-file` or `--only` narrows it (the flags list is
results/site_notes/passage_flags.json by default; `--flags FILE` takes another, e.g. the reader-feedback list).
`--after RUN` leaves out every story that run already decided. A merged card is skipped, by name: the site build refuses
a display extension on a merge member, so there is nothing a reviewer could change on it.

Simon's rules: the site does not need the legal argument around a story, so a story may be TRIMMED to the narrative;
a story cut off may be EXTENDED (at most MAX_BACK segments back and MAX_FWD forward of its SOURCE span); two site cards
that are really one story are MERGED (septimus_site_decisions.json `merge`); two different stories that share a
background are fine. When a ruling ends the story, the ruling stays if it is the outcome of the events and the
Gemara's discussion of it goes (Simon 2026-11-15, Decision 2; Jeff's answer to `jeff:boundary-end-rule` is open).

Every change is display only: boundary_extensions.json and the merge list. Goldens, runs and story ids are untouched;
a merge redirects the absorbed id (story_ids.py), which is why a merge cannot be fully undone (applied.json says so).
A missing or invalid answer is counted and named, never applied (Lesson 21). Anything `apply` will not do is refused
BY NAME, never skipped silently.
"""
import argparse
import hashlib
import html
import json
import logging
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import draft_site_notes as D  # noqa: E402  (flat segments of the run the site exports)
from build_site_data import MAX_BACK, MAX_FWD, MERGE_MAX_GAP  # noqa: E402  (the one source for the limits)
from tractates import slug_of  # noqa: E402

DATA = ROOT / "site" / "data"
EXT = DATA / "boundary_extensions.json"
DECISIONS = ROOT / "results" / "shas_run" / "septimus_site_decisions.json"
FLAGS = ROOT / "results" / "site_notes" / "passage_flags.json"
WORK = ROOT / "results" / "site_notes" / "boundaries"
EXTRA = 2       # segments of context shown beyond the furthest a story may reach, on each side
log = logging.getLogger("review-site-boundaries")

PROMPT = """You are fixing where stories start and end on a family website for reading the stories of the Babylonian
Talmud. Readers want the story itself: the events, told from beginning to end. They do NOT need the legal argument
around it -- the Gemara's questions, proofs and rulings that come before or after the events.

Each file shows one story as the site shows it now (segments marked STORY) with the discussion around it
(BEFORE / AFTER). A segment that belongs to another story already on the site is marked "(site story <id>)". If there
is a line "Drafter's concern:", it says why someone doubted this story; its segment numbers refer to an earlier view
of the text, so use only the numbers in this file. The line "You may start no earlier than [n] and end no later
than [m]." gives the furthest the story may reach; never go beyond it.

Decide ONE of:
- "keep": the STORY segments are right as they are (or two different stories sharing one background, which is fine).
- "adjust": give new first and last segment numbers. You may DROP segments of legal argument at either end, and you
  may ADD segments to finish a story that is cut off, within the limits line. Never include a segment that belongs
  to another site story.
- "merge": this story and a nearby site story <id> are really ONE story split in two: the same events, not two
  stories. Only when nothing but at most 4 segments lies between them, and those segments are part of the same story.

When a ruling ends the story: KEEP the ruling if it is the outcome of the events (the judge's verdict in the case, what
the sage told the man to do); DROP the Gemara's discussion of that ruling (questions, proofs, other opinions).

If the card holds two separate stories that cannot be told apart by moving its ends, answer "keep" and start the
reason with "TWO STORIES:".

Answer with ONE JSON object per file, in one JSON file keyed by file number ("01", "02", ...):
{"code": "<the Story code on the first line>", "action": "keep" | "adjust" | "merge",
 "first": <segment number, for adjust>, "last": <segment number, for adjust>,
 "merge_with": "<site story id, for merge>", "reason": "<one sentence>"}

Prefer the smallest change that leaves a complete story with the legal argument removed. A segment that mixes the
end of the story with the start of the argument stays in (segments cannot be cut in the middle).
"""

SECOND_PROMPT = """You are checking a change another reviewer made to a story on a family website for reading the
stories of the Babylonian Talmud. Readers want the story itself -- the events, told from beginning to end -- and NOT
the legal argument around it (the Gemara's questions, proofs and discussion before or after the events). A ruling
that is the outcome of the events (the verdict in the case) belongs to the story; the discussion of it does not.

Each file shows a passage, segment by segment. Every segment is marked:
  KEPT     shown before the change and after it
  REMOVED  shown before the change, not after it
  ADDED    not shown before the change, shown after it
  (none)   context; not shown either way
"Change:" says what kind of change it was. KEEP means the reviewer changed nothing: then judge the story as shown.

Judge the story as shown AFTER the change (KEPT + ADDED). Answer with ONE JSON object per file, in one JSON file keyed
by file number ("01", "02", ...):
{"code": "<the Story code on the first line>",
 "complete": true | false,      // after the change, is it a whole story, beginning to end?
 "story_lost": true | false,    // did the change remove any of the events of the story?
 "legal_left": true | false,    // is legal argument still shown at either end?
 "verdict": "agree" | "disagree",   // disagree when the after is not complete or story was lost
 "reason": "<one sentence>"}
"""


def code(run, sid):
    return hashlib.sha256(f"bfix:{run}:{sid}".encode()).hexdigest()[:6].upper()


def second_code(run, sid):
    return hashlib.sha256(f"second:{run}:{sid}".encode()).hexdigest()[:6].upper()


# ---------------------------------------------------------------------------------------------------- site, positions

def tractates():
    return [t["tractate"] for t in json.loads((DATA / "index.json").read_text())["tractates"]]


_FLAT = {}


def flat_of(t):
    """(segments in reading order as (ref, index, he, en), {(ref, index): position}) for one tractate."""
    if t not in _FLAT:
        flat = D.flat_segments(t)
        _FLAT[t] = (flat, {(r, i): k for k, (r, i, _, _) in enumerate(flat)})
    return _FLAT[t]


def load_site():
    out = {}
    for t in tractates():
        for s in json.loads((DATA / f"{t}.json").read_text())["stories"]:
            out[s["id"]] = s
    return out


def source_bounds(story, pos):
    """Positions of the story's SOURCE first and last segment (its span, before any display extension)."""
    sp = story["span"]
    return pos[(sp[0]["ref"], sp[0]["start"])], pos[(sp[-1]["ref"], sp[-1]["end"])]


def shown_bounds(story, pos):
    """Positions of the first and last segment the site shows now."""
    g, h = story["segments"][0], story["segments"][-1]
    return pos[(g["ref"], g["i"])], pos[(h["ref"], h["i"])]


def merge_groups():
    return json.loads(DECISIONS.read_text())["merge"]["groups"]


def merged_cards():
    """{card id: keep id} for every member of a recorded merge."""
    return {m["card"]: g["keep"] for g in merge_groups() for m in g["members"]}


def removed_cells():
    """{tractate: {(ref, segment)}} of every `remove` decision: passages taken off the site on purpose."""
    out = defaultdict(set)
    for e in json.loads(DECISIONS.read_text()).get("remove", {}).get("passages", []):
        out[e["tractate"]] |= {(e["ref"], i) for i in range(int(e["start_segment"]), int(e["end_segment"]) + 1)}
    return out


def decided_in(runs):
    out = {}
    for r in runs:
        f = WORK / r / "decisions.json"
        if not f.exists():
            raise SystemExit(f"--after {r}: {f} does not exist")
        out.update(json.loads(f.read_text()))
    return out


# ---------------------------------------------------------------------------------------------------------- export

def story_file(run, s, flat, pos, owner, concern):
    """(text, {file number: position}) for one story. The window is built from the SOURCE span, so every segment the
    limits allow is in the file (plus EXTRA of context), whatever the site shows now."""
    a, z = source_bounds(s, pos)
    sa, sz = shown_bounds(s, pos)
    allow_lo, allow_hi = max(0, a - MAX_BACK), min(len(flat) - 1, z + MAX_FWD)
    lo, hi = max(0, min(allow_lo - EXTRA, sa)), min(len(flat) - 1, max(allow_hi + EXTRA, sz))
    numbers = {n: k for n, k in enumerate(range(lo, hi + 1), start=1)}
    num_of = {k: n for n, k in numbers.items()}
    lines = [f"Story code: {code(run, s['id'])}", f"Story at {s['ref']}."]
    if concern:
        lines.append(f"Drafter's concern: {concern}")
    lines += [f"You may start no earlier than [{num_of[allow_lo]}] and end no later than [{num_of[allow_hi]}].", ""]
    for n, k in numbers.items():
        r, i, he, en = flat[k]
        role = "STORY" if sa <= k <= sz else ("BEFORE" if k < sa else "AFTER")
        other = owner.get(k)
        tag = f" (site story {other})" if other and other != s["id"] else ""
        lines += [f"[{n}] {role} ({r}){tag}"] + ([he] if role == "STORY" else []) + [en, ""]
    return "\n".join(lines), numbers


def owners(site, t, pos):
    """{position: card id} for every segment any site card of tractate t shows."""
    return {pos[(g["ref"], g["i"])]: x["id"] for x in site.values() if x["tractate"] == t for g in x["segments"]}


def select(site, ids=None, only=None, flags=None, after=()):
    """(stories to review, {skip reason: [ids]}) -- every site story unless narrowed; nothing dropped unnamed."""
    pool = sorted(site)
    if flags is not None:
        pool = [i for i in pool if i in flags]
    if ids is not None:
        missing = sorted(set(ids) - set(site))
        if missing:
            raise SystemExit(f"--ids-file names {len(missing)} ids not on the site: {missing[:5]}")
        pool = [i for i in pool if i in ids]
    if only:
        pool = [i for i in pool if site[i]["tractate"] in only]
    done, merged = decided_in(after), merged_cards()
    skipped = {"decided in " + "+".join(after): [i for i in pool if i in done],
               "part of a merge (no display change is possible on it)": [i for i in pool if i in merged and i not in done]}
    return [i for i in pool if i not in done and i not in merged], skipped


def export(run, batch=20, ids=None, only=None, flags_file=None, after=()):
    d = WORK / run
    if (d / "manifest.json").exists():
        raise SystemExit(f"{d} already exported; pick a new --run")
    site = load_site()
    concerns = json.loads(Path(flags_file or FLAGS).read_text()) if Path(flags_file or FLAGS).exists() else {}
    todo, skipped = select(site, ids, only, concerns if flags_file else None, after)
    for sub in ("batches", "keys", "answers"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    (d / "prompt.md").write_text(PROMPT)
    files, own = [], {}
    for sid in todo:
        s = site[sid]
        t = s["tractate"]
        flat, pos = flat_of(t)
        if t not in own:
            own[t] = owners(site, t, pos)
        text, numbers = story_file(run, s, flat, pos, own[t], concerns.get(sid, ""))
        files.append({"id": sid, "numbers": numbers, "text": text})
    for b in range(0, len(files), batch):
        chunk, n = files[b:b + batch], b // batch
        (d / "keys" / f"{n:03d}.json").write_text(json.dumps([{"id": c["id"], "numbers": c["numbers"]} for c in chunk]))
        bd = d / "batches" / f"{n:03d}"
        bd.mkdir(exist_ok=True)
        for k, c in enumerate(chunk, start=1):
            (bd / f"{k:02d}.txt").write_text(c["text"] + "\n")
    (d / "manifest.json").write_text(json.dumps({
        "run": run, "stories": len(files), "batches": -(-len(files) // batch), "after": list(after),
        "only": sorted(only) if only else None, "flags": str(flags_file) if flags_file else None,
        "limits": {"back": MAX_BACK, "forward": MAX_FWD, "merge_gap": MERGE_MAX_GAP},
        "skipped": {k: len(v) for k, v in skipped.items()}, "exported": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1))
    (d / "skipped.json").write_text(json.dumps(skipped, indent=1))
    log.info("exported %d stories into %s; skipped %s", len(files), d, {k: len(v) for k, v in skipped.items()})
    return files, skipped


# ---------------------------------------------------------------------------------------------------------- import

def import_(run):
    """decisions.json: {id: {action, first_pos, last_pos | merge_with, reason, tractate}}, positions in the flat run."""
    d = WORK / run
    site = load_site()
    out, bad = {}, []
    for kf in sorted((d / "keys").glob("*.json")):
        keys = json.loads(kf.read_text())
        af = d / "answers" / kf.name
        try:
            raw = json.loads(af.read_text()) if af.exists() else {}
        except json.JSONDecodeError as e:
            log.warning("batch %s answers unreadable: %s", kf.stem, e)
            raw = {}
        for k, item in enumerate(keys, start=1):
            sid, numbers = item["id"], {int(a): b for a, b in item["numbers"].items()}
            a = raw.get(f"{k:02d}")
            if not isinstance(a, dict) or str(a.get("code", "")).strip().upper() != code(run, sid):
                bad.append((sid, kf.stem, "missing answer or wrong code"))
                continue
            act, reason, t = a.get("action"), str(a.get("reason", "")), site[sid]["tractate"] if sid in site else None
            if act == "keep":
                out[sid] = {"action": "keep", "reason": reason, "tractate": t}
            elif act == "adjust":
                try:
                    first, last = numbers[int(a["first"])], numbers[int(a["last"])]
                except (KeyError, ValueError, TypeError):
                    bad.append((sid, kf.stem, f"adjust with bad segment numbers {a.get('first')}..{a.get('last')}"))
                    continue
                if first > last:
                    bad.append((sid, kf.stem, "adjust: first after last"))
                    continue
                _, pos = flat_of(t)
                lo, hi = source_bounds(site[sid], pos)
                if first < lo - MAX_BACK or last > hi + MAX_FWD:
                    bad.append((sid, kf.stem, "adjust beyond the limits line"))
                    continue
                out[sid] = {"action": "adjust", "first_pos": first, "last_pos": last, "reason": reason, "tractate": t}
            elif act == "merge" and a.get("merge_with") in site and a["merge_with"] != sid:
                out[sid] = {"action": "merge", "merge_with": a["merge_with"], "reason": reason, "tractate": t}
            else:
                bad.append((sid, kf.stem, f"unknown action {act!r} or merge target {a.get('merge_with')!r}"))
    (d / "decisions.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    (d / "invalid.json").write_text(json.dumps([{"id": i, "batch": b, "why": w} for i, b, w in bad], indent=1))
    log.info("decisions: %s; invalid %d (batches %s)", dict(Counter(v["action"] for v in out.values())), len(bad),
             sorted({b for _, b, _ in bad}))
    for sid, b, why in bad:
        log.warning("  not decided: %s (batch %s: %s)", sid, b, why)
    return out, bad


# ----------------------------------------------------------------------------------------------------------- plan

def ext_entry(back, fwd, reason, run):
    return {"start_back": max(back, 0), "end_forward": max(fwd, 0), "start_trim": max(-back, 0), "end_trim": max(-fwd, 0),
            "reason": reason[:300], "decided_by": f"boundary review {run} (Simon 2026-11-15: no legal argument)"}


NUMS = ("start_back", "end_forward", "start_trim", "end_trim")


def same_numbers(e, f):
    return all(int((e or {}).get(k) or 0) == int((f or {}).get(k) or 0) for k in NUMS)


def plan(run, hold=(), confirmed=()):
    """What `apply` would do, without writing: (changes, refused).

    changes: [{"kind": "adjust" | "delete" | "merge", "ids": [...], "tractate", "before", "after", ...}]
    refused: [(id, reason)] -- every decision `apply` will not carry out, by name.
    `hold` ids (the second reader rejected them) are left out; `confirmed` ids are merges the second reader upheld
    although the other card disagreed or carried a trim -- the trim is then dropped, and recorded."""
    d = WORK / run
    decisions = json.loads((d / "decisions.json").read_text())
    man = json.loads((d / "manifest.json").read_text()) if (d / "manifest.json").exists() else {}
    earlier = decided_in(man.get("after") or [])
    site, ext, merged = load_site(), json.loads(EXT.read_text()), merged_cards()
    hold, confirmed = set(hold), set(confirmed)
    changes, refused, in_merge = [], [], set()

    def other_view(o, sid):
        v = decisions.get(o) or earlier.get(o)
        if v is None or (v["action"] == "merge" and v["merge_with"] == sid):
            return None
        return v["action"]

    for sid, v in sorted(decisions.items()):
        if v["action"] != "merge":
            continue
        o = v["merge_with"]
        if sid in hold or o in hold:
            refused.append((sid, f"held by the second reader (merge with {o})"))
            continue
        if sid not in site or o not in site:
            refused.append((sid, f"merge with {o}: a card is not on the site"))
            continue
        if sid in merged or o in merged:
            refused.append((sid, f"merge with {o}: would join a third card to an existing merge "
                                 f"({merged.get(sid) or merged.get(o)})"))
            continue
        s, x = site[sid], site[o]
        if s["tractate"] != x["tractate"]:
            refused.append((sid, f"merge with {o}: across tractates"))
            continue
        _, pos = flat_of(s["tractate"])
        pair = sorted([s, x], key=lambda c: source_bounds(c, pos)[0])
        gap = source_bounds(pair[1], pos)[0] - source_bounds(pair[0], pos)[1] - 1
        if not 0 <= gap <= MERGE_MAX_GAP:
            refused.append((sid, f"merge with {o}: {gap} segments apart in the source (limit {MERGE_MAX_GAP})"))
            continue
        if {sid, o} & in_merge:
            if not any(c["kind"] == "merge" and set(c["ids"]) == {sid, o} for c in changes):
                refused.append((sid, f"merge with {o}: one of them is already in another merge this run"))
            continue    # the pair was decided from the other side already
        ok = sid in confirmed or o in confirmed
        view = other_view(o, sid)
        if view and not ok:
            refused.append((sid, f"merge with {o}: DISAGREEMENT, that card's own review said {view} "
                                 "(second reader decides)"))
            continue
        trimmed = [c for c in (sid, o) if c in ext and any(ext[c].get(k) for k in NUMS)]
        if trimmed and not ok:
            refused.append((sid, f"merge with {o}: {', '.join(trimmed)} already carries a display trim or extension, "
                                 "which a merge would drop (second reader decides)"))
            continue
        a0, z1 = source_bounds(pair[0], pos)[0], source_bounds(pair[1], pos)[1]
        changes.append({"kind": "merge", "ids": [c["id"] for c in pair], "keep": pair[0]["id"], "tractate": s["tractate"],
                        "range": [a0, z1], "dropped_ext": {c: ext[c] for c in trimmed}, "reason": v["reason"],
                        "group": {"tractate": s["tractate"], "keep": pair[0]["id"],
                                  "members": [{"ref": c["span"][0]["ref"], "start_segment": c["span"][0]["start"],
                                               "end_segment": c["span"][0]["end"], "card": c["id"]} for c in pair],
                                  "rule": "boundary", "reason": v["reason"][:300],
                                  "decided_by": "Simon 2026-11-15: 'if this is actually 1 story, then make it 1'",
                                  "source": f"boundary review {run}"}})
        in_merge |= {sid, o}

    for sid, v in sorted(decisions.items()):
        if v["action"] != "adjust":
            continue
        if sid in in_merge:
            refused.append((sid, "adjust superseded by a merge the second reader upheld"))
            continue
        if sid in hold:
            refused.append((sid, "held by the second reader"))
            continue
        if sid not in site:
            refused.append((sid, "not on the site (absorbed by a merge)"))
            continue
        if sid in merged:
            refused.append((sid, f"adjust on a card that is part of a merge ({merged[sid]}); the site build refuses it"))
            continue
        s = site[sid]
        _, pos = flat_of(s["tractate"])
        a, z = source_bounds(s, pos)
        back, fwd = a - v["first_pos"], v["last_pos"] - z
        if back > MAX_BACK or fwd > MAX_FWD:
            refused.append((sid, f"beyond the extension limits (back {back}, forward {fwd})"))
            continue
        new = ext_entry(back, fwd, v["reason"], run) if (back or fwd) else None
        old = ext.get(sid)
        if same_numbers(old, new):
            continue    # what the site shows already
        changes.append({"kind": "adjust" if new else "delete", "ids": [sid], "tractate": s["tractate"],
                        "range": [v["first_pos"], v["last_pos"]], "before": old, "after": new, "reason": v["reason"]})

    # A segment Simon or Jeff REMOVED from the site (septimus_site_decisions.json `remove`) may not come back as part of
    # a widened card: Taanit 23b:9, 2026-11-16, was extended over 23b:8, removed with "drop 8-8, do not widen 9-9".
    removed = removed_cells()
    for c in list(changes):
        flat, pos = flat_of(c["tractate"])
        shown = set()
        for i in c["ids"]:
            a, z = shown_bounds(site[i], pos)
            shown |= set(range(a, z + 1))
        added = {(flat[k][0], flat[k][1]) for k in range(c["range"][0], c["range"][1] + 1) if k not in shown}
        hit = added & removed.get(c["tractate"], set())
        if hit:
            changes.remove(c)
            refused.append((c["ids"][0], f"would show {sorted(hit)[0][0]}:{sorted(hit)[0][1]}, which a `remove` "
                                         "decision took off the site"))

    # No segment may be shown in two cards: checked against EVERY card of the tractate, not only this run's.
    while True:
        bad = overlaps(site, changes)
        if not bad:
            break
        for c, why in bad:
            changes.remove(c)
            refused.append((c["ids"][0], why))
    return changes, refused


def final_ranges(site, changes, t):
    """{card id: (lo, hi)} the site would show in tractate t after `changes`."""
    _, pos = flat_of(t)
    rng = {sid: shown_bounds(s, pos) for sid, s in site.items() if s["tractate"] == t}
    for c in changes:
        if c["tractate"] != t:
            continue
        if c["kind"] == "merge":
            for i in c["ids"]:
                rng.pop(i, None)
            rng[c["keep"]] = tuple(c["range"])
        else:
            rng[c["ids"][0]] = tuple(c["range"])
    return rng


def overlaps(site, changes):
    """[(change, reason)] for changes whose result shares a segment with another card (only the first per pass)."""
    for t in sorted({c["tractate"] for c in changes}):
        rng = final_ranges(site, changes, t)
        mine = {i: c for c in changes if c["tractate"] == t for i in (c["ids"] if c["kind"] != "merge" else [c["keep"]])}
        items = sorted(rng.items(), key=lambda kv: kv[1])
        for (i, (lo, hi)), (j, (lo2, hi2)) in zip(items, items[1:]):
            if lo2 <= hi and (i in mine or j in mine):
                c = mine.get(i) or mine.get(j)
                other = j if c is mine.get(i) else i
                return [(c, f"would share a segment with site story {other}")]
        for i, (lo, hi) in items:      # a card swallowed whole by a wider one is not adjacent in the sort
            for j, (lo2, hi2) in items:
                if i != j and lo <= lo2 and hi2 <= hi and (i in mine or j in mine):
                    c = mine.get(i) or mine.get(j)
                    return [(c, f"would share a segment with site story {j if c is mine.get(i) else i}")]
    return []


# ---------------------------------------------------------------------------------------------------------- apply

def read_ids(f):
    return set(Path(f).read_text().split()) if f else set()


def apply(run, dry_run=False, hold=(), confirmed=()):
    """Write the plan: display extensions / trims, merge groups, changed.txt, applied.json, and mark every changed
    story's note for redraft. Refuses to run twice: applied.json is the only full record of what was there before."""
    d = WORK / run
    if (d / "applied.json").exists() and not dry_run:
        raise SystemExit(f"{d / 'applied.json'} exists: run {run} was applied already; nothing changed")
    changes, refused = plan(run, hold, confirmed)
    kinds = Counter(c["kind"] for c in changes)
    log.info("plan for %s: %s; refused %d", run, dict(kinds), len(refused))
    for sid, why in refused:
        log.warning("  refused: %s (%s)", sid, why)
    if dry_run:
        for c in changes:
            log.info("  %s %s -> %s", c["kind"], "+".join(c["ids"]), c["range"])
        return changes, refused
    ext, dec = json.loads(EXT.read_text()), json.loads(DECISIONS.read_text())
    record, changed = {}, []
    for c in changes:
        if c["kind"] == "merge":
            for i in c["ids"]:
                ext.pop(i, None)   # a merge is the union of the source spans; an extension cannot ride along
            dec["merge"]["groups"].append(c["group"])
            record["+".join(c["ids"])] = {"kind": "merge", "group": c["group"], "dropped_ext": c["dropped_ext"]}
        elif c["kind"] == "delete":
            ext.pop(c["ids"][0])
            record[c["ids"][0]] = {"kind": "delete", "before": c["before"], "after": None}
        else:
            ext[c["ids"][0]] = c["after"]
            record[c["ids"][0]] = {"kind": "adjust", "before": c["before"], "after": c["after"]}
        changed += c["ids"]
    EXT.write_text(json.dumps(ext, ensure_ascii=False, indent=1) + "\n")
    DECISIONS.write_text(json.dumps(dec, ensure_ascii=False, indent=1) + "\n")
    (d / "changed.txt").write_text("".join(f"{i}\n" for i in sorted(set(changed))))
    (d / "applied.json").write_text(json.dumps({
        "run": run, "applied": time.strftime("%Y-%m-%dT%H:%M:%S"), "held": sorted(hold), "confirmed": sorted(confirmed),
        "undo": "Trims and extensions: put `before` back in site/data/boundary_extensions.json (null = no entry). "
                "A merge can NOT be fully undone: story_ids.py never revives a redirected id, so removing the group "
                "mints a new id for the absorbed card and orphans readers' checkmarks and its old note key.",
        "changes": record, "refused": [{"id": i, "why": w} for i, w in refused]}, ensure_ascii=False, indent=1))
    marked = mark_notes_for_redraft(set(changed))
    log.info("applied: %d stories changed; %d notes marked for redraft; %d refused", len(set(changed)), marked,
             len(refused))
    return changes, refused


def mark_notes_for_redraft(ids):
    """A changed story's note describes the old boundaries: `drafted` + not approved makes build_site_notes.py take the
    next draft whole (its keep_text rule) instead of keeping the old approved text."""
    n = 0
    for f in sorted((DATA / "notes").glob("*.json")):
        doc = json.loads(f.read_text())
        hit = [i for i in doc["notes"] if i in ids]
        for i in hit:
            doc["notes"][i].update(drafted="boundary-changed", approved=False)
        if hit:
            f.write_text(json.dumps(doc, ensure_ascii=False, indent=1))
            n += len(hit)
    return n


# ------------------------------------------------------------------------------------------------------- calibrate

def jeff_stories(target_file):
    """(tractate slug, [(key, first position, last position)]) from an expert boundary target file."""
    doc = json.loads(Path(target_file).read_text())
    t = slug_of(doc["tractate"]) if "tractate" in doc else None
    by = defaultdict(dict)
    for x in doc["targets"]:
        t = t or slug_of(x["located_on"].rsplit(" ", 1)[0])
        by[x["review_key"]][x["direction"]] = (x["located_on"], x["segment"])
    _, pos = flat_of(t)
    out, unplaced = [], []
    for k, v in sorted(by.items()):
        if "start" in v and "end" in v and v["start"] in pos and v["end"] in pos:
            out.append((k, pos[v["start"]], pos[v["end"]]))
        else:
            unplaced.append(k)
    if unplaced:
        log.warning("%s: %d expert stories have no start/end placed in the site's run: %s", t, len(unplaced), unplaced[:5])
    return t, out


def after_ranges(run, t, site):
    """{card id: (before, after)} for the cards of tractate t this run decided (keep / adjust / merge)."""
    decisions = json.loads((WORK / run / "decisions.json").read_text())
    _, pos = flat_of(t)
    out = {}
    for sid, v in decisions.items():
        s = site.get(sid)
        if not s or s["tractate"] != t:
            continue
        before = shown_bounds(s, pos)
        if v["action"] == "keep":
            out[sid] = (before, before)
        elif v["action"] == "adjust":
            out[sid] = (before, (v["first_pos"], v["last_pos"]))
        elif v["merge_with"] in site:
            o = site[v["merge_with"]]
            ends = [source_bounds(s, pos), source_bounds(o, pos)]
            out[sid] = (before, (min(e[0] for e in ends), max(e[1] for e in ends)))
    return out, decisions


def calibrate(run, target_files, sorted_file=None):
    """Score a run's decisions against Jeff's 2005 boundaries (plan step 3). Reads decisions only; applies nothing.

    A  starts kept   -- of measurable stories (wholly inside one reviewed card), his first segment still shown
    B  ends kept     -- his last segment still shown; every cut end goes to cut_ends.json for sorting
    C  left alone    -- of cards that already match him exactly: same start and not lengthened (an earlier end is B's)
    D  benefit       -- extra segments (shown but not his) removed; information only
    E  extend/merge  -- stories over two or more cards or past one card: merges of two of his stories, extensions
                        past his end (each listed)"""
    site = load_site()
    sorts = json.loads(Path(sorted_file).read_text()) if sorted_file else {}
    report, cut_ends, cases = {}, [], defaultdict(list)
    for tf in target_files:
        t, stories = jeff_stories(tf)
        flat, _ = flat_of(t)
        ranges, decisions = after_ranges(run, t, site)
        r = Counter()
        for key, js, je in stories:
            hold = [sid for sid, (b, _) in ranges.items() if b[0] <= js and je <= b[1]]
            if len(hold) == 1:
                sid = hold[0]
                (blo, bhi), (alo, ahi) = ranges[sid]
                r["measurable"] += 1
                start_kept, end_kept = alo <= js <= ahi, alo <= je <= ahi
                r["A_starts_kept"] += start_kept
                r["B_ends_kept"] += end_kept
                if not start_kept:
                    cases["A_start_cut"].append({"tractate": t, "key": key, "card": sid, "jeff": [js, je], "after": [alo, ahi]})
                if not end_kept and ahi < je:
                    k = f"{t}:{key}"
                    cut_ends.append({"key": k, "tractate": t, "card": sid, "jeff": [js, je], "after": [alo, ahi],
                                     "reason": decisions[sid].get("reason", ""),
                                     "kept_end": [flat[x][0] + ":" + str(flat[x][1]) + " " + flat[x][3] for x in range(max(alo, ahi - 1), ahi + 1)],
                                     "cut": [flat[x][0] + ":" + str(flat[x][1]) + " " + flat[x][3] for x in range(ahi + 1, je + 1)]})
                    sort = sorts.get(k)
                    r[f"B_cut_{sort or 'unsorted'}"] += 1
                if (blo, bhi) == (js, je):
                    r["C_exact"] += 1
                    r["C_left_alone"] += alo == js and ahi <= je
                    if not (alo == js and ahi <= je):
                        cases["C_changed"].append({"tractate": t, "key": key, "card": sid, "jeff": [js, je], "after": [alo, ahi]})
                extra = {x for x in range(blo, bhi + 1)} - set(range(js, je + 1))
                r["D_extra"] += len(extra)
                r["D_removed"] += len({x for x in extra if not alo <= x <= ahi})
            else:
                over = [sid for sid, (b, _) in ranges.items() if b[0] <= je and js <= b[1]]
                if not over:
                    continue
                r["E_stories"] += 1
                shown_b = {x for sid in over for x in range(ranges[sid][0][0], ranges[sid][0][1] + 1)}
                shown_a = {x for sid in over for x in range(ranges[sid][1][0], ranges[sid][1][1] + 1)}
                mine = set(range(js, je + 1))
                r["E_jeff_segments_before"] += len(mine & shown_b)
                r["E_jeff_segments_after"] += len(mine & shown_a)
                for sid in over:
                    (blo, bhi), (alo, ahi) = ranges[sid]
                    if ahi > max(bhi, je) and blo <= je:
                        cases["E_past_his_end"].append({"tractate": t, "key": key, "card": sid, "jeff": [js, je],
                                                        "before": [blo, bhi], "after": [alo, ahi]})
        # merges of two of his separate stories
        for sid, v in decisions.items():
            if v["action"] != "merge" or sid not in site or v["merge_with"] not in site or site[sid]["tractate"] != t:
                continue
            _, pos = flat_of(t)
            m1, m2 = source_bounds(site[sid], pos), source_bounds(site[v["merge_with"]], pos)
            h1, h2 = ({k for k, js, je in stories if js <= m[1] and m[0] <= je} for m in (m1, m2))
            r["E_merges"] += 1
            if h1 and h2 and not (h1 & h2):
                r["E_merge_of_two_jeff_stories"] += 1
                cases["E_merge_of_two"].append({"tractate": t, "card": sid, "with": v["merge_with"],
                                                "jeff": sorted(h1 | h2)})
        report[t] = dict(r)
    for t, r in report.items():
        r["narrative_lost"] = r.get("measurable", 0) - r.get("A_starts_kept", 0) + r.get("B_cut_lost", 0)
        r["narrative_lost_pct"] = round(100 * r["narrative_lost"] / r["measurable"], 1) if r.get("measurable") else None
        r["C_pct"] = round(100 * r.get("C_left_alone", 0) / r["C_exact"], 1) if r.get("C_exact") else None
    d = WORK / run
    (d / "cut_ends.json").write_text(json.dumps(cut_ends, ensure_ascii=False, indent=1))
    (d / "calibration.json").write_text(json.dumps({"report": report, "cases": cases,
                                                    "unsorted_cut_ends": [c["key"] for c in cut_ends if c["key"] not in sorts]},
                                                   ensure_ascii=False, indent=1))
    for t, r in report.items():
        log.info("calibrate %s %s: %s", run, t, r)
    return report, cut_ends, cases


# --------------------------------------------------------------------------------------------------- second reader

def second_select(run, changes, refused, targets=(), sample=100, keeps=40, seed=20261115):
    """{id: why it is read} -- every big trim, merge, merge disagreement and expert-segment cut; a random sample of the
    rest. Also returns the changes by id, so the files can be written."""
    site = load_site()
    decisions = json.loads((WORK / run / "decisions.json").read_text())
    jeff = defaultdict(set)
    for tf in targets:
        t, st = jeff_stories(tf)
        for _, js, je in st:
            jeff[t] |= set(range(js, je + 1))
    why, by_id = {}, {}
    for c in changes:
        by_id[c["ids"][0]] = c
        if c["kind"] == "merge":
            why[c["ids"][0]] = "merge"
            continue
        if c["kind"] == "delete":      # undoes an extension someone decided earlier: always read
            why[c["ids"][0]] = "undoes an earlier extension"
            continue
        s = site[c["ids"][0]]
        _, pos = flat_of(s["tractate"])
        b0, b1 = shown_bounds(s, pos)
        before, after = set(range(b0, b1 + 1)), set(range(c["range"][0], c["range"][1] + 1))
        if len(before - after) * 2 >= len(before):
            why[c["ids"][0]] = "trim removes half or more"
        elif (before - after) & jeff.get(s["tractate"], set()):
            why[c["ids"][0]] = "cuts an expert segment"
    for sid, w in refused:
        v = decisions.get(sid, {})
        if v.get("action") == "merge" and ("DISAGREEMENT" in w or "display trim" in w):
            why[sid] = "merge refused: " + w
            s, o = site[sid], site[v["merge_with"]]
            _, pos = flat_of(s["tractate"])
            ends = [source_bounds(s, pos), source_bounds(o, pos)]
            by_id[sid] = {"kind": "merge", "ids": sorted([sid, v["merge_with"]], key=lambda i: source_bounds(site[i], pos)[0]),
                          "tractate": s["tractate"], "range": [min(e[0] for e in ends), max(e[1] for e in ends)],
                          "refused": True}
    rnd = random.Random(seed)
    rest = sorted(i for i, c in by_id.items() if i not in why and c["kind"] != "merge")
    for i in rnd.sample(rest, min(sample, len(rest))):
        why[i] = "random adjust"
    kept = sorted(i for i, v in decisions.items() if v["action"] == "keep" and i in site)
    for i in rnd.sample(kept, min(keeps, len(kept))):
        why[i] = "random keep"
        s = site[i]
        _, pos = flat_of(s["tractate"])
        by_id[i] = {"kind": "keep", "ids": [i], "tractate": s["tractate"], "range": list(shown_bounds(s, pos))}
    return why, by_id


def before_after_lines(site, c, flat, pos):
    """[(position, mark)] for one change's window: KEPT / REMOVED / ADDED / ''."""
    before = set()
    for i in c["ids"]:
        b0, b1 = shown_bounds(site[i], pos)
        before |= set(range(b0, b1 + 1))
    after = set(range(c["range"][0], c["range"][1] + 1))
    lo, hi = max(0, min(before | after) - EXTRA), min(len(flat) - 1, max(before | after) + EXTRA)
    marks = []
    for k in range(lo, hi + 1):
        marks.append((k, "KEPT" if k in before and k in after else "REMOVED" if k in before else
                      "ADDED" if k in after else ""))
    return marks


def second_export(run, targets=(), sample=100, keeps=40, batch=20, hold=(), confirmed=()):
    d = WORK / run / "second"
    if (d / "manifest.json").exists():
        raise SystemExit(f"{d} already exported")
    changes, refused = plan(run, hold, confirmed)
    why, by_id = second_select(run, changes, refused, targets, sample, keeps)
    site = load_site()
    for sub in ("batches", "keys", "answers"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    (d / "prompt.md").write_text(SECOND_PROMPT)
    files = []
    for sid in sorted(why):
        c = by_id[sid]
        flat, pos = flat_of(c["tractate"])
        kind = {"merge": "MERGE (two site cards joined into one)", "keep": "KEEP (nothing changed)",
                "delete": "back to the detector's span", "adjust": "TRIM / EXTEND"}[c["kind"]]
        lines = [f"Story code: {second_code(run, sid)}", f"Story at {site[sid]['ref']}.", f"Change: {kind}", ""]
        for n, (k, mark) in enumerate(before_after_lines(site, c, flat, pos), start=1):
            r, i, he, en = flat[k]
            lines += [f"[{n}] {mark or '-'} ({r})", en, ""]
        files.append((sid, "\n".join(lines)))
    for b in range(0, len(files), batch):
        chunk, n = files[b:b + batch], b // batch
        (d / "keys" / f"{n:03d}.json").write_text(json.dumps([{"id": i, "why": why[i], "kind": by_id[i]["kind"],
                                                               "ids": by_id[i]["ids"]} for i, _ in chunk]))
        bd = d / "batches" / f"{n:03d}"
        bd.mkdir(exist_ok=True)
        for k, (_, text) in enumerate(chunk, start=1):
            (bd / f"{k:02d}.txt").write_text(text + "\n")
    (d / "manifest.json").write_text(json.dumps({"run": run, "stories": len(files), "why": dict(Counter(why.values())),
                                                 "exported": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1))
    log.info("second reader: %d files (%s)", len(files), dict(Counter(why.values())))
    return why


def second_import(run):
    """second.json {id: answer + why}; hold.txt = changes the reader rejected; confirmed.txt = refused merges upheld.
    Gate (plan step 5) on the random adjusts: <=10% disagree apply all but those; 10-20% read every adjust; >20% stop."""
    d = WORK / run / "second"
    out, bad = {}, []
    for kf in sorted((d / "keys").glob("*.json")):
        keys = json.loads(kf.read_text())
        af = d / "answers" / kf.name
        try:
            raw = json.loads(af.read_text()) if af.exists() else {}
        except json.JSONDecodeError:
            raw = {}
        for k, item in enumerate(keys, start=1):
            a = raw.get(f"{k:02d}")
            if (not isinstance(a, dict) or str(a.get("code", "")).strip().upper() != second_code(run, item["id"])
                    or a.get("verdict") not in ("agree", "disagree")):
                bad.append((item["id"], kf.stem))
                continue
            out[item["id"]] = {**a, "why": item["why"], "kind": item["kind"], "ids": item["ids"]}
    hold = sorted({i for v in out.values() if v["verdict"] == "disagree" and v["kind"] != "keep"
                   and not v["why"].startswith("merge refused") for i in v["ids"]})
    confirmed = sorted(i for i, v in out.items() if v["why"].startswith("merge refused") and v["verdict"] == "agree")
    rnd = [v for v in out.values() if v["why"] == "random adjust"]
    pct = round(100 * sum(v["verdict"] == "disagree" for v in rnd) / len(rnd), 1) if rnd else None
    gate = None if pct is None else ("apply all but the disagreed" if pct <= 10 else
                                     "second-read every adjust first" if pct <= 20 else "STOP")
    summary = {"read": len(out), "invalid": bad, "by_why": {w: dict(Counter(v["verdict"] for v in out.values() if v["why"] == w))
                                                           for w in sorted({v["why"] for v in out.values()})},
               "random_adjust_disagree_pct": pct, "gate": gate,
               "keeps_not_complete": sorted(i for i, v in out.items() if v["kind"] == "keep" and v.get("complete") is False)}
    (d / "second.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    (d / "summary.json").write_text(json.dumps(summary, indent=1))
    (d / "hold.txt").write_text("".join(f"{i}\n" for i in hold))
    (d / "confirmed.txt").write_text("".join(f"{i}\n" for i in confirmed))
    log.info("second reader: %d read, %d invalid; random adjusts %s%% disagree -> %s; hold %d, merges upheld %d",
             len(out), len(bad), pct, gate, len(hold), len(confirmed))
    return summary


# ----------------------------------------------------------------------------------------------- Simon's sample page

def sample_html(run, n=20, seed=7, hold=(), confirmed=(), out=None):
    """A page of before/after pairs, Hebrew and English (CLAUDE.md rule 1), for Simon to read before apply."""
    changes, _ = plan(run, hold, confirmed)
    site = load_site()
    rnd = random.Random(seed)
    merges = [c for c in changes if c["kind"] == "merge"]
    others = [c for c in changes if c["kind"] != "merge"]
    n_merge = min(len(merges), max(2, n // 5))     # merges are the change hardest to undo: always some in the sample
    pick = rnd.sample(merges, n_merge) + rnd.sample(others, min(len(others), n - n_merge))
    decisions = json.loads((WORK / run / "decisions.json").read_text())
    css = """:root{--bg:#fbfaf7;--fg:#222;--muted:#666;--kept:#fff;--rem:#fde2e1;--add:#dff3e3;--line:#ddd}
@media (prefers-color-scheme:dark){:root{--bg:#1b1b1b;--fg:#eee;--muted:#aaa;--kept:#222;--rem:#4a2323;--add:#1f3d26;--line:#444}}
body{background:var(--bg);color:var(--fg);font:16px/1.5 Georgia,serif;margin:0 auto;max-width:900px;padding:16px}
h2{font-size:1.1rem;margin-top:2.5rem;border-top:1px solid var(--line);padding-top:1rem}
.seg{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:6px 8px;border-radius:4px;margin:2px 0}
.seg .he{direction:rtl;font-size:1.1rem}.KEPT{background:var(--kept)}.REMOVED{background:var(--rem)}
.ADDED{background:var(--add)}.ctx{opacity:.45}.tag{font:12px sans-serif;color:var(--muted)}
.why{color:var(--muted);font-style:italic}@media(max-width:600px){.seg{grid-template-columns:1fr}}"""
    body = [f"<h1>Boundary review {html.escape(run)}: {len(pick)} before/after pairs</h1>",
            "<p>Red = shown now, removed by the change. Green = added. White = kept. Faded = context, not shown.</p>"]
    for c in pick:
        sid = c["ids"][0]
        flat, pos = flat_of(c["tractate"])
        body.append(f"<h2>{html.escape(site[sid]['ref'])} &middot; {c['kind']} &middot; "
                    f"<span class=tag>{html.escape(' + '.join(c['ids']))}</span></h2>")
        body.append(f"<p class=why>{html.escape(decisions.get(sid, {}).get('reason', c.get('reason', '')))}</p>")
        for k, mark in before_after_lines(site, c, flat, pos):
            r, i, he, en = flat[k]
            body.append(f"<div class='seg {mark or 'ctx'}'><div class=en><span class=tag>{html.escape(r)}:{i} "
                        f"{mark}</span><br>{en}</div><div class=he>{he}</div></div>")
    page = (f"<!doctype html><html><head><meta charset=utf-8><meta name=viewport content='width=device-width'>"
            f"<title>Boundary sample</title><style>{css}</style></head><body>{''.join(body)}</body></html>")
    out = Path(out or WORK / run / "sample.html")
    out.write_text(page)
    log.info("sample page: %s (%d pairs)", out, len(pick))
    return out


# ------------------------------------------------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("--run", required=True)
    e.add_argument("--batch", type=int, default=20)
    e.add_argument("--ids-file", help="one story id per line; default every story on the site")
    e.add_argument("--only", nargs="*", help="tractate slugs")
    e.add_argument("--flags", nargs="?", const=str(FLAGS), default=None,
                   help=f"only the stories in a flags file {{id: concern}} (default file {FLAGS.relative_to(ROOT)})")
    e.add_argument("--after", nargs="*", default=[], help="leave out every story these runs already decided")
    sub.add_parser("import").add_argument("--run", required=True)
    p = sub.add_parser("apply")
    p.add_argument("--run", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--hold", help="ids the second reader rejected (one per line): not applied")
    p.add_argument("--confirmed", help="refused merges the second reader upheld (one per line)")
    c = sub.add_parser("calibrate")
    c.add_argument("--run", required=True)
    c.add_argument("--targets", nargs="+", required=True)
    c.add_argument("--sorted", help="{cut-end key: fine | ruling | lost}, the sorter's answers")
    s = sub.add_parser("second-export")
    s.add_argument("--run", required=True)
    s.add_argument("--targets", nargs="*", default=[])
    s.add_argument("--sample", type=int, default=100)
    s.add_argument("--keeps", type=int, default=40)
    sub.add_parser("second-import").add_argument("--run", required=True)
    h = sub.add_parser("sample-html")
    h.add_argument("--run", required=True)
    h.add_argument("--n", type=int, default=20)
    h.add_argument("--hold")
    h.add_argument("--confirmed")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [review-site-boundaries] %(message)s",
                        handlers=[logging.FileHandler(ROOT / "project.log"), logging.StreamHandler(sys.stdout)])
    if a.cmd == "export":
        export(a.run, a.batch, read_ids(a.ids_file) if a.ids_file else None, set(a.only) if a.only else None,
               a.flags, tuple(a.after))
    elif a.cmd == "import":
        import_(a.run)
    elif a.cmd == "apply":
        apply(a.run, a.dry_run, read_ids(a.hold), read_ids(a.confirmed))
    elif a.cmd == "calibrate":
        calibrate(a.run, a.targets, a.sorted)
    elif a.cmd == "second-export":
        second_export(a.run, a.targets, a.sample, a.keeps)
    elif a.cmd == "second-import":
        second_import(a.run)
    else:
        sample_html(a.run, a.n, hold=read_ids(a.hold), confirmed=read_ids(a.confirmed))


if __name__ == "__main__":
    main()
