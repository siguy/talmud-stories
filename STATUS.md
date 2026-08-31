# STATUS — where the project is today

**Last rewritten: 2026-08-31.** Rewritten every session, never appended.
Read this first. Companion: [`FRAMEWORK.md`](FRAMEWORK.md) — how we measure and what
counts as good enough. Language and capability names come from there.

---

## The headline

**Kiddushin's blind list has been spent, and it moved three cells — two of them in the
opposite direction from what this file said yesterday.**

**1. Kiddushin's recall deficit is Triage's, not Detection's.**
Triage measured for the first time: **95.6%** (86 of 90) while examining **38%** of pages.
Detection, measured on the pages that survived triage, is **97.7%** — against Ketubot's
**97.9%**. A difference of one story. The entire 2.7-point end-to-end gap (93.3% vs 96.0%)
is Triage, which Kiddushin skips 62% of the tractate to buy.
→ [`2026-08-31-kiddushin-recall.md`](docs/findings/2026-08-31-kiddushin-recall.md)

Yesterday this file called 93.3% "the first like-for-like comparison of the two
tractates." It was like-for-like on the *pipeline*, not on the capability. **Detection
generalizes across tractates** — the first evidence either way, since Ketubot was the
only blind list we had.

**2. Kiddushin's boundary score was 85% / 91% all along, not 60% / 73%.**
The old figure came from 15 correction targets with a ±7-point noise band. Built blind
from the 2005 list — **176 targets, 130 scorable** — Kiddushin clears the ≥75% gate and
scores **above Ketubot's 80% / 84%**. It is above the gate on the *shipped untrimmed*
output alone (77% / 85%).
→ [`2026-08-31-kiddushin-boundary-set.md`](docs/findings/2026-08-31-kiddushin-boundary-set.md)

**The noise demonstration is exact.** Across two identical-code runs **one target**
changes verdict — Kiddushin 66b seg 0, NEAR→HIT. On 15 targets that flip is 6.7 points and
reads as a result; on 130 it is 0.77 and reads as nothing. Same noise, same single target.

**3. The clause-edge ceiling is not a Ketubot artifact.** 88% of Jeff's Kiddushin
boundaries land on a clause edge against Ketubot's 87%. Split by direction: **ends 95% /
96%, starts 80% / 79%**. So the residual 12-13% that no clause-anchored prompt can reach
is almost entirely a **start** problem — which is where a finer splitter would have to pay
for itself.

**What this costs to believe: one run per tractate on recall.** Boundaries now have a
measured noise floor on both tractates; **recall still has none anywhere**, because
measuring it means re-running the detector. Both recall figures are single runs of a model
known to move ~3% of its own output (Lesson 22).

## Scoreboard — capabilities per [`FRAMEWORK.md`](FRAMEWORK.md) §1

| capability | metric | Ketubot | Kiddushin | gate |
|---|---|---|---|---|
| **[1 Triage](docs/capabilities/1_triage.md)** | stories surviving, BLIND | **98.0%** at 44% of pages ✓ | **95.6%** at 38% of pages — **NEW** ✗ | ≥98% *(provisional)* |
| **[2 Detection](docs/capabilities/2_detection.md)** | recall given the page survived triage, BLIND | **97.9%** ✓ | **97.7%** ✓ — **NEW** | ≥95% *(provisional)* |
| | *end-to-end recall (triage × detection), BLIND* | *96.0% loose / 87.9% strict* | *93.3% loose / 83.3% strict* | — |
| | *golden recall, CIRCULAR* | *92.1% (90.9% before the Mishnah-tagger fix)* | *95.3%* | — |
| **[3 Classification](docs/capabilities/3_classification.md)** | precision, CIRCULAR, harness | **89.2%** ✓ | **85.3%** ✓ | ≥85% *(provisional)* |
| **[4 Boundaries](docs/capabilities/4_boundaries.md)** | hit / near, BLIND | **80% / 84%** ✓ (ceiling ~87%) | **85% / 91%** ✓ — **NEW** (ceiling ~88%) | ≥75% *(provisional)* |
| **[5 Review](docs/capabilities/5_review.md)** | days per tractate | not started | not started | days, not weeks *(derived)* |
| **[6 Publication](docs/capabilities/6_publication.md)** | — | not started | not started | — |

**Four of five gates are provisional** — see FRAMEWORK §2b. They compose
(`triage × detection = end-to-end`), so only the end-to-end number needs defending, and
that is a product decision, not a technical one. Two questions are open there: one for
Simon, one for Jeff.

