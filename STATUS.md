# STATUS — where the project is today

**Last rewritten: 2026-08-31.** Rewritten every session, never appended.
Read this first. Companion: [`FRAMEWORK.md`](FRAMEWORK.md) — how we measure and what
counts as good enough. Language and capability names come from there.

---

## The headline

**Three items shipped today that were all supposed to be cheap measurements, and two of
them corrected an attribution this file was making.** The strategic fork below is
unchanged — review throughput is still what stands between two tractates and thirty-seven
— but the map of where the deficits actually live is now materially different.

**1. The triage trade is priced, on both tractates, and Kiddushin's gap closes.**
Stage 2 re-run on all 224 discarded pages: 0 errors, 28 proposals, 4 real.
Ketubot 96.0% → **96.6%** (+1 story, **124 calls per story**); Kiddushin 93.3% →
**96.7%** (+3 stories, **33 calls per story**). Examined end to end the two tractates land
**0.1 points apart** against 2.7 apart as shipped — the whole Ketubot/Kiddushin recall gap
is the triage threshold, and it is **recoverable rather than structural**.
→ [`2026-08-31-triage-recall-price.md`](docs/findings/2026-08-31-triage-recall-price.md)

**And the sweep found a far better rule than "keep everything" — now SHIPPED.** The
endpoints bracket the trade but do not locate the best point in it. A page needed its
narrative event *corroborated* (`N>=2`, or `N>=1 and V>=2`) or it was discarded; that
clause alone was the richest seam of missed stories in the corpus — the 8 pages it
discarded across both tractates hold **6 real stories** (~75%, against 14.3% for
discarded pages overall), **Ketubot 51a among them**, the false skip found by hand on
2026-02-13 and never fixed. `should_skip_page()` now keeps any page with **≥1
NARRATIVE_EVENT**.

| | Ketubot | Kiddushin |
|---|---|---|
| **Triage recall** | 98.0% → **98.7%** ✓ | 95.6% → **97.8%** |
| end-to-end recall | 96.0% → **96.6%** | 93.3% → **95.6%** |
| cost | 4 calls, 3 false proposals | 4 calls, 2 false proposals |

**Ketubot gets the entire gain available from reading the whole tractate, for 4 calls
instead of 124.** A `V>=4` clause would add one more Kiddushin story but costs 70 useless
Ketubot calls — a threshold fitted to a single case, rejected and pinned by a test
(Lesson 18). → [`2026-08-31-triage-single-narrative.md`](docs/findings/2026-08-31-triage-single-narrative.md)

**2. Two of the three stories blamed on Ketubot triage are not triage's fault.**
Ketubot 20a and 82b are still missed with **every page examined** — Stage 2 cannot find
them when handed the text. They are Detection failures wearing Triage's label, and both
`1_triage.md` and the 2026-08-30 miss diagnosis attributed all three to Stage 1. Only 72b
was recoverable by looking. Kiddushin is the mirror image: **3 of its 4 come back**.

**3. Classification precision is being charged for defects already fixed.** Resolving the
unreadable rejection notes by hand turned up something larger than the sort: the banked
per-round figures are properties of *the version reviewed*. Of the 8 notes where the
detector disagreed with a plainly-stated position at review time, **today it agrees with
7**. Population was also **34, not 24** — the item's table omitted two rounds.
→ [`2026-08-31-unclassified-notes-resolved.md`](docs/findings/2026-08-31-unclassified-notes-resolved.md),
**Lesson 36**

**4. One open question with Jeff is retired without asking him.** Kiddushin 58a was listed
as a proposed-then-`NOT_A_STORY` case needing his ruling. His own 2005 margin note on that
passage says *"Not sure this is a story. Very minimal."* — he agreed with us twenty years
before we made the call. **44a stands as the only one to ask.** Given his last two rounds
returned 1 and 15 verdicts, not spending one on an answered question is the whole game.
→ [`2026-08-31-kiddushin-comments-harvest.md`](docs/findings/2026-08-31-kiddushin-comments-harvest.md)

