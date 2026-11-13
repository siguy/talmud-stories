---
title: "Learn all the stories" sign-up for the Septimus yahrzeit (v1)
capability: [publication]
tractate: []
blocked_by: []
awaiting: []
writes: [site/, scripts/build_site_data.py, tests/test_site_data.py, docs/technical/septimus-signup-plan.md, firebase/, functions/]
finding:
superseded_by:
---

# "Learn all the stories" sign-up for the Septimus yahrzeit (v1)

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) first, then this. **Full plan:
[`docs/technical/septimus-signup-plan.md`](../docs/technical/septimus-signup-plan.md)** (scope, data model,
assignment, list versions, backend choice, risks). Builds on the reader from
[`2026-10-12-septimus-story-viewer.md`](2026-10-12-septimus-story-viewer.md).

## The problem

Daniel Septimus wants his community to collectively learn every story in Shas by his father Joe Septimus's first
yahrzeit (8 Elul 5787). People sign in with Google and commit minutes per week; each week they get consecutive
stories in order through Shas, by email and on a My stories page; missed stories roll over 2 weeks, then return to
the pool; when commitments exceed the list, stories are learned more than once.

## Method

PRs b–f in plan §9: landing + sign-in + commitment; weekly job (assignment, rollover, cycles); My stories + progress;
weekly email; Joe Septimus page. (a, word counts, done in #79.) Backend: Firebase Auth + Firestore on
`septimus-stories`, Blaze for the scheduled job and email (plan §8d).

## How you know it worked

- At 390 px in a real browser: land, sign in, commit 10 min/week; the account is recorded with its `?src=`.
- Emulator test over 3 simulated weeks: consecutive stories within each budget; a missed story rolls over 2 weeks,
  then goes to someone else; re-running a week changes nothing.
- A test weekly email to Simon renders on a phone and its unsubscribe link works.
- Per-tractate progress counts add up to the stories learned.

## Guardrails

- The goldens decide what is a story; boundary widenings stay display-only. Never edit `results/canonical/*`.
- AI notes stay hidden until approved. No secrets in the repo. No scope beyond plan §3 v1.

## When done

Write the finding to `docs/findings/<date>-septimus-signup.md`, add an `## Outcome` section
below, then `python3 scripts/board.py finish 2026-11-08-septimus-signup`. **Never delete it.**
