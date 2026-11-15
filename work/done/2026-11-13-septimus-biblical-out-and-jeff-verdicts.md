---
title: Septimus site — biblical stories out of scope, Jeff's 2026-11-12 verdicts applied
capability: [publication]
tractate: []
blocked_by: []
awaiting: []
writes: [scripts/build_site_data.py, results/shas_run/septimus_site_decisions.json, site/data/, tests/test_site_data.py, docs/technical/septimus-story-filter.md, docs/technical/septimus-signup-plan.md]
finding:
superseded_by:
---

# Septimus site — biblical stories out of scope, Jeff's 2026-11-12 verdicts applied

**Self-contained.** A fresh session executes this with no other context.
Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then this.

## The claim to test / the problem

Simon, 2026-11-13, three decisions for what the Septimus family site ships:

- **A.** Biblical stories leave the site's default list, reversing 2026-11-10, for consistency with
  Jeff's R-S1 (he ruled the Berakhot 54a-b lepers out of scope). They are kept in the site data in a
  separate `out_of_scope` bucket with the reason, so a later filter can surface them. No UI.
- **B.** Remove the 12 passages Jeff ruled not / borderline: Arakhin 23b:0-1, Pesachim 66b:4,
  Shabbat 147a:6, Chullin 46a:8, Chullin 57b:6-7, Niddah 7b:4-5, and Eruvin 41a:1, 51a:2-3, 53b:8,
  59b:9-11, 67b:15-18, 68a:10-11. Match by span overlap (Lesson 36).
- **C.** Add Sanhedrin 52b:4 (LOW in both runs): Jeff 2026-11-12 "I would include it", Simon
  2026-11-13 "Include this". An explicit per-passage inclusion, not a gate.

## Method

Decisions live in `results/shas_run/septimus_site_decisions.json`, each with who decided and when;
`scripts/build_site_data.py` reads it. No judge or detector runs, no API calls.

## How you know it worked

Before/after counts per tractate; each removal matched to one shipped story; 52b:4 present with
provenance; no story both in `stories` and `out_of_scope`; tests pin all three.

## Guardrails

The inclusion list is the only promotion and is per passage, by name. A removal or inclusion that
matches nothing is named on stderr, never silent.

## When done

Add an `## Outcome` section below and `python3 scripts/board.py finish <slug>`. **Never delete it.**

## Outcome

Done 2026-11-13. Site 1,897 -> **1,784** stories (-102 biblical, -12 Jeff not/borderline, +1 Sanhedrin 52b:4).

- **A.** 102 stories flagged `biblical` (unchanged count since 2026-11-10) moved from `stories` to each tractate
  file's `out_of_scope` list, with `out_of_scope_reason`. Largest: Sanhedrin 39, Megillah 9, Shabbat 8, Sotah 7.
  Berakhot 54b:0 (the lepers) is among them. No story is in both lists (asserted in the build and the tests).
  Why the reversal: one scope with Jeff's R-S1, after he ruled the lepers out of scope on 2026-11-12.
- **B.** All 12 removals matched exactly one shipped story by overlap: the Eruvin card spans 53b_8-9 and 67b_15-16
  matched the site's 53b:8-8 and 67b:15-18. None was biblical.
- **C.** `sanhedrin-52b-4-4` ships with `included_by` (Jeff 2026-11-12 + Simon 2026-11-13), `reviewed: true`,
  its honest `LOW_CONFIDENCE` grade.
- Decisions are data: `results/shas_run/septimus_site_decisions.json`. No model calls.
- Side effect: 7 of the 60 precision-sample stories are no longer on the site (the 6 above from the sample, plus
  `berakhot-54b-0-0`); the sample file was not changed.
