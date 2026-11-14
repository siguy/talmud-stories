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
the detector stories Jeff calls yes. They stay in the scholarly work -- except for one narrowing: a passage Gemini
calls `out_of_scope` and Claude calls `not` (not a story at all) does not ship (Simon 2026-11-10).

Biblical stories are OUT OF SCOPE for the site (Simon 2026-11-13, reversing 2026-11-10, to stay consistent with
Jeff's R-S1). They are still found and flagged `biblical: true` -- both judges' `out_of_scope`, Claude alone under
decisions.json, a hand flag in decisions.json, and Stage 4j's own biblical-actor demotion (whose pre-filter grade is
what the site reads) -- but they are written to each tractate file's `out_of_scope` list, with the reason, never to
`stories`. A later filter may surface them; the default list does not.

Per-passage decisions (results/shas_run/septimus_site_decisions.json, each with who decided and when):
  remove   -- Jeff ruled not / borderline on a passage the site shipped; matched by span OVERLAP (Lesson 36)
  include  -- an expert `story` verdict plus Simon's yes on a passage the filter held back (Sanhedrin 52b:4).
              The only way past the definite-only filter, by name, never a rule. On the site it reads like any
              other story of its tractate (Simon 2026-11-13: "just count it as a regular story"): no badge, no
              `reviewed`, no provenance field. Who decided lives in the decisions file, and the build names it.
  promote  -- a RULE over a graded pool, by owner decision (Simon 2026-11-14): every passage both Claude grader
              passes call `story` (results/shas_run/low_pool/pool/promotions.json, judge prompt sha 88e8fff62716,
              calibrated 32/33 vs Jeff) ships, carrying `included_by` so the batch can be filtered or removed in one
              step. Still narrowed by every exclusion above; dropped ones are named on stderr. Model-graded, never
              read back into a golden, ruler or expert list.
A decision that matches nothing is named on stderr.

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
SITE_HELD = ()   # Eruvin was held (plan §7 Q4) until Simon's 2026-11-09 decision: it ships like every other tractate
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

SITE_DECISIONS = "results/shas_run/septimus_site_decisions.json"


def site_decisions():
    """Simon's site decisions: (biblical ships?, {tractate: [remove entries]}, {tractate: [include entries]})."""
    d = json.loads((ROOT / SITE_DECISIONS).read_text())
    by = lambda k: {t: [e for e in d[k]["passages"] if e["tractate"] == t] for t in {e["tractate"] for e in d[k]["passages"]}}
    return d["biblical"]["ships"], by("remove"), by("include")


def promotion_rules():
    """The `promote` rules of the site decisions, each checked against its source file: the build refuses if the
    file's ids, count or judge prompt sha differ from what Simon approved (a regraded pool must not ship silently)."""
    d = json.loads((ROOT / SITE_DECISIONS).read_text()).get("promote", {"rules": []})
    out = []
    for r in d["rules"]:
        src = json.loads((ROOT / r["source"]).read_text())
        ids = [p["id"] for p in src["promotions"]]
        if ids != r["ids"] or len(ids) != r["count"] or src["meta"]["judge_prompt_sha"] != r["judge_prompt_sha"]:
            raise SystemExit(f"site build refused: {r['source']} no longer matches the `promote` rule "
                             f"{r['included_by']} (ids, count or judge prompt sha changed)")
        out.append((r, src["promotions"]))
    return out


def run_spans(path):
    """[(key, story, cells)] of every span in one run, stories[] and mishnah_stories[] alike."""
    pages = json.loads((ROOT / path).read_text())["pages"]
    return [(k, s, {(r, g.get("index")) for r, gs in pieces(pages, i, s) for g in gs})
            for i, p in enumerate(pages) for k in ("stories", "mishnah_stories") for s in p.get(k, [])]


