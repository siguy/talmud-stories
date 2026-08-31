# Capability 5 — Review

**Definition:** get human scholars to confirm, reject and annotate entries fast enough
that the whole Talmud is reachable — see [`FRAMEWORK.md` §1.5](../../FRAMEWORK.md).
**Gate:** a scholar reviews a tractate in **days, not weeks** (DERIVED — the only gate in
this project with a real basis)
**Current:** **not started** as a measured capability. No throughput number, no
inter-rater number — one reviewer has ever reviewed anything.

*Written 2026-08-30 from the sources in `tasks/NEXT/00`. History, not status.*

---

## Waves are not capabilities

No wave belongs to Review. That is itself the finding: **eight review rounds have been run
and none of them was ever treated as an engineering object with a metric.** Everything
below was built as support for some other capability's wave, and the throughput cost was
noticed only when someone went looking for the bottleneck.

---

## What we tried

### The rounds that actually happened

Measured 2026-08-30 by reading the verdict files themselves.

| date | tractate | reviewed / shown | detector | file |
|---|---|---|---|---|
| 2026-01-08 | Ketubot | 25 / 243 | v4-era | `ketubot_review_Jeffrey_Rubenstein_2026-01-08.json` |
| ~2026-01-25 | Ketubot | 30 (15 true / 15 false) | v4.1 | recorded in `94f7844`, no verdict file in the repo |
| 2026-02-05 | Ketubot | 128 | v5.1 | `v5_1_feedback_anonymous_2026-02-05 (1).json` |
| 2026-02-20 | Ketubot | 109 / 113 | v5.1 | `v5_1_feedback_anonymous_2026-02-20.json` |
| 2026-02-26 | Ketubot | 49 / 49 | v8 delta | `v8_delta_feedback_anonymous_2026-02-26.json` |
| 2026-03-17 | Ketubot | **187 / 189** | canonical | `canonical_review_anonymous_2026-03-17.json` |
| 2026-04-23 | Kiddushin | **96 / 96** | v7 | `kiddushin_review_2026-04-23.json` |
| 2026-05-26 | Kiddushin | **1 / 95** | Wave 3 | `kiddushin_review_2026-05-26 (1).json` |
| 2026-06-03 | Ketubot | 4 corrections | Wave 3 | applied by `402ed0d` |
| 2026-07-06 | Kiddushin | **15 / 95** | Wave 4 | `jeff comms/wave4_kiddushin_review_2026-07-06.json` |

Two rows carry most of the information in this table. **2026-05-26: one verdict on
ninety-five stories.** **2026-07-06: fifteen.** After the two exhaustive rounds
(2026-03-17 and 2026-04-23), reviewing stopped being exhaustive and never resumed.

### The interfaces

| when | what | outcome | evidence |
|---|---|---|---|
| 2026-01-05 | First review interface — self-contained HTML, no server, statistics dashboard, search/type/confidence filters | shipped; the shape everything since has kept | `ff94499` |
| 2026-01-05 | Reviewer-name field with `localStorage`; **auto-save across browser sessions**; reviewer guide + email template | shipped. Small, and it is why verdicts survived at all | `9e9cef8`, `e1a017e`, `5019882` |
| 2026-01-05 | Side-by-side English/Hebrew with length-adjustment controls | shipped | `e10610b` |
| 2026-01-22 | **`batch_review.html` — keyboard shortcuts Y / N / S** | shipped. The only *throughput* mechanism this project has ever built, and it was never measured or reused | `68ce263` |
| 2026-01-25 | **The text-display bug.** Stories were flattened out of pages without copying the segments array, so `story.page_segments` was always undefined and **no text was ever displayed** — reviewers saw criteria and reasoning but not the passage | **three commits to fix** (`6cc7bc2`, `b56d492`, `391a285`). Root cause: one missing `page_segments: page.segments`. Written into `CLAUDE.md` as a standing rule: *validation UIs must display text; test in a browser before claiming done* | `b56d492`, `95740cd` |
| 2026-01-25 | Context window trimmed to 1 segment either side of the story | shipped | `81bb7de` |
| 2026-02-22 | **v8 delta review UI** — compare v7 vs v8 and show only what changed, in 3 tiers (8 cross-page merges, 10 new/status/removed, 31 absorbed/reclassified), **skipping 69 unchanged stories** | shipped. The project's one real attempt at spending expert attention only where it is needed; Jeff returned 49 verdicts | `8cce970` |
| 2026-03-02 | Canonical review UI expanded from 19 flagged items to **all 189 stories in 3 sections** (needs-review / auto-applied / all-other), with a classification filter | shipped; produced the 187-verdict round that the golden is built on | `3d17f92` |
| 2026-03-27 | Kiddushin review UI + email draft | shipped; produced the 96-verdict round | `14a5f3a` |
| 2026-05-25 | Wave 3 Kiddushin UI, published to GitHub Pages | shipped; **returned 1 verdict** | `c7fe851` |
| 2026-06-15 | Wave 4 UI with v9-vs-v10 comparison and strikethrough on trimmed framing | shipped; returned 15 verdicts, 11 of them negative | `c430cc5` |
| 2026-08-30 | **The review UI's Hebrew/English asymmetry fixed — structurally.** Every segment is now rendered once into a single row carrying both languages, so emitting one without the other is impossible rather than merely avoided; the proposed span is **highlighted inside the full text** rather than trimmed to | shipped and verified in a browser on the real 3.4 MB page, then audited across every card: 0 mismatched EN/HE cell counts, 0 truncations, 12/12 and 23/23 cross-page stories bilingual. Guarded by `tests/test_review_ui_symmetry.py`, which runs the page's **actual display JavaScript** under Node against a real fixture (75 ms, no API key) and was confirmed to **fail** when each original bug is reintroduced | `b394489`, Lesson 25 |

