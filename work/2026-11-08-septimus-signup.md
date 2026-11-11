---
title: "Learn all the stories" sign-up for the Septimus yahrzeit (v1)
capability: [publication]
tractate: [ketubot, kiddushin, gittin, yevamot]
blocked_by: []
awaiting: []
writes: [site/, scripts/build_site_data.py, tests/test_site_data.py, docs/technical/septimus-signup-plan.md, firebase/]
finding:
superseded_by:
---

# "Learn all the stories" sign-up for the Septimus yahrzeit (v1)

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) first, then this. **Full plan:
[`docs/technical/septimus-signup-plan.md`](../docs/technical/septimus-signup-plan.md)** (scope, data model,
assignment, list versions, backend choice, risks). Builds on the reader from
[`2026-10-12-septimus-story-viewer.md`](2026-10-12-septimus-story-viewer.md).

## The problem

Daniel Septimus wants his community to collectively learn every story by his father Joe Septimus's first yahrzeit.
People sign in with Google, say how much time they will give, get stories assigned, mark them learned, and everyone
sees how many are left.

## Method

Four PRs on `septimus/signup-*`: (a) word counts + reading time in the export; (b) Google sign-in + sign-up by time +
assignment; (c) my stories + mark learned + progress field; (d) Joe Septimus page placeholder. Backend: Firebase Auth +
Firestore (pending Simon's confirmation, plan §8).

**Build plan (inventory, order, schedule, what can start before the Shas PR):**
[`docs/history/2026-11-10-PLAN-septimus-signup-build.md`](../docs/history/2026-11-10-PLAN-septimus-signup-build.md).

## How you know it worked

- Every story carries `words` and `minutes`; totals match the plan's §2 table.
- At 390 px in a real browser: sign in, pledge 15 minutes, receive consecutive stories summing ≈15 minutes; a second
  account cannot receive the same stories; marking learned shows on the progress field from another device.
- Per-tractate counts on the progress field sum to the shipped story counts.

## Guardrails

- The goldens decide what is a story; boundary widenings stay display-only. Never edit `results/canonical/*`.
- AI notes stay hidden until approved. No secrets in the repo. No scope beyond plan §3 v1.

## When done

Write the finding to `docs/findings/<date>-septimus-signup.md`, add an `## Outcome` section
below, then `python3 scripts/board.py finish 2026-11-08-septimus-signup`. **Never delete it.**
