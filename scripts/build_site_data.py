#!/usr/bin/env python3
"""Export the stories for the Septimus family viewer (work/2026-10-12-septimus-story-viewer.md).

THE FILTER IS docs/technical/septimus-story-filter.md -- read it before changing anything here.
In one line: **only definite stories reach the site.** It is a PUBLICATION filter, stricter than
the scholarly catalogue, and it never writes back: goldens, detector runs and judge outputs are
read-only here, and borderlines and maybes stay in the scholarly work where they matter.

    reviewed tractate (Jeff's golden)  -> his YES / HIGH_CONFIDENCE in stories[] only
    unreviewed tractate (detector)     -> YES / HIGH_CONFIDENCE in EVERY run listed, in stories[],
                                          AND both consensus judges call the passage a story

Never shipped: BORDERLINE (Simon 2026-10-15), LOW_CONFIDENCE (2026-10-12), NOT_A_STORY,
mishnah_stories[] (Stage 4g withheld them; never shown to Jeff, never judged), and a judge
`out_of_scope` (biblical, R-S1). A second gate may narrow, never promote (Lesson 45).

Hebrew already carries nikud in the cached Sefaria segments; coverage is asserted below.
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "data"

# runs: the first is exported (its boundaries and summaries are shown); every run must agree.
# consensus: results/consensus/<tractate> (judge_detector_spans.py), None for a reviewed golden.
SOURCES = {
    "ketubot": {"runs": ["results/canonical/ketubot_canonical.json"], "reviewed": True, "consensus": None},
    "kiddushin": {"runs": ["results/canonical/kiddushin_canonical.json"], "reviewed": True, "consensus": None},
    "gittin": {"runs": ["results/canonical/gittin_canonical.json"], "reviewed": True, "consensus": None},
    "yevamot": {"runs": ["results/v11/v14_yevamot/run1.json", "results/v11/v14_yevamot/run2.json"],
                "reviewed": False, "consensus": "results/consensus/yevamot"},
    "berakhot": {"runs": ["results/v14/berakhot/run1.json", "results/v14/berakhot/run2.json"],
                 "reviewed": False, "consensus": "results/consensus/berakhot"},
}
DEFINITE = ("YES", "HIGH_CONFIDENCE")


def definite_cells(path):
    """Cells of YES/HIGH_CONFIDENCE spans in stories[] (never mishnah_stories) of one run."""
    pages = json.loads((ROOT / path).read_text())["pages"]
    return {(r, g.get("index")) for i, p in enumerate(pages) for s in p.get("stories", [])
            if s.get("classification") in DEFINITE for r, gs in pieces(pages, i, s) for g in gs}


def strong_yes_cells(tractate):
    """Cells (page ref, segment index) of units BOTH judges call `story`; None = no judge gate."""
    d = SOURCES[tractate]["consensus"]
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
    """Only definite stories ship: BORDERLINE, LOW_CONFIDENCE and NOT_A_STORY never do."""
    return "story" if classification in DEFINITE else None


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


def build(tractate):
    src = SOURCES[tractate]
    reviewed = src["reviewed"]
    pages = json.loads((ROOT / src["runs"][0]).read_text())["pages"]
    strong = strong_yes_cells(tractate)
    others = [definite_cells(q) for q in src["runs"][1:]]
    stories = []
    for i, p in enumerate(pages):
        for s in p.get("stories", []):           # never mishnah_stories[]: withheld, unreviewed, unjudged
            t = tier(s.get("classification"))
            ps = pieces(pages, i, s)
            segs = [(r, g) for r, gs in ps for g in gs]
            assert segs, (tractate, p["ref"], s)
            cells = {(r, g.get("index")) for r, g in segs}
            # Gates may only NARROW the detector's/golden's own `story` tier, never promote (Lesson 45).
            if strong is not None and not cells & strong:
                t = None   # not a story to BOTH judges
            if any(not cells & o for o in others):
                t = None   # below YES/HIGH (or absent) in another run: the detector is not deterministic
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
                "in_mishnah": False,   # mishnah_stories[] never ship (kept for the page's schema)
                "extended": None,
                "reviewed": reviewed,
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
    for t in SOURCES:
        reviewed = SOURCES[t]["reviewed"]
        stories = add_reading_time(build(t), wpm)
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
