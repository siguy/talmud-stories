# Lessons Learned

Ongoing log of mistakes, surprises, and things worth remembering across sessions.

---

## 2026-03-25: Golden Dataset + Detector Experiments

### Lesson 1: Never split feedback processing into "auto" and "defer" without scheduling the "defer" pile

**What happened:** Across three prior feedback rounds, we categorized Jeff's corrections as "auto-apply" (classification changes) and "needs review" (boundary/merge changes). We applied the auto ones immediately but never came back to the needs-review pile. Jeff noticed — 10 of his 53 corrections in the canonical review were things he'd already told us to fix.

**Rule:** When splitting work into "now" and "later" buckets, the "later" bucket must go into a task list with a specific due date. If there's no mechanism to return to deferred work, it doesn't get done.

### Lesson 2: Don't add feedback from reviewed pages as few-shot examples for those same pages

**What happened:** We expanded the detector's few-shot example bank from 128 to 282 entries by adding Jeff's canonical review corrections. The new examples were mostly from pages 2-60. When we re-ran the detector, it massively over-rejected stories on pages 2-60 (72 → 52 stories) while pages 61-112 barely changed (110 → 109). Classic train/test contamination.

**Rule:** Few-shot examples must come from a different dataset than what you're evaluating on. If Jeff reviews Ketubot, use those examples when detecting stories in Bava Metzia, not when re-running on Ketubot.

### Lesson 3: The canonical review verdict format is different from prior rounds

**What happened:** The canonical review uses `correct/incorrect/approve/adjust` verdicts on the *already-corrected* data, while prior rounds used `correct/incorrect/confirm_remove/reject_remove` on the *base* data. We initially planned to add it as a 4th entry in the timestamp-based feedback system, but realized this would cause the canonical review's "correct" (meaning "the correction was right") to override the prior round's "incorrect" (which triggered the correction), effectively undoing the correction.

**Rule:** When combining feedback from different review rounds, understand what each verdict means in context. A "correct" on corrected data is not the same as a "correct" on base data. We solved this by processing the canonical review as a separate post-processing step.

### Lesson 4: Cost estimates should be verified before building infrastructure

**What happened:** The brainstorm estimated $2/run for detector experiments ($100 for 50 runs). Actual cost: $0.30/run (Gemini Flash, not Claude). We built autoresearch infrastructure (program.md, run_experiment.py) for a 50-experiment loop that turned out to be both cheap enough to run impulsively and also unnecessary — the error taxonomy already told us what was wrong.

**Rule:** Before building experiment infrastructure, verify: (a) the actual cost per experiment, (b) whether you already know what to try. If you know the answer, run 2-3 targeted experiments, not 50 blind ones.

### Lesson 5: Prompt engineering has a ceiling

**What happened:** We tried two levels of prompt modification — aggressive (5 new disqualifiers) and light (just confidence calibration). The aggressive version caused a catastrophic regression (0.93 → 0.57). The light version still regressed (0.93 → 0.89). The remaining 26 false positives are genuine judgment calls that can't be resolved by telling the model "legal discussions aren't stories" — it already knows that. The ambiguity is in passages that have BOTH narrative and legal elements.

**Rule:** When your baseline is already 0.93, the remaining errors are the hard cases. Prompt engineering works for systematic, clear-cut errors. It doesn't work for judgment calls that require domain expertise. The next step is either fine-tuning, a different model, or acceptance.

### Lesson 6: Run the full evaluation before drawing conclusions

**What happened:** The first experiment evaluation only covered pages 2-60. The composite score was 0.44, which looked catastrophic. But much of that was because the evaluator penalizes for every golden story not in the detected results — and all 61-112 stories were "missing" since we hadn't run that range yet.

**Rule:** Always run the full evaluation pipeline before interpreting results. Partial evaluations are misleading when the scoring function considers all pages.

---

### Lesson 7: Post-processing classifiers beat prompt modifications for precision improvements

**What we found:** Research shows that adding a lightweight second-stage classifier (logistic regression or LightGBM) trained on false positive features is more effective than modifying prompts when you need to reduce false positives without hurting recall. The ACL 2024 "LlmCorr" paper demonstrates this pattern. A post-processing classifier can only affect passages the detector already found — it can never cause new false negatives. Prompt modifications affect everything and can cause cascading regressions.

