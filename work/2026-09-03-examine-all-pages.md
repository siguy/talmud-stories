---
title: Ship examine_all_pages — Simon has accepted the call cost; price the review cost
capability: [triage]
tractate: [ketubot, kiddushin]
blocked_by: []
awaiting: []
writes: [src/story_detector_v11.py, src/event_triage.py, results/v11/]
finding:
superseded_by:
---

# Ship `examine_all_pages` — Simon has accepted the call cost; price the review cost

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) §1.1 and
[`docs/findings/2026-08-31-triage-recall-price.md`](../docs/findings/2026-08-31-triage-recall-price.md).

## The decision, already made

The trade was measured on 2026-08-31 and left open as *"a product decision, and the
review-cost half of it is still unpriced."* **Simon decided on 2026-09-03: take it.**

| | shipped triage | every page examined |
|---|---|---|
| Ketubot end-to-end recall | 96.0% | **96.6%** (+1 story) |
| Kiddushin end-to-end recall | 93.3% | **96.7%** (+3 stories) |
| extra Stage 2 calls | — | 224 across both tractates |
| precision on discarded pages | — | 14.3% (4 real of 28 proposals) |

The two tractates converge — **the whole Ketubot/Kiddushin gap is the triage threshold,
and it closes.**

## What it costs, in the two currencies

**Money: negligible.** Median page text is **11.7K characters**; a Stage 2 call is that
plus roughly 15K characters of prompt scaffolding, so on the order of **10K input tokens
and ~1.5K output per call**. 224 calls ≈ **2.5M input / 0.35M output tokens** for both
tractates — single-digit dollars at Flash rates, and about **100–120 extra calls per new
tractate**. Verify against current Gemini pricing before quoting a figure to anyone; the
token counts above are measured, the dollar figure is not.

**Jeff's attention: the real price, and still unmeasured.** ~24 extra false proposals per
tractate reach the review queue. Against a 25-proposal round like Gittin's, that is
roughly a doubling of what he reads to gain 1–3 stories. **That is the number this item
must produce**, and it is why "Simon doesn't mind the cost" does not by itself close the
question — the cost that matters is not Simon's.

**This item is therefore mostly about mitigating the second cost, not paying the first.**

## Method

1. **Ship the flag.** `examine_all_pages` already exists and was fixed on 2026-09-01 to
   gate page selection alone. Enabling it is a configuration change, not new code. Keep
   Stage 1 running and its labels recorded — they stay useful as a *feature* even when
   they no longer gate.
2. **Do not ship it naked.** Pair it with
   [`extra-story-discriminator`](2026-09-03-extra-story-discriminator.md) so the 24 extra
   proposals arrive **ranked** rather than shuffled into the queue. Triage labels become an
   input to that ranking: a proposal from a page Stage 1 wanted to discard is prior
   evidence against it, worth 14.3% precision as a base rate.
3. **Re-run affected numbers.** Every recall, precision and composite figure on the board
   is conditioned on the shipped skip decisions. Enabling this changes the denominator of
   the Detection rows (`FRAMEWORK` §1.2 — detection is quoted *given the page survived
   triage*, and now every page does). **The Detection cells must be re-derived, not
   carried over.**
4. **Screen the cheaper options first anyway.**
   [`triage-recall-options`](2026-09-03-triage-recall-options.md) lists five untried
   approaches, two of them free. On Ketubot the `N≥1` rule already captures 100% of the
   available gain at 1/31 the cost. If the opener lexicon and amud-pairing recover the
   same stories for no calls, this item ships a worse trade. **Order matters: screen, then
   ship.**

## How you know it worked

- Blind recall on both lists moves to ~96.6% / 96.7%, matching the 2026-08-31 measurement.
- Proposals added to the review queue, counted — **the number Jeff feels**.
- Detection cells re-derived under the new denominator, and STATUS/STATE say which rule
  each number describes.

## Guardrails

- **Nothing on the board may keep a pre-change number without saying so.** This is the
  exact shape of the session's recurring defect: a number correct for the question it was
  built for, quoted against a different one.
- Triage labels stay recorded even when not gating. Losing them loses a feature.

## When done

Finding to `docs/findings/<date>-examine-all-pages.md`, `## Outcome` here, then
`python3 scripts/board.py finish examine-all-pages`.
