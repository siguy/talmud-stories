# Did we find the stories across Shas? (2026-11-10)

Simon's question: did we find the stories accurately across all of Shas, how has that been checked, and what are
the numbers. **Short answer: not verified, and in two places the measurements on hand cannot verify it.** What the
numbers do show:

- **The detector finds about 9 in 10 of Jeff's stories** on the one tractate held out from all tuning (Eruvin). That
  is **measured** and blind.
- **The site shows about 2 in 3 of them.** The site ships only stories rated definite in both runs, and about a third
  of Jeff's stories don't get that rating in one run or the other. This is **measured** on Eruvin and Yevamot. It is
  what the rule was designed to do, but no one has put a number on it before.
- **Roughly 85% of what the site ships are real stories.** This is **indicated, not measured**. No expert has graded a
  random sample of shipped v14 stories, so this cannot be verified with what exists today.
- **Every page of every tractate was either examined or skipped by triage on purpose**, and no call failed. This is
  **measured**.
- **32 of the 37 tractates have no expert list**, so their recall is **indicated** from 5 others (Lesson 18).

Every number below comes from one command, which makes no model calls and takes about 10 seconds:

```
python3 scripts/measure_shas_accuracy.py --out results/shas_run/accuracy/shas_accuracy.json
```

The script runs the recall harness (`scripts/measure_recall_vs_expert_list.py`) as a subprocess for each run, so it
never re-implements the matcher. The JSON on disk is what this finding quotes.

---

## 1. What "done and verified" means (written before measuring)

| question | done means | measurement that can support it | BLIND / CIRCULAR | fails if |
|---|---|---|---|---|
| **Recall: does the catalogue have Jeff's stories?** | the detector proposes ≥95% of his blind-list stories on a held-out tractate, in both runs (FRAMEWORK §1.2, gate PROVISIONAL) | the recall harness vs `eruvin_2005.json` (held out); Yevamot as a second, non-held-out read | BLIND | under 95% end-to-end |
| **Recall: does the site have them?** | not set. The site is precision-first by Simon's design (L-045), so no gate exists. The number has to be stated anyway, because "found the stories" will be read as "the site has them" | blind list vs `site/data/<t>.json` | BLIND | no gate; reported as a fact for Simon to judge |
| **Precision: are shipped stories real?** | ≥85% of shipped stories are stories by Jeff's rules (FRAMEWORK §4, gate PROVISIONAL) | the only verifying measurement is **Jeff's verdicts on a random sample of shipped v14 stories**, and it **does not exist**. What does exist: (a) Jeff's verdicts on older YES/HIGH calls, (b) a blind lower bound from his lists, (c) Claude grading the unlisted rest | (a) CIRCULAR, (b) BLIND, (c) neither: Claude's judgment | under 85% |
| **Coverage: was every page looked at?** | every page in the Sefaria text is labelled by triage, present in both runs, and either examined or deliberately skipped, with no failed call | `coverage()` in the script, over every run file | n/a (a count, not a judgment) | any page missing, any failed triage or Stage 2 call, or the two runs on different triage |
| **Generalisation: does it hold for the 32 tractates with no list?** | a blind list, or an expert sample, on tractates unlike the five | none exist | n/a | cannot be checked today |

## 2. The numbers

### Recall (BLIND)

| | Eruvin (held out) | Yevamot (development†) |
|---|---|---|
| Jeff's list stories (denominator) | 74 | 100 |
| **Triage**: on a page we examined | **72 (97.3%)**, 53% of pages examined | **100 (100%)**, 44% examined |
| **Detection given triage**, run 1 / run 2 | **67/72 = 93.1%** / 93.1% | 95/100 = 95.0% / 93/100 = 93.0% |
| **End-to-end proposed**, run 1 / run 2 | **67/74 = 90.5%** / 90.5% | 95.0% / 93.0% |
| proposed in either run | 68/74 = 91.9% | 95/100 |
| proposed as a story (not `NOT_A_STORY`), run 1 / 2 | 64 / 64 | 91 / 90 |
| definite (YES/HIGH), run 1 / 2 | 50 / 51 | 67 / 66 |
| **on the site** (definite in both runs) | **49/74 = 66.2%** | **64/100 = 64.0%** |

† Yevamot is where v13/v14's twin pass was designed and measured, so it is blind as to the list but not held out.
Eruvin is the clean figure.

**Why Jeff's stories are not on the site** (from `not_on_site` in the JSON):

| cause | Eruvin | Yevamot |
|---|---|---|
| graded a story, but below YES/HIGH in at least one run | **15** | **27** |
| proposed, but `NOT_A_STORY` in both runs | 4 | 5 |
| never proposed | 4 | 4 |
| triage skipped the page (14b, 32b) | 2 | 0 |
| **total missing from the site** | **25** | **36** |

