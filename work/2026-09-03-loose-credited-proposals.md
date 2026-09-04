---
title: The proposals credited to the expert's list by a window, not a match — 11 became 1
capability: [classification, review]
tractate: [ketubot, kiddushin, gittin]
blocked_by: []
awaiting: []
writes: [validation/ui/, validation/feedback/, results/recall/proposal_credit_audit.json]
finding: docs/findings/2026-09-03-loose-window-proposal-credit.md
superseded_by:
---

# Proposals credited by a window, not a match — 11 top-confidence became 1

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) first, then
[the finding](../docs/findings/2026-09-03-loose-window-proposal-credit.md).
**Capabilities: 3 Classification, 5 Review.** **Cost:** free until the round.

> ## UPDATE 2026-09-03 — most of this evaporated, and that is the finding
>
> The window that created this population was replaced
> ([`exact-matcher-cutover`](../docs/findings/2026-09-03-exact-matcher-cutover.md)).
> `results/recall/proposal_credit_audit.json` **has already been re-run** and the
> loose-only bucket is now **Gittin 0, Ketubot 0, Kiddushin 1**:
>
> | | was | now |
> |---|---|---|
> | loose-only proposals | 35 | **1** |
> | of those `YES`/`HIGH_CONFIDENCE` | 11 | **1** |
>
> **The one survivor is `Kiddushin 39b 8-10`**, `HIGH_CONFIDENCE`, credited to
> `kiddushin_041` — *a son dies while fulfilling the commandment of honouring his parents*.
> Read it against `kiddushin_041` and put it in exactly one of the three named states
> below. **Do not re-run the audit expecting 35**; that number was a measurement artifact
> and its disappearance is not evidence about the detector.
>
> What did **not** change: the Gittin/speech-act extras this item was going to share a
> review page with are unaffected, and one page is still the right ask.

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
   [`gittin-two-unjudged-yes`](2026-09-02-gittin-two-unjudged-yes.md) **and the 6
   speech-act entries from [`story-criteria`](2026-08-30-story-criteria.md) 6a/6b**
   (`docs/findings/2026-09-03-speech-act-blast-radius.md`). **One page, not three** —
   review throughput is the bottleneck and three pages is three asks. The three 6a
   entries that are genuinely all-speech (7a:1, 15a:0, 112a:11) are a `borderline`
   question for Jeff; the other three (17a:10, 54a:22, 85a:13-14) are boundary bugs and
   do not belong on a page at all — fix them, don't ask about them.

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
