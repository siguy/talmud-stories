# Plan: run all of Shas for the Septimus site by Sunday 2026-11-15, reusable for Jeff

*Written 2026-11-09. Planning only: no API calls, no detector runs, no merges were made writing it.
Stacks on PR siguy/talmud-stories#84. Supersedes the cost and configuration sections of
[`docs/technical/shas-finder-plan.md`](../technical/shas-finder-plan.md) (§3 and §4 there still say v11 and one run;
the adopted detector is v14 and the site needs two runs). Its scope table (§2) still stands, with the corrections in §6.4.*

**The short version.** It is feasible, with about two days of slack. The model calls themselves are about half a day of
wall time; the risk is in the code that has to be written first, and in people. Run detector v14 as it is, twice per
tractate. Use Google's **Flex** tier (same code path, half price), not the **Batch API** (half price too, but it would
mean rebuilding the pipeline). Estimated cost: **~$65 on Flex, ~$130 on the standard tier**, for 31 tractates, two runs
each, plus the scope judge. Nothing in the detector or its prompts needs changing.

Terms used below:
- **Standard / Flex / Batch** are three ways Google serves the same model. *Standard* answers in seconds at full price.
  *Flex* is the same call, answered when Google has spare capacity (seconds to minutes), at half price. *Batch* means
  uploading a file of thousands of requests and collecting the answers later (up to 24 hours), also at half price.
- **TPM** = tokens per minute, Google's rate limit. A token is roughly ¾ of an English word (fewer for Hebrew).
- **Gate** = an automatic check that stops one tractate from going further if it fails.
- **Examined page** = a page that survived Stage 1 triage and went to Stage 2. Only examined pages cost real money.

---

## 1. Is it feasible by Sunday? Yes, if the pre-flight code lands by Tuesday night

### What has to happen, in order

```
fetch text (31 tractates) ─┐
pre-flight code + tests ───┼─► triage (once per tractate) ─► run 1 ┐
merge #82 → #83 → #84 ─────┘                               run 2 ┴─► gates ─► Gemini judge ─► Claude judge* ─► site build ─► Simon reads samples ─► deploy
```
\* Claude judges only the passages Gemini calls out of scope (§2.5). That is what keeps it off the critical path.

### How long the machine work takes (from measured runs)

| step | measured basis | Shas estimate | at 8 tractates in parallel |
|---|---|---|---|
| Sefaria fetch | sequential, polite delay | 4,276 pages, ~1–3 h | run 2–3 tractates at once: ~1 h |
| Stage 1 triage | **never measured** (both v14 runs used a cached triage) | ~5 s/page guess → ~6 h serial | **~45 min** |
| Stage 2+4, one run | Berakhot 1,760 s for 106 examined pages = 16.6 s/page | ~2,140 examined pages → ~10 h | **~1.25 h** |
| Stage 2+4, both runs | | ~20 h serial | **~2.5 h** |
| Gemini judge | Berakhot 224 units, threaded | ~4,100 units | ~1 h |
| Claude judge (subset) | 20 units per subagent | ~150–250 units → ~10 subagents | ~1 h |

So the model work fits inside one working day. Flex may stretch it (§5.3): Google targets "1–15 minutes" per Flex
request when it is busy. That is why the schedule leaves Wednesday and Thursday for it.

### Day by day

| day | what runs | who | done when |
|---|---|---|---|
| **Mon 11-09** (tonight) | Simon reads this, answers §7 | Simon | §7 answered |
| **Tue 11-10** | Merge #82 → #83 → #84 (or branch off #84). Pre-flight code, §4 items 1–7, with tests. **In the background, from the morning:** Sefaria fetch of all 31 tractates (free, needs none of the new code). Evening: Flex smoke test (10 Berakhot pages, ~$0.10) | Claude session on Simon's Mac | tests green; fetch gates G1 green; Flex verdict |
| **Wed 11-11** | Triage all 31 (`--triage-only`), then run 1 and run 2 of every tractate, 8 processes at a time, largest tractates first | the driver, unattended | every tractate past G2–G4, or named as failed |
| **Thu 11-12** | Re-run whatever failed (resume, not restart). Gemini judge on every tractate. Export the Claude subset | driver + Claude session | G5–G6 green |
| **Fri 11-13** | Claude subagents judge the subset; import; build `site/data/`; tests; check the site in a browser. Simon reads the samples (§2.6) | Claude session, Simon ~1 h | PR ready |
| **Sat 11-14** | **Slack.** Nothing is scheduled. Simon decides whether unattended runs may continue (§7 Q6) | — | — |
| **Sun 11-15** | Merge, deploy | Simon | live |

