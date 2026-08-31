# Approach Review: Is This the Right Way to Find Talmud Stories, and How Does It Scale?

**Date:** 2026-07-06
**Scope:** Strategic review of the detection approach after Wave 4 (v10), plus a
concrete path to covering the entire Babylonian Talmud.
**Inputs:** Pipeline architecture audit (src/, docs/technical/), evaluation
history audit (scripts/evaluate_golden.py, all wave results, 15 lessons,
error taxonomy, overfitting research), and an external check of Sefaria's
digitized *Ein Yaakov*.

---

> ## ⚠️ UPDATE 2026-08-28 — corrections from Jeff's actual answers
>
> This review was written before Jeff responded. His 2026-07-06 reply
> ([`validation/feedback/jeff_2026-07-06_feedback_ledger.md`](../../validation/feedback/jeff_2026-07-06_feedback_ledger.md),
> from [`jeff comms/Simon Brief Questions.docx`](../../jeff%20comms/Simon%20Brief%20Questions.docx))
> confirms the thesis but overturns three specifics. Where this document and the
> points below disagree, **the points below win.**
>
> 1. **Recall probe (supersedes §4.1):** don't ask Jeff to cold-read 10 random
>    pages — he *already* made detector-blind story lists ~20 years ago for
>    several masekhtot. One is already in the repo:
>    [`validation/feedback/Kiddushin missesd stories.docx`](../../validation/feedback/Kiddushin%20missesd%20stories.docx)
>    (Kiddushin misses: 33a, 45a, 53a, 71a… with Hebrew + confidence). Use his
>    lists as independent ground truth; ask him for the rest.
> 2. **Ein Yaakov (supersedes §4.2):** Jeff is skeptical and correct. It is
>    *all* aggada (needs filtering + a human judgment on every gap) and, crucially,
>    **omits halakhic stories** — which this database explicitly includes. Demote
>    from "highest-leverage recall probe" to "cheap optional aggadic-only
>    cross-check." His own lists are the better asset.
> 3. **Endgame + validation (supersedes §5.2 / §5.4):** not a static published
>    corpus but a **living, crowd-sourced, editable database** — scholars flag
>    not-a-story / borderline / suggest-additions as they encounter stories; Jeff
>    (or a small editor group) finalizes; **contested/borderline cases are kept
>    and flagged**, not silently resolved. Add three per-story columns: **notes,
>    scholarship references, Yerushalmi parallels.** Auto-accept-plus-sample still
>    applies to the bulk; distributed reviewers take the filtered borderline pile.
>
> 4. **RECALL IS NOW MEASURED (2026-08-28) — supersedes §3.1 and §4.1.** Jeff's
>    Ketubot list (`jeff comms/b.ketubot (1).doc`, created 2005, 149 stories) is a
>    genuinely detector-blind ground truth. **v10 recall = 143/149 = 96.0%**;
>    golden = 96.6%. The "plausibly 80–85%" guess in §3.1 was pessimistic, and the
>    "most important unmeasured number in the project" is now measured, for $0 in
>    expert time. The 6 misses cluster into halakhic-story-plus-ruling (20a, 77a),
>    lexicon-gap openers (67b `אמרו עליו`, 82b `בראשונה`), and narrative-inside-speech
>    (72b, 53a). → [`recall_measurement_ketubot_2026-08-28.md`](2026-08-28-recall-measurement-ketubot.md)
>    Caveat: Ketubot is our most-tuned tractate, so this is not a generalization
>    estimate. Ask Jeff which other tractates he has lists for.
> 5. **Wave 4's spans are reverted (2026-08-28).** 55% of emitted cuts severed a
>    word; the mechanism had zero observed successes. `results/v10/wave4_notrim/`
>    is the current honest output. → [`../v10/wave4_span_failure_audit_2026-08-28.md`](2026-08-28-wave4-span-failure-audit.md)
>
> **Scope fact threaded through everything:** the target is **all stories,
> including halakhic ones** — not aggadic only. Jeff also gave the sharp
> story-definition criterion the detector was missing:
> [`docs/findings/2026-07-06-jeff-story-definition-criteria.md`](2026-07-06-jeff-story-definition-criteria.md)
> (hypothetical→not-a-story / actual→story; speech-acts need action; emotions
> count). And Wave 4's boundary mechanism proved broken in his review, replaced
> by [`tasks/PLAN_wave5.md`](../../tasks/PLAN_wave5.md).

