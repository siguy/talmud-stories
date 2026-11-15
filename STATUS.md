# STATUS — where the project is today

**Rewritten 2026-11-15**, at `02438ad` (PR #96). The last rewrite was 2026-09-29, and about 25
PRs have merged since. This file is rewritten each time, never appended to.

This file holds the judgment and the live hazards. The generated matrix is
[`STATE.md`](STATE.md) (run `python3 scripts/board.py`; never edit it by hand). The terms
used here (capability names, BLIND / CIRCULAR, measured / indicated / suspected) come from
[`FRAMEWORK.md`](FRAMEWORK.md). Every figure links to the finding it comes from.

---

## 1. Where we are now

- **All of Shas is on the Septimus site: 37 tractates, 1,811 stories,** plus 102 biblical
  stories that are found and held in each file's `out_of_scope` list (measured: counted
  from `site/data/` at `02438ad`). The site ships **definite stories only**
  ([filter doc](docs/technical/septimus-story-filter.md), L-045).
- **How we got from 1,897 to 1,811:**

  | step | stories | source |
  |---|---|---|
  | Shas run, biblical stories shipped with a flag (11-10) | 1,897 | [shas-run](docs/findings/2026-11-10-shas-run.md) |
  | biblical stories moved out of scope, plus 12 passages Jeff ruled not/borderline removed (11-13) | 1,784 | [shas-accuracy §Update](docs/findings/2026-11-10-shas-accuracy.md) |
  | 80 LOW-pool promotions (11-14) | 1,864 | [low-pool grader](docs/findings/2026-11-13-low-pool-grader-calibration.md) |
  | twin-pass card cleanup, two passes (11-14) | 1,847, then 1,811 | [twin-pass cards](docs/findings/2026-11-14-twin-pass-site-cards.md) |

- **Story ids are permanent now** (`site/data/story_ids.json`, `scripts/story_ids.py`). Before
  this, a story's id was its span, so fixing a boundary orphaned every read-checkmark,
  note and piece of feedback attached to it. Ids are now matched by segment overlap: a
  shifted story keeps its id, a merge redirects, a removed story's id is retired. The first
  real case was Ketubot 106a, which kept `ketubot-106a-2-3` after its span went back to 3-3.
- **The active detector is v14**, adopted 2026-11-08. Confirmed by
  `grep -n 'as detector_module' scripts/run_new_tractate.py`, which shows `story_detector_v14`
  at line 329. ([v14 vs v11, Yevamot](docs/findings/2026-11-08-v14-vs-v11-yevamot.md))
- **The run itself (11-09 → 11-10):** 32 new tractates through triage, two v14 runs, both
  judges and gates G1–G7. No gate is red; 9 tractates under 90% two-run agreement ship by
  Simon's ruling. **The bill was $85** (AI Studio), not the metered $69.82
  ([shas-run](docs/findings/2026-11-10-shas-run.md)).

## 2. Accuracy across Shas

Short version: **the detector finds nearly all of Jeff's stories. The site shows about 7 in
10 of them, because it ships only definite stories. Roughly 9 in 10 of what it ships are
real stories, but that figure is indicated, not measured.**

**Caution:** every figure in this section was measured on the **1,784-story** site, before
the 80 promotions and the 36 twin-card removals. None of it has been re-run since (see §7).

### Recall: does the site have Jeff's stories? (BLIND)

From [how-many-stories-we-miss](docs/findings/2026-11-13-how-many-stories-we-miss.md). These
counts use Jeff's lists *after* his later `not` rulings are taken out of the denominators.

| | Eruvin (held out) | Yevamot | Eruvin + Yevamot |
|---|---|---|---|
| denominator | 55 | 99 | 154 |
| detector proposes it (either run) | 55 (100%) | 94 (94.9%) | **149 (96.8%)** |
| on the site | 43 (78.2%) | 64 (64.6%) | **107 (69.5%)**, Wilson 61.8–76.2% |

- **The site filter, not the detector, is where stories are lost.** On the 154 stories, the
  filter costs about 27 points (36 stories graded LOW, or definite in only one run). The
  detector costs about 3 points (finding) and 4.5 points (graded `NOT_A_STORY`). Measured.
