#!/usr/bin/env python3
"""Permanent story ids for the Septimus site: the registry site/data/story_ids.json.

WHY. A site story id used to be derived from its span (`<tractate>-<daf>-<start>-<end>`), so any boundary change -- a
golden correction, a re-run moving an end segment -- gave the same story a new id and orphaned everything keyed on it:
read-checkmarks (localStorage), feedback issues, boundary_extensions.json, notes/<t>.json and the sign-up app's
`claims/{storyId}`. Now an id is minted ONCE and never re-derived (docs/technical/septimus-viewer-plan.md §3.1).

THE ID IS A NAME, NOT AN ADDRESS. A new id is minted from the span it was born with, so it reads like one -- and every
id that existed when the registry was created is exactly the old span id, so nothing already shipped changed. After a
boundary change the id keeps its old digits; the CURRENT span is the story's `span` field. Never parse a span out of an
id. If the birth span's string is already taken (by a retired or redirected id), the mint gets `-v2`, `-v3`, ...

MATCHING (every build, per tractate). Each built story is matched to the registry entry it OVERLAPS most, by segments
(Lesson 36: overlap, never an exact key), greedily from the largest overlap down, one story per entry:
    boundary shift   -> the entry keeps its id; its recorded span is updated
    split            -> the larger part keeps the id, the other part mints a new one
    merge            -> the merged story keeps the id it overlaps most; the other entry becomes `redirect` to it
    removed          -> `retired` (never reused for another story)
    back again       -> a story overlapping only a RETIRED entry revives it: the same passage is the same story,
                        so a reader's checkmark comes back. A redirected id is never revived.
    nothing overlaps -> mint
A TIE at any step (one story overlapping two entries equally, or two stories one entry equally) is refused: that is a
judgement for a person, never a guess. Resolve it by editing the winning entry's `span` in story_ids.json to the new
span and rebuilding.

A tractate not built in this run is not touched: a tractate held off the site keeps its ids for when it returns.
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "site" / "data" / "story_ids.json"
REDIRECTS = ROOT / "site" / "data" / "redirects.json"
ABOUT = ("Permanent story ids (scripts/story_ids.py; docs/technical/septimus-viewer-plan.md §3.1). Written by "
         "scripts/build_site_data.py; edit by hand only to settle a refused tie (set the winning entry's span). "
         "status: active | redirect (see redirect_to) | retired. span = the id's current source span "
         "[{ref, start, end}] -- never parse it from the id.")


class IdConflict(SystemExit):
    """A match the build will not guess (a tie). SystemExit, so the site build stops with the message."""


def empty():
    return {"about": ABOUT, "ids": {}}


def load(path=REGISTRY):
    return json.loads(Path(path).read_text()) if Path(path).exists() else empty()


def save(reg, path=REGISTRY):
    """One entry per line, keys sorted: a rebuild that changes nothing changes no byte, and a change is a one-line diff."""
    lines = [f" {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in sorted(reg["ids"].items())]
    Path(path).write_text('{\n "about": ' + json.dumps(ABOUT) + ',\n "ids": {\n' + ",\n".join(" " + x for x in lines)
                          + "\n }\n}\n")


def span_of(segments):
    """[{ref, start, end}] of a story's SOURCE segments (before any display extension), one piece per page, in order."""
    out = []
    for g in segments:
        if out and out[-1]["ref"] == g["ref"]:
            out[-1]["start"], out[-1]["end"] = min(out[-1]["start"], g["i"]), max(out[-1]["end"], g["i"])
        else:
            out.append({"ref": g["ref"], "start": g["i"], "end": g["i"]})
    return out


def cells(span):
    return {(p["ref"], i) for p in span for i in range(p["start"], p["end"] + 1)}


def span_id(tractate, span):
    """The legacy id string: <tractate>-<daf of page one>-<start>-<end on page one>. Used only to MINT."""
    p = span[0]
    return f"{tractate}-{p['ref'].split()[-1]}-{p['start']}-{p['end']}"


