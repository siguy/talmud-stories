---
title: Does the twin pass recover Ketubot's 7 adjacent misses?
capability: [detection]
tractate: [ketubot]
blocked_by: []
awaiting: []
writes: [results/v11/ketubot/, results/recall/ketubot_jeff2005_matches_twinall.json, docs/findings/2026-09-15-ketubot-twin-pass.md]
finding:
superseded_by:
---

# Does the twin pass recover Ketubot's 7 adjacent misses?

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md), then
[`twin-pass`](../docs/findings/2026-09-14-twin-pass.md) and
[`miss-anatomy`](../docs/findings/2026-09-07-miss-anatomy.md).
**Capability: 2 Detection.** **Depends on Jeff: no.**

## The claim to test

On Yevamot the twin pass took Detection recall **89.2% -> 94.1%**, recovering **6 of its 7**
adjacent-class misses by name (the 7th is a Mishnah-scope case). **Ketubot holds 7 of the
18 adjacent cases** — the largest share — and has never been run on v11.

**Claim:** the same pass recovers Ketubot's 7, at a comparable reviewer cost (Yevamot:
12 proposals added, 9 not on Jeff's list).

## Method

**Two arms, both on v11 with Kiddushin few-shots.** The control is not optional and the
shipped v10 artifact cannot serve as one: v10 ran on **Ketubot** few-shots, so comparing
twin-on against it would confound the pass with the few-shot change
([`ketubot-v11-runner`](done/2026-09-15-ketubot-v11-runner.md)).

1. Control — `TWIN_PASS` unset -> `results/v11/ketubot/ketubot_v11.json`
2. Twin — `TWIN_PASS=1 TWIN_TRIGGER=all` -> `results/v11/ketubot/ketubot_v11_twinall.json`

Runs are deterministic (spread 0.0, established 2026-09-09), so one run per arm.
Stage 1 is fully cached: 97 examined / 125 skipped, no triage spend.

3. Score both through `measure_recall_vs_expert_list.py` with `--matcher exact` **and no
   other matcher** — the 4-gram window cannot see this defect at all.
4. **Report the 7 adjacent cases by name**, found or not. A headline that moves while the
   named cases stay missed is a different effect and must be said so.
5. Report **proposals added and how many are not on Jeff's list** beside the recall
   change. That is the reviewer cost, and review throughput is the bottleneck.
6. Score the neutral boundary ruler `--by-direction` on both arms.

## How you know it worked

- Ketubot Detection recall (given the page survived triage) rises from **90.3%**.
- The 7 adjacent cases are named individually with their outcome.
- Proposals-not-on-his-list is reported and is single digits, as on Yevamot.
- The boundary ruler has not fallen.

## Guardrails

- **The control arm ships in the same finding.** Without it the number is a v11 + Kiddushin
  + twin composite and no part of it is attributable (Lesson 22).
- **A Ketubot v11 figure is not comparable to the v7-v10 Ketubot figures** — different
  few-shot source. Say which, every time.
- Blind and corrections rulers reported apart (Lesson 24).
- Never quote the composite score (Critical Rule #5).
- `--output` on every scoring call; never bare (Critical Rule #4).

## When done

Finding to `docs/findings/2026-09-15-ketubot-twin-pass.md`, `## Outcome` here, then
`python3 scripts/board.py finish 2026-09-15-ketubot-twin-measure`.
