#!/usr/bin/env python3
"""How many real stories are missing from the Septimus site, and where were they lost?

No model calls. Read-only except --out. Finding: docs/findings/2026-11-13-how-many-stories-we-miss.md

  1. stages    every story on the five expert lists that counts for recall (`--standard current`:
               the 2005 list minus what Jeff has since ruled `not`, results/expert_lists/superseded_by_rule.json)
               is assigned to exactly ONE stage where it was lost -- for the SITE and, separately, for the
               DETECTOR alone. The recall harness (scripts/measure_recall_vs_expert_list.py, exact matcher) runs
               as a subprocess, so this never re-implements make_locator. Joins are by span OVERLAP (Lesson 36).
  2. estimate  site recall on the two v14 tractates with a list (Eruvin, Yevamot) and the 2026-11-12 precision
               sample, extrapolated to every unreviewed tractate's shipped count, with a bootstrap interval. The
               three reviewed tractates (site from goldens) are counted directly.
  3. pool      spans proposed as a story in some run but not shipped (results/consensus/<t>/units.json), by how
               the two runs graded them, and what each candidate ship rule would add.

Usage:
  python3 scripts/measure_site_misses.py --out results/shas_run/accuracy/site_misses.json
"""
import argparse
import json
import logging
import math
import random
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import tractates as T  # noqa: E402
from measure_shas_accuracy import (DEFINITE, harness, load, pieces, unit_order, window)  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [site-misses] %(message)s",
                    handlers=[logging.StreamHandler(sys.stderr), logging.FileHandler(ROOT / "project.log")], force=True)
log = logging.getLogger()

DECISIONS = "results/shas_run/septimus_site_decisions.json"
SAMPLE = {"definite": 54, "n": 60, "source": "docs/findings/2026-11-13-jeff-verdicts-eruvin-and-septimus-sample.md §2"}
SEED = 20261113
DRAWS = 10000

# What each list can tell us, and how far it can be trusted. BLIND = the list was written before any
# detector existed and its labels never reached a prompt; CIRCULAR = they did, or the site is built from them.
LISTS = {
    "eruvin": {"args": ["--expert-json", "results/expert_lists/eruvin_2005.json"], "v14": True,
               "grade": "BLIND, held out: no Eruvin label in any prompt; site from two v14 runs"},
    "yevamot": {"args": ["--expert-json", "results/expert_lists/yevamot_2005.json"], "v14": True,
                "grade": "BLIND list, partly CIRCULAR detector: development tractate for v13/v14 (rules and "
                         "3 few-shot passages from Yevamot); site from two v14 runs"},
    "gittin": {"args": ["--expert-json", "results/expert_lists/gittin_2005.json"], "v14": False,
               "grade": "BLIND list, CIRCULAR site: the golden (and so the site) is built from this list"},
    "kiddushin": {"args": ["--expert-json", "results/expert_lists/kiddushin_2005.json"], "v14": False,
                  "grade": "CIRCULAR: Kiddushin few-shots in the detector; site from a golden built with the list"},
    "ketubot": {"args": ["--expert-doc", "jeff comms/b.ketubot (1).doc"], "v14": False,
                "grade": "CIRCULAR: Ketubot is the few-shot source; site from a golden built with the list"},
}

# Stage names, in the order a story is tested against them. The first that applies is where it was lost.
ON_SITE = "on the site"
SITE_STAGES = [
    ON_SITE,
    "moved out of scope as biblical",
    "removed by a Jeff verdict",
    "triage discarded the page",
    "withheld as a Mishnah story",
    "never proposed",
    "proposed, NOT_A_STORY",
    "site filter: definite in one run only",
    "site filter: LOW (or BORDERLINE) wherever proposed",
    "golden: definite but no Jeff yes behind it",
    "definite, dropped by the site for another reason",
]
DET_STAGES = ["proposed (either run)", "triage discarded the page", "withheld as a Mishnah story", "never proposed"]


def wilson(k, n, z=1.96):
    if not n:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 3), round(c + h, 3))


def site_file(slug):
    return load(f"site/data/{slug}.json")


def cells_of(stories):
    return {(g["ref"], g["i"]) for s in stories for g in s["segments"]}


def removed_cells(slug):
    out = set()
    for e in load(DECISIONS)["remove"]["passages"]:
        if e["tractate"] == slug:
            out |= {(e["ref"], i) for i in range(int(e["start_segment"]), int(e["end_segment"]) + 1)}
    return out


def site_grade(s):
    """The grade the site reads (build_site_data.site_classification): before Stage 4j's biblical demotion."""
    return s.get("classification_pre_biblical_filter") or s.get("classification")


