---
title: Re-run every tractate on the current detector, once the pending changes are settled
capability: [detection, classification, boundaries]
tractate: [ketubot, kiddushin, gittin]
blocked_by: []
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

## BLOCKED on one answer from Simon — and the frontmatter cannot say so

**`awaiting` resolves only to an item slug or a `jeff:` question in `comms/JEFF.md`**
(`tests/test_bookkeeping.py::test_blocked_by_and_awaiting_resolve`). There is no namespace
for a question aimed at Simon, though FRAMEWORK §2b already names two of them. So this
blocker lives in prose, where the board cannot see it — **do not start this item on the
strength of an empty `awaiting` field.**

**"The segment story finder was too loose" does not resolve to one change on disk**, and
this item must not run until it does. The candidates:

| candidate | what it is | shipped? |
|---|---|---|
| **the recall aligner's window** | returns a window up to 14 segments wide; 35 proposals read as "on his list" and are not (Ketubot 19, Kiddushin 9, Gittin 7) | scoring only — **does not change detector output**, so a re-run does not fix it → [`loose-credited-proposals`](2026-09-03-loose-credited-proposals.md) |
| **the quasi-speech-act screen** | 2026-09-03; tightens what counts as an *action* | **not shipped** — Wave 6c is blocked on Jeff |
| **boundary R-B1** | the opening-formula rule, worth 4–5 points on three tractates | shipped, and **is** a reason to re-run |
| **the `N≥1` triage rule** | keeps more pages, i.e. *looser*, not tighter | shipped, and **is** a reason to re-run |

**If the intended change is the aligner window, a re-run is the wrong instrument** — that
is a measurement defect and re-scoring the existing artifacts fixes it for free. If it is
R-B1 and the triage rule, the re-run is right and this item proceeds. Ask before spending
the runs.

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
