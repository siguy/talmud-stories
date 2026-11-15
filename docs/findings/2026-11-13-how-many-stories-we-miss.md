# How many stories are missing from the site? (2026-11-13)

Simon, 2026-11-13: *"the BIGGER issue is how many stories did we miss?!"*

**Answer: at least about 700 real stories are missing from the Septimus site (range roughly 520 to 940).**
The site ships 1,784, so it holds about 70% of the stories we can count. **The detector is not the main
cause.** It proposes 97% of Jeff's stories on the two v14 tractates with a list. **The site's definite-only
filter is the main cause:** about three in four of the missing stories were found and graded LOW, or definite
in only one of the two runs.

The 700 is a **lower bound, and an indicated figure, not a measured one.** It is extrapolated from two expert
lists (154 stories) and a 60-story precision sample. Jeff's lists are not comprehensive, and what they list is
probably the clearer material. Every reason the number could be wrong points the same way: more misses, not fewer
(§3).

One command, no model calls, about 5 seconds:

```
python3 scripts/measure_site_misses.py --out results/shas_run/accuracy/site_misses.json
```

It runs the recall harness (`measure_recall_vs_expert_list.py`, exact matcher, `--standard current`, so Jeff's
later `not` rulings in `superseded_by_rule.json` leave each denominator) as a subprocess. It joins every list
story to the site, the runs, the goldens and the Septimus decisions by **span overlap**. Each story is assigned to
exactly one stage, and the stages sum to the denominator.

## 1. Where Jeff's stories are lost: the site, list by list (measured)

The denominator is the stories that count for recall: the 2005 list, minus what Jeff has since ruled `not`, minus
Kiddushin's non-blind appendix entries. **The raw list lengths (74, 102, 111, 90, 149) are not denominators.**

| | **Eruvin** | **Yevamot** | Gittin | Kiddushin | Ketubot |
|---|---|---|---|---|---|
| ground truth | **BLIND, held out** | BLIND list; detector partly CIRCULAR (v13/v14 developed on it) | BLIND list; site CIRCULAR | CIRCULAR | CIRCULAR |
| site built from | two v14 runs | two v14 runs | golden | golden | golden |
| denominator (counts for recall) | 55 | 99 | 110 | 90 | 145 |
| **on the site** | **43 (78.2%)** | **64 (64.6%)** | 108 (98.2%) | 52 (57.8%) | 86 (59.3%) |
| triage discarded the page | 0 | 0 | 0 | 4 | 1 |
| never proposed | 0 | 2 | 2 | 9 | 9 |
| withheld as a Mishnah story | 0 | 2 | 0 | 0 | 0 |
| proposed, graded NOT_A_STORY | 2 | 5 | 0 | 3 | 1 |
| **site filter: definite in one run only** | 2 | 5 | n/a | n/a | n/a |
| **site filter: LOW (or BORDERLINE) wherever proposed** | **8** | **21** | 0 | **22** | **48** |
| moved out of scope as biblical | 0 | 0 | 0 | 0 | 0 |
| removed by a Jeff verdict | 0 | 0 | 0 | 0 | 0 |

- **No list story was lost to the biblical move or to Jeff's removals.** That is expected. Jeff's lists are
  post-biblical sage stories (R-S1), and his removals were his own `not`/`borderline` verdicts, which also take
  those entries out of the denominator.
- **On the reviewed tractates, the 70 list stories lost at the site filter are Jeff's own listed stories**, held
  at the old detector's grade in the golden: 60 LOW (39 Ketubot, 21 Kiddushin) and 10 BORDERLINE. A BORDERLINE in
  a golden is Jeff's own answer, so those 10 stay off under definite-only. The 60 LOW are only the old detector's
  call. This is the open question in the 11-10 finding §4.3, now with a count.
- Kiddushin's and Ketubot's "never proposed" and "triage" rows describe the old detector (v10/v11, which built
  those goldens), read from `results/recall/<t>_jeff2005_matches.json`. They are not v14 numbers.

## 2. The same stories, the detector alone (proposed in either run, measured)

| | Eruvin | Yevamot | Gittin | Kiddushin | Ketubot |
|---|---|---|---|---|---|
| **proposed in either run** | **55/55 (100%)** | **94/99 (94.9%)** | 107/110 | 76/90 | 128/145 |
| triage discarded the page | 0 | 0 | 0 | 4 | 4 |
| withheld as a Mishnah story | 0 | 2 | 0 | 0 | 1 |
| never proposed | 0 | 3 | 3 | 10 | 12 |

**Site filter vs. detector, on the v14 lists (Eruvin + Yevamot, 154 stories):**

| | stories | share |
|---|---|---|
| on the site | 107 | **69.5%** (Wilson 95%: 61.8–76.2%) |
| lost to the **site filter** (LOW, or definite in one run) | **36** | **23.4%** |
| lost to the detector's **classification** (proposed, graded NOT_A_STORY) | 7 | 4.5% |
| lost to the detector's **finding** (never proposed, or Mishnah-withheld) | 4 | 2.6% |
| lost to triage | 0 | 0% |

