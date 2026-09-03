---
title: 11 top-confidence proposals credited to the expert's list by a window, not a match
capability: [classification, review]
tractate: [ketubot, kiddushin, gittin]
blocked_by: []
awaiting: []
writes: [validation/ui/, validation/feedback/, results/recall/proposal_credit_audit.json]
finding: docs/findings/2026-09-03-loose-window-proposal-credit.md
superseded_by:
---

# 11 top-confidence proposals credited by a window, not a match

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) first, then
[the finding](../docs/findings/2026-09-03-loose-window-proposal-credit.md).
**Capabilities: 3 Classification, 5 Review.** **Cost:** free until the round.

## The problem

35 proposals across the three measured tractates sit inside an expert story's search
window without overlapping its own segments, and were therefore treated as corroborated.
**11 of them are `YES` or `HIGH_CONFIDENCE`** — the band we tell Jeff he can skim.

Nobody has judged any of them. They are `unverified`, not `wrong`: each is either a story
of ours his list does not name, our mis-bounding of one that is his, or a false positive,
and nothing on disk separates those.

## Method

1. `python3 scripts/audit_proposal_credit.py --out results/recall/proposal_credit_audit.json`
   — the list, per tractate, with what each was credited to.
2. **Read each of the 11 against the expert entry it was credited to** before putting any
   on a page. Some will turn out to be our mis-bounding of *his* story, and those are a
   Boundaries problem, not a Classification question — sending him a boundary error as
   *"is this a story?"* wastes a verdict and gets a confusing answer.
3. Put what survives on the next review page, with the extras already queued from
   [`gittin-two-unjudged-yes`](2026-09-02-gittin-two-unjudged-yes.md). **One page, not
   two** — review throughput is the bottleneck and two pages is two asks.

## How you know it worked

Each of the 11 ends in exactly one of three states, named: **a boundary error** (fixed
here, no verdict needed), **queued for review**, or **judged**. A count that does not
break down that way means some were quietly dropped.

## Guardrails

- **Do not fold them into any golden as accepted.** No expert has labelled them. The
  Gittin golden already handles this correctly — they are in `unlabelled_proposals`.
- **Do not treat this as a recall problem.** Recall is a question about *his* stories and
  is unaffected; these move precision only. Anyone recomputing 87.9 / 83.3 / 97.3 from
  this has misread it.
- **Do not "fix" the loose window.** It is correct for recall, which is what it was built
  for. The fix is to use the strict test wherever the join is read in the proposal
  direction — which is what the audit does.

## When done

Write the finding, add an `## Outcome`, and
`python3 scripts/board.py finish 2026-09-03-loose-credited-proposals`.