---

## 1. Verdict in one paragraph

The core approach — LLM classification with expert-in-the-loop validation — is
right, and the engineering discipline around it (immutable eval harness,
frozen detector versions, same-day baselines, a lessons log that honestly
records failures) is genuinely better than most research code. But the project
has reached the end of what this *shape* of the system can deliver. Three
structural facts now dominate everything else: **(a)** measured recall is
circular (the golden datasets only contain stories the detector itself found,
so the ~0.92 composite score cannot see what the detector systematically
misses); **(b)** the single-expert validation loop costs 2–6 weeks of calendar
time per tractate, which at 37 tractates is a 3–5 year serial bottleneck,
while compute costs ~$0.30/tractate and is irrelevant; **(c)** detection
accuracy has plateaued — every gain since Wave 1 came from post-processors and
corrections to the golden data, not from a smarter detector. Scaling to the
whole Bavli is therefore not a detector problem. It is a **validation-economics
problem** plus a **recall-measurement problem**, and the plan should be
restructured around those two.

---

## 2. What the project gets right (keep all of this)

1. **The golden datasets are the real asset.** 267 expert-validated stories
   (182 Ketubot + 85 Kiddushin) with boundaries, classifications, and
   Jeff Rubenstein's notes is a scholarly resource independent of any
   detector. Whatever detection technology exists in five years, this data
   feeds it. Keep investing here.

2. **The evaluation discipline is correct.** An immutable harness
   (`scripts/evaluate_golden.py`), versioned detectors that are never edited
   in place, same-day baseline regeneration (Lesson 11), and score-neutrality
   proofs before shipping — this is how real ML teams avoid fooling
   themselves.

3. **Wave 4's direction was the right lesson, generalized.** Replacing the
   regex boundary-trimmer with LLM judgment (because surface markers like
   אלא are framing 30–50% of the time and content 50–70% of the time) is a
   specific instance of the general rule: *in this corpus, almost no surface
   pattern is reliable; semantic judgment wins.* The remaining lexical
   post-processors (start-snap 4h, end-trim 4i, biblical-actor filter 4j,
   the hardcoded introducer lists) should be expected to fail the same way
   the regex did, and should eventually be retired or converted to
   *features* consumed by a learned model rather than *rules* that act
   unilaterally.

4. **Costs are understood and tiny.** ~$0.30–0.60 and ~15–20 minutes per
   100 pages. This is the single most liberating fact in the project (see §5).

---

## 3. The three structural problems

### 3.1 Measured recall is circular — the score can't see what's missing

How the golden datasets were built: the detector proposed stories; Jeff
corrected classifications and boundaries. Jeff never performed an independent,
exhaustive read of a tractate. Stories he happened to notice were missing
(5 on Kiddushin: 45a, 53a, 71a, 33a, 81b) are recorded in
`known_missing_stories` — but **excluded from scoring**.

Consequence: "recall 0.94" means *recall against the universe of stories the
detector already found once*. True recall against the text is unknown —
plausibly 80–85%, and the misses are not random: they concentrate in exactly
the categories the detector is structurally weak on (baraita-embedded
narratives, second stories on multi-story pages, stories whose openers don't
match the canonical introducer lexicon). Lesson 14 documented the perverse
side-effect: when the detector *improves* and finds a real story the golden
lacks, the score goes *down*.