**One cell now sits below its gate, and it is the one that matters most: Kiddushin
Triage, 95.6% against ≥98%.** That is the only failing cell on the board, and per
FRAMEWORK §2 it is the capability whose errors are invisible and permanent. It is also the
gate FRAMEWORK itself calls "circular reasoning in a principle's clothing" — set to
Ketubot's own value, on the tractate that happens to skip *less*. So the honest reading is
not "Kiddushin triage is broken" but **"the trade is priced differently on the two
tractates and nobody chose either price"**: Kiddushin gives up 2.4 more points of recall
for 6 more points of corpus skipped, about one story per 1.5 points of pages not examined.
That is the open end-to-end question for Simon (FRAMEWORK §2b), now with a number attached.

**The Detection row is quoted differently than it was yesterday, on purpose.** The
headline is now recall *given the page survived triage*, because the end-to-end figure
charges Triage's losses to Detection as well and the two capabilities have separate gates.
Both readings are in the table.

Classification
measured 2026-08-30 on the current detector with the immutable harness: Ketubot 89.2%,
Kiddushin 85.3% — correcting an earlier claim in this file that we had no current number.

**But the 86 / 68 Classification numbers were never Classification numbers.** They counted
every rejection, whatever Jeff objected to. Sorting the notes: most rejections are
**boundary, merge or confidence-level** complaints — three other capabilities pooled into
one figure. Separated, both tractates land near 92-95% and the gap between them mostly
disappears. Review-round precision is therefore quoted as a **range**, because unreadable
notes set its width. → [`docs/findings/2026-08-30-detection-classification-ruler.md`](docs/findings/2026-08-30-detection-classification-ruler.md)

**We have a harness point estimate, not a review-round one.** The 89.2% / 85.3% above come
from `evaluate_golden.py` against the golden. What the *review rounds* still cannot give is
a point estimate, because the reviewer never recorded *which thing* he was rejecting. That
fix is a review-UI change, `NEXT/04`, not more inference over free text.

**Detection is softer than 96% under a strict test.** The published test credits a
proposal anywhere in a 14-segment search window. Requiring it to overlap a segment the
story actually occupies gives 87.9% Ketubot / 83.3% Kiddushin. The 12 Ketubot stories in
the gap are **cross-page stories whose text sits on a continuation daf where we proposed
nothing** — 17b, 50a and 51a each carry zero proposals.

## What changed today

- **Kiddushin Triage measured, and it owns the whole recall gap.** 95.6% (86/90) at 38%
  of pages; Detection given triage is 97.7% vs Ketubot's 97.9%. Cause split of the 6
  misses: **4 triage-discarded, 2 examined-and-nothing-proposed.** `triage × detection =
  end-to-end` re-checked and holds on a second tractate (0.956 × 0.977 = 0.934).
  → [`2026-08-31-kiddushin-recall.md`](docs/findings/2026-08-31-kiddushin-recall.md)
- **A blind Kiddushin boundary set: 176 targets, noise 7 points → 0.77.** 85% / 91%,
  above the gate and above Ketubot. The old 60% / 73% is retired, not averaged.
  → [`2026-08-31-kiddushin-boundary-set.md`](docs/findings/2026-08-31-kiddushin-boundary-set.md)
- **The clause-edge ceiling generalizes (88% vs 87%) and the residual is a *start*
  problem** — ends are 95-96% clause-aligned on both tractates, starts 79-80%.
- **Two Kiddushin stories are proposed and then classified `NOT_A_STORY`** (44a, 58a),
  which is why the figure reaching output is **91.1%**, not 93.3%. Both are
  rabbis-in-conversation passages — the material under `jeff:speech-act-policy`. Ketubot
  loses nothing this way in the current run.
- **Kiddushin 81b carries two of Jeff's stories, not one.** Every prior document discusses
  only the appendix case (R. Meir / R. Tarfon). The second — Rav Hanan of Nehardea, segs
  4-10, 100% text alignment — is blind, sits on an examined page, and was **never
  proposed**.
- **Wave 1's lexical override priced against a blind set for the first time: +1.1 points
  of triage recall** (one story, Kiddushin 49b) for 9 extra Stage 2 calls. Stage 1 alone
  would skip 109 of 162 pages; the shipped figure is 100.
- **`STATE.md`'s Triage and Detection cells are derived now, not pointers.** The recall
  harness writes `survived_triage` per story, so the generator reads the number instead of
  naming a file — closing one of the three cells its own footnote calls a known gap.
  Detection is quoted there **given the page survived triage**, with the end-to-end figure
  beneath it.
