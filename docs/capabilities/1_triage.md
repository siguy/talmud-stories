# Capability 1 — Triage

**Definition:** decide whether a page is worth examining at all — see
[`FRAMEWORK.md` §1.1](../../FRAMEWORK.md).
**Gate:** ≥98% of true stories surviving (PROVISIONAL)
**Current:** **98.0%** — 3 of 149 lost — on Jeff's 2005 Ketubot list (**BLIND**), while
examining 44% of pages. Measured 2026-08-30 (`c900ee4`). Kiddushin: **unmeasured**.

*Written 2026-08-30 from the sources in `tasks/NEXT/00`. History, not status —
status lives in [`STATUS.md`](../../STATUS.md).*

---

## What we tried

| when | what | outcome | evidence |
|---|---|---|---|
| 2026-02-13 | **Stage 1 event triage introduced** (Increment 2/5). Every segment classified NARRATIVE_EVENT / VERBAL_ACT / DELIBERATION / HABITUAL; a page is kept if ≥2 NARRATIVE_EVENT, or ≥1 NARRATIVE_EVENT + ≥2 VERBAL_ACT | shipped. 66.1% skip rate on Ketubot 2-60 (78 of 118 pages); **1 false skip found by hand** (Ketubot 51a) | `84c9f43` |
| 2026-02-13 | Threshold relaxed from "≥2 narrative events" to also keep 1 narrative + 2 verbal, so dialogue-carrying stories survive | shipped; zero false skips on the four strong story pages checked (10b, 8b, 2b, 60a) | `84c9f43` |
| 2026-02-13 | **Ablation: does triage help or hurt?** v7 with triage vs v7 without, scored against Jeff's 127 labels (**CIRCULAR**) | **measured: triage is the single largest accuracy driver.** 111/127 (87.4%) with, 106/127 (83.5%) without | `6ea4204` |
| 2026-03-27 | Kiddushin first run under v7 | 67% skip rate (109 of 162 pages), reported without any recall check | `14a5f3a` |
| 2026-05-18 | **Wave 1 Issue #5 — lexical override.** A page containing any of five canonical Hebrew introducers (`מעשה ב`, `הנהו בי תרי`, `ההוא ד`, `ההוא גברא`, `כי הא ד`, matched on the consonantal skeleton) forces Stage 2 to run whatever Stage 1 said | shipped and **it worked**: Kiddushin 45a and 53a — two stories Jeff had flagged as missed — recovered, each yielding one real story. 9 Kiddushin pages and 5 Ketubot pages moved from skipped to processed | `eff0218`, [`wave1_results.md`](../findings/2026-05-18-wave1-results.md) |
| 2026-08-30 | **First measurement of what triage discards.** Traced the 6 blind-list recall misses back through the pipeline | **measured: Stage 1 discards 124 of 222 Ketubot pages (56%)** — 1,535 segments never examined. 19 of Jeff's 149 stories touch a discarded page; 16 survive only because the other half of the daf pair was kept; **3 are lost outright** (Ketubot 20a, 72b, 82b — both pages of each pair discarded) | `9f7ddf8`, [`recall_miss_diagnosis`](../findings/2026-08-30-recall-miss-diagnosis.md) |
| 2026-08-30 | **Triage recall computed for the first time**, against the BLIND 2005 list | **measured: 98.0%** (146 of 149 survive) at 44% of pages examined. Reframed from "the biggest unmeasured thing in the project" to **a trade to be priced** | `c900ee4` |

## What we reverted, and why

**Nothing has been reverted in this capability.** Every change to Stage 1 since it was
built is still shipped: the relaxed threshold, and the Wave 1 lexical override. That is
worth stating plainly, because it is unusual in this project — and because it is also a
warning. Triage is the one capability where **no change has ever been reverted, and no
change has ever been measured against a blind dataset before shipping.** The two facts
are related.

The nearest thing to a revert is a decision *not* to act:

- **2026-08-30 — the 56% skip rate was not "fixed".** The obvious reaction to
  "we throw away half the tractate" is to loosen the threshold. It was deliberately not
  done. Triage exists to save money; a recall bar quoted without its cost saving is
  meaningless, and 2% of recall for a 56% cost cut may be a good trade. The decision was
  recorded as a trade to be priced (`NEXT/01`), not a defect to be patched
  ([`FRAMEWORK.md` §1.1](../../FRAMEWORK.md)). **Do not loosen Stage 1 without producing
  the exchange rate first.**

## Current best — the exact configuration

- **Code:** `src/event_triage.py` — `EventTriager.triage_page()` and
  `EventTriager.should_skip_page()`.
- **Rule:** keep the page if `NARRATIVE_EVENT ≥ 2`, **or**
  `NARRATIVE_EVENT ≥ 1 and VERBAL_ACT ≥ 2`. Otherwise skip.
- **Override:** `_page_has_story_introducer()` in `src/story_detector_v11.py:2011` —
  five introducers, nikud stripped (`_STORY_INTRODUCERS`, line 2002). Any hit forces
  Stage 2 (`src/story_detector_v11.py:1072`).
