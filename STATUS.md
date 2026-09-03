# STATUS — where the project is today

**Last rewritten: 2026-09-03.** Rewritten every session, never appended.
Read this first. Companion: [`FRAMEWORK.md`](FRAMEWORK.md) — how we measure and what
counts as good enough. Language and capability names come from there.

---

## The headline

**Gittin is measured end to end, and three separate hypotheses about what to fix next were
screened and refuted — all of them before spending a single tractate run.** The detector is
now clean: nothing live is unmeasured, and the next tractate's numbers will mean what they
say.

**1. Jeff answered everything, in two messages, and reversed himself three times on
seeing the text.** Questions 1-4 came back in prose on 2026-09-01; all 25 verdicts on the
review page arrived 2026-09-02. Of the five passages both messages cover, **three disagree,
always toward the stricter reading** — 25a *"high confidence"* became *"borderline, not
high confidence"*; 46a and 74b *"can be included"* became **no**. The rule that follows:
**a prose answer sets policy; only a verdict on the passage settles the passage.**
→ [`gittin_verdicts`](docs/findings/2026-09-02-gittin-25-verdicts.md),
[`lesson`](lessons/_a-policy-answer-does-not-certify-a-case.md)

**Three stories we found that his list does not have** — Gittin 19a:16, 43b:4, 70a:22 —
plus 4 borderline and **18 explicit negatives**, the first negative-label set this project
holds on a tractate that was never in a prompt.

**2. The Gittin golden exists, and it is the first that is BLIND end to end.** 135 entries:
25 he judged as spans, 110 corroborated by his 2005 list, and the two kinds of evidence
are **never merged** — a verdict judges the passage *and the extent*; a list entry says
only that a story is there. 23 proposals with no expert label are named in
`unlabelled_proposals` rather than written in with a null classification.
→ [`gittin_golden`](docs/findings/2026-09-02-gittin-golden.md)

**That design decision is what kept the session's biggest defect out of the golden**, and
it was not extra checking — it was refusing to write down a label nobody had given us.

**3. Classification is a point estimate at last — and the number the ruler prints is not
it.** Phase C's acceptance test passed: `unclassified_notes` is 0 and the range collapsed
to `0.143..0.143`. But **14.3% is precision on the residue** — the round covered only the
proposals his list does not name. The tractate figure is **83.7-86.7%** over the 135
labelled spans. The round changed shape and the metric quietly changed meaning.
→ [`point_estimate`](docs/findings/2026-09-02-classification-point-estimate.md)

**4. Three "what to fix next" hypotheses, screened cheaply, all refuted.**

| hypothesis | screen | result |
|---|---|---|
| the criteria wording is wrong | R-C3/R-C4 shipped and scored | **no effect** |
| we read more translation than source | expansion audit, no API calls | **null** — his two cases sit at 4.5x and 5.9x against a corpus median of 2.05, so he read them right, but the passages he *rejects* sit **lower** on expansion than the ones he accepts |
| Stage 2 runs out of attention on dense dapim | recall by story density | **refuted, backwards** — 83.3% where a story is **alone** on its daf, 90.7% on dapim with 4+ |

The third is the useful one. **The constraint is salience, not budget:** we find a story
among its own kind and miss it embedded in legal give-and-take. That also explains why
rewriting the criteria changed nothing — it changes how a candidate is *described*, and the
failure happens before there is a candidate.
→ [`density`](docs/findings/2026-09-03-detection-density.md)

**5. A supposed crisis measured down from 110 to 6.** `story-criteria` was ranked the
project's largest open item on the claim that Jeff's July rule *"would redefine 44% of the
golden"*. Phase 6a — described as *"~$0.10, needs nobody, changes nothing"* and **never run
for five weeks** — says the affected set is **6 entries, 2.4% of the accepted golden**. 110
was the bucket we had to *search*. And reading the 6: **three are spans that stop before
the action**, a Boundaries defect wearing a criteria costume. The criteria question is about
**three entries**. → [`blast_radius`](docs/findings/2026-09-03-speech-act-blast-radius.md)

**6. One real defect, corpus-wide: 35 proposals read as "on his list" and are not.** The
recall aligner returns a window up to 14 segments wide; anything inside it was silently read
as corroborated. Ketubot 19, Kiddushin 9, Gittin 7 — **11 of them top-confidence**. Recall
is untouched (a generous window is right for *did we find his stories*); this is an error
only where the association is read **backwards**.
→ [`proposal_credit`](docs/findings/2026-09-03-loose-window-proposal-credit.md)

