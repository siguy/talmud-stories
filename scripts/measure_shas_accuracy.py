#!/usr/bin/env python3
"""Did we find the stories across Shas? Every number in docs/findings/2026-11-10-shas-accuracy.md.

No model calls. Read-only except --out. It joins what is already on disk:

  recall     Jeff's BLIND 2005 lists (results/expert_lists/, the Ketubot .doc) against the two v14
             runs and against what the site ships (site/data/). The per-run figures come from the
             recall harness itself (scripts/measure_recall_vs_expert_list.py, run here as a
             subprocess into a temporary folder), so this script never re-implements its matcher.
  precision  (a) Jeff's verdicts on calls the detector showed him as YES/HIGH (results/rulers/,
             CIRCULAR, older detector versions); (b) a BLIND lower bound: the share of shipped
             stories on a tractate with a list that overlap a story on that list.
  coverage   every page of every run tractate: in the text, labelled by triage, present in both
             runs, examined or skipped, and any call failure.
  agreement  G4 per tractate, from results/shas_run/status.json.

Usage:
  python3 scripts/measure_shas_accuracy.py                 # print the report
  python3 scripts/measure_shas_accuracy.py --out x.json    # and write every number to x.json
"""
import argparse
import json
import logging
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import tractates as T  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [shas-accuracy] %(message)s",
                    handlers=[logging.StreamHandler(sys.stderr),
                              logging.FileHandler(ROOT / "project.log")])
log = logging.getLogger()

DEFINITE = ("YES", "HIGH_CONFIDENCE")
GRADES = "results/shas_run/accuracy/unlisted_shipped_grades.json"

# Tractates with a blind expert list AND two v14 runs on disk. Eruvin is the held-out exam: no
# detector version was ever tuned on it. Yevamot is a DEVELOPMENT tractate for v13/v14 (the twin
# pass was designed and measured on it), so its recall is blind as to the list but not held out.
V14_LISTED = {
    "eruvin": {"expert": ["--expert-json", "results/expert_lists/eruvin_2005.json"], "held_out": True},
    "yevamot": {"expert": ["--expert-json", "results/expert_lists/yevamot_2005.json"], "held_out": False},
}
# Jeff-reviewed tractates: the site ships from their goldens, which were built WITH his lists and
# verdicts, so their site recall is CIRCULAR and reported only as such.
REVIEWED_LISTED = {
    # --standard 2005: when this was written the default ("current") raised on Ketubot, because a lowercase
    # --tractate built refs no ruling matched. Fixed 2026-11-10 in measure_recall_vs_expert_list.py; 2005 is kept
    # so the finding's CIRCULAR site-recall row reproduces as published.
    "ketubot": ["--expert-doc", "jeff comms/b.ketubot (1).doc", "--standard", "2005"],
    "kiddushin": ["--expert-json", "results/expert_lists/kiddushin_2005.json"],
    "gittin": ["--expert-json", "results/expert_lists/gittin_2005.json"],
}


def load(p):
    return json.loads((ROOT / p).read_text())


def pieces(pages, i, s):
    """(page_ref, [segment indexes]) of one story, the way build_site_data.pieces reads it."""
    p = pages[i]
    a, b = int(s["start_segment"]), int(s["end_segment"])
    out = [(p["ref"], range(a, b + 1))]
    if s.get("spans_pages") and s.get("end_segment_page2") is not None and i + 1 < len(pages):
        out.append((pages[i + 1]["ref"], range(int(s.get("start_segment_page2") or 0), int(s["end_segment_page2"]) + 1)))
    return out


def cells_of_run(path, which):
    """Cells (ref, segment) of stories[] in one run: which='definite' (YES/HIGH), 'story' (anything
    but NOT_A_STORY), or 'any'. mishnah_stories[] are excluded: the site never ships them."""
    pages = load(path)["pages"]
    out = set()
    for i, p in enumerate(pages):
        for s in p.get("stories", []):
            c = s.get("classification")
            if which == "definite" and c not in DEFINITE:
                continue
            if which == "story" and c == "NOT_A_STORY":
                continue
            out |= {(r, g) for r, gs in pieces(pages, i, s) for g in gs}
    return out


