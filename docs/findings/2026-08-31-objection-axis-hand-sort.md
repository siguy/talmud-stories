# Reading the notes the rules could not — 2026-08-31

**Phase A of [`work/2026-08-30-review-verdict-axes.md`](../../work/2026-08-30-review-verdict-axes.md).**
No API calls, no Jeff. The job: take every rejection note `scripts/build_ruler.py` filed
as `unclassified`, read it by hand, and sort it onto the capability it actually indicts.

**Result — measured.** The population is **34 notes, not 24**. **27 of the 34 were
readable by a person** (79%). The residue is **7**, and all 7 are notes that are
*empty* — every note containing any text at all could be sorted. The bottleneck was the
keyword rules, not the reviewer.

| | before | after |
|---|---|---|
| notes naming no axis | **34** | **7** |
| rounds with a residue | 5 of 7 | **1 of 7** |
| Ketubot 2026-02-05 precision | 0.667 – **1.000** | 0.667 – **0.806** |
| Kiddushin 2026-04-23 precision | 0.674 – **0.921** | 0.674 – **0.899** |

Artifacts: [`results/rulers/objection_axes.json`](../../results/rulers/objection_axes.json)
(the hand sort, one row per note) · `results/rulers/{ketubot,kiddushin}_ruler.json`
(regenerated) · [`scripts/build_ruler.py`](../../scripts/build_ruler.py) (reads the sort,
falls back to the keyword rules).

**Regression checks hold.** Ketubot Detection 143/149 = 96.0% (strict 87.9%); Kiddushin
84/90 = 93.3% (strict 83.3%); `precision_all_causes` unchanged in all seven rounds, as
are `judged` and `accepted`. Only the upper bound and the residue move, which is the only
thing this work was allowed to move.

---

## 1. The population was 24 in the brief and 34 on disk

The brief's table listed four rounds. The ruler scores **seven**. The two it omitted
carry ten more unreadable notes:

| round | judged | unreadable | in the brief's table? |
|---|---|---|---|
| Ketubot 2026-03-17 (canonical) | 173 | 0 | yes |
| Ketubot **2026-02-05** (v5.1) | 36 | **9** | **no** |
| Ketubot 2026-02-20 (v5.1) | 102 | 0 | no |
| Ketubot 2026-02-26 (v8 delta) | 43 | 9 | yes |
| Kiddushin 2026-04-23 | 89 | 9 | yes |
| Kiddushin **2026-05-26** | 1 | **1** | **no** |
| Kiddushin 2026-07-06 (wave 4) | 15 | 6 | yes |

`docs/capabilities/3_classification.md` repeats the same short count — *"the range's width
is the unreadable notes: 9 + 9 + 6"*. Both are corrected by this finding: the width was
9 + 9 + 6 **+ 9 + 1**.

## 2. What the 34 turned out to be

| axis | n | what it indicts |
|---|---|---|
| **classification** | 9 | capability 3 — is it a story |
| **confidence** | 6 | capability 3, calibration — he agrees it is a story, the level is wrong |
| **boundary** | 6 | capability 4 — the extent |
| **merge** | 3 | capability 2 — how many stories are here |
| **display** | 1 | *none of the four* — the objection is to our renderer |
| **not_an_objection** | 2 | *none of the four* — the note affirms and the verdict rejects |
| **unresolvable** | 7 | the note is empty |

**Only 9 of 34 dispute whether the passage is a story.** The other 18 readable notes
indict three other capabilities, our own UI, or nothing at all. That is the same shape
Lesson 30 already established for the *readable* notes, now measured on the unreadable
remainder too — and it is the whole argument for Phase B.

### Why the keyword rules missed them

Not one miss is a hard case. The notes are plain; the rules are narrow. All 27 readable
notes, grouped — the counts sum to 27, and every row of the hand sort names its own
reason in `why_the_rules_missed_it`:

- **The note affirms rather than objects — 12.** Every rule in `OBJECTION_RULES` searches
  for the reviewer complaining. Half of these notes disagree by *asserting the criteria
  are met*. `Kiddushin 32b_1-1`, on a span we called `LOW_CONFIDENCE`: *"Yes, this is a
  story."* `Ketubot 10b_6-6`, on one we called `NOT_A_STORY`: *"This too is a story."*
  Six Kiddushin confidence disputes, four Ketubot overturned rejections, and the two
  notes that object to nothing at all.
- **He used his vocabulary and the rules wanted theirs — 11.** `legal debate` is not
  `legal (discussion|tradition)`, though `legal_debate_setting` is the name of one of our
  own disqualifiers. *"crossed out"* and *"trimmed"* are the review UI's own words for a
  boundary; the boundary rule knows `truncat` and `too long`. *"one long story"* and
  *"should go with what preceded it"* are merges that never say merge. *"a biblical
  story"* is a disqualifier with no rule at all.
- **A correction quoted instead of described — 2.** `Kiddushin 12b_10-10` is *"Here is
  the story:"* followed by the Hebrew. There is no keyword to find because he answered
  rather than complained; the correct extent *is* the note.
- **A typo — 1.** `Ketubot 42b_8-8`: *"just parts of a legal dicussion."*
- **A category the taxonomy does not have — 1.** `Kiddushin 8b_14-14` objects to our
  renderer. See §6.

Plus the **7 empty** notes, which are the residue. See §5.

The rules were not badly written; they were written to be conservative, and they were.
The lesson is about what conservatism costs when it is never audited: **34 notes, banked
for up to seven months, every one of them either readable in a minute or empty.**

## 3. The label under review is not the label in the ruler

Reading these notes needs the classification the reviewer was **shown**, and the ruler
does not carry it. The ruler joins old verdicts to *today's* proposals, so its
`detector_classification` is the current label. On `Ketubot 10b_1-1` that reads `YES`
beside a note saying *"This is definitely a story"* — which looks like nonsense until you
recover that the span was labelled **`NOT_A_STORY`** when he saw it, in February.

Recovered for all 34 by indexing the run each round was generated from
(`results/v5/pages_*.json`, `results/v8/wave1/`, `results/v7/kiddushin_v7.json`,
`results/v9/wave3/`, `results/v10/wave4/`) on `(ref, start_segment, end_segment)`.
34 of 34 resolved. Each row of the hand sort records it as
`classification_under_review`, so no future reading has to redo this.

## 4. The defect this uncovered: `incorrect` has meant two opposite things

**Measured.** In the 2026-02-05 round, **95 of the 125 verdicts sit on spans we had
labelled `NOT_A_STORY`** — 87 of them `correct`, 8 `incorrect`. That round's UI did not
ask *"is this proposal a story?"* It asked *"is our judgment right?"*, and showed him the
rejections too. `Ketubot 2a_5-6` is labelled `NOT_A_STORY` in `results/v5/pages_2-39.json`
and his verdict is `correct`: *"Exactly. This is a legal discussion about hypothetical
cases."*

So in that round `incorrect` can mean either:

- **over-call** — we said story, he says not. A false positive. Counts against precision.
- **under-call** — we said `NOT_A_STORY`, he says story. A false **negative**. It is the
  invisible half of capability 3 that `3_classification.md` records as having *"no
  measurement at all"* — and counting it against precision inverts its meaning.

**Four of the 34 are under-calls** (`Ketubot 10b_1-1`, `10b_3-3`, `10b_6-6`, `56b_11-11`),
all in that round, all overturning a `NOT_A_STORY`. `build_ruler.py`'s
`REJECTED = {'incorrect', 'confirm_remove'}` maps both directions to one bucket.

**Not re-scored here, deliberately.** Whether an overturned rejection belongs in a
precision denominator is a definition question, and Phase A's mandate is to read notes,
not to redefine the metric. Each round now reports
`rejections_inverted_direction` alongside the count, so the number is visible instead of
buried. Two smaller shapes get the same treatment:
`rejections_that_dispute_nothing` (2 — see §5) and `rejections_on_our_renderer` (1).

