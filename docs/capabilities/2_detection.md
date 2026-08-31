# Capability 2 — Detection

**Definition:** on a page we chose to examine, propose every span that might be a story —
see [`FRAMEWORK.md` §1.2](../../FRAMEWORK.md). It proposes; it does not judge.
**Gate:** ≥95% recall (PROVISIONAL)
**Current:** **Ketubot 96.0% loose / 87.9% strict** (143/149) on Jeff's 2005 list
(**BLIND**); **Kiddushin 93.3% loose / 83.3% strict** (84/90) on his Kiddushin list
(**BLIND**). Measured 2026-08-30, `results/rulers/`.
*Circular cross-check, not an accuracy claim:* golden recall 92.1% Ketubot / 95.3%
Kiddushin (**CIRCULAR**).

*Written 2026-08-30 from the sources in `work/done/2026-08-30-capability-histories.md`. History, not status.*

---

## Waves are not capabilities

Waves 1–3 each touched Detection **and** Classification in one session, and their
headline numbers pooled the two. This file takes only the Detection half; the
Classification half is in [`3_classification.md`](3_classification.md). Where a wave item
is claimed in both files, it is because the change had two distinct effects, not because
the credit is being counted twice.

| wave | Detection content | lives here? |
|---|---|---|
| Wave 1 (v8, 2026-05-18) | cross-page merge Case 5, gap-aware continuation, triage lexical override | yes (merge/coverage); the override is [Triage](1_triage.md) |
| Wave 2 (v8, 2026-05-24) | — (biblical filter is Classification; snap/trim are Boundaries) | no |
| Wave 3 (v9, 2026-05-25) | multi-story-per-page prompt + iterative second pass; embedded-story few-shots | yes |
| Waves 4 / 5 / 5b | — | no, all [Boundaries](4_boundaries.md) |
| Wave 6 | — | no, [Classification](3_classification.md) |
| Wave 7 (draft) | opener lexicon | shared with [Triage](1_triage.md) |

---

## What we tried

