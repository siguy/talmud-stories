# One ruler for Detection and Classification — 2026-08-30

**Why:** neither artifact we had could measure both. The goldens are built *from*
detector output, so they can never contain a story we did not propose — useful for
precision, useless for recall. Jeff's blind lists can measure recall but carry no
verdicts. `scripts/build_ruler.py` joins them, with every verdict on disk folded in.

**Result — measured.** Kiddushin's Detection cell is filled for the first time, and the
Classification numbers this project has been quoting turn out not to be classification
numbers.

| capability | Ketubot | Kiddushin |
|---|---|---|
| **Detection** (BLIND) | **96.0%** (143/149) · strict 87.9% | **93.3%** (83/89) · strict 84.3% |
| **Classification** (CIRCULAR) | **87.9% – 94.8%** (n=173, Mar 2026) | **67.4% – 92.1%** (n=89, Apr 2026) |

Artifacts: [`scripts/build_ruler.py`](../../../scripts/build_ruler.py) ·
`results/rulers/{ketubot,kiddushin}_ruler.json` ·
[`tests/test_build_ruler.py`](../../../tests/test_build_ruler.py)

---

## 1. It reproduces what was already established, then goes further

The build is only trustworthy if it returns the numbers arrived at independently, so
both are asserted in the test file: Ketubot recall **143/149 = 96.0%**, from
`measure_recall_vs_expert_list.py`; Ketubot precision **0.879** on the 2026-03-17 round,
which is where the quoted 86% comes from; Kiddushin **0.674** on 2026-04-23, the 68%.

What is new is everything the join makes visible.

## 2. The Classification numbers were never Classification numbers

A verdict of `incorrect` records that Jeff rejected something. It does not say **what he
rejected**. Reading the notes and sorting them:

| round | n | rejections by what he objected to |
|---|---|---|
| Ketubot 2026-03-17 | 173 | classification 9 · **boundary 7** · confidence 4 · merge 1 |
| Ketubot 2026-02-26 (v8 delta) | 43 | **boundary 7 · merge 4** · classification 2 · confidence 1 · unreadable 9 |
| Kiddushin 2026-04-23 | 89 | **confidence 10** · classification 7 · boundary 3 · unreadable 9 |
| Kiddushin 2026-07-06 (wave 4) | 15 | **boundary 5** · unreadable 6 |

Most rejections are not about whether the passage is a story. They are boundary
complaints, merge complaints, and disagreements about our confidence *level* — three
different capabilities (FRAMEWORK §1), pooled into one number and then reported as
Classification.

`adjust` is treated as **accepted** for the same reason: it means *"this is a story and
the boundary is wrong"*. Counting it against Classification turns a boundary failure
into a fake precision problem.

So precision is reported as a **range**, not a point:

- **lower bound** — every rejection counts (this is the old number)
- **upper bound** — only rejections disputing that it is a story count; unreadable notes
  fall here too, which is exactly what makes it a bound and not the answer

**Ketubot 87.9 – 94.8. Kiddushin 67.4 – 92.1.** The gap between the tractates is far
smaller than 86-vs-68 suggested; most of that apparent gap was Kiddushin's reviewers
objecting to confidence levels and boundaries, on an older detector.

The honest reading: **we still do not have a point estimate for Classification**, and the
way to get one is to make the reviewer say which thing is wrong, not to keep re-deriving
it from free text. That is a review-UI change, and it belongs with `NEXT/04`.

## 3. Detection recall is softer than 96% under a strict test

The published test asks whether any proposal overlaps the **search window** the aligner
used to find the story. That window runs up to 14 segments and routinely straddles a daf
boundary, so a proposal anywhere nearby is credited.

Requiring instead that a proposal overlap a segment the story **actually occupies**:

```
Ketubot    96.0%  ->  87.9%     12 stories credited by proximity only
Kiddushin  93.3%  ->  84.3%      8 stories
```

The pattern in the 12 is consistent and worth acting on: they are **cross-page stories
whose text sits on the continuation daf, where we proposed nothing at all.** Ketubot 17a
is typical — the story is entirely within Ketubot 17b segment 2, and Ketubot 17b, 50a and
51a each carry **zero proposals**. We are credited because a different story on the
preceding daf was proposed and the window spans the break.

Both numbers are in the artifact. `recall` stays the published test so comparisons hold;
`recall_strict` is the sensitivity. **Neither is wrong — but a claim of "96% of stories
found" should be quoted as 96% loose / 88% strict**, and the 8 points between them are a
concrete, named work item rather than noise.

## 4. Kiddushin Detection, measured for the first time

**93.3% (83/89 blind stories), strict 84.3%.** Misses: 10a, 13b, 21b, 26a, 68b, 81b.

Against the ≥95% provisional gate this is **below**, where Ketubot is above. That is the
first like-for-like comparison of the two tractates on a capability that matters, and it
supports what Wave 1 suspected: the detector generalises less well than the Ketubot
numbers implied.

The denominator is 89 — blind entries only, the appendix excluded (see
[the list parse finding](kiddushin_list_parse_2026-08-30.md) §4).

## 5. What the join also fixed

- **All 16 previously-unfolded Kiddushin verdicts are now in** (2026-05-26: 1,
  2026-07-06: 15). Both rounds turn out to be almost entirely boundary complaints, which
  is why their all-causes precision looks catastrophic (0.0 and 0.267) and their
  classification-only precision is 1.0.
- **37 → 52 Ketubot proposals carry no verdict at all.** They were never reviewed. That
  is the honest denominator problem behind any precision claim.
- **Verdict keys are matched by segment overlap, not equality.** Keys encode the span the
  reviewer saw, and spans move between runs, so exact matching silently drops verdicts
  from older rounds. Matches are labelled `exact` or `overlap` per entry.

## 6. What this does not do

- It does not add the stories we never proposed **to the goldens** — that is `NEXT/10`
  step 2, and it is what turns a golden into a resource rather than a record of our own
  performance. The ruler now names them: 6 for Ketubot, 6 for Kiddushin.
- It does not rebuild Kiddushin's golden on a current run. Its verdicts were given on v7
  output while the detector is v11, so its precision range describes v7.
- The `unclassified` notes (9 + 9 + 6) are the width of the precision range. Reading them
  by hand would narrow it; guessing at them would not.