## 5. The residue, stated rather than guessed

**7 notes, all empty, all in the Ketubot 2026-02-26 v8-delta round.** No amount of
re-reading recovers an axis from an empty string. What *is* recoverable is direction:
comparing `results/v7/` with `results/v8/wave1/` shows **all 7 sit on spans with no v7
entry** — they are stories v8 introduced, and rejected without a word. So they are
over-calls of unknown axis, and they are counted that way.

Two further notes are readable but object to nothing:

- `Ketubot 62a_4-4` — v8 raised it `HIGH_CONFIDENCE` → `YES`; his note is *"This is
  clearly a story. Keep as a 'Yes'."* He is agreeing with the change he is recorded as
  rejecting.
- `Kiddushin 73a_5-5` — already `HIGH_CONFIDENCE`; his note is *"Yes. This is a story,
  given the action (a public exposition) and the response (stoning)."*

Both are counted against precision today. Both are filed as `not_an_objection` rather
than resolved, because "he misclicked" and "the UI meant something we have not
reconstructed" are different explanations and we cannot tell them apart.

## 6. What this hands Phase B

The brief specifies four axes. The evidence says four is **one short, and each needs a
direction**:

1. **A fifth option is required: *the display is wrong*.** One of the 15 verdicts in the
   2026-07-06 round was spent on our renderer (`Kiddushin 8b_14-14`, *"the Hebrew is cut
   off"*). The brief's own risk section says two of that round's 15 were; this confirms
   one of them from the note text. Without a place to put it, a UI bug is scored as a
   detector error — which is exactly how one sat misfiled for seven weeks (Lesson 25).
2. **Direction is not optional.** *"You wrongly called this a story"* and *"you wrongly
   called this not a story"* are opposite errors that today land in one bucket. The
   under-call direction is the only measurement this project has ever had of capability
   3's invisible half; four cases exist and they are all in one round from February.
3. **`Borderline` is already load-bearing.** Six of the 34 are the reviewer disputing a
   `LOW_CONFIDENCE` label upward while agreeing it is a story. The brief's `Borderline`
   option and its confidence axis are what those six needed.
4. **A verdict that contradicts its note must be catchable at entry.** Two of 34 affirm
   and reject at once. A UI that asks *"is it a story?"* first would have made both
   impossible to record.

## 7. Method note, for reuse

Sorted by hand, not by an LLM, and the brief's reasoning holds up: at n=34 a person is
cheaper and every judgment is auditable against the note text, which the hand sort quotes
verbatim beside it. An LLM pass would add a second layer of inference on top of the one
being removed. **At n≈240 the answer would be different** — the cost of reading flips —
and the right design there is an LLM proposal with a human confirming the disputed
subset, not an unreviewed classifier.

The sort itself is **CIRCULAR** in the sense of FRAMEWORK §3: it is our reading of his
words. Each row carries `confidence: measured | unresolvable` and a `reading` field
saying what in the note settles the axis, so a disagreement can be argued at the row.

## 8. Corrections owed

- `docs/capabilities/3_classification.md` — *"9 + 9 + 6 across the rounds"* undercounts.
  The width was 34 notes across five rounds; it is now 7 in one.
- `work/2026-08-30-review-verdict-axes.md` — the *"24 `unclassified` notes"* in Phase A
  and the four-round table are a subset of what the ruler scores.
- `STATUS.md` — Kiddushin's Classification range narrows to **67.4 – 89.9%**. Ketubot's
  headline range (87.9 – 94.8%, the 2026-03-17 round) does **not** move; that round had
  no unreadable notes.

Both range endpoints stay **CIRCULAR** and **indicated**, not measured: the upper bound
still assumes every non-classification objection is correctly assigned, and 7 notes still
name no axis.