def promoted(tractate, taken, removals, biblical, drop, matched):
    """Stories added by the `promote` rules for one tractate (Simon 2026-11-14). Bounds: the pool unit's cells -- the
    detector span the grade refers to, never the grader's chosen segments (every other site story is bounded by a
    detector span). Summary: the detector's reader-facing summary of the SAME passage, run 1 then run 2, else none --
    never the grader's reason. A promotion is DROPPED, and named, when it overlaps a story already built (shipped or
    out of scope), a `remove` decision, a biblical or judge-drop cell, a Stage 4j biblical span or a withheld Mishnah
    story in either run."""
    src = SOURCES[tractate]
    rules = [(r, [p for p in ps if p["slug"] == tractate]) for r, ps in promotion_rules()]
    rules = [(r, ps) for r, ps in rules if ps]
    if not rules:
        return []
    if src["reviewed"]:
        raise SystemExit(f"site build refused: a promotion names reviewed tractate {tractate}; Jeff's evidence rules there")
    pages = json.loads((ROOT / src["runs"][0]).read_text())["pages"]
    seg = {(p["ref"], g.get("index")): g for p in pages for g in p["segments"]}
    spans = [x for q in src["runs"] for x in run_spans(q)]
    out = []
    for r, ps in rules:
        for u in ps:
            cells = [tuple(c) for c in u["cells"]]
            cs = set(cells)
            why = ("overlaps a story already built" if cs & taken else
                   "overlaps a `remove` decision" if any(cs & decision_cells(e) for e in removals) else
                   "biblical (consensus judges)" if cs & biblical else
                   "judges: not a story" if cs & drop else
                   "Stage 4j biblical span" if any(cs & c and s.get("filtered_as_biblical") for _, s, c in spans) else
                   "withheld Mishnah story" if any(cs & c and k == "mishnah_stories" for k, _, c in spans) else None)
            missing = [c for c in cells if c not in seg]
            if missing:
                raise SystemExit(f"site build refused: promotion {u['id']} has cells outside the text {missing[:3]}")
            if why:
                matched.append(("promote-dropped", (r["included_by"], u["id"], why), None))
                continue
            ref, a = cells[0]
            b = max(i for rr, i in cells if rr == ref)
            sid = f"{tractate}-{ref.split()[-1]}-{a}-{b}"
            same = [s for _, s, c in spans if c == cs and is_reader_summary(s)]
            segs = [(c[0], seg[c]) for c in cells]
            if not NIKUD.search("".join(g.get("hebrew") or "" for _, g in segs)):
                print(f"  no nikud: {tractate} {u['id']}", file=sys.stderr)
            matched.append(("promote", (r["included_by"], u["id"]), sid))
            out.append({
                "id": sid, "tractate": tractate, "ref": ref, "refs": list(dict.fromkeys(c[0] for c in cells)),
                "start_segment": a, "tier": "story",
                # the detector's best grade across the two runs (the pool is LOW in at least one)
                "classification": next((x for x in ("YES", "HIGH_CONFIDENCE", "LOW_CONFIDENCE") if x in (u["run1"], u["run2"])),
                                       u["run1"]),
                "biblical": False, "biblical_reason": None, "in_mishnah": False, "extended": None,
                "reviewed": src["reviewed"],
                "summary": same[0]["one_sentence_summary"] if same else "",
                # provenance: the whole batch can be filtered or removed in one step (septimus_site_decisions.json)
                "included_by": r["included_by"],
                "segments": [{"ref": rr, "i": g.get("index"), "he": clean(g.get("hebrew")), "en": clean(g.get("english"))}
                             for rr, g in segs],
            })
    return out


def decision_cells(e):
    """Cells of a decision's span on its page (single-page spans; that is all a decision names today)."""
    return {(e["ref"], i) for i in range(int(e["start_segment"]), int(e["end_segment"]) + 1)}