| when | what | outcome | evidence |
|---|---|---|---|
| 2026-01-19 | **One story per page → an array of stories per page**, each with its own extracted text | shipped. Ketubot 10b went 1 entry → 3; 67b 1 → 4 | `fab7282` |
| 2026-01-20 | **Segment-based detection** — keep Sefaria's aligned `text[]`/`he[]` structure instead of flattening the page; Hebrew narrative-marker scoring; character extraction; continuation grouping | shipped, and it is still the architecture. Matched Jeff's counts on the four pages checked (2a: 0, 10b: 3, 62b: 7, 67b: 5) | `b8290b8` |
| 2026-02-13 | **v7 constrained detection** — event-annotated prompt with anti-legal instructions and Ground-Truth few-shots | 109/127 vs v6's 105/127 against Jeff's 128 labels (**CIRCULAR**): +4 net, 10 fixes, 6 regressions | `12d8a89` |
| 2026-02-13 | **Stage 4 cross-page merge using triage event types**, promoting a NOT_A_STORY fragment when the adjacent page has a detected story | fixed 2 cross-page regressions (54a→54b, 56b→57a) | `cfaca8a` |
| 2026-02-22 | **v7.1/v8 cross-page work**: 5-segment context with Hebrew + event annotations (was 3, English-only, 150 chars); Case 4 merge when both sides are real stories; legacy merge relaxed from AND to OR; a post-detection **stitching** pass for stories flagged as continuing but never merged | shipped on Jeff's 96.3% review (105/109 correct), which had flagged 14 cut-off stories and 5 missing conclusions | `9435425`, `c7a2581`, `16ab025`, `40e3727` |
| 2026-03-01 | **Cross-page merge bug**: Stage 4c was overwriting correct 4b merges by grabbing an independent story further down page N+1 instead of the continuation fragment at seg 0 | fixed with four guards + 15 regression tests; 12 bad merges undone and re-stitched from seg 0 | `abe9337`, `cac23bb` |
| 2026-03-27 | **Sliding-window boundary check** — ask "is there a story at this page boundary?" across all boundaries | **REVERTED.** Caught 2 of 3 hand-picked missed merges, then produced **28 false positives** across ~100 boundaries in production. Triage filtering could not find a threshold | `de6a8c1`, Lesson 9 |
| 2026-03-27 | **Stage 4f continuation check** — the same problem asked narrowly: "does *this* detected story continue on the next page?" | shipped. **3 genuine cross-page stories, 0 false positives** on Kiddushin. The narrow question worked where the open one failed | `14a5f3a`, `6b2e471`, Lesson 10 |
| 2026-05-18 | **Wave 1 Issue #1 — first-segment skip ("the glitch")**: when both sides flag continuation and page 2's story starts at seg 1, force seg 0 | shipped; fired on Kiddushin 70a→70b **and on Ketubot 103b→104a**, a case Jeff had never seen. **Merge F1 0.59 → 0.88 on the Ketubot golden (CIRCULAR)** — the largest single-change gain in the project's history | `eff0218`, [`wave1_results.md`](../findings/2026-05-18-wave1-results.md) |
| 2026-05-18 | **Wave 1 Issue #2 — gap-aware continuation**: reject any bridge with segments intervening between story-end and the page break | shipped; removed 3 of Jeff's 4 false bridges (12b→13a, 29b→30a, 31a→31b). **#47 (39b→40a) survives** — it is adjacent, so the rule cannot see it; needs a content signal. Still open | `eff0218` |
| 2026-05-25 | **Wave 3 Item 1 — multi-story per page**: prompt section plus a second "find more, non-overlapping" Stage 2 pass, capped at one extra pass | **mixed.** The target fixture (Kiddushin 71a) still returns 1 story. But Items 1–3 together lifted Ketubot golden recall +0.044 (FN 17 → 10, **CIRCULAR**) and surfaced **7 new Kiddushin candidates** — the per-item split is not separable from the run | `dcefb30`, [`wave3_results.md`](../findings/2026-05-25-wave3-results.md) |
| 2026-05-25 | **Wave 3 Item 2 — embedded-story few-shots** (baraita-framed and objection-framed, drawn from Ketubot so Kiddushin stays clean per Lesson 2) | **half worked.** Kiddushin 33a seg 5 — the bathhouse story Jeff flagged as missed — is now detected. 81b seg 9 still missed: its lead-in does not resemble either pattern closely enough | `dcefb30` |
| 2026-08-28 | **True recall measured for the first time**, against `jeff comms/b.ketubot (1).doc` — 149 stories, written 2005-02-02, twenty years before the detector | **measured: 143/149 = 96.0% (BLIND).** The roadmap had guessed 80–85%. Two matcher fixes were needed first: Hebrew character 4-grams (Jeff writes abbreviated and unvocalised) and a corpus-wide sliding window (his story blocks cross daf boundaries). Before them the same data read 89.7% with 34 stories unlocated; after, 96.0% with zero | `8b86a9f`, [`recall_measurement`](../findings/2026-08-28-recall-measurement-ketubot.md) |
| 2026-08-30 | **Strict recall introduced.** The published test credits a proposal anywhere in the aligner's search window (up to 14 segments, straddling daf boundaries). Strict requires overlap with a segment the story actually occupies | **measured: 96.0% → 87.9% Ketubot, 12 stories credited by proximity only.** The 12 are cross-page stories whose text sits on a continuation daf carrying **zero proposals** — Ketubot 17b, 50a, 51a | `4de7135`, [`ruler`](../findings/2026-08-30-detection-classification-ruler.md) |
| 2026-08-30 | **Kiddushin Detection measured for the first time** | **measured: 93.3% loose / 83.3% strict** (84/90, BLIND) — **below the 95% gate where Ketubot is above.** First like-for-like comparison of the two tractates | `4de7135`, corrected by `2cd1094` |
| 2026-08-30 | Five stories from Jeff's blind list added to the Ketubot golden (20a, 53a, 67b, 72b, 82b) — a *double* miss, never detected and never labelled, so the harness was structurally unable to penalise them | golden 182 → 187; golden recall 0.9371 → 0.9085 (**the drop is the deliverable**); blind recall untouched at 96.0%; golden coverage of Jeff's list 96.6% → 100% | `2e61035` |

