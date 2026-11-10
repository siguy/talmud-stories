#!/usr/bin/env python3
"""Export the stories for the Septimus family viewer (work/2026-10-12-septimus-story-viewer.md).

THE FILTER IS docs/technical/septimus-story-filter.md -- read it before changing anything here.
In one line: **only definite stories reach the site.** It is a PUBLICATION filter, stricter than
the scholarly catalogue, and it never writes back: goldens, detector runs and judge outputs are
read-only here, and borderlines and maybes stay in the scholarly work where they matter.

    reviewed tractate (Jeff's golden)  -> YES / HIGH_CONFIDENCE in stories[] WITH Jeff's own evidence
                                          behind it (a yes verdict, or his 2005 list) -- the golden
                                          also carries detector calls he never saw
    unreviewed tractate (detector)     -> YES / HIGH_CONFIDENCE in EVERY run listed, in stories[]

Never shipped: BORDERLINE (Simon 2026-10-15), LOW_CONFIDENCE (2026-10-12), NOT_A_STORY,
mishnah_stories[] (Stage 4g withheld them; never shown to Jeff). A second gate may narrow,
never promote (Lesson 45). The consensus judges are NOT a gate here (Simon 2026-11-09): the
Gemini judge is the detector's own model and adds almost nothing; the Claude judge drops ~13% of
the detector stories Jeff calls yes. They stay in the scholarly work -- except for one narrowing: a passage BOTH judges call
`out_of_scope` (biblical characters, R-S1) does not ship.

Hebrew already carries nikud in the cached Sefaria segments; coverage is asserted below.
"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "data"

sys.path.insert(0, str(ROOT / "scripts"))
import tractates as T  # noqa: E402  (the one slug/English/Hebrew table; file locations by convention)

# runs: the first is exported (its boundaries and summaries are shown); every run must agree.
# ruler: results/rulers/<t>_ruler.json (scripts/build_ruler.py) -- where Jeff's evidence is read.
# The three reviewed tractates are listed by hand (their evidence is Jeff's). Every other tractate
# is "unreviewed": two v14 runs plus the consensus judges' scope answers, at the paths
# scripts/tractates.py gives, so a new tractate needs no edit here.
REVIEWED = {
    "ketubot": {"runs": ["results/canonical/ketubot_canonical.json"], "reviewed": True},
    "kiddushin": {"runs": ["results/canonical/kiddushin_canonical.json"], "reviewed": True},
    "gittin": {"runs": ["results/canonical/gittin_canonical.json"], "reviewed": True},
}
SITE_HELD = ("eruvin",)       # held for Jeff (docs plan §7 Q4): never on the site until Simon says so
EXISTING = ("yevamot", "berakhot")   # shipped before the Shas run; kept in this order after the reviewed three


def unreviewed_source(slug):
    P = T.Paths(slug, ROOT)
    rel = lambda p: str(p.relative_to(ROOT))
    return {"runs": [rel(P.run(1)), rel(P.run(2))], "reviewed": False, "scope_judges": rel(P.consensus)}


def judged(slug):
    """True when both runs and the Gemini judge's answers are on disk: the tractate is ready for the site build."""
    P = T.Paths(slug, ROOT)
    return P.run(1).exists() and P.run(2).exists() and (P.consensus / "gemini.json").exists()


def discover():
    """(sources, skipped): every tractate in the table with both runs and a judge, in the table's order,
    and the ones with a run on disk that are NOT ready (named, never silently dropped)."""
    src = dict(REVIEWED)
    for slug in EXISTING:
        src[slug] = unreviewed_source(slug)
    skipped = []
    for slug in T.SLUGS:
        if slug in src or slug in SITE_HELD:
            continue
        if judged(slug):
            src[slug] = unreviewed_source(slug)
        elif T.Paths(slug, ROOT).run(1).exists() or T.Paths(slug, ROOT).run(2).exists():
            skipped.append(slug)
    return src, skipped


SOURCES, NOT_READY = discover()


def biblical_cells(tractate):
    """Cells of passages BOTH judges call `out_of_scope` (biblical characters, R-S1). The judges are
    used for this one narrowing only -- Jeff excludes biblical stories, and the detector does not."""
    d = SOURCES[tractate].get("scope_judges")
    if not d:
        return set()
    verdict = {m: {r["id"]: r["answer"].get("verdict") for r in json.loads((ROOT / d / f"{m}.json").read_text())["rows"]
                   if r["answer"].get("outcome") == "ok"} for m in ("gemini", "claude")}
    units = json.loads((ROOT / d / "units.json").read_text())["units"]
    return {tuple(c) for u in units
            if verdict["gemini"].get(u["id"]) == verdict["claude"].get(u["id"]) == "out_of_scope" for c in u["cells"]}