**Rule:** When trying to improve precision (reduce false positives), don't modify the detection prompt. Build a separate filter that runs AFTER detection. It's safer, more interpretable, and generalizes better.

### Lesson 8: Abstract patterns generalize; specific examples memorize

**What we found:** Research on "Synthetic Prompting" (Wan et al., 2023) shows that abstract pattern descriptions outperform specific examples in few-shot prompts. Our error taxonomy already has the abstract patterns ("dialogue is not events," "narrative settings don't make stories"). The mistake was adding those patterns alongside the specific passages. The specific passages caused memorization; the abstract patterns alone would have been safer.

**Rule:** When converting expert feedback into prompt guidance, use the expert's reasoning patterns, not their specific examples. "A passage where all activity is verbal acts is NOT a story" > "Ketubot 7a_1-1 is NOT a story."

### Lesson 9: Targeted tests on hand-picked examples don't predict production performance

**What happened:** A boundary check that correctly found 2/3 cross-page stories on hand-picked boundaries found 28 false positives when run on all ~100 boundaries. The LLM is too generous about what counts as a story at page breaks — the same false positive problem as everywhere else. Tuning the triage filter either let everything through or blocked everything.

**Rule:** When testing a new detection approach, always run on the FULL dataset, not just known examples. A technique that works on 3 hand-picked cases tells you the concept is sound but says nothing about precision at scale. Budget the full evaluation into the test — don't iterate on filters in a trial-and-error loop.

---

## 2026-03-27: Kiddushin Run

### Lesson 10: Narrow questions beat open-ended detection for precision

**What happened:** We tried two approaches for catching cross-page stories the merge passes missed. The first (sliding-window boundary check) asked "is there a story at this page boundary?" — an open-ended detection question. It found 28 false positives across ~100 boundaries because the LLM is too generous about what counts as a story. The second (Stage 4f continuation check) asked "does THIS specific detected story continue on the next page?" — a yes/no question about a known story. It caught 3 genuine cross-page stories with 0 false positives on Kiddushin.

**Rule:** When you need to extend an existing detection (not find new things), frame the question as narrowly as possible. Give the LLM the specific thing to check against, not an open search. "Does story X continue?" is fundamentally different from "Find any story at this boundary" — the first constrains the answer space, the second invites false positives.

---

*Add new lessons below this line. Date each entry.*

## Lesson 11 — LLM nondeterminism breaks historical baselines (2026-05-18)

**Context:** Wave 1 Ketubot regression check. The "0.9308 composite" baseline
(`docs/golden/baseline_ketubot.json`) was generated months ago from a specific
Gemini Flash run. Today, running the same v7 detector + same triage cache +
same prompts yields composite 0.858 — a 7-point swing from LLM drift alone.

**Rule:** When testing a detector change against a historical score, generate
a FRESH baseline from the unchanged code on the same day. Compare new-fresh
against old-fresh, not against the frozen JSON. The frozen JSON is only valid
as a sanity floor for the GOLDEN dataset itself, not for detector evaluation.

**Why:** The first Wave 1 check looked like a regression (-0.014 composite vs
the frozen 0.93), but apples-to-apples (v7 fresh vs v8 fresh) showed +0.06.
Trusting the frozen baseline would have killed a real improvement.

**How to apply:** Any "did this regress?" test must run BOTH versions today,
in the same window, before comparing. Cache the fresh baseline only for the
duration of the session.

## Lesson 12 — Most boundary feedback is text-internal, not segment-level (2026-05-24)

**Context:** Wave 2 implemented Issue #3 (start-boundary snap) and Issue #4
(end-boundary trim) as deterministic segment-level post-processors. On audit
of all 16 boundary cases Jeff flagged on Kiddushin: every single one is
text-internal — the introducer Jeff wants the story to start at, or the
commentary he wants trimmed, sits INSIDE the start/end segment, not in a
separate adjacent segment. Segment-level snap/trim cannot reach these.

**Rule:** Before designing a mechanical post-processor, audit the actual
evidence at the granularity the post-processor operates on. If feedback is
"the story should start with X" and X is in the SAME segment as the detector's
start, no segment-level fix will help — you need sub-segment text editing or
a re-segmentation pass.