## What we reverted, and why

**1. The sliding-window boundary check (2026-03-27, `de6a8c1`).**
The idea: page-at-a-time processing makes the page break invisible to the model, so ask
directly whether a story sits at each boundary. On three hand-picked boundaries it found
2 of 3 known missed merges. In production across ~100 boundaries it produced **28 false
positives**, and no triage threshold separated them — the filter either let everything
through or blocked everything. Reverted the same session.

**Why it matters, and why not to re-try it in that form:** the failure was not the
mechanism, it was the *question*. "Is there a story here?" is open-ended, and this model
is generous about what counts as a story — the same over-detection seen everywhere else.
Replacing it with **"does this specific story continue?"** — a yes/no about a known
object — gave 3 real merges and 0 false positives on the same corpus (Lesson 10). Any
future attempt at page-boundary recovery should be framed narrowly, or it will reproduce
the 28.

**2. Detector-improvement experiments of 2026-03-25 (`c0ce13e`).**
Reverted for Classification reasons; recorded in
[`3_classification.md`](3_classification.md). They are relevant here only as the origin
of the rule that few-shots must not come from the pages being evaluated (Lesson 2), which
constrains every Detection prompt change since.

**3. Not a revert but a re-diagnosis, twice — both in our own disfavour of the earlier
story.** Three cases first filed as Detection misses turned out to be Classification
rejections, because the check behind the claim was narrower than the claim:

- **Ketubot 77a** — recorded as "never proposed." Measured over 8 re-runs of identical
  code: segs 13-14 **proposed in 7 of 8 runs**, classified `NOT_A_STORY` in 6 of those 7.
  Production fell in the ~1/8 tail. Capability reassigned 2 → 3 (`abdc4af`).
- **Ketubot 20a segs 2-3 and 53a seg 11** — stamped "never proposed by any detector run
  through v10" after checking only `results/v10/wave4_notrim/`. A text search across all
  53 run files found both, in `results/v5/pages_2-39.json` and
  `results/v7/ablation_v6_triage_merge.json`, at 100% Hebrew 4-gram coverage, both
  classified `NOT_A_STORY` (`6284070`).

**The taxonomy of the six Ketubot blind-list misses is therefore 3 Detection misses and
2 Classification rejections, plus 77a — not 5 misses + 1.** Any doc predating
2026-08-30 that says otherwise is superseded.

## Current best — the exact configuration

- **Detector:** `src/story_detector_v11.py` (the highest-numbered file is the active one;
  every lower one is a frozen ship point). Stage 2 = `detect_stories()`.
- **Model:** `gemini-3-flash-preview` for the production detection runs; the model is
  read from `GEMINI_MODEL`. Gemini 3 Flash was chosen over Gemini 3 Pro on measurement,
  not price: Flash 117/127 (92.1%) vs Pro 115/127 (90.6%) on Jeff's labels
  (**CIRCULAR**), with Pro 4× the cost and 3× slower — Pro is too conservative on
  borderline stories (`5ec53e3`).
- **Post-processing that affects coverage:** Stage 4b/4c cross-page merge (Cases 1–5),
  4d stitching, 4f continuation check, all in `src/story_detector_v11.py`.
- **The measured outputs:** `results/v10/wave4_notrim/*.json` — segment-level boundaries,
  no spans. These are the files both rulers read.
