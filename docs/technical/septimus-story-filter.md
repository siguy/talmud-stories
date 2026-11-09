# The Septimus story filter — what reaches the family site

**Owner:** Simon. **Code:** `scripts/build_site_data.py` (the only place it is applied).
**Guards:** `tests/test_site_data.py`. **Lesson:** L-045.

## The rule in one line

**Only definite stories reach the site.** If there is any reasonable doubt that a passage
is a story, it stays off.

## Two separate things — keep them separate

| | The scholarly catalogue (with Jeff) | The Septimus site |
|---|---|---|
| Purpose | Find **every** story; argue the edge cases | Give readers stories that are certainly stories |
| Maybes | **Matter.** BORDERLINE, LOW_CONFIDENCE and judge splits are the work: they go to Jeff, they set the rules, they measure recall | **Never shipped** |
| Where it lives | goldens (`results/canonical/`), detector runs, `docs/STORY_RULES.md`, judge outputs | `site/data/*.json`, built from those, read-only |
| Who changes it | Jeff's rulings, measured experiments | this filter |

The filter **never writes back**. It reads goldens, detector runs and judge outputs, and
writes only `site/data/`. Nothing about the site — a story it drops, a count it shows — is
evidence about a story's status in the catalogue, and nothing in the catalogue should be
tightened to make the site look cleaner. A BORDERLINE in a golden is Jeff's answer and is
kept there; it is just not shown to families.

## What ships

**A tractate Jeff has reviewed** (Ketubot, Kiddushin, Gittin — read from the golden):
- his `YES` and `HIGH_CONFIDENCE` stories in `stories[]`.

**A tractate he has not** (Yevamot, Berakhot — read from detector runs), all of:
1. the detector grades it `YES` or `HIGH_CONFIDENCE` **in every run listed** — the detector is
   not deterministic, so one run's YES is not definite;
2. it is in `stories[]`;
3. **both** consensus judges (Gemini and Claude, the same prompt, `judge_detector_spans.py`)
   call the passage a `story`.

Shown with `reviewed: false` and the page's "not yet checked by a scholar" notice.

## What never ships

- `BORDERLINE` — Jeff's own maybes (Simon, 2026-10-15)
- `LOW_CONFIDENCE` — the detector's maybes (Simon, 2026-10-12)
- `NOT_A_STORY`
- `mishnah_stories[]` — withheld by Stage 4g, never shown to Jeff, never judged
- a passage either judge calls `borderline`, `not`, `unsure` or `out_of_scope` (biblical, R-S1)
- a passage a judge call **failed** on — a failure is counted, never read as a yes (Lesson 21)

## The one principle behind every line

**A later gate may narrow what ships, never promote what an earlier one held back** (L-045).
Each check is an AND. The judges cannot rescue a LOW; a golden YES cannot rescue a passage the
judges were never asked about; one run cannot outvote another. Combining signals for the
site means taking their intersection. Anything that would *widen* what ships is a decision
for Simon, not a code change.

## Adding a tractate

1. Run the adopted detector **twice** on it (`scripts/run_new_tractate.py`).
2. Judge every span either run proposed:
   `JUDGE_PROMPT=<current prompt> JUDGE_TRACTATE=<T> python3 scripts/judge_detector_spans.py units`,
   then `gemini`, then `export` → Claude Code subagents → `import`. Add `<T>` to `TRACTATES` there.
3. Add it to `SOURCES` in `build_site_data.py` with both runs and its consensus directory.
4. Rebuild (`python3 scripts/build_site_data.py`), update `SITE_WORDS` in the test and §2 of
   `septimus-signup-plan.md`, check it in the browser, run the tests.

When Jeff reviews a tractate, switch its source to his golden and drop the judge gate — his
YES is the definite answer.

## History

- 2026-10-12 — site created; LOW not shipped; BORDERLINE shown as a separate tier; Mishnah
  stories shipped flagged.
- 2026-10-15 — Simon: no borderlines on the site (PR #67, never merged; superseded here).
- 2026-11-09 — this document. One rule for all tractates: BORDERLINE and Mishnah stories
  removed from the reviewed tractates; Yevamot moved from one v11 run to two v14 runs plus
  both judges; Berakhot added the same way. The first Berakhot export let the judges promote
  LOW_CONFIDENCE and read one run only — both fixed, L-045.
