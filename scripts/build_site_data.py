#!/usr/bin/env python3
"""Export the stories for the Septimus family viewer (work/2026-10-12-septimus-story-viewer.md).

Reads (read-only): results/canonical/{ketubot,kiddushin,gittin}_canonical.json and
results/v11/yevamot/yevamot_v11.json, and Berakhot (below). Writes site/data/index.json + site/data/<tractate>.json.

Tiers (decided 2026-10-12): `story` = YES or HIGH_CONFIDENCE; `borderline` = BORDERLINE, shown
separately. LOW_CONFIDENCE is NOT shipped (Simon, 2026-10-12). NOT_A_STORY never ships. Yevamot has no expert
round: its stories are detector output, flagged `reviewed: false`.

mishnah_stories[] (Stage 4g's withheld Mishnah-internal stories) IS exported, per Simon
2026-10-12: flagged `in_mishnah: true` and `reviewed: false` (detector output, never shown to
Jeff; whether they count is still his scope question).

Berakhot (Simon, 2026-11-09): detector v14 output (results/v14/berakhot/run1.json),
`reviewed: false`, and ONLY the `story` passages both consensus judges call a story
(results/consensus/berakhot/{gemini,claude}.json, prompt judge_register_v2.md) -- the
strong-yes set. A v14 span ships only if it is YES/HIGH_CONFIDENCE AND its segments
overlap such a unit -- both gates, the judges never override the detector's grade -- AND
run2 also grades an overlapping span YES/HIGH (the detector is not deterministic). Borderline, split
and out-of-scope passages (the five biblical episodes, R-S1) do not ship.

Hebrew already carries nikud in the cached Sefaria segments; coverage is asserted below.
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "data"

SOURCES = {
    "ketubot": ("results/canonical/ketubot_canonical.json", True),
    "kiddushin": ("results/canonical/kiddushin_canonical.json", True),
    "gittin": ("results/canonical/gittin_canonical.json", True),
    "yevamot": ("results/v11/yevamot/yevamot_v11.json", False),
    "berakhot": ("results/v14/berakhot/run1.json", False),
}
CONSENSUS = {"berakhot": "results/consensus/berakhot"}
# The detector is not deterministic: a story is definite only if EVERY run grades it YES/HIGH.
# Each extra run listed here must also hold a YES/HIGH span overlapping the shipped one.
CORROBORATE = {"berakhot": ["results/v14/berakhot/run2.json"]}


def definite_cells(path):
    """Cells of YES/HIGH_CONFIDENCE spans in stories[] (never mishnah_stories) of one run."""
    pages = json.loads((ROOT / path).read_text())["pages"]
    return {(r, g.get("index")) for i, p in enumerate(pages) for s in p.get("stories", [])
            if tier(s.get("classification")) == "story" for r, gs in pieces(pages, i, s) for g in gs}


def strong_yes_cells(tractate):
    """Cells (page ref, segment index) of units BOTH judges call `story`; None = no filter."""
    d = CONSENSUS.get(tractate)
    if not d:
        return None
    verdict = {m: {r["id"]: r["answer"].get("verdict") for r in json.loads((ROOT / d / f"{m}.json").read_text())["rows"]
                   if r["answer"].get("outcome") == "ok"} for m in ("gemini", "claude")}
    units = json.loads((ROOT / d / "units.json").read_text())["units"]
    return {tuple(c) for u in units if verdict["gemini"].get(u["id"]) == verdict["claude"].get(u["id"]) == "story"
            for c in u["cells"]}
NIKUD = re.compile("[ְ-ׇ]")
KEEP = {"b", "i", "strong", "em", "big", "small", "br"}
TAG = re.compile(r"<(/?)([a-zA-Z0-9]+)[^>]*>")
SUP = re.compile(r"<sup\b.*?</sup>|<i class=\"footnote\">.*?</i>", re.S)


def clean(html):
    html = SUP.sub("", html or "")
    return TAG.sub(lambda m: f"<{m.group(1)}{m.group(2).lower()}>" if m.group(2).lower() in KEEP else "", html)


def tier(classification):
    if classification == "NOT_A_STORY":
        return None
    if classification == "BORDERLINE":
        return "borderline"
    return "story" if classification in ("YES", "HIGH_CONFIDENCE") else None


def pieces(pages, i, s):
    """(page_ref, [segments]) pieces of one story. Cross-page: start..end on page one,
    start_page2..end_page2 on the next page (evaluate_golden.py reads it the same way)."""
    p = pages[i]
    a, b = int(s["start_segment"]), int(s["end_segment"])
    out = [(p["ref"], p["segments"][a:b + 1])]
    if s.get("spans_pages") and s.get("end_segment_page2") is not None:
        q = pages[i + 1]
        assert q["ref"] == s["spans_pages"][1], (p["ref"], q["ref"])
        out.append((q["ref"], q["segments"][int(s.get("start_segment_page2") or 0):int(s["end_segment_page2"]) + 1]))
    return out


def build(tractate, path, reviewed):
    d = json.loads((ROOT / path).read_text())
    pages = d["pages"]
    strong = strong_yes_cells(tractate)
    others = [definite_cells(q) for q in CORROBORATE.get(tractate, [])]
    stories = []
    for i, p in enumerate(pages):
        for in_mishnah, key in ((False, "stories"), (True, "mishnah_stories")):
            for s in p.get(key, []):
                t = tier(s.get("classification"))
                ps = pieces(pages, i, s)
                segs = [(r, g) for r, gs in ps for g in gs]
                assert segs, (tractate, p["ref"], s)
                if strong is not None and (t != "story" or not {(r, g.get("index")) for r, g in segs} & strong):
                    # The judges can only NARROW the detector's `story` tier, never promote: a span ships
                    # only if the detector says YES/HIGH_CONFIDENCE AND both judges call it a story.
                    # (2026-11-09: letting the judges promote LOW_CONFIDENCE shipped 8 stories that were
                    # not definite -- Simon: only definite stories reach the site. Lesson 45.)
                    t = None
                if t == "story" and any(not {(r, g.get("index")) for r, g in segs} & o for o in others):
                    t = None   # graded below YES/HIGH (or not proposed) in another run: not definite
                if t is None:
                    continue
                if not NIKUD.search("".join(g.get("hebrew") or "" for _, g in segs)):
                    print(f"  no nikud: {tractate} {p['ref']} {s['start_segment']}", file=sys.stderr)
                stories.append({
                    "id": f"{tractate}-{p['ref'].split()[-1]}-{s['start_segment']}-{s['end_segment']}",
                    "tractate": tractate,
                    "ref": p["ref"],
                    "refs": [r for r, _ in ps],
                    "start_segment": int(s["start_segment"]),
                    "tier": t,
                    "classification": s.get("classification"),
                    "in_mishnah": in_mishnah,
                    "extended": None,
                    # Mishnah-internal stories were never shown to Jeff, whatever the tractate.
                    "reviewed": reviewed and not in_mishnah,
                    # "[Restored from ... merge]" is a bookkeeping placeholder, not a summary: never show it.
                    "summary": "" if str(s.get("one_sentence_summary", "")).startswith("[") else s.get("one_sentence_summary", ""),
                    # ref + index locate a segment exactly, so feedback on one can be traced to the source.
                    "segments": [{"ref": r, "i": g.get("index"), "he": clean(g.get("hebrew")), "en": clean(g.get("english"))}
                                 for r, g in segs],
                })
    return apply_extensions(tractate, stories, pages)


EXT = DATA_EXT = ROOT / "site" / "data" / "boundary_extensions.json"
MAX_BACK, MAX_FWD = 2, 4


def apply_extensions(tractate, stories, pages):
    """Display-only: widen a cut-off story by whole neighbouring segments (never the golden).

    site/data/boundary_extensions.json: {story_id: {start_back, end_forward, reason}}, produced by
    reviewing each cut-off story against its real neighbouring segments. Ids, tiers and the
    golden are untouched; an extended story says so (`extended`), so the page can tell the reader.
    """
    if not EXT.exists():
        return stories
    ext = json.loads(EXT.read_text())
    flat = [(p["ref"], g) for p in pages for g in p["segments"]]
    pos = {(r, g.get("index")): k for k, (r, g) in enumerate(flat)}
    for s in stories:
        e = ext.get(s["id"])
        if not e or not (e.get("start_back") or e.get("end_forward")):
            continue
        sb, ef = int(e.get("start_back") or 0), int(e.get("end_forward") or 0)
        assert 0 <= sb <= MAX_BACK and 0 <= ef <= MAX_FWD, (s["id"], sb, ef)
        a, z = s["segments"][0], s["segments"][-1]
        ka, kz = pos[(a["ref"], a["i"])], pos[(z["ref"], z["i"])]
        lo, hi = max(0, ka - sb), min(len(flat) - 1, kz + ef)
        s["segments"] = [{"ref": r, "i": g.get("index"), "he": clean(g.get("hebrew")), "en": clean(g.get("english"))}
                         for r, g in flat[lo:hi + 1]]
        s["extended"] = {"start_back": ka - lo, "end_forward": hi - kz, "reason": cap_reason(e.get("reason"))}
        s["refs"] = list(dict.fromkeys(g["ref"] for g in s["segments"]))
    return stories


CONFIG = ROOT / "site" / "config.js"


def reading_wpm():
    """Reading speed lives in ONE place, site/config.js (`readingWpm`), so the page and the export agree."""
    m = re.search(r"readingWpm:\s*(\d+)", CONFIG.read_text())
    assert m, "site/config.js must set readingWpm"
    return int(m.group(1))


def add_reading_time(stories, wpm):
    """`words` = whitespace tokens of the English with HTML stripped, over the segments the reader is shown
    (so after any display extension). `minutes` = ceil(words / wpm), minimum 1 (septimus-signup-plan.md §2)."""
    for s in stories:
        s["words"] = sum(len(TAG.sub(" ", g["en"]).split()) for g in s["segments"])
        s["minutes"] = max(1, math.ceil(s["words"] / wpm))
    return stories


def cap_reason(r):
    return str(r or "")[:300]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    wpm = reading_wpm()
    index = {"reading_wpm": wpm, "tractates": []}
    for t, (path, reviewed) in SOURCES.items():
        stories = add_reading_time(build(t, path, reviewed), wpm)
        ids = [s["id"] for s in stories]
        assert len(ids) == len(set(ids)), f"{t}: duplicate story ids"
        (OUT / f"{t}.json").write_text(json.dumps({"tractate": t, "reviewed": reviewed, "stories": stories},
                                                  ensure_ascii=False, indent=1))
        n = {k: sum(1 for s in stories if s["tier"] == k) for k in ("story", "borderline")}
        words, minutes = sum(s["words"] for s in stories), sum(s["minutes"] for s in stories)
        index["tractates"].append({"tractate": t, "reviewed": reviewed, **n, "in_mishnah": sum(1 for s in stories if s["in_mishnah"]),
                                   "words": words, "minutes": minutes})
        print(f"{t:10} story={n['story']:4} borderline={n['borderline']:3} reviewed={reviewed} "
              f"in_mishnah={index['tractates'][-1]['in_mishnah']} words={words} minutes={minutes}")
    (OUT / "index.json").write_text(json.dumps(index, indent=1))


if __name__ == "__main__":
    main()