### The process machinery

| when | what | outcome | evidence |
|---|---|---|---|
| 2026-03-25 | **The error taxonomy** — 187 verdicts sorted into 6 systematic patterns with Jeff's own language, detection heuristics and Aramaic structural markers | shipped; still the best summary of what he objects to | `ac8e83c`, [`error_taxonomy.md`](../golden/workflow/error_taxonomy.md) |
| 2026-08-28 | **The feedback ledger** — one durable, status-tracked row per note, created the moment feedback arrives, checked before replying or shipping | shipped for the 2026-07-06 round. It is the mechanism that stops Lesson 1 recurring, and it worked: the round's open items are still tracked | [ledger](../../validation/feedback/jeff_2026-07-06_feedback_ledger.md), Lesson 17 |
| 2026-08-30 | **Every verdict on disk joined into one artifact**, matched by segment **overlap** rather than key equality (keys encode spans, and spans move between runs, so exact matching silently drops older rounds) | shipped. Folded in the 16 Kiddushin verdicts that had never been used | `4de7135`, `scripts/build_ruler.py` |

## What we reverted, and why

**Nothing has been reverted here either — but three things were *dropped*, which in a
review pipeline costs more.**

**1. Feedback split into "auto-apply" and "needs review", and the second pile was never
scheduled (Lesson 1).** Across three rounds we applied the classification changes
immediately and deferred the boundary and merge corrections. Jeff noticed: **10 of his 53
canonical-review corrections were things he had already told us to fix.** The rule that
came out of it — *if there is no mechanism to return to deferred work, it does not get
done* — is now a memory as well as a lesson, and it still recurs: the 2026-05-26 and
2026-07-06 Kiddushin verdicts sat unfolded for months and were only folded in on
2026-08-30 (`6d1f917`, `4de7135`).

**2. A display bug that manufactured expert feedback (Lesson 25).** The Wave 4 UI trimmed
the Hebrew at the detector's character offsets and showed the full English beside it, and
cross-page stories emitted an "English (continued)" block with **no Hebrew counterpart at
all** — 35 stories across the three outputs. Cost, measured: **2 of the 15 verdicts** in
the 2026-07-06 round were spent on our renderer rather than on the detector, and one of
them — Kiddushin 8b seg 14 — was filed in the ledger under **cross-page merge defects and
sat there for seven weeks.** The detector had merged it correctly the whole time
(`spans_pages: ['Kiddushin 8b','Kiddushin 9a']`, `continues_to_next_page: true`). Only
the UI dropped the Hebrew. One fewer real defect; seven weeks of misdirected work.

We already had the rule *"open validation UIs in a browser before calling them done."* It
was not followed. The cost was not the bug — it was a false entry on the defect list and
an expert's goodwill spent describing our own rendering to us.

**3. `verdict: incorrect` records *that* he disagreed and never *what with* (Lesson 30).**
The vocabulary was never designed. `adjust` literally means *"this is a story and the
boundary is wrong"*, and it was counted as a classification failure. Sorting the notes by
what he actually objected to:

```
Ketubot   2026-03-17 (n=173)  classification 9 · boundary 7 · confidence 4 · merge 1
Ketubot   2026-02-26 (n= 43)  boundary 7 · merge 4 · classification 2 · confidence 1 · unreadable 9
Kiddushin 2026-04-23 (n= 89)  confidence 10 · classification 7 · boundary 3 · unreadable 9
Kiddushin 2026-07-06 (n= 15)  boundary 5 · unreadable 6
```

Most rejections are not about storyhood. This is a **Review** defect with a
**Classification** symptom: months of treating Classification as the weakest capability,
and Kiddushin as far worse than Ketubot, were mostly an artifact of the verdict vocabulary.

## Current best — the exact configuration

- **Reviewer:** one — Jeff Rubenstein (NYU). There has never been a second.
- **Interface:** static self-contained HTML, generated per round by
  `validation/generators/*.py`, published to GitHub Pages, verdicts kept in
  `localStorage` and exported as JSON.
- **Verdict vocabularies, plural and inconsistent across rounds:** early rounds used
  `correct` / `incorrect` / `confirm_remove` / `reject_remove` on **base** data; the
  canonical round used `correct` / `incorrect` / `approve` / `adjust` on
  **already-corrected** data. A `correct` on corrected data is not a `correct` on base
  data, and treating them alike would have silently undone the corrections — which is why
  the canonical round is applied as a separate post-processing layer (Lesson 3).
