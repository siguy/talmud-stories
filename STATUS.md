# STATUS — where the project is today

**Last rewritten: 2026-08-30 (evening).** Rewritten every session, never appended.
Read this first. Companion: [`FRAMEWORK.md`](FRAMEWORK.md) — how we measure and what
counts as good enough. Language and capability names come from there.

---

## The headline

**Jeff sent expert lists for four more tractates** (`jeff comms/8-30-2026/`), with:
*"I will get to all this soon. But here is the kiddushin list I have."* — so **the
boundary question is still unanswered** and capability 4 stays blocked.

Rough parse: **Kiddushin ~96, Gittin 112, Yevamot 102, Eruvin 73.** Treat these as
indicated, not measured — the Kiddushin document is **dirtier than the Ketubot one**:
9 of its 105 parsed entries are Jeff's own English review comments, which inherit the
preceding daf reference (making Kiddushin 81b appear to hold 11 stories), and it
contains `הוספתי--י.ר.` — *"I added — J.R."* — very likely marking stories he took from
**our** output, which are therefore **not blind**. `NEXT/05` fixes this and everything
downstream depends on it.

Why it matters: a **blind** dataset is one the detector had no hand in creating, so it
can measure *recall* — what we never found. We had exactly one (Ketubot, 149 stories).
Kiddushin had none, which is why three cells in the scoreboard read "unmeasured." That
is now fixable, and three tractates we have never touched become testable.

## Scoreboard — capabilities per [`FRAMEWORK.md`](FRAMEWORK.md) §1

| capability | metric | Ketubot | Kiddushin | gate |
|---|---|---|---|---|
| **1 Triage** | stories surviving | **98.0%** at 44% of pages | unmeasured → **now possible** | ≥98% *(provisional)* |
| **2 Detection** | recall, BLIND | **96.0%** | unmeasured → **now possible** | ≥95% *(provisional)* |
| | *golden recall, CIRCULAR* | *92.1% (90.9% before the Mishnah-tagger fix)* | *95.3%* | — |
| **3 Classification** | precision, CIRCULAR | **89.2%** ✓ | **85.3%** ✓ | ≥85% *(provisional)* |
| **4 Boundaries** | hit / near, BLIND | **80% / 84%** (ceiling ~87%) | 60%/73% ±7pt, circular | ≥75% *(provisional)* |
| **5 Review** | days per tractate | not started | not started | days, not weeks *(derived)* |
| **6 Publication** | — | not started | not started | — |

**Four of five gates are provisional** — see FRAMEWORK §2b. They compose
(`triage × detection = end-to-end`), so only the end-to-end number needs defending, and
that is a product decision, not a technical one. Two questions are open there: one for
Simon, one for Jeff.

**Every measurable capability is now at or above its provisional gate.** Classification
measured 2026-08-30 on the current detector: Ketubot 89.2%, Kiddushin 85.3% — correcting
an earlier claim in this file that we had no current number. What is *not* measured is
Kiddushin's recall, and that is what `NEXT/05`-`07` unlock.

## What changed today

- **Measurement became honest.** The boundary test set was built entirely from Jeff's
  corrections, so it could never reveal a boundary we had right and broke. Rebuilt from
  his blind 2005 list: **35 gradeable targets → 249**, run-to-run noise **7 points → 0**.
  → [`docs/golden/v11/boundary_ruler_rebuild_2026-08-30.md`](docs/golden/v11/boundary_ruler_rebuild_2026-08-30.md)
- **Boundary trimming is worth much less than claimed.** The old ruler said it doubled
  us on Ketubot 61-112 (33%→67%). The blind ruler says untrimmed was already 79% right.
  → [`docs/golden/v11/trim_asymmetry_2026-08-30.md`](docs/golden/v11/trim_asymmetry_2026-08-30.md)
- **Triage is a trade, not a defect.** 98% recall while examining 44% of pages. Worth
  pricing, not reflexively fixing.
