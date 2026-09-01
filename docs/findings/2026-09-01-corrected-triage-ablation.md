# The corrected triage ablation: Stage 1 buys ~8 points of precision — 2026-09-01

**Capability: 1 Triage.** **Status: measured.** **No API calls** — the Stage 2 output on
the discarded pages was already paid for by
[`2026-08-31-triage-recall-price.md`](2026-08-31-triage-recall-price.md); this is the
first time it has been scored **against the golden** rather than against the blind lists.

Replaces the row struck by
[`2026-09-01-contaminated-no-triage-ablation.md`](2026-09-01-contaminated-no-triage-ablation.md).
Stage 1 has had no valid direct measurement that it improves accuracy since that
retraction. It has one now.

**The result:** turning triage off costs **~8 points of classification precision on both
tractates** and buys at most **+0.6 points** of golden recall. **The February claim's
direction was right; its evidence was not.** Now the direction is measured.

---

## Why this is a valid A/B and the 2026-02-13 one was not

| | 2026-02-13 (retracted) | this |
|---|---|---|
| "no triage" arm | `skip_triage=True` → every segment stamped `DELIBERATION` | **real cached labels**, only the skip decision overridden |
| shared half of the two arms | separately generated | **byte-identical**, asserted by `merge_triage_recall_run.py` |
| lost a story on a page both arms examined | **yes, 3** — arithmetically impossible | **no** |

The second row is what makes this cleaner than a re-run could be. The merged arm keeps
every non-skipped page's stories byte-identical to the shipped run, so there is **no
run-to-run noise in the shared half** (Lesson 22 is satisfied by construction, not by a
repeat run): the only difference between the columns is the 224 pages Stage 1 discarded.

Both arms are the v10 generation with real labels. This therefore does **not** reproduce
the retracted `111/127 vs 106/127` — a different detector generation against a
smaller golden — and should not be read as restoring it.

## The numbers, as counts

Golden is **CIRCULAR** — precision only, never recall (CLAUDE.md rule 5).

**Ketubot** (222 pages; 124 discarded by Stage 1)

| | triage ON (shipped) | every page examined |
|---|---|---|
| true positives | 149 | **150** |
| false positives | 18 | **35** |
| false negatives | 15 | **14** |
| precision | **89.2%** | **81.1%** |
| recall | 90.9% | 91.5% |
| F1 | **90.0%** | **86.0%** |

**Kiddushin** (162 pages; 100 discarded)

| | triage ON (shipped) | every page examined |
|---|---|---|
| false positives | 14 | **24** |
| true positives / false negatives | *unchanged* | *unchanged* |
| precision | **85.3%** | **77.1%** |
| F1 | **90.0%** | **85.3%** |

**Nothing was lost by examining more pages** — TP rose, FN fell, and no entry appears in
the second arm's miss list that was not in the first. That is the invariant whose violation
exposed the original contamination, and it now holds.

## Three things this does not say

**1. "False positive" here means "not in the golden", not "wrong".** The golden holds only
stories the detector previously proposed on pages triage *kept*, so a proposal on a
never-examined page has had no chance to be in it. The 2026-08-31 finding flagged the same
population and said plainly that the non-matching proposals **have not been read**. Some
of the +17 and +10 may be real stories nobody has ever judged.

**2. Kiddushin's TP is unchanged even though the blind list says 3 stories were
recovered** (10b, 14a, 69a). Those three are on Jeff's 2005 list and are *not in the
golden* — so the golden cannot see them. This is the circularity CLAUDE.md warns about,
visible in a single cell: **the measure that shows triage helping is structurally unable to
show what it costs.** Read this finding against
[`2026-08-31-triage-recall-price.md`](2026-08-31-triage-recall-price.md), never instead of
it.

**3. The composite hid it.** Precision fell 8 points and false positives nearly doubled
while the composite moved **0.9115 → 0.8954**, about 1.6 points. Rule 5 says never verify
with the composite; this is what that looks like when the underlying counts move hard.

## What it means for the gate

FRAMEWORK §1.1 marks the ≥98% triage bar PROVISIONAL, and the trade now has both halves
priced on both tractates:

- **What Stage 1 saves:** 56% / 62% of the corpus unexamined, and **~8 points of
  classification precision** it would otherwise give away.
- **What Stage 1 costs:** 3 Ketubot / 4 Kiddushin blind-list stories, of which 1 and 3 are
  actually recoverable by looking (2026-08-31).

So the honest summary is that **Stage 1 is worth keeping and was worth measuring** — and
that the reason to keep it is precision and reviewer load, not compute. 124 extra calls per
tractate is pennies; 17 extra unjudged proposals landing in front of the one reviewer is
not, and review throughput is the project's binding constraint.

## Reproduce

No API calls. The merged arms are gitignored (`.gitignore:25`) and regenerate
deterministically:

```bash
python3 scripts/merge_triage_recall_run.py --tractate ketubot
python3 scripts/evaluate_golden.py \
  --detected results/v10/wave4_notrim/ketubot_v10_2-60_notrim.json \
             results/v10/wave4_notrim/ketubot_v10_61-112_notrim.json \
  --golden results/canonical/ketubot_canonical.json --output /tmp/triage_on.json
python3 scripts/evaluate_golden.py \
  --detected results/v11/triage_recall/ketubot_v10_2-60_notrim_plus_skipped.json \
             results/v11/triage_recall/ketubot_v10_61-112_notrim_plus_skipped.json \
  --golden results/canonical/ketubot_canonical.json --output /tmp/triage_off.json
```

**Always pass `--output`** — bare, `evaluate_golden.py` overwrites
`docs/golden/v7/baseline_ketubot.json` (CLAUDE.md rule 4; both files verified unchanged
after this run).