- **Failure default:** on an unparseable model response the page is tagged all
  DELIBERATION (`src/event_triage.py:216`), whose comment reads *"safest — won't skip
  pages incorrectly."* **The comment is backwards** — measured by reading the code:
  all-DELIBERATION gives `narrative_count == 0`, which fails both keep-conditions in
  `should_skip_page()`, so a failed triage call **silently discards the page**. This is
  Lesson 21's shape (a failed call recorded as a judgment) sitting in the one stage whose
  errors leave no trace. How often it fires is **unmeasured** — nothing counts parse
  failures — and it is not in the shipped skip counts either way, since those come from a
  cache. Found while writing this file, 2026-08-30; not fixed here.
- **Model:** `GEMINI_MODEL`, currently `gemini-3-flash-preview` for detection runs;
  triage results are cached (`results/v7/event_triage_*.json`) and reused rather than
  re-run, so the shipped skip decisions predate several model changes.
- **The numbers came from:** `results/v10/wave4_notrim/*.json`, whose skipped pages carry
  `skipped_by_triage: true` **with their full segment text** — so the discarded 56% can
  be re-examined with no re-fetch.

Reproduce the skip rates directly from those files: Ketubot 73/118 + 51/104 = **124 of
222 (56%)**; Kiddushin **100 of 162 (62%)** (measured 2026-08-30).

## Distance to gate

**At the gate, exactly — and that is the problem with the gate.** 98.0% measured against
a ≥98% bar that [`FRAMEWORK.md` §1.1](../../FRAMEWORK.md) marks PROVISIONAL and describes
as "our current value, which is circular reasoning in a principle's clothing." The shape
of the bar is defensible (invisible, permanent losses get the strictest bar); the number
is not yet defended. It falls out of the end-to-end target once that is set — an open
question for Simon (FRAMEWORK §2b).

**Run-to-run noise is unknown.** Triage has never been re-run twice on the same pages,
so there is no noise floor for this capability, and Lesson 22 says a single-run number of
this kind cannot be told from a coin flip until that spread is measured. What we do know:
the shipped triage decisions come from a **cache**, so today's 98.0% is stable by
construction — it is a property of a fixed artifact, not a re-runnable measurement. A
fresh triage run on a current model could land anywhere, and nobody has tried.

**Kiddushin is unmeasured.** It now has a blind list
([`kiddushin_2005.json`](../../results/expert_lists/kiddushin_2005.json), 90 stories),
so the cell is fillable — `NEXT/06`. Its skip rate is 62%, higher than Ketubot's 56%,
so its triage recall could plausibly be worse (suspected, no evidence either way).

## Ceiling

**None known.** No structural limit has been found or argued for. Triage discards are a
pure threshold decision on a signal we generate ourselves, so unlike Boundaries (13% of
expert boundaries are not on a clause edge — a real ceiling) there is nothing here that
says "no configuration can reach it."

What exists instead is a **measurement ceiling**, and it is the important thing about
this capability: *a page never examined produces no record of what was lost.* Triage
errors are invisible by construction. The only way to see them is an external blind list,
which is why this capability had no number at all until 2026-08-30 — four detector
versions after it shipped (v8, v9, v10, v11)
([`FRAMEWORK.md` §1.1](../../FRAMEWORK.md), Lesson 27's family of failures).

## Untried

- **Re-run Stage 2 on the 124 discarded Ketubot pages and price the trade.** The single
  highest-value item here; brief written and ready (`tasks/NEXT/01`), no API cost beyond
  pennies, text already on disk. It answers whether "96% recall" is really "96% of the
  44% we look at." **Never attempted.**
- **Measure Kiddushin triage recall** against its new blind list — `NEXT/06`, no API
  calls.
- **Mine the opener lexicon instead of hand-writing it** (`tasks/PLAN_wave7.md`, DRAFT,
  never executed). The five introducers were invented, not derived. Wave 7 proposes
  ranking opening n-grams from the 149 blind stories plus the golden by story-frequency
  vs corpus-frequency, and using them **as a triage prior only, never as a classifier**
  (Lesson 15). Two known misses have openers outside the lexicon: Ketubot 67b
  (`אמרו עליו על הלל הזקן`) and 82b (`בראשונה היו כותבין`).
- **Per-opener precision before shipping any addition.** `בראשונה` is common in
  non-narrative contexts; if it fires on 200 pages to recover 1 story that is a cost
  decision, not a free win (`PLAN_wave7.md`). Nothing in the current five has ever had
  its precision measured.
- **A local model for Stage 1** — Dicta's rabbinic-Hebrew BERT (BEREL family) as a
  triage replacement, near-zero marginal cost at corpus scale and it removes the API
  dependency from the highest-volume stage. Proposed 2026-07-06
  ([`approach_review_and_scaling` §4.6](../findings/2026-07-06-approach-review-and-scaling.md)),
  never tried.
- **Declined, by Jeff:** *Ein Yaakov coverage as a triage prior.* Proposed 2026-07-06 as
  part of "the highest-leverage new idea" (§4.2); **Jeff declined it the same day** — it
  is all aggada and structurally omits the halakhic stories this database explicitly
  includes. Demoted to an optional aggadic-only cross-check
  ([ledger, Part 2(b)](../../validation/feedback/jeff_2026-07-06_feedback_ledger.md)).
  Do not re-propose it as a recall or triage probe.
- **Deliberately not done:** loosening the threshold. See "What we reverted" above.