- **Four latent measurement defects fixed before they could be quoted, and three are the
  same mistake: a literal standing in for a property.** `score_boundary_targets.py`
  classified blind-vs-corrections by a *filename*, so the new Kiddushin set would have been
  reported as a corrections set — Lesson 24's pooling, arriving through a string
  comparison. `board.py` decided whether a tractate had a triage number with
  `if t == "ketubot"`, so Kiddushin's cell would have gone on reading "never measured"
  however many times it was measured. `measure_recall_vs_expert_list.py` had no committed
  triage-recall measurement at all — the published 98.0% was computed by hand while writing
  FRAMEWORK. And the fourth: changing its `load_detected` signature broke `build_ruler.py`,
  which the suite caught immediately; the caller now unpacks by name so the next such change
  fails loudly rather than silently.

- **Lesson 35** — a composed metric names the pipeline, not the capability. Lesson 30's
  shape one level up: there the pooling was across *reasons for a rejection*, here across
  *stages of a pipeline*. Both send the fix to the wrong place.

**The previous session's changes** (the boundary ruler rebuild, the Mishnah-tagger fix,
the Ketubot 77a re-diagnosis, the detection/classification ruler) are recorded in
[`docs/capabilities/`](docs/capabilities/) and their dated findings. This section is
rotated each session, not appended.

## Waiting on Jeff — email sent 2026-08-30

**The question:** when a ruling is what makes a passage a story at all, is that ruling
part of the story we display, or the discussion that follows it? His 2005 lists keep it;
his review notes say cut it. Blocks the end rule for capability 4.
→ draft: [`comms/sent/2026-08-30-email-jeff.md`](comms/sent/2026-08-30-email-jeff.md)

**To add when we next write — five items:**

1. At what error rate does reviewing our output become worse than working from scratch?
   That number sets the Classification gate and only he can answer it.
2. **Do stories inside the Mishnah count?** We currently delete them. Two genuine Ketubot
   cases: 14b seg 11 and 77a seg 8 (the Sidon tanner). His blind 2005 list contains no
   Mishnah-only story; his review rounds accepted both into our golden — his own two
   sources disagree, exactly as on the boundary question.
3. **When we send results for a new tractate, ask him to keep his appendix separate.**
   In Kiddushin the appendix entries were merged into the list and cost us five of its
   stories as blind ground truth. Not urgent — Gittin, Yevamot and Eruvin are clean until
   we run there — but it must be said *before* the first review round, not after.
   → `work/2026-08-30-kiddushin-parse-open-calls.md` item 1b
4. A correction we owe him: the email said Ketubot 77a is a story "our own set has" — it
   is not. Our golden holds a *different* 77a story (the Sidon tanner, seg 8); his is at
   segs 13-14. The substance stands (we do miss his), the claim did not. Pairs naturally
   with item 2 — same daf.
5. **Two of his own Kiddushin stories are ones we throw away as `NOT_A_STORY`**, and they
   are the cleanest test case yet for `jeff:speech-act-policy` — real passages he listed,
   which our current criteria reject. **44a**, `ר' אסי לא על לבי מדרשא` (R. Assi did not
   go to the study house), and **58a**,
   `בעא מיניה ר' חייא בר אבין מרב הונא` (R. Hiyya b. Avin asked R. Huna). Both are
   rabbis-in-conversation. Neither is in our golden, so no round has ever put them in
   front of him. Show him these two rather than restating the policy question in the
   abstract. Measured 2026-08-31; they are why Kiddushin's recall reaching output is
   91.1% and not 93.3%
   ([`kiddushin_recall` §4](docs/findings/2026-08-31-kiddushin-recall.md)).

**Before any next review round:** `validation/generators/generate_wave4_review_ui.py`
still reads `results/v10/wave4/` — the **reverted** char-offset span data — deliberately,
so the regenerated page stayed comparable to what Jeff actually saw during brief 04's
verification. Point it at `results/v10/wave4_notrim/` before showing him anything new.

## Next — items in [`work/`](work/), each self-contained

**Kiddushin's blind list is now largely spent.** Two of its three items are done; only
`kiddushin-comments-harvest` remains, and it is the one that needs no list at all — Jeff's
10 anchored remarks, each carrying the exact passage he was looking at.

**What today's numbers point at next, in order:**

1. **`triage-recall-price`** — promoted from "lower value". It was the cheapest item on
   the board yesterday and is now the one the scoreboard's only failing cell asks for.
   Re-run Stage 2 on the discarded pages (124 Ketubot, 100 Kiddushin, text already on
   disk) and produce the exchange rate that FRAMEWORK §1.1 says a triage bar is meaningless
   without. It is also the only route to the single number that would settle four
   provisional gates at once.
