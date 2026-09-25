# STATUS — where the project is today

**Last rewritten: 2026-09-15** (integration of #47, #48, #49); **updated 2026-09-25** for Jeff's
2026-09-23 verdicts (the section directly below, and the Jeff / Next sections). Rewritten every session, never appended.
Read this first. Companion: [`FRAMEWORK.md`](FRAMEWORK.md) — how we measure and what
counts as good enough. Language and capability names come from there.

---

## 2026-09-25 — Jeff answered the page: all 10 verdicts

- **Goldens moved by his word only.** Ketubot: 12 → `BORDERLINE` (2 this round, 10 where
  he had written "borderline" and we had rounded it to LOW — Lesson 42), 15a:0 → NOT;
  `accepted` 164 → 163. Kiddushin 39b → segment 7. Gittin 57b / 68a → `OUT_OF_SCOPE`.
  Yevamot 105a:13 is a new story not on his list (banked; no Yevamot golden yet).
- **Rules in his words** ([STORY_RULES](docs/STORY_RULES.md)): R-S1 scope = rabbis and
  post-biblical figures; R-B4 Gemara commentary is not the story; R-C5 a bare report is
  not a story; R-C2 speech alone is BORDERLINE with conflict. The pipeline already had
  parts of R-S1 and R-C5 — the news is his wording, his cases and the labels.
- **Twin pass ON by default.** Its prompt carried none of Stage 2's disqualifiers, which
  is why it re-admitted what he rejected. Now it does; re-asked on the 21 additions on
  disk it drops 3 of 7 known-false and **one story on his 2005 list (Yevamot 78a:13)**.
  No shipped artifact is under the new default yet — the cells below predate it.
→ [`jeff-verdicts`](docs/findings/2026-09-25-jeff-verdicts-scope-commentary-reports.md)

## The headline (2026-09-15)

**The largest class of Detection miss is named, measured, and recovered — on one
tractate.** 18 of the 38 stories we miss across four blind lists sit **one segment from
something we proposed, and in 18 of 18 that proposal is a different story**: the missed
one's formulaic twin. The Talmud tells the same shape of anecdote two or three times in a
row with different actors — R. Zadok and the noblewoman, then Rav Kahana and the
noblewoman — and the detector returns one and stops. A targeted pass that shows the model
the story it found *and* the segment beside it, and asks one narrow question, recovers
them: **Yevamot 89.2% → 94.1%**, all six of that tractate's twin misses by name, nothing
lost, 0 span repairs, **9 extra proposals** for Jeff per tractate. Merged default off;
**on by default since 2026-09-25**, after his verdicts.
→ [`miss-anatomy`](docs/findings/2026-09-07-miss-anatomy.md) ·
[`twin-pass`](docs/findings/2026-09-14-twin-pass.md)

**The density finding is corrected.** "Detection is worst where a story stands alone" was
Triage's losses charged to Detection: **all nine Triage misses on the board sit in one
cell** — a story alone on a daf whose other segments carry no narrative label — and
conditioned on the page being examined, the profile reverses (93.8% alone, 85.4% at 5+).
Salience was the right idea aimed one stage too late.

**Triage is re-measured under the live rule and the current matcher, both causes named:**
Ketubot **98.0%** (rule +1.4, matcher −0.7), Kiddushin **97.8%** (rule +2.2, matcher 0).
The board still prints the *artifacts* (96.6 / 95.6); which it should print is now an
item, not a silent choice. → [`triage-remeasured`](docs/findings/2026-09-07-triage-live-rule-remeasured.md)

**The default model was measured and reverted.** #42 had set `gemini-3.8-flash` at
`thinking=high`; on an intact prompt that scores **27.8%** with 9 of 20 pages returning
nothing — the JSON is cut off mid-object and the run reports success. Preview with
thinking off, the config every shipped number came from, scores 83.3% on the same pages.
It is the default again, pinned by tests. → [`default-model`](docs/findings/2026-09-14-default-model-measured.md)

**And a two-night detour that produced only false findings, kept as the record.** A first
attempt at the twin problem spliced an instruction into the detection prompt and ended
its f-string early: `{few_shot_section}` went to the model as literal text, every call
lost its examples, recall fell 83.3% → 50.7%, and nothing raised. It was blamed on model
drift, on thinking levels, on run-to-run variance, before the prompt was diffed. The
detector is in fact **deterministic** — three repeats, identical story sets, spread 0.0 —
so single runs are comparable and every "noise floor" claim from those nights is void.
The check that ends it is one command: **diff the rendered prompt against the last
known-good.** A test now fails if any placeholder survives into a built prompt.
→ [`broken-prompt`](docs/findings/2026-09-09-broken-prompt-explains-everything.md)

**What the previous rewrite said, still true:** every recall figure is measured under
exact-phrase anchoring; loose/strict is retired; Yevamot is detected and measured; three
"what to fix next" hypotheses were screened and refuted — the criteria wording, the
translator, and attention-per-page. The fourth, the one that survived screening, is the
twin pass above.

## Scoreboard — capabilities per [`FRAMEWORK.md`](FRAMEWORK.md) §1

*Every recall cell below is measured under exact-phrase anchoring on the **shipped
artifacts**. Two measured improvements are NOT in the cells because neither is the
shipped default: the live Triage rule (Ketubot 98.0 / Kiddushin 97.8, see
[`promote-liverule-denominator`](work/done/2026-09-07-promote-liverule-denominator.md)) and
the twin pass (Yevamot Detection **94.1%**, `TWIN_PASS=1 TWIN_TRIGGER=all` — **the
default since 2026-09-25**, but no artifact has been re-run under it). Read a cell as "what the artifact on disk holds", never as the ceiling.*

| capability | metric | Ketubot | Kiddushin | Gittin | **Yevamot** | gate |
|---|---|---|---|---|---|---|
| **[1 Triage](docs/capabilities/1_triage.md)** | stories surviving, BLIND | **96.6%** at 44% of pages | **95.6%** at 38% | **100%** at 52% ✓ | **100%** at 44% ✓ | ≥98% *(provisional)* |
| | *live keep-rule, RETIRED MATCHER — not comparable, see below* | *98.7%* | *97.8%* | — | — | — |
| | *if every page were examined (NOT shipped)* | *124 calls/story* | *33 calls/story* | — | — | — |
| **[2 Detection](docs/capabilities/2_detection.md)** | recall given the page survived triage, BLIND | **90.3%** | **88.4%** | **97.3%** ✓ | **89.2%** | ≥95% *(provisional)* |
| | *end-to-end (triage × detection), BLIND* | *87.2%* | *84.4%* | *97.3%* | *89.2%* | — |
| | *golden recall, CIRCULAR* | *92.1%* | *95.3%* | — | — | — |
| **[3 Classification](docs/capabilities/3_classification.md)** | precision, CIRCULAR, harness | **89.2%** ✓ | **85.3%** ✓ | — | — | ≥85% *(provisional)* |
| | *BLIND, over labelled spans* | — | — | **83.7-86.7%** | — | — |
| **[4 Boundaries](docs/capabilities/4_boundaries.md)** | hit / near, BLIND | **80% / 84%** ✓ (ceiling ~87%) | **85% / 91%** ✓ (ceiling ~88%) | **85% / 89%** ✓ | not scored | ≥75% *(provisional)* |
| | *under his stated formula rule (R-B1)* | *82% (61-112)* | *88%* | *86%* | — | — |
| **[5 Review](docs/capabilities/5_review.md)** | days per tractate | not started | not started | **1 round, 25 verdicts, 1 day** | not started | days, not weeks *(derived)* |
| **[6 Publication](docs/capabilities/6_publication.md)** | — | not started | not started | not started | not started | — |

**Two Detection cells fell by ~7 points and no detector changed.** They were measured
through a search window up to 14 segments wide that credited a proposal anywhere inside it;
that window is retired. The numbers above are what the same runs were always worth. **Do
not read the drop as a regression, and do not compare any figure here against one dated
before 2026-09-03 without saying which matcher produced it.**

**The Triage row needs its caveat read.** The 96.6% / 95.6% pair is the *shipped artifacts*
— which still carry the **previous** keep-rule — located by the current matcher, and it is
the pair that composes with Detection. The live rule (`>=1 NARRATIVE_EVENT`, shipped
2026-08-31) was measured at 98.7% / 97.8% **with the retired matcher**, so the true live
figure is **unmeasured**: the two differ by rule *and* by matcher, and mixing them hides
one inside the other. → [`board-reads-stale-triage`](work/done/2026-09-01-board-reads-stale-triage.md)

**Ketubot Triage now reads below its gate, and Detection below its own on three tractates.**
That is a change in what we know, not in what the pipeline does.

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

**~~Detection is softer under a strict test~~ — resolved 2026-09-03: there is one test
now.** The loose column was a 14-segment search window, and the stories "in the gap" were
never in a gap: 17b, 50a and 51a carry zero proposals and always did. The strict figure was
the right one, and it is now the only one. The suspicion recorded here — *treat the loose
column as an upper bound and verify by name* — was correct, and checking it by name on
6 Kiddushin passages (2 of which the window credited to a different passage on the same
daf) is what eventually paid for the fix. Kept as the record of how it was found.

## What changed 2026-09-07 → 09-15 — three PRs

**#47 measurement.** `scripts/audit_miss_anatomy.py` classifies every expert-list miss by
cause and by distance from the nearest proposal, no API calls. Triage / Mishnah-withheld /
adjacent / near / far / blank = 9 / 2 / **18** / 11 / 3 / 4 of 47. `merge_triage_recall_run.py
--live-rule` fixed: it left `skipped_by_triage: True` on rescued pages, so a story read as
triage-lost and detector-found at once and the Triage cell could not move. Two decisions
handed on as items: what the board's cells describe, and whether `HABITUAL` keeps a page
(Ketubot 82b: 4 HABITUAL, 0 NARRATIVE_EVENT, discarded).

**#48 the twin pass.** `_find_adjacent_twins` in `story_detector_v11.py`. Its own prompt;
the page-level prompt is byte-identical on or off, pinned by `tests/test_twin_pass.py`.
Two triggers: `labelled` asks only where Stage 1 marked the neighbour narrative (+2 on
the slice, 2 calls); `all` asks about every free neighbour (+4, ~30 calls per 20 pages,
recovers the 121b criers that sit inside a segment Stage 1 called DELIBERATION). Full
Yevamot under `all`: 91 → 96 of 102, 12 proposals added, 9 not on his list. A truncated
model response (`MAX_TOKENS` with partial text) is now reported and counted instead of
becoming "no stories". Also carries the series-clause detour: `SERIES_RULE`, measured
+1 unrelated story and no twin, off.

**#49 the default.** `gemini-3-flash-preview`, thinking off. A set-but-empty
`GEMINI_THINKING_LEVEL` is off, not "use the default". Closes
`thinking-level-experiment`: high starves the output of tokens, 27.8%.

**Instruments that earned their place this fortnight:** `span_repairs` — 0 / 90 / 237
separated three conditions recall alone read as noise; `scripts/score_noise_floor_slice.py`
— repeats on a fixed 20-page slice, ~4 min a run, deterministic, so a one-run comparison
is a measurement.

## What changed 2026-09-03 — the matcher

**The instrument, not the detector.** `locate` compared sets of Hebrew 4-grams per segment
and grew a window while coverage improved; a union only grows, so no window was ever too
wide. Replaced by exact-phrase anchoring on phrases unique corpus-wide. **All six readers of
an expert list now share one locator**, so the ruler and the recall harness agree per
tractate for the first time — 130/149, 76/90, 108/111.

**Numbers:** Ketubot 96.0 → **87.2**, triage 98.0 → **96.6**, detection-given-triage 97.9 →
**90.3**; Kiddushin 93.3 → **84.4**; Gittin 100 → **97.3**; Yevamot 94.1 → **89.2**. Strict
recall barely moved — three of four unchanged to the story — which is the evidence that the
loose column was the artifact.

**One story changed strict verdict**, and it is worth knowing by name: Ketubot's testimony
of R. Yosi the Priest is a baraita appearing **twice**, at 26b:7 and 27a:1. Jeff cites 27a;
we proposed only the 26b copy. Ketubot strict is 130/149, not 131.

**One entry left the Gittin golden.** 34a:9 was in as `expert_blind_list`/`YES` because a
7-segment window credited it to Jeff's story at 34a:11 — *did not marry* within thirty days
against its formulaic near-twin *did not return*. Nobody had labelled it. Golden is now
**134 / 116**, repinned in `GOLDEN_COUNTS` with the reason beside the count.

**Not rebuilt: the blind boundary target sets.** The tighter window aligns *more* stories
(Ketubot 147→148, Kiddushin 88→89), but the banked sets carry 23 `rule*` annotations the
builder cannot regenerate, and `git show HEAD:` is their only copy. Its own item, with
annotations-first ordering written into it
([`boundary-testset-rebuild`](work/2026-09-03-boundary-testset-rebuild.md)).

**Three callers still use 4-grams on purpose** — two assign a daf *label* and write
ground-truth files; one exists to reproduce a frozen retracted claim. Named in the finding.

**Yevamot also landed in this merge:** first run, **89.2%**, Triage lost 0 of 102, two
crashes fixed that had each eaten a full stage.

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
means. → [`board-reads-stale-triage`](work/done/2026-09-01-board-reads-stale-triage.md), and a
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
  **4 triage-discarded, 2 examined-and-nothing-proposed.** *(Detection figures superseded
  2026-09-03 — 88.4% / 90.3% under the current matcher. The finding stands: the gap is
  Triage's. The 6 misses are 14.)*
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
`jeff:speech-act-policy` is **answered (2026-09-23)** — R-C2. New and free:
`jeff:scope-edges` (Elijah with a rabbi; a biblical exemplum inside a rabbinic story;
Titus / Yannai / Agrippa).

**The review page was sent 2026-09-16 and came back complete 2026-09-23** — see the top
of this file. What it carried, for the record:
- the **1 top-confidence proposal** credited to his list by the search window but never
  actually overlapping it — Kiddushin 39b 8-10 (`work/2026-09-03-loose-credited-proposals.md`).
  **It was 11 until 2026-09-03**; the other 10 were the window, not proposals needing a
  verdict, and asking about them would have spent his attention on our instrument
- the **2 Gittin extras** nobody has judged — Nebuzaradan (57b:0-4) and Ashmedai
  (68a:7-12) (`work/2026-09-02-gittin-two-unjudged-yes.md`)
- the **3 genuinely speech-only entries** from 6a — 7a:1, 15a:0, 112a:11 — as a
  `borderline` question (`work/2026-08-30-story-criteria.md`)
- **the 9 Yevamot proposals the twin pass added that his list does not carry**
  (2026-09-14) — his verdicts on these are what turns the pass on by default

**One page, not four.** Review throughput is the bottleneck (his last two full rounds
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

**1. ~~Send the review page~~ — done; answered 2026-09-23, applied 2026-09-25.** Next in
its place: **re-run a tractate under the new default** (twin pass on, new wording) so the
cells stop describing the old detector, and so the one thing the re-ask cannot see — a
neighbour the new wording would *add* — gets measured. Then 6c of
[`story-criteria`](work/2026-08-30-story-criteria.md), now unblocked.

**2. Run the twin pass on Ketubot.** 7 of the 18 corpus twin misses are there and it is
the one tractate the pass has not touched. Needs `run_new_tractate.py` — or a sibling —
taught to read `results/v7/ketubot_pages_*.json` rather than `results/sefaria/`; ~1 hour
of plumbing, then ~30 min of run. Kiddushin (3) and Gittin (1) after.

**3. Decide what the board's cells describe** —
[`promote-liverule-denominator`](work/done/2026-09-07-promote-liverule-denominator.md). Simon's
call. Recommended: print both per row.

**4. `HABITUAL` as narrative evidence** —
[`habitual-is-narrative-evidence`](work/2026-09-07-habitual-is-narrative-evidence.md).
No API calls to screen. Definitional, not a threshold; worth one story in the measured
corpus, so argue it from the principle or not at all.

**5. Reach 2.** Eleven misses sit 2–6 segments from a proposal. One flag on the twin
pass; untried. The cost is calls, and it is measurable on the slice in 4 minutes.

**Hold, unchanged:** Eruvin until a review round returns; the speech-act policy is Jeff's
(`jeff:speech-act-policy`, the two Yevamot misses the twin pass could not reach are it).

**Done since the last rewrite:** `board-reads-stale-triage` · `formulaic-cluster-splitting`
(reopened, then measured: the series clause is +1, no twin) · `adjacent-twin-check` ·
`bench-is-not-reproducible` (premise refuted) · `thinking-level-experiment`.


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
