---
title: Stage 1 counts NARRATIVE_EVENT and ignores HABITUAL — decide whether that is right
capability: [triage]
tractate: [ketubot, kiddushin, gittin, yevamot]
blocked_by: []
awaiting: []
writes: [src/event_triage.py, results/v11/triage_rules/, tests/test_triage_rules.py]
finding:
superseded_by:
---

# Does a HABITUAL segment keep a page?

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md), then
[`2026-09-07-triage-live-rule-remeasured`](../docs/findings/2026-09-07-triage-live-rule-remeasured.md)
and [`2026-08-31-triage-single-narrative`](../docs/findings/2026-08-31-triage-single-narrative.md).
**Capability: 1 Triage.** **Depends on Jeff: no.** **Cost: no API calls to screen.**

## The claim to test

`should_skip_page()` keeps a page on `>=1 NARRATIVE_EVENT`. Stage 1 also emits
`HABITUAL`, and that label **counts for nothing**. Measured 2026-09-07: **Ketubot 82b**
carries 4 `HABITUAL` and 0 `NARRATIVE_EVENT` and is discarded — *"in the beginning they
would write two hundred for a virgin… until Shimon ben Shetah came and enacted"*, an entry
on Jeff's blind list. Our own Stage 1 saw it, labelled it, and the keep-rule threw it away.

**This is definitional, not a threshold.** `V>=4` was rejected in August as a number fitted
to one story, with a test pinning the rejection (Lesson 18, Lesson 37). *"A habitual
practice is narrative evidence"* is a claim about what the labels mean, and it either
holds for every tractate or it does not. **Do not argue it from the count** — it is worth
1 story in the measured corpus, and if that is the case for it, the case is bad.

## Method

1. **No API calls.** `sweep_triage_rules.py` prices candidates against the discarded-page
   Stage 2 output already on disk. `N+H >= 1` is strictly looser than the shipped rule, so
   it is in that script's admissible set; assert it per candidate as the script requires.
2. Price on **all four** tractates, not the two the discarded-page rerun covers — for
   Gittin and Yevamot report extra pages examined and say plainly that the recall gain
   there is **unmeasured**, not zero.
3. Report the **precision cost in reviewer-facing proposals**, not just calls. Review
   throughput is the project's bottleneck; the August decision turned on 24 false
   proposals, not on 224 calls.
4. Sweep the interval, not the endpoints (Lesson 37): `N>=1` (shipped), `N+H>=1`,
   `N+H>=1 or V>=4`, keep-everything.

## How you know it worked

- Ketubot 82b is examined, and Stage 2's verdict on it is reported either way — an
  examined page that still yields nothing is a *result*, not a failure.
- Triage recall re-measured with `--matcher exact` only, from **98.0% / 97.8%**.
- The shipped decision is stated as **principled or tuned**, in those words, with a test
  pinning whichever way it goes — as `V>=4` has.

## Guardrails

- Never quote a Triage figure without saying which matcher and which rule produced it.
- A looser rule cannot lose a story it already keeps; if a sweep row shows recall falling,
  the harness is wrong, not the rule.

## When done

Finding to `docs/findings/<date>-habitual-triage.md`, `## Outcome` here, then
`python3 scripts/board.py finish 2026-09-07-habitual-is-narrative-evidence`.
