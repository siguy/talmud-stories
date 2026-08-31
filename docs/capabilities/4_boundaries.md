# Capability 4 — Boundaries

**Definition:** for a confirmed story, decide the exact extent of text to display — see
[`FRAMEWORK.md` §1.4](../../FRAMEWORK.md).
**Gate:** ≥75% hit+near (PROVISIONAL — the loosest of the six)
**Current:** **Ketubot 80% hit / 84% hit+near** on the 229 scorable targets derived from
Jeff's 2005 list (**BLIND**); untrimmed segment boundaries alone score 75% / 83%.
**Kiddushin 60% / 73%, ±7 points**, on 15–16 correction targets (**CIRCULAR + biased**).
Measured 2026-08-30.

*Written 2026-08-30 from the sources in `tasks/NEXT/00`. History, not status.*

---

## Waves are not capabilities

**Waves 4, 5 and 5b are entirely this capability.** Wave 2's start-snap and end-trim are
here too (they are usually filed under "Kiddushin fixes"). Nothing in Wave 6 belongs
here. Two failures usually filed elsewhere belong here: Kiddushin 53a and 71a are
**Detection hits with the wrong extent**, not Detection misses
([`appendix_provenance_correction`](../golden/v11/appendix_provenance_correction_2026-08-30.md)),
and a large share of the review-round rejections that were counted against Classification
were boundary complaints (Lesson 30).

This capability has the longest failure record in the project. That is not an accident:
it is the only one where a wrong answer is **visible to the reader**, so it attracted
five successive mechanisms, and four of them were wrong.

---

## What we tried