**A hazard confirmed in the wild:** the loose recall window credits us with a *different
passage on the same daf* in 2 of 6 cases tested by name today. It also manufactured a
dramatic false result — that Jeff's 2005 notes contradicted his own 2026 verdicts on the
same passages — which evaporated under a strict test. **Treat the loose figure as an
upper bound and check by name before building on it.**

**5. A round nothing has ever read, and the note that was hiding it.** `STATE.md` listed
*three* files as expert verdicts no ruler reads. Opened and counted: **one** holds
verdicts — Jeff's **2026-01-08** Ketubot round, **25 verdicts, 24 with notes, signed by
name**. The other two are an empty `validations` dict and an automated eval trace. Listing
all three made it look like filing backlog and buried the real one. `board.py` now counts
verdicts and omits empty files.

It is unread for a mechanical reason: `build_ruler.load_reviews()` needs a **dict** keyed
`<ref>_<start>-<end>`, and this round is a **list** keyed by daf — skipped by an
`isinstance` guard, silently. Two things in it exist nowhere else: **9 cross-page refs
covered by no round any ruler reads** (cross-page stories being the project's known weak
spot), and **`length_adjustment` / `spans_multiple_pages` as structured fields** — the
review UI had the right shape in January and lost it, which Phase B should see before
redesigning the axes from scratch. **Not foldable mechanically** (no segment spans, v4
output not on disk); recorded on `golden-completeness` with that caveat.
→ [`2026-08-31-january-round-recovered.md`](docs/findings/2026-08-31-january-round-recovered.md)

**6. Indexed for reuse.** Today's work was findable only by reading five findings end to
end, so: all six new scripts and five findings are in `CLAUDE.md`'s Key Files; six new
`Don't` entries; **Lessons 37 and 38** written and the lessons index repaired (35 and 36
were never added either); `FRAMEWORK.md` §1.1 now carries *how* to supply the cost saving
its triage bar demands; and `new_tractate_workflow.md` gained Steps 7b/7c — measure blind
recall, then price what triage discarded — which is the sequence Gittin/Yevamot/Eruvin
need next.

**Two live traps were in that workflow doc**, and they had been there for months: Step 7
instructed `--output docs/golden/v7/baseline_ketubot.json` — the exact command that
destroys an unreproducible baseline — and told the reader to compare against a composite
score that *rises when expert validations are deleted*. Both are CLAUDE.md rules, violated
by the document that new-tractate work follows first. Fixed.

**Nothing above touches the fork.** Detection was never the problem, Triage now looks
better than it did, and review throughput still is.

**Later the same day: `review-verdict-axes` Phase B is BUILT** — and it should be read for
what it is. The review page now records *which* thing is wrong: **is it a story**
(yes / **borderline** / no) as the only required question, with extent / confidence /
grouping behind a disclosure, `display_problem` as its own control, and the **detector
version on every verdict**. A wrong extent opens a **Hebrew quote box with a stated
include/cut polarity**, filled by highlighting the text on the page — the field whose
absence leaves **16 of our 70 boundary targets** `mixed` or `unclear`, because direction
has only ever been guessed from prose. 605 banked verdicts map into the new shape with **0 unmapped**;
both rulers rebuild **byte-identical**; all **18** injected defects fail the test that
guards them; verified in a browser. Suite **121 → 153**. The review page leads with the
**Hebrew** — the wave 4 page keeps English-first on purpose, so it stays comparable with
the page Jeff was actually shown.

**But it buys fidelity, not throughput, and this file should stop conflating the two.**
Four axes with progressive disclosure is click-neutral on a correct entry and costs more
clicks on a wrong one. It turns Classification from a range into a number *once a round
comes back* — that is Phase C, now its own item awaiting `jeff:axes-round`. The throughput
evidence, found in `5_review.md` while building this: the one round Jeff completed **100%**
of was the **delta** UI that showed him only what had changed (49/49); the two that showed
him all 95 stories again returned **1** and **15**. Nothing in this change addresses that,
and no item on the board does either.
→ [`review_verdict_axes_phase_b`](docs/findings/2026-08-31-review-verdict-axes-phase-b.md)

## Scoreboard — capabilities per [`FRAMEWORK.md`](FRAMEWORK.md) §1

