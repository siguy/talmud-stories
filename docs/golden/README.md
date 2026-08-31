# docs/golden — data only, and a redirect table

**As of 2026-08-30 this directory holds data, not prose.** Every writeup, plan and email
that lived here has moved; what remains is the JSON that scripts read and one file the
immutable harness writes to.

## What is still here, and why

| file | why it stayed |
|---|---|
| `v7/baseline_ketubot.json` | `scripts/evaluate_golden.py` writes here when `--output` is omitted. Moving it would force an edit to the harness, which `CLAUDE.md` forbids. **Historical, irreplaceable — always pass `--output`.** |
| `v7/boundary_corrections.json` | output of `scripts/boundary_lookup.py` |
| `v7/canonical_feedback_analysis.json` | output of `scripts/analyze_canonical_feedback.py` |
| `v9/wave3_round2_ketubot_score.json` | full eval output behind the Wave 3 round-2 rescore |
| `v10/post_improvement_ketubot.json` | v10-era score artifact |

## Where everything else went

Four destinations, decided file by file:

- **`docs/findings/`** — dated findings and measurements, `YYYY-MM-DD-slug.md`
- **`docs/history/`** — plans and approach docs, superseded by what they produced
- **`comms/sent/`** — email drafts to Jeff (the one still unsent is `comms/`)
- **`tests/baselines/`** — score baselines, which are *inputs* to `scripts/verify_wave3.py`, not prose
- **`docs/technical/`** — the one live how-to (`new_tractate_workflow.md`)