2. **`opener-lexicon`** — mine openers rather than invent them. Both remaining Kiddushin
   Detection misses and three of the four triage losses open on frames outside the five
   hand-written introducers, and the override is now measured to be worth +1.1 points of
   triage recall when it fires.
3. **`kiddushin-comments-harvest`** — unchanged, and now better targeted: several of the
   10 remarks are boundary corrections, and there is finally a Kiddushin boundary gate
   that can tell whether acting on them helps.

```
kiddushin-list-parse DONE ─┬─ kiddushin-recall        DONE   (triage + detection)
                           ├─ kiddushin-boundary-set  DONE   (176 blind targets)
                           └─ kiddushin-comments-harvest     still open

start any time:   review-verdict-axes · kiddushin-12a-dedup · opener-lexicon
now the priority: triage-recall-price
open calls:       kiddushin-parse-open-calls   (denominator 90; item 1b is for Jeff)
incomplete:       golden-completeness
```

All items are `work/2026-08-30-<slug>.md`. Finished ones are in
[`work/done/`](work/done/) with an `## Outcome` — **never deleted**, which is how
"what has already been done" stays answerable.

| item | capability | needs | Jeff? |
|---|---|---|---|
| **[triage-recall-price](work/2026-08-30-triage-recall-price.md)** — price the trade over the discarded pages. **Now the highest-value item**: Kiddushin Triage is the board's only failing cell and this is what its gate is missing | 1 | — | no |
| **[opener-lexicon](work/2026-08-30-opener-lexicon.md)** — mine openers, never invent them. Targets the triage losses directly | 1, 2 | — | no |
| **[kiddushin-comments-harvest](work/2026-08-30-kiddushin-comments-harvest.md)** — Jeff's 10 anchored remarks | 3, 4 | — | no |
| **[review-verdict-axes](work/2026-08-30-review-verdict-axes.md)** — make the reviewer say *which* thing is wrong; the only route to a Classification point estimate | 3, 5 | — | no |
| [second-story-guard](work/2026-08-30-second-story-guard.md) — stop discarding a second story sharing a segment | 4 | — | *awaiting* |
| [kiddushin-parse-open-calls](work/2026-08-30-kiddushin-parse-open-calls.md) | ground truth | — | **1b** |
| **[golden-completeness](work/2026-08-30-golden-completeness.md)** — fold in every verdict (the ruler names all 12) | 3, ground truth | — | no |
| [kiddushin-12a-dedup](work/2026-08-30-kiddushin-12a-dedup.md) — one detection covering two stories | 2 | — | no |
| [story-criteria](work/2026-08-30-story-criteria.md) — was Wave 6; 6a runs now, 6c blocked by design | 3 | comments-harvest | **6b** |

**Done 2026-08-31** — `kiddushin-recall` · `kiddushin-boundary-set`.
**Done 2026-08-30** — `capability-histories` · `ketubot-77a` · `fetch-new-tractates` ·
`ketubot-golden-additions` · `kiddushin-list-parse` · `review-ui-display-asymmetry`.

\* `second-story-guard` is **not blocked**: deleting a whole second story is wrong
whatever Jeff answers about where an entry ends. Its *value* depends on his answer; the
work does not. That is `awaiting`, not `blocked_by`.

## Where things live — one job each

| file | its one job |
|---|---|
| **[`STATE.md`](STATE.md)** | **generated instrument panel** — coverage matrix, gates, what is in flight. Never edit it; run `python3 scripts/board.py`. |
| **`STATUS.md`** | where we are, in words: judgment, hazards, what is *indicated* rather than measured. Rewritten each session. |
| **[`FRAMEWORK.md`](FRAMEWORK.md)** | the six capabilities, how each is measured, what the gates are and **why**. Carries no current values. |
| [`WORK.md`](WORK.md) | generated board — open items, in flight, done. |
| [`work/*.md`](work/) | one self-contained item per ready task. When done: add `## Outcome` and `git mv` to [`work/done/`](work/done/) — **never delete**. |
| [`lessons/`](lessons/) | one file per lesson, L-001…L-030. Numbers are permanent. |
| [`docs/findings/`](docs/findings/) | dated findings. Corrected by a **new** dated finding, never edited to look as though they were always right. |
| [`docs/history/`](docs/history/) | plans and approach docs, superseded by what they produced. |
| [`docs/capabilities/`](docs/capabilities/) | per-capability history: tried, reverted and why, current best, distance to gate, ceiling, untried. **Read before opening work on a capability.** |
| [`comms/JEFF.md`](comms/JEFF.md) | every open question (with the slug items name in `awaiting:`), corrections owed, and the sent log. |
| `validation/feedback/jeff_*_ledger.md` | everything Jeff has **said**, and its disposition. Different job from JEFF.md, and kept. |
| `docs/golden/` | **data only** since 2026-08-30, plus a redirect table for its old paths. |
| `CLAUDE.md` | how to work in this repo, and the route to read things in. Not status. |
| `FOR_SIMON.md` | the plain-English narrative. |

