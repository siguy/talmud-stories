# PLAN — Consensus at scale: machines argue, Jeff settles only the disagreements

**Written 2026-09-28. Status: planned, not started.** Simon approved the direction and a
Claude model as a second, independent judge (2026-09-28). Each phase is a self-contained
item in `work/`, listed at the end. Read [`FRAMEWORK.md`](../../FRAMEWORK.md),
[`docs/STORY_RULES.md`](../STORY_RULES.md) and
[`2026-09-27-detector-is-not-deterministic`](../findings/2026-09-27-detector-is-not-deterministic.md)
first.

---

## 1. The problem, in one paragraph

Jeff's attention is the only scarce resource in this project; API calls are not. A full
Yevamot run is ~590 Gemini calls. Review throughput is measured: 25 bounded passages came
back in a day, 95 open-ended ones drew 1 verdict (`comms/JEFF.md`). And the detector is not
deterministic — identical runs disagree on 3 of 102 of his stories, each time by *not
looking at all*. So today we spend few calls and ask him about everything. This plan
inverts that: spend calls freely to (a) find more, (b) judge every candidate against the
rules **he already stated**, (c) measure how often a unanimous machine verdict agrees with
him — and send him only what the machines disagree about, plus a small audit.

## 2. Principles this plan is built from (each one earned, with its source)

| principle | from |
|---|---|
| A **narrow question beats a broad instruction** | the twin pass recovered every twin a "find everything" prompt missed (2026-09-14) |
| **Rules in his words, one per decision**, with his cases | `docs/STORY_RULES.md` |
| **The golden is the product; the blind lists are the instrument** — never tune toward the instrument | STORY_RULES §"Two artifacts" |
| **BLIND vs CIRCULAR** on every dataset | FRAMEWORK |
| **Contested cases are kept and flagged**, never silently resolved; `borderline` is a column | Jeff, 2026-07-06 and 2026-09-01; Lesson 42 |
| **Never use labelled examples from the pages being evaluated** | Lesson 2 |
| **Anchor to text units, never character offsets** | Lesson 16 |
| **Measure a rate before building a rule** | Lesson 18 |
| **Same-code repeats**; a delta means nothing without the spread | Lesson 22, Lesson 43 |
| **A failed call is counted, never read as a verdict** | Lesson 21 |
| **Send him 25, not 150** | `comms/JEFF.md` sent log |
| **Machine agreement is not evidence.** Five runs of one model agree on its systematic mistakes. Consensus is *measured* against him before it is trusted, and never written into a golden as his label | this plan |

## 3. Architecture

```
            ┌────────────── RECALL ──────────────┐   ┌──────────── JUDGMENT ────────────┐
 Sefaria →  Stage 1 labels (no page skipped)      →   candidate pool (every proposal,     
            Stage 2 + twin pass × N runs (Gemini)      "found in k of N", unioned by overlap)
                                                   →   RULE PANEL, per candidate:
                                                        one narrow judge per STORY_RULES rule
                                                        × 2 model families (Gemini, Claude)
                                                        each answer cites segment indices
                                                   →   TIERS
                                                        consensus-story    → corpus, "machine consensus"
                                                        consensus-not      → dropped, audited
                                                        contested          → Jeff queue (≤25/round)
                                                        out-of-scope       → R-S1 catalogue
                                                   →   JEFF: contested + random audit
                                                        every verdict → golden (as HIS label)
                                                                      → regression case for its judge
                                                                      → a new rule when no judge covers it
```

### 3a. Recall layer
- **No page is skipped.** `examine_all_pages` exists in v11 (tested; only ever adds pages).
  Simon accepted the call cost on 2026-09-03 (`work/2026-09-03-examine-all-pages.md`).
- **N runs, N = 5 to start**, pooled by segment overlap; each candidate carries
  `found_in: k/N` and the classification each run gave it. N is a measured choice
  (phase B reports recall against N = 1…5), not a guess.

### 3b. Judgment layer — the rule panel
One judge per question, each a small prompt carrying **only** its rule, Jeff's words,
and his precedent cases (from `STORY_RULES.md`), asking yes / no / unsure with the segment
indices it relied on:

| judge | question | rule |
|---|---|---|
| J-actual | Does it narrate something that happened (not a hypothetical, not a legal case)? | Jeff 2026-07-06 criteria |
| J-event | Beyond speech, does something happen? Quasi-speech-acts (*retracted, considered, responded, sent a question*) are speech | R-C2, his 2026-09-02 list |
| J-conflict | If speech only: is there conflict and implied change? | R-C2 |
| J-report | Is it a bare report of one act with nothing following? | R-C5 |
| J-custom | Is it a custom? If so, does a one-time event follow? | R-C3 |
| J-commentary | Is this the Gemara's commentary on a story rather than the story? | R-B4 |
| J-scope | Are the actors biblical figures in a biblical episode? | R-S1 |
| J-mishnah | Is it the Mishnah's own copy of the story? | R-C1 (already deterministic, Stage 4g — re-used, not re-asked) |
| J-bounds | Where does it start and end (segment + Hebrew phrase, never offset)? | R-B1, R-B2, R-B4 |

**Composition is code, not a model.** The verdict is computed from the judges' answers by
a written decision table (e.g. *actual ∧ event ∧ ¬report ∧ ¬commentary ∧ ¬scope →
story; speech-only ∧ conflict → borderline; scope → out-of-scope*). The table is the rule
register made executable, so a change to it is reviewable and a disagreement can be traced
to one rule.

