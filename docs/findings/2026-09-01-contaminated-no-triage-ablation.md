# The 2026-02-13 no-triage ablation is contaminated — retracting "the single largest accuracy driver" — 2026-09-01

**Capability: 1 Triage.** **Status: measured.** **No API calls; no detector was run.**
Both arms are v7 artifacts already on disk, scored against Jeff's 2005 Ketubot list
(149, **BLIND**) through the recall harness's own aligner.

**Reproduce:** `python3 scripts/audit_no_triage_ablation.py`
→ [`results/v11/ablation_audit/no_triage_ablation_audit.json`](../../results/v11/ablation_audit/no_triage_ablation_audit.json)

---

## What this changes

[`docs/capabilities/1_triage.md`](../capabilities/1_triage.md) has carried this since
February, as the capability's only evidence that Stage 1 earns its place:

> **measured: triage is the single largest accuracy driver.** 111/127 (87.4%) with,
> 106/127 (83.5%) without

**The artifact behind it cannot support it, and the row is retracted.** Triage may well be
the largest accuracy driver — [`2026-08-31-triage-recall-price.md`](2026-08-31-triage-recall-price.md)
gives real reasons to think Stage 1 is broadly doing its job (14.3% precision on the pages
it discards). This particular experiment never showed it.

This is the other half of a hazard that finding already navigated. It knew not to *use*
the `--skip-triage` default when pricing the trade, and said so. Nothing had yet gone back
to the archived run **built on** that default, or to the conclusion drawn from it.

## The proof, which does not require reading the code

`results/v7/ablation_v7_no_triage.json` and `results/v7/ketubot_v7_2-60.json` are a
matched pair: v7, same era, the same 118 Ketubot 2a–60b pages, the same 1,485 segments.
The only claimed difference is Stage 1.

Turning a filter off can only **add** pages to examine. So it cannot subtract a story the
filtered arm already found on a page it already examined. Scored against the blind list:

| | triage ON | "triage OFF" |
|---|---|---|
| pages examined | 40 / 118 | 118 / 118 |
| proposals | 74 | 91 |
| classified `NOT_A_STORY` | 2 | **44** |
| Jeff's stories found (44 placed) | **42** | **37** |

**The arm that examined three times as many pages found five fewer stories.** Three of
those losses — Ketubot 52b, 53a, 54a — are on pages **both** arms examined in full, which
is arithmetically impossible for a change to the page set. (The other two are impossible
by the same logic one step further out: the no-triage arm held strictly more of the
story's text and still lost it. The count of 3 is the conservative one.)

So the ablation changed something other than which pages were seen.

## What it changed

```python
# story_detector_v7.py:658-664 — and unchanged in v8:727, v9:845, v10:1014, v11:1058
elif skip_triage:
    # Generate default triage (all DELIBERATION) so detection still works
    triage_results[ref] = [EventType.DELIBERATION] * n_segs
```

`skip_triage=True` does not bypass Stage 1. It **substitutes a false Stage 1 output**, and
two downstream consumers read it:

- **Stage 2's prompt** renders the label per segment — `[DELIBERATION] Seg 4:`
  (`story_detector_v7.py:75`) — under a header stating each segment "has been
  pre-classified by event type". Every page was therefore introduced to the model as
  containing no narrative event, and then the model was asked to find stories on it.
- **Post-processing `rule3_v6_ensemble`** demotes a proposal sitting on a page with
  "only 0 NARRATIVE_EVENT(s)" — true of all 118 pages by construction. Hence
  `NOT_A_STORY` 2 → 44.

`tests/ablation_test.py:196` is what produced the file, via
`run_pipeline(pages, skip_triage=True)`.

**The contest it actually ran was true labels against uniformly false ones** — a much
easier contest to win, and not one anybody chose to run.

## What follows

- **The capability row is struck, with the reason**, not deleted. A retraction that
  removes the claim also removes the record that it was ever believed.
- **The file is kept.** It is contaminated as a measurement and is now *evidence*; nothing
  should overwrite or delete it.
- **The flag is still live in v11**, and reads as though it does what its name says. The
  next person to reach for it to mean "no triage" gets the same answer.
  → [`work/2026-09-01-fix-skip-triage-flag.md`](../../work/2026-09-01-fix-skip-triage-flag.md)
- **The triage-vs-no-triage question is open again**, and is cheap to close correctly: the
  method in [`2026-08-31-triage-recall-price.md`](2026-08-31-triage-recall-price.md) —
  real cached labels, skip decision as the only variable — is exactly the corrected
  experiment, already implemented in `scripts/run_triage_recall_price.py`.

## Scope

This says nothing about the current triage numbers. The 2026-08-31 pricing and the
`N>=1` rule change that followed it both used cached labels and never touched this flag,
so **no shipped or published figure moves.** What moves is one historical claim, and the
status of one archived file.
