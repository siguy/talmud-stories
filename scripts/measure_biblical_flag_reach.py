#!/usr/bin/env python3
"""The reach of detector v15's biblical-actor rule (Stage 4j) against v14's, on every run on disk (Lesson 27).

No model calls: the rule reads `criteria.identifiable_characters.evidence`, which every run already holds.
For every story in stories[] of every run the site reads (the reviewed goldens, Yevamot's v14 runs, every
results/v14/<t>/run{1,2}.json), it records:
  - v14 / v15  : the two rules applied to the same evidence string
  - judges     : the story overlaps a unit the site flags biblical from the judges (both out_of_scope, Claude alone,
                 or a hand flag in results/shas_run/decisions.json) -- build_site_data.judge_cells()
  - gemini_oos : the story overlaps a unit the Gemini judge alone called out_of_scope (Claude may have said `not`,
                 which drops it from the site, or `story`, which ships it unflagged)
  - jeff_yes   : (reviewed tractates) the story overlaps a passage Jeff said yes to or listed in 2005
  - definite   : the grade the site reads is YES / HIGH_CONFIDENCE

    python3 scripts/measure_biblical_flag_reach.py            # summary + every changed story
    python3 scripts/measure_biblical_flag_reach.py --json OUT # also the per-story rows

Stories graded NOT_A_STORY before 4j are left out: neither rule can put them on the site.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import build_site_data as B  # noqa: E402
from src import story_detector_v14 as V14  # noqa: E402
from src import story_detector_v15 as V15  # noqa: E402


def gemini_oos_cells(t):
    d = B.SOURCES[t].get("scope_judges")
    if not d:
        return set()
    g = {r["id"] for r in json.loads((ROOT / d / "gemini.json").read_text())["rows"]
         if r["answer"].get("outcome") == "ok" and r["answer"].get("verdict") == "out_of_scope"}
    return {tuple(c) for u in json.loads((ROOT / d / "units.json").read_text())["units"] if u["id"] in g
            for c in u["cells"]}


def rows():
    out = []
    for t, src in B.SOURCES.items():
        biblical, _ = B.judge_cells(t)
        gem = gemini_oos_cells(t)
        jeff = B.jeff_evidence_cells(t) if src["reviewed"] else set()
        for k, run in enumerate(src["runs"], 1):
            pages = json.loads((ROOT / run).read_text())["pages"]
            for i, p in enumerate(pages):
                for s in p.get("stories", []):
                    grade = B.site_classification(s)
                    if grade in (None, "NOT_A_STORY"):
                        continue
                    ev = V15.story_evidence(s)
                    cells = {(r, g.get("index")) for r, gs in B.pieces(pages, i, s) for g in gs}
                    out.append({
                        "tractate": t, "run": k, "ref": p["ref"],
                        "span": f"{s['start_segment']}-{s['end_segment']}",
                        "grade": grade, "definite": grade in B.DEFINITE,
                        "evidence": ev, "kinds": V15._evidence_kinds(ev) if ev else [],
                        "v14": bool(s.get("filtered_as_biblical")) or V14._actors_are_biblical_only(ev),
                        "v15": V15.biblical_flag(ev),
                        "judges": bool(cells & biblical), "gemini_oos": bool(cells & gem), "jeff_yes": bool(cells & jeff),
                        "reviewed": src["reviewed"],
                        "summary": s.get("one_sentence_summary", ""),
                    })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args()
    R = rows()
    c = Counter()
    for r in R:
        c["stories"] += 1
        c[f"v14={r['v14']:d} v15={r['v15']:d}"] += 1
        if r["definite"]:
            c[f"definite v14={r['v14']:d} v15={r['v15']:d}"] += 1
        if r["v15"] and r["jeff_yes"]:
            c["v15 flags a passage Jeff said yes to"] += 1
        if r["judges"]:
            c[f"judges flag: v14={r['v14']:d} v15={r['v15']:d}"] += 1
        if r["v15"] and not r["judges"]:
            c["v15 flags, judges do not"] += 1
            c[f"v15 flags, judges do not: gemini out_of_scope={r['gemini_oos']:d}"] += 1
    for k in sorted(c):
        print(f"{c[k]:6}  {k}")
    for title, f in (("NEWLY FLAGGED by v15", lambda r: r["v15"] and not r["v14"]),
                     ("UNFLAGGED by v15", lambda r: r["v14"] and not r["v15"]),
                     ("v15 flags a passage Jeff said yes to", lambda r: r["v15"] and r["jeff_yes"]),
                     ("judges flag, v15 does not", lambda r: r["judges"] and not r["v15"])):
        sel = [r for r in R if f(r)]
        print(f"\n== {title}: {len(sel)} (definite {sum(r['definite'] for r in sel)})")
        for r in sel:
            print(f"  {r['tractate']} r{r['run']} {r['ref']}:{r['span']} {r['grade']} j={r['judges']:d} g={r['gemini_oos']:d} "
                  f"| {r['evidence']} | {r['summary'][:110]}")
    if a.json:
        Path(a.json).write_text(json.dumps(R, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