**Critical path:** pre-flight code (Tue) → triage → two runs (Wed) → judges (Thu–Fri) → site build → Simon's samples
→ deploy. The fetch is off the critical path as long as it starts Tuesday morning. **Slack: Thursday plus Saturday,
about two days.** The one thing that eats it is a pre-flight change that breaks something and is found late. That is
why §4 keeps every change outside the detector, and why the Flex switch defaults to off.

**What can run in parallel:** fetch beside the code work; tractates beside each other (separate processes, separate
output files); run 1 beside run 2 of the same tractate, **once its triage cache is written** (both read it; if both
triaged at once they would race to write it). The runner's checkpoint file sits beside its `--output`, so two runs with
different outputs never share one (`scripts/run_new_tractate.py:338`).

**Rate limit:** today's 3M TPM error came from four judge runs, each with its own thread pool. One detector process
uses about 90k TPM (24k tokens in per page every 16.6 s). Eight processes ≈ 0.75M TPM, a quarter of the quota.
The runner already retries a 429 (rate-limit error). Do not run any other Gemini work on the key that day.

---

## 2. The process: one driver, a gate after every step, and nothing a person has to remember

### 2.1 Shape

A new script, `scripts/run_shas.py` (not a detector change). For each tractate it walks one state machine and writes
where it got to in `results/shas_run/status.json`:

`fetched → triaged → run1 → run2 → gated → judged_gemini → claude_exported → claude_imported → in_site`

- Each step calls the script that already does it (`fetch_tractate_pages.py`, `run_new_tractate.py --triage-only`,
  `run_new_tractate.py --output results/v14/<t>/run{1,2}.json`, `judge_detector_spans.py …`). The driver adds order,
  parallelism and checks. It adds no detection logic.
- **Resume is the default.** Re-running the driver skips every step whose output exists and passed its gate, and
  resumes the rest from their own checkpoints (the runner already does this for Stage 1 and Stage 2).
- **A failed tractate stops; the others carry on** (CLAUDE.md: one source failing never stops the run). It is named in
  `status.json` with the gate that stopped it.
- `--parallel 8`, largest tractates first, so the long ones are not left running alone at the end.
- Every step logs tractate, step and counts to `project.log`.

### 2.2 The gates (a tractate that fails one goes no further)