**Why:** Wave 2's snap-forward fired 0 times and trim fired 0 times because
of this mismatch. The only post-processor that landed real wins (3 biblical
demotions + 3 extend-back snaps) was the biblical-actor filter and the
"introducer in the segment BEFORE detector's start" extension — neither of
which were in Jeff's flagged-case list. The flagged cases will require Wave 3
text-level changes.

**How to apply:** When the user reports "the story should start at X" with X
quoted in Hebrew, immediately check whether X is in the same segment the
detector picked. If yes, route to text-level work; if no, segment-level
post-processing can address it.

## Lesson 13 — Tight numeric gates penalize correct quality improvements (2026-05-24)

**Context:** Wave 2 ships 3 rabbinically correct start-boundary snaps
(ההוא ד / ההיא openers). Two land on Ketubot stories Jeff has not yet
reviewed. Because the unchanged Ketubot golden inherits the pre-snap
boundaries from v7, the snaps mechanically lower IoU by 1 segment on each
story → composite drops 0.0002 below Wave 1. Strict "Wave 2 ≥ Wave 1"
gate fails by this margin, even though each snap is unambiguously correct
by human reading.

**Rule:** A composite-score gate measures agreement with the current
golden, not absolute quality. When a mechanical change disagrees with
golden on a small number of cases the expert hasn't yet ruled on, the
right response is to ship + flag for expert review, not to disable the
change to pass the gate.

**Why:** Disabling the snap to satisfy the gate would throw away verified
quality wins to chase a tenth of a percent of agreement with a golden that
hasn't seen the changed cases. The cost of asking Jeff later is small;
the cost of regressing real quality is permanent.

**How to apply:** When a strict score gate fails by noise-scale margins,
inspect the disagreement cases by hand. If the change is defensible per
expert convention, ship + document + flag for next review round. If not,
tighten the change.

## Lesson 14 — When the detector overtakes the golden, FPs are a recall win in disguise (2026-05-25)

**Context:** Wave 3 added iterative Stage 2 + embedded-story few-shots.
On Ketubot this recovered 7 stories the golden had as FNs (recall
+0.044). On Kiddushin the same changes surfaced 7 NEW story candidates
v8 had not detected — 5 of which scored as false positives because the
Kiddushin golden was built from v8 output + Jeff's prior reviews.
Inspecting the 7 by hand: most are real rabbinic narratives, and one is
the EXACT story Jeff flagged as missed in his 2026-04-23 review
(Kiddushin 33a seg 5, Rabbi Hiyya in bathhouse). The gate read this as
a regression (-0.0103 composite).

**Rule:** When a detector improvement causes the FP count to rise but
the new "FPs" overlap previously-flagged-as-missed cases or look like
real stories under inspection, that's the detector overtaking the
golden — not a quality regression. Treat as Lesson 13 (ship + flag).

**Why:** A golden built from an older detector's output records that
detector's coverage as the ceiling. A better detector finds more, and
the metric punishes it. Re-disabling the improvement to chase
agreement with a stale frozen target loses real quality without
gaining anything.

**How to apply:** Before bisecting prompt changes to "fix" an FP
regression, dump the new-only detections and check by hand against the
expert's prior missed-stories list. If ≥1 new FP corresponds to a
known missed case, the gate result is misleading — ship, flag the new
detections for the next review pass, and expect the golden to update.

## Lesson 15 — Regex text-internal boundary editing cannot generalize (2026-06-03)

**Context:** Wave 3 Item 4 (`edit_text_internal_boundaries`) used a
hand-built regex set to identify story-vs-framing inside the first/last
segment — markers like ההוא ד / ההיא at the start, אלא / rabbi-name
patterns at the end. Audit was 10/17 pass on Jeff's flagged cases.
Jeff's 2026-06-03 reply on the shipped Item 4: it worked on 5 of the
canonical ההוא/ההיא openers, but on 7 OTHER stories the same kinds of
markers (אלא, rabbi names) WERE the story content — and the regex
chopped them out. Jeff's diagnosis verbatim: *"crude criteria, such as
the word אלא or a rabbi's name automatically signalling the story's
end."* Net change in golden agreement: ~0 (recovered cases cancel new
over-trims).

