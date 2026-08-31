# STATUS — where the project is today

**Last rewritten: 2026-08-30 (evening).** Rewritten every session, never appended.
Read this first. Companion: [`FRAMEWORK.md`](FRAMEWORK.md) — how we measure and what
counts as good enough. Language and capability names come from there.

---

## The headline

**Jeff sent expert lists for four more tractates** (`jeff comms/8-30-2026/`), with:
*"I will get to all this soon. But here is the kiddushin list I have."* — so **the
boundary question is still unanswered** and capability 4 stays blocked.

Rough parse: **Gittin 112, Yevamot 102, Eruvin 73** — indicated, not measured.
**Kiddushin is now parsed properly: 95 stories, measured** (`NEXT/05` done). The rough
figure was 105, of which 9 were Jeff's own English review comments and 4 were
parallels-column citations. 81b no longer appears to hold 11 stories; it holds 4.
→ [`docs/findings/2026-08-30-kiddushin-list-parse.md`](docs/findings/2026-08-30-kiddushin-list-parse.md)

Why it matters: a **blind** dataset is one the detector had no hand in creating, so it
can measure *recall* — what we never found. We had exactly one (Ketubot, 149 stories).
Kiddushin now has one too, so three scoreboard cells that read "unmeasured" for the life
of the project are unblocked — **06, 07 and 08 are ready to run.**

**The list is already contaminated, and we nearly missed it.**
`Kiddushin missed stories.docx` is the appendix Jeff describes as *"additional stories
that you and Claude found that were not on my list"* — cases from across our runs, which
he annotated and **merged into his list**. None of the five is blind: each is there
because we put the page in front of him. Plus the one he marked `הוספתי--י.ר.` himself.

But **blind and "counts for recall" are different questions.** Circularity only matters
in the direction that *flatters*. Four of the five (33a, 45a, 53a, 71a) are in his list
because **we proposed them**, so counting them could only raise recall — excluded. The
fifth (**81b**) we **never proposed**; he found it in page text our review UI displayed,
so it can only count *against* us, and dropping it is what inflates the number.

**Recall denominator: 90** — 89 strictly blind, plus 81b. →
[`docs/findings/2026-08-30-appendix-provenance-correction.md`](docs/findings/2026-08-30-appendix-provenance-correction.md)

We caught this only because the appendix survived as a separate file.

**Gittin, Yevamot and Eruvin cannot have this problem — and that makes them the best
ground truth we have.** We have never run the detector on those tractates, so there is
nothing of ours for Jeff to have merged. Their lists are pristine. They are also the only
place we can run a *floor* test: whatever is on his list we should at minimum find, with
no prior output to have primed either side. The contamination risk there is entirely in
the future, and it starts the moment we send him results.

## Scoreboard — capabilities per [`FRAMEWORK.md`](FRAMEWORK.md) §1

| capability | metric | Ketubot | Kiddushin | gate |
|---|---|---|---|---|
| **[1 Triage](docs/capabilities/1_triage.md)** | stories surviving | **98.0%** at 44% of pages | unmeasured → **ready, `NEXT/06`** | ≥98% *(provisional)* |
| **[2 Detection](docs/capabilities/2_detection.md)** | recall, BLIND | **96.0%** loose / **87.9%** strict | **93.3%** loose / **83.3%** strict — **NEW** | ≥95% *(provisional)* |
| | *golden recall, CIRCULAR* | *92.1% (90.9% before the Mishnah-tagger fix)* | *95.3%* | — |
| **[3 Classification](docs/capabilities/3_classification.md)** | precision, CIRCULAR, harness | **89.2%** ✓ | **85.3%** ✓ | ≥85% *(provisional)* |
| **[4 Boundaries](docs/capabilities/4_boundaries.md)** | hit / near, BLIND | **80% / 84%** (ceiling ~87%) | 60%/73% ±7pt, circular | ≥75% *(provisional)* |
| **[5 Review](docs/capabilities/5_review.md)** | days per tractate | not started | not started | days, not weeks *(derived)* |
| **[6 Publication](docs/capabilities/6_publication.md)** | — | not started | not started | — |

**Four of five gates are provisional** — see FRAMEWORK §2b. They compose
(`triage × detection = end-to-end`), so only the end-to-end number needs defending, and
that is a product decision, not a technical one. Two questions are open there: one for
Simon, one for Jeff.

