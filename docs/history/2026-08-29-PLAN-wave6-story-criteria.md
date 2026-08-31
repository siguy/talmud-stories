# Wave 6 Plan — Story-definition criteria (SPLIT: measure → ask Jeff → implement)

**Status:** Phase 6a executable now. **6c is BLOCKED on Jeff's answer — by design.**
**Restructured 2026-08-29** after an audit found that the original plan's core
justification was half wrong and that it would silently redefine ~40% of the golden.

---

## Why this wave is split

Jeff gave us a sharp story-definition rule on 2026-07-06
([criteria](../findings/2026-07-06-jeff-story-definition-criteria.md)). Encoding
it looks like a prompt change. It isn't — it is a **question about what the dataset
means**, and we cannot answer it for him. Two findings force the split.

### Finding 1 — Jeff's 2026-07-06 rule contradicts Jeff's 2026-03-17 rulings

Both are his. Neither is wrong. They cannot both be mechanically applied.

| 2026-03-17 (the 187-review corpus behind [error_taxonomy.md](../findings/2026-03-17-error-taxonomy.md)) | 2026-07-06 ([criteria](../findings/2026-07-06-jeff-story-definition-criteria.md)) |
|---|---|
| *"There is only one action followed by a legal ruling"* → **not a story** | *"A man stole another man's cow and sold it. Rava ruled…. In this case you may have a story."* |
| *"The actions mentioned in the reasoning, 'stating, objecting, asking questions' are all part of a dialogue, and not really events."* | *"speech-acts don't count… minimally there must be some action beyond the speech"* — implying speech **plus** action qualifies |
| *"Low confidence. It is mostly a legal case. The action 'explaining' is dialogue, not really an action."* → **LOW_CONFIDENCE, still a story** | the same passage type now reads as **not a story at all** |

LEGAL_FALSE_POSITIVE is the project's **largest error category (11 instances, 21%)**.
Relaxing the rule that suppresses it, to recover 1–2 false negatives, is a trade that
must be argued and measured — not assumed.

### Finding 2 — the blast radius is ~40% of the golden, not a short list

| | Total stories | LOW_CONFIDENCE |
|---|---|---|
| Ketubot golden | 182 | **77 (42%)** |
| Kiddushin golden | 96 | **33 (34%)** |

Per the taxonomy, *"mostly dialogue with minimal physical action → LOW_CONFIDENCE"*
is Jeff's **existing applied policy**: such passages are stories, just weak ones. His
new rule says speech-acts are not stories at all. The rule therefore points directly
at a bucket holding **110 of 278 golden stories**. That is a redefinition of the
dataset, and it is his call, not ours.

### Finding 3 — the original plan mis-attributed its own evidence

Wave 6 was justified on recovering Ketubot 20a and 77a as criteria failures. **20a's
page was never processed** — both 19b and 20a were skipped by triage, so Stage 2
never saw it. Of the 6 known recall misses:

| Miss | Responsible stage | Fix belongs to |
|---|---|---|
| 20a, 72b, 82b | **TRIAGE** — page never processed | triage recovery (no criteria change can help) |
| 67b | Stage 2 — opener `אמרו עליו` outside lexicon | [Wave 7](2026-08-28-PLAN-wave7-opener-lexicon.md) |
| 53a | Stage 2 — plausibly criteria | **this wave** |
| 77a | Stage 2 — **measured**: criteria, see seed case below | **this wave** |

Realistic criteria payoff: **1–2 stories**, not 3. That is Lesson 12 — audit the
evidence at the granularity the mechanism operates on.

---

## Seed case — Ketubot 77a (measured 2026-08-30, brief `tasks/NEXT/02`)

**The premise this case was filed under was wrong.** Brief 02 and
[`recall_miss_diagnosis_2026-08-30.md`](../findings/2026-08-30-recall-miss-diagnosis.md)
both state that Jeff's blind 2005 entry and our golden agree on a story at
Ketubot 77a "segments 8-14", and that Stage 2 proposed nothing. **All three claims are
false.** They are two different stories on one daf, conflated by the recall locator's
coarse 7-segment window.

| | golden's 77a story | Jeff's blind 2005 77a story |
|---|---|---|
| segments | **8** | **13-14** |
| passage | Sidon tanner ma'aseh (`מעשה בצידון בבורסי אחד שמת`) | Rav / R. Elazar / Shmuel, "feed Elazar barley" (`אכסוה שערי לאלעזר`) |
| Talmudic layer | **Mishnah** | **Gemara** |
| n-gram coverage of Jeff's text | 0.010 | **0.943** |
| in our golden? | yes (LOW_CONFIDENCE) | **no** |