**Two model families, same judges.** `gemini-3-flash-preview` (the detector's model) and
**`claude-opus-5`** (Simon, 2026-09-28). Independence is the point: the same model asked
five times reduces noise, not bias. Claude runs through the **Batch API** (50% off, no
latency need) with the judge prompt as a **cached prefix**; structured output via
`output_config.format`; adaptive thinking; effort measured in phase C, not assumed.

### 3c. Tiers
A candidate is **consensus** only when all of: found in ≥ k of N runs (k set in phase D),
both model families' decision tables agree, and no judge answered `unsure`. Everything
else is **contested**. Thresholds are fixed in phase D **before** looking at held-out
agreement, and reported both ways if revised (Lesson 37: principled boundary vs tuned
threshold).

### 3d. Jeff's loop
- **Contested queue, ≤25 per round**, ranked by information: a split on a rule he has
  never ruled on outranks a new instance of a settled rule; within that, stories found in
  fewer runs first (the fragile ones).
- **Audit sample, ~10 per round**, drawn at random from the consensus tiers — this is what
  keeps the consensus error rate *measured* after launch, and what grows the scarce
  negative labels.
- **Every verdict does three jobs:** it enters the golden as *his* label (never the
  panel's); it becomes a regression case for the judge it bears on; and if no judge covers
  his reason, it is a candidate new rule for the register — *annotate, never move* the
  blind lists.
- **`jeff:review-error-rate` becomes answerable.** Instead of "what error rate can you
  live with?", phase E shows him a measured rate for the consensus tier and asks whether
  that is good enough to publish flagged.

## 4. Calibration — how we know consensus means anything

**Frozen before any judge is written** (phase A), so the exam cannot drift toward the
answers:

- **Labels:** every expert verdict on disk (`map_verdict_vocabularies.py`: 605 banked,
  plus the 2026-09-02 Gittin 25 and 2026-09-23 page) and the five 2005 lists (positives
  only — a list says a story exists, never that something is not one).
- **Held out:** every page cited as a precedent in any judge prompt is **excluded** from
  calibration (Lesson 2). The precedents are the cases quoted in `STORY_RULES.md`.
- **Split and labelled:** BLIND = Gittin + Yevamot verdicts and all five lists (the
  headline); CIRCULAR = Ketubot + Kiddushin verdicts (their prompts were built from
  Ketubot labels). Reported separately, never pooled.
- **Negatives are scarce — count them first.** Roughly: Gittin 18 `no`, Yevamot 4,
  Ketubot 24 `NOT_A_STORY`, Kiddushin 11. Simon's pre-screen `no`s are **not** expert
  labels and are reported as a separate row. With n this small, report intervals, and
  expect the audit sample (3d) to be the real source of negatives.
- **Version-matched** (Lesson 36): a verdict judges the span he saw; match candidates by
  overlap, and report how many verdicts could not be matched.

## 5. Gates — fixed now, before measuring

| phase | passes if | if it fails |
|---|---|---|
| B pooled recall | pooled-N Detection recall on Yevamot and Gittin ≥ best single run + 2 stories, **and** the spread across single runs is reported | keep N = 2 union; stop increasing N |
| C panel mechanics | 0 uncounted failures; every judge answer cites ≥1 real segment; decision table unit-tested on every STORY_RULES precedent | fix before D |
| D consensus quality (BLIND) | consensus-story tier agrees with his verdicts/lists **≥ 95%**, lower 95% bound ≥ 90%; consensus-not tier contains **≤ 1** story on his lists per tractate | publish nothing as consensus; use the panel only to *rank* the queue |
| D workload | contested queue ≤ 40 per tractate | tighten nothing to hit it — report it; the queue size is a finding, not a knob |
| E first round | Jeff returns the page; his agreement with the audit sample is recorded | the audit is the fallback measurement |

## 6. Cost (estimates; phase B/C measure the real numbers)

- **Gemini recall:** ~590 calls per Yevamot run with triage; examine-all-pages roughly
  doubles the pages → ~1,200 × N = 5 → **~6,000 calls per tractate**.
- **Claude judges:** ~180–300 candidates × ~8 judges ≈ **2,400 calls per tractate**,
  median passage ~830 English characters plus Hebrew; judge prompt cached. At Opus 5
  batch rates, order of **$10–40 per tractate** — to be measured in phase C on one
  tractate before any other runs.
- **Gemini judges:** same count, cheaper.
- The whole Bavli is ~22× Yevamot. Cost is not the constraint; Jeff's rounds are.

## 7. What this plan does NOT do

- It does not change the shipped detector's defaults or artifacts. Everything writes to
  `results/consensus/` until a phase-D finding says otherwise.
- It does not write any machine verdict into a golden as an expert label.
- It does not touch `evaluate_golden.py` or the blind lists.
- It does not re-propose Ein Yaakov, a cold read, or a fixed panel (`comms/JEFF.md`,
  "Things he decided").

## 8. Risks named up front

1. **Correlated error** — both models share a misreading (e.g. dialectic narrated as
  action). Mitigation: calibration measures it; the audit keeps measuring it.
2. **Judge prompts drift into few-shot overfitting** — precedents are his cases, and their
  pages are excluded from calibration; a test pins that list.
3. **The decision table becomes a tuned threshold** — it may only encode stated rules;
  every row cites one.
4. **Jeff's answers are rounded into our columns** (Lesson 42) — the review page keeps a
  free-text reason and the out-of-scope answer as its own option.
5. **Run-to-run variance hides in averages** — every figure is reported with its spread.

## 9. The phases (items in `work/`)

| phase | item | depends on | parallel with |
|---|---|---|---|
| A | [`consensus-a-calibration-set`](../../work/2026-09-28-consensus-a-calibration-set.md) — freeze the exam | — | B |
| B | [`consensus-b-pooled-recall`](../../work/2026-09-28-consensus-b-pooled-recall.md) — N runs, no page skipped | — | A |
| C | [`consensus-c-rule-panel`](../../work/2026-09-28-consensus-c-rule-panel.md) — judges, decision table, two models | A | B |
| D | [`consensus-d-calibrate`](../../work/2026-09-28-consensus-d-calibrate.md) — measure consensus vs Jeff; set tiers | A, B, C | — |
| E | [`consensus-e-jeff-round`](../../work/2026-09-28-consensus-e-jeff-round.md) — first contested + audit page | D | — |

**On concurrency:** A and B write disjoint paths, so they can run side by side. `board.py
lanes` nonetheless puts every item in one serial lane, because
`2026-09-03-rerun-all-tractates` declares the whole of `results/`. Do not run A or B
while that item is running.

Relationship to open items: **`extra-story-discriminator`** asks the same question
(which unlisted proposals are worth his time) with detector features; phase D answers it
with the panel and should record the comparison there. **`examine-all-pages`** is phase
B's switch. **`story-criteria` 6c** (put R-C2/R-C5/R-B4 into Stage 2) is not blocked by
this plan, but a panel that works makes it less urgent — decide after D.