There is also a second, quieter recall ceiling: **Stage 1 triage skips
~60–66% of pages** and a skipped page is unrecoverable unless it happens to
contain a hardcoded introducer string. Triage has never been independently
scored against ground truth. One documented false negative exists
(Ketubot 51a, triaged entirely as DELIBERATION), and nobody knows how many
others there are, because nothing measures it.

**This is the most important unmeasured number in the project.** Everything
else — publication claims, whether the FP classifier is worth building,
whether triage thresholds are safe — depends on it.

### 3.2 The expert loop is the bottleneck, by four orders of magnitude

| Resource | Per tractate | Whole Bavli (37 tractates, 2,711 dapim) |
|---|---|---|
| LLM compute | ~$0.30–0.60, ~30 min | **~$10–25, ~2 days of runs** |
| Jeff's review | 2–6 weeks calendar | **~3–5 years, serially** |

Ketubot took four review rounds over ~6 weeks. Kiddushin's seven new Wave 3
candidates have been awaiting verdicts since 2026-05-26. The constraint is not
Jeff's willingness — it's that the workflow asks one senior scholar to
hand-verdict every detected story. No detector improvement changes this
arithmetic. Only changing the *validation design* does (§5.2).

### 3.3 Detection accuracy has genuinely plateaued

The score trajectory tells one story consistently:

| Wave | Ketubot composite | What moved it |
|---|---|---|
| v7 fresh (2026-05-18) | 0.8576 | — |
| Wave 1 (v8) | 0.9164 | Cross-page **merge post-processors** (+0.06, nearly all of it Merge F1: 0.59→0.88) |
| Wave 2 (v8) | 0.9162 | ~nothing (biblical filter helped Kiddushin +0.046) |
| Wave 3 (v9) | 0.9170 | ~nothing net |
| Wave 4 (v10) | 0.9171 | score-neutral by design |

Lesson 5 (prompt edits regress), Lesson 8 (specific examples cause
memorization), and the overfitting research all point at the same underlying
fact: the remaining ~26 Ketubot false positives are *legal discussions with
narrative framing*, where 50% of FPs contain physical actions and 68% of true
stories do — the distinguishing feature is **structural** (does the narrative
serve the legal debate, or vice versa), which no additional prompt rule
captures. The error taxonomy confirms ~75% of flagged error instances remain
unsolved, dominated by merge misses (32%), legal FPs (21%), and boundary
under-extension (19%).

**Implication:** stop expecting composite gains from prompt engineering. The
remaining headroom lives in (a) learned post-processing, (b) ensembling,
(c) fine-tuning, and (d) fixing the merge architecture — roughly in that
order of effort.

---

## 4. How to identify stories more effectively (ranked)

### 4.1 First, measure true recall (1 day of Jeff's time, highest value per hour)

> **Superseded by the 2026-08-28 update banner (point 1):** Jeff already has
> detector-blind lists; use them instead of commissioning a fresh cold-read.

Pick **10 random dapim** from the already-validated tractates. Jeff (or a
qualified grad student) reads them cold and lists *every* story, without
seeing detector output. Compare against the detector. This converts "recall
is probably 80-something" into a real number with a confidence interval, and
it tells you whether the misses are triage-caused (page never processed) or
Stage-2-caused (page processed, story not seen). Ten dapim ≈ one day of
expert time — the cheapest decisive experiment available to this project.

### 4.2 Build the Ein Yaakov reference layer (the highest-leverage new idea)

> **Superseded by the 2026-08-28 update banner (point 2):** Jeff's reply demotes
> this — Ein Yaakov omits halakhic stories and needs filtering, so it is a cheap
> optional aggadic-only cross-check, not the primary recall probe.

*Ein Yaakov* (Jacob ibn Habib, ~1516) is a human-curated compilation of
essentially **all the aggadic (non-legal) material in the Bavli** — a
500-year-old answer key for "where is the narrative material?" covering every
tractate. Verified on 2026-07-06: Sefaria hosts it fully digitized,
structured per-tractate (including Ketubbot and Kiddushin), **but its passages
are not ref-linked to Bavli dapim** — the 341 links on Ketubot 62b contain
zero Ein Yaakov entries. The alignment must be built, and it is tractable:
Ein Yaakov quotes the Talmud essentially verbatim, so n-gram / fuzzy matching
of its Hebrew against the same Vilna text the project already caches will map
each Ein Yaakov paragraph to a daf + segment range. A few days of engineering,
no expert time, near-zero LLM cost.

