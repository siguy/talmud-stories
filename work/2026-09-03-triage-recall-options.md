---
title: Screen the untried triage-recall options before spending another tractate run
capability: [triage]
tractate: []
blocked_by: []
awaiting: []
writes: [results/recall/, scripts/mine_openers.py, scripts/pair_amudim.py, scripts/screen_discarded_pages.py, src/story_detector_v11.py, src/event_triage.py]
finding:
superseded_by:
---

# Screen the untried triage-recall options before spending another tractate run

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) §1.1 and
[`docs/capabilities/1_triage.md`](../docs/capabilities/1_triage.md), then this.

## Where the losses actually are

12 of Jeff's ~350 blind-list stories are never proposed. **7 die in triage** — the page was
never examined, so no prompt change can reach them:

| tractate | miss | opener |
|---|---|---|
| Ketubot | 20a | `בר שטיא זבין נכסי` |
| Ketubot | 72b | `אמר רבה בר בר חנה: זימנא חדא הוה קאזילנא` |
| Ketubot | 82b | `בראשונה היו כותבין` |
| Kiddushin | 10b | `וכבר שלח יוחנן בן בג בג` |
| Kiddushin | 14a | `אמר רבי יהודה: פעם אחת היינו יושבים` |
| Kiddushin | 21b | `איבעיא להו` |
| Kiddushin | 69a | `אושפזיכניה דרבי שמלאי ממזר הוה` |

**Four of the seven open with a first-person or reported-narrative formula**
(`פעם אחת`, `זימנא חדא`, `בראשונה`, `וכבר שלח`) that the five-introducer lexicon does not
contain. That is not a coincidence and it is the cheapest thing on this list.

## What has already been tried, and whether it worked

| tried | outcome | still shipped? |
|---|---|---|
| Keep-rule relaxed `N≥2` → `N≥1 or (N≥1 and V≥2)` (2026-02) | shipped, untested against a blind set at the time | yes |
| **Lexical override — 5 Hebrew introducers force Stage 2** (2026-05) | **worked: +1.1 pts Kiddushin**, recovered 45a and 53a | yes |
| Corroboration clause removed, keep on `N≥1` (2026-08-31) | **worked: Ketubot 98.0→98.7%, Kiddushin 95.6→97.8% for 8 extra calls.** On Ketubot it captures 100% of the gain available from reading the whole tractate at 1/31 the cost | yes |
| Failed triage call no longer discards the page (2026-08-31) | shipped; 0 shipped decisions changed, hazard removed | yes |
| `V≥4` clause | **rejected** — +1 Kiddushin story for 70 useless Ketubot calls, a threshold fitted to one case | no |
| Examine every page (2026-08-31) | **priced, not shipped**: 96.6% / 96.7%, +24 false proposals per tractate. → [`examine-all-pages`](2026-09-03-examine-all-pages.md) | no |

**Nothing in this capability has ever been reverted, and nothing was measured against a
blind set before shipping.** Both facts are recorded in the capability doc as a warning.

## The untried options, cheapest first

Screen in this order. Each is a separate measurement; **stop and write the finding after
each**, rather than bundling.

1. **Mine the opener lexicon.** Already an open item —
   [`opener-lexicon`](2026-08-30-opener-lexicon.md), never executed. Four of the seven
   triage misses above have openers outside the five-term list. **No API calls**: extract
   opening n-grams from the blind lists, rank story-frequency against corpus-frequency,
   and price each candidate opener by how many pages it would newly keep. Do this first.

2. **Pair the two amudim of a daf.** 16 of Jeff's 19 Ketubot stories that touch a
   discarded page survive only because *the other half of the daf pair* was kept — the
   keep decision is already effectively coupled, by luck. Make it explicit: if amud A is
   kept, examine amud B. **No API calls to price it** — the cached triage labels say
   exactly how many pages this adds and which of the 7 misses it recovers. Ketubot 20a and
   82b lost *both* halves, so this will not reach them; it may reach others.

3. **Re-run triage with the current model.** The shipped skip decisions come from a
   **cache built before several model changes**, and triage has never been run twice on
   the same pages. There is **no noise floor for this capability at all** — Lesson 22 says
   a single-run number of this kind cannot be told from a coin flip. A fresh run on
   `gemini-3-flash-preview` may move recall for free, and either way it produces the
   spread nobody has.

4. **Union of two triage runs** — keep the page if *either* run says keep. Doubles the
   cost of the cheapest stage in the pipeline to buy recall on the stage whose errors are
   invisible and permanent. Only worth doing once (3) has shown the run-to-run spread; if
   the spread is zero this buys nothing.

5. **A cheap second-chance ranker over discarded pages.** The measured alternative —
   Stage 2 on every discarded page — costs 224 calls to find 4 stories at 14.3% precision.
   Instead run a **narrow, cheap question** on discarded pages only (*"does anything happen
   to anyone on this page?"*, one call, small prompt, no few-shots), rank, and send only
   the top slice to Stage 2. Compare against the measured endpoint: same recall for fewer
   calls, or better recall for the same. This is Lesson 10's shape — narrow questions beat
   open-ended detection.

6. **Triage reads English first, like Stage 2 does.** Jeff's 46a verdict —
   *"there is no story. It is filled in by the translator"* — is a measured precision
   hazard in Stage 2. Nobody has checked which language Stage 1 leans on, or whether an
   Aramaic-only triage arm keeps a different set of pages. Screen before assuming a
   direction: it could cost recall rather than buy it.

**Do not loosen Stage 1 without producing the exchange rate first** — the standing rule
from 2026-08-30, and the reason the 56% skip rate was deliberately not "fixed".

## How you know it worked

Per option: pages newly kept, stories recovered from the list of 7, extra Stage 2 calls,
and false proposals added — all against the **blind** 2005 lists, both tractates, measured
the same day (Lesson 11).

## When done

One finding per option screened. Add an `## Outcome` here naming which shipped and which
were refuted, then `python3 scripts/board.py finish triage-recall-options`.