**The pattern across 3, 5 and 6 is the session's real finding.** In each case a number was
correct for the question it was built to answer, got quoted against a different one, and
nothing errored — the ruler's 14.3%, `story-criteria`'s 110, the loose window's credit.
→ [`lesson`](lessons/_a-number-is-an-answer-to-the-question-it-was-built-for.md)

**What is shipped and measured since Gittin ran:** **R-B1**, the opening formula — from one
sentence of Jeff's — worth **Gittin 82→86%, Kiddushin 84→88%, Ketubot 61-112 77→82%** on
boundaries. It is the only change with a measured effect. The parallel-practice rule shipped
unmeasured on 2026-09-01 and is now measured: **no effect on any ruler, all five case checks
pass** → [`parallel_measured`](docs/findings/2026-09-03-parallel-rule-measured.md)

## Scoreboard — capabilities per [`FRAMEWORK.md`](FRAMEWORK.md) §1

| capability | metric | Ketubot | Kiddushin | **Gittin** | gate |
|---|---|---|---|---|---|
| **[1 Triage](docs/capabilities/1_triage.md)** | stories surviving, BLIND | **98.7%** at 46% of pages ✓ | **97.8%** at 41% of pages | **100%** at 52% ✓ | ≥98% *(provisional)* |
| | *previous rule, for comparison* | *98.0% at 44%* | *95.6% at 38%* | — | — |
| | *if every page were examined (NOT shipped)* | *96.6% e2e · 124 calls/story* | *96.7% e2e · 33 calls/story* | — | — |
| **[2 Detection](docs/capabilities/2_detection.md)** | recall given the page survived triage, BLIND | **97.9%** ✓ | **97.7%** ✓ | **100%** ✓ | ≥95% *(provisional)* |
| | *end-to-end (triage × detection), BLIND* | *96.0% loose / 87.9% strict* | *93.3% loose / 83.3% strict* | *100% loose / **97.3%** strict* | — |
| | *golden recall, CIRCULAR* | *92.1%* | *95.3%* | — | — |
| **[3 Classification](docs/capabilities/3_classification.md)** | precision, CIRCULAR, harness | **89.2%** ✓ | **85.3%** ✓ | — | ≥85% *(provisional)* |
| | *BLIND, over labelled spans* | — | — | **83.7-86.7%** — **NEW** | — |
| **[4 Boundaries](docs/capabilities/4_boundaries.md)** | hit / near, BLIND | **80% / 84%** ✓ (ceiling ~87%) | **85% / 91%** ✓ (ceiling ~88%) | **85% / 89%** ✓ | ≥75% *(provisional)* |
| | *under his stated formula rule (R-B1)* | *82% (61-112)* | *88%* | *86%* | — |
| **[5 Review](docs/capabilities/5_review.md)** | days per tractate | not started | not started | **1 round, 25 verdicts, 1 day** | days, not weeks *(derived)* |
| **[6 Publication](docs/capabilities/6_publication.md)** | — | not started | not started | not started | — |

**Gittin's Classification cell is the only BLIND one on the board, and it is not
comparable to the two beside it.** The other two are harness precision against a golden
the detector helped build; Gittin's is over 135 spans of which **110 are corroborated by
his 2005 list rather than judged** — his list says a story is *there* and says nothing
about our extent. Only 25 have been judged as spans. That is a review-throughput limit,
not a measurement one. **The ruler prints 0.143 for Gittin: that is precision on the
residue after his list is removed, not the tractate's precision.**

