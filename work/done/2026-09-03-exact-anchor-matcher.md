---
title: Locate an expert story by exact unique phrase, not by a growing gram-set window
capability: [detection, boundaries]
tractate: [ketubot, kiddushin, gittin, yevamot]
blocked_by: []
awaiting: []
writes: [scripts/measure_recall_vs_expert_list.py, scripts/measure_strict_recall.py,
         results/recall/, tests/test_exact_anchor_matcher.py,
         docs/findings/2026-09-03-exact-anchor-matcher.md, STATE.md, WORK.md]
finding: docs/findings/2026-09-03-exact-anchor-matcher.md
superseded_by:
---

# Locate an expert story by exact unique phrase, not by a growing gram-set window

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then this.

## The problem

Every recall figure on the board depends on `locate()` in
`scripts/measure_recall_vs_expert_list.py`, which finds an expert's story by comparing
**sets of Hebrew 4-grams per segment** — word order and position discarded — and then
grows a window while coverage improves. Accumulating segments can only *add* grams, so
nothing penalises a too-wide window: a neighbour sharing `אמר ליה` extends it. Windows run
to 14 segments, and the loose figure credits a proposal anywhere inside one.

**Measured:** 5 of Yevamot's 96 loose credits are a different story on the same daf; on
Kiddushin it was 2 of 6 cases checked by name.

## The claim to test

Jeff's 2005 text is essentially verbatim Vilna, so exact phrase matching should work and
the abbreviation problem the harness was built around (`א"ל` vs `אמר ליה`) is mostly not
present. Measured on Yevamot's 102 stories, 2026-09-03, before this item was filed:

- 102/102 contain at least one exact 6-word phrase from Sefaria
- 102/102 contain at least one exact 6-word phrase **unique in the whole tractate**
- median 85% of a story's 6-word shingles match exactly
- anchoring first-and-last unique phrase: median located span **1 segment**, max 8 —
  against the current median 7, max 14. All five loose-only cases collapse to one segment.

**Re-derive these numbers here; they were measured in a scratch session and are not on
disk.** A tractate with no unique anchor is possible and must be *checked per tractate*,
never assumed — fuzzy 4-grams stay as the fallback for those.

## Method

1. Anchor on unique exact word-shingles; extend the span while shingles keep matching
   **contiguously**, not while a gram-set keeps growing.
2. Add `--matcher exact|fuzzy` to both `measure_recall_vs_expert_list.py` and
   `measure_strict_recall.py`. Fuzzy stays the fallback per story, and stays reachable.
3. Re-measure **all four** tractates and either reproduce the banked figures or **name and
   explain every story that moves, one by one**. Expect strict recall to move up slightly
   and loose to move down toward it — that is the point.
4. Ketubot's ground truth is a `.doc` parsed by a different path than the three JSON
   lists (`parse_expert_doc`, not `parse_kiddushin_list.py`) and must be checked
   separately.

## How you know it worked

Every story whose located span changes is named with its old and new span and a one-line
reason. A count that does not break down that way means some moved unexplained.

## Guardrails

- **`scripts/evaluate_golden.py` is immutable.** It is not in `writes:` and must not be
  touched.
- **`results/recall/<t>_jeff2005_matches.json` unsuffixed is the denominator `board.py`
  reads.** A new matcher writes a **suffixed** variant until it is proven; never over the
  banked file.
- **Unique anchors locate precisely but can under-state extent** if only a story's middle
  is unique — and boundary scoring reads the same locations. Extension must recover the
  full extent, and the span-length distribution is the evidence that it does.
- Do not fold this into any golden, and do not restate a recall number anywhere until the
  four-tractate reconciliation is complete.

## When done

Write the finding to `docs/findings/2026-09-03-exact-anchor-matcher.md`, add an
`## Outcome` section below, and
`python3 scripts/board.py finish 2026-09-03-exact-anchor-matcher`.

## Outcome

**Done, measured, and shipped behind a flag.** The finding is
[`docs/findings/2026-09-03-exact-anchor-matcher.md`](../../docs/findings/2026-09-03-exact-anchor-matcher.md).

The claim held on every list: **all 452 stories across the four tractates carry at least
one exact 6-word phrase that is unique in their own tractate**, and nothing fell back to
the 4-gram aligner anywhere. The brief's Yevamot figures re-derived at 102/102, 102/102,
median 0.83 (it said 0.85) of shingles matching exactly.

**Loose recall collapses onto strict; strict barely moves.** Ketubot 96.0→87.2,
Kiddushin 93.3→84.4, Gittin 100.0→97.3, Yevamot 94.1→89.2, against strict figures of
87.2 / 83.3 / 97.3 / 89.2. Three of the four strict figures are unchanged **to the
story**. Same-day fuzzy re-runs reproduce every banked number exactly, so the change is
additive and the comparison matched.

**Two things moved, both named.** One story changes strict verdict — Ketubot's testimony
of R. Yosi the Priest, a baraita that appears **twice** (26b:7 and 27a:1); Jeff cites 27a,
we proposed only the 26b copy, and the 7-segment window covered both. Ketubot strict is
**130/149**. And two Ketubot stories (27a, 51a) move **from Detection's column to
Triage's**: their windows spilled onto an examined neighbouring daf while their own daf
was skipped, so Ketubot triage is **96.6%, not 98.0%**, and detection-given-triage 90.3%.
Every other change is a loose credit withdrawn — 12 / 8 / 3 / 5 — including the five
Yevamot cases `yevamot_strict.json` had flagged for checking by name. All five were the
window reaching a neighbour on the same daf.

**Independent check, not used by the matcher:** agreement with Jeff's own daf labels goes
51→85 (Kiddushin), 90→104 (Gittin), 72→97 (Yevamot).

**Why the default is still `fuzzy`, and what is left.** Not doubt about the matcher.
`build_ruler.py`, `audit_proposal_credit.py`, `audit_detection_density.py` and
`build_gittin_golden.py` call `recall.locate` **directly**; flipping this harness alone
would leave the ruler and the recall row locating the same stories differently. The
unsuffixed `results/recall/*.json` the board reads are untouched, and the exact artifacts
are banked with an `_exact` suffix. **The cutover across those five call sites is the
follow-on**, and it retires the loose/strict double-quote entirely — it is Simon's call
because it moves two published Ketubot cells.

Two things fixed mid-item, both found by measuring rather than by reading: the first
extension rule accepted any exact phrase within 250 tokens of the anchor and stretched
a 55-word Gittin story across 21 segments (the positional test replaced it); and exact
`coverage` was first reported as the fraction of phrases placed, which is far lower than
gram coverage and would have called 25 of 149 Ketubot stories "unlocated" — it now
reports gram coverage of the located span, the same quantity `locate` returns.
