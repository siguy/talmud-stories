# Pricing the triage trade: the misses are labelling, not threshold — and the one ablation we had is contaminated — 2026-09-01

**Capability: 1 Triage.** **No API calls; no detector was run.** Everything below is read
from artifacts already on disk: the blind recall matches
(`results/recall/*_jeff2005_matches.json`), the cached Stage 1 labels
(`results/v7/event_triage_*.json`), and the two v7 runs that form the archived ablation.

Answers most of [`work/2026-08-30-triage-recall-price.md`](../../work/done/2026-08-30-triage-recall-price.md)
— FRAMEWORK §1.1's demand that a triage bar be quoted with its cost saving — and
**invalidates the method that item proposed for the rest of it.**

**Three results, in the order they matter:**

1. **Stage 1's misses are labelling failures, not threshold failures.** 10 of the 13 pages
   that killed a story were scored with **zero** narrative events, not one below the bar.
   No cheap threshold change recovers anything: relaxing to `narrative>=1` costs 4 extra
   calls per tractate and recovers **0 stories on both**.
2. **`results/v7/ablation_v7_no_triage.json` is not a no-triage run**, and the
   "triage is the single largest accuracy driver" conclusion drawn from it in 2026-02-13
   does not follow from it. `skip_triage=True` stamps every segment `DELIBERATION` and
   feeds that into Stage 2's prompt. The mechanism is **live in v11**.
3. **The full price, both tractates.** Examining everything Stage 1 discards costs 124
   extra Stage 2 calls for at most 3 stories on Ketubot (**1 per 41**, +2.0 pts) and 100
   for at most 4 on Kiddushin (**1 per 25**, +4.4 pts).

**Reproduce:** `python3 scripts/price_triage_trade.py --out results/v11/triage_recall/`
→ [`results/v11/triage_recall/triage_trade.json`](../../results/v11/triage_recall/triage_trade.json)

---

## 1. The ceiling — what re-examining the discarded corpus could return, at most

Stage 2 cannot find what it is never shown, so the stories on the blind list that died in
Stage 1 bound what any triage change can buy. Both denominators are **BLIND**.

| | Ketubot | Kiddushin |
|---|---|---|
| blind denominator | 149 | 90 |
| pages skipped | **124 / 222 (56%)** | **100 / 162 (62%)** |
| segments never examined | 1,535 | 1,459 |
| stories killed by Stage 1 | 3 | 4 |
| **ceiling: extra calls per story** | **1 per 41** | **1 per 25** |
| **ceiling: recall gain** | **+2.0 pts** | **+4.4 pts** |

This is a **ceiling, not a forecast**: it assumes Stage 2 finds every one of those stories
once shown the page, which it does not — Detection given the page survived triage is
97.9% / 97.7%. It also counts only the recall side. The precision side — how many *false*
proposals 224 extra pages would push into the review queue — is **not measured here**, and
§4 explains why it could not be.

## 2. The diagnosis — a threshold miss and a labelling miss need opposite fixes

Both look identical in the recall number. Separated by the cached labels on each page that
killed a story (N = NARRATIVE_EVENT, V = VERBAL_ACT, D = DELIBERATION, H = HABITUAL):

| story | page | N | V | D | H | kind |
|---|---|---|---|---|---|---|
| Ketubot 20a | 19b | 0 | 4 | 7 | 0 | labelling |
| | 20a | 0 | 9 | 1 | 0 | labelling |
| Ketubot 72b | 72a | 0 | 5 | 14 | 0 | labelling |
| | 72b | **1** | 1 | 12 | 0 | threshold |
| Ketubot 82b | 82b | 0 | 0 | 10 | 4 | labelling |
| | 83a | 0 | 3 | 7 | 0 | labelling |
| Kiddushin 10b | 10a | 0 | 0 | 10 | 0 | labelling |
| | 10b | 0 | 5 | 10 | 0 | labelling |
| Kiddushin 14a | 13b | 0 | 2 | 15 | 0 | labelling |
| | 14a | **1** | 0 | 18 | 0 | threshold |
| Kiddushin 21b | 21b | 0 | 4 | 17 | 0 | labelling |
| Kiddushin 69a | 68b | 0 | 1 | 9 | 0 | labelling |
| | 69a | **1** | 0 | 15 | 0 | threshold |

**10 of 13 killer pages carry zero narrative events.** Stage 1 did not narrowly miss these
pages; it read them as containing nothing that happens. Ketubot 82b — a 97-word story on
Jeff's list — is labelled 10 DELIBERATION + 4 HABITUAL, not one narrative event anywhere.

The three `threshold` pages are no help either, because **every one of them is the second
half of a story whose first half is a `labelling` page**. Both halves must be examined for
the story to be recoverable, so a threshold change alone recovers none of them.

## 3. The price of every rule we can price without an API call

Stage 1's keep-condition is a threshold over labels that are cached, so each variant can
be priced exactly. `extra calls` is against the shipped decision (which includes the Wave 1
lexical override: 6 extra Ketubot pages, 9 Kiddushin).

| rule | Ketubot examined | +calls | +stories | Kiddushin examined | +calls | +stories |
|---|---|---|---|---|---|---|
| **shipped** `N>=2 or (N>=1 and V>=2)` | 92 / 222 (41%) | — | — | 53 / 162 (33%) | — | — |
| `N>=1` | 97 (44%) | +4 | **0** | 61 (38%) | +4 | **0** |
| `N>=2 or (N>=1 and V>=1)` | 96 (43%) | +4 | **0** | 56 (35%) | +1 | **0** |
| `N>=1 or V>=3` | 167 (75%) | +70 | 2 | 114 (70%) | +54 | 1 |
| **neighbour** — shipped + the daf either side | 156 (70%) | +60 | **0** | 94 (58%) | +34 | **0** |
| **off** — examine everything | 222 (100%) | +124 | 3 | 162 (100%) | +100 | 4 |

