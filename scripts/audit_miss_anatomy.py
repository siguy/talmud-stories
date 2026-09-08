#!/usr/bin/env python3
"""Anatomy of every expert-list miss: what failed, and where on the daf.

Answers two questions the pooled recall figure cannot:

  1. Is the "detection is worst where a story stands alone" profile real, or is it
     Triage's losses charged to Detection? Separates *isolation* (how many of Jeff's
     stories share the daf) from *context* (whether the REST of the daf carries any
     narrative segment at all, per the cached Stage 1 labels) -- the confound the
     2026-09-03 density finding named and could not break.

  2. For every miss, how far away is the nearest thing the detector actually proposed?
     A miss with a proposal one segment away is a different defect from a miss with
     nothing on the daf, and the two want opposite fixes.

No API calls: reads the shipped runs, the cached triage labels and the exact-anchor
recall output. Every miss is classified into exactly one bucket, and the buckets sum
to the misses (Lesson 21's shape: a partition that does not sum is not a partition).

    python3 scripts/audit_miss_anatomy.py --out results/recall/miss_anatomy.json
"""
import argparse
import collections
import json
import re
from pathlib import Path

# The shipped run per tractate -- the same artifacts the recall harness scores.
RUNS = {
    "ketubot": [
        "results/v10/wave4_notrim/ketubot_v10_2-60_notrim.json",
        "results/v10/wave4_notrim/ketubot_v10_61-112_notrim.json",
    ],
    "kiddushin": ["results/v10/wave4_notrim/kiddushin_v10_notrim.json"],
    "gittin": ["results/v11/gittin/gittin_v11.json"],
    "yevamot": ["results/v11/yevamot/yevamot_v11.json"],
}
# Cached Stage 1 labels. These are per-segment and per-daf; they are the only
# committed measure of "how much of this daf is legal argument".
TRIAGE = {
    "ketubot": ["results/v7/event_triage_2-60.json", "results/v7/event_triage_61-112.json"],
    "kiddushin": ["results/v7/event_triage_kiddushin.json"],
    "gittin": ["results/triage/gittin.json"],
    "yevamot": ["results/triage/yevamot.json"],
}
NARRATIVE_LABELS = {"NARRATIVE_EVENT", "HABITUAL"}


def load_triage(tractate):
    out = {}
    for path in TRIAGE[tractate]:
        blob = json.loads(Path(path).read_text())
        out.update(blob.get("triage_results", blob))
    return out


def load_run(tractate):
    """Proposals and segment text per daf.

    Reads `mishnah_stories` deliberately and tags it: a story Stage 4g withheld was
    FOUND and then removed, which is a different answer from never proposed (Lesson 27).
    """
    proposals, segments = collections.defaultdict(list), {}
    for path in RUNS[tractate]:
        blob = json.loads(Path(path).read_text())
        for page in blob["pages"] if isinstance(blob, dict) else blob:
            ref = page["ref"]
            segments[ref] = page.get("segments") or []
            for key in ("stories", "mishnah_stories"):
                for story in page.get(key) or []:
                    proposals[ref].append((
                        story.get("start_segment", story.get("start")),
                        story.get("end_segment", story.get("end")),
                        story.get("classification") or story.get("label"),
                        key,
                    ))
    return proposals, segments


def classify(story, proposals):
    """One bucket per miss. Distance is in segments, 0 = overlapping."""
    if story["found"]:
        return "FOUND", None
    if not story["survived_triage"]:
        return "TRIAGE", None
    nearest = None
    for start, end, label, key in proposals:
        if start is None:
            continue
        overlaps = start <= story["end"] and end >= story["start"]
        distance = 0 if overlaps else min(abs(start - story["end"]), abs(end - story["start"]))
        if nearest is None or distance < nearest["distance"]:
            nearest = {"distance": distance, "start": start, "end": end,
                       "label": label, "key": key}
    if nearest is None:
        return "BLANK", None
    if nearest["distance"] == 0 and nearest["key"] == "mishnah_stories":
        return "MISHNAH_WITHHELD", nearest
    if nearest["distance"] <= 1:
        return "ADJACENT", nearest
    if nearest["distance"] <= 6:
        return "NEAR", nearest
    return "FAR", nearest