| when | what | outcome | evidence |
|---|---|---|---|
| 2026-01-20 | **Fuzzy text-anchor extraction** — match the model's quoted boundary words into the page with `difflib`, 3–5 word chunks, 50–60% similarity, estimate the missing edge | shipped; fixed "boundaries not found in text" errors. Superseded by segment-based detection days later | `2e4e969` |
| 2026-01-25 | Review UI trimmed to 1 segment of context either side of the story | shipped | `81bb7de` |
| 2026-02-13 | **Stage 4a boundary refinement** — trim DELIBERATION segments off story edges using the triage event types | shipped; 4 stories trimmed. Still in the pipeline, and it is why Wave 2's end-trim later found nothing to do | `cfaca8a` |
| 2026-02-22 | **v7.1 ruling guard** — do not trim a trailing DELIBERATION segment if it contains a ruling verb **and** names a character from the story | shipped, in response to Jeff's "stories missing their resolving ruling" | `fcc5af9` |
| 2026-02-22 | Prompt rule: *the rabbi's ruling that resolves the narrative case is part of the story*; abrupt endings are not weakeners | shipped | `81cfd82` |
| 2026-05-24 | **Wave 2 Issue #3 — start-boundary snap** to a canonical introducer, forward within 3 segments or back by one | shipped. Fired **3×**, all "extend back", all textbook `ההוא ד` / `ההיא` openers (Kiddushin 12a 14→13, Ketubot 67b 5→4, 85a 9→8). All three are rabbinically correct by inspection; **none had been flagged by Jeff**, so the unchanged golden penalised two of them: Ketubot composite −0.0002 | `1c4d18d`, Lesson 13 |
| 2026-05-24 | **Wave 2 Issue #4 — end-boundary trim** of trailing stam markers | **fired 0 times.** Two reasons, both measured: Stage 4a already trims trailing stam at segment level, and **all 16 boundary cases Jeff flagged on Kiddushin are text-internal** — the commentary sits inside the last segment, not in a separate one | `1c4d18d`, Lesson 12 |
| 2026-05-25 | **Wave 3 Item 4 — regex text-internal spans.** Search the first segment for the earliest canonical introducer and the last for the latest trailing-stam marker; emit `text_span_start` / `text_span_end` as char offsets. Score-neutral by harness design | shipped on a **10/17 audit** against Jeff's flagged cases | `dcefb30` |
| 2026-06-03 | **Jeff's verdict on Item 4** | **MIXED, and it killed the approach.** It worked on 5 canonical `ההוא`/`ההיא` openers and **over-trimmed 7 other stories**, where the same markers (`אלא`, a rabbi's name) *were* the story content. Jeff, verbatim: *"crude criteria, such as the word אלא or a rabbi's name automatically signalling the story's end."* Net golden change ≈ 0 | `402ed0d`, Lesson 15 |
| 2026-06-15 | **Wave 4 (v10) — LLM character offsets.** Following Lesson 15's own advice ("let the model judge"), a per-story Gemini call returns `{start_offset, end_offset}` in nikud-stripped coordinates, mapped back | shipped on **14/14** of a held-out fixture from Jeff's May review, 0/6 violations on a production gate, 262 stories, 0% skip rate, composites unchanged | `c430cc5` |
| 2026-07-06 | **Jeff reviews 15 Wave 4 Kiddushin stories** | **11 of 15 incorrect**, one cut **mid-word inside a Biblical quotation** (30a seg 7) | [ledger](../../validation/feedback/jeff_2026-07-06_feedback_ledger.md) |
| 2026-08-28 | **Full audit of every emitted cut** — not the 15 Jeff saw, all 189 across all three v10 outputs | **measured, and ~10× worse than the sample implied: 104 of 189 cuts (55%) sever a Hebrew word; only 7 (4%) land on a clause edge.** Cross-tab of Jeff's verdicts: of the 9 reviewed stories that were **trimmed**, **9 were wrong and 0 right**; of the 6 untrimmed, 4 were right. **The mechanism has zero observed successes** | `54d6b90`, [`wave4_span_failure_audit`](../golden/v10/wave4_span_failure_audit_2026-08-28.md), Lesson 18 |
| 2026-08-28 | **Wave 4 REVERTED**, spans stripped to segment-level, plus a permanent structural gate | shipped. Ketubot composite **0.9171 → 0.9171**, proven by running the harness both ways rather than reasoning about it; 0 mid-word cuts remain; `scripts/audit_text_spans.py --strict` now fails a build on any mid-word cut | `54d6b90`, Lesson 19 |
| 2026-08-30 | **Wave 5 — clause selection.** The model picks a punctuation-delimited **clause index**; we compute the offset. A mid-word cut becomes structurally impossible, enforced by an assertion that fails the build. Split on `. : ? !` only, never commas (the comma is the corpus's most frequent mark, 4,855 vs 3,959 periods, and Jeff's Kiddushin 12b seg 4 correction is a story continuing past one) | shipped. Model A/B on Kiddushin: **both arms 0 mid-word cuts and 100% clause-edge**, against 55%/4% for Wave 4. `gemini-2.5-flash` over-trims; `gemini-3.7-flash`+HIGH under-trims; accuracy a wash, so the **under-trimming failure mode was chosen** — over-trimming is unrecoverable | `cf2c18d` |
| 2026-08-30 | **Wave 5 Step 1 — run Ketubot for the first time.** Wave 5 had only ever run on Kiddushin, so 36 of 52 expert targets scored N/A | scorable targets **16 → 35**. Pooled: no-trim 11% HIT / 29% HIT+NEAR → clause spans **40% / 63%** | `fe707cb` |
| 2026-08-30 | **Wave 5 Step 2 — the summary bug.** The span prompt read `story['summary']`, present on **0 of 262** stories, so 100% fell through to a joined event list that stops before the story's resolution — while 35 of 52 targets are ENDs | fixed (`one_sentence_summary` first, one shared `story_summary()`). Moved **14 of 262 boundaries (5%)** and **zero of the 35 scored targets** | `fe707cb`, [`wave5_summary_fix`](../golden/v11/wave5_summary_fix_2026-08-30.md) |
| 2026-08-30 | **The noise floor, measured for the first time in the project** — same code, same input, run twice | **measured: 3% of boundaries move on identical code**, and the scoreboard reads **50% vs 56% HIT** on the 16 Kiddushin targets, because one target flipped NEAR→HIT from nondeterminism. One target = 6.25 points | `fe707cb`, Lesson 22 |
| 2026-08-30 | **Wave 5b — per-clause role labelling**, then compute the boundary from the labels: replaces "which clause?" with a structured judgment | **BUILT, REVIEWED, SHELVED.** Three independent reviews: the idea is right, the execution is not. 433 lines committed *with* their defects so they would not be lost | `1582e07`, [`wave5b_review`](../golden/v11/wave5b_review_2026-08-30.md), [`wave5b_decision`](../golden/v11/wave5b_decision_2026-08-30.md) |
| 2026-08-30 | **Wave 5b Step 0 — a failed call is no longer stamped as a judgment** (failure-injection test written first, watched fail, then fixed) | fixed. With every call failing: before `{kept_full: 6, no_split: 2, skipped: 6}` = 14 counts for 6 stories, 6 fabricated speech profiles, 0 `needs_review`; after `{no_split: 1, skipped: 5}` = 6 counts, 0 profiles, 5 `needs_review`. Guarded by `tests/test_wave5b_runner_outcomes.py` | `d473944`, Lesson 21 |
| 2026-08-30 | **The boundary ruler rebuilt** — corrections harvest widened 52 → 70, `quote_polarity` modelled, and a **neutral 294-target set built from Jeff's 2005 list** by sequence-aligning his own edition against the Sefaria Hebrew (147 of 149 stories align, median 99% of his letters matched in order) | **measured: gradeable targets 35 → 249; noise floor 7 points → 0.** The two sources, twenty years apart, agree on **84%** of their 32 overlapping boundaries | `6be55d7`, [`boundary_ruler_rebuild`](../golden/v11/boundary_ruler_rebuild_2026-08-30.md), Lesson 23 |
| 2026-08-30 | **End-trim cap at 3 clauses** — every end regression cut too *early* (drifts −6 −6 −6 −6 −4 −3 −2 −2 −2 −1); caps of 1/2/3 score identically | shipped at 80%/84% → **81%/86%** on the neutral ruler… | `2e4fd89` |
| 2026-08-30 | …then **REVERTED** once Simon settled which expert standard we build for | see below | `a7659d3`, [`trim_asymmetry`](../golden/v11/trim_asymmetry_2026-08-30.md), Lesson 24 |