| capability | metric | Ketubot | Kiddushin | gate |
|---|---|---|---|---|
| **[1 Triage](docs/capabilities/1_triage.md)** | stories surviving, BLIND | **98.7%** at 46% of pages ✓ — **NEW RULE** | **97.8%** at 41% of pages — **NEW RULE** | ≥98% *(provisional)* |
| | *previous rule, for comparison* | *98.0% at 44%* | *95.6% at 38%* | — |
| | *if every page were examined (NOT shipped)* | *96.6% e2e · 124 calls/story* | *96.7% e2e · 33 calls/story* | — |
| **[2 Detection](docs/capabilities/2_detection.md)** | recall given the page survived triage, BLIND | **97.9%** ✓ | **97.7%** ✓ — **NEW** | ≥95% *(provisional)* |
| | *end-to-end (triage × detection), BLIND* | *96.0% loose / 87.9% strict* | *93.3% loose / 83.3% strict* | — |
| | *golden recall, CIRCULAR* | *92.1% (90.9% before the Mishnah-tagger fix)* | *95.3%* | — |
| **[3 Classification](docs/capabilities/3_classification.md)** | precision, CIRCULAR, harness | **89.2%** ✓ | **85.3%** ✓ | ≥85% *(provisional)* |
| **[4 Boundaries](docs/capabilities/4_boundaries.md)** | hit / near, BLIND | **80% / 84%** ✓ (ceiling ~87%) | **85% / 91%** ✓ — **NEW** (ceiling ~88%) | ≥75% *(provisional)* |
| **[5 Review](docs/capabilities/5_review.md)** | days per tractate | not started | not started | days, not weeks *(derived)* |
| **[6 Publication](docs/capabilities/6_publication.md)** | — | not started | not started | — |

**Four of five gates are provisional** — see FRAMEWORK §2b. They compose
(`triage × detection = end-to-end`), so only the end-to-end number needs defending, and
that is a product decision, not a technical one. Two questions are open there: one for
Simon, one for Jeff.

**Both Triage cells moved on 2026-08-31 when the corroboration clause was removed:
Ketubot 98.0% → 98.7% (now clears its gate with margin rather than sitting exactly on
it), Kiddushin 95.6% → 97.8% (from 2.4 points below the gate to 0.2 — within noise of it
on a denominator of 90, though not formally clearing it).** The paragraph below describes
the position *before* that change and is kept because the reasoning still stands.

**One cell sat below its gate, and it was the one that mattered most: Kiddushin
Triage, 95.6% against ≥98%** — the capability whose errors FRAMEWORK §2 calls invisible
and permanent. It is also the gate FRAMEWORK itself calls "circular reasoning in a
principle's clothing", set to Ketubot's own value on the tractate that skips *less*. So
the reading is not "Kiddushin triage is broken" but **"the trade is priced differently on
the two tractates and nobody chose either price"**: Kiddushin gives up 2.4 more points of
recall for 6 more points of corpus skipped, about one story per 1.5 points of pages not
examined. That is the open end-to-end question for Simon, now with a number attached.

**And as of 2026-08-31 that trade has a measured price rather than an inferred one.**
Examining every discarded page brings Kiddushin to **96.7%** and Ketubot to **96.6%** —
the gap closes entirely, so the deficit is the *threshold*, not the tractate. The cost is
100 extra Stage 2 calls and, more importantly, **24 extra false proposals per tractate
landing in front of the reviewer** (precision on discarded pages is 14.3%). The decision
therefore belongs to whoever owns review throughput, and **the review-cost half is still
unpriced.** → [`triage_recall_price`](docs/findings/2026-08-31-triage-recall-price.md)

**The Detection row is quoted conditionally on purpose.** The end-to-end figure charges
Triage's losses to Detection as well, and the two have separate gates (Lesson 35). Both
readings are in the table.

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
fix is a review-UI change — **built 2026-08-31**, see
[`review_verdict_axes_phase_b`](docs/findings/2026-08-31-review-verdict-axes-phase-b.md) —
not more inference over free text. The point estimate itself waits on a round.