def build(tractates):
    rows = []
    for tractate in tractates:
        triage = load_triage(tractate)
        proposals, segments = load_run(tractate)
        expert = json.loads(Path(f"results/recall/{tractate}_jeff2005_matches.json").read_text())
        located = [s for s in expert if s.get("located")]
        per_daf = collections.Counter(s["located"][0][0] for s in located)

        # Segments belonging to ANY expert story on the daf, so that "context" measures
        # the daf around the stories rather than the stories themselves. Without this
        # the density measure is partly caused by the very stories it is predicting.
        own = collections.defaultdict(set)
        for s in located:
            for i in range(s["located"][0][1], max(s["located"][0][1], s["located"][1][1]) + 1):
                own[s["located"][0][0]].add(i)

        for s in located:
            ref, start = s["located"][0]
            end = s["located"][1][1]
            labels = triage.get(ref) or []
            context = [l for i, l in enumerate(labels) if i not in own[ref]]
            row = {
                "tractate": tractate, "ref": ref, "start": start, "end": end,
                "words": s["words"], "text": s["text"],
                "found": bool(s.get("in_detector")),
                "survived_triage": bool(s.get("survived_triage")),
                "expert_stories_on_daf": per_daf[ref],
                "context_segments": len(context),
                "context_narrative_fraction": (
                    sum(1 for l in context if l in NARRATIVE_LABELS) / len(context)
                    if context else None
                ),
                "proposals_on_daf": len(proposals.get(ref, [])),
            }
            row["bucket"], row["nearest_proposal"] = classify(row, proposals.get(ref, []))
            rows.append(row)
    return rows


def report(rows):
    scored = [r for r in rows if r["context_narrative_fraction"] is not None]
    buckets = collections.Counter(r["bucket"] for r in scored)
    assert sum(buckets.values()) == len(scored)

    def cell(r):
        isolation = "alone" if r["expert_stories_on_daf"] == 1 else "multi"
        context = "legal-only" if r["context_narrative_fraction"] == 0 else "has-narrative"
        return f"{isolation} / {context}"

    print(f"{len(scored)} expert stories · {len(scored) - buckets['FOUND']} misses")
    print("  " + "  ".join(f"{k}={v}" for k, v in buckets.most_common() if k != "FOUND"))
    print()
    print("Isolation x context — the split the density finding could not make")
    print(f"  {'cell':24}{'end-to-end':>20}{'given page examined':>24}   misses")
    for name in ("alone / legal-only", "alone / has-narrative",
                 "multi / legal-only", "multi / has-narrative"):
        group = [r for r in scored if cell(r) == name]
        if not group:
            continue
        examined = [r for r in group if r["bucket"] != "TRIAGE"]
        found = sum(1 for r in group if r["found"])
        found_ex = sum(1 for r in examined if r["found"])
        misses = collections.Counter(r["bucket"] for r in group if not r["found"])
        print(f"  {name:24}{100*found/len(group):7.1f}% ({found:3}/{len(group):3})"
              f"{100*found_ex/len(examined):11.1f}% ({found_ex:3}/{len(examined):3})   "
              + " ".join(f"{k}:{v}" for k, v in sorted(misses.items())))
    print()
    print("Proposals produced vs expert stories present, per daf (triage-skipped dapim excluded)")
    by_daf = collections.defaultdict(lambda: [0, 0, 0, 0])
    seen = {}
    for r in scored:
        if r["bucket"] == "TRIAGE":
            seen[(r["tractate"], r["ref"])] = None
    for r in scored:
        key = (r["tractate"], r["ref"])
        if key in seen:
            continue
        band = min(r["expert_stories_on_daf"], 5)
        by_daf[band][2] += r["found"]
        by_daf[band][3] += 1
    dafim = collections.defaultdict(set)
    for r in scored:
        if (r["tractate"], r["ref"]) in seen:
            continue
        band = min(r["expert_stories_on_daf"], 5)
        dafim[band].add((r["tractate"], r["ref"], r["proposals_on_daf"]))
    print(f"  {'expert stories':16}{'dapim':>7}{'mean proposals':>16}{'recall':>10}")
    for band in sorted(dafim):
        group = dafim[band]
        mean = sum(p for _, _, p in group) / len(group)
        _, _, found, total = by_daf[band]
        label = str(band) if band < 5 else "5+"
        print(f"  {label:16}{len(group):>7}{mean:>16.2f}{100*found/total:>9.1f}%")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tractates", nargs="*", default=list(RUNS))
    ap.add_argument("--out")
    args = ap.parse_args()
    rows = build(args.tractates)
    report(rows)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(rows, ensure_ascii=False, indent=1))
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