def judge_cells(tractate):
    """(biblical, drop): cells to FLAG as biblical (R-S1; out of scope for the site and Jeff's catalogue since 2026-11-13) and cells to DROP
    (Gemini says out_of_scope, Claude says `not`: not a story at all -- the one narrowing, Simon 2026-11-10)."""
    d = SOURCES[tractate].get("scope_judges")
    if not d:
        return set(), set()
    verdict = {m: {r["id"]: r["answer"].get("verdict") for r in json.loads((ROOT / d / f"{m}.json").read_text())["rows"]
                   if r["answer"].get("outcome") == "ok"} for m in ("gemini", "claude")}
    # Claude only judges Gemini's out_of_scope units, so a flagged unit with no valid Claude answer would read as
    # "a story, not biblical" and ship unflagged (Lesson 21/38: absence reads as a decision). Refuse, naming them.
    # Units the Gemini judge could not answer validly twice: Claude decides alone (Simon, 2026-11-10).
    import check_tractate_run as C
    alone = set(C.decisions(ROOT)[1].get(tractate, []))
    hand = set(C.decisions(ROOT)[2].get(tractate, []))
    unanswered = sorted(i for i, v in verdict["gemini"].items() if v == "out_of_scope" and i not in verdict["claude"])
    unanswered += sorted(alone - set(verdict["claude"]))
    if unanswered:
        raise SystemExit(f"site build refused: {tractate}: {len(unanswered)} unit(s) Gemini called out_of_scope "
                         f"have no Claude answer with outcome ok: {unanswered[:8]}")
    units = json.loads((ROOT / d / "units.json").read_text())["units"]
    flagged = lambda u: verdict["gemini"].get(u["id"]) == "out_of_scope" or u["id"] in alone
    biblical = {tuple(c) for u in units for c in u["cells"]
                if (flagged(u) and verdict["claude"].get(u["id"]) == "out_of_scope") or u["id"] in hand}
    drop = {tuple(c) for u in units for c in u["cells"] if flagged(u) and verdict["claude"].get(u["id"]) == "not"}
    return biblical, drop


def site_classification(s):
    """The grade the site reads. Stage 4j demotes a story whose actors are only biblical; the site reads the
    grade from before that filter and flags the story, so it is kept in `out_of_scope` (Simon 2026-11-13) rather than
    lost as a LOW."""
    if s.get("filtered_as_biblical"):
        return s.get("classification_pre_biblical_filter")
    return s.get("classification")


DEFINITE = ("YES", "HIGH_CONFIDENCE")


def definite_cells(path):
    """Cells of YES/HIGH_CONFIDENCE spans in stories[] (never mishnah_stories) of one run."""
    pages = json.loads((ROOT / path).read_text())["pages"]
    return {(r, g.get("index")) for i, p in enumerate(pages) for s in p.get("stories", [])
            if site_classification(s) in DEFINITE for r, gs in pieces(pages, i, s) for g in gs}


# Golden-entry fields that record Jeff's own answer on that entry (later rounds than the ruler reads).
JEFF_FIELDS = ("review_verdict", "label_source", "expert_answer", "source")


def is_reader_summary(s):
    """True when a story's `one_sentence_summary` is written for a reader. Two kinds are pipeline text and never shown:
    "[Restored from ... merge]" bookkeeping placeholders, and every twin-pass addition's -- story_detector_v14
    `_find_adjacent_twins` copies the twin judge's `reason` into it ("Passage B is a distinct incident ..."): the
    model's argument that the segment is a separate story, not a summary of it."""
    text = str(s.get("one_sentence_summary") or "")
    return bool(text) and not text.startswith("[") and s.get("source") != "twin_pass"


def reader_summaries(path):
    """{frozenset(cells): reader-facing summary} for the stories[] of one run -- the source of a card's summary when
    the exported run has none for the SAME passage (identical cells; an overlapping story is a different passage)."""
    pages = json.loads((ROOT / path).read_text())["pages"]
    out = {}
    for i, p in enumerate(pages):
        for s in p.get("stories", []):
            if is_reader_summary(s):
                out.setdefault(frozenset((r, g.get("index")) for r, gs in pieces(pages, i, s) for g in gs),
                               s["one_sentence_summary"])
    return out


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