- **Durable record:** `validation/feedback/jeff_<date>_feedback_ledger.md`, one row per
  note with status and where addressed.
- **Joined view:** `results/rulers/{tractate}_ruler.json` — every proposal with every
  verdict and what each rejection objected to.

## Distance to gate

**Not measurable yet — nothing has been instrumented.** What exists instead is the
arithmetic that produced the gate, and it is the clearest number in the project:

| resource | per tractate | whole Bavli (37 tractates, 2,711 dapim) |
|---|---|---|
| LLM compute | ~$0.30–0.60, ~30 min | **~$10–25, a weekend of runs** |
| Jeff's review | **2–6 weeks calendar** | **~3–5 years, serially** |

Ketubot took four review rounds over ~6 weeks
([§3.2](../golden/workflow/approach_review_and_scaling_2026-07-06.md)). **Compute is
four orders of magnitude away from being the constraint.** No detector improvement
changes this arithmetic; only changing the validation design does. That is why this is
the one derived gate — and why the endgame is a crowd-sourced database rather than a
static corpus.

**Two numbers that would make this a real capability, and neither has ever been taken:**
days per tractate, and inter-rater agreement. The second is not merely unmeasured — it is
**unmeasurable today**, because there has only ever been one rater.

**A gap worth naming, measured 2026-08-30.** `STATUS.md` lists **`NEXT/04` as a ready,
bolded task** — *"make the reviewer say which thing is wrong"* — and **the brief file does
not exist.** `tasks/NEXT/04_review_ui_asymmetry.md` was deleted in `b394489` when its
original job (the display bug) was completed, and `4de7135` then repointed the *name* at a
new job without writing a new brief. In a repo whose convention is one self-contained
brief per ready task, this one is a name with nothing behind it.

## Ceiling

**None technical. The ceiling is one person's calendar**, and it is the reason the
project's endgame changed shape.

Jeff's own answer, 2026-07-06, is the design constraint: not a fixed panel and not a
static published corpus, but a **Google-Doc-style shared interface** carrying all
tractates, where any scholar can flag *not a story* / *remove*, mark **borderline**, or
suggest additions, gradually, as they encounter stories — with him or a small editor group
checking before finalisation, and **contested cases kept and flagged rather than silently
resolved** ([ledger Part 2(d)](../../validation/feedback/jeff_2026-07-06_feedback_ledger.md)).

He also offered to recruit colleagues to seed some tractates and cross-check against his
old lists. **That offer has not been taken up.**

## Untried

- **Make the reviewer say which thing is wrong.** The single highest-value item here, and
  the only route to a Classification point estimate: separate verdict axes for *is it a
  story* / *is the extent right* / *is the confidence right* / *is the merge right*.
  Re-deriving intent from free text has a measured ceiling — **24 notes across the rounds
  are unreadable**, and that is exactly the width of the precision range (Lesson 30).
  Named as `NEXT/04`; **no brief exists** (see above).
- **Show `mishnah_stories` to the expert.** The review UI still does not display what the
  Mishnah filter withheld, so the one person who could settle the scope question has never
  been shown the passages it removes (`804a097`).
- **Measure a round.** Nobody has ever recorded how long a review took, or verdicts per
  hour. Zero cost; it just requires asking.
- **A second reviewer.** Until there are two, inter-rater agreement — half of this
  capability's stated metric — cannot exist. Jeff has offered to recruit; the ask has not
  been made.
- **Auto-accept plus sample.** The publishable product does not require every story
  hand-verdicted; it requires a corpus with **measured, stated error rates**, which is how
  large annotated corpora are actually built. The proposed routing — auto-accept where the
  detector, an FP classifier and an ensemble agree, with a 5–10% audited sample to
  *measure* the residual error; an expert queue for disagreements; auto-reject with a
  low-rate sample to bound the miss rate — is specified at
  [§5.2](../golden/workflow/approach_review_and_scaling_2026-07-06.md) and **nothing of it
  is built.** Two of its three inputs (the FP classifier, the ensemble) are also untried —
  see [Classification](3_classification.md).
- **Reuse the throughput UI.** `batch_review.html` with Y/N/S keyboard shortcuts was built
  in January 2026 and never used for a real round.
- **Ask Jeff to keep his appendix separate** on the next tractate — one sentence, costs
  him nothing, and it cannot be reconstructed afterwards. It is the difference between a
  blind list and an unverifiable one (Lesson 29, `NEXT/09` item 1b). Gittin, Yevamot and
  Eruvin are still clean; **the window closes the moment we send him results**.
- **Declined, by Jeff:** a fresh cold-read of 10 random dapim as a recall probe — he
  already had detector-blind lists and offered those instead
  ([ledger Part 2(a)](../../validation/feedback/jeff_2026-07-06_feedback_ledger.md)). Also
  declined: a fixed validation panel, in favour of open crowd-sourcing (Part 2(d)).
