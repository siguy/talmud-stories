# Gittin recall is 108/111, not 108/112 — the expert retracted one of his own entries

**2026-09-02.** Applies the retraction Jeff made on 2026-09-01
([his words](2026-09-02-jeff-answers-gittin.md)) to the artifacts, which had kept
scoring against all 112.

## What changed

`gittin_075` — Gittin 57a, the Sadducee's exchange with R. Ḥanina about the land's
fertility:

> *"I agree that this is not a story and should not have been included. The list was
> wrong. Great to have the AI correct it!"*

We proposed nothing on that passage, so it scored as one of four strict misses. **It is
not a miss.** It is the one shape of result a blind list cannot express on its own: a case
where the detector was right and the ground truth was wrong.

| | before | after |
|---|---|---|
| recall denominator | 112 | **111** |
| strict recall | 108/112 = **96.4%** | 108/111 = **97.3%** |
| loose recall | 112/112 = 100% | 111/111 = 100% |
| strict misses | 4 | **3** — 38b, 46b, 57a Beitar |

The three that remain are all passages he has confirmed **are** stories, so the deficit is
now entirely ours. Two of them (38b, 57a Beitar) he ruled on individually the same day;
46b he has not been asked about.

## Annotated, never deleted

The entry stays in `results/expert_lists/gittin_2005.json`. It carries
`counts_for_recall: false` plus a new `retracted_by_expert` block holding his exact words,
the date, and the source file. **`blind` stays `true`** — it was detector-blind, and still
is. Blindness is a fact about how the entry was produced; being a story is a fact about
the passage, and conflating the two would make the flag unable to answer either question.

This is the standing rule in [`docs/STORY_RULES.md`](../STORY_RULES.md): his lists are
evidence, so a disagreement is an annotation, never an edit. The one thing that makes this
case different is that the disagreement is **his own**, which is the only kind that can
change a denominator.

## What was regenerated

| file | how |
|---|---|
| `results/expert_lists/gittin_2005.json` | annotated by hand; `counts.recall_denominator` 112 → 111 |
| `results/recall/gittin_strict.json` | `measure_strict_recall.py --expert-json … --detected results/v11/gittin/gittin_v11.json` |
| `results/recall/gittin_jeff2005_matches.json` | `measure_recall_vs_expert_list.py`, same list, same run |
| `results/recall/gittin_strict_rc3.json` | same, against the R-C3 arm — a sibling left at 112 is a number someone quotes later |

`docs/findings/2026-08-31-gittin-first-run.md` carries a **Correction** at the head of its
recall section rather than an edit to its figures: the numbers there were true of what we
knew, and a finding that silently changes its own history stops being usable as a record.

## The one that should be checked

Every loader filters on the flag, so nothing needed a code change — but that is a property
worth re-testing rather than assuming. `tests/test_board_reports_what_it_holds.py` pins
that the board's count-for-recall equals the harness filter *and* the ruler denominator,
and it stays green here, which is the evidence that the three did not drift.

**The trap this avoided:** anything taking `len(stories)` as the denominator keeps 112 and
reports 96.4% forever, with no error and no way to notice. That is why the flags exist and
why CLAUDE.md says to filter on them.

## What it does not change

Boundaries. `tests/expert_boundary_targets_2005_gittin.json` is built from the extents Jeff
*chose*, and the 57a entry contributed targets like any other. A passage that is not a
story still has a boundary he drew, and removing it from a boundary exam would be
discarding evidence to make a different number move. The boundary set is untouched, and
the Gittin boundary figures stand.