def build(tractate, matched=None):
    """(stories, out_of_scope). `matched` collects (decision kind, entry, story id) for the build's report."""
    matched = [] if matched is None else matched
    _, removals, inclusions = site_decisions()
    removals, inclusions = removals.get(tractate, []), inclusions.get(tractate, [])
    src = SOURCES[tractate]
    reviewed = src["reviewed"]
    pages = json.loads((ROOT / src["runs"][0]).read_text())["pages"]
    jeff = jeff_evidence_cells(tractate) if reviewed else None
    biblical, drop = judge_cells(tractate)
    others = [definite_cells(q) for q in src["runs"][1:]]
    other_summaries = [reader_summaries(q) for q in src["runs"][1:]]
    stories, seen = [], set()
    for i, p in enumerate(pages):
        for s in p.get("stories", []):           # never mishnah_stories[]: withheld, unreviewed, unjudged
            t = tier(site_classification(s))
            ps = pieces(pages, i, s)
            segs = [(r, g) for r, gs in ps for g in gs]
            assert segs, (tractate, p["ref"], s)
            cells = {(r, g.get("index")) for r, g in segs}
            include = [e for e in inclusions if cells & decision_cells(e)]
            # Gates may only NARROW the detector's/golden's own `story` tier, never promote (Lesson 45).
            if jeff is not None and not cells & jeff and not any(s.get(k) for k in JEFF_FIELDS):
                t = None   # in the golden, but a detector call Jeff never answered
            if cells & drop:
                t = None   # Gemini says biblical, Claude says not a story at all (Simon 2026-11-10)
            if any(not cells & o for o in others):
                t = None   # below YES/HIGH (or absent) in another run: the detector is not deterministic
            sid = f"{tractate}-{p['ref'].split()[-1]}-{s['start_segment']}-{s['end_segment']}"
            if include:
                t = "story"   # an explicit per-passage decision (expert `story` + Simon), never a rule
                matched += [("include", e, sid) for e in include]
            remove = [e for e in removals if cells & decision_cells(e)]
            if remove and t is not None:
                matched += [("remove", e, sid) for e in remove]
                t = None   # Jeff ruled not / borderline (2026-11-12); the site ships definite stories only
            if t is None:
                continue
            if sid in seen:
                # The detector can propose the identical span twice (Yevamot 15a:16, v14 run1). One passage
                # is one story on the site; the duplicate is counted and named, never silently dropped.
                print(f"  duplicate span, shipped once: {sid}", file=sys.stderr)
                continue
            seen.add(sid)
            # The card's summary: the exported run's own when it is reader-facing, else the same passage's in another
            # run, else none -- the page then shows no summary line. Never invented (no model call here).
            summary = s["one_sentence_summary"] if is_reader_summary(s) else next(
                (o[frozenset(cells)] for o in other_summaries if frozenset(cells) in o), "")
            if not NIKUD.search("".join(g.get("hebrew") or "" for _, g in segs)):
                print(f"  no nikud: {tractate} {p['ref']} {s['start_segment']}", file=sys.stderr)
            stories.append({
                "id": sid,
                "tractate": tractate,
                "ref": p["ref"],
                "refs": [r for r, _ in ps],
                "start_segment": int(s["start_segment"]),
                "tier": t,
                "classification": site_classification(s),
                # Biblical characters (R-S1): out of scope for the site and Jeff's catalogue (Simon 2026-11-13).
                "biblical": bool(cells & biblical) or bool(s.get("filtered_as_biblical")),
                "biblical_reason": ("consensus judges / decisions.json" if cells & biblical else
                                    "Stage 4j biblical-actor filter" if s.get("filtered_as_biblical") else None),
                "in_mishnah": False,   # mishnah_stories[] never ship (kept for the page's schema)
                "extended": None,
                # the tractate's own state: an included passage reads as a regular story (Simon 2026-11-13);
                # its provenance stays in septimus_site_decisions.json, never on the card
                "reviewed": reviewed,
                "summary": summary,
                # ref + index locate a segment exactly, so feedback on one can be traced to the source.
                "segments": [{"ref": r, "i": g.get("index"), "he": clean(g.get("hebrew")), "en": clean(g.get("english"))}
                             for r, g in segs],
            })
    taken = {(g["ref"], g["i"]) for x in stories for g in x["segments"]}
    stories += promoted(tractate, taken, removals, biblical, drop, matched)
    order = {(p["ref"], g.get("index")): k for k, (p, g) in enumerate((p, g) for p in pages for g in p["segments"])}
    stories.sort(key=lambda x: order[(x["segments"][0]["ref"], x["segments"][0]["i"])])   # page order, promoted in place
    stories = apply_extensions(tractate, stories, pages)
    if site_decisions()[0]:
        return stories, []
    # Simon 2026-11-13: biblical stories are out of scope for the site. Kept, with the reason, for a later filter.
    out = [dict(s, out_of_scope_reason=f"biblical (R-S1): {s['biblical_reason']}; Simon 2026-11-13")
           for s in stories if s["biblical"]]
    return [s for s in stories if not s["biblical"]], out


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
        for r in [C.g3_run(P, 1), C.g3_run(P, 2), C.g4_pair(P), C.g6_judge(P, "gemini"), C.g6_judge(P, "claude")]:
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
    matched = []
    for t in SOURCES:
        reviewed = SOURCES[t]["reviewed"]
        stories, out_of_scope = build(t, matched)
        stories, out_of_scope = add_reading_time(stories, wpm), add_reading_time(out_of_scope, wpm)
        ids = [s["id"] for s in stories + out_of_scope]
        assert len(ids) == len(set(ids)), f"{t}: duplicate story ids (or a story both shipped and out of scope)"
        # `stories` is what the site shows. `out_of_scope` is retained, never shown by default (Simon 2026-11-13).
        (OUT / f"{t}.json").write_text(json.dumps({"tractate": t, "reviewed": reviewed, "stories": stories,
                                                   "out_of_scope": out_of_scope}, ensure_ascii=False, indent=1))
        n = {k: sum(1 for s in stories if s["tier"] == k) for k in ("story", "borderline")}
        words, minutes = sum(s["words"] for s in stories), sum(s["minutes"] for s in stories)
        index["tractates"].append({"tractate": t, "name": T.english(t), "he": T.hebrew(t), "reviewed": reviewed, **n, "in_mishnah": sum(1 for s in stories if s["in_mishnah"]),
                                   "out_of_scope": len(out_of_scope), "words": words, "minutes": minutes})
        print(f"{t:10} story={n['story']:4} borderline={n['borderline']:3} reviewed={reviewed} "
              f"in_mishnah={index['tractates'][-1]['in_mishnah']} out_of_scope={len(out_of_scope)} "
              f"words={words} minutes={minutes}")
    (OUT / "index.json").write_text(json.dumps(index, indent=1))
    report_decisions(matched)


