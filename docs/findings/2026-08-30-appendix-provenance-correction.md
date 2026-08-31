# The Kiddushin appendix is three findings, not one — 2026-08-30

**Corrects:** [`detection_classification_ruler_2026-08-30.md`](2026-08-30-detection-classification-ruler.md)
and commit `240c3cb`, both of which treat the five appendix cases as a single
category ("ours, therefore excluded"). **Status of every claim below: measured.**

**Result:** the Kiddushin recall denominator moves **89 → 90**. Loose recall is
unchanged at **93.3%** (83/89 → 84/90); **strict recall falls 84.3% → 83.3%**.

---

## 1. What prompted it

Simon: *"the 5 stories from Jeff's doc were detected by us! He said so. We just can't
find them in the previous UI validator instances we sent him."*

Both halves turned out to be right, and both were recorded wrongly.

**Why they could not be found in the UIs.** The Kiddushin review UIs store Hebrew as
escaped `\u05xx` sequences, not literal characters — 138,331 of them in
`validation/ui/kiddushin_review.html`, which reports **zero** Hebrew characters to any
plain-text search. Decode the escapes and all five passages are present at 97–100% in
every Kiddushin UI. The Ketubot UIs embed literal Hebrew, which is why the problem never
showed up there. Nothing was missing; the search could not see it.

## 2. What our runs actually proposed

Measured by searching every Kiddushin run for the passage **text** (character 4-grams
over the consonantal skeleton), not for its page reference —
`scripts/check_appendix_coverage.py`:

| case | Jeff's label | best span | contains | verdict |
|---|---|---|---|---|
| 33a | Yes | seg 5 | 99% | **proposed in full** (seg 6 partial in v7/v8; full from Wave 3) |
| 45a | Low confidence | seg 5 | 91% | **proposed in full** from Wave 1 (absent in v7) |
| 53a | Low confidence | seg 8 | 39% | **proposed, truncated** — the story occupies segs 8–9 |
| 71a | Low confidence | segs 4–5 | 38% | **proposed, truncated** — the story occupies segs 2–5 |
| 81b | Yes | seg 14 | 9% | **never proposed** — the story is seg 9 |

Two prior claims were wrong. Commit `240c3cb` records *"71a and 81b were never proposed
by any run"* — false for 71a, whose tail we proposed. And the same commit calls 33a
`PART` in every run, when it has been full since Wave 3. Both errors came from the old
coverage test, which asked whether a proposed span **touched a segment sharing >30%
vocabulary** with the case, rather than whether it **contained the story**. That script
now reports both, with the weaker test labelled as weak, and no longer crashes on run
files that have no `pages` key.

## 3. Why the denominator changes

Blindness and the recall denominator are different questions, and collapsing them is
what produced the error.

None of the five is **blind**: each is in Jeff's list because we put the page in front
of him. But circularity is only dangerous in the direction that **flatters**:

- 33a, 45a, 53a, 71a — in his list **because we proposed them**. Counting them can only
  raise recall. Excluded, as before.
- 81b — in his list because he read a page we showed him and found a story **we had
  missed**. Counting it can only *lower* recall. **Dropping it is what inflates the
  number**, so it stays in.

Hence `counts_for_recall`, separate from `blind`, in
`results/expert_lists/kiddushin_2005.json`. Denominator **90**; strictly blind **89**.

## 4. What that exposes about the loose test

Adding 81b moved strict recall (84.3% → 83.3%) but **not** loose recall. The ruler
entry says why:

```
kiddushin_r092   expert_segments = [Kiddushin 81b, seg 9]
                 detector_span   = [Kiddushin 81b, segs 1-3]
                 proposed = True (loose)      strict = False
```

The loose test credits us with finding a story at segment 9 because we proposed
segments 1–3 — six segments away, with **9% text overlap**. This is the first case
where the loose window can be shown to credit a story we can *prove* we never proposed,
independently of the aligner. It is direct evidence for the position FRAMEWORK §1.2
already takes: quote the strict number beside the loose one, and treat the loose one as
an upper bound.

## 5. What this is evidence about

The five cases are three different capability signals, which the single "not blind"
label hid:

| | capability | signal |
|---|---|---|
| 33a, 45a | **Detection** | successes, later confirmed by the expert |
| 53a, 71a | **Boundaries** | detection hits with the wrong extent — one half of a two-segment story |
| 81b | **Detection** | a genuine miss, caught by the expert reading a page we surfaced |

`NEXT/09` item 1b — ask Jeff to keep future appendices separate — is unchanged and now
better motivated: it is not only about provenance, it is about being able to tell these
three apart at all.
