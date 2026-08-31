# Capability 3 — Classification

**Definition:** decide whether a proposed span is really a story, by Jeff's criteria —
see [`FRAMEWORK.md` §1.3](../../FRAMEWORK.md).
**Gate:** ≥85% precision (PROVISIONAL — *"the weakest of the six"*)
**Current:** **Ketubot 89.2%, Kiddushin 85.3%** — harness precision against the canonical
goldens (**CIRCULAR**), measured 2026-08-30 (`46d90b2`). *Review-round precision is a
**range**, not a point: Ketubot 87.9–94.8% (Mar 2026), Kiddushin 67.4–92.1% (Apr 2026, on
v7) — see §"Distance to gate".*

*Written 2026-08-30 from the sources in `work/done/2026-08-30-capability-histories.md`. History, not status.*

---

## Waves are not capabilities

Wave 6 is entirely Classification and has never been implemented. Waves 1–3 mixed this
capability with [Detection](2_detection.md); Wave 2's biblical-actor filter and Wave 3's
Item 3 are the Classification halves. Waves 4/5/5b contain nothing that belongs here.

One entry that looks like it belongs to Detection and does not: **the Mishnah filter**
(Wave 1 Issue #7). It removes stories the model correctly classified, on a scope rule.
Its cost lands in this capability's false-negative column, so it is recorded here.

---

## What we tried

| when | what | outcome | evidence |
|---|---|---|---|
| 2026-01-09 | First expert feedback applied: distinguish legal discussions from stories | shipped; the founding distinction of the project | `27170ba` |
| 2026-01-22 | **v4.1** — dialogue-marker weight cut from +10 to +3; Jeff's 6 validated examples added; a post-detection **self-check** pass | shipped; 30 stories on Ketubot 2a-39b | `68ce263` |
| 2026-01-25 | **Jeff's v4.1 verdict: 50% false-positive rate** (30 stories reviewed, 15 true / 15 false) | the number that reset the project | `94f7844` |
| 2026-01-25 | **v5.1** — built directly on that review. New `rabbi_legal_opinion` disqualifier (*rabbis **attributing** legal opinions are not characters **in** a story*); causality tightened from "connected" to "A caused B caused C"; change tightened from "different" to "transformed"; three new weakeners; self-check 6 → 7 questions | shipped. On Ketubot 2-39: `rabbi_legal_opinion` fired **53 times**; both of Jeff's true 8b stories found; his sequential-events example (14b) correctly rejected; 21 self-check adjustments | `94f7844`, `e37c20e` |
| 2026-01-25 | **Extrapolation check** — run v5.1 on the unseen Ketubot 40-60 and compare story rates | **measured: 20.6% vs 17.7%, a 2.8-point difference.** Read at the time as "no evidence of overfitting"; on a CIRCULAR basis, and the reading did not survive March | `ce82884` |
| 2026-02-12 | **v6** — Jeff's 128-passage review encoded: `identifiable_characters` replaces `named_characters` (anonymous characters count fully); biblical-narrative disqualifier **removed** because Jeff validated biblical stories; new `legal_deliberation` / `legal_debate_setting` disqualifiers; self-check to 9 questions | **regression: 105/127 (82.7%) vs v5.1**, 10 fixes and 12 regressions, net −2 (**CIRCULAR**) | `764877e`, `9bb8202` |
| 2026-02-13 | **v7** — decomposed pipeline: triage → constrained detection → merge | 109/127 (85.8%), +4 net over v6 | `12d8a89` |
| 2026-02-13 | **Adversarial validation** — three calls: detector defends, "Jeff's advocate" attacks, adjudicator rules | **BUILT AND DISABLED.** After 3 rounds of prompt tuning it was net −1 (109 → 108). The adjudicator over-demotes borderline stories Jeff had confirmed. Code retained, `enable_adversarial=False` | `77131ea` |
| 2026-02-13 | **Post-processing rules, 3 tried, 1 kept.** Rule 1 (single-event filter) **disabled** — regressed cross-page stories where count=1 is a partial-page artifact. Rule 2 (duplicate reclassification) **disabled** — the model flags valid continuations as duplicates. Rule 3 (v6 ensemble: demote where v6 disagrees **and** triage shows ≤1 narrative event) **enabled** | Rule 3: +3 net, zero regressions, 87.4% → 89.8% (**CIRCULAR**). This is the project's one working ensemble result | `b664003` |
| 2026-02-13 | **Model comparison, measured not assumed** | Gemini 3 Flash **92.1%** > Gemini 3 Pro 90.6% > Gemini 2.0 Flash+pp 89.8%. Pro is 4× the cost, 3× slower, and *more conservative* — it misses borderline stories Flash catches. Also: with G3 Flash, post-processing adds **nothing** (117/127 either way) — the model absorbed the rule | `a74554a`, `5ec53e3` |
| 2026-03-25 | **Golden dataset built** from four review rounds; `scripts/evaluate_golden.py` written and marked IMMUTABLE | baseline composite **0.93** (**CIRCULAR**): F1 0.92, IoU 0.98, merge F1 0.86, with 26 false positives named as the quality gap | `dc16195`, [`findings_v10`](../findings/2026-03-25-golden-dataset-v10.md) |
| 2026-03-25 | **Experiment 1 — aggressive prompt.** Five new disqualifiers from Jeff's own language; few-shot bank expanded 128 → 282 by loading the canonical review | **REVERTED. Catastrophic: composite 0.93 → 0.57.** Ketubot 2-60 fell from 72 detected stories to 44 | `c0ce13e` |
| 2026-03-25 | **Experiment 2 — light prompt.** Confidence calibration only (3 lines) plus the expanded few-shots | **REVERTED. Still a regression: 0.89.** Pages 2-60 fell 72 → 52; pages 61-112 barely moved (110 → 109) | `c0ce13e`, Lesson 2 |
| 2026-05-24 | **Wave 2 Issue #6(b) — biblical-actor filter.** Demote a story whose only named actors are biblical | shipped. Fired 3× on Kiddushin (38a "the Jewish people", 72b Nebuchadnezzar, 69b Ezra); two are exactly Jeff's flagged cases. **Kiddushin classification F1 0.9101 → 0.9257** (CIRCULAR). Fired 0× on Ketubot | `1c4d18d`, [`wave2_results.md`](../findings/2026-05-24-wave2-results.md) |
| 2026-05-25 | **Wave 3 Item 3 — sharper not-a-story rules**, written as abstract patterns rather than passages (Lesson 8): all-verbal → not a story; biblical-actor-only → not a story; <2 distinct actions or no change → not a story | **failed on its own target: Kiddushin FPs went up, not down.** Shipped anyway, because inspection showed the new "FPs" were largely real stories the golden did not contain — including Jeff's own flagged-missing 33a | `dcefb30`, Lesson 14 |
| 2026-06-03 | Jeff's Wave 3 reply applied: 7a re-added as LOW_CONFIDENCE, 26a and 102a confirmed not stories, 106a boundary extended | Ketubot composite 0.9170 → 0.9171 (+1 TP, −1 FP) | `402ed0d` |
| 2026-08-29 | **Wave 6 written, then split into measure → ask Jeff → implement**, after an audit found its own justification half wrong | **6c BLOCKED by design.** See "Ceiling" | [`PLAN_wave6.md`](../history/2026-08-29-PLAN-wave6-story-criteria.md) |
| 2026-08-30 | **Harness precision measured on the current detector** — correcting a claim in FRAMEWORK that no current number existed | **measured: Ketubot 89.2% (TP 149 / FP 18), Kiddushin 85.3% (TP 81 / FP 14)** (**CIRCULAR**). Both at or above the gate | `46d90b2` |
| 2026-08-30 | **The 86% / 68% figures re-derived** by sorting every rejection by *what Jeff objected to* | **measured: they were never Classification numbers.** Most rejections are boundary, merge or confidence-level complaints. Separated, both tractates land near 92–95% and the tractate gap mostly evaporates | `4de7135`, Lesson 30, [`ruler`](../findings/2026-08-30-detection-classification-ruler.md) |
| 2026-08-30 | **Ketubot 77a diagnosed** over 8 re-runs of identical code | **measured:** segs 13-14 proposed in 7 of 8 runs, classified `NOT_A_STORY` in 6 of those 7, every run citing the same three prompt disqualifiers. A Classification failure sitting on proposal-level variance | `abdc4af` |
| 2026-08-30 | **Mishnah filter cost measured** by scoring twice through the immutable harness | **measured: 4 of Ketubot's 15 golden false negatives — 27%.** Folding them back moves golden recall 0.9085 → 0.9329, precision unchanged. Blind recall identical at 96.0% both ways | `804a097`, [`mishnah_filter_delta`](../findings/2026-08-30-mishnah-filter-delta.md) |
| 2026-08-30 | **Mishnah tagger chapter-boundary bug fixed** — the tagger read only `מתני׳`/`גמ׳`, but Sefaria opens a new chapter's first Mishnah with the chapter incipit, so `גמ׳` came first and everything before it was back-tagged as Mishnah | **fixed and measured: Ketubot TP 149 → 151, FN 15 → 13, golden recall 90.9% → 92.1%**, precision and merge unchanged. 72 segments on 12 pages, every change a correction | `8fd68de` |

## What we reverted, and why

**1. The two prompt experiments of 2026-03-25 (`c0ce13e`) — the most instructive
failure in the project.**
Aggressive → **0.93 to 0.57**. Light → **0.93 to 0.89**. Root cause: the expanded
few-shot bank was drawn from Jeff's canonical review, which is predominantly pages 2-60,
and those are the pages being evaluated. The model memorised the specific rejections and
over-applied them locally — pages 61-112, which had almost no examples from that review,
barely moved (110 → 109). Textbook train/test contamination.

**The two rules this bought, both still binding:**
- **Lesson 2** — few-shot examples must come from a different dataset than the one being
  evaluated. Every prompt change since has obeyed it; Wave 3's embedded-story examples
  were deliberately taken from Ketubot so Kiddushin stayed clean.
- **Lesson 5** — prompt engineering has a ceiling. At 0.93 the residual errors are
  judgment calls in passages with **both** narrative and legal elements; the model
  already knows legal discussions are not stories.

**2. Adversarial validation (2026-02-13, `77131ea`) — built, tuned three times,
disabled.** Net −1 on Jeff's 128 labels. The adjudicator systematically over-demotes the
borderline cases Jeff had confirmed. The code is still in the tree behind
`enable_adversarial=False`. Do not re-enable it without a new reason; three tuning rounds
already failed.

**3. Post-processing Rules 1 and 2 (2026-02-13, `b664003`) — disabled at birth.**
Rule 1 (demote single-event stories) broke cross-page stories, where `count == 1` reflects
seeing half a story. Rule 2 (trust the model's duplicate flag) demoted valid continuations.
Both are the same error: a page-local signal read as a global one.

**4. Not reverted, and worth flagging as a live contradiction: the Mishnah filter.**
Wave 1 Issue #7 moves any story lying entirely inside a Mishnah block out of `stories`
into `mishnah_stories` — a key **no harness and no review UI reads**. So a story we found
and then deliberately deleted scored exactly like a story we never found, from v8 to v11
(Lesson 27). Two halves:

- **The bug half is fixed** (`8fd68de`): two of the four Ketubot deletions were plain
  Gemara mis-tagged at a chapter boundary. TP 149 → 151.
- **The scope half is Jeff's to settle, and both sides of it are his.** The premise is his
  (Kiddushin 50b: *"catalogued with Mishnah stories, not Talmud stories"*) — but he also
  marked **correct** in review all four Ketubot stories the filter deletes. He asked for a
  separate **catalogue**; we built a **deletion** that nothing catalogues, scores or
  displays. Under his literal words there is no contradiction to resolve. Two genuine
  cases remain (Ketubot 14b seg 11, 77a seg 8, plus Kiddushin 50b seg 10), queued for the
  next email ([`email_jeff_next_open_questions.md`](../../comms/email_jeff_next_open_questions.md)).

**5. Not a revert but a redefinition of the number.** The 86% / 68% precision figures,
which made Classification "our weakest capability" for months, counted every `incorrect`
verdict whatever Jeff objected to — including `adjust`, which literally means *"this is a
story and the boundary is wrong"* (Lesson 30). Any doc quoting 86/68 as classification
precision is superseded by `4de7135`.

## Current best — the exact configuration

- **Detector:** `src/story_detector_v11.py`, Stage 2 — Detection and Classification are
  one call today. That is an implementation detail, not a reason to measure them together
  ([`FRAMEWORK.md` §1](../../FRAMEWORK.md)).
- **Model:** `gemini-3-flash-preview`. Chosen on measurement over Gemini 3 Pro
  (`5ec53e3`).
- **Criteria in force:** the v5.1/v6/v7 lineage — six criteria, a disqualifier list
  (`rabbi_legal_opinion`, `legal_deliberation`, `legal_debate_setting`, all-verbal,
  biblical-actor-only, <2 distinct actions), weakeners, and a self-check pass. Few-shots
  come from `src/ground_truth.py` (Jeff's labels), never from the pages under evaluation.
- **Post-processors that change a classification:** biblical-actor filter (Wave 2), the
  v6-ensemble Rule 3 (v7), and `filter_mishnah_only_stories()` (Wave 1 — see above).
- **Harness:** `scripts/evaluate_golden.py` — **IMMUTABLE**, never modified during an
  experiment. **Always pass `--output`**: it defaults to overwriting
  `docs/golden/v7/baseline_ketubot.json`, an irreplaceable historical record (`46d90b2`).
- **Goldens:** `results/canonical/ketubot_canonical.json` — 222 pages, **187 entries, 164
  accepted** (YES 59 / HIGH 28 / LOW 77 / NOT_A_STORY 23);
  `kiddushin_canonical.json` — 162 pages, **96 entries, 85 accepted** (44/8/33/11).
  Verified 2026-08-30. Quote them the same way — entries against entries, accepted
  against accepted, never one of each (`6d1f917`).
- **Never verify with the composite score.** It is built from ratios over pages already in
  the golden, so *deleting* expert validations makes it go **up**. Verify with counts and
  `git hash-object` (`work/done/2026-08-30-capability-histories.md`).

## Distance to gate

**Above the gate on the harness measure, in both tractates — and the gate is the
weakest of the six.**

| measure | Ketubot | Kiddushin | gate |
|---|---|---|---|
| harness precision (CIRCULAR, current detector) | **89.2%** | **85.3%** | ≥85% |
| review-round precision, all-causes → classification-only | 87.9 → 94.8% (n=173, Mar 2026) | 67.4 → 92.1% (n=89, Apr 2026, v7) | — |

Three things this table hides, all of them stated rather than smoothed:

1. **We have a harness point estimate, not a review-round one.** The review rounds cannot
   give a point estimate, because the reviewer never recorded *which thing* he was
   rejecting. The range's width **is** the unreadable notes: 9 + 9 + 6 across the rounds.
   Narrowing it needs the review UI to capture the distinction (`work/2026-08-30-review-verdict-axes.md`), not
   more inference over free text (Lesson 30).
2. **The gate itself is invented.** *"Below ~85% a reviewer spends more time rejecting
   than confirming"* is a plausible sentence with no measurement behind it. Only Jeff can
   settle it, and the question is drafted
   ([FRAMEWORK §2b](../../FRAMEWORK.md), [`email_jeff_next_open_questions.md`](../../comms/email_jeff_next_open_questions.md)).
3. **Precision is measured on a CIRCULAR set, which is correct for precision and useless
   for the other direction.** The invisible half of this capability — real stories we
   *reject* — is as costly as a Detection miss and has no measurement at all. The only
   three cases we know of (Ketubot 77a, 20a, 53a) were found by chasing blind-list misses,
   not by any classification metric (`abdc4af`, `6284070`).

**Noise floor: partially known, and it is not small.** Ketubot 77a's segs 13-14 are
proposed in 7 of 8 identical runs and rejected in 6 of those 7 — so this capability's
verdict on a single borderline passage is roughly a 7-in-8 / 6-in-7 coin. No aggregate
precision figure has ever been repeated on identical code, so the spread on 89.2% is
unmeasured (Lesson 22).

## Ceiling

**Two ceilings, and the second is the real one.**

**1. Prompt engineering caps out (measured, 2026-03-25).** Two attempts to encode Jeff's
own reasoning as prompt rules both regressed — badly. The residual false positives are
*legal discussions with narrative framing*, where roughly half of false positives contain
physical action and two-thirds of true stories do; the distinguishing feature is
structural (does the narrative serve the legal debate, or the debate the narrative), which
no additional prompt rule captures
([Lesson 5](../../lessons/README.md), [§3.3](../findings/2026-07-06-approach-review-and-scaling.md)).

**2. The ground truth is contested — by the expert, with himself. This is the ceiling
that matters, and it is definitional, not technical.**

Jeff's 2026-07-06 criteria contradict his own 2026-03-17 rulings. Both are his; neither is
wrong; they cannot both be mechanically applied
([`PLAN_wave6.md`](../history/2026-08-29-PLAN-wave6-story-criteria.md) Finding 1):

| 2026-03-17 rulings | 2026-07-06 criteria |
|---|---|
| *"only one action followed by a legal ruling"* → **not a story** | *"A man stole another man's cow and sold it. Rava ruled…. In this case you may have a story."* |
| *"stating, objecting, asking questions are all part of a dialogue, not really events"* | *"speech-acts don't count… minimally there must be some action beyond the speech"* — i.e. speech **plus** action qualifies |
| dialogue-heavy passages → **LOW_CONFIDENCE, still stories** | the same passages read as **not stories at all** |

**The blast radius is measured: 110 of the 249 accepted golden entries are
LOW_CONFIDENCE** — Ketubot 77 of 164, Kiddushin 33 of 85 (verified 2026-08-30). Jeff's
newer rule points directly at that bucket. Applying it is not a prompt change; it is a
redefinition of what the dataset means, and it is his call. That is why Wave 6 is split
into **6a measure → 6b ask → 6c implement**, with 6c blocked by design.

This is also why [`FRAMEWORK.md` §1.3](../../FRAMEWORK.md) calls this the one capability
where *"mark it borderline and let database users decide"* is a legitimate answer rather
than an evasion — and Jeff's own crowd-sourcing preference (keep contested cases, flagged)
suggests he may choose exactly that.

## Untried

- **Wave 6a — measure the blast radius on one axis** (*does anything non-speech happen?*)
  across the 110 LOW_CONFIDENCE golden entries. ~$0.10, needs nobody, and it is the
  deliverable that makes 6b answerable. **Never run.**
- **Wave 6b — ask Jeff the question**, in his own words, with the count and 3–4 examples:
  should those entries become NOT_A_STORY, stay LOW_CONFIDENCE, or take a new
  **borderline** status? Drafted, not sent.
- **A post-hoc false-positive classifier** — logistic regression / LightGBM on the
  features the detector already emits (`criteria_met_count`, disqualifiers, actor type,
  segment count), validated leave-one-tractate-out. Recommended twice (Lesson 7, 2026-03;
  [§4.3](../findings/2026-07-06-approach-review-and-scaling.md), 2026-07) on the
  grounds that a post-filter **can only demote, so it can never create a new missed
  story** — the opposite risk profile to a prompt edit. **Never built.** Note the
  converse, recorded in `PLAN_wave6`: it also cannot *recover* false negatives, which is
  what Wave 6 is for, so the two are separate jobs and must not be bundled.
- **A `borderline` flag in the output schema.** Jeff asked for contested cases to be kept
  and surfaced rather than silently decided
  ([ledger Part 2(d)](../../validation/feedback/jeff_2026-07-06_feedback_ledger.md)).
  Nothing in the pipeline emits one.
- **A criteria-conformance test set** of labelled minimal pairs — hypothetical legal case
  vs matched factual story; pure discussion vs discussion+action; emotional-reaction
  cases — gating every future detector, **test-only and never few-shot** (Lessons 2, 8).
  Specified in
  [`jeff_story_definition_criteria.md`](../findings/2026-07-06-jeff-story-definition-criteria.md)
  and in `PLAN_wave6`; the seed case (the Ketubot 77a minimal pair, segs 8 and 13-14 on
  one daf) is written. **Not built.**
- **Fold in the verdicts nobody used.** The goldens are incomplete in a way that flatters
  nothing: 16 Kiddushin verdicts from the 2026-05-26 and 2026-07-06 rounds were never
  folded in; Ketubot has 26 unique deferred/needs-review items, 8 skipped and 5 deferred
  boundary corrections; **52 Ketubot proposals carry no verdict at all** (`f415a9f`,
  `4de7135`, `work/2026-08-30-golden-completeness.md`). Separately, the ruler folds in 7 of
  the 8 verdict files on disk — the 2026-01-08 round (25 verdicts) is not among them
  (measured 2026-08-30 from `results/rulers/*.json`).
- **Rebuild the Kiddushin golden on a current run.** Its verdicts were given on **v7**
  output while the detector is v11, so its precision range describes v7, not what we ship
  (`4de7135`).
- **Ensembling / self-consistency for the judgment calls** — see
  [Detection](2_detection.md); it is listed there but its payoff is here, since the
  residual errors are judgment calls and judgment calls benefit from votes.
- **Deliberately not done:** re-enabling adversarial validation; re-trying Rules 1 and 2;
  any further attempt to raise precision by adding disqualifiers to the Stage 2 prompt.
  All three have failed measurements behind them.