**Rule:** Stop building deterministic regex post-processors for
text-internal semantic decisions. Surface markers (אלא, rabbi names,
תניא, מעשה ב, ההוא) are diagnostic of structure 30-50% of the time and
of story content the other 50-70%. Only a model that reads the
surrounding meaning can tell them apart.

**Why:** Our audit looked at 17 hand-picked cases drawn from Jeff's
prior boundary corrections — which biased the sample toward cases the
regex was implicitly built to fit. The 7 new failures came from
ordinary stories outside that sample, where the same markers play a
content role. Audit precision on the hand-picked sample doesn't
predict precision in the wild — same pattern as Lesson 9.

**How to apply:** When sub-segment text decisions need to be made,
either (a) emit the slice from the LLM during the detection pass with
an explicit `text_span_start` / `text_span_end` schema, or (b) skip
the slice entirely and let segment-level boundaries stand. Do NOT add
a regex post-processor; you'll move score 0 net while introducing
silent over-trims.

## Lesson 16 — LLMs cannot count characters; anchor boundaries to real text units (2026-08-28)

Wave 4 followed Lesson 15's advice — "emit the slice from the LLM
with an explicit text_span_start/text_span_end schema" — but
implemented it as **character offsets**. Jeff's 2026-07-06 review
(`validation/feedback/jeff_2026-07-06_feedback_ledger.md`) proved it
broken: 8 of 15 reviewed Kiddushin stories were mis-trimmed, one
(30a seg 7) cut in the middle of a word, inside a Biblical quotation.

Verified root cause: the nikud-stripping position map is faithful
(`stripped[i] == hebrew[map[i]]` for every i in
`src/story_detector_v10.py`), so the wrong cuts come from the model's
raw offset numbers, not the mapping. LLMs reproduce text reliably but
**do not count characters reliably**.

**Rule:** Never ask an LLM for a character offset / index into text.
When you need a sub-segment boundary, have the model **select a real
text unit** (a punctuation-delimited clause) or **quote the boundary
words verbatim**, then locate that unit deterministically. Sefaria's
Davidson text is fully punctuated and its English is aligned and
already-correct — use those units.

**Why:** Character counting is a known LLM weakness; text
reproduction is a known strength. The whole point of Lesson 15 (let
the model judge meaning) was right — the failure was the numeric
*interface*, not the idea of LLM emission.

**How to apply:** See `tasks/PLAN_wave5.md` — clause-index selection
anchored to punctuation, with a verbatim-quote fallback, plus an
assertion that every emitted boundary sits at a clause/word boundary
(a mid-word cut becomes a build error, not a silent corruption).

## Lesson 17 — Feedback and lessons must be durable gates, not passive notes (2026-08-28)

