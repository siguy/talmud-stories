# Story finder across all of Shas: plan (produces story list v1)

*Written 2026-11-08. Work item: [`work/2026-11-08-shas-finder-run.md`](../../work/2026-11-08-shas-finder-run.md).
Comes **before** the sign-up ([`septimus-signup-plan.md`](septimus-signup-plan.md)), which reads the list this produces.
Nothing here has been run. No API calls before Simon approves the plan and the cost.*

## 1. Where coverage stands (from `STATE.md`, generated 2026-11-08)

| Tractate | In repo | Expert list (BLIND) | Expert review rounds | Recall, end-to-end (strict) |
|---|---|---|---|---|
| Ketubot | detector run + golden | 149 stories | 6 | 87.2% |
| Kiddushin | detector run + golden | 90 | 5 | 83.3% |
| Gittin | detector run + golden | 111 | 3 | 97.3% |
| Yevamot | detector run (v11), no golden | 100 | 0 | 89.0% |
| Eruvin | Sefaria pages fetched (207), **never run** | 74 | 0 | — |
| 32 others | nothing | none | 0 | — |

**Eruvin has been run on Simon's machine** (not in the repo) and is **held until Jeff reviews it** (Simon,
2026-11-09). No other tractate has been run.

Recall is measured on Jeff's 2005 lists (BLIND). Story precision on reviewed rounds, read against the call Jeff was
shown, is ~0.92–0.95 (CIRCULAR, `docs/findings/2026-09-29-verdicts-read-against-the-call-shown.md`).

## 2. Scope: the 37 Bavli tractates with Gemara

Standard Vilna pagination; pages = amudim from 2a to the last daf.

| Order | Tractate | Last daf | Pages | Status |
|---|---|---|---|---|
| — | **Eruvin** | 105 | 208 | run locally; held for Jeff |
| 1 | — | | | (Berakhot is first) |
| 2 | Berakhot | 64 | 126 | |
| 3 | Shabbat | 157 | 312 | |
| 4 | Pesachim | 121 | 240 | |
| 5 | Yoma | 88 | 174 | |
| 6 | Sukkah | 56 | 110 | |
| 7 | Beitzah | 40 | 78 | |
| 8 | Rosh Hashanah | 35 | 68 | |
| 9 | Taanit | 31 | 60 | |
| 10 | Megillah | 32 | 62 | |
| 11 | Moed Katan | 29 | 56 | |
| 12 | Chagigah | 27 | 52 | |
| 13 | Nedarim | 91 | 180 | |
| 14 | Nazir | 66 | 130 | |
| 15 | Sotah | 49 | 96 | |
| 16 | Bava Kamma | 119 | 236 | |
| 17 | Bava Metzia | 119 | 236 | |
| 18 | Bava Batra | 176 | 350 | |
| 19 | Sanhedrin | 113 | 224 | |
| 20 | Makkot | 24 | 46 | |
| 21 | Shevuot | 49 | 96 | |
| 22 | Avodah Zarah | 76 | 150 | |
| 23 | Horayot | 14 | 26 | |
| 24 | Zevachim | 120 | 238 | |
| 25 | Menachot | 110 | 218 | |
| 26 | Chullin | 142 | 282 | |
| 27 | Bekhorot | 61 | 120 | |
| 28 | Arakhin | 34 | 66 | |
| 29 | Temurah | 34 | 66 | |
| 30 | Keritot | 28 | 54 | |
| 31 | Meilah | 22 | 42 | |
| 32 | Tamid | 33 | 64 | |
| 33 | Niddah | 73 | 144 | |
| — | Yevamot, Ketubot, Gittin, Kiddushin | — | 804 | done |
| | **Total to run** | | **4,610** | |