- **The rulers:** `scripts/measure_recall_vs_expert_list.py` (recall + what the Mishnah
  filter withheld) and `scripts/build_ruler.py` → `results/rulers/{tractate}_ruler.json`,
  which carries both `recall` and `recall_strict` per entry and is regression-tested
  against the published 96.0% (`tests/test_build_ruler.py`).

**Reproducing the number requires the blind lists**, not the goldens: a golden is built
*from* detector output and therefore cannot contain a story we never proposed
([`FRAMEWORK.md` §3](../../FRAMEWORK.md)).

## Distance to gate

| | current | gate | verdict |
|---|---|---|---|
| Ketubot loose | 96.0% | ≥95% | above |
| Ketubot strict | 87.9% | ≥95% | **7 points below** |
| Kiddushin loose | 93.3% | ≥95% | below |
| Kiddushin strict | 83.3% | ≥95% | **12 points below** |

**Which test the gate refers to has never been decided,** and it changes the answer.
FRAMEWORK's scoreboard quotes the loose figure and instructs that the strict one be
quoted beside it; on the loose test Ketubot passes and Kiddushin does not, and on the
strict test neither does.

**The loose test demonstrably over-credits — measured, not suspected, as of
2026-08-30.** Jeff's Kiddushin 81b story sits at segment 9; every run proposed segments
1–3 and 14 and nothing at 9 — **9% text overlap** — and the loose test credits it. This
is the first case provable without relying on the aligner, and it is pinned by
`tests/test_build_ruler.py::test_the_loose_window_credits_a_story_we_never_proposed`
(`2cd1094`).

**Noise floor: unknown for recall.** No same-code repeat has been run through the recall
harness. What *is* known, from the boundary work, is that this model moves ~3% of its own
outputs between identical runs (Lesson 22) and that Ketubot 77a is proposed in 7 of 8
runs — so a single production run can and does land in a tail. A recall figure from one
run carries an uncertainty band nobody has measured.

**One caveat on the miss labels.** `parse_expert_doc` matches only single-amud headers,
so stories under two-amud headers (`מט ע"ב-נ ע"א`) are credited to the preceding daf —
15 such headers in the Ketubot document, 21 stories across Gittin/Yevamot/Eruvin. The
**96% is unaffected** (`locate()` matches by n-gram across the whole corpus and never
reads the parsed ref), but the per-story `ref` label is unreliable, which is why
`results/rulers/ketubot_ruler.json` lists the misses as 19b/53a/67a/72a/77a/82b while the
prose calls them 20a/53a/67b/72b/77a/82b. Same six stories, different labels. **Any
per-daf analysis needs the parser fixed first** (`abdc4af`, `488576a`).

## Ceiling

**Human, not technical — and measured in Jeff's own words.** His 2005 lists missed
stories he later accepted from us; he cites this as proof of the project's value:
*"the AI has found some stories we missed"*
([ledger Part 2(a)](../../validation/feedback/jeff_2026-07-06_feedback_ledger.md)). So
100% against a blind list is not the standard, and matching a careful scholar working
deliberately is the honest ceiling ([`FRAMEWORK.md` §1.2](../../FRAMEWORK.md)). The
number 95 remains **invented** — see FRAMEWORK §2b.

**A structural sub-ceiling that is not a ceiling on Detection at all.** Two Kiddushin
cases (33a, 53a) have been `PART` in every run ever made — we propose one segment of a
two-segment story
([`kiddushin_list_parse` §4a](../findings/2026-08-30-kiddushin-list-parse.md)). That
survives every wave, but it is a **Boundaries** failure sitting on top of a Detection
hit, and counting it against Detection hides where the fix belongs
([`appendix_provenance_correction`](../findings/2026-08-30-appendix-provenance-correction.md)).