**Nothing cheap recovers anything.** The two smallest relaxations cost almost nothing and
return nothing, which is the §2 diagnosis showing up in the cost column. Every rule that
recovers a story examines 58–100% of the corpus, at which point Stage 1 has stopped paying
for itself.

**The neighbour rule was the hypothesis §2 suggested, and it is dead.** 6 of the 7 killed
stories span a daf boundary, so it looked as though triage was losing them to two
independent coin flips — fix that by dragging in the daf either side of every kept page.
Priced: **60 extra Ketubot calls and 34 Kiddushin for zero stories.** It fails because in
every pair at least one page has no examined neighbour at all — the killed stories sit
inside runs of discarded pages, not on the edge of kept ones. Recorded here so it is not
proposed again.

## 4. The archived ablation cannot be used, and the mechanism behind it is live

`results/v7/ablation_v7_no_triage.json` reads exactly like this item's experiment already
run — v7 over all 118 Ketubot 2a–60b pages, 0 skipped, against
`results/v7/ketubot_v7_2-60.json` at 78 skipped. Same detector, same era, same 1,485
segments. Scored against Jeff's list it gives:

| | triage ON | triage OFF |
|---|---|---|
| pages examined | 40 / 118 | 118 / 118 |
| proposals | 74 | 91 |
| classified `NOT_A_STORY` | 2 | **44** |
| Jeff's stories found (44 placed, 2a–60b) | **42** | **37** |

**Turning triage off lost 5 net and 6 gross.** That is impossible for a change that only
ever adds pages: 6 of the stories it lost sit on pages *both* runs examined. So the
ablation changed something other than which pages were seen, and it did:

```python
# story_detector_v7.py:658-664  (and v8:727, v9:845, v10:1014, v11:1058 — unchanged)
elif skip_triage:
    # Generate default triage (all DELIBERATION) so detection still works
    triage_results[ref] = [EventType.DELIBERATION] * n_segs
```

Stage 2 renders that label into its own prompt — `[DELIBERATION] Seg 4:`
(`story_detector_v7.py:75`) — under a header telling the model each segment "has been
pre-classified by event type". So `skip_triage=True` does not bypass Stage 1. It tells
Stage 2, on every page, that nothing narrative happens there, and then asks it to find
stories. Post-processing reads the same stub: `rule3_v6_ensemble` demoted 22 proposals for
sitting on a page with "only 0 NARRATIVE_EVENT(s)", which is true of all 118 pages by
construction — hence 2 → 44 `NOT_A_STORY`.

**Two consequences.**

- **The 2026-02-13 conclusion does not follow from this artifact.** It is recorded in
  [`docs/capabilities/1_triage.md`](../capabilities/1_triage.md) as *"measured: triage is
  the single largest accuracy driver — 111/127 (87.4%) with, 106/127 (83.5%) without"*,
  and `tests/ablation_test.py:196` is what produced the file, via `skip_triage=True`. The
  comparison it actually ran is **true labels against uniformly false ones**, which is a
  far easier contest to win than triage against no triage. Triage may well help; this does
  not show it. Corrected in the capability history rather than edited out.
- **The defect is live in the current detector.** Every version v7–v11 carries the same
  stub, so the method this work item specified — *"run Stage 2 only on them"* — would have
  produced the same contaminated answer today. A correct bypass must pass the **real**
  cached labels and override only the skip decision.

## 5. What this does not answer

**The precision cost.** The recall side is priced; the review-queue side is not. The
ablation's 74 → 91 proposals cannot stand in for it, because those 91 were produced under
false labels (§4). Since review throughput is the project's binding constraint — Jeff's
last two rounds returned 1 verdict and 15 — the cost of examining 224 more pages is
**how many false proposals reach him per story recovered**, and that number is still
unmeasured. It needs a corrected Stage 2 run: real labels, skip decision overridden.
Successor item: [`work/2026-09-01-triage-bypass-and-precision.md`](../../work/2026-09-01-triage-bypass-and-precision.md).

## 6. What follows for the gate

FRAMEWORK §1.1 marks the ≥98% bar PROVISIONAL and "circular reasoning in a principle's
clothing". It can now be quoted with its price on both tractates:

- **Ketubot** buys 56% of the corpus skipped for 2.0 points of recall — **1 story per 41
  pages not examined.**
- **Kiddushin** buys 62% for 4.4 points — **1 story per 25.**

Kiddushin is the worse trade in both columns: it skips more and loses more. But the fix its
failing cell implies — loosen the threshold — is now **measured not to work**, on both
tractates. Closing that 4.4 points means making Stage 1 see narrative on pages it currently
scores at zero, which is a labelling problem: the opener lexicon
([`work/2026-08-30-opener-lexicon.md`](../../work/2026-08-30-opener-lexicon.md), and note
Ketubot 82b's opener `בראשונה היו כותבין` is one of the two known misses it targets), or a
different Stage 1 model. Not a threshold.

**Status of every number here: measured.** The ceilings are exact; the rule prices are
exact given the cached labels; §4's contamination is proven from source and from an
impossible result, not inferred.