**Every measurable capability is now at or above its provisional gate.** Classification
measured 2026-08-30 on the current detector with the immutable harness: Ketubot 89.2%,
Kiddushin 85.3% — correcting an earlier claim in this file that we had no current number.

**But the 86 / 68 Classification numbers were never Classification numbers.** They counted
every rejection, whatever Jeff objected to. Sorting the notes: most rejections are
**boundary, merge or confidence-level** complaints — three other capabilities pooled into
one figure. Separated, both tractates land near 92-95% and the gap between them mostly
disappears. Review-round precision is therefore quoted as a **range**, because unreadable
notes set its width. → [`docs/findings/2026-08-30-detection-classification-ruler.md`](docs/findings/2026-08-30-detection-classification-ruler.md)

**We have a harness point estimate, not a review-round one.** The 89.2% / 85.3% above come
from `evaluate_golden.py` against the golden. What the *review rounds* still cannot give is
a point estimate, because the reviewer never recorded *which thing* he was rejecting. That
fix is a review-UI change, `NEXT/04`, not more inference over free text.

**Detection is softer than 96% under a strict test.** The published test credits a
proposal anywhere in a 14-segment search window. Requiring it to overlap a segment the
story actually occupies gives 87.9% Ketubot / 83.3% Kiddushin. The 12 Ketubot stories in
the gap are **cross-page stories whose text sits on a continuation daf where we proposed
nothing** — 17b, 50a and 51a each carry zero proposals.

## What changed today

- **Measurement became honest.** The boundary test set was built entirely from Jeff's
  corrections, so it could never reveal a boundary we had right and broke. Rebuilt from
  his blind 2005 list: **35 gradeable targets → 249**, run-to-run noise **7 points → 0**.
  → [`docs/findings/2026-08-30-boundary-ruler-rebuild.md`](docs/findings/2026-08-30-boundary-ruler-rebuild.md)
- **Boundary trimming is worth much less than claimed.** The old ruler said it doubled
  us on Ketubot 61-112 (33%→67%). The blind ruler says untrimmed was already 79% right.
  → [`docs/findings/2026-08-30-trim-asymmetry.md`](docs/findings/2026-08-30-trim-asymmetry.md)
- **Triage is a trade, not a defect.** 98% recall while examining 44% of pages. Worth
  pricing, not reflexively fixing.
