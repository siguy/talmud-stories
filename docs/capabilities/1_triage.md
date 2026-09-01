# Capability 1 — Triage

**Definition:** decide whether a page is worth examining at all — see
[`FRAMEWORK.md` §1.1](../../FRAMEWORK.md).
**Gate:** ≥98% of true stories surviving (PROVISIONAL)
**Current:** **Ketubot 98.0%** — 3 of 149 lost — while examining 44% of pages;
**Kiddushin 95.6%** — 4 of 90 lost — while examining 38% of pages. Both on Jeff's 2005
lists (**BLIND**), both measured with `scripts/measure_recall_vs_expert_list.py`
(Ketubot 2026-08-30 `c900ee4`, Kiddushin 2026-08-31).
**Priced 2026-09-01:** the saving is 56% / 62% of the corpus, at **1 story per 41 / 25**
pages not examined — and **no threshold change buys any of it back**, because the misses
are labelling failures ([`triage_recall_price`](../findings/2026-09-01-triage-recall-price.md)).

*Written 2026-08-30 from the sources in `work/done/2026-08-30-capability-histories.md`. History, not status —
status lives in [`STATUS.md`](../../STATUS.md).*

---

## What we tried

| when | what | outcome | evidence |
|---|---|---|---|
| 2026-02-13 | **Stage 1 event triage introduced** (Increment 2/5). Every segment classified NARRATIVE_EVENT / VERBAL_ACT / DELIBERATION / HABITUAL; a page is kept if ≥2 NARRATIVE_EVENT, or ≥1 NARRATIVE_EVENT + ≥2 VERBAL_ACT | shipped. 66.1% skip rate on Ketubot 2-60 (78 of 118 pages); **1 false skip found by hand** (Ketubot 51a) | `84c9f43` |
| 2026-02-13 | Threshold relaxed from "≥2 narrative events" to also keep 1 narrative + 2 verbal, so dialogue-carrying stories survive | shipped; zero false skips on the four strong story pages checked (10b, 8b, 2b, 60a) | `84c9f43` |
| 2026-02-13 | **Ablation: does triage help or hurt?** v7 with triage vs v7 without, scored against Jeff's 127 labels (**CIRCULAR**) | ~~**measured: triage is the single largest accuracy driver.** 111/127 (87.4%) with, 106/127 (83.5%) without~~ — **RETRACTED 2026-09-01. The conclusion does not follow from the artifact.** The "without" arm was produced by `skip_triage=True` (`tests/ablation_test.py:196`), which does not bypass Stage 1 — it stamps every segment `DELIBERATION` and feeds that to Stage 2. The contest it ran was **true labels vs uniformly false ones**, not triage vs no triage. Triage may still help; this never showed it | `6ea4204`, [`triage_recall_price` §4](../findings/2026-09-01-triage-recall-price.md) |
| 2026-03-27 | Kiddushin first run under v7 | 67% skip rate (109 of 162 pages), reported without any recall check | `14a5f3a` |
| 2026-05-18 | **Wave 1 Issue #5 — lexical override.** A page containing any of five canonical Hebrew introducers (`מעשה ב`, `הנהו בי תרי`, `ההוא ד`, `ההוא גברא`, `כי הא ד`, matched on the consonantal skeleton) forces Stage 2 to run whatever Stage 1 said | shipped and **it worked**: Kiddushin 45a and 53a — two stories Jeff had flagged as missed — recovered, each yielding one real story. 9 Kiddushin pages and 5 Ketubot pages moved from skipped to processed | `eff0218`, [`wave1_results.md`](../findings/2026-05-18-wave1-results.md) |
| 2026-08-30 | **First measurement of what triage discards.** Traced the 6 blind-list recall misses back through the pipeline | **measured: Stage 1 discards 124 of 222 Ketubot pages (56%)** — 1,535 segments never examined. 19 of Jeff's 149 stories touch a discarded page; 16 survive only because the other half of the daf pair was kept; **3 are lost outright** (Ketubot 20a, 72b, 82b — both pages of each pair discarded) | `9f7ddf8`, [`recall_miss_diagnosis`](../findings/2026-08-30-recall-miss-diagnosis.md) |
| 2026-08-30 | **Triage recall computed for the first time**, against the BLIND 2005 list | **measured: 98.0%** (146 of 149 survive) at 44% of pages examined. Reframed from "the biggest unmeasured thing in the project" to **a trade to be priced** | `c900ee4` |
| 2026-08-31 | **Kiddushin triage recall measured — the cell that had been empty for the life of the project.** Same script as Ketubot, run the same day so the comparison holds (Lesson 11) | **measured: 95.6%** (86 of 90) while examining **38%** of pages — 2.4 points below Ketubot for 6 points more of the corpus skipped. **All of Kiddushin's end-to-end recall deficit is here**, not in Detection: detection-given-triage is 97.7% vs Ketubot's 97.9%. Wave 1's lexical override is worth **+1.1 points** of it (one story, Kiddushin 49b), priced against a blind set for the first time | [`kiddushin_recall`](../findings/2026-08-31-kiddushin-recall.md) |
| 2026-08-31 | **A failed triage call no longer discards the page.** `TRIAGE_FAILED` as a distinguishable provenance value; `should_skip_page()` fails open on it; failures counted and named | shipped, and **0 shipped skip decisions change** — proven against the caches, which contain no failures. Ten failure-injection tests, written first and watched fail | [`finding`](../findings/2026-08-31-triage-failure-default.md), Lesson 21 |
| 2026-09-01 | **The trade priced on both tractates, from disk alone** — the ceiling, the cached-label diagnosis, and every keep-rule variant. `scripts/price_triage_trade.py` | **measured: nothing cheap recovers anything.** Ceiling **1 story per 41 calls** (Ketubot, +2.0 pts) and **1 per 25** (Kiddushin, +4.4). Relaxing to `narrative>=1` recovers **0 on both**, because **10 of 13 killer pages carry ZERO narrative events** — the misses are labelling, not threshold. The daf-neighbour rule priced at **+60/+34 calls for 0 stories** and is dead. Also **retracts the 2026-02-13 ablation** (row above) | [`triage_recall_price`](../findings/2026-09-01-triage-recall-price.md) |