Order: Berakhot first (small, story-rich: the cost calibration run); then Seder Moed and the narrative-rich Nashim/Nezikin tractates; the technical Kodashim/Taharot tractates last.
Excluded: Shekalim (its Gemara is Yerushalmi), Kinnim and Middot (no Gemara). The page counts are from Vilna
pagination and are confirmed per tractate when the Sefaria fetch runs (Eruvin's cache holds 207, not 208).

## 3. Cost and time (measured on Berakhot 2026-11-08; the original estimate kept below)

**Measured — Berakhot full run, 2026-11-08** (`results/v11/berakhot/berakhot_v11.json` → `run_meta.tokens`, 0
unmetered calls). Prices: `gemini-3-flash-preview` Standard tier, $0.50 / M input, $3.00 / M output incl. thinking
(aistudio.google.com/docs/pricing, read 2026-11-08).

| Stage | Calls | Input tokens | Output tokens | Cost |
|---|---|---|---|---|
| Stage 1 (triage) | 123 | 652,958 | 128,326 | $0.71 |
| Stage 2 + twin + Stage 4 | 699 | 2,622,303 | 254,709 | $2.08 |
| **Total, 125 pages** | 822 | 3,275,261 | 383,035 | **$2.79 = $0.022 / page** |

Thinking tokens: 0, since thinking is off. Two pages' triage came from the 2-page smoke test's cache (smoke cost $0.03,
not counted above). Per page: triage ~5.3k in / 1.0k out; Stage 2 + twin ~21k in / 2.0k out. **Wall time was 39 min**
(18.7 s/page): Stage 1 took 10 min, and Stage 2 onward took 29 min. `run_meta.elapsed_seconds` (1,738) times
**Stage 2 onward only**, so the "242 pages in 21 minutes" for Yevamot below leaves out its triage too. Measured per
page *examined* by Stage 2, Berakhot ran 16.4 s and Yevamot 11.9 s, about 1.4×. Both tractates examined 106 pages:
Yevamot skipped 136 at triage, Berakhot 19. Indicated cause: Berakhot proposes more stories (212 vs 168), so it makes
more twin and span calls, and its pages are longer (22 vs 16 segments/page).

**Re-quote, the other 31 tractates (4,276 pages): ~$95** at $0.022/page (vs ~$175 estimated), and **~22 hours** one
at a time at 18.7 s/page (vs ~6.5). Time scales with how many pages pass triage. Cost per page varies with how much each tractate triages in. Berakhot is story-dense, so this
quote is more likely high than low.

### The original estimate (2026-11-08, before measurement)

Nothing on disk records tokens or dollars: `run_meta` has elapsed time only. Measured: the Yevamot v11 run did
**242 pages in 21 minutes** (~5.2 s/page, twin pass on).

Estimate per page (Gemini 3 Flash, twin pass on, rounded up): triage ~6k tokens in / 1k out; Stage 2 + twin pass
~30k in / 5k out. At list prices (~$0.50 per million tokens in, ~$3 per million out) that is **~$0.04 per page**.

| | Pages | Cost (estimated) | Wall time, one at a time |
|---|---|---|---|
| Berakhot (calibration) | 126 | ~$5 | ~11 min |
| All 32 remaining (Eruvin held) | 4,402 | **~$175** (range $90–$350) | ~6.5 hours |

The range is wide because the token counts are guesses. **Step 0 makes it a measurement:** record token usage in
`run_meta` (a few lines in `scripts/run_new_tractate.py`, no change to detection), run Berakhot, and price the rest
from its real tokens before spending more. If Berakhot comes in more than 50% above the estimate, stop and
re-quote to Simon.

A second run per tractate (the union of two runs catches ~3–5 more stories per 100, because the detector is not
deterministic: Lesson 43) doubles the cost. **Not in list v1.** It is a candidate for list v2.

## 4. Steps

0. **Pre-flight (no API calls).** Close `work/2026-11-07-pre-eruvin-run-fixes.md`: its checklist is ticked and
   #69–#73 merged, but it has no Outcome. Generalise the runner past its hard-coded `KNOWN` tractate list
   (`scripts/run_new_tractate.py:49`) and the `SOURCES` map; add Sefaria fetch for any tractate; add token logging.
   Tests for each (failure injection where a failure could be stamped as "no stories": Lesson 21).
1. **Eruvin: held** until Jeff reviews it (Simon, 2026-11-09). Its local run joins the repo when he has; it is then
   scored once against `results/expert_lists/eruvin_2005.json` (BLIND), end-to-end and given-triage, both named.
2. **The other 32**, Berakhot first (smoke test on 2 pages, then full; price the rest from its tokens): fetch → run → structural checks (§5). One tractate per commit, so a
   failure re-runs one tractate, not Shas.
3. **Build list v1**: `site/data/` for all tractates with the same ship rule (YES + HIGH_CONFIDENCE = story,
   BORDERLINE its own tier, LOW_CONFIDENCE not shipped), dated, `list_version: v1`.

**Configuration ("latest rules, most accurate process", Simon 2026-11-09):** the runner's defaults. Detector = the
module `scripts/run_new_tractate.py` imports (v11, with the 2026-11-07 run-path fixes); model `gemini-3-flash-preview`,
thinking off, twin pass on, Stage 1 rule `N>=1`. This is the configuration measured best on Yevamot (92–94%, BLIND).
The newest rule wording (v13/v14, which carries Jeff's 2026-10-07 and 2026-10-25 rulings) was measured on a slice and
made more errors, so it is **not** used (`docs/findings/2026-11-07-detector-v13-slice.md`). Jeff's rulings still
reach the list where they matter: through the goldens and `STORY_RULES.md`, not the detector prompt.
Step 0 status: runner takes any fetched tractate and records `run_meta.tokens` per stage (done 2026-11-09, tested).
No prompt or model change rides on this run. If one is proposed, it is its own measured item with a same-code repeat.

## 5. How quality is gated without an expert round

- Every tractate other than the four reviewed ones is labelled **"not yet reviewed"**, as Yevamot is.
- **Hard gates per tractate** (the run is refused, not shipped): every Sefaria page present in the output; zero
  pages with `stage2_error` (the site build already refuses these); zero failed triage pages left after one retry.
- **Indicated quality:** stories per page in the range seen on the four done tractates; any tractate far outside it
  gets 10 random stories read by Simon before it ships (stated as indicated, not measured).
- **Measured quality** only where a blind list exists: Eruvin. Every other tractate's precision and recall are
  unknown until Jeff (or someone) reviews it, and the site says so.

## 6. What Simon does

1. Answer §8.
2. Approve the Berakhot calibration (~$5), then the rest (~$175, re-quoted from Berakhot's real tokens).
3. Provide a Gemini API key through the secure credential form when the run starts (never in chat). Alternatively,
   run the commands on his own machine, where `.env` already has the key.
4. Read 10 stories from any tractate that fails the indicated-quality check.

## 7. Parallelism

`python3 scripts/board.py lanes` today: 39 open items, **3 lanes**, one serial lane of 37. The Shas run is one new
item writing `results/sefaria/`, `results/triage/`, `results/v11/<tractate>/`, `scripts/run_new_tractate.py` and
`site/data/`. It can run beside the sign-up work only after PR a (word counts) merges, because both write
`site/data/` and `scripts/build_site_data.py`. Several tractates can run at once in one session if Gemini rate
limits allow; that is one lane, not several.

## 8. Open questions

1. ~~Where are the other tractates?~~ Answered 2026-11-09: only Eruvin, on Simon's machine, held for Jeff.
2. ~~Run Eruvin now?~~ Answered: no, wait for Jeff.
3. ~~Approve Berakhot?~~ Approved 2026-11-09 (~$5), "latest rules and the most accurate version of the process".
   Read as: the runner's measured-best configuration (§4). Runs on Simon's machine: this cloud container cannot reach
   Sefaria or Gemini. Prompt: [`shas-run-local-prompt.md`](shas-run-local-prompt.md).
4. Approve the re-quoted total for the other 31, once Berakhot has measured it.
