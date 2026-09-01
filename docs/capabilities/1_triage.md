# Capability 1 — Triage

**Definition:** decide whether a page is worth examining at all — see
[`FRAMEWORK.md` §1.1](../../FRAMEWORK.md).
**Gate:** ≥98% of true stories surviving (PROVISIONAL)
**Current:** **Ketubot 98.7%** — 2 of 149 lost — while examining 46% of pages;
**Kiddushin 97.8%** — 2 of 90 lost — while examining 41% of pages. Both on Jeff's 2005
lists (**BLIND**), both measured with `scripts/measure_recall_vs_expert_list.py`.
**The keep-rule changed on 2026-08-31** (a single NARRATIVE_EVENT is now enough); the
previous rule read 98.0% / 95.6%.

*Written 2026-08-30 from the sources in `work/done/2026-08-30-capability-histories.md`. History, not status —
status lives in [`STATUS.md`](../../STATUS.md).*

---

## What we tried

| when | what | outcome | evidence |
|---|---|---|---|
| 2026-02-13 | **Stage 1 event triage introduced** (Increment 2/5). Every segment classified NARRATIVE_EVENT / VERBAL_ACT / DELIBERATION / HABITUAL; a page is kept if ≥2 NARRATIVE_EVENT, or ≥1 NARRATIVE_EVENT + ≥2 VERBAL_ACT | shipped. 66.1% skip rate on Ketubot 2-60 (78 of 118 pages); **1 false skip found by hand** (Ketubot 51a) | `84c9f43` |
| 2026-02-13 | Threshold relaxed from "≥2 narrative events" to also keep 1 narrative + 2 verbal, so dialogue-carrying stories survive | shipped; zero false skips on the four strong story pages checked (10b, 8b, 2b, 60a) | `84c9f43` |
| 2026-02-13 | **Ablation: does triage help or hurt?** v7 with triage vs v7 without, scored against Jeff's 127 labels (**CIRCULAR**) | ~~**measured: triage is the single largest accuracy driver.** 111/127 (87.4%) with, 106/127 (83.5%) without~~ **— RETRACTED 2026-09-01. The artifact cannot support the claim.** The "without" arm came from `run_pipeline(skip_triage=True)` (`tests/ablation_test.py:196`), which does not bypass Stage 1 — it stamps every segment `DELIBERATION`, which Stage 2 renders into its prompt and post-processing reads as an empty page. Proven independently of the code: **the arm examining 3x the pages found 5 FEWER of Jeff's stories, 3 of them on pages both arms examined** — impossible for a change to the page set. The contest it ran was true labels vs uniformly false ones. Triage may still be the largest driver; this never showed it | `6ea4204`, [`contaminated_ablation`](../findings/2026-09-01-contaminated-no-triage-ablation.md) |
| 2026-03-27 | Kiddushin first run under v7 | 67% skip rate (109 of 162 pages), reported without any recall check | `14a5f3a` |
| 2026-05-18 | **Wave 1 Issue #5 — lexical override.** A page containing any of five canonical Hebrew introducers (`מעשה ב`, `הנהו בי תרי`, `ההוא ד`, `ההוא גברא`, `כי הא ד`, matched on the consonantal skeleton) forces Stage 2 to run whatever Stage 1 said | shipped and **it worked**: Kiddushin 45a and 53a — two stories Jeff had flagged as missed — recovered, each yielding one real story. 9 Kiddushin pages and 5 Ketubot pages moved from skipped to processed | `eff0218`, [`wave1_results.md`](../findings/2026-05-18-wave1-results.md) |
| 2026-08-30 | **First measurement of what triage discards.** Traced the 6 blind-list recall misses back through the pipeline | **measured: Stage 1 discards 124 of 222 Ketubot pages (56%)** — 1,535 segments never examined. 19 of Jeff's 149 stories touch a discarded page; 16 survive only because the other half of the daf pair was kept; **3 are lost outright** (Ketubot 20a, 72b, 82b — both pages of each pair discarded) | `9f7ddf8`, [`recall_miss_diagnosis`](../findings/2026-08-30-recall-miss-diagnosis.md) |
| 2026-08-30 | **Triage recall computed for the first time**, against the BLIND 2005 list | **measured: 98.0%** (146 of 149 survive) at 44% of pages examined. Reframed from "the biggest unmeasured thing in the project" to **a trade to be priced** | `c900ee4` |
| 2026-08-31 | **Kiddushin triage recall measured — the cell that had been empty for the life of the project.** Same script as Ketubot, run the same day so the comparison holds (Lesson 11) | **measured: 95.6%** (86 of 90) while examining **38%** of pages — 2.4 points below Ketubot for 6 points more of the corpus skipped. **All of Kiddushin's end-to-end recall deficit is here**, not in Detection: detection-given-triage is 97.7% vs Ketubot's 97.9%. Wave 1's lexical override is worth **+1.1 points** of it (one story, Kiddushin 49b), priced against a blind set for the first time | [`kiddushin_recall`](../findings/2026-08-31-kiddushin-recall.md) |
| 2026-08-31 | **A failed triage call no longer discards the page.** `TRIAGE_FAILED` as a distinguishable provenance value; `should_skip_page()` fails open on it; failures counted and named | shipped, and **0 shipped skip decisions change** — proven against the caches, which contain no failures. Ten failure-injection tests, written first and watched fail | [`finding`](../findings/2026-08-31-triage-failure-default.md), Lesson 21 |
| 2026-08-31 | **The trade priced at last — Stage 2 re-run on every discarded page, both tractates.** Skip decision the only variable: shipped triage labels from cache (not the all-DELIBERATION `--skip-triage` default), real cross-page context, `gemini-2.5-flash` matching the shipped run's provenance. All 224 discarded pages verified to reproduce their skip decision before any call | **measured. 224 calls, 0 errors, 28 proposals, 4 real. Ketubot 96.0% -> 96.6% (+1 story, 124 calls/story); Kiddushin 93.3% -> 96.7% (+3 stories, 33 calls/story).** Examined end-to-end the two tractates converge to **96.6% / 96.7%** — the whole Ketubot/Kiddushin gap is the triage threshold and it **closes**. Precision on discarded pages 4/28 = **14.3%**, so Stage 1 is broadly doing its job. **And 2 of the 3 stories blamed on Ketubot triage (20a, 82b) are still missed with every page examined** — Detection failures wearing Triage's label | [`triage_recall_price`](../findings/2026-08-31-triage-recall-price.md) |
| 2026-08-31 | **The corroboration clause removed — `should_skip_page()` now keeps any page with ≥1 NARRATIVE_EVENT.** Chosen by sweeping intermediate rules against both blind lists (`scripts/sweep_triage_rules.py`, no API), because the price finding had measured only the two endpoints | **measured and SHIPPED. Ketubot triage recall 98.0% -> 98.7%, Kiddushin 95.6% -> 97.8%**, for **8 extra Stage 2 calls** and 5 false proposals across both tractates. The 8 pages the clause discarded hold **6 real stories** — ~75% against 14.3% for discarded pages overall — including **Ketubot 51a**, the false skip found by hand on 2026-02-13 and never fixed. On Ketubot `N>=1` captures **100% of the gain available from reading the entire tractate at 1/31st the cost**. A `V>=4` clause was rejected: +1 Kiddushin story for 70 useless Ketubot calls, a threshold fitted to one case (Lesson 18) | [`triage_single_narrative`](../findings/2026-08-31-triage-single-narrative.md), `tests/test_triage_single_narrative.py` |
| 2026-09-01 | **`skip_triage` fixed and renamed `examine_all_pages`** (v11 only; v7-v10 frozen). The flag now gates the page selection alone — Stage 1 runs whenever labels are not supplied, and supplied labels are never overwritten. A second all-DELIBERATION default in the Stage 2 loop became `[]` (renders `UNKNOWN`) | shipped, **0 published or shipped numbers move** — every shipped run used cached labels and never touched the flag. 10 failure-injection tests written first, 9 of 10 watched fail; they also pin that v7-v10 keep the stub, so the retracted ablation stays reproducible from the code that made it | [`examine_all_pages_fix`](../findings/2026-09-01-examine-all-pages-fix.md) |
| 2026-09-01 | **The ablation re-run correctly**, replacing the row struck the same day. Real cached labels, skip decision the only variable, shared half of the two arms **byte-identical** so there is no run-to-run noise in it (Lesson 22 by construction). Scored against the golden (**CIRCULAR** — precision only) | **measured: Stage 1 buys ~8 points of classification precision on both tractates.** Ketubot precision 89.2% -> 81.1%, FP 18 -> 35, TP 149 -> 150, F1 90.0% -> 86.0%; Kiddushin 85.3% -> 77.1%, FP 14 -> 24. **Nothing was lost by examining more pages** — the invariant whose violation exposed the contaminated original. The February claim's *direction* was right; its evidence never was | [`corrected_ablation`](../findings/2026-09-01-corrected-triage-ablation.md) |