def run_cells(path, key="stories"):
    """{'definite'|'low'|'not': cells} for one run or golden; key='mishnah_stories' for the withheld ones."""
    pages = load(path)["pages"]
    out = defaultdict(set)
    for i, p in enumerate(pages):
        for s in p.get(key, []) or []:
            c = site_grade(s)
            kind = "definite" if c in DEFINITE else "not" if c == "NOT_A_STORY" else "low"
            out[kind] |= {(r, g) for r, gs in pieces(pages, i, s) for g in gs}
    return out


def counted(rows):
    return [r for r in rows if r.get("counts_for_recall", True) and not r.get("call_failed")]


def key(r):
    return (r["ref"], r["text"])


# ---------------------------------------------------------------- 1. stages

def stages_v14(slug, cfg, tmp, site, oos, removed):
    P = T.Paths(slug, ROOT)
    runs = [P.run(1).relative_to(ROOT), P.run(2).relative_to(ROOT)]
    per = [{key(r): r for r in counted(harness(slug, cfg["args"], rp, tmp)[0])} for rp in runs]
    assert set(per[0]) == set(per[1]), f"{slug}: the two runs disagree on the denominator"
    order = unit_order(runs[0])
    rc = [run_cells(rp) for rp in runs]
    mish = run_cells(runs[0], "mishnah_stories")["low"] | run_cells(runs[0], "mishnah_stories")["definite"] \
        | run_cells(runs[1], "mishnah_stories")["low"] | run_cells(runs[1], "mishnah_stories")["definite"] \
        | run_cells(runs[0], "mishnah_stories")["not"] | run_cells(runs[1], "mishnah_stories")["not"]
    rows = []
    for k, a in per[0].items():
        b = per[1][k]
        if not a.get("located"):
            raise SystemExit(f"{slug}: list story {a['ref']} has no located window; refusing to guess its stage")
        w = window(a, order)
        d = [bool(w & c["definite"]) for c in rc]
        lo = [bool(w & c["low"]) for c in rc]
        proposed = a["in_detector"] or b["in_detector"]
        if not a["survived_triage"]:
            det = "triage discarded the page"
        elif proposed:
            det = "proposed (either run)"
        elif w & mish:
            det = "withheld as a Mishnah story"
        else:
            det = "never proposed"
        if w & site:
            st = ON_SITE
        elif w & oos:
            st = "moved out of scope as biblical"
        elif w & removed:
            st = "removed by a Jeff verdict"
        elif det != "proposed (either run)":
            st = det
        elif not (any(d) or any(lo)):
            st = "proposed, NOT_A_STORY"
        elif all(d):
            st = "definite, dropped by the site for another reason"
        elif any(d):
            st = "site filter: definite in one run only"
        else:
            st = "site filter: LOW (or BORDERLINE) wherever proposed"
        rows.append({"id": a.get("id"), "ref": a["ref"], "site": st, "detector": det,
                     "cells": sorted(w), "text": a["text"][:80]})
    return rows


def stages_reviewed(slug, cfg, tmp, site, oos, removed):
    """Site from the golden; detector = the run the golden was built from, as the committed recall file read it."""
    golden = Path(f"results/canonical/{slug}_canonical.json")
    rows_g = counted(harness(slug, cfg["args"], golden, tmp)[0])
    committed = {key(r): r for r in load(f"results/recall/{slug}_jeff2005_matches.json")}
    order = unit_order(golden)
    gc = run_cells(golden)
    rows = []
    for a in rows_g:
        if not a.get("located"):
            raise SystemExit(f"{slug}: list story {a['ref']} has no located window; refusing to guess its stage")
        c = committed.get(key(a))
        if c is None:
            raise SystemExit(f"{slug}: {a['ref']} is in the denominator but not in the committed recall file")
        w = window(a, order)
        if not c["survived_triage"]:
            det = "triage discarded the page"
        elif c["in_detector"]:
            det = "proposed (either run)"
        elif c.get("in_mishnah_filtered"):
            det = "withheld as a Mishnah story"
        else:
            det = "never proposed"
        if w & site:
            st = ON_SITE
        elif w & oos:
            st = "moved out of scope as biblical"
        elif w & removed:
            st = "removed by a Jeff verdict"
        elif w & gc["definite"]:
            st = "golden: definite but no Jeff yes behind it"
        elif w & gc["low"]:
            st = "site filter: LOW (or BORDERLINE) wherever proposed"
        elif w & gc["not"]:
            st = "proposed, NOT_A_STORY"
        elif det != "proposed (either run)":
            st = det
        else:
            st = "proposed, NOT_A_STORY"  # proposed by the run, not carried into the golden as a story
        rows.append({"id": a.get("id"), "ref": a["ref"], "site": st, "detector": det,
                     "cells": sorted(w), "text": a["text"][:80]})
    return rows