DEFINITE = ("YES", "HIGH_CONFIDENCE")


def definite_cells(path):
    """Cells of YES/HIGH_CONFIDENCE spans in stories[] (never mishnah_stories) of one run."""
    pages = json.loads((ROOT / path).read_text())["pages"]
    return {(r, g.get("index")) for i, p in enumerate(pages) for s in p.get("stories", [])
            if s.get("classification") in DEFINITE for r, gs in pieces(pages, i, s) for g in gs}


# Golden-entry fields that record Jeff's own answer on that entry (later rounds than the ruler reads).
JEFF_FIELDS = ("review_verdict", "label_source", "expert_answer", "source")


def jeff_evidence_cells(tractate):
    """Cells Jeff has said yes to: on his 2005 list, or a verdict read as `yes` (scripts/verdict_reading.py,
    via the ruler). Simon's own pre-screen round is not Jeff's and does not count."""
    entries = json.loads((ROOT / f"results/rulers/{tractate}_ruler.json").read_text())["entries"]
    out = set()
    for e in entries:
        yes = any(v.get("read_as") == "yes" and "simon" not in v.get("round", "") for v in e.get("verdicts", []))
        if not (e.get("expert_listed") or yes):
            continue
        out |= {tuple(c) for c in e.get("expert_segments") or []}
        if yes:
            out |= {(r, i) for r, a, b in e.get("detector_span") or [] for i in range(a, b + 1)}
    return out


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
    jeff = jeff_evidence_cells(tractate) if reviewed else None
    biblical = biblical_cells(tractate)
    others = [definite_cells(q) for q in src["runs"][1:]]
    stories, seen = [], set()
    for i, p in enumerate(pages):
        for s in p.get("stories", []):           # never mishnah_stories[]: withheld, unreviewed, unjudged
            t = tier(s.get("classification"))
            ps = pieces(pages, i, s)
            segs = [(r, g) for r, gs in ps for g in gs]
            assert segs, (tractate, p["ref"], s)
            cells = {(r, g.get("index")) for r, g in segs}
            # Gates may only NARROW the detector's/golden's own `story` tier, never promote (Lesson 45).
            if jeff is not None and not cells & jeff and not any(s.get(k) for k in JEFF_FIELDS):
                t = None   # in the golden, but a detector call Jeff never answered
            if cells & biblical:
                t = None   # biblical characters, out of scope (R-S1): both judges say so
            if any(not cells & o for o in others):
                t = None   # below YES/HIGH (or absent) in another run: the detector is not deterministic
            if t is None:
                continue
            sid = f"{tractate}-{p['ref'].split()[-1]}-{s['start_segment']}-{s['end_segment']}"
            if sid in seen:
                # The detector can propose the identical span twice (Yevamot 15a:16, v14 run1). One passage
                # is one story on the site; the duplicate is counted and named, never silently dropped.
                print(f"  duplicate span, shipped once: {sid}", file=sys.stderr)
                continue
            seen.add(sid)
            if not NIKUD.search("".join(g.get("hebrew") or "" for _, g in segs)):
                print(f"  no nikud: {tractate} {p['ref']} {s['start_segment']}", file=sys.stderr)
            stories.append({
                "id": sid,
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


def check_unreviewed_gates():
    """Every unreviewed tractate must have passed its run, pair and judge gates (scripts/check_tractate_run.py).
    A red gate stops the build, naming it: a tractate that failed must not ship by being on disk."""
    import check_tractate_run as C
    bad = []
    for t, src in SOURCES.items():
        if src["reviewed"]:
            continue
        P = T.Paths(t, ROOT)
        for r in [C.g3_run(P, 1), C.g3_run(P, 2), C.g4_pair(P), C.g6_judge(P, "gemini")]:
            if r.status == "red":
                bad.append(f"{t} {r.gate}: {'; '.join(r.failures)[:300]}")
    if bad:
        raise SystemExit("site build refused, a gate is red:\n  " + "\n  ".join(bad))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    wpm = reading_wpm()
    if NOT_READY:
        print(f"NOT on the site (a run exists but not both runs and the Gemini judge): {NOT_READY}", file=sys.stderr)
    check_unreviewed_gates()
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
        index["tractates"].append({"tractate": t, "name": T.english(t), "he": T.hebrew(t), "reviewed": reviewed, **n, "in_mishnah": sum(1 for s in stories if s["in_mishnah"]),
                                   "words": words, "minutes": minutes})
        print(f"{t:10} story={n['story']:4} borderline={n['borderline']:3} reviewed={reviewed} "
              f"in_mishnah={index['tractates'][-1]['in_mishnah']} words={words} minutes={minutes}")
    (OUT / "index.json").write_text(json.dumps(index, indent=1))


if __name__ == "__main__":
    main()