What the alignment buys, corpus-wide:

1. **A recall probe for the whole Bavli.** Any detector-missed passage that
   Ein Yaakov includes is a candidate false negative — automatically, on all
   2,711 dapim, without Jeff. (Caveat: aggadah ⊃ stories. Ein Yaakov also
   contains homiletics, theology, and exegesis that are *not* narratives by
   Jeff's criteria — so it flags candidates for triage, not confirmed misses.
   The reverse containment is the useful one: nearly every *story* is aggadah,
   so detector-found ∖ Ein Yaakov is rare and detector-missed ∩ Ein Yaakov is
   a high-yield review queue.)
2. **A triage prior.** A page with substantial Ein Yaakov coverage should
   never be skipped by Stage 1 — this directly patches the unmeasured triage
   recall ceiling (§3.1) with a principled, human-curated signal instead of a
   hardcoded introducer list.
3. **A validation router.** Detector ∩ Ein Yaakov = high confidence;
   disagreements in either direction = the queue worth expert attention (§5.2).

### 4.3 Ship the post-detection FP classifier (already planned as Track 1 — endorsed)

Train a small model (logistic regression / LightGBM) on Jeff's NOT_A_STORY
labels, using the features the detector already emits (criteria_met_count,
disqualifiers, actor type, segment count) plus Ein Yaakov coverage once §4.2
exists. Lesson 7's reasoning is correct: a post-filter can only demote, so it
can never create new missed stories, and unlike prompt rules it produces a
calibrated score — which §5.2 needs for routing. Validate with
leave-one-tractate-out so the claim "it generalizes" is tested, not assumed.

### 4.4 Cheap ensemble / self-consistency for the judgment-call cases

The residual FPs are judgment calls; judgment calls benefit from votes.
Two options, both trivially affordable at ~$0.30/tractate baseline cost:

- **Self-consistency:** run Stage 2 at temperature ~0.7, k=3, take the
  majority classification. Disagreement between samples *is itself the
  signal* — it identifies exactly the borderline stories a human should see.
- **Cross-model check:** a second model (e.g., a Claude or a Gemini Pro pass)
  re-verdicts only detected stories (~$1/tractate). Agreement → auto-accept;
  disagreement → expert queue. This also breaks the single-vendor dependency
  (every stage currently rides one Gemini model with no retries and no
  fallback — a real operational risk for a multi-year project).

### 4.5 Fix the merge architecture, not the merge rules

Merge F1 is the weakest component (0.67 Kiddushin / 0.86 Ketubot) and the
error taxonomy's largest bucket (32%). The current fix pattern — ever more
intricate case logic (5 cases + overrides + gap-awareness) bolted onto a
page-at-a-time detector — is the regex story again: patching a structural
problem with rules. The structural fix is **sliding-window detection**
(overlapping windows of ~1.5 pages so no story ever straddles a hard
boundary), estimated at +25% cost in the overfitting research — i.e., ~$0.08
per tractate. Do this once, at the v11 fork, before mass rollout — not after
3,000 stories have been detected with the old geometry.

### 4.6 Fine-tuning: defer, but collect toward it

267 positive examples + a growing NOT_A_STORY set is near the threshold where
fine-tuning (Gemini Flash tuning or an open Hebrew model) beats few-shot
prompting, and it would eliminate the few-shot contamination anxiety
entirely. But it locks in whatever the labels currently are — so do it after
the recall probe (§4.1) and after 1–2 more tractates of golden data, with
leave-one-tractate-out evaluation. Related low-cost option worth one
experiment: Dicta's rabbinic-Hebrew BERT models (BEREL family) as a local
Stage-1 triage replacement — near-zero marginal cost at corpus scale and
removes the API dependency from the highest-volume stage.