| gate | after | checks | measured baseline |
|---|---|---|---|
| **G1 text** | fetch | page count equals Sefaria's own shape index; refs contiguous; every page has segments; every segment has non-empty Hebrew **and** English; Hebrew carries vowel points (nikud) on ≥ 95% of segments (a page of bare consonants means a different text version came back) | Gittin, Yevamot, Eruvin caches |
| **G2 triage** | triage | every page labelled; `triage_failed = 0` after one resume; SHA-1 of the triage cache recorded | — |
| **G3 run health** | each run | every fetched page in the output; `stage2_errors`, `twin_failures`, `pass2_failures`, `truncated_responses` and the top-level `stage4_call_failures` all **0**; `empty_responses ≤ 2`, listed; `tokens.*.unmetered = 0`; `detector_module = src.story_detector_v14`, model `gemini-3-flash-preview`, thinking off, `twin_trigger = all`; **triage SHA unchanged** (proves the run did not re-triage); span sanity: every story `start ≤ end` inside its page, span repairs ≤ 3 | Berakhot and Yevamot v14: all 0; empty responses 0–2; span repairs 0–2 |
| **G4 two runs agree** | run 2 | same `git_rev`, same model, same triage SHA; kept-story counts within 10% of each other; share of definite passages that are definite in **both** runs not far below Berakhot's and Yevamot's (the driver computes both tractates' figure first and uses the lower as the floor) | Berakhot 189 vs 187; Yevamot 154 vs 151 |
| **G5 density** | gated | stories per examined page inside the range of the five run tractates. Outside it is **amber**, not red: the tractate continues, Simon reads 10 random stories | Berakhot 1.8, Yevamot 1.5 per examined page |
| **G6 judges** | judges | 0 `failed` / `invalid` after one resume; judge prompt SHA `84bfb33fd32a` (v2) on every tractate | Berakhot 224/224 valid |
| **G7 site** | build | `python3 -m pytest tests/ -q` (L-045's guards: nothing below YES/HIGH ships, definite in both runs, no biblical) | — |

### 2.3 What a person looks at, and what never needs one

- **Never needs a person:** a tractate with every gate green. That is the design goal: about 30 of 31.
- **Needs Claude (not Simon):** any red gate. Read `status.json` and `project.log`, fix the cause, resume. A second
  failure at the same gate goes to Simon with the error.
- **Needs Simon (~1 hour on Friday):** 10 stories from any amber (G5) tractate; 10 from Sanhedrin, Sotah and Megillah
  together, where biblical retelling is densest and the scope filter carries the most load (§6.6); and one look at the
  site.
- **Never Jeff, this week.** See §6.8.

### 2.4 Logged per tractate (all already in `run_meta` unless marked new)

Pages fetched / examined / skipped; triage SHA; per-stage calls and tokens; **new:** cached tokens and the model
version string Google returns (§4 item 4); **new:** service tier (standard or flex); elapsed time; every failure
counter; `git_rev`; `stage2_fingerprint` (the prompt's fingerprint). The driver adds the gate results and dollar cost
per tractate (tokens × the prices in §5.2).

### 2.5 The judges: Gemini on everything, Claude only where it can change the site

The site drops a passage only when **both** judges call it `out_of_scope` (`biblical_cells()`,
`scripts/build_site_data.py:45`). So Claude's answer matters to the site only on passages Gemini already called
`out_of_scope`. On Berakhot that was 7 of 224 units; on Yevamot 10 of 184. Asking Claude about only those gives the
**same site, exactly**, with ~10 subagent batches instead of ~200. The other units are judged by Claude later, for Jeff
(§3), off the deadline.

This is a narrowing of *what we ask*, not of *the rule*: the site rule is unchanged, and a test should pin that an
unanswered unit ships (as it does now: a missing Claude verdict is never `out_of_scope`).

### 2.6 Why this is accurate enough without an expert round

Precision of the detector's YES/HIGH, where Jeff reviewed it: 141 of 155 his yes (91%,
`docs/technical/septimus-story-filter.md`). Requiring both runs removes the coin-flip cases. Every unreviewed tractate
ships with `reviewed: false` and the "not yet checked by a scholar" notice, as Yevamot and Berakhot do now.

---

## 3. Making the run serve Jeff later

**Keep everything the run produces. Nothing extra has to be computed this week; it has to not be thrown away.**

Already in every run file, and must be committed whole (not filtered to what the site uses):
- `stories[]` at **every** grade: YES, HIGH, LOW, `NOT_A_STORY`. LOW and `NOT_A_STORY` are the borderline and rejected
  calls Jeff's rulings are written about.
- `mishnah_stories[]` (Stage 4g withheld them; Jeff has never seen them).
- `twin_verdicts`, `span_repairs`, page-level `skipped_by_triage`. The skipped pages are where any recall loss starts
  (triage recall is ~95%).
- `run_meta`: configuration, fingerprint, tokens, failures.

Also commit: the Sefaria text and triage cache per tractate (a later re-run then reads the identical input), the judge
`units.json`, `gemini.json` for **all** units, and `claude.json` marked in its meta as a partial subset.

**New, cheap, worth having:**
- **The two-run disagreement, per tractate**, as its own file: passages definite in one run and not the other, and
  grade shifts. It is the cheapest uncertainty signal there is, and it is exactly the list of passages to show Jeff
  first. (Script: generalise `compare_v14_v11_*.py` to v14-vs-v14; no model calls.)
- **Cross-tractate parallels.** The Bavli repeats many stories in several tractates. A shared-text match across all
  run files (no model calls) is scholarly material for Jeff, and tells the site where a family will meet the same story
  twice (§6.7).

**Open questions: which touch the run, which only touch reading it later**

| question | touches the run? | why |
|---|---|---|
| R-S1 biblical scope edges (`jeff:scope-edges`) | **for the site only** | handled after the run, by the judges, and re-appliable to files on disk |
| R-C2 question-and-answer (`jeff:question-and-answer`) | no | v14 grades these LOW or `NOT_A_STORY`; both are kept. If Jeff says they are stories, they are re-read, not re-found |
| R-C0 "one event, then a ruling" / judge prompt v4 | no | not adopted (`docs/findings/2026-11-09-judge-register-v4.md`); it moves borderline → not, which never ships anyway |
| boundary-end rule | no | boundaries can be re-cut on the saved spans |
| a ruling that **widens** what a story is | **yes, in principle** | spans v14 never proposed are not on disk. Acceptable: no such ruling is pending, and it would mean a new detector version anyway |
| Eruvin held for Jeff | for the site | §7 Q4 |

---

## 4. What, if anything, to change: nothing in the detector; seven small things around it

**The detector: run it as is.** v14 is adopted, measured on two tractates, and carries Jeff's rulings to 10-25. Every
alternative (v15 biblical filter, judge v4, model 3.8, prompt reordering for caching) is a measured experiment of its
own and does not fit the week. The rule is in CLAUDE.md: no prompt or model change rides on this run.

**Ranked by value against deadline risk** (all outside `src/`; each with a test):

| # | change | value | risk | note |
|---|---|---|---|---|
| 1 | Merge #82 → #83 → #84 (or run from #84's branch) | required: v14 import and the site filter live there | low | Simon's call (§7 Q3) |
| 2 | `scripts/check_tractate_run.py`: gates G1–G6 as one read-only script | high | low | reads files, writes a report |
| 3 | `scripts/run_shas.py`: the driver (§2.1) | high | low–medium | calls existing scripts; resume by output presence |
| 4 | Token meter also records `cached_content_token_count` and `response.model_version`; runner records service tier | medium: cost becomes exact, reproducibility | very low | `scripts/run_new_tractate.py` `TokenMeter` only |
| 5 | Convention-based sources: `build_site_data.py` `SOURCES` and `judge_detector_spans.py` `TRACTATES` read `results/v14/<t>/run{1,2}.json` and `results/consensus/<t>/` for any tractate; `SITE_WORDS` in the test read from a generated file | high: otherwise ~90 hand edits | low | keeps the hand entries for the five existing tractates |
| 6 | `judge_detector_spans.py export --only-gemini-out-of-scope` | high: ~200 subagent batches → ~10 | low | §2.5; test that the site output is identical on Berakhot and Yevamot |
| 7 | Flex tier, off by default: `GEMINI_SERVICE_TIER=flex` read by the runner's existing wrapper around `generate_content` (it already wraps every call to count tokens), which adds `service_tier` and a ≥ 600 s timeout to the call's config. Same for the judge's Gemini backend | ~$65 | low–medium | no detector file is touched. Ships only if the smoke test (§5.3) passes |
| — | **Not this week:** Batch API rewrite; v15 biblical filter; judge prompt v4; switching model; explicit caching; Shekalim | | high | §5.4, §6 |

---

## 5. Cost, and whether the Batch discount stacks

### 5.1 Simon's premise, checked against Google's pages (fetched 2026-11-09)

- **The detector uses `gemini-3-flash-preview`** (`src/model_config.py` `DEFAULT_MODEL`; every v14 `run_meta`).
  Google's pricing page calls it "our legacy Flash model". It supports Batch, Flex and caching (its model page). No
  shutdown date is listed.
- **Its price:** standard $0.50 in / $3.00 out per million tokens. **Batch: $0.25 / $1.50. Flex: $0.25 / $1.50.** No
  promotion is listed for it.
- **"50% off on top of 50% off of 3.7 and 3.8":** there is **no 3.7** on the pricing page (3.6 and 3.8). 3.8 Flash is
  $0.75 / $3.75 now, rising to $1.50 / $7.50 on 1 January 2027, so today's 3.8 price is in effect half its 2027
  price, and 3.8 Batch ($0.375 / $1.875) is half of that. **So the stack is real, but only on 3.8, and 3.8 on Batch
  still costs more than our model on Flex** ($0.375 vs $0.25 in). 3.8 also measured worse on Jeff's list: 75.0% vs
  83.3% recall, 4 truncations (`docs/findings/2026-09-14-default-model-measured.md`). Cheapest and most accurate is the
  model we have, at half price.
- **Batch and Flex do not stack with each other.** They are two tiers at the same half price. Context caching is
  billed at its own rate on top of either.
- **Caching.** *Implicit* caching (Google reuses a prompt's repeated opening automatically) is on by default for 2.5 and
  newer, with no stated discount percentage, and Google lists no minimum size for `gemini-3-flash-preview`. Our Stage 2
  prompt opens with the same rules every call, so some of it may already be cached and billed cheaper; we do not know,
  because the meter does not record it (§4 item 4). *Explicit* caching would mean restructuring the prompt, which is a
  detector change: out.
- **Rate limits for Batch** are tier-dependent: 3M enqueued tokens on Tier 1 (useless for us), 400M on Tier 2 (Gemini
  3.8 figures; none are published for `gemini-3-flash-preview`). Flex gets no extra limits; it counts against the
  normal TPM.

Sources: [pricing](https://aistudio.google.com/docs/pricing), [Batch API](https://aistudio.google.com/docs/batch-api),
[Flex inference](https://ai.google.dev/gemini-api/docs/flex-inference),
[gemini-3-flash-preview model page](https://aistudio.google.com/docs/models/gemini-3-flash-preview),
[caching](https://aistudio.google.com/docs/caching), [rate limits](https://aistudio.google.com/docs/rate-limits).
Google moves these pages (each `ai.google.dev` link now redirects to `aistudio.google.com`) and changes prices; re-check
on the day.

### 5.2 The estimate

**Measured inputs** (v14, `run_meta.tokens`, Stage 2+4, per run):

| | examined pages | tokens in | tokens out | $ standard | $ per examined page |
|---|---|---|---|---|---|
| Berakhot run 1 | 106 of 125 | 2.77M | 0.26M | $2.16 | $0.0204 |
| Yevamot run 1 | 106 of 242 | 2.36M | 0.22M | $1.83 | $0.0173 |

**Assumed:** 4,276 pages in the 31 tractates (plan §2 less Berakhot and Eruvin; Tamid is smaller, §6.4). Share
examined: Berakhot 85%, Gittin ~51%, Yevamot 44%. The Kodashim and Taharot tractates will sit lower, so **50% central,
40–65% range** (~1,710–2,780 examined pages). Triage has **never been metered**: ~5k tokens in, ~0.7k out per page
(the prompt is ~10k characters plus the page). Gemini judge: ~1.9 units per examined page (Berakhot 2.1, Yevamot 1.7),
~$0.007 per unit (the script's own estimate on Berakhot).

| item | standard | Flex or Batch |
|---|---|---|
| Stage 1 triage, once (shared by both runs) | ~$20 ($13–30) | ~$10 |
| Stage 2+4, run 1 | ~$41 ($30–57) | ~$20 |
| Stage 2+4, run 2 | ~$41 ($30–57) | ~$20 |
| Gemini judge, all ~4,100 units | ~$29 | ~$15 |
| Claude judge | $0 API (subagents) | $0 |
| Retries, smoke tests (+10%) | ~$13 | ~$7 |
| **Total** | **~$145 ($110–190)** | **~$72 ($55–95)** |

The second run costs ~$41 standard / ~$20 Flex. It is what makes "definite" mean definite (L-045), so it is not
optional for the site. The Gemini judge on non-site units (~$15 of the Flex figure) is optional; it is kept because
it is the consensus record Jeff's work uses, and it makes `units.json` complete.

**Hard stop:** the driver sums cost from tokens after every tractate and stops starting new ones above the cap Simon
sets (§7 Q2). Separately, set a budget alert in Google Cloud billing.

### 5.3 Flex: the recommendation, and the test before using it

Flex is the same `generate_content` call with one extra setting, so the pipeline, its order and its checkpoints stay
exactly as measured. Two risks: (a) it is a **preview** feature, and a busy Flex queue returns 429/503 with no fallback
(the runner already retries both); (b) latency, "1–15 min" targeted when busy, would slow a serial runner badly.

**Smoke test, Tuesday evening (~$0.10):** 10 Berakhot pages with Flex. Pass if: 0 errors after retries; median call
≤ 30 s; and the kept stories on those pages differ from the two standard runs no more than the two standard runs
differ from each other. Fail → run standard and spend ~$70 more. One Flex/standard difference is not a finding about
Flex (Lesson 22); the test only asks whether it is inside the noise we already measured.

### 5.4 Batch: not this week

Batch is asynchronous: send a file, wait up to 24 h, collect. The pipeline is not one call per page. It is about six
rounds, each depending on the previous one's answers:

1. Stage 1 triage (independent per page: batchable as is)
2. Stage 2 first pass (independent per page given triage)
3. Stage 2 "find more stories" pass (only on pages where 2 found one; its prompt lists 2's stories)
4. twin pass (built from the merged 2+3 output)
5. Stage 4d stitch and 4f continuation (built from the merged, page-sorted results of all pages)
6. Stage 4k clause spans (built from the final stories)

To batch it, every round becomes a submit, wait, collect, and a replay of the detector's own code with the answers
filled in. That is a rewrite of the call path in a frozen detector (or a v15), worst case six 24-hour waits, and it
saves the same 50% as Flex. **Not worth it this week.** Worth reconsidering only for a much larger future job (a full
re-run of Shas after a new detector version), and only if Flex turns out unusable.

---

## 6. What else you may not be thinking of

1. **The deadline risk is code, not compute.** The models are ~½ day. Every change in §4 sits outside the detector,
   is tested, and has a fallback (Flex off; hand-run the scripts if the driver breaks).
2. **Where it runs.** The cloud container cannot reach Sefaria or Gemini, so it runs on Simon's Mac: plugged in, awake
   (the app can keep it awake), on a stable network, for about a day. The key stays in `.env`, never in chat.
3. **Quota sharing.** Any other Gemini work on the same key (judge experiments, another session) shares the 3M TPM.
   Wednesday is Shas-only.
4. **Tractate structure.**
   - **Tamid:** the Bavli Gemara starts at 25b, so it is ~17 amudim, not the 64 in the plan table. The fetch derives
     pages from Sefaria's shape index, so this corrects itself; G1 checks against the same index.
   - **Shekalim** is Yerushalmi (different structure: halakhot, not dapim; Bavli-trained few-shots). Daf Yomi learners
     include it in "Shas". Recommend: not this week, list v2 (§7 Q5). **Kinnim and Middot** have no Gemara; excluded.
   - **Very long tractates** (Bava Batra 350 pages, Shabbat 312, Chullin 282) start first.
   - **Mishnah-heavy pages:** Stage 4g withholds Mishnah-only stories, kept in `mishnah_stories[]`; nothing to do.
5. **Few-shots come from Ketubot and Kiddushin.** On Kodashim (sacrifices) that is new territory for the detector.
   Watch G5 there.
6. **The biblical filter carries more load outside Berakhot.** Sanhedrin (Perek Ḥelek), Sotah, Megillah (Esther) and
   Bava Batra are full of biblical retelling. The site removes a passage only when both judges say out of scope; on
   Berakhot both caught all five that the detector kept. That is why Simon's sample (§2.3) includes those tractates.
7. **The same story in several tractates.** The Bavli repeats stories (often word for word). The site will show some
   twice, in different tractates. Fine for this week; the parallels list (§3) shows how many, and is useful to Jeff.
8. **Review load on Jeff.** ~2,000 unreviewed stories cannot go to him. What can: a random sample of ~50 shipped
   stories across Shas, which would give the site a *measured* precision with an error bar, and the two-run
   disagreement list as the first things for him to see. That is for after Sunday.
9. **The site will probably show fewer stories than Daniel's ~3,000.** Shipped per page so far: Yevamot 0.34, Gittin
   0.62, Berakhot 0.89. On 4,276 pages that suggests ~1,500–2,100 more, so ~2,000–2,600 in all, because only definite
   stories ship. Worth telling Daniel before launch (§7 Q8). The site itself: ~3 KB per story, ~8 MB in all, loaded
   per tractate; fine.
10. **Reproducibility.** Both runs of a tractate on the same day, same code (Lessons 11, 22). Record Google's model
    version string (§4 item 4): Google already re-routes a deprecated model silently (`gemini-2.5-flash` is billed as
    3.5 Flash-Lite from 1 December), and a "preview" model can change under the same name.
11. **Repository size.** Run files are ~27 KB per page: two runs + text for 4,276 pages ≈ 300 MB, against a 60 MB
    repository today. Under GitHub's limits (no single file near 100 MB), but clones get slower. Commit them anyway:
    the repo's rule is that a measurement nobody can re-read did not happen.
12. **Stale instructions.** `docs/technical/shas-finder-plan.md` §3–§4 and `docs/technical/shas-run-local-prompt.md`
    still say v11, one run, output under `results/v11/`. Anyone following them would run the wrong thing. Update them
    when this plan is approved (one-line pointers to this doc).
13. **Bookkeeping.** Execute this as a work item (`work/2026-11-08-shas-finder-run.md` already exists; fill its
    `writes:` with `site/data/`, `scripts/build_site_data.py`, `results/v14/`, `results/consensus/`, `results/shas_run/`)
    and check `board.py lanes`: the sign-up work also writes `site/data/`.

---

## 7. Decide before starting (only Simon can answer these)

1. **Flex or standard?** Recommendation: Flex, if Tuesday's smoke test passes; standard otherwise. Saves ~$70.
2. **Budget cap.** ~$72 on Flex, ~$145 standard (estimated). A hard stop at **$200**?
3. **Merge #82 → #83 → #84 into main before the run**, or run from #84's branch and merge everything after?
   Recommendation: merge first, so the run's `git_rev` is a commit on main.
4. **Eruvin.** It is held for Jeff. Should the site show Eruvin by Sunday? That needs two fresh v14 runs (~$3) and
   ships it `reviewed: false`, like the others. Does "held" mean held from the site, or only from the scholarly record?
5. **Shekalim:** leave out this week (recommended), or try it?
6. **Saturday:** may the machine keep running unattended, and is Saturday a working day for you, or pure slack?
7. **Claude judge on the subset only this week**, full Claude arm later for Jeff? (Recommended; the site is identical.)
8. **Tell Daniel** that the definite-only rule probably means ~2,000–2,600 stories, not ~3,000?
9. **Cross-tractate repeats:** ship as they are this week? (Recommended.)
10. **Your Mac** can run unattended for about a day, Wednesday? If not, the schedule moves Wednesday's work to night
    runs.

---

## Not done here

No API calls, runs or merges. No code written. The cost is an estimate built from two measured v14 runs and three
unmeasured assumptions (share of pages examined, triage tokens, Flex latency), each named above with its range.
