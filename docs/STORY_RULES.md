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

## Scope — whose stories?

### R-S1 · The collection is stories about rabbis and post-biblical figures
**Jeff, 2026-09-23, on Gittin 57b (Nebuzaradan) and 68a (Solomon and Ashmedai):** *"This
is a full blown story, but it is about biblical characters, not rabbis. So it is not in
the class of stories that we are looking at."* — *"not in our scope, which is rabbis and
post-biblical figures."*

- **Status:** settled for biblical episodes retold. **Not** a judgment that they are not
  stories — he marked confidence *right* on both, "that it is a story. But not our kind of
  story." So they get their own label, **`OUT_OF_SCOPE`**, never `NOT_A_STORY`.
- **It was always there.** Neither passage is on his 2005 Gittin list: the rule was
  applied in 2005 and simply never written down.
- **Rate, measured first** (Lesson 18): by the detector's summaries, **3 proposals of ~560**
  across Gittin, Kiddushin, Yevamot and Ketubot are biblical episodes (Gittin 57b:0-4,
  68a:7-12; Yevamot 77a:0, Doeg and the lineage of David — unjudged). No accepted entry
  in any golden is one. A small false-positive source, not a recall risk.
- **Applied:** Gittin 57b:0-4 and 68a:7-12 are in `gittin_canonical.json`'s
  `out_of_scope` list — neither entries nor unlabelled (`build_gittin_golden.py`). In the
  twin-pass question since 2026-09-25.
- **Edges, open** (`jeff:scope-edges`): Elijah appearing to a rabbi (Gittin 6b, Kiddushin
  40a); a biblical exemplum cited *inside* a rabbinic story (Kiddushin 32b, Abraham
  serving guests); post-biblical non-rabbis (Titus, King Yannai, Agrippa). All three are
  in the golden today and read as in scope under his wording; that is our reading, not his.

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

### R-C2 · Speech alone is BORDERLINE when there is conflict — and not a story when there is not
**Jeff, 2026-09-01:** *"Sometimes dialogue can be counted as stories… when there is
conflict and implied change. But these would always be borderline. Unfortunately there are
no real hard and fast rules, that is, unless we make one."*
**Jeff, 2026-09-23, confirming the rule we proposed on the three cases that turn on it:**
Ketubot 7a:1 — *"mostly speech acts… technically there is not enough actions. But there
is conflict and some implied change, so it is borderline."* Ketubot 112a:11 — *"mainly a
dialogue, so lacking the actions necessary for a story. But has conflict, so can be
borderline."* (Being mocked is conflict; it is not an event.)

- **Status:** **settled 2026-09-23.** Speech with no event beyond speaking: `BORDERLINE`
  if there is conflict, `NOT_A_STORY` if there is not. Quasi-speech-acts count as speech
  (*retracted, considered, responded, sent a question* — his list, 2026-09-02).
- **Applied to the Ketubot golden, 2026-09-25:** 7a:1 and 112a:11 by his verdict, and
  **10 more** where he had written *"borderline"* in his own words in an earlier round
  and our auto-applier rounded it to `LOW_CONFIDENCE`, because the golden had no such
  column. In those rounds he used the two as one category (*"low confidence/borderline"*).
  Each carries his quote (`scripts/apply_jeff_2026-09-23_verdicts.py`). The other
  `LOW_CONFIDENCE` entries were **not** touched: the word is his to use, not ours to infer.
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

### R-C5 · A bare report of what someone did is not a story — the act has to lead somewhere
**Jeff, 2026-09-23**, four passages, one shape:
- Yevamot 15a (R. Akiva's etrog): *"There is no real story here, just a report of what
  R. Akiva did."*
- Yevamot 106b (Mar Zutra's ḥalitza document): *"just a description of what Mar Zutra
  did… even if it were against him, the narrative ends there. There is no continuation."*
- Yevamot 17a: *"a description of rabbi's sitting in a certain arrangement. But then they
  just have a discussion."*
- Ketubot 15a:0: *"a legal discussion discussing facts of an incident and their
  consequences, but not enough of the incident is given."*

- **Status:** settled on those four. It is his 2026-09-01 test (*"two actions, causal
  connection"*) stated from the other side: one act, however it is introduced — even
  *מעשה ב…* — is a precedent, not a story. It is also the other half of R-C3: a custom
  with **no** one-time event after it (Mar Zutra *"would score"*) stays a custom.
- **Rate, indicated not measured:** 10 accepted Ketubot entries carry a single event in
  the detector's own `multiple_events` field (two of them now ruled: 15a:0 no, 112a:11
  borderline). Kiddushin and Gittin entries carry no such field, so they cannot be
  screened without a run. **Do not bulk-relabel on this count** (Lesson 18, Lesson 27).
- **Applied:** Ketubot 15a:0 → `NOT_A_STORY`. In the twin-pass question since 2026-09-25.

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
- **Indicated, 2026-09-23:** on Yevamot 106b he wrote *"then you have the gemara making a
  legal ruling, which is not part of the narrative at all."* That leans to *cut the
  ruling*. It does not settle R-B3: 106b is not a story, so it is not the case R-B3 asks
  about — a ruling that is what makes a passage a story.

### R-B4 · The Gemara's commentary on a story is not part of the story
**Jeff, 2026-09-23, on Kiddushin 39b 8-10:** *"it is actually part of the Gemara's
commentary on the story. In this commentary the gemara revises some of the story, or adds
some details. But these are of the Gemara's efforts to resolve certain issues. So I would
not include them in the story at all, although, at some level, they influence the
audience's understanding of the story."* And on Yevamot 15a: *"the gemara's comment about
the story. It does tell you about what R. Akiva was thinking, but it is not part of the
story."*

- **Status:** settled. Stronger than R-B2 in two ways: *excluded*, not "need not be
  quoted", and it covers commentary **inside or after** a story — including where the
  commentary revises the story or adds a detail to it.
- **Applied:** Kiddushin 39b golden 8-8 → **7-7** (segment 7 is the incident; his 2005
  entry `kiddushin_041` and his 2026-04-23 note both start there). In the twin-pass
  question since 2026-09-25 — Yevamot 15a:14, one of his three twin-pass rejections, is the
  Gemara's commentary on the story beside it (the other two are R-C5).

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