def site_stories(slug):
    p = ROOT / "site" / "data" / f"{slug}.json"
    if not p.exists():
        return None
    return [s for s in load(p.relative_to(ROOT))["stories"] if s.get("tier") == "story"]


def site_cells(slug):
    return {(g["ref"], g["i"]) for s in site_stories(slug) or [] for g in s["segments"]}


def harness(slug, expert_args, run_path, tmp):
    """Run the recall harness on one run; return its per-story list and its headline lines."""
    out = Path(tmp) / f"{slug}_{Path(run_path).stem}.json"
    cmd = [sys.executable, "scripts/measure_recall_vs_expert_list.py", *expert_args, "--tractate", slug,
           "--detected", str(run_path), "--out", str(out)]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"recall harness failed on {slug} {run_path}:\n{r.stderr[-2000:]}")
    lines = [l.split("[recall] ", 1)[-1] for l in (r.stdout + r.stderr).splitlines()
             if any(k in l for k in ("RECALL vs", "TRIAGE recall", "DETECTION recall", "CAUSE of"))]
    return json.loads(out.read_text()), lines


def unit_order(run_path):
    """Every (ref, segment) of a run in corpus order, and each one's position: the harness's
    `located` is the FIRST and LAST cell of its window, which runs in this order (and can cross a daf)."""
    units = [(p["ref"], i) for p in load(run_path)["pages"] for i in range(len(p.get("segments", [])))]
    return units, {u: k for k, u in enumerate(units)}


def window(story, order):
    """All cells of a located expert story (the harness writes only its two ends)."""
    units, pos = order
    a, b = (tuple(c) for c in story["located"])
    return set(units[pos[a]:pos[b] + 1])


def counted(stories):
    return [s for s in stories if s.get("counts_for_recall", True) and not s.get("call_failed")]


def recall_v14(tmp):
    out = {}
    for slug, cfg in V14_LISTED.items():
        P = T.Paths(slug, ROOT)
        runs = [P.run(1), P.run(2)]
        per_run, lines = [], []
        for rp in runs:
            st, ln = harness(slug, cfg["expert"], rp.relative_to(ROOT), tmp)
            per_run.append({s["id"]: s for s in counted(st)})
            lines.append(ln)
        ids = list(per_run[0])
        assert set(ids) == set(per_run[1]), "the two runs disagree on the denominator"
        order = unit_order(runs[0].relative_to(ROOT))
        definite = [cells_of_run(rp.relative_to(ROOT), "definite") for rp in runs]
        storyish = [cells_of_run(rp.relative_to(ROOT), "story") for rp in runs]
        site = site_cells(slug)
        row = Counter()
        missed_site = []
        for i in ids:
            a, b = per_run[0][i], per_run[1][i]
            cells = window(a, order)
            row["listed"] += 1
            row["survived_triage"] += a["survived_triage"]
            row["proposed_run1"] += a["in_detector"]
            row["proposed_run2"] += b["in_detector"]
            row["proposed_either"] += a["in_detector"] or b["in_detector"]
            row["story_run1"] += bool(cells & storyish[0])
            row["story_run2"] += bool(cells & storyish[1])
            row["definite_run1"] += bool(cells & definite[0])
            row["definite_run2"] += bool(cells & definite[1])
            both = bool(cells & definite[0]) and bool(cells & definite[1])
            row["definite_both"] += both
            on = bool(cells & site)
            row["on_site"] += on
            if not on:
                why = ("triage discarded the page" if not a["survived_triage"] else
                       "not proposed in either run" if not (a["in_detector"] or b["in_detector"]) else
                       "proposed, but NOT_A_STORY in both runs" if not (cells & storyish[0] or cells & storyish[1]) else
                       "proposed as a story, below YES/HIGH in at least one run" if not both else
                       "definite in both runs, dropped by the site (biblical or duplicate)")
                missed_site.append({"ref": a["ref"], "why": why, "text": a["text"][:90]})
        out[slug] = {"held_out": cfg["held_out"], "counts": dict(row), "harness": lines,
                     "not_on_site": missed_site, "why_not_on_site": dict(Counter(m["why"] for m in missed_site))}
    return out


