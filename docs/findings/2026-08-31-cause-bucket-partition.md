# The miss-cause split is now a partition by construction

**Date:** 2026-08-31
**Capability:** 1 Triage, 2 Detection
**Status:** fixed, guarded
**Item:** [`work/2026-08-31-cause-bucket-partition.md`](../../work/done/2026-08-31-cause-bucket-partition.md)

---

## The defect

`measure_recall_vs_expert_list.py` printed the miss-cause split as though it were a
partition and never checked it was one:

```
CAUSE of the 3 misses: 4 triage discarded the page, 2 page examined and nothing proposed
```

The total came from the run's proposals (`not in_detector`). The first bucket came from
`triage_lost` — **every** story on an unexamined page, found or not. Those coincide only
while a story on an unexamined page cannot be found. That stops being true the moment a
detected file's proposals disagree with its own `skipped_by_triage` flags, which the
merged artifacts in `results/v11/triage_recall/` do deliberately.

This is the only line in the pipeline that attributes a miss to Triage rather than
Detection. Lesson 35 exists because charging one capability's losses to another sends the
fix to the wrong place; a split that silently fails to cover the misses is that failure
with no warning attached.

## The fix — structural, not defensive

Both buckets are now derived from the misses, so they partition by construction:

```python
missed      = [r for r in rows if not r['in_detector']]
triage_lost = [r for r in missed if not r['survived_triage']]
kept_missed = [r for r in missed if     r['survived_triage']]
```

The assertion remains, but it can now only fire if that derivation is edited — it guards
the code, not the data. **Preferred over asserting on the old computation**, per the item:
an invariant that cannot be violated beats one that is checked.

`triage_lost_all` (all stories on unexamined pages) is kept for the `TRIAGE recall` line
and the `TRIAGE-LOST` listing, where it is the correct population.

## The disagreement is now surfaced, not swallowed

A hard assert would have made the merged artifacts unmeasurable — and they are legitimate
inputs of exactly the mismatching kind, which is why the item said not to trade one away
for the other. Instead the harness warns and names the cases:

```
WARNING 3 story/stories are FOUND on pages this file still flags skipped_by_triage
(e.g. Kiddushin 10b, Kiddushin 14a, Kiddushin 69a). Expected for the merged artifacts in
results/v11/triage_recall/ ... While it holds, the TRIAGE and DETECTION lines above
describe the SHIPPED skip decision, not this run; the RECALL line is unaffected.
```

That last clause is the part worth having: it says exactly which numbers on screen can
still be trusted.

## Verified

Merged artifact, the case that produced `4 + 2 != 3`:

```
CAUSE of the 3 misses: 1 triage discarded the page, 2 page examined and nothing proposed
```

**No published number moved** — checked, not assumed:

| | recall | triage | detection | causes |
|---|---|---|---|---|
| Ketubot, shipped run | 96.0% | 98.0% | 97.9% | 3 + 3 = 6 ✓ |
| Kiddushin, shipped run | 93.3% | 95.6% | 97.7% | 4 + 2 = 6 ✓ |

Guarded by `tests/test_recall_cause_buckets.py` — 7 tests written first and watched fail,
including the exact row-shape that produced the bad split.

## Bounds

- The warning fires per *run*, not per page; it names the first three cases only.
- It does not attempt to decide which of the two sources is right. It cannot: both are
  legitimate depending on what the file is for.
