---
title: Reader feedback loop - triage, ledger, routes
capability: [publication, review]
tractate: []
blocked_by: []
awaiting: []
writes: [scripts/feedback_triage.py, results/site_feedback/, worker/, site/app.js, site/config.js, tests/test_site_feedback.py, docs/site-feedback-log.md, results/site_notes/held.json]
finding:
superseded_by:
---

# Reader feedback loop

Plan: [`docs/history/2026-11-15-PLAN-reader-feedback-loop.md`](../docs/history/2026-11-15-PLAN-reader-feedback-loop.md).
Decisions (Simon, 2026-11-15/16): D1 boundary fixes automatic + before/after list; D2 redrafted notes automatic with a
monthly spot check; D3 Jeff-reviewed tractates only with Simon's yes; D4 forward Sefaria text errors monthly;
D5 no "recently fixed" list yet; D6 attach the account (nothing to attach until sign-in exists on the site);
D10 staging as a second origin, tagged; D11 copy box + mailto Talmud-stories@projects.simonbrief.com;
D12 triage runs as a workflow in the PRIVATE feedback repo (not set up here); D9 weekly, Sunday.

## Done in this item
- Phase 1a: live path confirmed (two test reports, issues #5/#6, closed with outcome `test`).
- Phase 2: `scripts/feedback_triage.py` (pull / report / close / changelog / route-note / case), offline tests.
- Phase 1b: `note` category, `span` / `extended` / `note_drafted` / `note_approved` / `site` / `test` fields, multi-origin CORS,
  reader-usable fallback. **Deployed 2026-11-16** (Cloud Run revision 00005; staging and production sites); form tested on both, fallback seen on staging.

## Not done (see Outcome)
Boundary route (`--flags`), waits for the boundary-review PR. Phase 5 until ~20 confirmed cases.

## Still open
- PR 103 merge (auto-mode blocked `gh pr merge`; Simon merges). Deployed from this branch, which equals main + this PR.
- Boundary route: `feedback_triage.py boundary-flags` writes `{id: concern}`; run `review_site_boundaries.py export --flags results/site_feedback/_local/boundary_flags.json` when real reports exist.
- D12: copy `worker/feedback-weekly.yml` into the private feedback repo as `.github/workflows/triage.yml`.
- Disable orphaned workflows (needs Simon's yes). D6: no sign-in on the site yet. Phase 5 at ~20 confirmed cases.