The detector proposes 149 of 154 (96.8%, end-to-end and given-triage alike, since triage lost nothing here). The
site shows 107. **The site filter costs about 27 points of recall; the detector costs about 3.** The detector
figures cover proposal only. Proposed and graded a story is 142/154 (92.2%).

One reading note: the stage counts use overlap, so a list story counts as on the site if any shipped segment
touches it. One Yevamot story the detector never proposed is credited "on the site" this way, through a
neighbouring shipped story. Overlap is generous, so it can only understate misses.

## 3. The estimate: how many real stories are missing (indicated)

**Method.** For the 34 tractates the site builds from two v14 runs (1,535 shipped stories):
missing ≈ S × p × (1 − r) / r, where
- S = 1,535 shipped (`site/data`, `reviewed: false`);
- p = 54/60 = 0.90, the precision sample (2026-11-12; Jeff's verdicts on 7, Simon's on the rest, so **indicated**;
  Wilson 0.80–0.95). Under the 2026-11-13 scope (biblical out) it is 53/59, the same 90%;
- r = 107/154 = 0.695, site recall on the two v14 lists (**measured**).

The bootstrap resamples the list stories within each list and the 60-story sample, 10,000 draws, seed 20261113.
The three reviewed tractates ship from goldens under a different rule, so they are counted directly: their listed
stories not on the site.

| | missing real stories |
|---|---|
| 34 unreviewed tractates | **≈ 607** (bootstrap 95%: **420–842**) |
| Eruvin's rate alone / Yevamot's rate alone | 386 / 756 |
| 3 reviewed tractates: listed stories not on the site (measured, listed only) | 99 (Ketubot 59, Kiddushin 38, Gittin 2) |
| **total** | **≈ 706 (519–941)** |

**Where the ~607 would have been lost**, in the proportions the two v14 lists show: site filter, LOW wherever
proposed **≈ 374**; site filter, definite in one run ≈ 90; graded NOT_A_STORY ≈ 90; Mishnah-withheld ≈ 26; never
proposed ≈ 26. **Biggest single source: a real story graded LOW_CONFIDENCE, about 60% of all misses.** On the
reviewed tractates the same thing holds: 70 of their 99 listed misses sit at LOW or BORDERLINE in the golden.

**Why this is a lower bound, and how blunt to be about it:**

1. **The lists are not comprehensive.** Jeff called the Eruvin list *"the preliminary list before refining"*.
   Gittin: of the 25 stories we found that were not on his list, he said **yes to 3** (19a:16, 43b:4, 70a:22).
   So even among passages we found, about 3% of his yes stories were missing from his list (113 vs 110). Stories
   that neither he nor we found are not counted anywhere.
2. **Listed stories are probably the clearer ones.** A story Jeff did not list in 2005 is more likely to be
   short or marginal, which is the material the detector grades LOW. Recall on unlisted stories is then lower
   than r, so misses are higher.
3. **The Eruvin denominator dropped the 19 entries he called `no`.** He ruled only on entries we had
   pre-flagged as questionable. The remaining 55 are the clean ones, so Eruvin's 78% flatters it.
4. **Reviewed tractates add only their listed misses.** Their unlisted misses are not estimated.
5. **Two lists is not a sample of tractates.** Eruvin's rate gives 386 and Yevamot's gives 756, a factor of two.
   The bootstrap captures the noise within a list, not the spread between tractates. Aggadah-heavy tractates
   (Sanhedrin, Bava Batra) are unlike either. Treat the 420–842 as too narrow, not too wide.
6. **Overlap matching is generous** (§2), which also pushes toward undercounting.

Against these, one thing could push the number down. If the 32 tractates without a list run at Eruvin's rate,
the unreviewed share is nearer 390.

**Other evidence, consistent with the main loss being the site filter's grading, none of it big enough to change
the estimate:**
- **Simon's neighbour check** around the 60-story sample (2026-11-12, measured on 10 flagged neighbours). 8 were
  already on the site as separate entries. 2 were missing. One was a real story held back at LOW (Sanhedrin 52b:4;
  Jeff *"I would include it"*, now on the site by a named `include`). The other was out of scope (the Berakhot
  54a lepers, R-S1). That is one in-scope miss in 10 neighbours, and it was the LOW grade. **Indicated.**
- **The Gemini scope judge** read every unshipped span. It calls **446 of the 1,049 LOW-in-both spans** a `story`,
  and 336 more `borderline`. It also calls 68 of the 95 spans that are definite in one run and LOW in the other a
  `story`. **Indicated, and not independent:** it is the detector's model family, and phase 1/1b were no-go as a
  judge.
- **The two-run disagreements** (11-10 finding §3): of 20 read at random, 12 read as stories and 4 as borderline.
  **Indicated.**

## 4. The recoverable pool, and what a looser rule would buy and cost

