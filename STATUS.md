# STATUS — where the project is today

**Last rewritten: 2026-08-31.** Rewritten every session, never appended.
Read this first. Companion: [`FRAMEWORK.md`](FRAMEWORK.md) — how we measure and what
counts as good enough. Language and capability names come from there.

---

## The headline

**The repository was reorganized around the six capabilities, and not one capability
number moved.** Say that first, because everything below is easy to mistake for progress.
Detection, Classification, Boundaries and Triage read exactly what they read on
2026-08-28. What changed is that the project can now be *navigated*: what was already
tried, what was reverted and why, and what a dead end costs.

**The strategic fork, stated plainly.** The detector is not the problem. It finds 96% of
the stories on a list Jeff wrote twenty years before it existed. The problem is that
reviewing a tractate costs 2–6 weeks of one scholar's calendar against ~$0.30 of compute
— four orders of magnitude apart — and his last two rounds returned **1 verdict and 15**.
Wave 6 would recover 1–2 stories. Review throughput is what stands between two tractates
and thirty-seven. That has been the measured answer since 2026-07-06 and no work has yet
been aimed at it.

**Nothing is blocked on us for the cheapest next steps.** `kiddushin-recall` and
`kiddushin-boundary-set` need no API calls and fill three cells that have read
"unmeasured" for the life of the project. Phase 6a costs about ten cents. All three are
written and ready in [`work/`](work/).

**Two clocks are running.** Gittin, Yevamot and Eruvin have pristine blind lists **only
until we send Jeff results for them** — and the ask that protects them
(`jeff:appendix-separate`) has to reach him *before* that round, not after. And he is
still sitting on the boundary question, which blocks capability 4 entirely.

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

## What changed today (2026-08-31)

All of it is infrastructure or correction. **No measurement moved.**

- **The reorganization landed** (PRs #1–#3). `docs/capabilities/` now carries a history
  per capability; `work/` replaced `tasks/NEXT/` with dated slugs and frontmatter;
  `lessons.md` became one file per lesson; `docs/golden/` is data only;
  `scripts/board.py` generates [`STATE.md`](STATE.md) and [`WORK.md`](WORK.md); and
  `tests/test_bookkeeping.py` makes a bookkeeping violation an ordinary test failure.
- **A failed triage call was silently discarding the page.** `triage_page()` returned
  all-DELIBERATION on a parse failure, which fails both keep-conditions — so a crashed
  call threw the page away, in the one stage whose errors leave no trace. Fixed with a
  distinguishable `TRIAGE_FAILED` value that **fails open**. Proven to change **0** of the
  shipped skip decisions. The *historical* failure rate is unknown and unrecoverable,
  because nothing counted it.
  → [`2026-08-31-triage-failure-default.md`](docs/findings/2026-08-31-triage-failure-default.md)
- **The public site was publishing a six-month-stale accuracy figure** — a v8-era
  *expert-agreement* number presented as accuracy. Corrected and dated, with the strict
  figure quoted beside the loose one. It will go stale again; nothing regenerates those
  pages.
- **Two hazards stopped being advice.** `docs/golden/v7/baseline_ketubot.json` is pinned
  in both the test suite and the pre-commit hook, so running `evaluate_golden.py` without
  `--output` now fails loudly instead of destroying an unreproducible baseline.
- **Three defects were found by *reading*, not by a failing test** — the triage default,
  the stale site numbers, and a `NEXT/04` listed as ready with no brief behind it. That is
  the argument for having written the capability histories.

## Waiting on Jeff — [`comms/JEFF.md`](comms/JEFF.md) owns this

**Do not keep a second copy here.** Open questions used to live in three places at once;
that file exists to end it. It carries all seven questions with the slug each work item
names in `awaiting:`, the corrections we owe, the full sent log, and the **ask order** —
which matters, because seven questions is two emails, not one.

Still unanswered and still blocking capability 4: `jeff:boundary-end-rule`, asked
2026-08-30, answered *"I will get to all this soon."*

**Before any next review round:** `validation/generators/generate_wave4_review_ui.py`
still reads `results/v10/wave4/` — the **reverted** char-offset span data — deliberately,
so the regenerated page stayed comparable to what Jeff actually saw. Point it at
`results/v10/wave4_notrim/` before showing him anything new.

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
| **[`STATE.md`](STATE.md)** | **generated instrument panel** — coverage matrix, gates, what is in flight. Never edit it; run `python3 scripts/board.py`. |
| **`STATUS.md`** | where we are, in words: judgment, hazards, what is *indicated* rather than measured. Rewritten each session. |
| **[`FRAMEWORK.md`](FRAMEWORK.md)** | the six capabilities, how each is measured, what the gates are and **why**. Carries no current values. |
| [`WORK.md`](WORK.md) | generated board — open items, in flight, done. |
| [`work/*.md`](work/) | one self-contained item per ready task. When done: add `## Outcome` and `git mv` to [`work/done/`](work/done/) — **never delete**. |
| [`lessons/`](lessons/) | one file per lesson, L-001…L-030. Numbers are permanent. |
| [`docs/findings/`](docs/findings/) | dated findings. Corrected by a **new** dated finding, never edited to look as though they were always right. |
| [`docs/history/`](docs/history/) | plans and approach docs, superseded by what they produced. |
| [`docs/capabilities/`](docs/capabilities/) | per-capability history: tried, reverted and why, current best, distance to gate, ceiling, untried. **Read before opening work on a capability.** |
| [`comms/JEFF.md`](comms/JEFF.md) | every open question (with the slug items name in `awaiting:`), corrections owed, and the sent log. |
| `validation/feedback/jeff_*_ledger.md` | everything Jeff has **said**, and its disposition. Different job from JEFF.md, and kept. |
| `docs/golden/` | **data only** since 2026-08-30, plus a redirect table for its old paths. |
| `CLAUDE.md` | how to work in this repo, and the route to read things in. Not status. |
| `FOR_SIMON.md` | the plain-English narrative. |

**The rule:** status here and nowhere else. Findings in a dated `docs/findings/` file.
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