def report_decisions(matched):
    """Name every per-passage decision and the story it matched; a decision that matched nothing is named too."""
    _, removals, inclusions = site_decisions()
    for kind, entries in (("remove", removals), ("include", inclusions)):
        for e in (e for es in entries.values() for e in es):
            hits = [sid for k, m, sid in matched if k == kind and m == e]
            span = f"{e['ref']}:{e['start_segment']}-{e['end_segment']}"
            print(f"  {kind:7} {span:22} -> {', '.join(hits) if hits else 'NO MATCH (not shipped by the filter)'}",
                  file=sys.stderr)
    for r, ps in promotion_rules():
        added = [sid for k, m, sid in matched if k == "promote" and m[0] == r["included_by"]]
        dropped = [m for k, m, _ in matched if k == "promote-dropped" and m[0] == r["included_by"]]
        print(f"  promote {r['included_by']}: {len(added)} of {len(ps)} added, {len(dropped)} dropped", file=sys.stderr)
        for _, uid, why in dropped:
            print(f"    dropped {uid}: {why}", file=sys.stderr)
        unbuilt = len(ps) - len(added) - len(dropped)
        if unbuilt:
            print(f"    NOT BUILT {unbuilt}: their tractate is not on the site", file=sys.stderr)


if __name__ == "__main__":
    main()
