# PLAN — Consensus at scale: machines argue, Jeff settles only the disagreements

> **Where this stands (2026-09-28, end of day).** Phase 1 ran and was a **no-go** — and the
> cause was our rule register, not the bet: it lacked Jeff's July rule that an incident
> followed by a ruling can be a story (now R-C0), and R-C5 carried a gloss of ours saying
> the opposite. Both fixed in `STORY_RULES.md`. Next is **phase 1b**
> ([`consensus-1b-corrected-register`](../../work/done/2026-09-28-consensus-1b-corrected-register.md)),
> blocked only on money: Gemini hit its monthly spend cap and Anthropic is out of credit.
> **2026-09-29:** money unblocked; the judge's budget raised to $75; the twin-pass wording
> and the verdict-reading defect fixed. **Phase 1b is ready to run.**
> **2026-10-01: phase 1b — no-go again** (finding §10). §4 unchanged. Phase 2 stays blocked,
> now awaiting `jeff:report-vs-incident`.
> Phase 2 stays blocked until a go. Full diagnosis:
> [`consensus-phase1`](../findings/2026-09-28-consensus-phase1.md) §7–§9.

**Written 2026-09-28; cut to two phases the same day after a three-way plan review**
(§7 records what was cut and why). Status: planned, not started. Simon approved the
direction and a Claude model as an independent second judge (2026-09-28).

Read [`FRAMEWORK.md`](../../FRAMEWORK.md), [`docs/STORY_RULES.md`](../STORY_RULES.md) and
[`2026-09-27-detector-is-not-deterministic`](../findings/2026-09-27-detector-is-not-deterministic.md)
first.

---

## 1. The bet, in one sentence

**When two independent models, each given Jeff's rule register, agree on whether a
passage is a story, they agree with Jeff often enough that he only needs to see the
passages they disagree on — plus a random audit that keeps that claim measured.**

Everything else (pooling runs, examining every page, narrow per-rule judges, batch
tooling) is only worth building if this is true. So the bet is tested first, cheaply, on
labels already on disk.

## 2. Principles (each one earned)

| principle | from |
|---|---|
| Jeff's attention is the scarce resource; API calls are not | ~590 calls per Yevamot run; 25 bounded passages answered in a day, 95 open-ended drew 1 |
| Rules in his words, one per decision | `docs/STORY_RULES.md` |
| **Machine agreement is not evidence.** Consensus is measured against him, never written into a golden as his label | this plan |
| BLIND vs CIRCULAR on every dataset — and now a third label, **rule-informed** | FRAMEWORK; §4 below |
| Contested cases are kept and flagged; `borderline` and `out_of_scope` are answers, not roundings | Jeff 2026-07-06, 2026-09-23; Lesson 42 |
| A failed call is counted, never read as a verdict | Lesson 21 |
| Join by overlap, and say what happens when one span meets two verdicts | Lesson 36 |
| Report the spread; one run is not a measurement | Lesson 22, Lesson 43 |
| Send him 25, not 150 | `comms/JEFF.md` |
| Keep one tractate untouched as the final exam | Eruvin: never run, no rule drawn from it, his 2005 list predates the project |

## 3. Phase 1 — test the bet on every labelled span on disk

**Item:** [`consensus-1-test-the-bet`](../../work/done/2026-09-28-consensus-1-test-the-bet.md).
~600 model calls, no detector run.

- **Unit judged:** the span Jeff judged, exactly as he saw it — not a detector candidate.
  That isolates *does the judgment agree with him* from *did a run find it* (review
  finding: joining to pooled runs would leave Ketubot/Kiddushin with nothing to join to).
- **One judge prompt**, carrying the whole of `STORY_RULES.md` (rules, his words, his
  cases). Output: `story | borderline | not | out_of_scope | unsure`, the rule(s) relied
  on, and the segment indices relied on. Split into narrower judges **only** where
  phase 1 shows a specific rule failing — "a narrow question beats a broad one" was
  proven for *finding* stories (the twin pass), not yet for classifying them.
