# Jeff's 2026-11-12 verdicts: Eruvin's 2005 list, and the Septimus precision sample

**Source:** two replies from Jeff, 2026-11-12 (`jeff comms/11-12-2026/`: `reply.md`, the `.docx`,
and the Eruvin review JSON). Recorded by `scripts/apply_jeff_2026-11-12_verdicts.py` (idempotent).
The 2005 lists are evidence and were not edited. His verdicts sit beside them in
`results/expert_lists/superseded_by_rule.json`.

## 1. Eruvin: 20 entries of his 2005 list. **Measured, BLIND**

He was shown 20 of his own 2005 entries, labelled *FROM YOUR 2005 LIST*. He was never shown a
detector call on them. Verdicts: **19 `no`, 1 `borderline`** (63a:4-5, `eruvin_055`). Every review
key maps to a list id, and the script asserts the segments the recall harness locates for each one.
His cover note: the Eruvin list *"seems to just be the preliminary list before refining"*. These
entries were *"all flagged as questionable"*.

Recount: `measure_recall_vs_expert_list.py --expert-json results/expert_lists/eruvin_2005.json
--tractate eruvin --detected results/v14/eruvin/run1.json --standard {2005,current}`. The `current`
output is now `results/recall/eruvin_jeff2005_matches.json`.

| v14 run 1 | 2005 list as written | indicated 2026-11-11 (our reading) | **after his verdicts** |
|---|---|---|---|
| denominator | 74 | 70 | **55** |
| triage keeps the page | 72/74 (97.3%) | 69/70 (98.6%) | **55/55 (100%)** |
| detection, given triage | 67/72 (93.1%) | 67/69 (97.1%) | **55/55 (100%)** |
| end to end | 67/74 (90.5%) | 67/70 (95.7%) | **55/55 (100%)** |

- **All 7 detector misses are among his 19 `no`** (13b:11, 14b:17-18, 32b:3-6, 53b:10-11,
  53b:12-13, 60a:15-16, 63a:0-3). That includes the 2 that triage discarded (14b, 32b).
- **Our 2026-11-11 reading was too generous to his list.** We called 13b:11 and 63a:0-3 real misses
  and 14b borderline. He said `no` to all three, though on 13b he wrote *"could be borderline. There
  is some conflict and drama in the dialogue. But not clear if there are two events."*
- Recall is 100% on 55 stories. With a denominator this size, read that as "no miss
  measured", not as a rate. The 55 are the entries nobody flagged as questionable.

**The precision side: the 12 entries we found that he now calls `no`.** In run 1 (run 2 agrees
on every one):

| run 1 call | entries | on the Septimus site? |
|---|---|---|
| YES / HIGH (definite) | **6**: 41a:1, 51a:2-3, 53b:8, 59b:9-11, 67b:15-18, 68a:10-11 | **all 6 ship** (definite in both runs) |
| LOW_CONFIDENCE | 4: 24a:5, 37b:8-9, 47a:16, 103a:17-19 | no |
| NOT_A_STORY (detector agreed with him) | 2: 24a:14, 53b:4 | no |

The borderline 63a:4-5 is LOW in both runs and does not ship. Of the 7 misses, run 2 proposed
53b:12 at HIGH, which is run 2 only and does not ship. **So 6 of the 73 Eruvin stories on the site
(8.2%) are now measured `no` by Jeff.** That is a lower bound on Eruvin site false positives: he
ruled only on entries we had pre-flagged as questionable. Removing them is the Septimus step's job,
not this one.

## 2. The Septimus precision sample: the 6 non-yes plus 2 missed stories. **Measured on 7 of 60; the rest indicated**

| # | passage | Simon (pre-read) | **Jeff** | rule |
|---|---|---|---|---|
| 1 | Arakhin 23b:0-1 | no | **not**: narrative inside the legal give-and-take is *"hypothetical or possible answers, not events"* | R-C0 |
| 2 | Pesachim 66b:4 | no | **not**: *"the Talmud discussing a story that appeared previously… a legal discussion"* | R-B4 |
| 3 | Chullin 46a:8 | borderline | **borderline** | R-C7 |
| 4 | Chullin 57b:6-7 | borderline | **borderline**: *"If the choice were story or not, I would say story"* | R-C7 |
| 5 | Niddah 7b:4-5 | borderline | **borderline** | R-C7 |
| 6 | Shabbat 147a:6 | borderline | **not**: a setting plus a question and answer *"is not enough for a story"* | R-C2 |
| 7 | Berakhot 54a:15 → 54b (lepers) | (missed start) | **out of scope**: *"an exegetical narrative. We are collecting sage-stories of post biblical times"* | R-S1 |
| 8 | Sanhedrin 52b:4 | (held back, LOW) | **story, include** | R-C1 |

