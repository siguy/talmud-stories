# The rules — what counts as a story, and where it starts and ends

**One numbered rule per decision, each with the words the expert used, the date he said
them, and what it implies for data we already hold.** Read this before changing a prompt,
a boundary, or a dataset.

**Why this file exists.** Every rule below was, until it was written down, a judgment
living in one person's head and re-derived differently each time it came up. Two of them
were re-litigated months apart with opposite outcomes. A rule that is not numbered cannot
be applied consistently to past work, and a rule with no provenance cannot be defended
when a number moves.

---

## Two artifacts, two jobs — and only one of them is frozen

**The golden set is the product. It is supposed to change.** The goal is a corpus of
stories under the criteria we hold *today*, better and more refined than any list that
existed in 2005 — and better than Jeff's own, because his lists were provisional and he
says so. Every rule settled below should be applied to it, and the machine improves
because the golden improves.

**The 2005 blind lists are the instrument, and an instrument you adjust to match the
result stops measuring.** They are the only artifact that can tell us we missed something,
because they were written before this project existed. Edit them toward our output and
recall becomes unfalsifiable.

| | the golden corpus | the 2005 blind lists · his raw verdicts |
|---|---|---|
| what it is | our best current answer | evidence of what an expert said, and when |
| when a rule is settled | **rebuild it under the rule**, versioned, provenance per entry | **annotate**, never move |
| when he corrects an entry | apply the correction | record it beside the original |
| what it answers | *what is in the corpus* | *what did we fail to find* |

So: `results/canonical/*_canonical.json` is rebuilt as the rules settle;
`results/expert_lists/*_2005.json` and `tests/expert_boundary_targets_2005*.json` keep
their values and gain annotations. **The golden getting better is the point of the
project; the ruler holding still is what lets us prove it.**

## The corollary: we never edit the evidence

Jeff's 2005 lists and his review verdicts are **evidence, not our working notes.** When a
rule he states later disagrees with something in them — and it does, because he called
those lists *"provisional"* and *"sloppy and preliminary"* himself — we mark the entry,
we never overwrite it.

| | what we do |
|---|---|
| He corrects an entry himself | Record the correction **with the date and the quote**. His new judgment supersedes his old one, and both stay visible. |
| A rule he states implies an old entry is wrong | **Annotate, never move.** The target keeps his 2005 value; the annotation says which rule applies and what that rule would make it. |
| We think an entry is wrong | It stays. Put it on the list for the next round and let him rule. |
| We want a number under the new rule | Score with `--standard`, which reads the annotation. Two standards, two numbers, both reproducible from one file. |

**Why not just fix the evidence.** The blind lists are the only thing in this project that
can tell us we are wrong. Editing them toward our own output turns the ruler into a mirror
— and the composite already taught us what that feels like: deleting expert validations
made the score go **up**. A dataset we are free to edit is not evidence any more. **This
says nothing about the golden**, which is ours to improve and which every settled rule
below should be applied to.

---

## Classification — is it a story?

### R-C1 · A Mishnah story belongs to the Mishnah; the Talmud's quotation of it is Talmudic
**Jeff, 2026-09-01:** *"10a is just the Mishnah itself, that the printers included in the
printing of the Talmud, but not technically part of the Talmud… the second instances
(Gittin 10b, 46a, 74b), where the Talmud quotes the story from the Mishnah, can be
included."* Eventually both, cross-referenced — *"Mishnah Gittin 1:5 with a parallel in
Bavli Gittin 10b."*

- **Status:** settled. Our pipeline already does it: Stage 4g withholds the Mishnah copy
  and keeps the Gemara's citation.
- **Implied by it:** `mishnah_stories[]` is a **catalogue, not a deletion**. Ketubot 14b
  and 77a are Mishnah stories and stop counting as Talmud false negatives.
- **Implemented:** `filter_mishnah_only_stories()`. **Read by:** the recall harness, the
  boundary scorer (`WITHHELD`), the axis review UI. **Blind to it:** `evaluate_golden.py`,
  which is immutable — use `report_mishnah_filter_delta.py`.

### R-C2 · Speech alone can be a story when there is conflict and change — and it is borderline
**Jeff, 2026-09-01:** *"Sometimes dialogue can be counted as stories… when there is
conflict and implied change. But these would always be borderline. Unfortunately there are
no real hard and fast rules, that is, unless we make one."*

- **Status:** open as a general policy, and his answer invites **us** to propose the rule.
- **Settled instances:** Gittin 57a (the fertility exchange) is **not** a story — *"The
  list was wrong. Great to have the AI correct it!"* Gittin 43a is **low confidence at
  most**. Gittin 25a is **high confidence**.
- **Implied by it:** `borderline` must be a first-class verdict, which the axis review UI
  emits and the pipeline does not yet.

### R-C3 · A habitual frame does not disqualify — what matters is whether an event follows
**Jeff, 2026-09-01, on Gittin 57a (Beitar):** *"clearly a story. After the custom you have
the one time event — One day the emperor's daughter…"*

