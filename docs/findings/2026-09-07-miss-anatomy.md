# Every miss, anatomised — the density profile was Triage's, and the rest is one bug

**2026-09-07.** Status: **measured.** No API calls. Reproduce with

```bash
python3 scripts/audit_miss_anatomy.py --out results/recall/miss_anatomy.json
```

Corrects [`2026-09-03-detection-density.md`](2026-09-03-detection-density.md), which is
kept as written. It reported *"recall is lowest where a story is alone on its daf"* and
concluded the constraint is **salience**, aiming the next Detection attempt at the
isolated story in legal surroundings. It also named the reason it could not go further:
*"alone on the daf" and "surrounded by legal material" are the same dapim in this data.*

**They are not.** The cached Stage 1 labels measure the second directly, and separating
them dissolves the profile.

## The two variables, separated

*Isolation* = how many of Jeff's stories share the daf. *Context* = whether the segments
of the daf **outside every expert story on it** carry any narrative label at all. The
second is computed with the stories' own segments removed, so it is not partly caused by
the thing it predicts.

| | end-to-end | given the page was examined | the misses |
|---|---|---|---|
| **alone / legal-only** | **81.4%** (57/70) | **93.4%** (57/61) | 9 TRIAGE, 3 blank, 1 Mishnah |
| alone / has-narrative | 94.2% (49/52) | 94.2% (49/52) | 1 blank, 2 near |
| multi / legal-only | 94.3% (132/140) | 94.3% (132/140) | 7 adjacent, 1 near |
| multi / has-narrative | 87.9% (167/190) | 87.9% (167/190) | 11 adjacent, 8 near, 3 far, 1 Mishnah |

**All nine Triage misses on the entire board are in one cell** — a story alone on a daf
whose remaining segments carry no narrative label. That cell is 70 of 452 stories, and
12.9% of them are lost before Stage 2 ever runs. Every other cell has a Triage miss rate
of **zero**.

Condition on the page having been examined and the profile **reverses**:

| expert stories on the daf | 1 | 2 | 3 | 4 | 5+ |
|---|---|---|---|---|---|
| recall, given the page was examined | **93.8%** | 94.2% | 90.5% | 91.7% | **85.4%** |

Detection is **best** on the lone story and worst on the crowded daf. The 83.3%-vs-90.7%
profile that refuted the attention hypothesis was Triage's losses pooled into Detection —
the exact error `CLAUDE.md` warns about in its own Don't list, committed inside the
finding that measures recall.

**What survives, and it is worth as much:** *legal-only* is a real and strong predictor —
**of a Stage 1 skip**. A daf whose only narrative material is the story itself is the daf
Stage 1 discards. That is a measured, single-variable description of Triage's entire
failure mode, on a signal Stage 1 has already computed. Salience was the right idea aimed
one stage too late.

## Where the rest of the misses are: one segment away

Every miss classified by distance from the nearest thing the detector actually proposed:

| | n |
|---|---|
| Triage — daf never examined | 9 |
| Mishnah filter withheld it (found, then removed) | 2 |
| **proposal ≤1 segment away** | **18** |
| proposal 2–6 away | 11 |
| proposal >6 away | 3 |
| nothing proposed anywhere on the daf | 4 |

**4 of 452 stories are true blanks.** In 29 of the 38 Detection misses the model was
reading the right stretch of the daf.

## Reading all 18 adjacent cases: not a boundary bug

The obvious hypothesis is mis-bounding — we found the story and cut it in the wrong
place. **In 18 of 18 the nearby proposal is a *different* story, and in almost all of them
it is the missed story's formulaic twin.**

| daf | Jeff's story | what we proposed instead |
|---|---|---|
| Kiddushin 40a | R. Zadok and the noblewoman | **Rav Kahana and the noblewoman** |
| Yevamot 121b (x2) | *"who is of the house of Ḥiwai — Ḥiwai has drowned"* | *"who is of the house of Ḥasa — Ḥasa has drowned"* |
| Yevamot 63a | R. Elazar and the field ploughed crosswise — *"trading is better than this"* | Rav among the sheaves — **same closing line** |
| Ketubot 67b | Hillel buys the poor man a horse and a runner | the people of Upper Galilee buy a poor man meat |
| Ketubot 61a (x2) | Abuha bar Ihi; the two pious men — who serves each kind, and Elijah | Rav Anan and the mushroom dish; Ameimar at the king's door |
| Ketubot 112a | the Sadducee to R. Ḥanina on his father's field | the Amorite on the palm by the Jordan |

The 2–6 band is the same mechanism at greater reach: on Ketubot 53a, Ketubot 77a,
Kiddushin 30a, Kiddushin 71a and Gittin 38b the run produced **exactly one proposal** on a
daf holding two to six of Jeff's stories.

**The mechanism, stated:** *given a run of formulaically parallel anecdotes, the detector
returns a representative rather than each instance.* It is not blindness and it is not a
boundary disagreement. Counted per daf, the total is near-right and the members are wrong:

| expert stories on the daf | 1 | 2 | 3 | 4 | 5+ |
|---|---|---|---|---|---|
| mean proposals produced | 1.27 | 2.33 | 3.00 | 3.87 | 5.07 |

Roughly the right *number*, falling behind from three, with substitution underneath — we
propose passages not on his list while omitting members of a cluster.

## Why nothing saw this until now

The retired 4-gram window was structurally incapable of showing it. Parallel anecdotes
share their vocabulary almost completely — `ההוא דהוה קאמר ואזיל`, `אמר ליה`, a shared
closing line — so a window opened on one member covered the cluster and credited every
member of it. **The single defect the old matcher was worst at hiding is the single
largest defect we have.** That is [Lesson 41](../../lessons/) in its most expensive form.

## What this changes

1. **The next Detection attempt is not a criteria rewrite and not a second pass over dense
   dapim.** It is splitting formulaic clusters — up to 29 stories, ~6 points of Detection
   recall across four tractates. New item:
   [`formulaic-cluster-splitting`](../../work/2026-09-07-formulaic-cluster-splitting.md).
2. **`second-story-guard` is the same family and should be re-ranked with it.** That item
   addresses a second story sharing *one segment* being trimmed away; this is a second
   story in an *adjacent* segment never proposed at all. Same expert complaint, two
   stages apart.
3. **Triage has a named, single-variable failure mode** and a signal it already computes.
   Folded into [`board-reads-stale-triage`](../../work/2026-09-01-board-reads-stale-triage.md),
   which must re-measure Triage anyway.
4. **`jeff:boundary-end-rule` does not block any of this.** These are not extent
   questions. The 18 adjacent cases are passages Jeff listed and we never proposed.

## What this does not establish

- **Correlational still.** Nothing here re-runs the detector; the cluster mechanism is
  read off 18 cases and a per-daf count, not demonstrated by a fix that recovers them.
  The recovery is the test, and it is the work item.
- **The Stage 1 result is on the shipped artifacts**, which carry the *previous* keep-rule.
  Whether the live `>=1 NARRATIVE_EVENT` rule already rescues some of those 9 is
  unmeasured, and is exactly what `board-reads-stale-triage` exists to settle. Do not
  quote 12.9% as the live figure.
- **`context_narrative_fraction` is our own instrument.** A daf reading `legal-only`
  is one Stage 1 labelled that way; if Stage 1 mislabels narrative as deliberation, this
  measure and the skip decision fail *together* and the correlation is partly tautological.
  The honest form of the claim is: **the labels Stage 1 acts on already separate the dapim
  it loses stories on**, which is a statement about the threshold, not about the labeller.
