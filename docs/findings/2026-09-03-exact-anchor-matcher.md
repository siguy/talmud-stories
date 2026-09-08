# Locating an expert story by exact unique phrase — the loose recall figure was the window, not the match

**2026-09-03.** Status: **measured**, on all four tractates that have a run.
Work item: [`work/done/2026-09-03-exact-anchor-matcher.md`](../../work/done/2026-09-03-exact-anchor-matcher.md).
Shipped **behind a flag** (`--matcher exact`); the default is unchanged. See
[The decision this leaves open](#the-decision-this-leaves-open).

## The problem

Every recall figure on the board comes from `locate()` in
`scripts/measure_recall_vs_expert_list.py`, which finds an expert's story by comparing
**sets of Hebrew 4-grams per segment** — word order and position discarded — then grows a
window while coverage improves. Accumulating segments can only *add* grams, so nothing
ever penalises a too-wide window: a neighbour sharing `אמר ליה` extends it. Windows run to
14 segments, and the loose figure credits a proposal anywhere inside one.

## What was measured

Jeff's 2005 text is essentially verbatim Vilna, so the abbreviation problem the 4-gram
aligner was built around (`א"ל` vs `אמר ליה`) is mostly not present. Across all four lists,
**every single story** contains at least one exact 6-word phrase that is **unique in its
whole tractate** — 149/149 Ketubot, 90/90 Kiddushin, 111/111 Gittin, 102/102 Yevamot.
Nothing fell back to the 4-gram aligner on any of the four.

`locate_exact` anchors on those phrases and then extends over every other phrase of the
story **that sits where the story says it should** — a phrase *k* words in belongs *k*
words into the passage, give or take small elisions. That positional test is the whole
difference: a gram set cannot reject a neighbour; a phrase landing 300 words from its
place is simply not this story's copy of it.

### The independent check

Nothing in the matcher reads Jeff's own daf labels, so they are a free scorecard:

| | 4-gram window | exact anchor |
|---|---|---|
| Kiddushin | 51/90 | **85/90** |
| Gittin | 90/111 | **104/111** |
| Yevamot | 72/102 | **97/102** |

Located span, segments — median / max: Ketubot 7/14 → **2/9**, Kiddushin 7/14 → **1/15**,
Gittin 8/14 → **2/11**, Yevamot 7/14 → **2/11**. The remaining wide spans are genuinely
long stories (Abba Sikkara and the fall of Jerusalem, R. Dosa b. Harkinas), each at
0.94–0.96 gram coverage.

## The numbers

Same-day fuzzy re-runs reproduce every banked figure exactly, so the change is additive
and the comparison is matched (Lesson 22).

| | loose | | strict | | triage | |
|---|---|---|---|---|---|---|
| | 4-gram | exact | 4-gram | exact | 4-gram | exact |
| **Ketubot** | 96.0% | **87.2%** | 87.9% | **87.2%** | 98.0% | **96.6%** |
| **Kiddushin** | 93.3% | **84.4%** | 83.3% | 83.3% | 95.6% | 95.6% |
| **Gittin** | 100.0% | **97.3%** | 97.3% | 97.3% | 100.0% | 100.0% |
| **Yevamot** | 94.1% | **89.2%** | 89.2% | 89.2% | 100.0% | 100.0% |

**Loose collapses onto strict and strict barely moves.** That is the result: the gap
between the two figures was the window, not a real ambiguity about what we found. The
strict figures this project quotes were right all along — three of the four are unchanged
to the story.

## The two things that did move, by name

**One story changes strict verdict: Ketubot, the testimony of R. Yosi the Priest**
(`העיד רבי יוסי הכהן ורבי זכריה בן הקצב`), so Ketubot strict is **130/149 = 87.2%**, not
131. The baraita appears **twice**: at 26b:7 (`מתיב רבא`) and again at 27a:1
(`איכא דאמרי, אמר רבא: אף אנן נמי תנינא`). Jeff cites **27a**; the detector proposed only
the 26b copy. The 7-segment window covered both and credited it. This is a duplicate
passage, not a substantive miss — but "we proposed the parallel a daf earlier" is not
"we proposed this", and the strict test is the one that says so.

**Two Ketubot stories move from Detection's column to Triage's** — 27a above, and
`ההוא יתום ויתומה דאתו לקמיה דרבא` at 51a. Both had windows spilling onto an examined
neighbouring daf while their own daf was skipped; both now read as what they are, pages
Stage 1 never examined. Ketubot triage recall is therefore **96.6%, not 98.0%**, and its
detection-given-triage **90.3%**. No other tractate's split moves.

Every other change is a loose credit withdrawn — 12 Ketubot, 8 Kiddushin, 3 Gittin,
5 Yevamot, each named in the work item's reconciliation. The five Yevamot cases are
exactly the five `results/recall/yevamot_strict.json` already flagged as "check these by
name", now resolved: all five were the window reaching a neighbour on the same daf.

## The decision this leaves open

The default stays `--matcher fuzzy` and the **unsuffixed** `results/recall/*.json` the
board reads are untouched. The reason is not doubt about the matcher: `build_ruler.py`,
`audit_proposal_credit.py`, `audit_detection_density.py` and `build_gittin_golden.py` all
call `recall.locate` **directly**, so flipping this harness alone would leave the board
internally inconsistent — the ruler and the recall row would be locating the same stories
differently. Cutting over is one item across five call sites, and it is worth doing:
it retires the loose/strict double-quote entirely.

Exact-matcher artifacts are banked suffixed:
`results/recall/{ketubot,kiddushin,gittin,yevamot}_jeff2005_matches_exact.json`.

## Reproduce

```bash
python3 scripts/measure_strict_recall.py --matcher exact --tractate Yevamot \
  --expert-json results/expert_lists/yevamot_2005.json \
  --detected results/v11/yevamot/yevamot_v11.json
```

`--matcher fuzzy` on the same command reproduces the banked figures. Ketubot goes through
`--expert-doc "jeff comms/b.ketubot (1).doc"` — a different parse path from the three JSON
lists, added to `measure_strict_recall.py` here so all four are measured by one script.

## Guarded

`tests/test_exact_anchor_matcher.py` pins, on a synthetic corpus: the neighbour that
shares the story's opening formula is **not** absorbed; a story whose middle alone is
unique is still located to its **full extent** (boundary scoring reads these same spans);
a story that cannot anchor returns `None` so the caller falls back **per story** and the
fallback is **counted and named**, never a silent zero (Lesson 38); and `coverage` stays
the same quantity under both matchers, so the 0.6 unlocated floor keeps its meaning.