- **The six recall misses do NOT split into two populations — all six are absent from
  the golden.** The claimed exception (Ketubot 77a) was a locator artifact: Jeff's blind
  entry there is segs **13-14** (Gemara, 94% text alignment) while the golden's 77a story
  is seg **8** (a Mishnah ma'aseh, 1% alignment). Two different stories on one daf, joined
  only by the recall locator's coarse 7-segment window.
  → [`docs/findings/2026-08-30-recall-miss-diagnosis.md`](docs/findings/2026-08-30-recall-miss-diagnosis.md)
- **Ketubot 77a is a Classification miss, not a Detection one** (measured, 8 identical
  re-runs, `NEXT/02`). Segs 13-14 are **proposed in 7 of 8 runs** and rejected as
  `NOT_A_STORY` in 6 of those 7, always citing the same three of the prompt's own
  disqualifiers. The empty production `stories` list is the ~1/8 tail. Seed case written
  into [`docs/history/2026-08-29-PLAN-wave6-story-criteria.md`](docs/history/2026-08-29-PLAN-wave6-story-criteria.md).
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
  why it survived four waves. → Lesson 27,
  [`docs/findings/2026-08-30-mishnah-tagger-chapter-boundary.md`](docs/findings/2026-08-30-mishnah-tagger-chapter-boundary.md)
  The remaining 2 (Ketubot 14b seg 11, 77a seg 8) are genuine Mishnaic *ma'asim* — a
  question for Jeff, not a bug. Now queued below.
- **A runner bug was fixed and guarded:** a failed API call could be recorded as a
  considered judgment. → Lesson 21, `tests/test_wave5b_runner_outcomes.py`
- **Wave 5b shelved.** Its trigger was measured on the biased ruler. Salvage list in
  `work/2026-08-30-second-story-guard.md`.
- **One ruler now measures Detection and Classification for both tractates.**
  `scripts/build_ruler.py` joins the blind lists, the detector proposals and all six
  review rounds — including the 16 Kiddushin verdicts that had never been folded in. It
  reproduces the published 96.0% and 86% as its regression check, then shows what those
  numbers were hiding. → `results/rulers/`
- **Kiddushin has a blind list.** 95 stories, parsed from the .doc's own table structure
  rather than a converter's line dump; the parser reproduces Ketubot's established 149
  as its regression check, and all 95 texts match an independent renderer character for
  character. Jeff's 9 review comments came back with their **exact anchor positions**, so
  each attaches to the passage he was looking at — which is what makes them usable to
  `NEXT/08`. → Lesson 28

## Waiting on Jeff — email sent 2026-08-30

**The question:** when a ruling is what makes a passage a story at all, is that ruling
part of the story we display, or the discussion that follows it? His 2005 lists keep it;
his review notes say cut it. Blocks the end rule for capability 4.
→ draft: [`comms/sent/2026-08-30-email-jeff.md`](comms/sent/2026-08-30-email-jeff.md)

**To add when we next write — four items:**

1. At what error rate does reviewing our output become worse than working from scratch?
   That number sets the Classification gate and only he can answer it.
2. **Do stories inside the Mishnah count?** We currently delete them. Two genuine Ketubot
   cases: 14b seg 11 and 77a seg 8 (the Sidon tanner). His blind 2005 list contains no
   Mishnah-only story; his review rounds accepted both into our golden — his own two
   sources disagree, exactly as on the boundary question.
3. **When we send results for a new tractate, ask him to keep his appendix separate.**
   In Kiddushin the appendix entries were merged into the list and cost us five of its
   stories as blind ground truth. Not urgent — Gittin, Yevamot and Eruvin are clean until
   we run there — but it must be said *before* the first review round, not after.
   → `work/2026-08-30-kiddushin-parse-open-calls.md` item 1b
4. A correction we owe him: the email said Ketubot 77a is a story "our own set has" — it
   is not. Our golden holds a *different* 77a story (the Sidon tanner, seg 8); his is at
   segs 13-14. The substance stands (we do miss his), the claim did not. Pairs naturally
   with item 2 — same daf.

**Before any next review round:** `validation/generators/generate_wave4_review_ui.py`
still reads `results/v10/wave4/` — the **reverted** char-offset span data — deliberately,
so the regenerated page stayed comparable to what Jeff actually saw during brief 04's
verification. Point it at `results/v10/wave4_notrim/` before showing him anything new.

## Next — items in [`work/`](work/), each self-contained

**Lead with Kiddushin only.** It is the sole new tractate where we already have a mature
detector output (95 stories, a golden set, 8 review rounds), so its list pays off
immediately with zero API calls. Gittin, Yevamot and Eruvin have **no detector output at
all** — their lists are worth nothing until the detector runs there, which is a larger
job that should wait until Kiddushin shows what we get.

```
                          ┌── kiddushin-recall            (triage + detection)
kiddushin-list-parse DONE ┼── kiddushin-boundary-set      all three unblocked,
                          └── kiddushin-comments-harvest  and independent of each other

start any time:   review-verdict-axes · kiddushin-12a-dedup · opener-lexicon
lower value:      triage-recall-price · second-story-guard
open calls:       kiddushin-parse-open-calls   (denominator 90; item 1b is for Jeff)
incomplete:       golden-completeness
```

All items are `work/2026-08-30-<slug>.md`. Finished ones are in
[`work/done/`](work/done/) with an `## Outcome` — **never deleted**, which is how
"what has already been done" stays answerable.

| item | capability | needs | Jeff? |
|---|---|---|---|
| **[kiddushin-recall](work/2026-08-30-kiddushin-recall.md)** — report over both denominators (90 / 94) | 1, 2 | — | no |
| **[kiddushin-boundary-set](work/2026-08-30-kiddushin-boundary-set.md)** — ~190 targets, kills the ±7pt noise | 4 | — | no |
| **[kiddushin-comments-harvest](work/2026-08-30-kiddushin-comments-harvest.md)** — Jeff's 10 anchored remarks | 3, 4 | — | no |
| **[review-verdict-axes](work/2026-08-30-review-verdict-axes.md)** — make the reviewer say *which* thing is wrong; the only route to a Classification point estimate. Planned as step 7a | 3, 5 | — | no |
| [triage-recall-price](work/2026-08-30-triage-recall-price.md) — price the trade over the 124 discarded pages | 1 | — | no |
| [second-story-guard](work/2026-08-30-second-story-guard.md) — stop discarding a second story sharing a segment | 4 | — | *awaiting* |
| [kiddushin-parse-open-calls](work/2026-08-30-kiddushin-parse-open-calls.md) | ground truth | — | **1b** |
| **[golden-completeness](work/2026-08-30-golden-completeness.md)** — fold in every verdict (the ruler names all 12) | 3, ground truth | — | no |
| [kiddushin-12a-dedup](work/2026-08-30-kiddushin-12a-dedup.md) — one detection covering two stories | 2 | — | no |
| [story-criteria](work/2026-08-30-story-criteria.md) — was Wave 6; 6a runs now, 6c blocked by design | 3 | comments-harvest | **6b** |
| [opener-lexicon](work/2026-08-30-opener-lexicon.md) — was Wave 7; mine openers, never invent them | 1, 2 | — | no |

**Done today** — `capability-histories` · `ketubot-77a` · `fetch-new-tractates` ·
`ketubot-golden-additions` · `kiddushin-list-parse` · `review-ui-display-asymmetry`.

\* `second-story-guard` is **not blocked**: deleting a whole second story is wrong
whatever Jeff answers about where an entry ends. Its *value* depends on his answer; the
work does not. That is `awaiting`, not `blocked_by`.

## Where things live — one job each

| file | its one job |
|---|---|
| **`STATUS.md`** | where we are. Rewritten each session. **Start here.** |
| **`FRAMEWORK.md`** | the six capabilities, how each is measured, what the gates are and why. |
| `work/*.md` | one self-contained item per ready task. When done: add `## Outcome` and `git mv` to `work/done/` — **never delete**. |
| `lessons/` | one file per lesson, L-001..L-030. Numbers are permanent. |
| `docs/golden/**` | dated findings. Immutable once written. |
| [`docs/capabilities/`](docs/capabilities) | per-capability history: what we tried, what we reverted and why, current best, distance to gate, ceiling, untried. One file per capability, linked from the scoreboard above. |
| `validation/feedback/jeff_*_ledger.md` | everything Jeff has said, and its disposition. |
| `CLAUDE.md` | how to work in this repo. Not status. |
| `FOR_SIMON.md` | the plain-English narrative. |

**The rule:** status here and nowhere else. Findings in a dated `docs/golden/` file.
Rules in `lessons/`. Ready work in `work/`. Never append status to a plan.

## Ground truth on hand

```
BLIND   (can measure recall)
  Ketubot    149 stories (2005 list) · 294 derived boundary targets
  Kiddushin   90 stories, MEASURED  -> results/expert_lists/kiddushin_2005.json
                 95 parsed, minus 1 he added himself, minus 4 appendix entries we
                 proposed ourselves (circular; counting them could only flatter).
                 The 5th appendix case (81b) we never proposed, so it STAYS -- it
                 can only count against us. Denominator 90; strictly blind 89.
                 ~180 boundary targets derivable from the 89 (NEXT/07)
  Gittin 112 · Yevamot 102 · Eruvin 73   <- PRISTINE. We have never run the detector on
                                            these, so nothing of ours can have been
                                            merged in. Each needs its own parse; a
                                            detector run there is a clean floor test.
CIRCULAR (precision and consistency only — never recall)
  Ketubot   golden: 187 entries, 164 accepted (23 NOT_A_STORY) — v7 + v9, many rounds
  Kiddushin golden:  96 entries,  85 accepted (11 NOT_A_STORY) — v7 only, ONE round
                     16 verdicts from the May-26 and Jul-06 rounds are NOT folded in
  70 boundary corrections across 8 review rounds
  10 Kiddushin review remarks, each anchored to its passage (NEXT/08)

SEFARIA TEXT on hand (text only — no detector has been run on these)
  Ketubot · Kiddushin                     results/v7/, results/v10/wave4_notrim/
  Gittin   2a-90b   178 dapim  2,990 seg  results/sefaria/gittin.json   <- NEW 08-30
  Yevamot  2a-122b  242 dapim  3,865 seg  results/sefaria/yevamot.json  <- NEW 08-30
  Eruvin   2a-105a  207 dapim  3,645 seg  results/sefaria/eruvin.json   <- NEW 08-30
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

**Quote golden counts the same way.** "Ketubot 182 · Kiddushin 85" compared entries
against accepted-only. Use 187/96 or 164/85, never one of each.