From `results/consensus/<t>/units.json`: every span either run proposed, across the 34 unreviewed tractates. A
span is counted only if it does not overlap a shipped story, an out-of-scope story or a Jeff removal.

| how the two v14 runs graded it | spans | on Eruvin + Yevamot: on Jeff's list / Jeff `no` / spans (BLIND) | Gemini judge: story / borderline / not / out of scope |
|---|---|---|---|
| definite in one run, LOW in the other | **95** | 7 / 0 / 14 | 68 / 16 / 6 / 5 |
| definite in one run, NOT/absent/withheld in the other | 26 | 0 / 1 / 1 | 7 / 5 / 5 / 9 |
| **LOW in both runs** | **1,049** | 29 / 6 / 116 | 446 / 336 / 237 / 29 |
| LOW in one run, NOT/absent in the other | 89 | 2 / 2 / 11 | 16 / 26 / 39 / 8 |
| definite in both, not shipped (biblical, removed, judge drop) | 97 | 0 / 6 / 8 | 9 / 1 / 3 / 82 |

**How often a LOW call is a real story, where Jeff has looked.** On his last verdict on each passage the detector
showed him as LOW_CONFIDENCE (Ketubot, Kiddushin, Gittin; detector v5–v11; **CIRCULAR**), he said **yes on 97 of
150 (64.7%; Wilson 57–72%)**, borderline on 21 and no on 32. That splits sharply by tractate: Kiddushin 38 yes / 7
no, Ketubot 56 / 20 borderline / 9, Gittin 3 / 1 / 16. **The BLIND lower bound** is 29 of the 116 LOW-in-both
spans on Eruvin and Yevamot (25%) overlapping a story on his list. His lists are not comprehensive, so the truth
is somewhere between 25% and 65%.

Per tractate (largest pools): Chullin 81, Sanhedrin 80, Shabbat 79, Bava Batra 75, Bava Metzia 60, Berakhot 59,
Eruvin 59, Yevamot 57, Pesachim 56, Avodah Zarah 55 spans that are LOW in both. All 34 are in `site_misses.json`
(`pool.by_tractate`).

### Options for Simon (proposals, nothing applied)

Precision now is 0.90 (the sample). q is the share of added spans that are real stories, as a low / mid / high
range. For one-run spans, q comes from the 12-of-20 reading. For LOW-in-both, the low end is the blind 25% and the
high end is Jeff's 65%. "Recall after" is **measured** on Eruvin + Yevamot (107/154 today).

| rule | spans added | real stories added (low–high) | non-stories added | site precision after | Eruvin + Yevamot recall after |
|---|---|---|---|---|---|
| **0. Reviewed tractates: ship a golden LOW story that is on Jeff's own list** | **60** (Ketubot 39, Kiddushin 21) | 60 | 0 by his list | unchanged | n/a (Ketubot 86→125 of 145, 59→86%; Kiddushin 52→73 of 90, 58→81%) |
| **A. Definite in one run and at least LOW in the other** | 95 | 57 (37–74) | 38 (21–58) | 0.88 (0.87–0.89) | 114/154 = **74.0%** |
| **B. Definite in either run** | 121 | 73 (47–95) | 48 (26–74) | 0.88 (0.86–0.89) | 114/154 = 74.0% |
| **C. B plus LOW in both runs** | 1,170 | 543 (309–773) | 627 (397–861) | **0.71 (0.63–0.80)** | 142/154 = **92.2%** |

- **Option 0 costs nothing in precision by Jeff's own evidence.** He listed these stories, and none has a later
  `not` from him. It narrows nothing and touches only the reviewed tractates. It does not conflict with the
  2026-11-09 ruling against judge promotion, because no judge is involved. It is still a promotion past the
  detector's grade, so it is Simon's call (L-045: a gate narrows, never promotes, except one named passage at a
  time).
- **A buys about 57 stories for about 38 non-stories.** Precision stays inside its own noise (0.90 → 0.88). B adds
  26 more spans, of which the judge calls 9 out of scope. That is mostly noise for little gain.
- **C is the only rule that moves recall a lot**: 70% → 92% on the lists. Precision falls to about 0.71, below
  the 0.85 provisional gate. Under definite-only, it is not a site rule. It is the scale of the catalogue work for
  Jeff: **about 1,050 LOW spans, perhaps 260–680 of them real stories.**
- Not proposed here: a rule that uses the judges, which Simon rejected on 2026-11-09.

## Labels

- **measured:** every row of §1 and §2; the pool counts; recall-after per rule on Eruvin + Yevamot; Jeff's yes
  rate on LOW calls (CIRCULAR); the blind 25%.
- **indicated:** the ~700 total and every extrapolated figure in §3; p = 0.90; q and the precision-after column in
  §4; the judge and reading evidence.
- **suspected:** that unlisted stories are graded LOW more often than listed ones (§3 point 2). It is the main
  reason to read 700 as a floor, and nothing here measures it. A random-page read by Jeff would.