- **Two model families:** `gemini-3-flash-preview` (the detector's) and
  **`claude-opus-5`**. Plain synchronous calls at this size; batch and caching wait until
  a full-Bavli run is actually scheduled.
- **Labels** from `scripts/build_ruler.py`'s `load_reviews()` and the five 2005 lists,
  cleaned: Simon's test round excluded; a bare `incorrect` with no readable objection is
  **unknown**, not *not a story* (it may be a boundary complaint); `applies_to:
  corrected` rows reported separately.
- **Measured, per tractate and pooled, with Wilson intervals:**
  - how often the two models agree;
  - when they agree, how often Jeff agrees — **on his `no`s separately** (the costly
    error: a non-story published as consensus) and on his `yes`es;
  - stories on his 2005 lists the models call `not` (the other costly error);
  - where they split, which model sides with him;
  - which rule each disagreement with Jeff cites.

## 4. What phase 1 can and cannot conclude — said now, not after

The negatives are the constraint. Approximately: Ketubot ~24 `NOT_A_STORY` and
Kiddushin ~11 (**CIRCULAR** — their labels shaped the detector's prompts); Gittin 18 and
Yevamot 3 `no` (**rule-informed** — R-C5, R-B4, R-S1 were written from these very
verdicts, so a judge carrying the register has seen their reasoning). A Wilson lower
bound ≥ 90% needs ~35 agreeing rows with no error, ~50 with one. **No subset reaches
that cleanly.**

So phase 1 reports **indicated**, never measured. Its decision is go / no-go, fixed now:

| outcome | decision |
|---|---|
| both models agree with each other on ≥ 80% of spans, **and** agreed verdicts contradict his `no` on ≤ 2 spans across all four tractates, **and** ≤ 2 of his list stories are called `not` | **go** to phase 2 |
| otherwise | **no-go** — record which rule the errors cite; the panel may still rank a review queue, but nothing is called consensus |

The real, measured error rate comes from the phase 2 audit, round by round.

## 4a. Why these tractates

- **Phase 1: all four labelled tractates**, because the scarce thing is his negatives,
  not tractates. Each is reported separately; pooled only for the go/no-go.
- **Phase 2: Yevamot.** Three same-code runs are already on disk (a free 3-run pool);
  it has no golden yet, and its golden item is waiting on exactly a round like this; he
  has just reviewed five Yevamot passages; his 102-story list covers recall.
- **Eruvin: untouched.** No detector run, no rule, no prompt. It is the clean exam for the
  whole approach once it works; using it earlier spends the only one we have.

## 5. Phase 2 — the first round under consensus (only on a go)

**Item:** [`consensus-2-yevamot-round`](../../work/2026-09-28-consensus-2-yevamot-round.md).

- **Candidates:** the union, by overlap, of the three same-code Yevamot runs on disk
  (`results/v11/twin_pass/yevamot_full_twinall.json`, `yevamot_full_twin2.json`,
  `yevamot_full_twin2_r2.json`), each carrying `found_in: k/3`. Overlap chains are not
  merged transitively (A∩B, B∩C ≠ one candidate) — tested. `mishnah_stories[]` is read and
  kept as its own tier (R-C1), decided explicitly in a comment.
- **Tiers:** consensus = both models agree and neither is `unsure`; contested = anything
  else. **k is not a threshold in round 1** — it ranks the queue (fewest runs first).
- **Jeff's page:** ≤25 contested, ranked (splits on a rule he has never ruled on first),
  **plus an audit sampled from both consensus tiers** (~5 consensus-story, ~5
  consensus-not), shuffled in and not marked as audit.
- **Every verdict:** into a new Yevamot golden as *his* label (builder pattern of
  `build_gittin_golden.py`); audit agreement recorded as the live error rate; a
  disagreement becomes a regression case for the prompt; a reason no rule covers becomes a
  candidate rule in STORY_RULES, in his words.
- **The email** asks `jeff:review-error-rate` with the phase 1 indication and says the
  audit will turn it into a measurement; carries the free ask `jeff:scope-edges`.

## 6. Shipped now, separately

[`review-page-scope-and-quote`](../../work/done/2026-09-28-review-page-scope-and-quote.md) — the
two defects Jeff hit on 2026-09-23 (no "a story, but out of scope" answer; the doubled
Hebrew quote capture). Independent of this plan; needed before phase 2's page.

## 7. What the review cut, and why (2026-09-28)

Three reviewers (convention/ceremony, correctness/statistics, simplicity) independently
reached one verdict: the first draft built the whole system before running the cheap test
that could kill it. Deferred until the phase 2 audit shows they are needed:

| cut | why |
|---|---|
| **Pooling 5 new runs + examine-all-pages** (~6,000 calls/tractate) | Off the critical path for the bet; and it changed two variables at once. Three runs already exist. Examine-all-pages stays its own item (`2026-09-03-examine-all-pages`) — note `run_new_tractate.py` documents `--examine-all-pages` but does not implement it |
| **Eight per-rule judges + a decision table** | A second hypothesis nested in the first. One register-wide prompt citing its rule still traces each disagreement to a rule. Decompose only where a rule fails |
| **A standalone calibration builder with a pinned hash** | `build_ruler.py` already joins lists, proposals and verdicts; a git commit is the freeze |
| **The ≥95% / ≥90% gate** | Not measurable on the labels that exist (§4). Replaced by an honest go/no-go and a measured audit |
| **Batch API, cache tuning, an effort pilot** | Right at Bavli scale, premature at ~600 calls |
| **A k-of-N threshold** | Fixed after seeing the pools, it would be tuned; in round 1 k only ranks |
| **Five findings documents** | One finding per phase |

Corrections the review found in the first draft, carried into the items: Yevamot has 3
expert `no`s, not 4; the detector's fingerprint is `_stage2_fingerprint`, not
`run_fingerprint`; Gittin and Yevamot labels are rule-informed, not BLIND; per-rule judges
would have needed an `n/a` answer to avoid sending everything to contested.

## 8. What this plan does not do

It changes no detector default or shipped artifact, writes no machine verdict into a
golden, does not touch `evaluate_golden.py` or the blind lists, and does not touch
Eruvin. It does not re-propose Ein Yaakov, a cold read, or a fixed panel.
