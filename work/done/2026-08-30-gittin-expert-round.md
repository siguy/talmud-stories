---
title: Gittin — expert round
capability: [review]
tractate: [gittin]
blocked_by: [2026-08-30-gittin-review-ui]
awaiting: []
writes: [validation/feedback/gittin/]
finding:
superseded_by:
---

# Gittin — expert round

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md) and
[`docs/technical/new_tractate_workflow.md`](../../docs/technical/new_tractate_workflow.md),
which documents this sequence, then this.

## Method

See the workflow doc; this item is the handle and the ordering.

## Guardrails

- **Ask Jeff to keep his appendix separate BEFORE the first review round**, not
  after (Lesson 29). Once merged into his list it cannot be reconstructed, and the
  list stops being able to measure what we missed.
- Regenerate a same-day baseline before any comparison (Lesson 11).
- Report the corrections ruler and the neutral ruler separately (Lesson 24).

## When done

Finding to `docs/findings/`, add `## Outcome`, `git mv` to `work/done/`.

## Outcome

**Done, 2026-09-02.** The round ran on `validation/ui/axis_gittin_unlisted.html` — the 25
proposals with no entry on his 2005 list — and **all 25 came back**:
**3 `yes`, 4 `borderline`, 18 `no`**.
Finding: [`2026-09-02-gittin-25-verdicts.md`](../../docs/findings/2026-09-02-gittin-25-verdicts.md).
Verbatim reply kept at `jeff comms/9-02-2026/`; ingest copy at
`validation/feedback/gittin_axes_review_2026-09-02.json`.

**Three stories he did not have** — 19a:16, 43b:4, 70a:22 — and 18 explicit negatives,
which is the first negative-label set this project holds on a tractate that was never in
a prompt.

### Why this closed with its `blocked_by` still open

`2026-08-30-gittin-review-ui` is still an open item, but the page it describes exists and
is what he reviewed. The Gittin sequence was executed ahead of its own bookkeeping during
the 2026-09-01 blind run; the artifacts are on disk and the round is done. **The dependency
was satisfied in fact and not in the file** — left as-is rather than back-dating the
upstream items, because a `## Outcome` written now for work done then would be a
reconstruction, and this file says plainly which it is.

### The guardrail that mattered, and the one that did not

- **Lesson 29 (`jeff:appendix-separate`) held.** He returned a standalone verdict file and
  merged nothing into his 2005 list, so the Gittin list is still blind. The ask stays in
  every email until he acknowledges it as a standing habit — one round is not a policy.
- **The instrument failed anyway.** Every structured field came back empty and five
  boundary corrections arrived as prose. The round succeeded; the schema did not capture
  it. → [`axis-fields-unused`](2026-09-02-axis-fields-unused.md)

### What it opened

Two things neither this item nor the workflow doc anticipated:

1. **He reversed three of his own prose answers** once he saw the text — always toward the
   stricter reading. → [`_a-policy-answer-does-not-certify-a-case.md`](../../lessons/_a-policy-answer-does-not-certify-a-case.md)
2. **`"It is filled in by the translator"`** — a named mechanism for a class of false
   positives, sitting in our prompt, where English gets 300 characters and Hebrew 200.
   → [`english-first-prompt`](2026-09-02-english-first-prompt.md)