**A third pooling now known, and it inflates the pessimism: those round figures are
per-version.** Of the notes stating a plain position where the detector disagreed at
review time, **today it agrees with 7 of 8**. A round's precision is a historical fact
about v5.1 / v7 / v8, not about the current detector, and quoting it as the capability's
number charges today's model for calls it no longer makes (**Lesson 36**).
→ [`unclassified_notes_resolved`](docs/findings/2026-08-31-unclassified-notes-resolved.md)

**Detection is softer under a strict test — and that is the end-to-end row, not the
capability row.** The published test credits a
proposal anywhere in a 14-segment search window. Requiring it to overlap a segment the
story actually occupies gives 87.9% Ketubot / 83.3% Kiddushin. The 12 Ketubot stories in
the gap are **cross-page stories whose text sits on a continuation daf where we proposed
nothing** — 17b, 50a and 51a each carry zero proposals.

**The loose test's over-crediting is now confirmed by name, not just in aggregate.**
Checking 6 commented Kiddushin passages individually, it credits us with a **different
passage on the same daf** twice (30a, 58a). Treat the loose column as an upper bound and
verify by name before building on it.

## What changed 2026-09-01

**One historical claim retracted; no current number moves.** Stage 1's only evidence that
it earns its place — *"triage is the single largest accuracy driver, 87.4% with, 83.5%
without"* (2026-02-13) — rests on `results/v7/ablation_v7_no_triage.json`, and that file is
**not a no-triage run**. `skip_triage=True` stamps every segment `DELIBERATION` and feeds
it to Stage 2's prompt and to post-processing, so the contest it ran was true labels
against uniformly false ones.

Proven without reading the code: **the arm examining 3x the pages found 5 fewer of Jeff's
stories**, 3 of them on pages both arms examined — impossible for a change to the page set.
The capability row is struck with its reason rather than deleted, and the file is kept as
evidence. Triage may well be the largest driver; yesterday's 14.3% precision on discarded
pages is a better reason to think so. **The flag is still live in v11**, which is now a
`Don't` in `CLAUDE.md` and a work item.
→ [`2026-09-01-contaminated-no-triage-ablation.md`](docs/findings/2026-09-01-contaminated-no-triage-ablation.md)
· [`fix-skip-triage-flag`](work/done/2026-09-01-fix-skip-triage-flag.md)

**And the flag is fixed, same day.** `skip_triage` is renamed **`examine_all_pages`** and
now gates the page selection alone: Stage 1 runs whenever labels were not supplied, and
supplied labels are never overwritten — the old `elif` discarded them, which is what
`run_triage_recall_price.py` had to work around. A second all-DELIBERATION default in the
Stage 2 loop became `[]` (renders `UNKNOWN`). **v7-v10 keep the stub on purpose**, pinned
by a test, so the audited artifact stays reproducible. 10 failure-injection tests, 9 of 10
watched fail first.
→ [`2026-09-01-examine-all-pages-fix.md`](docs/findings/2026-09-01-examine-all-pages-fix.md)

**Nothing published moves.** Yesterday's pricing and the `N>=1` rule both used cached
labels and never touched this flag.

**And the ablation was re-run correctly, same day, with no API calls** — the Stage 2 output
on the discarded pages already existed and had only ever been scored against the blind
lists, never against the golden. **Stage 1 buys ~8 points of classification precision on
both tractates**: Ketubot 89.2% → 81.1% (FP 18 → 35), Kiddushin 85.3% → 77.1% (FP 14 → 24),
for at most +0.6 points of golden recall. Nothing was lost by examining more pages — the
invariant whose violation exposed the contaminated original. **February's claim had the
right direction and the wrong evidence; the direction is now measured.**
→ [`2026-09-01-corrected-triage-ablation.md`](docs/findings/2026-09-01-corrected-triage-ablation.md)

**The reason to keep Stage 1 is precision and reviewer load, not compute.** 124 extra calls
a tractate is pennies; 17 extra unjudged proposals in front of the one reviewer is not.

**And they were then read — the precision gain is mostly real, and the blind lists are not
badly incomplete.** Of 60 proposals triage suppresses, only **28** reach a reviewer at all
(the detector rejects 32 itself, so any cost quoted as 60 doubles the real burden).
**15 of the 28 are plainly legal**; 9 are Jeff's own stories re-found or re-bounded; **4 are
genuine candidates.**