So the recall row's `in_golden: true` is a locator artifact. The "1 miss present in the
golden vs 5 absent" split in the recall diagnosis is wrong: **all 6 misses are absent
from the golden.**

### What actually happens to each

Measured over **8 re-runs of identical code** (`src/story_detector_v11.py`,
`gemini-3-flash-preview`, cached triage; Lesson 22):

- **Seg 8 (golden's story) — proposed 8/8 runs**, `HIGH_CONFIDENCE`, all 6 criteria met,
  exact segment match to the golden. It is then **deleted from `stories` by
  `filter_mishnah_only_stories()`** (Wave 1 Issue #7) and moved to `mishnah_stories`.
  Neither `scripts/measure_recall_vs_expert_list.py` (line 97) nor
  `scripts/evaluate_golden.py` (lines 48, 74) ever reads `mishnah_stories`, so the
  story is invisible to both. **Not a Detection failure — a post-processing deletion.**
- **Segs 13-14 (Jeff's story) — proposed 7/8 runs**, and classified **`NOT_A_STORY` in 6
  of those 7** (1 run: `LOW_CONFIDENCE`). The production run fell in the ~1/8 tail where
  no candidate box was emitted at all, which is why the page's `stories` list is empty.

### The criteria finding — this is the part Wave 6 owns

Every rejecting run cited the **same three of the prompt's own automatic disqualifiers**:

```
'Legal debate with setting'
'A passage whose entire activity is verbal exchange'
'Rabbi stating legal opinion'
```

The passage's surface form is: Rav states a ruling → R. Elazar **travels** and recites it
before Shmuel → Shmuel mocks him ("feed Elazar barley") → R. Zeira **ascends** to Eretz
Yisrael, **finds** R. Binyamin bar Yefet sitting and reciting it → the mockery is recalled.
That form trips four of the prompt's disqualifiers and three clauses of its CRITICAL RULE
("a rabbi travels to another academy for a debate", "one sage sits before another",
"named rabbis make legal arguments to each other").

Under [Jeff's rubric](../findings/2026-07-06-jeff-story-definition-criteria.md) it
qualifies (INDICATED — our reading of his written criteria, not his verdict on this
passage): the events **actually happened**; there is **action beyond the speech**
(`אזל`, `סליק`, `אשכחיה` — went, ascended, found him), which is his stated minimum; and the
**mockery/humiliation** is the emotional reaction he says counts as an event.

**The shape to encode:** *sage travels, recites a teaching, is mocked, and the mockery
outlives the journey.* The prompt's two EMBEDDED STORIES patterns cover baraita-framing
and objection-framing only. Nothing covers travel-plus-reputational-consequence, and the
disqualifier list actively suppresses it.

### Two adjacent defects found while measuring this (Lesson 18), NOT owned by Wave 6

**Status 2026-08-30: defect 2 is fixed; defect 1 is narrowed from 4 stories to 2 and is now
a queued question for Jeff.** The original counts below were wrong in a way worth naming.

1. **The Mishnah filter contradicts the golden — 2 stories, not 4.**
   `filter_mishnah_only_stories()` moves stories into `mishnah_stories`, which **no harness
   reads**. On Ketubot it removed 4 stories the golden accepts — **4 of the 15 golden false
   negatives, 27%**. (This section previously said "31% of the 13"; 13 is the *post-fix*
   count, 15 was the real one. Same error was corrected in `STATUS.md`.)

   Two of those 4 were defect 2 below and are now back. The remaining two — Ketubot
   **14b seg 11** (`מעשה בתינוקת שירדה למלאות מים מן העין`) and **77a seg 8** (the Sidon
   tanner) — are genuine Mishnaic *ma'asim*, as is Kiddushin **50b seg 10**
   (`ומעשה בחמש נשים ובהן שתי אחיות`). A recurring category, not two oddities.

   His blind 2005 list contains no Mishnah-only story, but his review rounds accepted these
   into our golden — **his own two sources disagree**, the same shape as the boundary
   question, so this is his call and not ours. **Queued for the next email** →
   [`../comms/sent/2026-08-30-email-jeff.md`](../../comms/sent/2026-08-30-email-jeff.md)
   § "Not yet asked". Still decide the premise before Wave 6 measures against the golden.

2. **`_tag_mishnah_segments()` mislabelled Gemara as Mishnah at chapter boundaries —
   FIXED 2026-08-30.** At a new chapter Sefaria marks the opening Mishnah with the chapter
   incipit in `<big><strong>` (e.g. `אף על פי` on Ketubot 54b seg 5) instead of `מתני׳`. The
   tagger found `גמ׳` first, concluded the page began mid-Mishnah, and back-tagged every
   preceding segment — the previous chapter's Gemara tail and the `הדרן` formula included.
   7 pages were mis-tagged (Ketubot 54b, 65b, 70a, 95b, 101b; Kiddushin 41a, 58b), and two
   of the four deletions above were plain Gemara lost this way — 95b seg 0 is
   `דההוא גברא דמישכן ליה פרדיסא`, not Mishnah at all.

   Fixed in `src/story_detector_v11.py` by reading all four of Sefaria's structural markers
   (`מתני׳`, `גמ׳`, `הדרן`, chapter incipit) instead of two: 72 segments on 12 pages, every
   change a correction. Golden **TP 149 → 151, FN 15 → 13, composite 0.9115 → 0.9136**;
   precision and merge unchanged; **blind recall identical at 96.0%**, which is why nothing
   caught it. Guarded by `tests/test_mishnah_tagger_chapter_boundary.py`. → Lesson 27,
   [`../docs/findings/2026-08-30-mishnah-tagger-chapter-boundary.md`](../findings/2026-08-30-mishnah-tagger-chapter-boundary.md)

### Gate contribution

Add both passages to the conformance set as a **minimal pair on one daf**:
Ketubot 77a segs 13-14 must classify as a story (or `borderline` per 6b); Ketubot 77a
seg 8 must survive to a place a harness can see. Test-only, never few-shot (Lessons 2, 8).

---

## Phase 6a — Measure the blast radius (NO Jeff, ~$0.10)

Classify each of the 110 LOW_CONFIDENCE golden stories on one axis only:
**does anything non-speech happen?** (physical action, movement, state change, or an
emotional/internal reaction — which Jeff says *does* count).

- Output: `results/criteria/speech_act_blast_radius.json` + a human-readable table.
- Deliverable to Jeff: *"N stories currently in your golden would be demoted by your
  new rule. Here are examples."*
- This is a **measurement**, not a relabeling. Nothing in the golden changes.
- Use abstract criteria in the prompt, never the specific passages (Lesson 8).

## Phase 6b — Ask Jeff (the ONLY thing here needing his input)

Present the contradiction **in his own words**, side by side, with the count from 6a
and 3–4 concrete examples. Then one question:

> Passages where rabbis only speak — no action, no emotional reaction — are currently
> **LOW_CONFIDENCE stories** in the database, per your 2026-03-17 reviews. Your newer
> rule reads as **not stories at all**. There are N of them. Should they become
> NOT_A_STORY, stay LOW_CONFIDENCE, or get a new **borderline** status that the
> database surfaces rather than decides?

Frame it as a decision his data forces, not as an inconsistency to defend. His own
crowd-sourcing answer (keep contested cases, flagged) suggests he may well pick
`borderline` — but he chooses.

## Phase 6c — Implement (BLOCKED until 6b is answered)

Fork v11 → v12. Then:

1. Promote **hypothetical vs. actual** to the primary test; demote "has physical
   action" to a secondary signal.
2. Replace the blanket anti-legal disqualifier with the mixed-case rule (real event +
   ruling = story), **and measure the FP regression on the legal bucket in the same
   run** — recovery and regression are one trade, reported together.
3. Apply Jeff's 6b answer to the speech-act policy; emit a `borderline` flag if he
   chooses that.
4. Count emotional/internal reactions as qualifying events.

**Rollback discipline (Lesson 5: a prompt rewrite once cost 0.93 → 0.57):**
git checkpoint before the first prompt edit; **hard abort if either composite drops
> 0.02** below the same-day baseline; revert rather than iterate blindly.

**Approach note (Lesson 7):** a post-hoc classifier is the safer instrument for
false positives and *can never create new false negatives* — but it also **cannot
recover false negatives**, which is what this wave is for. So the two are separate
jobs and must not be bundled into one prompt. The FP classifier proceeds independently
and is not blocked on Jeff.

## Gates

| Gate | Threshold |
|---|---|
| Conformance set, **per axis** | beats v10 baseline on every axis (no averaging away a regression) |
| Legal-FP bucket | no net increase in NOT_A_STORY misclassification |
| Both composites, regenerated today | within 0.02, **both Ketubot ranges + Kiddushin** (Lessons 6, 11) |
| Recall vs Jeff's 2005 list | ≥ current; ideally recovers 53a/77a |
| Held-out | develop on Ketubot, gate on Kiddushin (Lesson 9) |

The conformance set is **TEST-ONLY and never few-shot material** (Lessons 2, 8).

Lesson 13/14 applies: if composite falls while conformance and expert-list recall
rise, that is a win and must be argued explicitly, not silently "fixed."

## Cost

6a ≈ $0.10. 6c ≈ $1–2 (re-detection per tractate at ~$0.30–0.60, plus gate re-runs).