| old path | new path |
|---|---|
| `docs/golden/v10/email_draft_jeff_v10_update.md` | [`comms/sent/2026-03-25-email-jeff-v10-update.md`](../../comms/sent/2026-03-25-email-jeff-v10-update.md) |
| `docs/golden/v10/email_draft_jeff_wave4.md` | [`comms/sent/2026-06-15-email-jeff-wave4.md`](../../comms/sent/2026-06-15-email-jeff-wave4.md) |
| `docs/golden/v10/email_draft_jeff_wave4_and_roadmap.md` | [`comms/sent/2026-07-06-email-jeff-wave4-and-roadmap.md`](../../comms/sent/2026-07-06-email-jeff-wave4-and-roadmap.md) |
| `docs/golden/v10/findings_v10_golden_dataset.md` | [`docs/findings/2026-03-25-golden-dataset-v10.md`](../findings/2026-03-25-golden-dataset-v10.md) |
| `docs/golden/v10/wave4_diff_ketubot.md` | [`docs/findings/2026-06-15-wave4-span-diff-ketubot.md`](../findings/2026-06-15-wave4-span-diff-ketubot.md) |
| `docs/golden/v10/wave4_diff_kiddushin.md` | [`docs/findings/2026-06-15-wave4-span-diff-kiddushin.md`](../findings/2026-06-15-wave4-span-diff-kiddushin.md) |
| `docs/golden/v10/wave4_span_failure_audit_2026-08-28.md` | [`docs/findings/2026-08-28-wave4-span-failure-audit.md`](../findings/2026-08-28-wave4-span-failure-audit.md) |
| `docs/golden/v11/appendix_provenance_correction_2026-08-30.md` | [`docs/findings/2026-08-30-appendix-provenance-correction.md`](../findings/2026-08-30-appendix-provenance-correction.md) |
| `docs/golden/v11/boundary_ruler_rebuild_2026-08-30.md` | [`docs/findings/2026-08-30-boundary-ruler-rebuild.md`](../findings/2026-08-30-boundary-ruler-rebuild.md) |
| `docs/golden/v11/detection_classification_ruler_2026-08-30.md` | [`docs/findings/2026-08-30-detection-classification-ruler.md`](../findings/2026-08-30-detection-classification-ruler.md) |
| `docs/golden/v11/email_jeff_2026-08-30.html` | [`comms/sent/2026-08-30-email-jeff.html`](../../comms/sent/2026-08-30-email-jeff.html) |
| `docs/golden/v11/email_jeff_2026-08-30.md` | [`comms/sent/2026-08-30-email-jeff.md`](../../comms/sent/2026-08-30-email-jeff.md) |
| `docs/golden/v11/email_jeff_next_open_questions.md` | [`comms/email_jeff_next_open_questions.md`](../../comms/email_jeff_next_open_questions.md) |
| `docs/golden/v11/kiddushin_list_parse_2026-08-30.md` | [`docs/findings/2026-08-30-kiddushin-list-parse.md`](../findings/2026-08-30-kiddushin-list-parse.md) |
| `docs/golden/v11/mishnah_filter_delta_2026-08-30.md` | [`docs/findings/2026-08-30-mishnah-filter-delta.md`](../findings/2026-08-30-mishnah-filter-delta.md) |
| `docs/golden/v11/mishnah_tagger_chapter_boundary_2026-08-30.md` | [`docs/findings/2026-08-30-mishnah-tagger-chapter-boundary.md`](../findings/2026-08-30-mishnah-tagger-chapter-boundary.md) |
| `docs/golden/v11/trim_asymmetry_2026-08-30.md` | [`docs/findings/2026-08-30-trim-asymmetry.md`](../findings/2026-08-30-trim-asymmetry.md) |
| `docs/golden/v11/wave5_summary_fix_2026-08-30.md` | [`docs/findings/2026-08-30-wave5-summary-fix.md`](../findings/2026-08-30-wave5-summary-fix.md) |
| `docs/golden/v11/wave5b_decision_2026-08-30.md` | [`docs/findings/2026-08-30-wave5b-decision.md`](../findings/2026-08-30-wave5b-decision.md) |
| `docs/golden/v11/wave5b_review_2026-08-30.md` | [`docs/findings/2026-08-30-wave5b-review.md`](../findings/2026-08-30-wave5b-review.md) |
| `docs/golden/v7/email_draft_jeff_kiddushin.md` | [`comms/sent/2026-04-07-email-jeff-kiddushin.md`](../../comms/sent/2026-04-07-email-jeff-kiddushin.md) |
| `docs/golden/v7/kiddushin_feedback_analysis_2026-04-23.md` | [`docs/findings/2026-04-23-kiddushin-feedback-analysis.md`](../findings/2026-04-23-kiddushin-feedback-analysis.md) |
| `docs/golden/v7/kiddushin_run_plan.md` | [`docs/history/2026-03-27-kiddushin-run-plan.md`](../history/2026-03-27-kiddushin-run-plan.md) |
| `docs/golden/v8/baselines/ketubot_wave1_baseline.json` | [`tests/baselines/ketubot_wave1_baseline.json`](../../tests/baselines/ketubot_wave1_baseline.json) |
| `docs/golden/v8/baselines/ketubot_wave2_baseline_today.json` | [`tests/baselines/ketubot_wave2_baseline_today.json`](../../tests/baselines/ketubot_wave2_baseline_today.json) |
| `docs/golden/v8/baselines/kiddushin_wave1_baseline.json` | [`tests/baselines/kiddushin_wave1_baseline.json`](../../tests/baselines/kiddushin_wave1_baseline.json) |
| `docs/golden/v8/baselines/kiddushin_wave2_baseline_today.json` | [`tests/baselines/kiddushin_wave2_baseline_today.json`](../../tests/baselines/kiddushin_wave2_baseline_today.json) |
| `docs/golden/v8/wave1_results.md` | [`docs/findings/2026-05-18-wave1-results.md`](../findings/2026-05-18-wave1-results.md) |
| `docs/golden/v8/wave2_results.md` | [`docs/findings/2026-05-24-wave2-results.md`](../findings/2026-05-24-wave2-results.md) |
| `docs/golden/v8/wave3_approach.md` | [`docs/history/2026-05-24-wave3-approach.md`](../history/2026-05-24-wave3-approach.md) |
| `docs/golden/v9/email_draft_jeff_wave3.md` | [`comms/sent/2026-05-25-email-jeff-wave3.md`](../../comms/sent/2026-05-25-email-jeff-wave3.md) |
| `docs/golden/v9/email_draft_jeff_wave3_round2.md` | [`comms/sent/2026-06-03-email-jeff-wave3-round2.md`](../../comms/sent/2026-06-03-email-jeff-wave3-round2.md) |
| `docs/golden/v9/wave3_results.md` | [`docs/findings/2026-05-25-wave3-results.md`](../findings/2026-05-25-wave3-results.md) |
| `docs/golden/v9/wave3_round2_ketubot_rescore.md` | [`docs/findings/2026-06-03-wave3-round2-ketubot-rescore.md`](../findings/2026-06-03-wave3-round2-ketubot-rescore.md) |
| `docs/golden/workflow/PLAN_golden_dataset_and_generalization.md` | [`docs/history/2026-03-25-PLAN-golden-dataset-and-generalization.md`](../history/2026-03-25-PLAN-golden-dataset-and-generalization.md) |
| `docs/golden/workflow/approach_review_and_scaling_2026-07-06.md` | [`docs/findings/2026-07-06-approach-review-and-scaling.md`](../findings/2026-07-06-approach-review-and-scaling.md) |
| `docs/golden/workflow/error_taxonomy.md` | [`docs/findings/2026-03-17-error-taxonomy.md`](../findings/2026-03-17-error-taxonomy.md) |
| `docs/golden/workflow/false_positive_learning_plan.md` | [`docs/history/2026-03-27-PLAN-false-positive-learning.md`](../history/2026-03-27-PLAN-false-positive-learning.md) |
| `docs/golden/workflow/jeff_story_definition_criteria.md` | [`docs/findings/2026-07-06-jeff-story-definition-criteria.md`](../findings/2026-07-06-jeff-story-definition-criteria.md) |
| `docs/golden/workflow/new_tractate_workflow.md` | [`docs/technical/new_tractate_workflow.md`](../technical/new_tractate_workflow.md) |
| `docs/golden/workflow/recall_measurement_ketubot_2026-08-28.md` | [`docs/findings/2026-08-28-recall-measurement-ketubot.md`](../findings/2026-08-28-recall-measurement-ketubot.md) |
| `docs/golden/workflow/recall_miss_diagnosis_2026-08-30.md` | [`docs/findings/2026-08-30-recall-miss-diagnosis.md`](../findings/2026-08-30-recall-miss-diagnosis.md) |
| `docs/golden/workflow/research_overfitting_and_generalization.md` | [`docs/findings/2026-03-25-overfitting-and-generalization-research.md`](../findings/2026-03-25-overfitting-and-generalization-research.md) |

## Older paths, broken before this move

Some documents still cite paths like `docs/golden/error_taxonomy.md` — flat paths that
have not existed since the 2026-05-24 reorganisation (`26c7595`) moved everything into
`v7/ v8/ v9/ v10/ workflow/`. Those references were already broken and are **left as
written**: the files carrying them are dated findings, and editing a finding to look as
though it had always been right is the habit this repo avoids. Map them by filename
through the table above.

`results/canonical/ketubot_canonical.json` also carries two `docs/golden/...` provenance
pointers. **They are deliberately not rewritten** — the golden is the artifact these moves
exist to protect, and running `sed` inside it to fix a link is not a trade worth making.