def stages(tmp):
    out = {}
    for slug, cfg in LISTS.items():
        sf = site_file(slug)
        site, oos = cells_of(sf["stories"]), cells_of(sf["out_of_scope"])
        fn = stages_v14 if cfg["v14"] else stages_reviewed
        rows = fn(slug, cfg, tmp, site, oos, removed_cells(slug))
        sc, dc = Counter(r["site"] for r in rows), Counter(r["detector"] for r in rows)
        assert sum(sc.values()) == sum(dc.values()) == len(rows)
        out[slug] = {"grade": cfg["grade"], "site_from": "two v14 runs" if cfg["v14"] else "golden",
                     "denominator": len(rows),
                     "site": {s: sc[s] for s in SITE_STAGES if sc[s]},
                     "detector": {s: dc[s] for s in DET_STAGES if dc[s]},
                     "on_site": sc[ON_SITE], "proposed": dc["proposed (either run)"],
                     "misses": [r for r in rows if r["site"] != ON_SITE]}
        log.info("%s: %d counted; on site %d; detector proposed %d; site stages %s", slug, len(rows),
                 sc[ON_SITE], dc["proposed (either run)"], out[slug]["site"])
    return out


# ---------------------------------------------------------------- 2. estimate

def shipped_counts():
    rows = {}
    for p in sorted((ROOT / "site/data").glob("*.json")):
        d = json.loads(p.read_text())
        if isinstance(d, dict) and "stories" in d and "reviewed" in d:
            rows[p.stem] = {"shipped": len(d["stories"]), "reviewed": d["reviewed"], "out_of_scope": len(d["out_of_scope"])}
    return rows


def estimate(st):
    shipped = shipped_counts()
    S = sum(v["shipped"] for v in shipped.values() if not v["reviewed"])
    lists = [st[s] for s in ("eruvin", "yevamot")]
    k = sum(x["on_site"] for x in lists)
    n = sum(x["denominator"] for x in lists)
    r, p = k / n, SAMPLE["definite"] / SAMPLE["n"]
    point = S * p * (1 - r) / r
    rng = random.Random(SEED)
    draws = []
    flags = [[m == ON_SITE for m in ([ON_SITE] * x["on_site"] + ["x"] * (x["denominator"] - x["on_site"]))] for x in lists]
    for _ in range(DRAWS):
        kk = sum(sum(rng.choice(f) for _ in f) for f in flags)
        pp = sum(rng.random() < p for _ in range(SAMPLE["n"])) / SAMPLE["n"]
        rr = kk / n
        draws.append(S * pp * (1 - rr) / rr)
    draws.sort()
    lo, hi = draws[int(0.025 * DRAWS)], draws[int(0.975 * DRAWS)]
    per_list = {s: round(S * p * (1 - st[s]["on_site"] / st[s]["denominator"]) / (st[s]["on_site"] / st[s]["denominator"]))
                for s in ("eruvin", "yevamot")}
    # Where the estimated misses were lost, in the proportions the two blind v14 lists show.
    lost = Counter()
    for x in lists:
        for s, c in x["site"].items():
            if s != ON_SITE:
                lost[s] += c
    tot_lost = sum(lost.values())
    by_stage = {s: round(point * c / tot_lost) for s, c in lost.most_common()}
    reviewed = {s: {"denominator": st[s]["denominator"], "on_site": st[s]["on_site"],
                    "listed_missing": st[s]["denominator"] - st[s]["on_site"]} for s in ("ketubot", "kiddushin", "gittin")}
    rev_missing = sum(v["listed_missing"] for v in reviewed.values())
    det_k = sum(x["proposed"] for x in lists)
    return {
        "unreviewed_tractates": sum(1 for v in shipped.values() if not v["reviewed"]),
        "unreviewed_shipped": S,
        "site_recall_eruvin_yevamot": {"on_site": k, "denominator": n, "share": round(r, 3), "wilson95": wilson(k, n)},
        "detector_recall_eruvin_yevamot": {"proposed": det_k, "denominator": n, "share": round(det_k / n, 3),
                                           "wilson95": wilson(det_k, n)},
        "precision_sample": {**SAMPLE, "share": round(p, 3), "wilson95": wilson(SAMPLE["definite"], SAMPLE["n"])},
        "unreviewed_missing_point": round(point),
        "unreviewed_missing_bootstrap95": [round(lo), round(hi)],
        "unreviewed_missing_by_list": per_list,
        "unreviewed_missing_by_stage": by_stage,
        "reviewed": reviewed,
        "reviewed_listed_missing": rev_missing,
        "total_point": round(point) + rev_missing,
        "total_range": [round(lo) + rev_missing, round(hi) + rev_missing],
        "method": "missing = S * p * (1 - r) / r, S = shipped on unreviewed tractates, p = precision sample, "
                  "r = site recall on Eruvin+Yevamot list stories; bootstrap resamples the list stories (per list) "
                  f"and the 60-story sample, {DRAWS} draws, seed {SEED}. Reviewed tractates: listed stories not on "
                  "the site, counted directly (their unlisted misses are not estimated).",
    }