**The four are the interesting part, and none is "Jeff missed one."** Ketubot 71a (a
Mishnaic `מעשה` quoted as precedent), Ketubot 112b (closing Eretz Yisrael aggada, and a
malformed `start_segment -2`), Kiddushin 25b and 27a (specific encounters whose content is
purely legal). **Every one falls inside a scope question already open with him** — so they
went into [`comms/JEFF.md`](comms/JEFF.md) as **evidence under `jeff:mishnah-scope` and
`jeff:speech-act-policy`**, not as new questions. They turn two abstract asks into concrete
passages, which is the form his last two rounds actually answered.
→ [`2026-09-01-unread-proposals-screened.md`](docs/findings/2026-09-01-unread-proposals-screened.md)

**The screen is a screen, not a verdict** — this session applying the project's own
`NARRATIVE_EVENT` criterion to decide what deserves his scarce attention.

## What changed 2026-08-31

**Morning: infrastructure and correction. Afternoon: three cells measured. Evening: three
work items shipped, and two of them corrected an attribution this file was making.**
The earlier sections are kept below because the reorganization they describe is what made
the rest cheap.

**Evening — three items closed, ~$0.30 of compute:**

- **`triage-recall-price` DONE**, widened from the brief's 124 Ketubot pages to all 224
  across both tractates. 224 calls, 0 errors. Exchange rate **124 calls/story (Ketubot)**
  vs **33 (Kiddushin)**; the two tractates converge to 96.6% / 96.7% when everything is
  examined. **No pipeline change** — precision on discarded pages is 14.3% and the review
  cost is unpriced. → [`triage_recall_price`](docs/findings/2026-08-31-triage-recall-price.md)
- **Ketubot 20a and 82b reattributed from Triage to Detection** — still missed with every
  page examined. `1_triage.md` and the 2026-08-30 miss diagnosis are corrected.
- **`review-verdict-axes` Phase A DONE** (Phases B and C remain, and B is the one that
  matters). Population **34, not 24**; resolved to 12 classification · 8 boundary ·
  4 confidence · 2 merge · 1 display · **7 permanently unresolvable** (all empty notes,
  all from one round). → [`unclassified_notes_resolved`](docs/findings/2026-08-31-unclassified-notes-resolved.md)
- **`kiddushin-comments-harvest` DONE.** 10 comments → 11 sentence-level remarks, all
  sorted. Two boundary targets captured **with polarity** (CUT / ADD), three real
  disagreements including `YES` and `HIGH_CONFIDENCE` on passages he calls non-stories,
  and two criteria categories we do not model (*report/tradition*, *teirutz*).
  → [`kiddushin_comments_harvest`](docs/findings/2026-08-31-kiddushin-comments-harvest.md)
- **Kiddushin 58a withdrawn from the Jeff queue** — he answered it in 2005.
- **Lesson 36** — a verdict belongs to the version that was reviewed. L-030's shape a
  third time: L-030 pooled across *reasons*, L-035 across *pipeline stages*, L-036 across
  *detector versions*.

**Both filed defects are now FIXED, and both fixes were structural rather than
defensive.**

- **The miss-cause split is a partition by construction.** Both buckets derive from
  `missed`, so the assertion can only fire if the derivation is edited. The merged
  artifact that printed *"3 misses: 4 … 2 …"* now prints *"1 … 2 …"*, and **no published
  number moved** (Ketubot 96.0/98.0/97.9, Kiddushin 93.3/95.6/97.7, verified). The merged
  artifacts stayed measurable: instead of asserting them into uselessness the harness
  warns, names the stories, and says which lines on screen remain trustworthy.
  → [`cause_bucket_partition`](docs/findings/2026-08-31-cause-bucket-partition.md)
- **`finish` now fixes links in both directions.** The defect was sharper than filed: the
  guard **already existed and was one-directional**, and its name promised finishing could
  not break links at all — the suite asserted a property the repo did not have (Lesson 31
  at one remove). Renamed rather than deleted, so the overclaim stays visible.
  `tracked()` now includes untracked-but-not-ignored files, closing a second hole where a
  brand-new file's broken links stayed green until committed.
  → [`finish_fixes_inbound_links`](docs/findings/2026-08-31-finish-fixes-inbound-links.md)