Data: `results/shas_run/precision_sample/jeff_verdicts_2026-11-12.json`. He agreed with Simon on
5 of the 6 and moved one stricter: 147a, borderline to not.

**Item 7 also covers a sample story.** `berakhot-54b-0-0` (biblical: true, Simon yes) is the 54b
half of the lepers passage. His ruling makes it out of scope for his catalogue. It is still a story
for the site, because the site ships biblical stories by Simon's 2026-11-10 decision
(`docs/technical/septimus-story-filter.md`).

**The 60, combining his 7 verdicts with Simon's pre-read on the other 53:**

| stratum | story | out of scope | borderline | not |
|---|---|---|---|---|
| aggadic | 19 | 1 | 0 | 0 |
| halakhic | 18 | 0 | 0 | 2 |
| kodashim (incl. Niddah) | 16 | 0 | 3 | 1 |
| **all 60** | **53** | **1** | **3** | **3** |

- **For the site:** 54/60 definite stories (90%). Counting borderline as story, 57/60 (95%).
  Not a story: **3/60 (5%)**, Jeff's verdicts.
- **For Jeff's catalogue:** 53/60 in scope.
- **Grade of the evidence.** The `not` count is **measured**, and it is a lower bound. The 53 yes are
  Simon's (the project owner), **indicated**. Jeff never saw them. The 7 Jeff verdicts are on
  detector output, so they are **not BLIND**. He was also shown Simon's grade with each passage,
  which may have anchored him. The 7 were picked by Simon's grade, not at random. The figures are
  unweighted across equal strata, so they are not the site-wide rate. Precision of the site is still
  **indicated**: closer to measured than before, but not measured.
- His cover note: *"The interface did not work for me."* He answered in a .docx. Simon's read: he
  was probably not signed into claude.ai, which the artifact review page needs. The Eruvin page was
  a standalone HTML file, and it worked.

## 3. Rules (in `docs/STORY_RULES.md`, each with his words and the date)

- **R-C0:** narrative inside the legal give-and-take is hypothetical, not an event (Arakhin 23b).
  A Mishnah story retold as a baraita is a story (Sanhedrin 52b).
- **R-B4:** the Talmud discussing a story already told is legal discussion, not a new story (Pesachim 66b).
- **R-C2:** a setting plus a question and answer is not a story (Shabbat 147a). **This settles
  `jeff:question-and-answer` by rule.** Yevamot 78b:9 (`yevamot_051`) has the question and answer
  and not even the setting, so it is `not`. It is annotated `tier: rule`, because he did not name it.
  The Yevamot recall denominator goes from **100 to 99**. Recall of the artifact on disk goes from
  89/100 (89.0%) to 88/99 (88.9%), since that run had found it. The v13/v14 drop of 78b:9 was a
  correct rejection.
- **R-S1:** an exegetical narrative built on biblical events is out of scope (Berakhot 54a-b).
- **R-C7 shape 3:** Chullin 57b, 46a and Niddah 7b are borderline. On 57b, forced to choose between
  two columns, he would say *story*. So borderline sits on the story side of the line.
- **The Eruvin list** is the least refined of the five, in his words.

## What this does not settle

- **The site.** Six Eruvin site stories are now Jeff `no`. Arakhin 23b, Pesachim 66b and Shabbat
  147a are `not`. Sanhedrin 52b:4 should be added. All of that belongs to the Septimus step.
- **Other Eruvin entries of the same shapes.** He ruled on 20, and only those 20 leave the
  denominator. His note suggests more of the list is questionable. That is **suspected**, and the
  list is not edited on suspicion.
- **The judge prompt moved.** The consensus judge embeds `STORY_RULES.md` (Scope through
  Triage), so these rules change its prompt sha: `84bfb33fd32a` becomes `88e8fff62716`.
  `check_tractate_run.py` G6 still pins `84bfb33fd32a`. Every judge output on disk keeps that sha
  and stays green. **Any new judge run is red at G6 until Simon re-pins**, which means adopting the
  new register for judging. `tests/test_claude_subset.py` now pins G6 to the fixture's own prompt.
  It tests subset marking, not the register.