- **The six recall misses do NOT split into two populations — all six are absent from
  the golden.** The claimed exception (Ketubot 77a) was a locator artifact: Jeff's blind
  entry there is segs **13-14** (Gemara, 94% text alignment) while the golden's 77a story
  is seg **8** (a Mishnah ma'aseh, 1% alignment). Two different stories on one daf, joined
  only by the recall locator's coarse 7-segment window.
  → [`docs/golden/workflow/recall_miss_diagnosis_2026-08-30.md`](docs/golden/workflow/recall_miss_diagnosis_2026-08-30.md)
- **Ketubot 77a is a Classification miss, not a Detection one** (measured, 8 identical
  re-runs, `NEXT/02`). Segs 13-14 are **proposed in 7 of 8 runs** and rejected as
  `NOT_A_STORY` in 6 of those 7, always citing the same three of the prompt's own
  disqualifiers. The empty production `stories` list is the ~1/8 tail. Seed case written
  into [`tasks/PLAN_wave6.md`](tasks/PLAN_wave6.md).
- **A Mishnah filter was silently deleting expert-validated stories. Half of it was a
  bug; that half is now fixed and measured.** `filter_mishnah_only_stories()` moves
  stories to `mishnah_stories`, which **neither** `measure_recall_vs_expert_list.py`
  **nor** `evaluate_golden.py` reads. It removed 4 Ketubot stories the golden accepts —
  **4 of the 15 golden false negatives, 27%** (an earlier line here said "31% of 13";
  13 is the *post-fix* count, 15 was the real one). Two of the 4 were not Mishnah at all:
  `_tag_mishnah_segments()` read every chapter boundary as a mid-Mishnah page, because
  Sefaria opens a new chapter's first Mishnah with the chapter incipit instead of
  `מתני׳`. 72 segments on 12 pages; Gittin and Yevamot would have hit it on 20 more.
  **Golden TP 149 → 151, FN 15 → 13, recall 90.9% → 92.1%, composite 0.9115 → 0.9136**,
  precision and merge unchanged. **Blind recall identical at 96.0% before and after** —
  the harness nobody reads for recall was the only one that could see the loss, which is
  why it survived four waves. → Lesson 26,
  [`docs/golden/v11/mishnah_tagger_chapter_boundary_2026-08-30.md`](docs/golden/v11/mishnah_tagger_chapter_boundary_2026-08-30.md)
  The remaining 2 (Ketubot 14b seg 11, 77a seg 8) are genuine Mishnaic *ma'asim* — a
  question for Jeff, not a bug. Now queued below.
- **A runner bug was fixed and guarded:** a failed API call could be recorded as a
  considered judgment. → Lesson 21, `tests/test_wave5b_runner_outcomes.py`
- **Wave 5b shelved.** Its trigger was measured on the biased ruler. Salvage list in
  `tasks/NEXT/03`.

## Waiting on Jeff — email sent 2026-08-30

**The question:** when a ruling is what makes a passage a story at all, is that ruling
part of the story we display, or the discussion that follows it? His 2005 lists keep it;
his review notes say cut it. Blocks the end rule for capability 4.
→ draft: [`docs/golden/v11/email_jeff_2026-08-30.md`](docs/golden/v11/email_jeff_2026-08-30.md)

**To add when we next write — three items**, framed in the draft's "Not yet asked":

1. At what error rate does reviewing our output become worse than working from scratch?
   That number sets the Classification gate and only he can answer it.
2. **Do stories inside the Mishnah count?** We currently delete them. Two genuine Ketubot
   cases: 14b seg 11 and 77a seg 8 (the Sidon tanner). His blind 2005 list contains no
   Mishnah-only story; his review rounds accepted both into our golden — his own two
   sources disagree, exactly as on the boundary question.
3. A correction we owe him: the email said Ketubot 77a is a story "our own set has" — it
   is not. Our golden holds a *different* 77a story (the Sidon tanner, seg 8); his is at
   segs 13-14. The substance stands (we do miss his), the claim did not.

**Before any next review round:** `validation/generators/generate_wave4_review_ui.py`
still reads `results/v10/wave4/` — the **reverted** char-offset span data — deliberately,
so the regenerated page stayed comparable to what Jeff actually saw during brief 04's
verification. Point it at `results/v10/wave4_notrim/` before showing him anything new.

## Next — briefs in [`tasks/NEXT/`](tasks/NEXT/), each self-contained

**Lead with Kiddushin only.** It is the sole new tractate where we already have a mature
detector output (95 stories, a golden set, 8 review rounds), so its list pays off
immediately with zero API calls. Gittin, Yevamot and Eruvin have **no detector output at
all** — their lists are worth nothing until the detector runs there, which is a larger
job that should wait until Kiddushin shows what we get.

```
              ┌── 06 Kiddushin recall (triage + detection)
05 parse ─────┼── 07 Kiddushin blind boundary set
  (blocker)   └── 08 harvest the embedded review comments

fully independent, start any time:   00 · 01 · 02 · 04 · 09 · 10 · 11 · 03
```

| | task | capability | needs | Jeff? |
|---|---|---|---|---|
| **05** | Parse the Kiddushin list properly — 3 streams, blind flags | ground truth | — | no |
| **06** | Kiddushin recall: triage + detection | 1, 2 | 05 | no |
| **07** | Kiddushin blind boundary set (~190 targets, kills the ±7pt noise) | 4 | 05 | no |
| **08** | Harvest Jeff's embedded comments — criteria + boundary corrections | 3, 4 | 05 | no |
| 00 | Per-capability history: what we tried, reverted, current best | all | — | no |
| 02 | ~~Why is Ketubot 77a never proposed~~ **DONE** — it *is* proposed; classification rejects it | 3 | — | no |
| 04 | Fix the review UI Hebrew/English asymmetry | 5 | — | no |
| 01 | Price the triage trade over the 124 discarded pages | 1 | — | no |
| 03 | Stop discarding a second story sharing a segment | 4 | — | low priority* |
| 09 | Fetch Gittin / Yevamot / Eruvin from Sefaria | ground truth | — | no |
| 10 | Add the 5 missing stories to the Ketubot golden | 2 | — | no |
| 11 | Kiddushin 12a — one detection covering two stories | 2 | — | no |
| — | Wave 6 — encode Jeff's criteria (08 feeds it) | 3 | 08 | no |

\* 03 is not blocked: deleting a whole second story is wrong whatever Jeff answers about
where an entry ends. Its *value* depends on his answer; the work does not.

## Where things live — one job each

| file | its one job |
|---|---|
| **`STATUS.md`** | where we are. Rewritten each session. **Start here.** |
| **`FRAMEWORK.md`** | the six capabilities, how each is measured, what the gates are and why. |
| `tasks/NEXT/*.md` | one self-contained brief per ready task. Delete when done. |
| `tasks/lessons.md` | 24 durable rules. Append-only. |
| `docs/golden/**` | dated findings. Immutable once written. |
| `docs/capabilities/` | per-capability history — **not written yet, see `NEXT/00`**. |
| `validation/feedback/jeff_*_ledger.md` | everything Jeff has said, and its disposition. |
| `CLAUDE.md` | how to work in this repo. Not status. |
| `FOR_SIMON.md` | the plain-English narrative. |

**The rule:** status here and nowhere else. Findings in a dated `docs/golden/` file.
Rules in `lessons.md`. Ready work in `tasks/NEXT/`. Never append status to a plan.

## Ground truth on hand

```
BLIND   (can measure recall)
  Ketubot   149 stories (2005 list) · 294 derived boundary targets
  Kiddushin ~96 · Gittin 112 · Yevamot 102 · Eruvin 73   ← NEW,
                                        Kiddushin needs NEXT/05 first
CIRCULAR (precision and consistency only — never recall)
  Ketubot   182 golden stories · Kiddushin 85
  70 boundary corrections across 8 review rounds

SEFARIA TEXT on hand (text only — no detector has been run on these)
  Ketubot · Kiddushin                     results/v7/, results/v10/wave4_notrim/
  Gittin   2a-90b   178 dapim  2,990 seg  results/sefaria/gittin.json   ← NEW 08-30
  Yevamot  2a-122b  242 dapim  3,865 seg  results/sefaria/yevamot.json  ← NEW 08-30
  Eruvin   2a-105a  207 dapim  3,645 seg  results/sefaria/eruvin.json   ← NEW 08-30
```

**Every reference in Jeff's Gittin, Yevamot and Eruvin lists resolves to a fetched
page** — ranges derived from Sefaria's own index, not guessed, and verified by
`python3 scripts/fetch_tractate_pages.py --verify-only`. The three entry counts
above are now **measured** (112 / 102 / 73 reproduce exactly), and all three lists
are genuinely blind — 0 English review comments, 0 `הוספתי` markers, unlike Kiddushin's.

`scripts/build_boundary_testset_2005.py` **cannot yet** build blind boundary sets for
these three, contrary to `NEXT/09`'s closing note: its `load_units` globs only
`results/v10/wave4_notrim/`, so it returns **0 segments** for all three (verified).
It needs one change — also read `results/sefaria/*.json`. Left undone here because
`NEXT/07` owns that script.

**But their per-daf attribution has a defect, in the same family as Kiddushin's.**
`parse_expert_doc` only matches single-amud headers, so **21 stories** under two-amud
headers (`סה ע"ב-סו ע"א`) are silently credited to the *preceding* daf — Gittin 11,
Yevamot 7, Eruvin 3. Entry counts are unaffected; **daf-level recall on these three
would be wrong until it is fixed.** One Gittin header (`יד ע"ד`) uses amud *dalet*, a
Yerushalmi form with no Bavli equivalent. `--verify-only` lists all 21.