**Closing those two items was the acceptance test** — both are linked from this file, and
`finish` repointed both automatically. Suite **107 → 121 passed, 1 skipped**.

Two things the work turned up about my own testing, both worth keeping: one new test
**passed vacuously** (it asserted against the wrong function body, since the file
enumeration lives in a helper) and had to be rewritten behaviourally; and the scratch
end-to-end test's cleanup `git checkout`-ed the generated board, reverting legitimate
regeneration — caught by the suite itself, and fixed by regenerating instead. The
underlying design point: `fix_inbound_links` now **skips generated files**, since editing
a file that is about to be regenerated achieves nothing and makes it briefly disagree with
its generator.

**A same-day correction, and it is the more useful result.** This file briefly reported
Ketubot 10b_3-3 as a live regression — a story Jeff called *"definitely a story"* that the
detector no longer proposed. **Withdrawn.** It was an artifact of matching verdict spans by
exact `(ref, start, end)` key: the run proposes 10b **3–5** at `HIGH_CONFIDENCE`, so a
boundary change read as a deleted story. Matching is now by overlap. The count stays 7 of 8
fixed; the composition changes, and the one genuine standing disagreement is **Kiddushin
52a**, where we still say `HIGH_CONFIDENCE` and Jeff says *"just a reference to the
Mishnah's story"* — plausibly a `jeff:mishnah-scope` symptom rather than a classifier
defect. Both errors pointed the same way: **exact-span matching reports a re-bounded story
as a deleted one** (Lesson 27's family, reached through a join).

**Afternoon — three cells measured:**

- **Kiddushin Triage measured, and it owns the whole recall gap.** 95.6% (86/90) at 38%
  of pages; Detection given triage 97.7% vs Ketubot's 97.9%. Cause split of the 6 misses:
  **4 triage-discarded, 2 examined-and-nothing-proposed.**
  → [`2026-08-31-kiddushin-recall.md`](docs/findings/2026-08-31-kiddushin-recall.md)
- **A blind Kiddushin boundary set: 176 targets, noise 7 points → 0.77.** 85% / 91%,
  above the gate and above Ketubot. The old 60% / 73% is retired, not averaged.
  → [`2026-08-31-kiddushin-boundary-set.md`](docs/findings/2026-08-31-kiddushin-boundary-set.md)
- **Two Kiddushin stories are proposed and then classified `NOT_A_STORY`** (44a, 58a),
  which is why the figure reaching output is **91.1%**. Both are on Jeff's own blind list
  and neither is in our golden, so no review round has ever shown them to him — they are
  the mirror image of `jeff:speech-act-policy` and are now recorded in
  [`comms/JEFF.md`](comms/JEFF.md).
- **Kiddushin 81b carries two of Jeff's stories, not one.** The second — Rav Hanan of
  Nehardea, 100% text alignment — is blind, on an examined page, and **never proposed**.
- **Wave 1's lexical override priced against a blind set for the first time: +1.1 points**
  of triage recall (one story, 49b) for 9 extra Stage 2 calls.
- **Four latent measurement defects fixed, three of them a literal standing in for a
  property.** `score_boundary_targets.py` classified blind-vs-corrections by *filename*;
  `board.py` decided whether a tractate had a triage number with `if t == "ketubot"`;
  `measure_recall_vs_expert_list.py` had no committed triage-recall measurement at all.
  The fourth: changing its `load_detected` signature broke `build_ruler.py`, caught by
  the suite. `STATE.md`'s Triage and Detection cells are derived now, not pointers.
- **Lesson 35** — a composed metric names the pipeline, not the capability. Lesson 30's
  shape one level up: there the pooling was across *reasons for a rejection*, here across
  *stages of a pipeline*. Both send the fix to the wrong place.

**Infrastructure and corrections (morning) — no measurement moved:**

- **The reorganization landed** (PRs #1–#3). `docs/capabilities/` now carries a history
  per capability; `work/` replaced `tasks/NEXT/` with dated slugs and frontmatter;
  `lessons.md` became one file per lesson; `docs/golden/` is data only;
  `scripts/board.py` generates [`STATE.md`](STATE.md) and [`WORK.md`](WORK.md); and
  `tests/test_bookkeeping.py` makes a bookkeeping violation an ordinary test failure.
- **A failed triage call was silently discarding the page.** `triage_page()` returned
  all-DELIBERATION on a parse failure, which fails both keep-conditions — so a crashed
  call threw the page away, in the one stage whose errors leave no trace. Fixed with a
  distinguishable `TRIAGE_FAILED` value that **fails open**. Proven to change **0** of the
  shipped skip decisions. The *historical* failure rate is unknown and unrecoverable,
  because nothing counted it.
  → [`2026-08-31-triage-failure-default.md`](docs/findings/2026-08-31-triage-failure-default.md)
- **The public site was publishing a six-month-stale accuracy figure** — a v8-era
  *expert-agreement* number presented as accuracy. Corrected and dated, with the strict
  figure quoted beside the loose one. It will go stale again; nothing regenerates those
  pages.
- **Two hazards stopped being advice.** `docs/golden/v7/baseline_ketubot.json` is pinned
  in both the test suite and the pre-commit hook, so running `evaluate_golden.py` without
  `--output` now fails loudly instead of destroying an unreproducible baseline.
- **Three defects were found by *reading*, not by a failing test** — the triage default,
  the stale site numbers, and a `NEXT/04` listed as ready with no brief behind it. That is
  the argument for having written the capability histories.

## Waiting on Jeff — [`comms/JEFF.md`](comms/JEFF.md) owns this

**Do not keep a second copy here.** Open questions used to live in three places at once;
that file exists to end it. It carries all seven questions with the slug each work item
names in `awaiting:`, the corrections we owe, the full sent log, and the **ask order** —
which matters, because seven questions is two emails, not one.

Still unanswered and still blocking capability 4: `jeff:boundary-end-rule`, asked
2026-08-30, answered *"I will get to all this soon."*

**Before any next review round:** `validation/generators/generate_wave4_review_ui.py`
still reads `results/v10/wave4/` — the **reverted** char-offset span data — deliberately,
so the regenerated page stayed comparable to what Jeff actually saw. Point it at
`results/v10/wave4_notrim/` before showing him anything new.

## Next — items in [`work/`](work/), each self-contained

**Lead with Kiddushin only.** It is the sole new tractate where we already have a mature
detector output (95 stories, a golden set, 8 review rounds), so its list pays off
immediately with zero API calls. Gittin, Yevamot and Eruvin have **no detector output at
all** — their lists are worth nothing until the detector runs there, which is a larger
job that should wait until Kiddushin shows what we get.

```
kiddushin-list-parse DONE ─┬─ kiddushin-recall           DONE  (triage + detection)
                           ├─ kiddushin-boundary-set     DONE  (176 blind targets)
                           └─ kiddushin-comments-harvest DONE  (11 remarks sorted)

triage-recall-price       DONE  (the trade is priced on both tractates)
review-verdict-axes       DONE (A+B) — Phase C is now its own item, and needs Jeff
start any time:   kiddushin-12a-dedup · opener-lexicon
open calls:       kiddushin-parse-open-calls   (denominator 90; item 1b is for Jeff)
incomplete:       golden-completeness
```

**`review-verdict-axes` is closed — Phases A and B both done — and what is left of it
needs Jeff, not us.** Both of Phase A's requirements are in the shipped page. The board's
open items are now, honestly, either **waiting on Jeff** (a round, the boundary rule, the
Mishnah scope) or **new-tractate work** that has never been started. **The next thing that
would move the bottleneck is not on the board at all**: showing Jeff only what has changed
since the round he already did, which is the one shape he has ever completed.

**`triage-recall-price` is promoted out of "lower value".** It was a Ketubot curiosity
yesterday; today Kiddushin Triage is the board's only failing cell, and this item is
exactly what that gate is missing — FRAMEWORK §1.1 says a triage bar quoted without its
cost saving is meaningless. Note its frontmatter still reads `tractate: [ketubot]` and its
body is scoped to the 124 discarded Ketubot pages; Kiddushin has 100 discarded pages of
its own with text already on disk, so the item is now under-scoped.

All items are `work/2026-08-30-<slug>.md`. Finished ones are in
[`work/done/`](work/done/) with an `## Outcome` — **never deleted**, which is how
"what has already been done" stays answerable.

| item | capability | needs | Jeff? |
|---|---|---|---|
| **[classification-point-estimate](work/2026-08-31-classification-point-estimate.md)** — send one tractate on the new page; the range becomes a number. **The instrument is built; this is the reading** | 3, 5 | a round | **yes** |
| **price the review cost of a delta-only round** — show him only what changed. No brief yet, and the only lead this project has on throughput | 5 | — | no |
| **[golden-completeness](work/2026-08-30-golden-completeness.md)** — fold in every verdict; the 16 unincorporated Kiddushin verdicts are confirmed and still unfolded | 3, ground truth | — | no |
| **price the review cost of loosening triage** — the missing half of the trade; no brief yet | 1, 5 | — | no |
| **fold the 2 harvested boundary targets** into `expert_boundary_targets_v2.json`, with polarity; needs a same-code repeat (Lesson 22) | 4 | — | no |
| [second-story-guard](work/2026-08-30-second-story-guard.md) — stop discarding a second story sharing a segment | 4 | — | *awaiting* |
| [kiddushin-parse-open-calls](work/2026-08-30-kiddushin-parse-open-calls.md) | ground truth | — | **1b** |
| [kiddushin-12a-dedup](work/2026-08-30-kiddushin-12a-dedup.md) — one detection covering two stories | 2 | — | no |
| [story-criteria](work/2026-08-30-story-criteria.md) — was Wave 6; 6a runs now, 6c blocked by design | 3 | comments-harvest | **6b** |
| [opener-lexicon](work/2026-08-30-opener-lexicon.md) — was Wave 7; mine openers, never invent them | 1, 2 | — | no |

**Done today** — `capability-histories` · `ketubot-77a` · `fetch-new-tractates` ·
`ketubot-golden-additions` · `kiddushin-list-parse` · `review-ui-display-asymmetry` ·
`kiddushin-recall` · `kiddushin-boundary-set` · **`triage-recall-price`** ·
**`kiddushin-comments-harvest`** · **`review-verdict-axes` Phases A and B**.

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
  Gittin 112 · Yevamot 102 · Eruvin 74   <- PRISTINE, and now PARSED 09-01 to
                                            results/expert_lists/*_2005.json. Eruvin was
                                            recorded as 73: its table is stored right-to-left,
                                            so the line parser dropped the first story and
                                            mis-attributed 53 of the rest. We have never run
                                            the detector on
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
above are now **measured** (112 / 102 / **74** — Eruvin's 73 was a parser artifact,
corrected 2026-09-01), and all three lists
are genuinely blind — 0 English review comments, 0 `הוספתי` markers, unlike Kiddushin's.

`scripts/build_boundary_testset_2005.py` **can** build blind boundary sets for these
three — correcting this file's earlier claim that it could not. Its `load_units` reads
`results/sefaria/*.json` as well as the detector outputs, and returns 2,990 / 3,865 /
3,645 segments for Gittin / Yevamot / Eruvin (verified 2026-08-31). What is missing is the
other half: each list must first be parsed to JSON the way Kiddushin's was, because
`--expert-json` is the only input the builder accepts for a list that is not the Ketubot
`.doc` (Lesson 28).

**But their per-daf attribution has a defect, in the same family as Kiddushin's.**
`parse_expert_doc` only matches single-amud headers, so **21 stories** under two-amud
headers (`סה ע"ב-סו ע"א`) are silently credited to the *preceding* daf — Gittin 11,
Yevamot 7, Eruvin 3. Entry counts are unaffected; **daf-level recall on these three
would be wrong until it is fixed.** One Gittin header (`יד ע"ד`) uses amud *dalet*, a
Yerushalmi form with no Bavli equivalent. `--verify-only` lists all 21.

**Quote golden counts the same way.** "Ketubot 182 · Kiddushin 85" compared entries
against accepted-only. Use 187/96 or 164/85, never one of each.