# ---------------------------------------------------------------- 3. pool

POOL = {
    "definite in one run, LOW in the other": "P1",
    "definite in one run, NOT/absent/withheld in the other": "P2",
    "LOW in both runs": "P3",
    "LOW in one run, NOT/absent/withheld in the other": "P4",
    "definite in both, not shipped (biblical/removed/judge drop)": "P0",
}
RULES = {
    "A: definite in one run + at least LOW in the other": ["P1"],
    "B: definite in either run": ["P1", "P2"],
    "C: B + LOW in both runs": ["P1", "P2", "P3"],
}


def grade_of(call):
    c = call.get("cls")
    return "D" if c in DEFINITE else "L" if c in ("LOW_CONFIDENCE", "BORDERLINE") else "N"


def pool_kind(u):
    g = sorted(grade_of(u["calls"].get(r, {})) for r in ("v14_r1", "v14_r2"))
    return {("D", "D"): "P0", ("D", "L"): "P1", ("D", "N"): "P2", ("L", "L"): "P3", ("L", "N"): "P4"}.get(tuple(g))


def gemini_verdicts(slug):
    p = ROOT / f"results/consensus/{slug}/gemini.json"
    if not p.exists():
        return {}
    return {r["id"]: r["answer"].get("verdict") for r in json.loads(p.read_text())["rows"] if r["answer"].get("outcome") == "ok"}


def pool(st, tmp):
    shipped = shipped_counts()
    per_t, tot, gem = {}, Counter(), defaultdict(Counter)
    blind = defaultdict(Counter)
    kinds_at = defaultdict(list)  # slug -> [(kind, cells)] of unshipped units, for the MEASURED recovery per rule
    # Counted list stories (yes) and Jeff's `not` rulings on list entries (no), located, for Eruvin and Yevamot.
    listed = {}
    for slug in ("eruvin", "yevamot"):
        run1 = T.Paths(slug, ROOT).run(1).relative_to(ROOT)
        rows = harness(slug, LISTS[slug]["args"], run1, tmp)[0]
        order = unit_order(run1)
        listed[slug] = {
            "yes": set().union(*(window(r, order) for r in rows if r.get("located") and r.get("counts_for_recall", True))),
            "no": set().union(*(window(r, order) for r in rows if r.get("located") and not r.get("counts_for_recall", True))),
        }
    for slug in sorted(shipped):
        p = ROOT / f"results/consensus/{slug}/units.json"
        if not p.exists():
            continue
        sf = site_file(slug)
        taken = cells_of(sf["stories"]) | cells_of(sf["out_of_scope"]) | removed_cells(slug)
        gv = gemini_verdicts(slug)
        c = Counter()
        for u in json.loads(p.read_text())["units"]:
            cells = {tuple(x) for x in u["cells"]}
            k = pool_kind(u)
            if k is None or (k != "P0" and cells & taken) or (k == "P0" and cells & cells_of(sf["stories"])):
                continue
            c[k] += 1
            gem[k][gv.get(u["id"], "unjudged")] += 1
            if slug in listed:
                kinds_at[slug].append((k, cells))
                blind[k]["units"] += 1
                blind[k]["on_list_yes"] += bool(cells & listed[slug]["yes"])
                blind[k]["jeff_no"] += bool(cells & listed[slug]["no"]) and not (cells & listed[slug]["yes"])
        per_t[slug] = {POOL_NAME[k]: c[k] for k in sorted(c)}
        tot += c
    return per_t, tot, gem, blind, kinds_at


POOL_NAME = {v: k for k, v in POOL.items()}


