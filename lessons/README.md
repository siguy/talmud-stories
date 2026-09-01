# Lessons

Ongoing log of mistakes, surprises, and things worth remembering across sessions.

Durable rules bought by a failure. **Numbers are permanent** — 313 `Lesson N` citations
across 65 files depend on them, so a lesson is never renumbered and never deleted.
One file each; add a new one as `lessons/_<slug>.md` on a branch and let it be numbered
when it lands on main, so two sessions cannot claim the same number (four did on
2026-08-30).

| # | date | lesson |
|---|---|---|
| 1 | 2026-03-25 | [Never split feedback processing into "auto" and "defer" without scheduling the "defer" pile](L-001-never-split-feedback-processing-into-auto-and-defer.md) |
| 2 | 2026-03-25 | [Don't add feedback from reviewed pages as few-shot examples for those same pages](L-002-don-t-add-feedback-from-reviewed-pages-as-few-shot.md) |
| 3 | 2026-03-25 | [The canonical review verdict format is different from prior rounds](L-003-the-canonical-review-verdict-format-is-different.md) |
| 4 | 2026-03-25 | [Cost estimates should be verified before building infrastructure](L-004-cost-estimates-should-be-verified-before-building.md) |
| 5 | 2026-03-25 | [Prompt engineering has a ceiling](L-005-prompt-engineering-has-a-ceiling.md) |
| 6 | 2026-03-25 | [Run the full evaluation before drawing conclusions](L-006-run-the-full-evaluation-before-drawing-conclusions.md) |
| 7 | 2026-03-25 | [Post-processing classifiers beat prompt modifications for precision improvements](L-007-post-processing-classifiers-beat-prompt.md) |
| 8 | 2026-03-25 | [Abstract patterns generalize; specific examples memorize](L-008-abstract-patterns-generalize-specific-examples.md) |
| 9 | 2026-03-25 | [Targeted tests on hand-picked examples don't predict production performance](L-009-targeted-tests-on-hand-picked-examples-don-t-predict.md) |
| 10 | 2026-03-27 | [Narrow questions beat open-ended detection for precision](L-010-narrow-questions-beat-open-ended-detection-for.md) |
| 11 | 2026-05-18 | [LLM nondeterminism breaks historical baselines](L-011-llm-nondeterminism-breaks-historical-baselines.md) |
| 12 | 2026-05-24 | [Most boundary feedback is text-internal, not segment-level](L-012-most-boundary-feedback-is-text-internal-not-segment.md) |
| 13 | 2026-05-24 | [Tight numeric gates penalize correct quality improvements](L-013-tight-numeric-gates-penalize-correct-quality.md) |
| 14 | 2026-05-25 | [When the detector overtakes the golden, FPs are a recall win in disguise](L-014-when-the-detector-overtakes-the-golden-fps-are-a.md) |
| 15 | 2026-06-03 | [Regex text-internal boundary editing cannot generalize](L-015-regex-text-internal-boundary-editing-cannot.md) |
| 16 | 2026-08-28 | [LLMs cannot count characters; anchor boundaries to real text units](L-016-llms-cannot-count-characters-anchor-boundaries-to.md) |
| 17 | 2026-08-28 | [Feedback and lessons must be durable gates, not passive notes](L-017-feedback-and-lessons-must-be-durable-gates-not.md) |
| 18 | 2026-08-28 | [Audit the whole output, not the sample the expert happened to see](L-018-audit-the-whole-output-not-the-sample-the-expert.md) |
| 19 | 2026-08-28 | [Reverting to the safe default beats shipping a better version of a broken feature](L-019-reverting-to-the-safe-default-beats-shipping-a.md) |
| 20 | 2026-08-29 | [Thinking tokens are drawn from max_output_tokens](L-020-thinking-tokens-are-drawn-from-max-output-tokens.md) |
| 21 | 2026-08-30 | [A failed call must never be recorded as a decision](L-021-a-failed-call-must-never-be-recorded-as-a-decision.md) |
| 22 | 2026-08-30 | [Measure the noise floor before believing a one-run comparison](L-022-measure-the-noise-floor-before-believing-a-one-run.md) |
| 23 | 2026-08-30 | [An exam built only from corrections cannot see a regression](L-023-an-exam-built-only-from-corrections-cannot-see-a.md) |
| 24 | 2026-08-30 | [Two expert sources can encode two different tasks](L-024-two-expert-sources-can-encode-two-different-tasks.md) |
| 25 | 2026-08-30 | [A display bug can manufacture expert feedback](L-025-a-display-bug-can-manufacture-expert-feedback.md) |
| 26 | 2026-08-30 | [Read the actual traceback, not the plausible one](L-026-read-the-actual-traceback-not-the-plausible-one.md) |
| 27 | 2026-08-30 | [A step that moves records out of the measured path is invisible by construction](L-027-a-step-that-moves-records-out-of-the-measured-path.md) |
| 28 | 2026-08-30 | [Read the source format, not the converter's output](L-028-read-the-source-format-not-the-converter-s-output.md) |
| 29 | 2026-08-30 | [A blind list stops being blind when the expert merges your output into it](L-029-a-blind-list-stops-being-blind-when-the-expert.md) |
| 30 | 2026-08-30 | ["Incorrect" is not a metric until you know what was rejected](L-030-incorrect-is-not-a-metric-until-you-know-what-was.md) |
| 31 | 2026-08-31 | [Verify a guard by simulating the failure it guards against](L-031-verify-a-guard-by-simulating-the-failure-it-guards.md) |
| 32 | 2026-08-31 | [A clean merge is not evidence that the result is correct](L-032-a-clean-merge-is-not-evidence-that-the-result-is.md) |
| 33 | 2026-08-31 | [When a mechanism needs a third guard, remove the mechanism](L-033-when-a-mechanism-needs-a-third-guard-remove-the.md) |
| 34 | 2026-08-31 | [A field an agent cannot ground fills with confident noise](L-034-a-field-an-agent-cannot-ground-fills-with-confident.md) |
| 35 | 2026-08-31 | [A composed metric names the pipeline, not the capability](L-035-a-composed-metric-names-the-pipeline-not-the-capability.md) |
| 36 | 2026-08-31 | [A verdict belongs to the version that was reviewed](L-036-a-verdict-belongs-to-the-version-that-was-reviewed.md) |
| 37 | 2026-08-31 | [The endpoints bracket a trade; they do not locate it](L-037-the-endpoints-bracket-a-trade-they-do-not-locate-it.md) |
| 38 | 2026-08-31 | [A guard that skips silently looks exactly like empty input](L-038-a-guard-that-skips-silently-looks-exactly-like-empty-input.md) |