## What we reverted, and why

**Nothing has been reverted in this capability.** Every change to Stage 1 since it was
built is still shipped: the relaxed threshold, the Wave 1 lexical override, the
2026-08-31 failure-default fix, and the 2026-08-31 removal of the corroboration clause. That is
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
- **Rule (changed 2026-08-31):** keep the page if `NARRATIVE_EVENT ≥ 1`. Otherwise skip.
  Was `NARRATIVE_EVENT ≥ 2` **or** `NARRATIVE_EVENT ≥ 1 and VERBAL_ACT ≥ 2`; the
  corroboration half was measured as the richest seam of missed stories in the corpus
  and removed. **Verbal acts alone still never keep a page** — deliberately, and pinned
  by `test_verbal_acts_alone_never_keep_a_page`.
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

Reproduce the *old* skip rates directly from those files: Ketubot 73/118 + 51/104 =
**124 of 222 (56%)**; Kiddushin **100 of 162 (62%)** (measured 2026-08-30). Under the
2026-08-31 rule those become **120 of 222 (54%)** and **96 of 162 (59%)** — 8 pages'
difference in total. The cached triage *labels* are unchanged, so the shipped outputs
are unaffected; the new rule applies to future runs.

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

**Kiddushin was below the gate at 95.6%, and the rule change took it to 97.8%** — 0.2
points short, which on a denominator of 90 is one story and is within any plausible noise
band for this capability (none has ever been measured). Ketubot moved 98.0% → 98.7% and
now clears with margin. The paragraph below describes the pre-change position.