def ruler_low_verdicts():
    """Jeff's last verdict on each passage the detector SHOWED him as LOW_CONFIDENCE (CIRCULAR, v5-v11)."""
    out, tot = {}, Counter()
    for slug in ("ketubot", "kiddushin", "gittin"):
        c = Counter()
        for e in load(f"results/rulers/{slug}_ruler.json")["entries"]:
            vs = []
            for v in e.get("verdicts", []):
                if "simon" in v.get("round", ""):
                    continue
                shown = v.get("shown") or ((e.get("detector_classification") or [None])[0]
                                           if v.get("applies_to") == "base" else None)
                if shown == "LOW_CONFIDENCE":
                    vs.append(v)
            if vs:
                c[vs[-1]["read_as"]] += 1
        out[slug] = dict(c)
        tot += c
    judged = tot["yes"] + tot["borderline"] + tot["no"]
    out["total"] = dict(tot)
    out["yes_share"] = round(tot["yes"] / judged, 3)
    out["wilson95"] = wilson(tot["yes"], judged)
    return out


def rules(st, tot, est, low, blind, kinds_at):
    """What each candidate rule adds. q = the share of added spans that are real stories, INDICATED, as a
    (low, mid, high) range. One-run-definite (P1, P2): the 2026-11-10 reading of 20 two-run disagreements
    (12 stories), its Wilson interval for the range. LOW in both (P3): low = the BLIND lower bound (share of
    such spans on Eruvin + Yevamot that overlap a list story), high = Jeff's verdicts on LOW calls
    (CIRCULAR, v5-v11), mid = their midpoint."""
    S = est["unreviewed_shipped"]
    p = est["precision_sample"]["share"]
    w = wilson(12, 20)
    b3 = blind["P3"]["on_list_yes"] / blind["P3"]["units"]
    q = {"P1": (w[0], 12 / 20, w[1]), "P2": (w[0], 12 / 20, w[1]),
         "P3": (b3, (b3 + low["yes_share"]) / 2, low["yes_share"])}
    out = {}
    for name, ks in RULES.items():
        added = sum(tot[k] for k in ks)
        real = [sum(tot[k] * q[k][j] for k in ks) for j in range(3)]
        prec = [(p * S + r) / (S + added) for r in real]
        # List stories this rule would bring onto the site, MEASURED on Eruvin + Yevamot: a miss lost at the
        # site filter whose window overlaps an unshipped unit of a kind the rule admits.
        recovered = 0
        for slug in ("eruvin", "yevamot"):
            for m in st[slug]["misses"]:
                if not m["site"].startswith("site filter"):
                    continue
                cells = {tuple(c) for c in m["cells"]}
                recovered += any(k in ks and cells & c for k, c in kinds_at[slug])
        n = est["site_recall_eruvin_yevamot"]["denominator"]
        k0 = est["site_recall_eruvin_yevamot"]["on_site"]
        out[name] = {"spans_added": added, "real_stories_added_est_low_mid_high": [round(r) for r in real],
                     "non_stories_added_est_low_mid_high": [round(added - r) for r in reversed(real)],
                     "site_precision_est_low_mid_high": [round(x, 3) for x in prec], "q": {k: q[k] for k in ks},
                     "eruvin_yevamot_list_recovered": recovered,
                     "eruvin_yevamot_site_recall_after": f"{k0 + recovered}/{n} = {(k0 + recovered) / n:.1%}"}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        st = stages(tmp)
        est = estimate(st)
        per_t, tot, gem, blind, kinds_at = pool(st, tmp)
    low = ruler_low_verdicts()
    rep = {
        "stages": st,
        "estimate": est,
        "pool": {"by_tractate": per_t, "total": {POOL_NAME[k]: tot[k] for k in sorted(tot)},
                 "gemini_judge_by_kind": {POOL_NAME[k]: dict(v) for k, v in sorted(gem.items())},
                 "blind_eruvin_yevamot_by_kind": {POOL_NAME[k]: dict(v) for k, v in sorted(blind.items())},
                 "jeff_on_low_calls_circular": low},
        "rules": rules(st, tot, est, low, blind, kinds_at),
    }
    log.info("estimate: %s", {k: est[k] for k in ("unreviewed_shipped", "site_recall_eruvin_yevamot", "unreviewed_missing_point",
                                                 "unreviewed_missing_bootstrap95", "reviewed_listed_missing", "total_point", "total_range")})
    log.info("by stage: %s", est["unreviewed_missing_by_stage"])
    log.info("pool: %s", rep["pool"]["total"])
    log.info("pool on Eruvin+Yevamot vs the lists (BLIND): %s", rep["pool"]["blind_eruvin_yevamot_by_kind"])
    log.info("Jeff on LOW calls (CIRCULAR): %s", low)
    for k, v in rep["rules"].items():
        log.info("rule %s: %s", k, v)
    if args.out:
        Path(args.out).write_text(json.dumps(rep, ensure_ascii=False, indent=1))
        log.info("wrote %s", args.out)


if __name__ == "__main__":
    main()
