# Jeff's ten verdicts: a scope rule, a commentary rule, a "report is not a story" rule — and the twin pass goes on

**2026-09-25.** Status: verdicts **measured** (his words, one file); golden changes
**applied**; twin-pass prompt change **measured on the additions already on disk** —
a re-ask, not a re-run, so it can see only what the new wording *drops*.
Item: [`jeff-2026-09-23-verdicts`](../../work/done/2026-09-25-jeff-2026-09-23-verdicts.md).
Source: `validation/feedback/review_2026-09-16_bundle_jeff_2026-09-23.json`.

## What he said

All 10 passages answered. For the first time on an axis page, the structured fields were
used: Hebrew start/end quotes on 4 of 10 (the Gittin round of 2026-09-02 returned every
structured field empty).

| passage | his answer | why, in his words (abridged) |
|---|---|---|
| Kiddushin 39b 8-10 | no | *"part of the Gemara's commentary on the story… I would not include them in the story at all"* |
| Gittin 57b 0-4 | no — **a story, out of scope** | *"a full blown story, but it is about biblical characters, not rabbis"* |
| Gittin 68a 7-12 | no — **a story, out of scope** | *"not in our scope, which is rabbis and post-biblical figures"* |
| Ketubot 7a:1 | **borderline** | *"mostly speech acts… But there is conflict and some implied change"* |
| Ketubot 112a:11 | **borderline** | *"mainly a dialogue… But has conflict"* |
| Ketubot 15a:0 | no | *"not enough of the incident is given"* |
| Yevamot 15a:14 | no | *"the gemara's comment about the story… just a report of what R. Akiva did"* |
| Yevamot 17a:4 | no | *"rabbi's sitting in a certain arrangement… then they just have a discussion"* |
| Yevamot 105a:13 | **yes**, starts wrong | quote: *רבה ואביי מדבית עלי קאתו … חיה שיתין שנין* |
| Yevamot 106b:9 | no | *"the narrative ends there. There is no continuation"* |

## What it means — four rules ([STORY_RULES.md](../STORY_RULES.md))

- **R-S1, new — scope is rabbis and post-biblical figures.** A biblical episode retold is
  a story, and not ours. His 2005 Gittin list omits both passages, so the rule is twenty
  years old and was simply never written down. Rate: 3 proposals of ~560 across four
  tractates; no accepted golden entry. Edges queued as `jeff:scope-edges`.
- **R-B4, new — the Gemara's commentary on a story is not the story**, even where it
  revises the story or adds a detail. Stronger than R-B2 (excluded, not optional) and it
  covers commentary inside a story as well as after it.
- **R-C5, new — a bare report of what someone did is not a story.** One act, however
  introduced, is a precedent. His 2026-09-01 test (*two actions, causal connection*) from
  the other side, and the unfinished half of R-C3.
- **R-C2, settled — speech alone is BORDERLINE with conflict, NOT without.** The rule he
  invited us to propose on 2026-09-01, confirmed on the cases that turn on it.

**And one indication, not a settlement:** on 106b, *"the gemara making a legal ruling…
is not part of the narrative at all"* leans `jeff:boundary-end-rule` towards *cut the
ruling*. 106b is not a story, so it is not the case that question asks about.

## What changed in the goldens

Counts by `tests/test_bookkeeping.py`: Ketubot `accepted` 164 → **163**; Kiddushin and
Gittin entries unchanged.

| golden | change | on whose word |
|---|---|---|
| Ketubot | 7a:1, 112a:11 → `BORDERLINE`; 15a:0 → `NOT_A_STORY` | his verdicts |
| Ketubot | **10 more → `BORDERLINE`**: 8a:9, 12b:0, 14b:11, 49b:6, 52b:4-5, 54a:13-14, 54a:22, 60b:5-9, 85a:13-14, 100b:17-18 | **his own word "borderline"** in earlier rounds, which our auto-applier rounded to `LOW_CONFIDENCE` because the golden had no such column. Each entry now carries the quote. |
| Kiddushin | 39b 8-8 → **7-7** | his verdict + his 2026-04-23 note + his 2005 entry `kiddushin_041` all start at 7 |
| Gittin | 57b:0-4, 68a:7-12 → new `out_of_scope` list (`OUT_OF_SCOPE`, R-S1); `unlabelled_proposals` 24 → 22 | his verdicts, through `build_gittin_golden.py` (which still reproduces the old file byte-for-byte without the new verdict file) |
| Yevamot | none — no golden yet. Verdicts banked on [`yevamot-golden`](../../work/2026-08-30-yevamot-golden.md), including **105a:13, a story not on his 2005 list** | his verdicts |