def recall_reviewed(tmp):
    """Site vs list on the three Jeff-reviewed tractates. CIRCULAR: the goldens were built with the list."""
    out = {}
    for slug, args in REVIEWED_LISTED.items():
        # Any run will do for the denominator and the located cells; use the golden itself.
        golden = f"results/canonical/{slug}_canonical.json"
        st, _ = harness(slug, args, golden, tmp)
        st = [s for s in counted(st) if s.get("located")]
        order = unit_order(golden)
        site = site_cells(slug)
        out[slug] = {"listed": len(st), "on_site": sum(bool(window(s, order) & site) for s in st)}
    return out


def precision_verdicts():
    """Jeff's verdicts on calls the detector SHOWED him as YES/HIGH (read via verdict_reading, in the
    rulers). One answer per passage: the last verdict on it. CIRCULAR (his review of our proposals) and
    on older detector versions (v5-v11), never on v14."""
    out = {}
    tot = Counter()
    for slug in ("ketubot", "kiddushin", "gittin"):
        d = load(f"results/rulers/{slug}_ruler.json")
        c = Counter()
        for e in d["entries"]:
            vs = []
            for v in e.get("verdicts", []):
                if "simon" in v.get("round", ""):
                    continue
                shown = v.get("shown") or ((e.get("detector_classification") or [None])[0]
                                           if v.get("applies_to") == "base" else None)
                if shown in DEFINITE:
                    vs.append(v)
            if vs:
                c[vs[-1]["read_as"]] += 1
        out[slug] = dict(c)
        tot += c
    judged = tot["yes"] + tot["no"] + tot["borderline"]
    out["total"] = dict(tot)
    out["yes_share_of_yes_no_borderline"] = round(tot["yes"] / judged, 3) if judged else None
    return out


def precision_blind_lower_bound(tmp):
    """Share of shipped stories (v14, both runs definite) that overlap a story on Jeff's blind list.
    A shipped story NOT on his list is either a non-story or a story he did not list -- his lists are
    not exhaustive (FRAMEWORK §1.2) -- so this is a LOWER bound on precision, not an estimate."""
    out = {}
    for slug, cfg in V14_LISTED.items():
        run1 = T.Paths(slug, ROOT).run(1).relative_to(ROOT)
        st, _ = harness(slug, cfg["expert"], run1, tmp)
        order = unit_order(run1)
        listed = set().union(*(window(s, order) for s in st if s.get("located")))
        stories = site_stories(slug)
        on = [s for s in stories if {(g["ref"], g["i"]) for g in s["segments"]} & listed]
        unlisted = [s["id"] for s in stories if s not in on]
        row = {"shipped": len(stories), "on_list": len(on), "lower_bound": round(len(on) / len(stories), 3),
               "unlisted_ids": unlisted}
        # The unlisted ones, as Claude read them (INDICATED). Every one must be graded, or the estimate
        # would quietly treat an ungraded story as absent (Lesson 38): refuse, naming them.
        grades = load(GRADES)["grades"].get(slug, {})
        ungraded = [i for i in unlisted if i not in grades]
        if ungraded:
            raise SystemExit(f"{slug}: {len(ungraded)} shipped unlisted stories have no grade in {GRADES}: {ungraded}")
        g = Counter(grades[i]["grade"] for i in unlisted)
        row["unlisted_graded"] = dict(g)
        row["estimate_yes"] = round((len(on) + g["yes"]) / len(stories), 3)
        row["estimate_yes_or_borderline"] = round((len(on) + g["yes"] + g["borderline"]) / len(stories), 3)
        out[slug] = row
    return out


