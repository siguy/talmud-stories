# The Gittin golden — 135 entries, two kinds of expert evidence, and two YES stories nobody has ever judged

**2026-09-02.** `results/canonical/gittin_canonical.json`, built by
[`scripts/build_gittin_golden.py`](../../scripts/build_gittin_golden.py). Gittin is the
third tractate with a golden and the first that is **BLIND end to end**: no Gittin
material was in any prompt, the run predates his list being opened, and the verdicts came
after the run.

| | |
|---|---|
| pages | 178 |
| entries | **135** |
| `expert_verdict` (he judged our span) | 25 |
| `expert_blind_list` (his list names a story our span overlaps) | 110 |
| `YES` / `BORDERLINE` / `NOT_A_STORY` | 113 / 4 / **18** |
| proposals with **no** expert evidence, kept out of the golden | 23 |
| his stories no proposal covers strictly | 3 |

**The 18 negatives are the thing this golden has that the other two do not.** They are
explicit expert rejections on a tractate that was never in a prompt — the only way to
measure precision without asking a model to grade itself.

## Two kinds of evidence, and why they may never be merged

Every entry carries `label_source`:

- **`expert_verdict`** — he was shown our span and answered. It judges the passage *and*
  the extent.
- **`expert_blind_list`** — his 2005 list names a story that our span overlaps under the
  strict test. It says **a story is there**. It says nothing about where it starts or
  ends, and it was written twenty years before the span existed.

Merging them would let an unvalidated boundary be quoted as expert-confirmed. That is
Lesson 24's shape — two sources, both his, that do not answer the same question — and a
test now fails if the split disappears.

**Every entry carries an expert label.** A proposal with no expert evidence is listed in
`unlabelled_proposals`, never written into `pages[].stories[]` with a null
classification. A null in a file called *golden* is read as a label by the next reader and
as a fact by the one after.

`BORDERLINE` stays its own answer for the same reason. He asked in 2026-07-06 for
contested cases to be kept and flagged; a golden that rounds them is the thing he
declined.

## What building it strictly uncovered

**Two `YES` proposals are on no expert list, and nobody has ever ruled on them:**

| | |
|---|---|
| **Gittin 57b:0-4** | Nebuzaradan and the bubbling blood of Zechariah |
| **Gittin 68a:7-12** | Solomon sends Benayahu to capture Ashmedai |

Both are famous aggadot. Both were **counted as matching his list** in
`results/recall/gittin_listed_keys.json`, and both were therefore left out of the 30-item
unlisted screen and the 25 sent to him.

The cause is the loose window, exactly as `STATUS.md` warns:

| his entry | its loose window | what our span at that spot actually is |
|---|---|---|
| `gittin_079` — the 400 captive children | 57a:22 → 57b:12 | 57b:0-4, **Nebuzaradan** |
| `gittin_097` — Resh Galuta and Rav Sheshet | 67b:18 → 68a:9 | 68a:7-12, **Ashmedai** |

The window is up to 14 segments wide and credits a proposal anywhere inside it. On
Kiddushin it was already shown to credit a different passage on the same daf in 2 of 6
cases checked by name. **This is the third and fourth instance, and the first found by a
consumer rather than by hand-checking.** Building the golden on the strict test is what
surfaced them: the loose test says "found", the strict test says "found *this*", and only
the second can label an entry.

### A claim we sent him is wrong

The 2026-09-01 email says:

> *"All 59 we called 'certain' are on your list; none of the extras we propose is one."*

**The first half is false.** Two of the 59 are not on his list. The second half stands.

It is very likely these are two more stories we found and he did not — they are the kind
of aggadah his lists are full of — but *likely* is not a verdict, and this project has
just been reminded that a passage is settled only by a ruling on that passage
([lesson](../../lessons/_a-policy-answer-does-not-certify-a-case.md)). They are recorded as
`indicated`, they stay out of the golden, and they go on the next page he sees.
→ [`gittin-two-unjudged-yes`](../../work/2026-09-02-gittin-two-unjudged-yes.md)

## Why the builder imports the recall module instead of re-implementing the match

`strict_matches()` calls `recall.locate` and `recall.overlap_frac` from
`measure_recall_vs_expert_list.py` — the same functions `measure_strict_recall.py` uses.
A golden built on a second, subtly different notion of "matched" would disagree with the
recall figure, and nothing in either file would say why. One definition, one place.

## What this golden is not for

**Do not score it with the composite.** The composite is built from ratios over pages
already in the golden, so deleting expert validations makes it go *up* (CLAUDE.md rule 5).
Counts are pinned in `GOLDEN_COUNTS` and the two-evidence split in `GITTIN_SHAPE`, both in
`tests/test_bookkeeping.py`, and both are asserted on every run.

**It is not a Classification measurement.** 110 of the 135 entries are labelled from a
blind list, which cannot be evidence about our precision on spans he never saw. The
measurement is [a separate item](../../work/2026-08-31-classification-point-estimate.md).
