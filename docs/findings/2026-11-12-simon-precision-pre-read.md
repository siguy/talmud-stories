# Simon's pre-read of the Shas precision sample — **indicated**

2026-11-12. Simon graded the 60-story stratified sample (`results/shas_run/precision_sample/sample.json`)
before deciding whether to send it to Jeff. **Simon is the project owner, not the expert.** These
verdicts are indicated, never ground truth. They are kept out of every ruler: the file is in
`EXCLUDED` in `scripts/verdict_reading.py`.

Verdicts: `validation/feedback/2026-11-simon-precision-sample.json` (each entry carries `stratum`).

## Result

| stratum | yes | borderline | no | story share (yes only) | yes + borderline |
|---|---|---|---|---|---|
| aggadic | 20 | 0 | 0 | 100% | 100% |
| halakhic | 18 | 1 | 1 | 90% | 95% |
| kodashim (incl. Niddah) | 16 | 3 | 1 | 80% | 95% |
| **all 60** | **54** | **4** | **2** | **90%** | **97%** |

Unweighted. The strata are equal-sized but the site is not, so this is not the site-wide rate. Read
it as a check that sits close to the ~85% already indicated, not as a new figure.

**No:** Arakhin 23b 0-1 and Pesachim 66b 4 (both HIGH_CONFIDENCE).
**Borderline:** Chullin 46a 8, Chullin 57b 6-7, Niddah 7b 4-5 and Shabbat 147a 6.
Every non-yes is in the halakhic or Kodashim/Niddah strata. Both biblical stories in the sample were yes.

## What the notes say: extent, not classification

Simon left notes on 11 of the 60 stories (10 yes, plus Shabbat 147a, borderline). Every note is about the boundary or a neighbouring story:
- **Ends too early, or the story continues:** Sanhedrin 11a 7, Sanhedrin 52b 3, Taanit 23b 10, Taanit 25a 4, Sanhedrin 99b 3-4 (unsure)
- **Starts too late:** Berakhot 54b 0, Shabbat 147a 6, Menachot 68b 13 (unsure)
- **An adjacent separate story, "did we catch it?":** Sotah 49a 9, Taanit 24b 9, Yevamot 105a 5-7, Yevamot 121a 10-13

None was flagged as a display problem.

## Are the flagged neighbours on the site? (checked 2026-11-12, measured)

Each quoted passage was located in the text, then looked up in `site/data/` and in v14 run 1.

| flagged | the passage Simon quoted | on the site? |
|---|---|---|
| Taanit 23b 10 | 23b 11-12 | yes, as its own story `taanit-23b-11-12` |
| Taanit 24b 9 | 24b 10 | yes, `taanit-24b-10-10` |
| Taanit 25a 4 | 25a 5 | yes, `taanit-25a-5-5` |
| Sotah 49a 9 | 49a 10 | yes, `sotah-49a-10-10` |
| Yevamot 105a 5-7 | 105a 8-9 | yes, `yevamot-105a-8-9` |
| Yevamot 121a 10-13 | 121a 14 | yes, `yevamot-121a-14-14` |
| Sanhedrin 11a 7 | 11a 8 (Yehuda ben Bava) | yes, `sanhedrin-11a-8-8` |
| Shabbat 147a 6 | 147a 5 (Hyrcanus) | yes, `shabbat-147a-5-5` |
| Sanhedrin 52b 3 | 52b 4 (the priest's daughter baraita) | **no**. Run 1 found it at LOW_CONFIDENCE, and the site ships definite stories only |
| Berakhot 54b 0 | Berakhot 54a 15 (the two lepers) | **no**. The story starts on the previous page, where run 1 proposed nothing |

Menachot 68b 13 and Sanhedrin 99b 3-4 carry no quote ("maybe", "not sure"), so they were not checked.

So 8 of the 10 are on the site, each as a separate entry. What Simon read as a story cut short is
mostly one narrative split into neighbouring entries: a grouping question, not a lost story. Two
are really missing: one held back by the definite-only filter (L-045, working as designed), and one
because the story starts on the page before.