**Gittin's Triage and Detection rows read 100%, and both are real** — his 112-story list
survived triage intact and every story was proposed somewhere. The honest figure is the
**strict** one, 97.3%, and its denominator is **111, not 112**: he retracted one of his own
entries (57a, the Sadducee on the land's fertility — *"the list was wrong. Great to have
the AI correct it!"*). The three remaining misses — 38b, 46b, 57a Beitar — are all
passages he confirms **are** stories, so that deficit is entirely ours.

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

## What changed 2026-09-02 / 09-03

**Jeff's two replies, and the golden they produced.** All 25 verdicts on the unlisted
Gittin proposals: 3 `yes`, 4 `borderline`, **18 `no`**. Three stories his list does not have
(19a:16, 43b:4, 70a:22). The Gittin golden is built from them plus 110 strict list matches,
with `label_source` on every entry and no entry unlabelled.

**Three of his prose answers were reversed by his own verdicts a day later**, always toward
the stricter reading. Recorded as a lesson, because the failure mode is cheap to repeat: a
policy answer that names specific refs *looks* like it disposed of them.

**Recall denominators corrected.** Gittin 112 → **111**, strict recall 96.4% → **97.3%**.
The retracted entry is annotated, never deleted — `counts_for_recall: false`, `blind` stays
true, with his words and the date attached.

**The loose window, measured backwards for the first time.** 35 proposals across three
tractates sit inside an expert story's search window without overlapping its own segments,
and were read as corroborated. **Ketubot 19, Kiddushin 9, Gittin 7; 11 top-confidence.**
Recall does not move. The Gittin golden is unaffected because it was built on the strict
test.

**Three fix hypotheses screened and refuted** — criteria wording, translator expansion,
attention-per-page — see the headline. **The parallel-practice rule, live and unmeasured
since 2026-09-01, is now measured: no effect on any blind ruler, all five case checks
pass.** Its predicted end-ruler cost did not occur, because the two passages it rescues are
**not scorable targets** — the ruler is blind to what the rule fixes, so it is quoted from
the five hand checks, not from the rulers.

**Phase 6a run at last: 6, not 110.** And three of the six are mis-bounded rather than
mis-classified.

**Two instrument defects fixed.** `board.py` could not see a golden or ruler for any
tractate outside a hardcoded pair, so the Gittin golden printed as *never measured*; and it
listed six items as blocked on Jeff when three were. Both pinned by tests.

**One ask withdrawn.** `jeff:appendix-separate` — asking Jeff to keep his appendix a
separate file — is gone and should not return. He is a partner here, and the engineering
premise was false anyway: **we know what we sent him and when**, so the join is ours to
make and `check_appendix_coverage.py` makes it, against any list, at any time.

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

**Later the same day: the board's own guards were checked, and three defects were behind a
green one.** `STATE.md` was read against the artifacts it summarises. Throughout,
`board.py --check` passed and so did `test_bookkeeping.py`. Neither is broken; neither
verifies the property a reader relies on. **`--check` regenerates and compares a checksum,
so a generator that misreads an artifact misreads it identically on both sides.**

**1. The Triage cells describe the rule that was replaced — still OPEN.** `STATE.md`
prints **98.0% / 95.6%**; `should_skip_page()` has been `N>=1` since 2026-08-31, giving
**98.7% / 97.8%**. The board derives both cells from
`results/recall/<t>_jeff2005_matches.json`, whose `survived_triage` predates the change —
recomputing from the artifacts returns exactly what the board prints. **The Detection cells
inherit the same conditioning.** So the file that promises it types no numbers is the wrong
one, and the hand-written file is right. Not repaired here: the fix rewrites the file
CLAUDE.md calls *"always the recall denominator"*, which changes what every recall cell
means. → [`board-reads-stale-triage`](work/2026-09-01-board-reads-stale-triage.md), and a
caveat now sits in [`1_triage.md`](docs/capabilities/1_triage.md) so the cells are not
quoted bare meanwhile.

**2. Two Kiddushin files collided on a dict key, and the blind list lost — FIXED.** Rows
were keyed `f.stem.split("_")[0]`, so `kiddushin_2005` and `kiddushin_comments_harvested`
both keyed to `kiddushin` and the second overwrote the first. **The "Ground truth on hand"
table never showed the Kiddushin blind list at all** — the 89-blind / 90-for-recall
denominator behind every Kiddushin number on the board — and printed another file's zeros
in its place. It was filed as *"a file renders as three zeros"*; running the pre-fix loader
showed the list was **absent, not mis-sized**. Found by executing the old code, not by
reading it — the `split` looks like a tidy-up.

**3. A verdict was dropped for being falsy — FIXED.** `_verdict_count()` required a truthy
`feedback_type`, so the January round read **24** where the file states
`"reviewed_count": 25`. The dropped entry is **Ketubot 17a**, where Jeff declines the
dropdown and answers in prose — stating a display defect, then *quoting the Hebrew of the
story he says the excerpt contains*. The most informative verdict in the round is the one
the inventory could not see. **This is the round Lesson 38 was bought by**: the fix written
for that lesson recovered it and then miscounted it.

**And `finish` was breaking outbound sibling links**, caught by the link guard on the first
item ever to cite a sibling — while its docstring claimed both directions were handled
(Lesson 31's shape, a third time). Fixed to one pass over three link shapes; two
self-inflicted regressions during that fix were caught by the suite and are pinned.

**No measured value moves.** `STATE.md` changes only in the ground-truth table and the
January round 24 → 25.
→ [`2026-09-01-board-guards-verify-the-wrong-property.md`](docs/findings/2026-09-01-board-guards-verify-the-wrong-property.md),
**Lesson 40**

**A hazard for whoever runs the suite next: it cannot go green off a Mac.** Four test files
fail for environment reasons alone — 29 tests across macOS-only `textutil` and a `node -e`
argv limit — and `test_expert_doc_span_headers.py` is red identically on `main`. The
project's entire bookkeeping regime (golden counts, the immutable-harness hash, link
integrity) is enforced by that suite. The `node` tests guard on `shutil.which('node')`; the
`textutil` ones have no availability guard at all.

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
that file exists to end it. It carries the slug each work item names in `awaiting:`, the
corrections we owe, the full sent log, and the ask order.

**Five questions remain open** (down from six — `jeff:appendix-separate` withdrawn
2026-09-03, see below; `jeff:mishnah-scope`, `jeff:opening-formula` and `jeff:axes-round`
closed 2026-09-01/02). Still unanswered and still blocking capability 4:
`jeff:boundary-end-rule`, asked 2026-08-30, answered *"I will get to all this soon."*
`jeff:speech-act-policy` is **partly answered** — no general rule, `borderline` is the
right column — with only the general policy for ~12 thin passages still open; the three
Gittin cases it named are settled.

**One review page is queued and not yet sent — this is the next concrete thing to do,
not a code change.** It bundles three sources that would otherwise be three separate
asks:
- the **11 top-confidence proposals** credited to his list by the loose search window but
  never actually overlapping it (`work/2026-09-03-loose-credited-proposals.md`)
- the **2 Gittin extras** nobody has judged — Nebuzaradan (57b:0-4) and Ashmedai
  (68a:7-12) (`work/2026-09-02-gittin-two-unjudged-yes.md`)
- the **3 genuinely speech-only entries** from 6a — 7a:1, 15a:0, 112a:11 — as a
  `borderline` question (`work/2026-08-30-story-criteria.md`)

**One page, not three.** Review throughput is the bottleneck (his last two full rounds
returned 1 verdict, then 15), so bundling is not a nicety — it is the difference between
one ask landing and three asks starving each other. The other three 6a entries (17a:10,
54a:22, 85a:13-14) are boundary bugs, not criteria questions, and do **not** go on the
page — they get fixed, not asked about.

**`jeff:appendix-separate` is withdrawn, permanently.** It asked Jeff to keep his
appendix of "stories you and Claude found" a separate file. That was wrong twice over:
Jeff is a partner on this project, not a contamination source, and the engineering
premise was false — we know exactly what we sent him and when, so the join is ours to
make (`scripts/check_appendix_coverage.py`, any list, any time). There was never a
closing window. Do not re-add this ask.

**Before any next review round:** `validation/generators/generate_wave4_review_ui.py`
still reads `results/v10/wave4/` — the **reverted** char-offset span data — deliberately,
so the regenerated page stayed comparable to what Jeff actually saw. Point it at
`results/v10/wave4_notrim/` before showing him anything new.

## Next — items in [`work/`](work/), each self-contained

**Two things, and only two, actually move the project right now.**

**1. Send the bundled review page.** Everything is ready: the 11 loose-credited
proposals, the 2 Gittin extras, the 3 speech-act entries. No code needed — see
[`loose-credited-proposals`](work/2026-09-03-loose-credited-proposals.md), which names
all three sources and why they're one ask, not three.

**2. Run Yevamot or Eruvin.** Both have pristine blind lists (102 and 73 stories,
never in a prompt) and the detector is now clean — nothing shipped since Gittin is
unmeasured. Gittin took twenty minutes of compute end to end; expect the same order of
magnitude. **Lead with whichever the reviewer wants back first** — running both
concurrently before the first review round returns would produce two tractates' worth of
unlabelled proposals with no golden-building lesson applied to either.

**A correction to this file's own record, found 2026-09-03.** Four Gittin placeholder
items from the original per-tractate workflow —
[`gittin-triage`](work/2026-08-30-gittin-triage.md),
[`gittin-detection`](work/2026-08-30-gittin-detection.md),
[`gittin-classification`](work/2026-08-30-gittin-classification.md),
[`gittin-review-ui`](work/2026-08-30-gittin-review-ui.md) — were never closed even
though the work they describe was done, under different item names, via the ad-hoc
first-blind-run path (`gittin-detection-run`, `gittin-expert-round`, `gittin-golden`).
Their declared write paths (`results/detection/gittin.json`,
`results/classification/gittin.json`, `validation/ui/gittin_review.html`) never
materialized; the real outputs live at `results/v11/gittin/`,
`results/canonical/gittin_canonical.json`, and
`validation/ui/axis_gittin_unlisted.html`. Now marked `superseded_by:` in each file's
frontmatter, left open rather than deleted per CLAUDE.md. **Not audited: whether the
Yevamot and Eruvin placeholder items (10 more, same template) are heading for the same
drift once those tractates run.** Worth checking before, not after.

```
kiddushin-list-parse DONE ─┬─ kiddushin-recall           DONE  (triage + detection)
                           ├─ kiddushin-boundary-set     DONE  (176 blind targets)
                           └─ kiddushin-comments-harvest DONE  (11 remarks sorted)

triage-recall-price          DONE  (the trade is priced on both tractates)
review-verdict-axes          DONE (A, B, C) — Phase C ran 2026-09-02, on Gittin
gittin-expert-round          DONE — gittin-golden DONE — gittin-recall-denominator DONE
story-criteria 6a            DONE — 6b bundled into the review page above
parallel-story-rule          DONE (measured, no effect, kept)
detection-density            DONE (attention-per-page hypothesis, refuted)
loose-window-proposal-credit DONE (the measurement) — the round is what's left
start any time:   kiddushin-12a-dedup · opener-lexicon
open calls:       kiddushin-parse-open-calls   (denominator 90; item 1b withdrawn)
incomplete:       golden-completeness
```

All items are `work/<date>-<slug>.md`. Finished ones are in [`work/done/`](work/done/)
with an `## Outcome` — **never deleted**, which is how "what has already been done"
stays answerable.

| item | capability | needs | Jeff? |
|---|---|---|---|
| **[loose-credited-proposals](work/2026-09-03-loose-credited-proposals.md)** — the bundled review page. **The single highest-leverage next action.** | 3, 5 | a round | **yes — page not yet sent** |
| **[gittin-two-unjudged-yes](work/2026-09-02-gittin-two-unjudged-yes.md)** — folded into the page above | 2, 3 | — | via the page |
| **[story-criteria](work/2026-08-30-story-criteria.md)** — 6a done (6, not 110); 6b folded into the page above; 6c blocked on 6b by design | 3 | — | via the page |
| **[golden-completeness](work/2026-08-30-golden-completeness.md)** — fold in every verdict; the 16 unincorporated Kiddushin verdicts are confirmed and still unfolded | 3, ground truth | — | no |
| **price the review cost of a delta-only round** — show him only what changed. No brief yet, and the only lead this project has on throughput | 5 | — | no |
| **price the review cost of loosening triage** — the missing half of the trade; no brief yet | 1, 5 | — | no |
| **fold the 2 harvested boundary targets** into `expert_boundary_targets_v2.json`, with polarity; needs a same-code repeat (Lesson 22) | 4 | — | no |
| [second-story-guard](work/2026-08-30-second-story-guard.md) — stop discarding a second story sharing a segment | 4 | — | *awaiting* `jeff:boundary-end-rule` |
| [kiddushin-parse-open-calls](work/2026-08-30-kiddushin-parse-open-calls.md) | ground truth | — | no — item 1b withdrawn 2026-09-03 |
| [kiddushin-12a-dedup](work/2026-08-30-kiddushin-12a-dedup.md) — one detection covering two stories | 2 | — | no |
| [opener-lexicon](work/2026-08-30-opener-lexicon.md) — was Wave 7; mine openers, never invent them | 1, 2 | — | no |
| Yevamot / Eruvin — triage, detection, classification, review-ui, expert-round, golden (10 items, unstarted) | all | text on disk, nothing else | not yet — after the first round |

**Done since the last full rewrite** — Jeff's 25 Gittin verdicts, the Gittin golden, the
Classification point estimate, the recall-denominator correction, the loose-window
audit (measurement), the detection-density screen, the parallel-rule measurement,
Phase 6a, the appendix-ask withdrawal, two `board.py` instrument fixes. Findings are
listed in the headline above; this line exists so the list of *slugs* is in one place
too: `gittin-25-verdicts` · `gittin-golden` · `classification-point-estimate` ·
`gittin-recall-denominator` · `loose-window-proposal-credit` · `detection-density` ·
`parallel-rule-measured` · `speech-act-blast-radius` · `remove-appendix-ask` ·
`board-stale-awaiting` · `board-sees-every-golden`.

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