**Kiddushin as measured under the old rule: 95.6%** (2026-08-31). **It is also
now known to be recoverable rather than structural**: examining every page brings
Kiddushin to 96.7% against Ketubot's 96.6%, closing the gap entirely
([`triage_recall_price`](../findings/2026-08-31-triage-recall-price.md)). The suspicion
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

- ~~Re-run the triage-vs-no-triage ablation correctly~~ — **done 2026-09-01**, with no
  API calls: the Stage 2 output on the discarded pages already existed and had only ever
  been scored against the blind lists, never against the golden. **Stage 1 buys ~8 points
  of precision on both tractates.** What it opened: **the 27 extra proposals it suppresses
  have still never been read.** They are scored false positives only because the golden
  cannot contain a story from a page triage never let anyone see, so nobody knows how many
  are real. That is the number that decides whether ~8 points of precision is a saving or
  an artifact — and it is a reading task, not a compute one.

- ~~Re-run Stage 2 on the discarded pages and price the trade~~ — **done 2026-08-31**,
  on **both** tractates rather than only Ketubot's 124 pages. Exchange rate 124 calls
  per story (Ketubot) vs 33 (Kiddushin). What it opened: the *review* cost of the 24
  extra false proposals is still unpriced, and that half lands on the bottleneck
  capability. **Do not loosen Stage 1 until it is.**
- **Read the 24 non-matching proposals from that run.** They are either hallucinations
  on legal pages or real stories absent from Jeff's list, and those two answers point
  opposite ways. Untested — the run checked proposals against the list, not for quality.
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