**Why the 10 are not scope creep.** In 2026 rounds he wrote *"low confidence/borderline"*
and *"It should be 'low confidence,' a borderline story"* — one category with two names.
The golden could hold only one, and rounded. Now that BORDERLINE is a column, those go
where he put them. The other 65 `LOW_CONFIDENCE` entries were **not** touched: the word is
his to use, and inferring it for him would be the thing this register exists to stop.

**How the immutable harness sees it:** BORDERLINE and LOW_CONFIDENCE are both "story" to
`evaluate_golden.py`, so the 12 reclassifications move no harness number. 15a:0 does, as
one golden story becoming a non-story. `OUT_OF_SCOPE` is outside `stories[]`, so a detector
proposal there scores as a false positive, which is what R-S1 says it is.

## The twin pass: on by default, with his reasons in its question

**Why now.** The twin pass made 12 Yevamot additions; 4 are on his list by the strict
matcher and all 8 others are now judged: 1 yes (105a:13), 3 no (Jeff), 4 no (Simon's
pre-screen). (STATUS.md counted 9 extras; the strict matcher puts 78a:13 on his list.) Every one of Jeff's three `no`s is an
R-B4 or R-C5 shape — commentary on the neighbour, or a report with no continuation — and
the old question offered the model no way to say so: *different actors* was enough for
`separate_incident`.

**What changed.** `_twin_prompt` (now its own method) lists, under `not_a_story`: the
Gemara's commentary on story A; a bare report with nothing following; a seating
description followed by discussion; a biblical episode. The page-level Stage 2 prompt is
untouched (pinned by `tests/test_twin_pass.py`). `TWIN_PASS` defaults to `1` and
`TWIN_TRIGGER` to `all`, the arm measured at Yevamot 89.2% → 94.1%. `TWIN_PASS=0` gives
the old detector for a control arm; the run fingerprint now includes the question's
source.

**Measured — re-asking every twin-pass addition on disk** (21: Yevamot 12, Kiddushin 9;
`scripts/rejudge_twin_additions.py`, `gemini-3-flash-preview`, thinking off; output
`results/v11/twin_pass/rejudge_2026-09-25.json`). The old wording, re-asked the same day,
reproduces **21 of 21** `separate_incident` — so the model has not moved and the wording
is the only variable.

| label (source) | n | new wording keeps | new wording drops |
|---|---|---|---|
| keep — on his 2005 list, or his `yes` | 8 | **7** | **1** — Yevamot 78a:13 |
| drop — his `no` or Simon's pre-screen `no` | 7 | 4 — 43a:12, 45a:17, 101b:13, **106b:9** | **3** — 15a:14, 17a:4, 78a:11 |
| unlabelled | 6 | 4 | 2 — Kiddushin 33a:17, 71a:3 |

Read it honestly:

- **It removes 3 of 7 known false additions, including two of Jeff's three.** 106b:9, his
  third, survives: the model reads *"followed by a challenge… and a halakhic
  resolution"* as the continuation he said is not there.
- **It costs one story on his 2005 list: Yevamot 78a:13** (`yevamot_050`, *כי אתא רב
  דימי אמר רבי יוחנן*). The new wording calls it *"a legal ruling reported by Rav Dimi
  … followed by the Gemara's analytical inference"*. Under his 2026 rules (R-C2, R-C5) that
  reading is defensible, and he called his lists *"provisional"*. **It is a recall loss
  against the ruler all the same**, of one story on 102, and the ruler is not edited to
  hide it. Whether `yevamot_050` is a story under his current rules is a question for him,
  not a thing to decide here.
- **What this cannot see:** a neighbour the old wording rejected and the new one would
  accept. The new wording only *adds* reasons to say no, so that set should be empty, but
  it is not measured. The next full run under the new default measures it.
- **n is tiny.** Seven labelled false additions. This is indicated, not a precision figure.

## Not done, on purpose

- **The page-level Stage 2 prompt does not carry R-S1, R-B4 or R-C5.** That is a detector
  change on every page and needs a scored two-arm run with a same-code repeat (Lesson 22).
  The twin question is narrower, so it could be measured by re-asking.
- **No bulk relabel on R-C5.** 10 accepted Ketubot entries have one event by the
  detector's own count; that is a screen, not his judgment (Lesson 18, Lesson 27).
- **The blind lists are untouched.** `yevamot_050` keeps its place as a story.

## Two defects in the review page, for its next build

- The 105a start quote came back with its text doubled — the highlight capture appended
  the selection twice.
- There is no "a story, but not our kind" answer, so he said it with `is_story: no`,
  `confidence: right` and a note. The builder maps it by key; the page should ask it.
