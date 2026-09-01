# One narrative event is enough — the corroboration clause, removed

**Date:** 2026-08-31
**Capability:** 1 Triage
**Datasets:** Jeff's 2005 Ketubot list (149, BLIND) and Kiddushin list (90, BLIND)
**Status:** measured, and **SHIPPED** — `src/event_triage.py` changed
**Follows:** [`2026-08-31-triage-recall-price.md`](2026-08-31-triage-recall-price.md)

---

## What changed

```
- if narrative_count >= 2:                              return False   # keep
- if narrative_count >= 1 and verbal_count >= 2:        return False   # keep
+ if narrative_count >= 1:                              return False   # keep
```

A page needed its narrative event **corroborated** — by a second one, or by two verbal
acts — or it was discarded unexamined. It no longer does.

## Why this rule and not "keep everything"

The [previous finding](2026-08-31-triage-recall-price.md) measured only the two endpoints:
the shipped rule, and examining every discarded page. The endpoints bracket the trade but
do not locate the best point inside it. Sweeping the intermediate rules against both blind
lists — no API calls, reusing the Stage 2 output already produced — puts almost the entire
gain at the very first step:

**Ketubot**

| rule | extra calls | recall | false proposals | calls/story |
|---|---|---|---|---|
| shipped | 0 | 96.0% | 0 | — |
| **N≥1** | **4** | **96.6%** | **3** | **4** |
| N≥1 or V≥3 | 70 | 96.6% | 13 | 70 |
| keep everything | 124 | 96.6% | 17 | 124 |

**Kiddushin**

| rule | extra calls | recall | false proposals | calls/story |
|---|---|---|---|---|
| shipped | 0 | 93.3% | 0 | — |
| **N≥1** | **4** | **95.6%** | **2** | **2** |
| N≥1 or V≥4 | 30 | 96.7% | 4 | 10 |
| keep everything | 100 | 96.7% | 7 | 33 |

**On Ketubot, `N≥1` captures 100% of the gain available from reading the entire tractate,
at 1/31st of the cost.** Everything beyond it is 120 calls and 14 false proposals for zero
additional stories.

The discarded pages with `N≥1` are 8 across both tractates and **6 carry a real story** —
a ~75% hit rate against **14.3%** for discarded pages as a whole. This is not a marginal
threshold; it is a clause that was discarding a high-value population wholesale.

## The result

| | Ketubot | Kiddushin |
|---|---|---|
| **Triage recall** | 98.0% → **98.7%** ✓ | 95.6% → **97.8%** |
| corpus examined | 44% → 46% | 38% → 41% |
| **end-to-end recall** | 96.0% → **96.6%** | 93.3% → **95.6%** |
| extra Stage 2 calls | 4 | 4 |
| false proposals added | 3 | 2 |

**Ketubot Triage now clears its gate with margin** rather than sitting exactly on it.
**Kiddushin, the board's only failing cell, goes from 2.4 points below the gate to 0.2.**
It does not clear ≥98% — the honest reading is that it is now within noise of it, on a
denominator of 90, and the gate itself is still PROVISIONAL.

No page that was previously examined is now skipped — asserted, not assumed, and true by
construction since the new rule is strictly looser.

## What was deliberately NOT adopted

**A `V >= 4` clause.** It would recover Kiddushin 10b (N=0, V=5), a real story, taking
Kiddushin to 96.7%. It also costs **70 extra Ketubot calls for zero extra Ketubot
stories**. That is a threshold fitted to one case in one tractate — Lesson 18's shape,
and precisely the kind of rule that looks free on the data it was chosen from. Pinned by a
test (`test_verbal_acts_alone_never_keep_a_page`) so the decision is revisited on purpose
rather than by drift.

## The overfitting question, stated honestly

**The rule was selected using the same blind stories it is scored against.** That is a
real hazard and it is worth being explicit about why this particular change is not
primarily a fitting artifact:

1. **`N≥1` is a boundary, not a tuned parameter.** It is "any narrative evidence at all".
   The arbitrary number was the old rule's *2*; there is no principled argument on record
   for why a narrative event should need corroboration, and the docstring's rationale
   ("stories often have 1 narrative setup followed by dialogue") actually argues *against*
   the clause it was justifying.
2. **It is corroborated by an observation that predates this measurement by six months.**
   Ketubot 51a was recorded as a false skip *found by hand* on 2026-02-13 and has sat in
   `docs/capabilities/1_triage.md` ever since. `N≥1` catches it. A rule fitted to today's
   data would not be expected to also fix a case documented in February.
3. **It helps both tractates**, which were measured independently.
4. **The rejected candidate is the fitted one**, and it was rejected on exactly this
   ground.

**The residual risk is real and untested.** The honest test is Gittin, Yevamot and Eruvin,
where blind lists exist and the detector has never run — a genuine held-out set. Until
then, treat the *magnitude* as measured on two tractates and the *generalisation* as
indicated.

## Cost at scale

The change costs ~2 percentage points more of the corpus examined. Extrapolated over Shas
that is real money but small: triage still skips more than half of every tractate. The
cost that matters is **5 additional false proposals across two tractates** reaching the
reviewer — against 24 for the keep-everything alternative — and review throughput is the
project's binding constraint.

## What this does not fix

Four stories remain lost to triage: **Ketubot 20a, 82b** and **Kiddushin 10b, 21b**.
20a and 82b are not really triage's to fix — Stage 2 fails to find them even when handed
the page ([previous finding](2026-08-31-triage-recall-price.md)). 10b needs the rejected
`V≥4` clause. 21b resists both.

## Reproduce

```bash
python3 scripts/sweep_triage_rules.py --tractate kiddushin      # the rule sweep, no API
python3 scripts/merge_triage_recall_run.py --tractate kiddushin --live-rule
python3 scripts/measure_recall_vs_expert_list.py \
  --expert-json results/expert_lists/kiddushin_2005.json --expert-filter recall \
  --tractate Kiddushin \
  --detected results/v11/triage_recall/kiddushin_v10_notrim_plus_liverule.json \
  --golden results/canonical/kiddushin_canonical.json \
  --out results/v11/triage_recall/kiddushin_liverule.json
```

Guarded by `tests/test_triage_single_narrative.py` (9 tests, written first and watched
fail). `tests/test_event_triage.py` and `tests/test_triage_failure_default.py` each had one
case pinning the old boundary; both were updated in place with a note rather than deleted,
so the change stays visible from the tests that used to assert the opposite.

## Note on existing outputs

**No published number moves.** The shipped runs used cached triage decisions
(`results/v7/event_triage_*.json`), which are unchanged; this rule affects future runs.
The figures above are what a re-run would produce, computed by splicing the already-paid-for
Stage 2 output for the 8 newly-examined pages into the shipped runs.
