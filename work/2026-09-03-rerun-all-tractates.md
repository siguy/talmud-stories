---
title: Re-run every tractate on the current detector, once the pending changes are settled
capability: [detection, classification, boundaries]
tractate: [ketubot, kiddushin, gittin]
blocked_by: [2026-09-03-tighten-story-finder]
awaiting: []
writes: [results/, STATUS.md, STATE.md, src/story_detector_v11.py]
finding:
superseded_by:
---

# Re-run every tractate on the current detector

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) §2–3, then this.

## Why

Simon, 2026-09-03: *"We need to rerun all the tractates now that we've tightened up the
segment story finder because we were too loose about that."*

**The shipped numbers are not all from the same detector.** The board carries figures
produced across v7 through v11 and across several models, and some rest on caches built
before changes that are now shipped:

- **Kiddushin's golden verdicts were given on v7 output** while the detector is v11. Its
  precision range describes v7, not what we ship.
- **Triage decisions come from a cache** predating several model changes; triage has never
  been run twice on the same pages, so this capability has **no noise floor at all**.
- R-B1 (the opening-formula boundary rule) shipped after the last full runs.
- The `N≥1` triage rule (2026-08-31) applies to future runs only — the cached labels are
  unchanged, so **no shipped output reflects it**.

A single clean run of every tractate on one detector and one model is the only way the
board's cells become comparable to each other.

## ANSWERED 2026-09-03 — it is the quasi-speech-act rule

Simon: *"Story finder — tighten it per what I suggested. Then rerun it so we can see the
actual score."* So the change is
[`tighten-story-finder`](2026-09-03-tighten-story-finder.md), and this item is
`blocked_by` it — there is nothing to re-run until it ships.

**Ruled out, and worth recording so it is not re-litigated:** the recall aligner's
14-segment window is *also* "too loose", credits 35 proposals as matching his list when
they do not, and **a re-run cannot fix it** — it is a scoring defect over artifacts we
already hold, repaired by re-scoring for free →
[`loose-credited-proposals`](2026-09-03-loose-credited-proposals.md).

## AND IT RUNS AFTER THE THINKING EXPERIMENT — a second ordering the board cannot see

`work/2026-09-03-thinking-level-experiment.md` (PR #42) must produce its answer **before**
this item spends its runs. #42 changes two things at once — the model becomes
`gemini-3.8-flash` and `thinking_level` becomes `high`, where unset had silently meant
*off*. **`high` was chosen on no evidence**, and its cost is measured: 7,867 thinking tokens
against 321 tokens of output, 14–70s a page.

Re-running before that experiment settles spends the expensive half at a setting nobody has
justified, and makes the result uninterpretable — model and thinking would have moved
together, so neither could be attributed. **Run the experiment, take its answer, then
re-run once.**

**This dependency is not in `blocked_by` because the item it names lives on another branch**
(PR #42) and `test_blocked_by_and_awaiting_resolve` requires every dependency to resolve to
an item that exists here. **Once #42 lands on main, add it:**

```
blocked_by: [2026-09-03-tighten-story-finder, 2026-09-03-thinking-level-experiment]
```

Until that line exists, this ordering lives only in prose — and the same warning applies as
for the Simon question above: **do not start this item on the strength of a short
`blocked_by` field.**

Two shipped changes are independent reasons this re-run is due regardless: **R-B1**, the
opening-formula boundary rule (worth 4–5 points on three tractates), and the **`N≥1`
triage rule**, which applies to future runs only — no shipped output reflects it.

## Method, once unblocked

1. **Freeze the configuration and write it down first** — detector version, model,
   thinking level, triage rule, boundary rules — into the run manifest. Every prior
   comparison problem on this project came from a number whose configuration was implicit.
2. **Order:** run [`triage-recall-options`](2026-09-03-triage-recall-options.md) and the
   [`examine-all-pages`](2026-09-03-examine-all-pages.md) decision **before** this, not
   after. Both change the page set. Re-running now and again in a fortnight wastes the
   expensive half twice.
3. **Re-run triage too, not just detection.** Reusing the cache defeats the point and
   leaves the noise floor unmeasured for a third time.
4. **Run each tractate at least twice** where budget allows (Lesson 22). This project has
   an 8-run measurement showing a story proposed in 7 of 8 identical runs; a single run per
   tractate cannot distinguish a regression from that variance.
5. **Score against the blind lists first, the goldens second.** The goldens were built
   with help from earlier detector versions and will flatter a new run in ways the blind
   lists cannot.

## How you know it worked

Every cell on the STATUS scoreboard traceable to **one** run manifest, with its provenance
tag (BLIND / CIRCULAR) and its run-to-run spread. Any cell that cannot be re-derived from
the new runs is named as legacy rather than quietly carried forward.

## Guardrails

- **No golden is rebuilt from a new run.** `build_canonical.py` already refuses any write
  that is not a strict addition, after a measured near-miss that would have deleted 5
  stories and *raised* the score.
- Kiddushin's v7-era verdicts do not become v11 verdicts by being re-run against. Its
  precision cell stays flagged until Jeff reviews v11 output.

## When done

Finding to `docs/findings/<date>-full-rerun.md`, `## Outcome` here, then
`python3 scripts/board.py finish rerun-all-tractates`.
