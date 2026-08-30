# Plan — Gemini model upgrade, measured (2.5-flash → 3.7-flash)

**Status:** DRAFT. **Deliberately separated from Wave 5** at Simon's instruction:
run the old model and the new model and understand the differences, rather than
bundling a model change into a mechanism change.

**Why separation matters here:** the project has repeatedly been burned by
unattributable score movement (Wave 4 was made score-neutral by design; Wave 6 is
split from Wave 5 for the same reason). A model swap changes *which stories are
found*; a mechanism change changes *where they trim*. Together they are unreadable.

---

## What is already settled (2026-08-29)

The **span stage** A/B is done — see [PLAN_wave5.md](PLAN_wave5.md). Because spans
are score-neutral, that comparison was safe to run alone. Result: both models
produce 0 mid-word cuts; 3.7-flash + thinking HIGH scores 5/8 vs 4/8 on Jeff's
stated boundaries and, decisively, **errs by keeping too much rather than cutting
too much**. Recommendation there: adopt 3.7-flash for the span stage.

**This plan covers the part that is NOT settled: Stage 1 triage and Stage 2
detection**, where a model change moves the score and the story set.

## Why this matters more than it looks

Triage currently skips **56% of Ketubot pages**, and 3 of the 6 known recall misses
(20a, 72b, 82b) are pages triage never passed to Stage 2. Triage is a
cheap classification task — exactly where a stronger model may behave differently.
This upgrade and the triage-recovery work are the same question asked two ways.

## Design

Three arms, same code (`src/story_detector_v11.py`), same inputs, same day
(Lesson 11 — never compare against a frozen historical baseline):

| Arm | Model | Thinking |
|---|---|---|
| **A** | gemini-2.5-flash | none (current production) |
| **B** | gemini-3.7-flash | none |
| **C** | gemini-3.7-flash | HIGH |

Arm B exists to separate *model* from *thinking*. Without it, a gain from C is
unattributable — the same mistake this plan exists to avoid.

## Measurements (all on Ketubot + Kiddushin, both ranges — Lesson 6)

| Metric | Why |
|---|---|
| Composite, F1, IoU, merge | the standard harness, regenerated same-day |
| **Recall vs Jeff's 2005 list** (143/149 = 96.0% baseline) | detector-blind ground truth; the honest recall number |
| **Segment-boundary agreement** vs the same list (69% exact baseline) | boundary quality, independent of the golden |
| **Triage skip rate** and stories lost to triage (3/149 baseline) | the suspected upgrade payoff |
| Story-set delta | which stories appear/disappear — inspect by hand (Lessons 13, 14) |
| Cost and wall-clock | 3.7 + HIGH ran 6.7x slower on the span stage |

## Interpretation rules agreed in advance

- **A composite drop is not automatically a regression.** If the new model finds
  stories the golden lacks, the score falls while quality rises (Lessons 13, 14).
  Any drop must be inspected story-by-story before it is called a regression.
- **Expert-list recall is the tiebreaker**, because it is the one metric that is not
  circular.
- Record the exact model string and thinking level in every output's metadata
  (roadmap 5.3 item 5 — pin and record external versions).

## Cost

3 arms x 2 tractates x ~$0.30–0.60 ≈ **$2–4**, plus 3.7+HIGH latency. Cheap enough
that the only real cost is analysis time.

## Sequencing

Run **after** Wave 5 ships (so the boundary mechanism is stable and not a
confound), and **before** Wave 6 (so the criteria work is built on the model we
intend to keep). If the upgrade changes the story set materially, Wave 6's
conformance baseline must be rebuilt on the new model.
