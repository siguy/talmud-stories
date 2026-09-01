---
title: The recall harness reports miss-causes as a partition without checking it is one
capability: [triage, detection]
tractate: []
blocked_by: []
awaiting: []
finding:
superseded_by:
---

# The recall harness reports miss-causes as a partition without checking it is one

**Self-contained.** A fresh session executes this with no other context.
Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then this.
**Capabilities: 1 Triage, 2 Detection** — this is the line that attributes a miss to one
or the other, so a wrong split sends the fix to the wrong capability.
**Depends on Jeff: no. Cost: under an hour, no API calls.**

## The problem

`scripts/measure_recall_vs_expert_list.py` (~line 261) prints:

```python
log.info('CAUSE of the %d misses: %d triage discarded the page, %d page examined and '
         'nothing proposed in range', len(rows) - len(found), len(triage_lost), len(kept_missed))
```

The sentence asserts a **partition**: every miss is either triage-discarded or
examined-but-nothing-proposed. Nothing checks that it is one.

The total, `len(rows) - len(found)`, is derived from **the current run's proposals**.
The two buckets come from `survived_triage`, which reads the `skipped_by_triage` flags
**baked into the detected file**. When those two disagree, the line prints a split that
does not add up — and says so with a straight face.

Observed 2026-08-31:

```
CAUSE of the 3 misses: 4 triage discarded the page, 2 page examined and nothing proposed in range
```

4 + 2 = 6 ≠ 3.

**Why it is latent rather than loud:** in normal use the detected file's triage flags and
its proposals come from the same run, so the numbers agree and the bug is invisible. It
surfaces only when a run's proposals disagree with its own `skipped_by_triage` flags —
which is exactly what the `results/v11/triage_recall/*_plus_*.json` measurement artifacts
deliberately do.

**Why it matters beyond the cosmetic:** this line is the *only* place the pipeline
attributes a miss to Triage vs Detection. Lesson 35 exists because charging one
capability's losses to another sends the fix to the wrong place. A split that silently
fails to cover the misses is that failure with no warning attached.

## Reproduce

```bash
python3 scripts/measure_recall_vs_expert_list.py \
  --expert-json results/expert_lists/kiddushin_2005.json --expert-filter recall \
  --tractate Kiddushin \
  --detected results/v11/triage_recall/kiddushin_v10_notrim_plus_skipped.json \
  --golden results/canonical/kiddushin_canonical.json \
  --out /tmp/scratch_cause_bucket.json
```

*(If `*_plus_skipped.json` is absent it is gitignored and regenerated in seconds:
`python3 scripts/merge_triage_recall_run.py --tractate kiddushin`.)*

## Method

1. **Write the failing test first** and watch it fail (Lesson 31 — a guard that cannot
   fail guards nothing). Build a small fixture whose `skipped_by_triage` flags disagree
   with its proposals; assert the harness refuses rather than printing a bad split.
2. **Assert the partition** where it is claimed:
   `len(triage_lost) + len(kept_missed) == len(rows) - len(found)`.
3. **Make the diagnostic name the actual cause.** A bare `AssertionError` on a measurement
   script is a poor result. The message should say that the detected file's
   `skipped_by_triage` flags disagree with its proposals, and name a page where they do.
4. **Decide deliberately between assert and warn, and record the reason.** The
   `results/v11/triage_recall/` artifacts are *legitimate* inputs of exactly this kind — a
   hard assert makes the harness unusable for the measurement it was just used for. A
   warning that names the mismatch and suppresses the misleading line may be the better
   answer. **Do not make the merged artifacts unmeasurable in the name of strictness.**
5. Check whether `survived_triage` should be **derived from the run's own proposals**
   rather than from a stored flag. If it can be, the two sources cannot diverge and the
   assertion becomes structural rather than defensive — the better fix, if it holds.

## How you know it worked

- The reproduce command above no longer prints a split that fails to sum.
- A test exists that fails when the assertion is removed — **demonstrated, not assumed**.
- The merged `results/v11/triage_recall/*_plus_*.json` artifacts are still measurable,
  and the session states explicitly what the harness now does with them.
- `python3 -m pytest tests/ -q` passes (was 107 passed / 1 skipped on 2026-08-31).

## Guardrails

- **`scripts/evaluate_golden.py` is IMMUTABLE.** This is a different harness
  (`measure_recall_vs_expert_list.py`) and may be edited — do not confuse them.
- Any `evaluate_golden.py` invocation needs `--output <scratch path>`; bare it destroys an
  unreproducible baseline (CLAUDE.md rule 4).
- **No published recall number may move.** This changes a *reporting* line, not a
  measurement. If a headline figure changes, stop — something else is wrong. Re-run the
  Ketubot and Kiddushin recall commands and confirm 96.0% / 93.3% on the shipped runs.
- Buckets presented as a partition must be asserted as one (Lesson 21). That is the rule
  this item is an instance of; apply it to any *other* bucket-split the file prints while
  you are in there, rather than fixing only the one that was caught.

## When done

Write the finding to `docs/findings/<date>-<slug>.md`, add an `## Outcome` section
below, then `python3 scripts/board.py finish <slug>`. **Never delete it.**

## Outcome

**Fixed 2026-08-31.** → [`docs/findings/2026-08-31-cause-bucket-partition.md`](../../docs/findings/2026-08-31-cause-bucket-partition.md)

Took the **structural** option the item preferred rather than the defensive one: both
buckets are now derived from `missed`, so they partition by construction and the assertion
can only fire if that derivation is edited. `triage_lost_all` is kept separately for the
`TRIAGE recall` line and the `TRIAGE-LOST` listing, where all-stories-on-unexamined-pages
is the correct population.

The merged artifact that printed `CAUSE of the 3 misses: 4 ... 2 ...` now prints
`1 ... 2 ...`, and **no published number moved** — Ketubot 96.0 / 98.0 / 97.9 with causes
3+3=6, Kiddushin 93.3 / 95.6 / 97.7 with causes 4+2=6, all verified rather than assumed.

Did **not** make the merged artifacts unmeasurable, per the item's guardrail. Instead the
harness warns, names the offending stories, and says which lines on screen remain
trustworthy: the RECALL line is unaffected, while TRIAGE and DETECTION describe the
shipped skip decision rather than the file in hand.

Guarded by `tests/test_recall_cause_buckets.py` — 7 tests written first and watched fail.