**The rule:** status here and nowhere else. Findings in a dated `docs/findings/` file.
Rules in `lessons/`. Ready work in `work/`. Never append status to a plan.

## Ground truth on hand

```
BLIND   (can measure recall)
  Ketubot    149 stories (2005 list) · 294 derived boundary targets, 229 scorable
  Kiddushin   90 stories, MEASURED  -> results/expert_lists/kiddushin_2005.json
                 95 parsed, minus 1 he added himself, minus 4 appendix entries we
                 proposed ourselves (circular; counting them could only flatter).
                 The 5th appendix case (81b) we never proposed, so it STAYS -- it
                 can only count against us. Denominator 90; strictly blind 89.
                 176 boundary targets, 130 scorable  <- BUILT 08-31, from the 89
                 -> tests/expert_boundary_targets_2005_kiddushin.json
                 The two filters differ ON PURPOSE: recall uses `counts_for_recall`
                 (90, keeps 81b), boundaries use `blind` (89, drops all 5 appendix
                 cases). A boundary target must be an extent JEFF chose.
  Gittin 112 · Yevamot 102 · Eruvin 73   <- PRISTINE. We have never run the detector on
                                            these, so nothing of ours can have been
                                            merged in. Each needs its own parse; a
                                            detector run there is a clean floor test.
CIRCULAR (precision and consistency only — never recall)
  Ketubot   golden: 187 entries, 164 accepted (23 NOT_A_STORY) — v7 + v9, many rounds
  Kiddushin golden:  96 entries,  85 accepted (11 NOT_A_STORY) — v7 only, ONE round
                     16 verdicts from the May-26 and Jul-06 rounds are NOT folded in
  70 boundary corrections across 8 review rounds (27 Kiddushin, 15 of them scorable)
     -- report these APART from the blind sets, never pooled (Lesson 24). On Kiddushin
        the two disagree on 4 of the 14 boundaries they share.
  10 Kiddushin review remarks, each anchored to its passage (NEXT/08)

SEFARIA TEXT on hand (text only — no detector has been run on these)
  Ketubot · Kiddushin                     results/v7/, results/v10/wave4_notrim/
  Gittin   2a-90b   178 dapim  2,990 seg  results/sefaria/gittin.json   <- NEW 08-30
  Yevamot  2a-122b  242 dapim  3,865 seg  results/sefaria/yevamot.json  <- NEW 08-30
  Eruvin   2a-105a  207 dapim  3,645 seg  results/sefaria/eruvin.json   <- NEW 08-30
```

**Every reference in Jeff's Gittin, Yevamot and Eruvin lists resolves to a fetched
page** — ranges derived from Sefaria's own index, not guessed, and verified by
`python3 scripts/fetch_tractate_pages.py --verify-only`. The three entry counts
above are now **measured** (112 / 102 / 73 reproduce exactly), and all three lists
are genuinely blind — 0 English review comments, 0 `הוספתי` markers, unlike Kiddushin's.

`scripts/build_boundary_testset_2005.py` **can** build blind boundary sets for these
three — correcting this file's 2026-08-30 claim that it could not. Its `load_units` reads
`results/sefaria/*.json` as well as the detector outputs, and returns 2,990 / 3,865 /
3,645 segments for Gittin / Yevamot / Eruvin (verified 2026-08-31). What is missing is the
other half: each list must first be parsed to JSON the way Kiddushin's was, because
`--expert-json` is the only input the builder now accepts for a list that is not the
Ketubot `.doc` (Lesson 28).

**But their per-daf attribution has a defect, in the same family as Kiddushin's.**
`parse_expert_doc` only matches single-amud headers, so **21 stories** under two-amud
headers (`סה ע"ב-סו ע"א`) are silently credited to the *preceding* daf — Gittin 11,
Yevamot 7, Eruvin 3. Entry counts are unaffected; **daf-level recall on these three
would be wrong until it is fixed.** One Gittin header (`יד ע"ד`) uses amud *dalet*, a
Yerushalmi form with no Bavli equivalent. `--verify-only` lists all 21.

**Quote golden counts the same way.** "Ketubot 182 · Kiddushin 85" compared entries
against accepted-only. Use 187/96 or 164/85, never one of each.