- **Status:** in the prompt, **and it does not work yet.** Say both halves.
- **Rate, measured first** (Lesson 18): 18 `HABITUAL` segments on examined Gittin pages,
  16 covered by no proposal, and **3 of those 16 sit inside one of his stories — 19%**,
  against 14.3% for discarded pages generally. Worth changing something.
- **What was changed:** the disqualifier now says a custom is often the frame of a story
  and the story starts at the custom, with his case and date attached.
- **What it bought:** on the four pages carrying the known cases, **1 of 3** recovered
  (58a seg 4). On a full re-run of the tractate, **nothing**: strict recall 108/112 before
  and after, the same four misses, and 7 gained / 9 lost proposals that are mostly the
  same stories re-bounded — churn indistinguishable from the noise floor without a
  same-code repeat (Lesson 22).
- **The diagnosis that matters:** Beitar is not proposed *at all*, not even as
  `NOT_A_STORY`. Detection never sees a candidate there, so no amount of classification
  wording will reach it. The mechanism is unresolved.
- **Kept anyway**, because the rule is his and the wording is faithful to it; pinned by
  `tests/test_prompt_carries_the_rules.py` so it is not silently dropped while it is still
  ineffective. The shipped Gittin artifact remains the pre-change run.
  Item: [`work/2026-09-02-habitual-frame.md`](../work/done/2026-09-02-habitual-frame.md).

### R-C4 · A story may be embedded inside a dictum
**Jeff, 2026-09-01, on Gittin 38b:** the dialogue *"includes a story, in R. Yohanan's
statement, that there were two families who set their meals at the wrong times and were
uprooted. (two actions, causal connection)"*

- **Status:** in the prompt ("judge what the speech CONTAINS, not only what the passage
  is"), and **not working**: 38b is still missed on the full re-run. Same shape as R-C3 —
  the passage is never proposed, so the failure is in Detection's reach and not in the
  criteria. Pinned by `tests/test_prompt_carries_the_rules.py`.

---

## Boundaries — where does it start and end?

### R-B1 · The story starts at the formula that introduces it
**Jeff, 2026-09-01:** *"These opening formulae are not technically part of the stories. But
they are important, as, for example, `תניא` indicates the Talmud thinks the story is
Tannaitic… Likewise, `אמר רב יהודה אמר רב` attributes the story (perhaps mistakenly)…
which might be significant to a scholar. If not too much trouble, we should include them."*

- **Status:** **shipped 2026-09-02.** `extend_start_over_opening_formula()`, Stage 4l.
- **Measured:** against the 2005 targets *as written*, +10 / −11 — a wash, and every one
  of the 11 losses is a target whose start excludes a formula. Against the rule he stated:
  **Gittin 82 → 86%, Kiddushin 84 → 88%, Ketubot 61-112 77 → 82%.**
- **Applied to past data by annotation:** `scripts/annotate_boundary_rules.py` marks each
  start target `included` or `excluded`; `score_boundary_targets.py --standard jeff-2026`
  reads it. **30 targets across the three sets are affected and none was moved on disk.**
- **Guarded:** `tests/test_opening_formula.py` — one clause, backwards only, and a long
  clause is the story rather than its frame.

### R-B2 · The legal discussion that follows a story need not be quoted
**Jeff, 2026-07-06**, and settled by Simon as the standard we build for: we end at the
story. His 2005 lists often run on into the sugya, so **for ends, the 2005 list is an
upper bound, not a target** — ending earlier than he does is expected, ending later is
wrong under both standards (Lesson 24).

- **Status:** settled and in force. It is why Gittin's end differences (7 early, 2 late)
  are read as 2 defects rather than 9.

### R-B3 · Where a ruling is what makes the passage a story, is the ruling in?
- **Status:** **open** (`jeff:boundary-end-rule`). Blocks
  [`work/2026-08-30-second-story-guard.md`](../work/2026-08-30-second-story-guard.md).

---

## Triage

### R-T1 · One narrative event is enough to read the page
Not his rule but ours, measured: a page with ≥1 `NARRATIVE_EVENT` is examined. Shipped
2026-08-31 after the corroboration clause was found discarding pages at a ~75% story rate.
**Principled, not tuned** — "any evidence at all" — and the fitted alternative (`V>=4`) was
rejected *with a test pinning the rejection*.

---

## How to apply these to work already done

1. **Re-score, do not re-label.** `--standard jeff-2026` on the boundary sets; the delta
   is the rule's effect and both numbers stay quotable.
2. **Re-read old findings against the register before citing them.** The 2026-09-01
   boundary analysis rejected R-B1 on numbers that were correct and on a standard that
   has since been settled. It is not wrong — it is superseded, and it says so.
3. **When a rule lands, name what it retires.** R-C1 retired the Gittin "double count"
   defect and the `mishnah_pair` screen bucket. Nothing else was touched.
4. **A new rule needs a rate before it needs an implementation** (Lesson 18), and a
   deterministic implementation needs the expert's words behind it (Lesson 15) — R-B1 has
   them; the 2026-06-03 regex trimmer did not, and cost a wave.