**The site's main loss is grading, not finding.** 42 of the 61 missing stories were proposed as stories and then
fell below the both-runs-definite bar. This is **measured**.

**Against the gates:** Eruvin is under the provisional Detection gate (93.1% vs 95%), and under the Triage gate
(97.3% vs 98%) by two stories. **Recall fails its own provisional gate on the held-out tractate.** The gap is small
(3 to 5 stories), and two runs differ by a story or two anyway (Lesson 43).

The three Jeff-reviewed tractates ship from their goldens, so site recall there is CIRCULAR (the goldens were built
with the lists): Ketubot 86/149, Kiddushin 52/90, Gittin 108/110. **The Ketubot and Kiddushin figures are a finding
in their own right.** Of Jeff's own list stories, 40 Ketubot and 21 Kiddushin sit in the golden at the old
detector's `LOW_CONFIDENCE`, and 13 and 16 are not in the golden at all, so the "definite only" filter keeps them off
the site. That a story is on his list is Jeff's own evidence. Whether that should count as definite is Simon's call
(see §4).

### Precision

| measurement | kind | result |
|---|---|---|
| Jeff's verdicts on calls shown to him as YES/HIGH (Ketubot, Kiddushin, Gittin, detector v5–v11, last verdict per passage) | **CIRCULAR**, older versions | 139 yes / 11 borderline / 9 no (+4 unknown, 3 out of scope) → **87.4% yes** |
| shipped v14 stories that overlap a story on Jeff's blind list | **BLIND lower bound** | Eruvin **50/73 = 68.5%**, Yevamot **60/85 = 70.6%** (85 since biblical stories ship; 3 of them biblical, none on his list, as R-S1 predicts) |
| the same, plus Claude's grading of every shipped story *not* on his list (`results/shas_run/accuracy/unlisted_shipped_grades.json`, 48 stories, each with its reason) | **indicated** (Claude, not Jeff) | Eruvin: 9 yes / 7 borderline / 7 no → **80.8%** yes, 90.4% yes-or-borderline. Yevamot: 15 / 9 / 1 → **88.2%**, 98.8% |
| the Gemini scope judge on the 1,541 judge units that overlap a shipped story | **indicated**, and not independent (same model as the detector) | 90.0% story, 5.6% borderline, 3.9% not |

**Reading:** the circular figure (87%), the Claude-graded blind estimate (81–88%) and the Gemini judge (90%) all
fall around **85%**. That is at the provisional gate, not clearly over it. **It is not verified:** none of the three
is Jeff grading a random sample of what v14 ships. The 7 Eruvin "no"s follow a pattern. Three are the Gemara quoting
a Mishnah story, which Jeff has called "no" before (Gittin 46a, 74b). The others are an enactment, a habitual
practice, a hypothetical, and a stretch of halakhic argument whose summary describes text outside the extent shipped
(Eruvin 64a:0-2).

The 141/155 (91%) quoted in `docs/technical/septimus-story-filter.md` has no command behind it. The re-runnable
figure is 139 of 159 judged (87.4%) when borderline counts against.

### Coverage (measured)

- **34 tractates with two v14 runs**: 4,787 pages, all in the Sefaria text, all labelled by triage, the same pages and
  the same triage hash in both runs. **0 triage failures, 0 Stage 2 errors, 0 Stage 4 call failures**
  (`coverage_summary.tractates_with_a_defect: []`).
- **Triage examined 2,076 of the 4,787 pages (43.4%)** and skipped the rest on purpose. That skip is the triage recall
  above: 97.3% on Eruvin and 100% on Yevamot, as measured here. Gittin was 100%, and Ketubot and Kiddushin 98.0% and
  97.8% under the shipped rule, as measured before (`STATE.md`).
- **The other 3 tractates** (Ketubot, Kiddushin, Gittin) ship from goldens built on v10/v11 runs, which were covered
  when those runs were checked.
- **37 of 37** Bavli tractates with Gemara are on the site.

### Two-run agreement (G4, measured)

1,420 of 1,526 definite passages are definite in both runs (**93.1%**) over the 32 run tractates. 9 are under 90% and
ship by Simon's ruling. **Note:** `docs/findings/2026-11-10-shas-run.md` says 93.7% (1,281 of 1,367). Its own table
sums to 1,420 / 1,526, so the 93.7% does not reproduce. It is probably from an earlier snapshot. *Corrected in the base
(`1ef317d`) while this finding was in review.*

## 3. The reading lists

**The biblical list** (`biblical_list.json`, 76 passages; all read):

- **45 dropped (both judges say out of scope): all 45 are biblical figures.** That is 45/45 correct flags: Moses,
  David, Solomon, Hosea, Joseph, Nebuchadnezzar, Sennacherib, Jeroboam and so on. Most are clearly stories too, so
  under Simon's 2026-11-10 rule (biblical stories stay on the site, flagged for Jeff) almost all of them would come
  back.
