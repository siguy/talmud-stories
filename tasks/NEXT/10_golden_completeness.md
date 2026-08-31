# NEXT 10 — Make the goldens complete: fold in every verdict, add the stories we never proposed

Read `STATUS.md` and `FRAMEWORK.md`. **Capability: 3 Classification (and the ground truth
under all six).** **No API calls** — every input already exists on disk.

## The problem, in one line

**A golden dataset built from detector output can only ever contain stories the detector
proposed.** Ours are, so they cannot. On Ketubot we can already name five stories Jeff
listed that appear in no golden at all.

On top of that, expert verdicts we *have* been given are sitting unapplied in both
tractates. This is Lesson 1's failure — feedback split into an "apply" pile and a "later"
pile, and the later pile never revisited — still live, three rounds on.

## What is missing, counted

**Kiddushin** — `results/canonical/kiddushin_canonical.json`, 96 entries / 85 accepted:

| round | verdicts | folded in? |
|---|---|---|
| `kiddushin_review_2026-04-23.json` | 96 | yes — this is the whole golden |
| `kiddushin_review_2026-05-26 (1).json` | 1 | **no** |
| `jeff comms/wave4_kiddushin_review_2026-07-06.json` | 15 | **no** |

Also: it is built on `results/v7/kiddushin_v7.json` while the detector is now v11, and
its own `known_missing_stories` field names five stories it does not contain.

**Ketubot** — `results/canonical/ketubot_canonical.json`, 182 entries / 159 accepted:

| bucket | count |
|---|---|
| `canonical_review_deferred_log` ∪ `needs_review_log` (17 overlap) | **26 unique** |
| `prior_rounds_skipped` | 8 |
| `boundary_corrections_deferred` | 5 |
| stories on Jeff's blind 2005 list that are in **no** golden | **5** |

The deferred notes are not junk. A sample: *"The merge is correct but the next paragraph
should also be included"*, *"our interpretation is correct — the change should be
implemented by adding this portion to the story"*. These are approvals and precise
instructions, recorded and then dropped.

The five absent stories are Ketubot 20a, 53a, 67b, 72b, 82b — all `in_detector: false`,
so they were never proposed and therefore never had a verdict to fold in.

## What "golden" should mean

Today it means *our proposals, corrected*. It should mean *the best available answer for
what stories are in this tractate*, which is a union of three sources:

```
detector output          (what we proposed)
  ∪ every expert verdict (what he said about it — including the deferred ones)
  ∪ expert-listed stories we never proposed   ← the part that is missing entirely
```

The third source is what turns a golden from a record of our own performance into a
resource. It is also what the endgame needs: a database that omits stories the expert
listed is not a story database.

## Method

1. **Fold in the unapplied verdicts.** Kiddushin's 16 first — smallest and cleanest.
   Then Ketubot's 26 + 8 + 5. For each: apply, or record why not. Nothing stays silently
   deferred (Lesson 17). Append to the ledger first.
2. **Add the expert-listed stories we never proposed**, flagged so they cannot be
   mistaken for detector output:
   `source: expert_list`, `detector_proposed: false`, `blind: true`.
   Ketubot's five come from `results/recall/ketubot_jeff2005_matches.json`
   (`in_golden: false`). Kiddushin's come from `NEXT/06` — **run 06 first**, its miss
   list is this input.
3. **Rebuild Kiddushin's golden on a current run**, not v7. Its 85 accepted entries were
   judged against output three detector versions old, which is why its precision number
   cannot be read against Ketubot's.
4. **Report both counts, both ways** — entries and accepted — per FRAMEWORK §3.

## Why this matters more than it looks

The scoreboard says Classification is 86% Ketubot / 68% Kiddushin and calls it the
weakest capability. That gap is **partly an artifact of this task not being done**:
Ketubot's golden has absorbed several rounds of correction on two detector versions,
Kiddushin's has absorbed one round on one old version. Until both are built the same way,
the comparison measures our bookkeeping as much as the detector.

## How you know it worked

Every verdict on disk is either applied or has a written reason. Both goldens name the
run they were built on and the rounds they contain. Every expert-listed story appears,
with `detector_proposed` saying whether we found it. Counts quoted entries-and-accepted.

## Guardrails

- **Do not let an added expert story pollute precision.** It was never proposed, so it
  cannot count for or against precision — it belongs in recall and in the resource.
  Filter on `detector_proposed` wherever precision is computed.
- The goldens stay **CIRCULAR** for precision (FRAMEWORK §3). Adding blind stories to a
  circular set does not make the set blind; it makes it *complete*. Those are different
  properties and the file must record both per entry.
- `scripts/evaluate_golden.py` is IMMUTABLE. If a new field breaks it, adapt the data.
- Rebuilding Kiddushin on a current run invalidates the stale 68%. Say so; do not quietly
  compare the new number to the old one (Lesson 22 — regenerate the baseline same-day).