- **Eruvin's 55/55 means "no miss measured", not 100% recall.** Jeff ruled 19 of his own 74
  Eruvin entries `no` on 2026-11-12, and all 7 detector misses were among those 19
  ([Jeff 11-12 verdicts](docs/findings/2026-11-13-jeff-verdicts-eruvin-and-septimus-sample.md)).
  The 55 left are the entries nobody flagged as questionable, so this flatters Eruvin.
- **The reviewed tractates (CIRCULAR, built from goldens):** on the site, Gittin 108/110,
  Kiddushin 52/90, Ketubot 86/145. Of the 70 list stories those three lose at the filter, 60
  are Jeff's own listed stories that the old detector graded LOW in the golden.
- **Estimate: at least ~700 real stories are missing from the site (range ~520–940).**
  Indicated. It is a lower bound, because Jeff's lists are not comprehensive and probably
  hold the clearer stories. About 60% of the misses are real stories graded LOW_CONFIDENCE.
  (Same finding, §3.)

### Precision: are the shipped stories real? (indicated)

- **The 60-story stratified sample:** 54/60 = 90% definite stories (Wilson 80–95%). 57/60
  count if borderline is included. **3/60 are not stories, measured by Jeff.** It stays
  *indicated* because 53 of the 60 grades are Simon's pre-read, and Jeff saw only the 7 that
  Simon's grade picked out ([Jeff 11-12 §2](docs/findings/2026-11-13-jeff-verdicts-eruvin-and-septimus-sample.md),
  [Simon's pre-read](docs/findings/2026-11-12-simon-precision-pre-read.md)).
- **What Simon's notes found:** they were about extent, not classification. Of 10 flagged
  "did we catch the next story?" neighbours, 8 were already on the site as separate cards.
  One was a real miss held at LOW (Sanhedrin 52b:4, now shipped on Jeff's word). The other
  turned out to be out of scope.

### Coverage and agreement (measured)

[shas-accuracy](docs/findings/2026-11-10-shas-accuracy.md):

- 4,787 pages in the 34 v14-run tractates, every one labelled by triage, with 0 triage,
  Stage 2 or Stage 4 call failures. Triage examined 43.4% of pages and skipped the rest on
  purpose.
- **G4 (the two runs agree):** 1,420 of 1,526 definite passages are definite in both runs
  (93.1%).
- **32 of the 37 tractates have no expert list**, so recall there is indicated from the
  other five (Lesson 18).

## 3. What shipped this week (11-09 → 11-15)

- **LOW-pool promotions: 80 stories added, model-graded.** A Claude grader (the judge
  prompt at sha `88e8fff62716`) was calibrated on 300 spans Jeff has ruled on. When both of
  its passes say `story`, it is right **32/33 = 0.97** of the time (Wilson 0.85–1.00), but
  it finds only **32/141** of Jeff's yes stories. Most of the calibration set is CIRCULAR,
  and the BLIND slice is only 6/6 spans. It graded all 1,259 pool spans twice, and 80 came
  out `story` in both passes. **Simon shipped all 80 on 2026-11-14 and waived the 54-of-60
  review bar** after reading part of the sample. Each carries
  `included_by: "low-pool-grader-2026-11-13"`, and the decision is recorded in
  `results/shas_run/septimus_site_decisions.json`. This is the first sanctioned promotion
  path past the detector's grade (L-045).
  ([finding](docs/findings/2026-11-13-low-pool-grader-calibration.md))
- **Twin-pass card cleanup: 1,864 → 1,811.** The first pass removed 17. The second read 60
  more: it removed 32 cards plus 1 duplicate, merged 3 pairs, extended 1, and kept 12. Simon
  kept the 4 he was asked about and then all 11 "show Simon" cards ("keep them all"). Every
  call was a rules-based read against `STORY_RULES.md`, not Jeff's, so these are
  *indicated* not-stories. **Main lesson: two runs agreeing is weak evidence for a twin-pass
  card**, because both runs share the twin prompt and make the same mistake together.
  ([finding](docs/findings/2026-11-14-twin-pass-site-cards.md))
- **Ketubot 106a segment-numbering fix.** Our 2026-05-25 email gave Jeff 0-based segment
  numbers without saying so, and linked to Sefaria, which counts from 1. His "segments 2-3"
  was Sefaria's count, and we applied it 0-based. The famine entry is back to 3-3. Of the 4
  items in that reply, only this one was a boundary, and nothing else moved. Whether the
  Elijah passage is its own story is now `jeff:106a-elijah-split`.
  ([finding](docs/findings/2026-11-14-jeff-segment-numbering.md); lesson
  `_say-which-number-is-segment-one`)
- **Feedback worker fixed and redeployed.** It now accepts story ids from every tractate,
  not only the 4 reviewed ones. 19 tests (`worker/feedback-worker.test.mjs`) found five more
  defects, all fixed: a prototype-key bypass, a trusted tractate label, a refs cap, an
  unhandled GitHub failure, and an over-long fallback URL. Redeployed to Cloud Run as
  revision `septimus-feedback-00004`. The steps are in `worker/README.md`.
- **Site data contract:** a JSON Schema; the viewer no longer reads the grade; twin-pass
  reasoning no longer leaks into 76 card summaries; 85 written summaries fill empty cards.
- **Jeff's 2026-11-12 verdicts applied:** Eruvin's 19 `no`s plus 1 borderline, and the 8
  sample passages. They moved the rule register: R-C0, R-B4, R-C2 (a setting plus a question
  and answer is not a story, which settles `jeff:question-and-answer` by rule), R-S1 and
  R-C7. Yevamot's denominator went from 100 to 99. The judge prompt's sha moved with the
  register, and G6 is re-pinned to `88e8fff62716`.
  ([finding](docs/findings/2026-11-13-jeff-verdicts-eruvin-and-septimus-sample.md))

## 4. Measured but not shipped

- **The narrate test** is recorded on main (closed 2026-11-15):
  [finding](docs/findings/2026-11-14-narrate-test.md). The question: does asking a model to *narrate* a passage tell a story
  from a non-story, and find where it ends? Measured, two passes each:
  - **A narrator without the rules** finds more of Jeff's stories but is too loose:
    precision 0.80–0.81, recall 0.57–0.65 of his 141 yes. The model was not the cause (Opus
    reads the same as Sonnet); the missing rule register was.
  - **The hybrid (narrate, then apply the rules):** precision about **0.95** (0.93–0.95),
    recall about **0.29** (0.29–0.30). It meets the second-judge bar, but only by turning
    into the grader. Combined with the grader, it adds about 10 of Jeff's 141 yes at no
    precision cost. Running it on the pool is Simon's call.
  - **The border test: no gain on ends.** Even with an unmarked window (no hint of the
    card's extent), the narrator picks the detector's extent in 83–86% of windows. Ketubot's
    end misses stay misses (10–12 of 21). Where both disagree with Jeff's 2005 ends, the
    answer probably lies in his conventions, so it is a question for him, not a better prompt.
- **Judge prompt v4 is not adopted** ([finding](docs/findings/2026-11-09-judge-register-v4.md)).
  Dropping "one event, then a ruling" from borderline also drops about 12 of Jeff's yeses,
  9 of them the "came before a rabbi" shape. v2 stays the judge's wording, now at the
  re-pinned sha.
- **Wider site rules, priced and not applied**
  ([how-many §4](docs/findings/2026-11-13-how-many-stories-we-miss.md)):
  - **Option 0:** ship the 60 golden-LOW stories that are on Jeff's own list. No precision
    cost by his evidence. Ketubot would go from 59% to 86%, Kiddushin from 58% to 81%.
  - **Rule A:** a story definite in one run and at least LOW in the other. About +57 real
    stories for about 38 non-stories; precision 0.90 → 0.88.

  Both are Simon's call.

## 5. Jeff

[`comms/JEFF.md`](comms/JEFF.md) owns this. Do not keep a second copy here.

- **Waiting on him:** nothing is out. He answered both 2026-11-12 asks the same day. **The
  next email is drafted and held, not sent** (Simon's decision).
- **Still open:** `jeff:boundary-end-rule` (asked 2026-08-30, still blocking capability 4),
  `jeff:miss-rate` (now with numbers to put beside it: the detector misses about 1 in 30,
  the site about 1 in 3), `jeff:review-error-rate`, `jeff:deliverable-shape`. Two free asks
  ride with the next email: `jeff:scope-edges` and `jeff:106a-elijah-split`.
- **Queued, not yet asked:** his older `yes` on 9 "came before a rabbi" passages (decides
  judge v4); 106 one-run-only passages (`results/shas_run/reading/jeff_two_run_disagreements.json`);
  the Ketubot end-boundary misses.
- **His interface note (2026-11-12):** *"The interface did not work for me."* The claude.ai
  artifact page probably needed him signed in. The standalone HTML page for Eruvin worked,
  so send standalone files.
- **Settled since 2026-09-29:** his 10-07, 10-25 and 11-12 replies closed nine questions
  (all in JEFF.md). His **recent rulings outrank the 2005 lists**, which are "initial"
  ([10-07](docs/findings/2026-10-09-jeff-answers-four-lines.md)).

## 6. Earlier (Aug–Oct), still true, condensed

- **Recall is measured with exact-phrase anchoring** (2026-09-03). The old 4-gram window
  credited neighbouring passages. Loose and strict recall are no longer separate figures.
  ([matcher](docs/findings/2026-09-03-exact-anchor-matcher.md))
- **The detector is not deterministic.** Identical full-tractate runs differ by a few
  stories, so compare runs in pairs, and treat a one-story delta between single runs as
  noise ([finding](docs/findings/2026-09-27-detector-is-not-deterministic.md), Lesson 43).
  This is why the site needs a story to be definite in *both* runs.
- **The twin pass** catches the formulaic "twin" story beside one already found. It has been
  on by default since 2026-09-25 ([twin-pass](docs/findings/2026-09-14-twin-pass.md)).
- **Classification precision read correctly** (verdicts read against the call Jeff was
  shown) is ~0.92–0.95 on the older review rounds. CIRCULAR, and true of older detector
  versions ([finding](docs/findings/2026-09-29-verdicts-read-against-the-call-shown.md)).
- **The consensus judge is not a gate.** Phase 1 and 1b were no-go
  ([phase 1](docs/findings/2026-09-28-consensus-phase1.md)). After Jeff's 10-07 rulings the
  two judges drifted apart, to 75.5% agreement
  ([v3](docs/findings/2026-10-09-consensus-v3.md)). The nine-question "lens" panel made a
  worse classifier but a sharp diagnostic
  ([lenses](docs/findings/2026-10-02-rule-panel-lenses.md)). The judges route and inform;
  they never promote on their own.
- **Borderline means "part of a story"** (R-C7). Widening it recovered partial stories, and
  narrowing it again was reverted ([finding](docs/findings/2026-10-09-borderline-definition-test.md)).
- **v13/v14 history:** on the 20-page slice v14 first lost to v11 and was not adopted
  ([v13 slice](docs/findings/2026-11-07-detector-v13-slice.md)). On full Yevamot the recall
  was tied, and v14 was adopted because what it removes is Jeff's October rulings. On
  Berakhot both judges side with v14 on 14 of 20 moved passages, against 1 for v11
  ([Berakhot](docs/findings/2026-11-08-v14-vs-v11-berakhot.md)).
- **The run path was reviewed and fixed before Eruvin** (PRs #69–#71): cross-page merges,
  unsorted twin additions, empty responses that had been written as "no stories", and 429
  retries ([run path](docs/findings/2026-11-07-pre-eruvin-code-review.md),
  [review UI](docs/findings/2026-11-07-review-ui-review.md)).
- **The public page moved** to simonbrief.com/talmud-stories, and GitHub Pages is retired.
  Its figures were typed by hand and are dated October 2026
  ([finding](docs/findings/2026-10-02-public-site-moved-to-hub.md)).

## 7. Live hazards

1. **The accuracy figures in §2 describe the 1,784-story site.** Since then 80 model-graded
   stories were added and 36 twin cards removed. Re-run `scripts/measure_site_misses.py` and
   `scripts/measure_shas_accuracy.py`, both with `--out` and no model calls, before quoting a
   site number.
2. **Site precision is not measured.** There are three soft spots: 53 of the 60 sample grades
   are Simon's; the 80 promotions rest on a mostly CIRCULAR calibration with a 6-span blind
   slice; and the twin cards that remain had one rules-based read, not Jeff's.
3. **Run agreement does not protect twin-pass cards** (§3). Do not read "definite in both
   runs" as independent evidence for them.
4. **Biblical material still gets past Stage 4j.** v14 keeps David and the Gibeonites in 2 of
   2 Yevamot runs and five Berakhot episodes in every run, because the actor filter misses
   groups and "God". The site catches these only through the judges' `out_of_scope` call. The
   planned post-hoc v15 filter (adding biblical peoples and treating generic actors as
   biblical) is **not built**.
5. **Several `STATE.md` cells describe old artifacts, not v14.** The Ketubot, Kiddushin and
   Gittin cells come from v10/v11 runs. The Yevamot cell (88.9%) is the v11 artifact; v14
   scores 95 and 93 of 100. `board.py` also lists `superseded_by_rule.json` as "shape not
   recognised". `board.py --check` passing means STATE.md matches what the generator
   computed, not that it is true.
6. **Say which segment is number one.** Our labels count from 0; Sefaria counts from 1. Every
   email and page must state the base, or quote the Hebrew opening.
7. **Any edit to `STORY_RULES.md` moves the judge prompt's sha.** New judge runs then go red
   at G6 until Simon re-pins. Outputs judged under an earlier sha stay green.
8. **Run outputs land under `results/v11/<tractate>/` even when v14 ran them.**
   `run_meta.detector_module` is what says which detector ran; trust that, not the path.
9. **The public hub page drifts.** Its numbers were typed by hand and dated October 2026, and
   the `AS_OF` constant is the only guard. Whoever moves a headline number updates it or its
   date.
10. **Verdicts that no ruler reads:** Gittin axes 2026-09-02 (25) and Ketubot 2026-01-08 (25).
    Simon's 60 are excluded on purpose, being the owner's grades and not the expert's
    (`STATE.md`).

## 8. Next

**Deferred by Simon (not started):**
- Background notes for the remaining tractates. Only Ketubot, Kiddushin, Gittin and Yevamot
  have drafted notes (`site/data/notes/`), and none is approved yet
  ([viewer plan §4](docs/technical/septimus-viewer-plan.md)).
- A "why it matters" enrichment pilot. No work item exists yet.

**Decisions for Simon:** Option 0 and Rule A (§4); whether to run the narrate hybrid on the
pool; whether to build the v15 biblical filter.

**Work items** ([`work/`](work/); check `python3 scripts/board.py lanes` before running two
at once):
- **Open, Septimus:** `2026-11-08-septimus-signup`, `2026-10-12-septimus-story-viewer`.
- **Open, catalogue:** `2026-09-28-consensus-2-yevamot-round`,
  `2026-10-02-jeff-feature-questions`, `2026-10-09-judge-answer-categories`,
  `2026-09-28-twin-pass-r-c5-wording` (its `awaiting:` is stale, since Jeff answered),
  `2026-09-07-habitual-is-narrative-evidence`, `2026-09-07-formulaic-cluster-splitting`.
- **Stale from 2026-08-30/09-03:** the per-tractate triage, detection, classification,
  review-UI and expert-round items for Eruvin, Gittin and Yevamot. The Shas run has
  overtaken much of what they describe. Re-read each before running it; close or rewrite.

## 9. Where things live

| file | its one job |
|---|---|
| [`STATE.md`](STATE.md) | generated instrument panel. Never edit; run `python3 scripts/board.py` |
| `STATUS.md` | this file: judgment and hazards, rewritten each session |
| [`FRAMEWORK.md`](FRAMEWORK.md) | the six capabilities, how each is measured, the gates and why |
| [`docs/STORY_RULES.md`](docs/STORY_RULES.md) | the rule register, in Jeff's words. Read it before touching a prompt, boundary or dataset |
| [`comms/JEFF.md`](comms/JEFF.md) | open questions (slugs), corrections owed, the sent log |
| [`docs/technical/septimus-story-filter.md`](docs/technical/septimus-story-filter.md) | what reaches the family site, and why |
| `results/shas_run/septimus_site_decisions.json` | every per-passage site decision: who made it, when, and why |
| `site/data/` | the shipped site: one file per tractate, plus `story_ids.json` and `redirects.json` |
| [`docs/findings/`](docs/findings/) | dated findings. Corrected by a new dated finding, never edited silently |
| [`docs/capabilities/`](docs/capabilities/) | per capability: what was tried, what was reverted and why. Read before opening work |
| [`work/`](work/) | one self-contained item per task; finished items go to `work/done/`, never deleted |
| `FOR_SIMON.md` | the plain-English story of the project |