## What we reverted, and why

**1. Wave 3's regex text-internal editor (2026-06-03).**
Surface markers are diagnostic of *structure* 30–50% of the time and of *story content*
the other 50–70%. `אלא` and a rabbi's name end a story sometimes and are the story other
times, and no regex can tell which. The 10/17 audit that justified shipping was drawn
from Jeff's own prior corrections — the very cases the regex was implicitly built to fit
— so its precision on that sample predicted nothing (Lesson 15, same shape as Lesson 9).
**Do not build another deterministic post-processor for a text-internal semantic
decision.**

**2. Wave 4's LLM character offsets (2026-08-28) — the project's largest single
failure.**
Lesson 15 said "let the model judge." Wave 4 did, and implemented the judgment as a
**character offset**. The nikud-stripping position map was proven faithful
(`stripped[i] == hebrew[map[i]]` for every `i`), so the bad cuts came from the model's
raw numbers. **LLMs reproduce text reliably and count characters unreliably** (Lesson 16).

Three separate rules came out of this one revert, and all three are now enforced in code:

- **Lesson 16** — never ask a model for a character offset; anchor to a real text unit.
  Enforced by Wave 5's clause selection plus a build-failing assertion.
- **Lesson 18** — an expert sample *locates* a defect and never *sizes* it. Jeff's 8
  flagged stories were 8 of 104 corrupt cuts; ~100 more sat in the two Ketubot files
  nobody had reviewed. Enforced by `scripts/audit_text_spans.py --strict`.
- **Lesson 19** — revert to the safe default **before** building the replacement. Cost
  $0, no API calls, score-neutral (0.9171 → 0.9171, proven by running the harness both
  ways). The risk is asymmetric: an over-inclusive segment boundary is recoverable by a
  reader; a mid-word cut is not. On Jeff's own sample, shipping untrimmed would have
  scored 4/6 instead of 4/15.

**3. The end-trim cap (2026-08-30, shipped and reverted the same day).**
It scored better — on the wrong ruler. Reading the actual Hebrew that Wave 5 cut split
the 12 end regressions in two: **~9 are definitional**, where the model removed
stam-Talmud legal give-and-take exactly as our prompt instructs and Jeff's 2005 unit
simply included it; **~3 are genuine over-cutting.** The two rulers encode two different
tasks — in 2005 Jeff was building a story *index*, so the legal frame belonged; in 2026 he
is reviewing a tool that *displays* stories and says *"the legal discussions that follow
the story need not be quoted."* Start boundaries agree 7/7; end boundaries 16/19
(Lesson 24).

**Simon settled it: we build for Jeff-2026.** That re-reads the 2005 list as an **upper
bound** rather than a target — ending earlier than his boundary is expected, ending later
is wrong under both standards. Scored that way on 105 Ketubot ends:

| variant | exact | earlier (expected) | **LATER (wrong either way)** |
|---|---|---|---|
| no trimming | 79 | 3 | **23** |
| Wave 5, uncapped | 78 | 17 | **10** |
| Wave 5 + cap at 3 | 80 | 9 | **16** |

**End-trimming is good after all** — it more than halves the definite overshoots — and
the cap undoes exactly the trims that fix them. Removed, with a comment in
`src/story_detector_v11.py:575` so it is not re-invented.

**4. Wave 5b — shelved, not reverted, and deliberately committed with its defects
(2026-08-30).** Three reviews agreed the design is right and the execution was not:
a failed call recorded as `clause_kept_full` (which also means *"the model judged all of
this in-story"*), a scorer that rated a **completely dead run** at 6%/38% — identical to
the legitimate baseline — a `reassemble()` path diverged from the fresh one, and a prompt
builder that string-split on `---` and silently cut a 3,351-char prompt to 489. One claim
in the plan was also false: *"English sentences nest over Hebrew clauses"* is wrong on
21% of boundary segments, and the cross-language check depended on it.

**The decision was to fix the measurement first — about 10 lines instead of the 433
already written.** The cheap path was run, and its precondition came back answered:
a properly-fed one-shot still sits at 40% HIT / 63% HIT+NEAR, unmoved by the summary fix.
But the same session found the gate could not resolve a change of that size, so **the
revival question is now different from the one the plan asked**: not "is 50% good enough"
but *"is the remaining 20% reachable at all, given 13% of boundaries are not on clause
edges?"* The salvage list is `tasks/NEXT/03` and `wave5b_review_2026-08-30.md`.

**5. A revert that never happened, and should be remembered as such: the old ruler.**
The corrections-only test set was not wrong so much as **structurally incapable** of
seeing a regression — every question was a case Jeff had flagged as wrong, so trimming
could only help. Its own builder header said so. We quoted its numbers anyway, because it
was the only ruler we had, and it told us Wave 5 **doubled** Ketubot 61-112 (33% → 67%).
The neutral ruler, same runs and same day, says the plain segment boundary was **already
79% right** and hit+near went 85% → 84% (Lesson 23).

## Current best — the exact configuration

- **Shipped output right now: segment-level boundaries with no sub-segment spans** —
  `results/v10/wave4_notrim/*.json`. This is the honest default that the Wave 4 revert
  restored, and it is what the goldens and the review UI read.
- **Best measured mechanism:** Wave 5 clause selection in `src/story_detector_v11.py`
  (`extract_text_spans_via_clauses`, `_llm_clause_span_for_story`, `story_summary()`),
  model `gemini-3.7-flash` with `thinking_level=HIGH`. Outputs:
  `results/v11/wave5_summaryfix/`. **The end-trim cap is removed**
  (`src/story_detector_v11.py:575` records why).
- **Structural guarantees, not conventions:** clauses split on `. : ? !` only; a
  build-failing assertion that every emitted boundary sits at a clause/word edge; and
  `scripts/audit_text_spans.py --strict` as a ship gate, with the v10 baseline recorded
  in its docstring.
- **Rulers — report them separately, never pooled (Lesson 24):**
  - `tests/expert_boundary_targets_2005.json` — **294 targets, BLIND**, from Jeff's 2005
    list; 229 scorable on Ketubot. The primary measure.
  - `tests/expert_boundary_targets_v2.json` — **70 targets, CIRCULAR and biased** (all
    are cases we got wrong). Answers "did we fix the known failures?" and nothing else.
    Carries `quote_polarity` and `harvest_rule`; `mixed`/`unclear` targets are flagged
    `needs_human` and skipped by the scorer.
  - Scorer: `scripts/score_boundary_targets.py`, `--targets` pools files and
    `--by-source` reports them apart.
- **Known caveat, live:** `validation/generators/generate_wave4_review_ui.py` still reads
  `results/v10/wave4/` — the **reverted** span data — kept deliberately so brief 04's
  verification stayed comparable to what Jeff actually saw. **Repoint it at
  `wave4_notrim/` before showing him anything new** ([`STATUS.md`](../../STATUS.md)).

## Distance to gate

**Above the gate on Ketubot, below it on Kiddushin, and the Kiddushin number is not
trustworthy.**

| | current | gate | noise |
|---|---|---|---|
| Ketubot (BLIND, n=229) | **80% / 84%** | ≥75% hit+near | **0 points**, measured on same-code repeats |
| Kiddushin (CIRCULAR + biased, n≈16) | 60% / 73% | ≥75% hit+near | **±7 points** — one target is 6.25 |

Three things follow:

1. **Ketubot clears the gate, and the measurement is stable enough to say so.** Two
   identical-code runs that genuinely differ (2 of 111 boundaries moved) score the same.
   That is the first gate in this project able to adjudicate a code change.
2. **Kiddushin's shortfall is not a fact about Kiddushin.** Its ruler is 16 corrections
   targets with a ±7-point noise floor, on a biased set. `tasks/NEXT/07` builds a blind
   Kiddushin boundary set (~180–190 targets) from the newly parsed 2005 list, which will
   kill the noise the same way Ketubot's did. **Until then, do not compare the two
   tractates on this row.**
3. **Untrimmed already scores 75% / 83%.** The whole trimming apparatus — three
   mechanisms, two reverts, four months — is worth about **5 points of HIT and 1 point of
   hit+near** on the blind ruler. The old exam said it doubled the score. That gap between
   the two readings is the most important thing this capability has learned.

**Blocked on Jeff, and honestly so.** The end rule is a product question in a
measurement's costume: when a ruling is what makes a passage a story at all, is that
ruling part of what we display, or the discussion that follows it? His 2005 lists keep it;
his 2026 notes cut it. Email sent 2026-08-30; his reply was *"I will get to all this
soon"* ([`STATUS.md`](../../STATUS.md), [`email_jeff_2026-08-30.md`](../golden/v11/email_jeff_2026-08-30.md)).

## Ceiling

**Measured, and unusually concrete: ~87%.**

**87% of Jeff's 2005 boundaries fall exactly on a clause edge** — 257 of 294. The other
13% fall *inside* a clause, so **no prompt can reach them** with the current splitter;
it would need a finer one (`6be55d7`). This is the first direct evidence for or against
Wave 5's core design choice, and it validates it: clause anchoring can reach seven-eighths
of the target.

*Measuring it required care worth recording.* A first pass said 61% land mid-clause —
an artifact, because clause ranges run past the closing `.` while Jeff's text ends on a
letter. The honest test is whether any Hebrew **letter** is left outside his boundary.

**A second limit, not a ceiling but a floor on what can be claimed:** the corrections
ruler's 2 contradictory targets and 3 duplicates cap a perfect run at 50/52 and nothing in
the scorer says so. Downgraded from a blocker to a cleanup once the neutral ruler existed
(`6be55d7`).

## Untried

- **Never trim away a clause that is itself narrative** — the principled guard, and the
  one salvageable piece of Wave 5b: its labeller used as a **veto on the trim** rather
  than as the mechanism that computes the boundary. ~40 lines against the original 433.
  Brief written: `tasks/NEXT/03`. It targets the one defect that survived the product
  decision: **Ketubot 62a and 105b each discard a whole second story** — R. Yochanan on
  the collapsing stair, and Mar Ukva and the spit, six clauses of narrative and dialogue
  Sefaria prints in full. Wrong under **every** definition of where a story ends.
- **A blind Kiddushin boundary set** (`tasks/NEXT/07`) — ~180–190 targets from the 2005
  list, which removes the ±7-point noise and makes the Kiddushin row meaningful.
- **Harvest Jeff's 10 anchored Kiddushin remarks** (`tasks/NEXT/08`) — each came back
  with its exact anchor position in the main text, so it attaches to the passage he was
  looking at. Several are boundary corrections. Unused.
- **A finer splitter for the 13%** — the only route past the measured ceiling. Nobody has
  costed it, and it may not be worth it: the reader sees the surrounding text.
- **Averaging repeated runs, or many more targets, before adjudicating any prompt
  change.** Recorded as necessary after the noise floor was found (Lesson 22); the neutral
  ruler solved it for Ketubot and nothing solves it for Kiddushin yet.
- **The open scorer defect (Wave 5b review §2.3):** a scorer still reads a run's skipped
  stories as ordinary boundaries. A live instance was caught in the Wave 5 Step 1 run —
  `skipped: 1`, folded into the metric as a "kept full" boundary without a word. It
  happened not to be a target that time (Lesson 21, point (d) — **still open**).
- **Declined, twice, with reasons:** the end-trim depth cap (a magic number standing in
  for a real signal, and it optimised for the wrong expert standard); and any further
  regex-based text-internal editing (Lesson 15).
