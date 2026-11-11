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
- `YES` and `HIGH_CONFIDENCE` stories in `stories[]` **that Jeff himself answered yes to** —
  a verdict read as yes (`scripts/verdict_reading.py`, via `results/rulers/<t>_ruler.json`) or
  a story on his 2005 list. The golden also carries a few detector calls he never saw
  (Ketubot 17a:3, a habitual "would"); those do not ship.

**A tractate he has not** (Yevamot, Berakhot — read from detector runs):
- the adopted detector grades it `YES` or `HIGH_CONFIDENCE` **in every run listed** (two) — the
  detector is not deterministic, so one run's YES is not definite;
- it is in `stories[]`;
- it is **not** a passage the Gemini judge calls `out_of_scope` and the Claude judge calls `not` — not a story
  at all (Simon, 2026-11-10).

**Biblical stories ship** (Simon, 2026-11-10: fine for the site "as long as they are classified as stories outside
of the fact they have biblical figure"; flag them and exclude them for Jeff's scholarly project). A story is
flagged `biblical: true` when both judges call it `out_of_scope` (or Claude alone, under
`results/shas_run/decisions.json`), when it is hand-flagged there, or when detector **v15's** Stage 4j rule
(`biblical_flag` in `src/story_detector_v15.py`) says its actors are biblical. The v15 rule is re-applied at build
time to the actor list every run already holds, so it needs no re-run; a story with no actor list keeps v14's 4j
record (`docs/findings/2026-11-11-v15-biblical-flag.md`). For a 4j demotion the site reads the grade **from before** that filter
(`classification_pre_biblical_filter`). This removes a filter rather than letting a gate promote: the both-runs
rule still applies to that grade. Jeff's catalogue excludes every flagged story.

Shown with `reviewed: false` and the page's "not yet checked by a scholar" notice.

**Why the detector's own grade, and not the judges** (Simon, 2026-11-09). Where Jeff reviewed
the detector's YES/HIGH calls, 141 of 155 were his yes (91%), 8 borderline, 6 no — the rules
built from his rulings work. The Gemini judge is the detector's own model
(`gemini-3-flash-preview`) and passes nearly everything the detector does. The Claude judge is
the only independent check, and it drops ~13% of the detector stories Jeff calls yes — and about
half of Yevamot's. Requiring both judges cut Yevamot from 83 passages to 40. The judges stay in
the scholarly work, where a disagreement is a question worth asking.

## What never ships

- `BORDERLINE` — Jeff's own maybes (Simon, 2026-10-15)
- `LOW_CONFIDENCE` — the detector's maybes (Simon, 2026-10-12)
- `NOT_A_STORY`
- `mishnah_stories[]` — withheld by Stage 4g, never shown to Jeff
- a golden story Jeff never answered
- an unreviewed story the detector grades below YES/HIGH in any run
- a passage Gemini calls `out_of_scope` and Claude calls `not` (not a story at all)
- the same span proposed twice ships once (counted and named on stderr)

## The one principle behind every line

**A later gate may narrow what ships, never promote what an earlier one held back** (L-045).
Each check is an AND. The judges cannot rescue a LOW; a golden YES cannot rescue a passage Jeff
never answered; one run cannot outvote another. Combining signals for the
site means taking their intersection. Anything that would *widen* what ships is a decision
for Simon, not a code change.

## Adding a tractate

1. Run the adopted detector **twice** on it (`scripts/run_new_tractate.py`).
2. For the biblical check, judge every span either run proposed:
   `JUDGE_PROMPT=<current prompt> JUDGE_TRACTATE=<T> python3 scripts/judge_detector_spans.py units`,
   then `gemini`, then `export` → Claude Code subagents → `import`. Add `<T>` to `TRACTATES` there.
3. Add it to `SOURCES` in `build_site_data.py` with both runs and `scope_judges`.
4. Rebuild (`python3 scripts/build_site_data.py`), update `SITE_WORDS` in the test and §2 of
   `septimus-signup-plan.md`, check it in the browser, run the tests.

When Jeff reviews a tractate, switch its source to his golden and its ruler — his yes is the
definite answer.

## History

- 2026-10-12 — site created; LOW not shipped; BORDERLINE shown as a separate tier; Mishnah
  stories shipped flagged.
- 2026-10-15 — Simon: no borderlines on the site (PR #67, never merged; superseded here).
- 2026-11-09 — this document. One rule for all tractates: BORDERLINE and Mishnah stories
  removed from the reviewed tractates; Yevamot moved from one v11 run to two v14 runs plus
  both judges; Berakhot added the same way. The first Berakhot export let the judges promote
  LOW_CONFIDENCE and read one run only — both fixed, L-045.
- 2026-11-09, later — Simon: the judges are not the gate. Unreviewed tractates ship the detector's
  YES/HIGH in both runs (Yevamot 82, Berakhot 112), minus biblical passages both judges flag.
  Reviewed tractates ship only stories with Jeff's own yes behind them (Ketubot 17a:3 removed).
- 2026-11-10 — Simon: biblical stories ship, flagged `biblical` and excluded from Jeff's catalogue,
  including those Stage 4j demoted. The one judge narrowing becomes Gemini-biblical plus
  Claude-not-a-story (5 passages across Shas, per `docs/findings/2026-11-10-shas-accuracy.md`). The site
  went from 1,803 to 1,897 stories, 102 of them flagged.
- 2026-11-11 — the detector's flag moves from v14's name list to v15's rule (Simon's 2026-11-10 approval). On the
  site: 1,897 stories unchanged, flagged 102 → 97 — five post-biblical stories v14 mistook for biblical (Elisha
  "Man of Wings" twice, Miriam of Tarmod, the pious man and Elijah, Elijah and the starving child). Every passage
  v15 newly flags on a shipped story was already flagged by the judges or by hand.
