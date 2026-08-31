# True Recall, Measured: 96% on Ketubot Against a Detector-Blind Expert List

**Date:** 2026-08-28
**Status:** Measured and reproducible. This closes the project's largest open
question.
**Supersedes:** [approach_review_and_scaling_2026-07-06.md](2026-07-06-approach-review-and-scaling.md)
§3.1, which called measured recall "circular" and "the most important unmeasured
number in the project," and guessed true recall at "plausibly 80–85%."

---

## 1. Why this was impossible until now

The golden datasets were built by having the detector propose stories and Jeff
correct them. So "recall 0.94" only ever meant *recall against the universe of
stories the detector already found once*. Nothing in the pipeline could see a story
the detector had never proposed. Every published accuracy claim rested on that gap.

The fix requires a story list built **independently of the detector**. We now have one.

## 2. The ground truth

`jeff comms/b.ketubot (1).doc` — Jeff Rubenstein's Ketubot story list.

| Property | Value |
|---|---|
| Created | **2005-02-02** (twenty years before this detector existed) |
| Last saved by | Jeffrey Rubenstein, 2026-01-05 |
| Extent | 19 pages, 6,791 words |
| Stories parsed | **149** across **55 dapim**, Ketubot 2b–111b |
| Columns | מיקום \| טקסט \| מקבילות \| הערות (location \| text \| parallels \| notes) |

Two things matter about this file beyond the numbers.

**It is genuinely detector-blind.** It predates the project by two decades. This is
the independent read the roadmap proposed commissioning (§4.1) — already done, at
zero cost in expert time.

**Jeff has already designed the database schema he asked us for.** His Part 2(d)
answer requested three extra per-story columns: notes, references to scholarship,
and Yerushalmi parallels. His 2005 table already has מקבילות (parallels — populated
with Yerushalmi and midrashic references) and הערות (notes). The crowd-sourced DB
should adopt this shape rather than invent one.

## 3. Result

Reproducible via [scripts/measure_recall_vs_expert_list.py](../../scripts/measure_recall_vs_expert_list.py):

| | Coverage of Jeff's 149 stories |
|---|---|
| **v10 detector** | **143 / 149 = 96.0%** |
| Golden dataset | 144 / 149 = 96.6% |
| Located in the text at all (matcher sanity check) | 149 / 149 |

**True recall on Ketubot is ~96%, not the 80–85% assumed.** The project is in
materially better shape than the roadmap believed.

### Honest limits on this number

1. **Ketubot is our most-tuned tractate** (ten golden iterations). This is not a
   generalization estimate. Kiddushin — or better, an unseen tractate — would be.
2. **Jeff's list is not exhaustive** and he says so: his lists are "imperfect," and
   "the AI has found stories his lists missed." The golden holds 182 Ketubot stories
   against his 149, consistent with that. So 96% is recall *against one expert's
   independent read*, which is the right benchmark to report — not against
   omniscience.
3. **"Covered" means segment overlap**, i.e. the detector found *a* story overlapping
   that text. It does not assert the boundaries agree. Boundary quality is a separate
   axis, measured by IoU in the harness.

## 4. Method (two non-obvious problems)

**Abbreviation mismatch.** Jeff writes unvocalized and heavily abbreviated (`א"ל`,
`ר"ע`, `ר'`); Sefaria's Davidson text is vocalized and spelled out (`אמר ליה`,
`רבי עקיבא`). Word-overlap matching collapses — the Rabbi Akiva story scored 0.41.
Hebrew **character 4-grams** are robust to this and score the same story at 1.00.

**Cross-page stories.** Expert story blocks routinely begin near the end of one daf
and finish on the next — Rabbi Akiva and Rachel starts at **Ketubot 62b segment 14**,
the last segment of the page. Any per-page matcher systematically undercounts. The
script sorts every segment in the tractate into one ordered sequence and slides a
window across daf boundaries.

Before both fixes, the same data appeared to show 89.7% recall with 34 stories
"unlocated." After: 96.0% with **zero** unlocated. If a matcher cannot find a famous
story that is plainly present, distrust the matcher before the detector.

## 5. The six misses — one coherent failure mode

Full per-story output: `results/recall/ketubot_jeff2005_matches.json`.

| Ref | Opening | Why it was likely missed |
|---|---|---|
| 20a | `בר שטיא זבין נכסי` | Real event resolved by a ruling (Rav Ashi). Current rule disqualifies "rabbi states legal opinion." |
| 77a | `אמר רב: האומר איני זן…` / `אכסוה שערי` | Same shape: halakhic ruling with a narrated reaction. **In golden, missed by v10** — a false negative against our own labels. |
| 67b | `אמרו עליו על הלל הזקן` | "They said about him" — opener absent from the introducer lexicon. |
| 82b | `בראשונה היו כותבין` | Institutional/historical narrative (Shimon ben Shetach's takanah). Opener absent from the lexicon. |
| 72b | `זימנא חדא הוה קאזילנא` | Story embedded inside a rabbi's quoted speech. |
| 53a | `יתיב רבין בר חנינא קמיה דרב חסדא` | Sitting-and-discussing frame reads as a speech-act. |

**Five of the six are also absent from the golden dataset** (all but 77a). They are
dataset gaps as much as detector gaps — adding them improves the asset regardless of
what the detector does next.

The clustering is the useful part. These are not six unrelated errors; they are
three recurring shapes:

1. **Halakhic story + ruling** (20a, 77a) — exactly the case Jeff's criteria
   ([jeff_story_definition_criteria.md](2026-07-06-jeff-story-definition-criteria.md)) says
   *is* a story: *"A man stole another man's cow and sold it. Rava ruled…. In this
   case you may have a story."* The detector's current anti-legal disqualifier is
   the direct cause.
2. **Openers outside the lexicon** (67b, 82b) — `אמרו עליו`, `בראשונה`.
3. **Narrative embedded in speech or discussion frames** (72b, 53a).

Shape (1) is squarely the Wave 6 criteria rewrite. That is the single strongest
argument for doing Wave 6 before Wave 5, and these six cases seed its conformance
test set.

## 6. What to do next with this

- **Ask Jeff which other tractates he has lists for.** This one file converted the
  project's biggest unknown into a number for free. A Kiddushin list would give a
  second, independent reading on a tractate tuned on less — a real generalization
  estimate. This should lead the reply to him.
- **Add the 5 missing stories to the Ketubot golden**, flagged with provenance
  (expert list, not detector-proposed).
- **Reuse the schema**: מקבילות and הערות become the parallels and notes columns of
  the crowd-sourced DB.
- **Correction to the ledger:** `validation/feedback/Kiddushin missesd stories.docx`
  is *not* comparable ground truth. It holds 5 entries — exactly the 5 already in
  `known_missing_stories`, two already recovered in Wave 1. It is a regression
  checklist, not a recall probe.