**The plateau claim, stated as it was found.** The 2026-07-06 approach review concluded
that *"detection accuracy has genuinely plateaued — every gain since Wave 1 came from
post-processors and corrections to the golden data, not from a smarter detector,"* with
the composite trajectory 0.8576 → 0.9164 → 0.9162 → 0.9170 → 0.9171 across Waves 1–4
([§3.3](../findings/2026-07-06-approach-review-and-scaling.md)). That is
**measured on a CIRCULAR set** and therefore says nothing about recall — a plateau in
agreement with the golden is compatible with any amount of undiscovered material. The
blind number that arrived seven weeks later (96.0%) was *better* than the roadmap
believed, which is the opposite of what a plateau reading would predict.

## Untried

- **Sliding-window / overlapping-window *detection*** — not the boundary check that
  failed, but changing the input geometry so a page break is never a hard edge.
  Documented 2026-03-27 as approach F with the explicit note that **no version, v1
  through v9, has ever tried changing the input windowing** (`074c7fb`); re-proposed
  2026-07-06 at an estimated +25% cost (~$0.08/tractate) and "do this once, at the v11
  fork, before mass rollout"
  ([§4.5](../findings/2026-07-06-approach-review-and-scaling.md)). Still untried.
  It targets the strict-recall gap directly: the 12 Ketubot loose-only credits are
  cross-page stories whose continuation daf carries no proposal at all.
- **Propose anything at all on Ketubot 17b, 50a, 51a** — three continuation dapim
  carrying zero proposals. Named, never investigated (`4de7135`).
- **The opener lexicon, mined rather than invented** (`docs/history/2026-08-28-PLAN-wave7-opener-lexicon.md`, DRAFT).
  Targets Ketubot 67b (`אמרו עליו`) and 82b (`בראשונה`). Shared with
  [Triage](1_triage.md); as a recall prior only, never a classifier (Lesson 15).
- **Kiddushin 12a — one detection covering two stories** (`work/2026-08-30-kiddushin-12a-dedup.md`), and the same
  shape Jeff flagged at 12a segs 13-15: two `הָהוּא גַּבְרָא` stories in one span, plus a
  partial duplicate ([ledger, Part 1](../../validation/feedback/jeff_2026-07-06_feedback_ledger.md)).
  A Detection question (*how many stories are here*), not a Boundaries one.
- **Kiddushin #47 (39b→40a)** — the one false bridge Wave 1's gap rule cannot reach,
  because it is adjacent. Open since 2026-05-18.
- **Ensembling / self-consistency** — k=3 at temperature ~0.7 with a majority vote, where
  disagreement between samples is itself the borderline signal; or a second-model
  re-verdict at ~$1/tractate, which also removes the single-vendor dependency (every
  stage currently rides one Gemini model with no retries and no fallback)
  ([§4.4](../findings/2026-07-06-approach-review-and-scaling.md)). Never tried,
  and it is the cheapest available answer to the run-to-run variance that put 77a in a
  1/8 tail.
- **Fine-tuning** — deferred deliberately, not rejected: it locks in whatever the labels
  currently are, so it should follow the recall probe and 1–2 more tractates of golden
  data, with leave-one-tractate-out evaluation
  ([§4.6](../findings/2026-07-06-approach-review-and-scaling.md)).
- **Declined, by Jeff:** *Ein Yaakov as a corpus-wide recall probe* — see
  [Triage](1_triage.md). Also declined: *a fresh cold-read of 10 random dapim*, because
  he already has detector-blind lists and offered them
  ([ledger Part 2(a)](../../validation/feedback/jeff_2026-07-06_feedback_ledger.md)).
- **The three pristine tractates.** Gittin (112), Yevamot (102) and Eruvin (73) have
  blind lists and fetched Sefaria text, and **the detector has never run there** — so a
  run is a clean floor test with no prior output priming either side, and their lists
  cannot have been contaminated the way Kiddushin's was
  ([`STATUS.md`](../../STATUS.md), `6d1f917`). This is the only generalization
  measurement available that is not partly circular.