- **31 that ship:**
  - **24 are right to ship and not biblical.** Second Temple and rabbinic figures named near a biblical one: Hananya
    ben Hizkiya, Agrippa's census, Elisha ben Avuya, Rabba bar bar Hana's desert tales, Nahum of Gam Zo, Ketia bar
    Shalom, Elijah meeting rabbis.
  - **2 are biblical and the flag missed them:** Megillah 7a:2-3 (Esther petitions the Sages) and Sanhedrin
    113a:10-113b:0 (Elijah, Ahab and Hiel; Claude decided alone). Both are stories, so they stay under the new rule,
    but both should carry the biblical flag for Jeff.
  - **5 are not stories, and ship anyway:** Pesachim 56a:1-2 (a list of Hezekiah's deeds), Megillah 15b:4-5 (the
    Attribute of Justice argues), Bava Kamma 17a:1-2 (Hezekiah's funeral honours), Sanhedrin 47a:0-0 (a report about
    Ahaz's bones), Avodah Zarah 3a:3-3b:1 (an eschatological trial). **All five are Gemini "out of scope" plus Claude
    "not a story".** The site drops a passage only when *both* judges say out of scope, so Claude's "not a story"
    has no effect. Across all of Shas that split occurs on **43 judge units, 5 of which overlap a shipped story:
    exactly these 5.** (indicated: my reading of all 5)

**Since resolved in the base** (`3df8464`, Simon 2026-11-10, merged into this branch): biblical stories now ship,
flagged `biblical`. Gemini-out-of-scope plus Claude-not-a-story now **drops** the passage, so none of the 5
non-stories is on the site. Megillah 7a:2-3 and Sanhedrin 113a:10-13 carry the flag. The 45/45 reading above stands:
the flag is right on every passage it was set on.

**The two-run disagreements** (`jeff_two_run_disagreements.json`, 106 passages, definite in exactly one run; 79 are
story/borderline and 27 story/not). I read a random sample of 20 (seed 20261110). 12 read as stories, 4 borderline,
and 4 not stories or biblical (Taanit 24a, Sukkah 31a, which is only a fragment, Sotah 13a, Taanit 27b). **Most of
this list is real stories the site does not show.** That fits the recall table: grading, not finding, is where the
site loses Jeff's stories. (indicated)

**The density sample** (11 random shipped stories from Zevachim and Keritot): **11 of 11 read as stories.** Zevachim
13a is the nearest to borderline. (indicated)

## 4. What is not verified, and what it would take

1. **Precision of the site is not verified.** To verify it, ask Jeff (or a second scholar) to grade a **random sample
   of shipped v14 stories, about 60, stratified across tractate types**: halakhic, aggadic-heavy (Sanhedrin,
   Megillah), and Kodashim. That costs his time and no model spend. **That sample now exists in the base**
   (`08d336a`: 59 stories, `validation/ui/shas_precision_sample.html`, the ask drafted and **not sent**). Until he
   answers, ~85% is indicated.
2. **Recall for the 32 tractates with no list is not verified.** Only Eruvin is a held-out blind test of v14. Jeff's
   2005 lists cover 5 tractates. Whether he has lists for others is a question for him, not something we can check
   here. Without them, the best check left is the same random-sample review aimed at recall: have him read a few
   random pages *triage skipped* and a few with no story found. That would put a rough number on what is missing
   where there is no list.
3. **The site shows about two-thirds of Jeff's stories, and nobody chose that number.** The both-runs-definite rule
   was chosen for precision. Its cost to recall is first measured here. Two decisions followed; one is still open. They narrow
   or widen the site, so they are his to make, not this finding's:
   - should a story on Jeff's own list (the Ketubot and Kiddushin goldens) ship when the old detector called it LOW?
     The site does not show 63 of the 149 Ketubot stories Jeff listed, or 38 of the 90 Kiddushin ones. 53 and 37 of
     those are LOW in the golden or missing from it;
   - ~~should Claude's "not a story" drop a passage that Gemini calls out of scope?~~ Decided yes in the base.
4. **A defect found along the way:** under the default `--standard current`, `measure_recall_vs_expert_list.py`
   **raises on the Ketubot .doc** (`superseded_by_rule.json`'s Ketubot 21b entry matches 0 rows). This script uses
   `--standard 2005` for Ketubot, which affects only the CIRCULAR site-recall row. The Ketubot recall cell in
   `STATE.md` cannot be regenerated from the default until this is fixed.

## Labels

- **measured:** every recall row; site recall; the blind lower bound; coverage; G4.
- **indicated:** precision (~85%); the reading-list judgments; recall on the 32 tractates with no list.
- **suspected:** the 93.7% in the run finding comes from an earlier snapshot.
