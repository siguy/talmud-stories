# The whole board now locates a story one way — the exact-anchor cutover

**2026-09-03.** Status: **measured and shipped as the default.**
Work item: [`work/done/2026-09-03-exact-matcher-cutover.md`](../../work/done/2026-09-03-exact-matcher-cutover.md).
Follows [the matcher itself](2026-09-03-exact-anchor-matcher.md), which measured the
change and shipped it behind a flag.

## What changed

`--matcher exact` is now the **default** in `measure_recall_vs_expert_list.py` and
`measure_strict_recall.py`, and the four scripts that called `recall.locate` directly —
`build_ruler.py`, `audit_proposal_credit.py`, `audit_detection_density.py`,
`build_gittin_golden.py` — now go through `recall.make_locator`. There is one locating
function for the whole board and one place to change it.

Before this, two of the six could use the better matcher and four could not, so the board
answered *"where is this story"* two different ways depending on which script was asked.
That is worse than either matcher alone.

## The numbers that moved, and where they now agree

| | Detection recall | | Triage recall | |
|---|---|---|---|---|
| | was | now | was | now |
| **Ketubot** | 96.0% loose / 87.9% strict | **87.2%** | 98.0% | **96.6%** |
| **Kiddushin** | 93.3% / 83.3% | **84.4% / 83.3%** | 95.6% | 95.6% |
| **Gittin** | 100.0% / 97.3% | **97.3%** | 100.0% | 100.0% |
| **Yevamot** | 94.1% / 89.2% | **89.2%** | 100.0% | 100.0% |

The ruler and the recall harness now report the **same** figure per tractate — 130/149,
76/90, 108/111 — which they did not before. Loose and strict coincide on Ketubot, Gittin
and Yevamot and differ by one story on Kiddushin.

The triage figures above are on the **shipped artifacts**, which still carry the
*previous* keep-rule; the live-rule pair (98.7% / 97.8%) has not been re-measured under
the new matcher and is flagged as such in
[`docs/capabilities/1_triage.md`](../capabilities/1_triage.md).

## Three things this exposed downstream

**1. The loose-credit population nearly vanished.** `audit_proposal_credit.py` found 35
proposals credited to an expert story by window alone, 11 of them `YES`/`HIGH_CONFIDENCE`
([the open item](../../work/2026-09-03-loose-credited-proposals.md)). Under exact
anchoring that bucket is **Gittin 0, Ketubot 0, Kiddushin 1** — and the one survivor,
Kiddushin 39b 8-10, is the single case that item now has to answer. Most of what looked
like a review backlog was a measurement artifact.

**2. One entry left the Gittin golden — correctly.** `Gittin 34a` segment 9 was in the
golden as `expert_blind_list` / `YES`. It was there because a 7-segment window credited it
to Jeff's `ההוא דאמר להו: אי לא **נסיבנא** עד תלתין יומין` — the man who did not **marry**
within thirty days, at 34a:11. Segment 9 is its near-identical neighbour: the man who did
not **return** within thirty days, the ferry case. Two formulaic cases one segment apart,
and the window covered both. Nobody ever labelled 34a:9; it is an unlabelled proposal now,
which is what it always was. Gittin's golden is **134 entries / 116 accepted**, repinned in
`GOLDEN_COUNTS` with that reason written beside it. **No other golden changes**, and the
count was verified by count, never by the composite (Critical Rule 5).

**3. The density finding survives.** `audit_detection_density.py` re-attributes stories to
the dapim their text actually sits on, so the density bands shift — but the shape it
reported is unchanged: recall 82% where a story is alone on its daf against 90% on dapim
with 4+, on the same 350-story denominator. The conclusion there did not depend on the
window.

## What is retired

**Stop quoting loose and strict as two figures.** They were two answers to one question,
separated by the search window. `measure_strict_recall.py` still prints both, and that is
now a self-check: if they diverge, a story is anchored somewhere its own segments are not.

Superseded measurements are kept, not deleted:
`results/recall/*_jeff2005_matches_fuzzy.json` holds the 4-gram reading of each tractate.
The unsuffixed files are the denominators `board.py` reads, as always.

## Guarded

`tests/test_build_ruler.py::test_the_window_no_longer_credits_a_story_we_never_proposed`
was the test that *pinned the bug* — Kiddushin 81b segment 9, a story every run failed to
propose and the loose window credited anyway. It now pins the fix, on a case that does not
depend on the aligner being right. `test_ketubot_detection_reproduces_the_published_recall`
carries the new number and the reason it moved; its real job is that the ruler and the
harness agree, whatever the number is.