def coverage():
    """Every page of every tractate with two v14 runs: present in text, triage and both runs."""
    rows = {}
    for slug in T.SLUGS:
        P = T.Paths(slug, ROOT)
        if not (P.run(1).exists() and P.run(2).exists()):
            continue
        text_refs = [p["ref"] for p in json.loads(P.text.read_text())["pages"]] if P.text.exists() else None
        r = [json.loads(P.run(n).read_text()) for n in (1, 2)]
        refs = [[p["ref"] for p in x["pages"]] for x in r]
        examined = [sum(1 for p in x["pages"] if not p.get("skipped_by_triage")) for x in r]
        meta = [x.get("run_meta", {}) for x in r]
        rows[slug] = {
            "pages_text": len(text_refs) if text_refs is not None else None,
            "pages_run": [len(x) for x in refs],
            "same_pages_both_runs": refs[0] == refs[1],
            "every_text_page_in_runs": text_refs is None or set(text_refs) == set(refs[0]) == set(refs[1]),
            "examined": examined,
            "skipped": [len(refs[0]) - examined[0], len(refs[1]) - examined[1]],
            "same_triage": meta[0].get("triage_sha1") == meta[1].get("triage_sha1"),
            "triage_failed": [m.get("triage_failed", {}).get("count", 0) for m in meta],
            "stage2_errors": [len(m.get("stage2_errors") or []) for m in meta],
            "stage4_call_failures": [len(x.get("stage4_call_failures") or []) for x in r],
            "detector": sorted({m.get("detector_module") for m in meta}),
        }
    return rows


def agreement():
    d = load("results/shas_run/status.json")
    out = {}
    for slug, t in d["tractates"].items():
        g4 = t.get("steps", {}).get("pair", {}).get("gates", {}).get("g4", {})
        m = g4.get("measured", {})
        out[slug] = {"status": g4.get("status"), "both": m.get("definite_in_both"),
                     "passages": m.get("definite_passages"), "share": m.get("definite_both_share")}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="write every number to this JSON file")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        rep = {
            "recall_v14_blind": recall_v14(tmp),
            "recall_reviewed_site_circular": recall_reviewed(tmp),
            "precision_jeff_verdicts_circular": precision_verdicts(),
            "precision_blind_lower_bound": precision_blind_lower_bound(tmp),
            "coverage": coverage(),
            "agreement_g4": agreement(),
        }
    cov = rep["coverage"]
    tot_pages = sum(c["pages_run"][0] for c in cov.values())
    tot_exam = sum(c["examined"][0] for c in cov.values())
    bad = [s for s, c in cov.items() if not (c["same_pages_both_runs"] and c["every_text_page_in_runs"]
                                            and c["same_triage"] and not any(c["triage_failed"])
                                            and not any(c["stage2_errors"]))]
    rep["coverage_summary"] = {"tractates": len(cov), "pages": tot_pages, "examined_run1": tot_exam,
                               "examined_share": round(tot_exam / tot_pages, 3), "tractates_with_a_defect": bad}
    g = rep["agreement_g4"]
    both = sum(v["both"] or 0 for v in g.values())
    pas = sum(v["passages"] or 0 for v in g.values())
    rep["agreement_summary"] = {"tractates": len(g), "definite_in_both": both, "definite_passages": pas,
                                "pooled_share": round(both / pas, 3) if pas else None,
                                "under_90": sorted(s for s, v in g.items() if (v["share"] or 1) < 0.9)}
    for slug, r in rep["recall_v14_blind"].items():
        log.info("%s (%s): %s", slug, "held out" if r["held_out"] else "development", r["counts"])
        for run, ln in enumerate(r["harness"], 1):
            for l in ln:
                log.info("  run%d %s", run, l)
        log.info("  not on site, by cause: %s", r["why_not_on_site"])
    log.info("reviewed tractates, site vs list (CIRCULAR): %s", rep["recall_reviewed_site_circular"])
    log.info("precision, Jeff's verdicts on YES/HIGH calls (CIRCULAR, v5-v11): %s", rep["precision_jeff_verdicts_circular"])
    log.info("precision, blind lower bound: %s", {k: {x: v[x] for x in ("shipped", "on_list", "lower_bound", "unlisted_graded",
                                                                  "estimate_yes", "estimate_yes_or_borderline")}
                                                    for k, v in rep["precision_blind_lower_bound"].items()})
    log.info("coverage: %s", rep["coverage_summary"])
    log.info("agreement G4: %s", rep["agreement_summary"])
    if args.out:
        Path(args.out).write_text(json.dumps(rep, ensure_ascii=False, indent=1))
        log.info("wrote %s", args.out)


if __name__ == "__main__":
    main()