---

## 5. Scaling to the entire Bavli

### 5.1 The size of the task

- **Corpus:** 37 tractates, 2,711 dapim. Validated so far: 194 dapim (~7%).
- **Expected stories:** Ketubot+Kiddushin density is 1.38/daf → naive
  extrapolation ≈ **3,700 stories**, realistically **2,500–4,500** because
  density varies enormously by seder (aggadah-rich Berakhot, Ta'anit,
  Megillah, Gittin ch. 5, Sanhedrin ch. 11 vs. nearly story-free stretches of
  Kodashim like Zevachim/Menachot).
- **Compute:** ~$10–25 and a weekend of runs for the whole corpus. Not a factor.
- **Expert time at current workflow:** 37 × (2–6 weeks) — not viable. This is
  the entire scaling problem.

### 5.2 Change the validation economics: from "Jeff reads everything" to "Jeff reads what matters"

> **Refined by the 2026-08-28 update banner (point 3):** the auto-accept-plus-
> sample logic holds, but Jeff wants the human layer to be **crowd-sourced** (open
> editable interface, gradual, borderline cases kept and flagged), not a fixed
> panel. Read the banner + ledger for his exact model.

The publishable end-product does not require every story hand-verdicted. It
requires **a corpus with measured, stated error rates** — which is how every
large annotated corpus in computational linguistics is actually built. Three
tiers:

| Tier | Criteria | Human treatment |
|---|---|---|
| **Auto-accept** | Detector + FP-classifier confident + ensemble agrees + Ein Yaakov concurs | Random 5–10% sample audited to *measure* the error rate; publish with confidence intervals |
| **Expert queue** | Any disagreement: ensemble split, classifier borderline, Ein Yaakov mismatch (either direction) | Jeff (and/or second annotators) verdict these — expert hours spent only where machines disagree |
| **Auto-reject** | Skipped by triage AND no Ein Yaakov coverage AND no introducer | Sample-audited at low rate to bound the miss rate |

On current agreement rates this plausibly cuts per-tractate expert load from
"every story" (~100–180) to a few dozen disagreements plus a fixed audit
sample — turning 3–5 years of serial review into roughly a year of part-time
review, without giving up statistical honesty. Two additional levers:

- **Second annotators.** Recruit 1–2 qualified grad students; calibrate them
  against Jeff on ~30 already-verdicted stories (measure inter-annotator
  agreement — this number is independently interesting for the paper, since
  "what counts as a story" is itself a scholarly question). Jeff's role
  shifts from primary annotator to adjudicator, which is a better use of the
  scarcest resource and standard practice for corpus construction.
- **Tractate ordering.** Do Bava Metzia next (already planned — good: tests
  generalization on a golden set not seeded by this detector's output), then
  **Ta'anit or Megillah** (short + aggadah-dense: many stories per unit of
  expert time, and a genre stress-test), then one Kodashim tractate (sparse:
  tests the false-positive rate where almost nothing should be found). Those
  three gates cover the genre spectrum before committing to the remaining ~30.

### 5.3 Engineering hardening before a corpus-scale run