This session repeated two already-recorded mistakes: (1) Lesson 9
(fixture ≠ production) — Wave 4 shipped on 14/14 hand-picked fixtures
and then failed 11/15 in the wild; (2) memory
`feedback_boundary_corrections.md` ("never split feedback processing
again") — yet Jeff's feedback was again processed partially and the
nuance nearly lost. The lessons existed and did not prevent
recurrence, because a lessons file is a passive record only consulted
if someone remembers to.

**Rule:** Every substantive piece of expert feedback goes into a
durable, status-tracked ledger the moment it arrives
(`validation/feedback/jeff_<date>_feedback_ledger.md`), and every
recurring lesson gets converted from prose into an **executable gate**
where possible.

**Why:** Feedback scattered across emails, JSON, .docx, and
conversation gets processed once, partially, then lost on the next
context clear. The cost is real: Jeff repeats himself and trust
erodes.

**How to apply:** (a) On any expert reply, create/append the ledger
FIRST, before analysis or code — one row per note, with status
open/addressed and where addressed. (b) Turn key lessons into gates:
no detector ships without scoring on a FRESH held-out sample (not its
own fixture); build a criteria-conformance test from
`docs/golden/workflow/jeff_story_definition_criteria.md`; assert
structural invariants (Lesson 16's clause-boundary check). (c) Before
replying to the expert, walk the ledger's open-items tracker so
nothing is dropped.

## Lesson 18 — Audit the whole output, not the sample the expert happened to see (2026-08-28)

Jeff reviewed 15 of 95 Kiddushin stories and flagged 8 bad trims. We
wrote the Wave 5 plan around "8 stories to fix." A full audit of every
emitted cut — cheap, no LLM, no expert — showed **104 of 189 cuts
(55%) sever a Hebrew word** and 96% land mid-clause, across all three
v10 outputs. ~100 corrupted cuts sat in the two Ketubot files nobody
had reviewed. The cross-tab was worse: of the 9 reviewed stories that
were actually trimmed, **9 were marked incorrect**; of the 6 untrimmed,
4 were correct. The feature had zero observed successes.

**Rule:** When an expert flags N instances of a defect, measure the
defect's population rate over the entire corpus before planning the
fix. Expert samples locate a bug; they never size it. Write the
structural check that counts *all* violations — it usually takes
minutes and no API budget.

**Why:** Expert review is a sparse, non-random sample (Jeff reviewed
16% of one tractate). Planning from it silently assumes the unreviewed
90% is fine. Here the plan's scope, its urgency, and its correct
sequencing were all wrong as a result.

**How to apply:** Before writing a fix plan from feedback, ask "what
fraction of all outputs has this property?" If the property is
structural — a boundary that must sit on a word edge, a field that must
parse, a ref that must resolve — it is checkable deterministically.
Build that check first, record the baseline in the script's docstring,
and make it the ship gate (`scripts/audit_text_spans.py --strict`).
See `docs/golden/v10/wave4_span_failure_audit_2026-08-28.md`.

## Lesson 19 — Reverting to the safe default beats shipping a better version of a broken feature (2026-08-28)

The Wave 5 plan went straight from "broken char-offset trimmer" to
"clause-anchored trimmer," leaving 153 stories with corrupt boundaries
live for however long v11 took to build and validate. The better first
move was to **delete the feature**: strip the spans, restore
segment-level boundaries, ship today. Cost: $0, no LLM calls, no new
detector. Score movement: none (0.9171 → 0.9171, verified by running
the harness both ways). On Jeff's own sample, untrimmed output would
have scored 4/6 instead of 4/15.

**Rule:** When a feature is measurably net-negative, revert it before
building its replacement. Ship the safe default, then treat the new
mechanism as an improvement over a clean baseline rather than a rescue
of a corrupt one.

**Why:** The risk is asymmetric. An over-inclusive segment boundary is
recoverable by a human reader — Jeff can see the extra text and tell us
to trim it. A mid-word cut destroys information and reads as
incompetence to the expert whose trust the project runs on. "We are
building a fix" does not help the reviewer looking at corrupt text
today. Reverting also removes all schedule pressure from the
replacement, which is how the replacement gets built properly.

**How to apply:** Ask "what does this system do if I delete the feature
entirely?" If the answer is *degraded but honest*, that is the correct
interim state. Prove neutrality by running the eval harness before and
after rather than reasoning about what it reads. Keep the reverted
version as a new file; never edit the frozen one
(`scripts/strip_text_spans.py` → `results/v10/wave4_notrim/`).

## Lesson 20 — Thinking tokens are drawn from max_output_tokens (2026-08-29)

Enabling `thinking_level=HIGH` on `gemini-3.7-flash` while leaving
`max_output_tokens=512` made **72 of 95 stories fail**. The model
spent 487 tokens thinking, hit `finish_reason=MAX_TOKENS`, and never
emitted the JSON. It looked like the new model was broken on the task.
It wasn't — the budget was.

The codebase already knew this: the Pro-model branch of `_call_google`
raises the budget to 32768 precisely because "Pro models require
thinking — give enough tokens for thinking + structured JSON output."
The `thinking_level` branch was added without carrying that lesson over.

**Rule:** Whenever you enable or raise model reasoning, raise the output
token budget in the same edit. Thinking and output share one budget.

**Why:** The failure is silent and misattributes cleanly to the wrong
cause — "the new model can't do this task" rather than "we gave it no
room to answer." A 75% failure rate is easy to read as a capability
result and act on.

**How to apply:** On any run with a non-trivial skip/error rate, check
`finish_reason` and `usage_metadata.thoughts_token_count` before
concluding anything about model quality. When adding a new config path
next to an existing one, read what the existing branch compensates for
— it usually encodes a bug someone already paid for.

## Lesson 21 — A failed call must never be recorded as a decision (2026-08-30)

Wave 5b's runner, written the same day as Lessons 18-19, reintroduced the
exact failure the v10 regex fallback taught us. Reproduced by stubbing
every model call to fail:

```
counts: {'clause_roles': 0, 'clause_kept_full': 5, 'skipped': 7}  sum=12
stories_labelled: 5
text_span_source on failed stories: {'clause_kept_full'}
speech_profile fabricated: {'all_speech': False}
needs_review set: 0
```

`clause_kept_full` means "the model read this and judged all of it
in-story." In a total outage every story got that stamp, a fabricated
`speech_profile` was written into the dataset intended to answer Jeff's
speech-act question, and the counters summed to 12 for 5 stories. The
scorer then rated the dead run at 6% HIT / 38% HIT+NEAR — identical to
the legitimate no-trim baseline.

The cause was structural, not careless: the failure path `continue`d an
inner (per-side) loop, then fell through to an unconditional
"success" write after the loop. `src/story_detector_v11.py` avoids this
by `continue`ing the *story* loop, keeping the buckets mutually
exclusive. The new code regressed against the file it was forked from.

**Rule:** Every outcome bucket must be mutually exclusive and must sum
to the number of items processed. Assert it. A failure must write a
distinguishable provenance value — never the value that also means a
considered judgment — and must never emit derived data (ratios, flags,
profiles) computed from absent inputs.

**Why:** A wrong answer gets caught. A *confident* answer with the
provenance stripped off does not — it flows into results docs, datasets,
and expert-facing artifacts as though it were a judgment. This is the
same shape as the v10 regex fallback, and it is quieter, which makes it
worse.

**How to apply:** (a) `assert sum(counts.values()) == n_processed` in
any runner that reports counts. (b) Write the failure-injection test
FIRST: stub the model to raise, assert no item acquires a
success-provenance value and no derived field is written. (c) When
forking a file, diff the failure paths specifically — that is where the
hard-won handling lives and where a rewrite silently drops it.
(d) Scorers must read the run's own failure counts and refuse to score,
or quarantine failures in their own bucket, rather than silently folding
them into the metric.

**Status:** the runner was fixed 2026-08-30 and is guarded by
`tests/test_wave5b_runner_outcomes.py` — the failure-injection test was
written first and watched fail. Same fixture, model failing every call:
before `{kept_full: 6, no_split: 2, skipped: 6}` = 14 counts for 6
stories with 6 fabricated speech profiles; after `{no_split: 1,
skipped: 5}` = 6 counts, 0 profiles, 5 `needs_review`. Point (d) —
the scorer — is **still open**.

## Lesson 22 — Measure the noise floor before believing a one-run comparison (2026-08-30)

Wave 5 Step 2 fixed a real defect: the boundary prompt read
`story['summary']`, present on **0 of 262** stories, so 100% of stories
fell through to a joined event list that stops before the story's
resolution — while 35 of the 52 expert targets are END boundaries. The
fix changed 14 of 262 boundaries (5%) and **zero** of the 35 scored
targets.

Before calling that a null result we ran the same code twice:

```
Kiddushin, 95 stories
  baseline vs fixed      (different code) :   6 (6%)
  fixed  vs fixed-repeat (SAME code)      :   3 (3%)   <- noise floor
```

And the two identical-code runs disagreed on the scoreboard: 50% vs 56%
HIT, because one target flipped NEAR→HIT from nondeterminism alone. On
16 scorable Kiddushin targets, one target is 6.25 points — and noise
moves about one target per run.

**Rule:** before attributing a score change to a code change, run the
SAME code twice and report that spread alongside the result. If the
effect is not larger than the spread, say so; do not report it as an
improvement.

**Why:** every prompt-tuning number this project has quoted came from
one run each side. A 6-point "gain" on a 16-target gate is one target,
which is exactly what the model moves on its own. Without the noise
floor you cannot tell a fix from a coin flip — and the write-up will
claim a fix, because that is the story you set out to tell.

**How to apply:** (a) One extra run of the unchanged side costs the same
as the run you already did — always spend it. (b) Report `n` targets and
"one target = X points" next to any percentage. (c) When the effect is
inside the noise, keep a change only on its own merits (this one is a
strict information improvement) and say plainly that the gate is silent.
(d) If a decision depends on the difference, fix the gate first — see
`docs/golden/v11/wave5_summary_fix_2026-08-30.md` §5.