def _overlaps(story_cells, entries):
    """[(overlap, story k, entry id)] for every overlapping pair, via a cell index (no all-pairs scan)."""
    owner = {}
    for i, e in entries.items():
        for c in cells(e["span"]):
            owner.setdefault(c, []).append(i)
    out = []
    for k, sc in enumerate(story_cells):
        for i, n in Counter(i for c in sc for i in owner.get(c, ())).items():
            out.append((n, k, i))
    return sorted(out, key=lambda x: (-x[0], x[1], x[2]))


def _greedy(pairs, stories, tractate, kind, got_s, got_e):
    """Assign pairs from the largest overlap down, one story per entry; refuse a tie between two free candidates."""
    for n, k, i in pairs:
        if k in got_s or i in got_e:
            continue
        rivals = [(kk, ii) for m, kk, ii in pairs if m == n and (kk, ii) != (k, i) and (kk == k or ii == i)
                  and kk not in got_s and ii not in got_e]
        if rivals:
            names = sorted({stories[kk]["id"] + " ~ " + ii for kk, ii in rivals + [(k, i)]})
            raise IdConflict(f"site build refused: ambiguous {kind} id match in {tractate} ({n} segments each): "
                             f"{'; '.join(names)}. Decide which id the passage keeps: set that entry's `span` in "
                             f"site/data/story_ids.json to the new span, then rebuild.")
        got_s[k], got_e[i] = i, k


def assign(reg, tractate, stories):
    """Give every story in `stories` its permanent id, updating `reg` in place.

    Each story needs `id` (its span id: the mint candidate) and `span`. Sets story["id"] to the permanent id and
    returns {"by_span_id": {span id: permanent id}, "moved": {ids whose span changed}, "minted": [...],
    "retired": [...], "redirected": {old: new}, "revived": [...]}.
    """
    ids = reg["ids"]
    mine = lambda st: {i: e for i, e in ids.items() if e["tractate"] == tractate and e["status"] == st}
    sc = [cells(s["span"]) for s in stories]
    got_s, got_e = {}, {}
    active = mine("active")
    _greedy(_overlaps(sc, active), stories, tractate, "active", got_s, got_e)
    retired = mine("retired")
    rest = [k for k in range(len(stories)) if k not in got_s]
    revive = [(n, k, i) for n, k, i in _overlaps(sc, retired) if k in rest]
    _greedy(revive, stories, tractate, "retired", got_s, got_e)

    report = {"by_span_id": {}, "moved": set(), "minted": [], "retired": [], "redirected": {},
              "revived": sorted(i for i in got_e if i in retired)}
    for k, s in enumerate(stories):          # page order, so minting is deterministic
        if k in got_s:
            i = got_s[k]
            if ids[i]["span"] != s["span"]:
                report["moved"].add(i)
        else:
            base = i = s["id"]
            v = 1
            while i in ids:
                v += 1
                i = f"{base}-v{v}"
            got_s[k] = i
            report["minted"].append(i)
        ids[i] = {"tractate": tractate, "status": "active", "span": s["span"]}
        report["by_span_id"][s["id"]] = i
        s["id"] = i
    # An active entry no story took: merged into the story it overlaps most (redirect), else gone (retired).
    for i, e in sorted(active.items()):
        if i in got_e:
            continue
        hits = sorted(((len(cells(e["span"]) & sc[k]), k) for k in range(len(stories)) if cells(e["span"]) & sc[k]),
                      key=lambda x: (-x[0], x[1]))
        if hits:
            e.update(status="redirect", redirect_to=stories[hits[0][1]]["id"])
            report["redirected"][i] = e["redirect_to"]
        else:
            e["status"] = "retired"
            report["retired"].append(i)
    for i in report["revived"]:
        ids[i].pop("redirect_to", None)
    return report


def redirects(reg):
    """{old id: current id, or null when retired}, chains followed -- what site/app.js reads. Active ids are absent."""
    ids, out = reg["ids"], {}
    for i, e in ids.items():
        if e["status"] == "active":
            continue
        cur, seen = i, set()
        while ids[cur]["status"] == "redirect" and cur not in seen:
            seen.add(cur)
            cur = ids[cur]["redirect_to"]
        out[i] = cur if ids[cur]["status"] == "active" else None
    return dict(sorted(out.items()))
