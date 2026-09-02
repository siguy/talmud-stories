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

## The standing principle: we never edit his data

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

**Why not just fix the data.** The blind lists are the only thing in this project that can
tell us we are wrong. Editing them toward our own output turns the ruler into a mirror —
and the composite already taught us what that feels like: deleting expert validations made
the score go **up**. A dataset we are free to edit is not evidence any more.

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

- **Status:** stated, **not yet implemented.** Stage 1 labels the segment `HABITUAL` and
  Stage 2 stops at the frame; this is a live miss.
- **Before implementing:** measure the corpus-wide rate (Lesson 18).
  Item: [`work/2026-09-02-habitual-frame.md`](../work/2026-09-02-habitual-frame.md).

### R-C4 · A story may be embedded inside a dictum
**Jeff, 2026-09-01, on Gittin 38b:** the dialogue *"includes a story, in R. Yohanan's
statement, that there were two families who set their meals at the wrong times and were
uprooted. (two actions, causal connection)"*

- **Status:** stated, not implemented, no mechanism yet. The story is not the passage's
  outer shape.

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