The pipeline audit found gaps that don't matter at 2 tractates and will hurt
at 37 (several also violate the project's own code standards):

1. **Resumable orchestrator with a manifest.** One driver that walks all
   tractates with per-page status (fetched / triaged / detected /
   post-processed), checkpointing, and resume. Currently an interrupted run
   re-executes every LLM call from scratch.
2. **LLM response cache** keyed on (model, prompt-hash) — makes re-runs free
   and interrupted runs cheap. A SQLite file is sufficient.
3. **Retries with backoff.** There is currently *no retry logic*; one
   transient API error silently costs a page. At 2,711 dapim, transient
   errors are a statistical certainty.
4. **Real logging.** Errors to `project.log` with source and record counts
   (the global code standard) — today most stages print to stdout only, so a
   mid-run crash on page 1,400 is undiagnosable.
5. **Pin versions of everything external.** The Gemini model string (the
   default fallback `gemini-2.0-flash` will be deprecated mid-project;
   record the exact model per run in output metadata), and the Sefaria text
   version. The whole result set is keyed to Sefaria's segment indices — if
   Sefaria ever re-segments a tractate, every boundary silently invalidates.
   Store a text anchor (first/last ~40 chars of Hebrew) alongside each
   boundary so results are re-alignable and corruption is detectable.
6. **Score triage independently, once.** Before trusting it on 2,500 unseen
   dapim, run Stage 2 on a sample of ~30 triage-skipped pages and count the
   stories found. That either validates the 60% cost saving or reveals a
   recall hole — at a cost of pennies.

### 5.4 What the output should be

> **Superseded by the 2026-08-28 update banner (point 3):** the output is a
> **living, crowd-sourced, editable database** (borderline cases kept + columns
> for notes / scholarship references / Yerushalmi parallels), not a one-time
> static published corpus.

Name the end-product now, because it disciplines every choice above: a
published, citable **"Bavli Narrative Corpus"** — every story in the
Babylonian Talmud with boundaries, text spans, classifications, provenance
(auto vs. expert-verdicted), and measured precision/recall with confidence
intervals; Jeff as co-author; the golden tractates as the fully-validated
core and the rest tiered per §5.2. That is a real contribution to both
digital humanities and Talmud scholarship, and it is reachable in roughly a
year under the revised validation design.

---

## 6. Recommended sequence

| # | Action | Cost | Depends on |
|---|---|---|---|
| 0 | Close Wave 4: send Jeff the pending email (UIs verified 2026-07-06) | done, awaiting send | — |
| 1 | **True-recall probe**: 10 random dapim, detector-blind exhaustive read | ~1 day expert | Jeff/student availability |
| 2 | **Ein Yaakov alignment layer**: fuzzy-match its Hebrew to daf+segments; wire in as triage prior + recall probe | ~2–4 days eng, ~$0 | — |
| 3 | **Triage audit**: Stage 2 on ~30 triage-skipped pages | pennies | — |
| 4 | **FP classifier (Track 1)** with leave-one-tractate-out validation | ~2–3 days eng | golden data (have it) |
| 5 | **v11 fork**: sliding-window detection (kills the merge bucket) + retries + response cache + manifest orchestrator + version pinning | ~1 week eng | 1–3 inform design |
| 6 | **Generalization gates**: Bava Metzia, then Ta'anit/Megillah, then one Kodashim tractate — under the tiered validation design (§5.2), with second annotators calibrated | weeks, parallelizable | 4, 5 |
| 7 | **Corpus run** on remaining tractates + sampled audits + corpus paper | ~$20 + audit time | 6 |
| — | Defer: fine-tuning (until after 1 and 6), Yerushalmi (different dialect/structure — separate project) | | |

The single most important reframe: **the detector is good enough to start
scaling now; the validation design is not.** Items 1–3 cost days and
de-risk everything; item 5 is the one detector re-architecture that is
clearly worth doing before, not after, the corpus run.

---

*Sources: pipeline audit of `src/story_detector_v10.py`, `src/event_triage.py`,
`docs/technical/HOW_IT_WORKS.md`, `docs/technical/VERSION_HISTORY.md`;
evaluation audit of `scripts/evaluate_golden.py`, `tasks/lessons.md` (15
lessons), `docs/findings/2026-03-17-error-taxonomy.md`,
`docs/findings/2026-03-25-overfitting-and-generalization-research.md`, wave
writeups in `docs/golden/v8/` and `docs/golden/v9/`; golden provenance from
`results/canonical/*.json`; Ein Yaakov availability verified against the
Sefaria API 2026-07-06 (digitized per-tractate; no existing daf-level links —
alignment must be built).*