## What we reverted, and why

**Nothing has been reverted in this capability.** Every change to Stage 1 since it was
built is still shipped: the relaxed threshold, the Wave 1 lexical override, and the
2026-08-31 failure-default fix. That is
worth stating plainly, because it is unusual in this project — and because it is also a
warning. Triage is the one capability where **no change has ever been reverted, and no
change has ever been measured against a blind dataset before shipping.** The two facts
are related.

**Priced and killed, 2026-09-01 — the daf-neighbour rule.** 6 of the 7 stories Stage 1
loses span a daf boundary, needing two independent keep-decisions to go right, so
"examine the daf either side of every kept page" looked like the cheap structural fix.
Priced from the cached labels before any code was written: **+60 Ketubot calls and +34
Kiddushin, for zero stories.** It fails because in every pair at least one page has no
examined neighbour — the killed stories sit inside *runs* of discarded pages, not on the
edge of kept ones. **Do not propose it again**
([`finding` §3](../findings/2026-09-01-triage-recall-price.md)).

The nearest thing to a revert is a decision *not* to act:

- **2026-08-30 — the 56% skip rate was not "fixed".** The obvious reaction to
  "we throw away half the tractate" is to loosen the threshold. It was deliberately not
  done. Triage exists to save money; a recall bar quoted without its cost saving is
  meaningless, and 2% of recall for a 56% cost cut may be a good trade. The decision was
  recorded as a trade to be priced (`NEXT/01`), not a defect to be patched
  ([`FRAMEWORK.md` §1.1](../../FRAMEWORK.md)). **Do not loosen Stage 1 without producing
  the exchange rate first.** — **Answered 2026-09-01, and the answer vindicates the
  restraint: loosening does not work.** Every threshold variant cheap enough to be worth
  running recovers **0 stories on both tractates**; every variant that recovers one
  examines 58–100% of the corpus.

## Current best — the exact configuration

- **Code:** `src/event_triage.py` — `EventTriager.triage_page()` and
  `EventTriager.should_skip_page()`.
- **Rule:** keep the page if `NARRATIVE_EVENT ≥ 2`, **or**
  `NARRATIVE_EVENT ≥ 1 and VERBAL_ACT ≥ 2`. Otherwise skip.
- **Override:** `_page_has_story_introducer()` in `src/story_detector_v11.py:2011` —
  five introducers, nikud stripped (`_STORY_INTRODUCERS`, line 2002). Any hit forces
  Stage 2 (`src/story_detector_v11.py:1072`).
- **Failure default — FIXED 2026-08-31.** An unparseable response used to be tagged all
  DELIBERATION under the comment *"safest — won't skip pages incorrectly."* The comment
  was backwards: all-DELIBERATION gives `narrative_count == 0`, failing both
  keep-conditions, so a failed call **silently discarded the page** — Lesson 21's shape in
  the one stage whose errors leave no trace. A failure now writes `EventType.TRIAGE_FAILED`,
  `should_skip_page()` **fails open** on it, and `summarize_triage()` counts and names the
  failed pages. Proven to change **0** of the shipped skip decisions (the caches hold no
  failures), so no published number moves. The **historical** failure rate remains unknown
  and unrecoverable, because nothing counted it.
  → [`2026-08-31-triage-failure-default.md`](../findings/2026-08-31-triage-failure-default.md),
  guarded by `tests/test_triage_failure_default.py`
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

**Kiddushin is measured, and it is below the gate: 95.6%** (2026-08-31). The suspicion
recorded here — that a 62% skip rate against Ketubot's 56% would cost recall — was
correct, and is now measured rather than suspected. **This is the first capability
number that differs materially between the two tractates**, and it is the whole of
Kiddushin's end-to-end gap; Detection is the same on both
([`kiddushin_recall`](../findings/2026-08-31-kiddushin-recall.md)).

That makes the provisional 98% gate a sharper problem than it was, because it was set on
the tractate that skips less. The exchange rate is now measurable on two tractates:
**Kiddushin gives up 2.4 more points of recall for 6 more points of corpus skipped** —
about one story per 1.5 points of pages not examined. Whether that is a good trade is the
open end-to-end question for Simon, not something to fix by loosening the threshold (see
"What we reverted").

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

- ~~Re-run Stage 2 on the 124 discarded Ketubot pages and price the trade~~ — **the
  recall half is done 2026-09-01**, on both tractates and with no API calls: ceiling
  1 story per 41 (Ketubot) / 25 (Kiddushin) calls. What it opened, and what is now the
  top item here: **the bypass is broken and the review cost is still unpriced.**
  `skip_triage=True` stamps every segment `DELIBERATION` in every version v7–**v11**, so
  the experiment cannot be run correctly until that is fixed
  (`work/2026-09-01-triage-bypass-and-precision.md`). Until then there is **no measurement
  of how many false proposals reach Jeff per story recovered** — the number that decides
  this, given review throughput is the binding constraint.
- ~~Measure Kiddushin triage recall~~ — **done 2026-08-31**, 95.6%. What it opened:
  the same measurement on Gittin, Yevamot and Eruvin, which cannot be run until the
  detector has produced triage decisions there.
- **Mine the opener lexicon instead of hand-writing it** (`docs/history/2026-08-28-PLAN-wave7-opener-lexicon.md`, DRAFT,
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
