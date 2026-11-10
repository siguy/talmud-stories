# Plan: run all of Shas for the Septimus site by Sunday 2026-11-15, reusable for Jeff

*Written 2026-11-09; revised the same day after a three-angle review (schedule and failure modes; cost and Google's
API; simplicity and the project's rules). Planning only: no API calls and no detector runs were made writing it.
PRs #82, #83 and #84 were merged into main the same evening (Simon). Supersedes §3 and §4 of
[`docs/technical/shas-finder-plan.md`](../technical/shas-finder-plan.md), which still say v11 and one run; its scope
table (§2) still stands, with the corrections in §6.4.*

**The short version.** It is feasible, with about two days of slack. The model calls take about half a day of wall
time; the risk is the code that has to be written first, and people. Run detector v14 as it is, twice per tractate,
on Google's **standard** tier. Estimated cost **~$145** (range $110–200). Google's **Flex** tier would halve that
(~$72), but it needs a library upgrade, slower calls and new retry code in the week of the deadline, so it is offered
as an option, not the default. The **Batch API** is the same half price and would mean rebuilding the pipeline: not
this week. Nothing in the detector or its prompts changes.

**Terms**
- **Standard / Flex / Batch:** three ways Google serves the same model. *Standard* answers in seconds at full price.
  *Flex* is the same call answered from spare capacity (seconds to minutes), half price. *Batch* means uploading a file
  of requests and collecting the answers up to 24 hours later, also half price.
- **Token:** roughly ¾ of an English word (Hebrew uses more). **TPM / RPM / RPD:** Google's limits on tokens per minute,
  requests per minute, requests per day.
- **429 / 503:** the error codes Google returns for "slow down" (rate limit) and "too busy right now".
- **Retry with backoff:** after such an error, wait, try again, and wait longer each time.
- **Gate:** an automatic check that stops one tractate going further if it fails.
- **Checkpoint:** a file a run saves as it goes, so a crashed run can resume instead of starting over.
- **SHA / hash:** a short fingerprint of a file's exact contents; if one byte changes, the fingerprint changes.
- **Examined page:** a page that survived Stage 1 triage and went to Stage 2. Only examined pages cost real money.
- **Unit:** one passage as the judges see it (overlapping proposals from both runs merged into one). **Cell:** one
  segment of one page.
- **measured / indicated / suspected:** the project's labels for how strong a claim is (FRAMEWORK.md).

---

## 1. Is it feasible by Sunday? Yes, if the pre-flight code lands by Tuesday night

### Order

```
commit Berakhot text+triage ─┐
pre-flight code + tests ─────┼─► triage (once per tractate) ─► run 1 ┐
fetch text (31 tractates) ───┘                                run 2 ┴─► gates ─► Gemini judge ─► Claude judge* ─► site build ─► Simon reads lists ─► deploy
```
\* Claude judges only what Gemini called out of scope, and only after Gemini's answers are final (§2.5).

### How long the machine work takes (standard tier, from measured runs)

| step | measured basis | Shas estimate | 8 tractates in parallel |
|---|---|---|---|
| Sefaria fetch | sequential, polite delay | 4,276 pages, ~1–3 h | 2–3 tractates at once: ~1 h |
| Stage 1 triage | **never metered** (both v14 runs used a cached triage) | ~5 s/page guessed → ~6 h | ~45 min |
| Stage 2+4, one run | Berakhot 16.6 s, Yevamot 14.3 s per examined page (~2.6 s per call, ~6.3 calls per page) | ~2,140 examined pages → ~10 h | ~1.25 h |
| Stage 2+4, both runs | | ~20 h | **~2.5 h** |
| Gemini judge | Berakhot 224 units, threaded | ~4,100 units | ~1 h |
| Claude judge (subset) | 20 units per subagent | ~150–250 units, ~10 subagents | ~1 h |

About 35,000 requests in all, most on Wednesday. The TPM fits (§1, rate limit); the per-day request limit has not
been checked (Tuesday task).

### Day by day

| day | what runs | who | done when |
|---|---|---|---|
| **Mon 11-09** | #82 → #83 → #84 merged (done). Simon answers §7 | Simon | §7 answered |
| **Tue 11-10** | Morning: commit Berakhot's text and triage cache (they exist only in two other worktrees); start the Sefaria fetch of all 31 in the background (free; needs none of the new code); check the key's RPM/RPD for `gemini-3-flash-preview` in AI Studio. Day: pre-flight code, §4 items 1–7, with tests. Evening: pin the run worktree to a tagged commit. *If Simon chose Flex:* the SDK bump and the Flex smoke test (§5.3) | Claude session on Simon's Mac | tests green; G1 green on the fetch |
| **Wed 11-11** | Triage all 31, then run 1 and run 2 of every tractate, 8 processes at a time, largest first | the driver, unattended | every tractate past G2–G4, or named as failed |
| **Thu 11-12** | Re-run whatever failed. Gemini judge on every tractate; G6 on Gemini; then export the Claude subset | driver + Claude session | G5–G6 green |
| **Fri 11-13** | Claude subagents judge the subset; import; G6 on Claude; build `site/data/`; tests; check the site in a browser. Simon reads the lists in §2.3 | Claude session; Simon ~1 h | PR ready |
| **Sat 11-14** | **Slack.** Nothing scheduled (§7 Q6) | — | — |
| **Sun 11-15** | Merge, deploy | Simon | live |

**Critical path:** pre-flight code (Tue) → triage → two runs (Wed) → Gemini judge → Claude judge → site build →
Simon's lists → deploy. **Slack: Thursday and Saturday, about two days.** What eats it is a pre-flight change found
broken late, which is why §4 keeps every change outside `src/` and the default tier is standard.

**What can run in parallel:** the fetch beside the code work; tractates beside each other (separate processes and
output files); run 1 beside run 2 of one tractate **once its triage cache is written**. Checkpoints sit beside each
run's `--output` (`scripts/run_new_tractate.py:338`), so two runs never share one. The one race: a runner re-triages
pages whose labels are all `TRIAGE_FAILED` (`run_new_tractate.py:184-186`), so G2 checks the cache file itself, and
the cache is written atomically (§4 item 1).

**Rate limit:** today's 3M TPM error came from four judge runs with thread pools. One detector process uses ~90k TPM;
eight ≈ 0.75M. No other Gemini work on the key on Wednesday.

---

## 2. The process: a simple loop, a gate after every step, nothing to remember

### 2.1 Shape

`scripts/run_shas.py` (not a detector change): **a loop over tractates, largest first, 8 at a time, that skips any
step whose output already exists and passed its gate**, then runs `scripts/check_tractate_run.py` on it. It writes
one line per tractate and step to `results/shas_run/status.json` and to `project.log` (tractate, step, counts, cost).

- Steps call the scripts that already exist: `fetch_tractate_pages.py`; `run_new_tractate.py --triage-only`;
  `run_new_tractate.py --output results/v14/<t>/run{1,2}.json`; `judge_detector_spans.py units / gemini / export /
  import`. The driver adds order and checks, no detection logic.
- **A failed tractate stops; the others carry on** (CLAUDE.md: one source failing never stops the run).
- **Runs from a dedicated worktree pinned to a tagged commit** (e.g. `shas-run-2026-11-11`). A fix to a red gate is
  made elsewhere, so it never changes the code a half-finished tractate is running.
- **Resuming a crashed run is allowed, but marked.** A resumed run's failure counters cover only the part after the
  crash (counters live in memory; a checkpoint keeps only `stage2_error`), so a resumed run is amber, not green, and the
  driver adds the counters from each attempt's log.
- No in-driver cost cap: a Google Cloud billing alert at Simon's cap (§7 Q2), plus cost per tractate in the report.

### 2.2 The gates

| gate | after | checks | baseline (measured) |
|---|---|---|---|
| **G1 text** | fetch | page count equals Sefaria's shape index; refs contiguous; every page has segments; every segment has Hebrew; Hebrew carries vowel points on ≥ 95% of segments; **empty English is counted and listed, not a failure** | empty English: Yevamot 12, Eruvin 9, Gittin 7 segments; vowel points 100% on all three |
| **G2 triage** | triage | every page labelled; no page whose labels are all `TRIAGE_FAILED`, read from the cache file; SHA of the cache recorded | — |
| **G3 run health** | each run | every fetched page in the output; `stage2_errors = 0`; `truncated_responses = 0`; `tokens.*.unmetered = 0`; `pass2_failures`, `twin_failures`, `stage4_call_failures` **≤ 3 each, listed** (they only lose *additions*, and the both-runs rule only narrows); `empty_responses ≤ 2`, listed; detector `src.story_detector_v14`, model `gemini-3-flash-preview`, thinking off, `twin_trigger = all`; **triage SHA unchanged** (the run did not re-triage); span repairs ≤ 3; `resumed_pages = 0`, else amber | v14 runs: pass2 failures 1 in 2 of 4 runs (Berakhot 42a, Yevamot 59b), twin 0, empty 0–2, span repairs 0–2 |
| **G4 two runs agree** | run 2 | same `stage2_fingerprint` and same hash of `src/story_detector_v14.py` (not `git_rev`, which any commit flips); same triage SHA; kept-story counts within 10%; ≥ 90% of passages definite in either run are definite in both (to be confirmed against Berakhot and Yevamot before Wednesday, and the number written here) | kept: Berakhot 189 / 187, Yevamot 154 / 151 |
| **G5 density** | G4 | stories per examined page within the range of the run tractates, **and** the Gemini out-of-scope rate per tractate no higher than Berakhot's and Yevamot's. Outside either: amber, Simon reads | 1.8 and 1.5 per examined page; out of scope 7/224 and 10/184 units |
| **G6 judges** | each judge | 0 `failed` / `invalid` after one resume; prompt SHA `84bfb33fd32a` (v2). **For Claude: every unit Gemini called `out_of_scope` has a Claude answer with outcome `ok`; the site build refuses otherwise** | Berakhot 224/224 valid |
| **G7 site** | build | `python3 -m pytest tests/ -q` (L-045's guards) | 514 passed, 1 skipped on main today |

### 2.3 Who looks at what

- **Never needs a person:** a tractate with every gate green. Expected: most of the 31.
- **Needs Claude:** any red gate. Read `status.json` and `project.log`, fix, resume. A second failure at the same gate
  goes to Simon with the error.
- **Needs Simon (~1 hour on Friday), targeted lists, not random samples:**
  1. **The biblical list** (§2.5): every definite passage where exactly one judge said out of scope, plus every one
     whose characters match the detector's biblical-name list, in all tractates. Random sampling would rarely land on
     these.
  2. 10 random stories from any amber (G5) tractate.
  3. One look at the site.
- **Never Jeff this week** (§6.8).

### 2.4 Logged per tractate

Already in `run_meta`: pages, examined/skipped, configuration, fingerprint, tokens per stage, failure counters,
elapsed time, `git_rev`. **New** (§4 item 3): `model_version` as Google reports it; cached tokens
(`cached_content_token_count`); the tier the server actually used (`usage_metadata.service_tier`). The driver adds
gate results and cost (tokens × §5.2 prices).

### 2.5 Biblical stories and the judges

**This week the site's existing rule does the work, unchanged:** a passage is removed when **both** judges call it
out of scope (`biblical_cells()`, `scripts/build_site_data.py:45`). The detector's own filter (Stage 4j,
`filter_biblical_actor_stories`) is a fixed list of names and misses group actors (*the Sages of Israel*, *the
Israelites*) and "God". On Berakhot both judges caught all five biblical passages the detector kept (n = 5,
**indicated**).

**Why Claude is asked only about Gemini's out-of-scope units.** Claude's answer can change the site only where Gemini
already said out of scope; elsewhere the passage ships whatever Claude says. Gemini flagged 7 of 224 units on
Berakhot and 10 of 184 on Yevamot, so this is ~10 subagent batches instead of ~200. It gives the same site **only if**
Claude goes last (Gemini's answers final, G6 green, before the export) and every flagged unit has a valid Claude answer
(G6). A missing Claude answer would otherwise read as "not biblical" and ship: that is the Lesson 21/38 failure, and
G6 is what stops it. The identity test (same site output on Berakhot and Yevamot) runs on a scratch copy, because
`import` overwrites `claude.json` (`judge_detector_spans.py:261`).

**The weak spot, said plainly.** Removal needs both judges, and Gemini is the detector's own model, so a biblical
passage Gemini misses ships. That matters most where biblical retelling is densest: Sanhedrin (Perek Ḥelek), Sotah,
Megillah (Esther), parts of Bava Batra. The 5-of-5 on Berakhot does not carry over to them (Lesson 18). This week's
answer costs no model calls: the targeted list in §2.3 and the out-of-scope rate in G5. Changing the rule to "either
judge removes it" would only narrow, which L-045 allows, but it reopens a settled filter and L-045 says a narrowing
gate is measured against Jeff first. That is Simon's call, after Sunday.

**After Sunday: v15 biblical filter.** Add biblical peoples and places to Stage 4j's list, and stop "God" and "the
Jewish People" counting as non-biblical actors when no rabbi is among them. No model calls; re-appliable to every run
on disk with no re-run. A new detector version (v14 is a ship point), with its reach counted on every tractate first
(Lesson 27).

### 2.6 Accuracy without an expert round

Where Jeff reviewed the detector's YES/HIGH calls, 141 of 155 were his yes (91%, **measured** on Ketubot, Kiddushin
and Gittin; **circular**, since he was reviewing the detector's own calls; **indicated** for other tractates).
Requiring both runs removes the coin-flip cases from Stage 2 onward. It does not sample triage noise: triage runs once
and both runs share it. Every unreviewed tractate ships `reviewed: false` with the "not yet checked by a scholar"
notice.

---

## 3. Making the run serve Jeff later

**Keep everything the run produces; nothing extra needs computing this week.** Commit whole run files, not filtered:
- `stories[]` at **every** grade (YES, HIGH, LOW, `NOT_A_STORY`); `mishnah_stories[]`; `twin_verdicts`;
  `span_repairs`; `skipped_by_triage` per page (where recall loss starts; triage recall is ~95%); `run_meta`.
- The Sefaria text and triage cache per tractate, so a later re-run reads identical input.
- The judges: `units.json`, `gemini.json` for **all** units, and `claude.json` marked in its meta as a subset.

**New, cheap, this week:** the **two-run disagreement** per tractate (passages definite in one run only; grade shifts),
from a v14-vs-v14 version of `compare_v14_v11_*.py`, no model calls. It is the cheapest uncertainty signal there is,
and the first list to show Jeff.

**After Sunday:** cross-tractate parallels (the Bavli repeats stories, often word for word): a shared-text match across
all run files, no model calls, scholarly material for Jeff; the full Claude arm on all units.

**Open questions: which touch the run, which only touch reading it later**

| question | touches the run? | why |
|---|---|---|
| R-S1 biblical scope edges (`jeff:scope-edges`) | site only | applied after the run, by the judges; re-appliable on disk |
| R-C2 question-and-answer (`jeff:question-and-answer`) | no | v14 grades these LOW or `NOT_A_STORY`, both kept; re-read, not re-found |
| R-C0 "one event, then a ruling" / judge prompt v4 | no | not adopted; moves borderline → not, which never ships |
| boundary-end rule | no | boundaries re-cut on saved spans |
| a ruling that **widens** what a story is | in principle | spans v14 never proposed are not on disk; none pending; would be a new detector version anyway |
| Eruvin held for Jeff | site only | §7 Q4 |

---

## 4. What to change: nothing in the detector; seven things around it

**The detector: run it as is.** v14 is adopted, measured on two tractates, and carries Jeff's rulings to 10-25. Every
alternative (v15, judge v4, model 3.8, prompt reordering for caching) is its own measured experiment. CLAUDE.md: no
prompt or model change rides on this run.

**Ranked by value against deadline risk** (all outside `src/`, each with a test):

| # | change | value | risk |
|---|---|---|---|
| 1 | **Retry with backoff on every Gemini call**, inside the runner's existing wrapper (`TokenMeter.metered`, `run_new_tractate.py:80`): 429/503, ~5 tries, 30–120 s. Today only Stage 2's first pass retries (`story_detector_v14.py:1523-1547`); triage raises and stops the tractate (`event_triage.py:190`); twin, stitch, continuation and clause-span calls fail once and are skipped. Also write the triage cache atomically (temp file + `os.replace`, `run_new_tractate.py:298`) | highest: this is what turns red tractates green | low |
| 2 | `scripts/check_tractate_run.py`: gates G1–G6, read-only | high | low |
| 3 | Record `model_version`, cached tokens and the served tier in the wrapper | medium: exact cost, reproducibility | very low |
| 4 | `scripts/run_shas.py`: the loop in §2.1 | high | low |
| 5 | **Any tractate, by convention**, in every reader: one generated table of slug / English / Hebrew names (multi-word names become `bava_batra`, not the `bava batra.json` the fetch writes today, `fetch_tractate_pages.py:126`) read by the runner, `judge_detector_spans.py` (its hard-coded `TRACTATES` and assert at `:49-59`, and `j.TEXT_SOURCES`), `build_site_data.py` `SOURCES`, the site test's `SITE_WORDS`, **and the site front end** (`site/app.js:3-4` hard-codes five names and its router at `:180` refuses any other) | required | low–medium |
| 6 | **Site home page reads `index.json` counts only**, not every tractate's file (`site/app.js:39` loads them all; 36 files ≈ 8 MB) | high for readers on phones | low |
| 7 | `judge_detector_spans.py export --only-gemini-out-of-scope`, plus G6's refusal in the site build | high: ~200 batches → ~10 | low |
| opt | **Flex**, only if Simon chooses it (§5.3): bump `google-genai` from 1.60.0 (installed and the `requirements.txt` floor; it has no `service_tier`) to a tested 1.7x; in the wrapper, add `service_tier=FLEX` and `http_options.timeout = 900_000` (**milliseconds**); fall back to standard after the retries; the judge's Gemini arm needs its own wrapper (it calls `story_detector_v11._call_google`, `judge_labelled_spans.py:370-378`) | ~$73 | medium |
| — | **Not this week:** Batch API; v15 biblical filter; judge v4; model switch; explicit caching; Shekalim; cross-tractate parallels | | |

---

## 5. Cost, and whether the Batch discount stacks

### 5.1 Simon's premise, checked against Google's pages (fetched 2026-11-09, twice, independently)

- **The detector uses `gemini-3-flash-preview`** (`src/model_config.py` `DEFAULT_MODEL`; every v14 `run_meta`). The
  pricing page calls it "our legacy Flash model". Its model page lists Batch, Flex and caching, last updated
  December 2025, no shutdown date.
- **Its price:** standard $0.50 in / $3.00 out per million tokens. **Batch $0.25 / $1.50. Flex $0.25 / $1.50.** No
  promotion is listed.
- **"50% off on top of 50% off of 3.7 and 3.8":** there is **no 3.7** on the page. 3.8 Flash (and 3.6) is $0.75 /
  $3.75 now, rising to $1.50 / $7.50 on 1 January 2027, so today's price is in effect half the 2027 one, and Batch or
  Flex halves it again ($0.375 / $1.875). **So the stack is real for 3.6 and 3.8, and still costs more than our model
  at half price** ($0.375 vs $0.25 in). 3.8 also measured worse on Jeff's list: 75.0% vs 83.3% recall, 4 truncations
  (`docs/findings/2026-09-14-default-model-measured.md`). Cheapest and most accurate is the model we have.
- **Batch and Flex are separate tiers at the same half price**; nothing says they combine, and they cannot apply to
  one call. **Cached input** is $0.05 on standard, Batch and Flex alike: 90% off standard input, 80% off Flex input.
- **Implicit caching** (Google reuses a prompt's repeated opening automatically) is on by default for 2.5 and newer;
  no discount percentage or minimum size is stated for our model. Stage 2's prompt and the judge's 25 KB system prompt
  open with the same text every call, so part of the bill may already be cheaper than §5.2 says. Unknown until item 3
  records it. *Explicit* caching would restructure the prompt: a detector change, out.
- **Batch limits** are tier-dependent (3M enqueued tokens on Tier 1, 400M on Tier 2; figures given for 3.8/3.6 only).
  Flex gets no extra limits.

Sources: [pricing](https://aistudio.google.com/docs/pricing), [Batch API](https://aistudio.google.com/docs/batch-api),
[Flex inference](https://aistudio.google.com/docs/flex-inference),
[gemini-3-flash-preview](https://aistudio.google.com/docs/models/gemini-3-flash-preview),
[caching](https://aistudio.google.com/docs/caching), [rate limits](https://aistudio.google.com/docs/rate-limits),
[python-genai changelog](https://github.com/googleapis/python-genai/blob/main/CHANGELOG.md) (`service_tier` from
1.69.0). The `ai.google.dev` links now redirect to `aistudio.google.com`; re-check prices on the day.

### 5.2 The estimate

**Measured** (v14, `run_meta.tokens`, Stage 2+4, one run):

| | examined pages | tokens in | tokens out | $ standard | $ per examined page |
|---|---|---|---|---|---|
| Berakhot run 1 | 106 of 125 | 2.77M | 0.26M | $2.16 | $0.0203 |
| Yevamot run 1 | 106 of 242 | 2.36M | 0.22M | $1.83 | $0.0173 |

**Assumed:** 4,276 pages in the 31 tractates (plan §2 less Berakhot and Eruvin; Tamid is smaller, §6.4). Share
examined: Berakhot 85%, Gittin ~51%, Yevamot 44%; Kodashim and Taharot will be lower, so **50% central, 40–65%
range**. Triage, **never metered**: the prompt averages ~11k characters *including* the page (2.9k fixed), ~3.5–4.5k
tokens in and ~0.5k out, thinking off; ~5k / 0.7k is used as a safe overestimate. Judge: ~1.9 units per examined page,
~$0.007 a unit (the script's own conservative estimate).

| item | standard | Flex (option) |
|---|---|---|
| Stage 1 triage, once (shared by both runs) | ~$20 ($13–30) | ~$10 |
| Stage 2+4, run 1 | ~$41 ($30–57) | ~$20 |
| Stage 2+4, run 2 | ~$41 ($30–57) | ~$20 |
| Gemini judge, all ~4,100 units | ~$29 (likely less: caching) | ~$15 |
| Claude judge | $0 API (subagents) | $0 |
| Retries, tests (+10%) | ~$13 | ~$7 |
| **Total** | **~$145 ($110–200)** | **~$72 ($55–100)** |

The second run (~$41) is what makes "definite" mean definite (L-045): not optional. The Gemini judge on non-site
units (~$20 of the standard figure) is optional; it is kept because it completes the consensus record for Jeff.

### 5.3 Flex: why it is the option, not the default

It is the same call with one setting, so the pipeline's order and checkpoints stay as measured. The reasons against it
this week, all from the review: the installed library cannot send the setting (an upgrade in deadline week); a busy
Flex queue returns 429/503 with no fallback, and today most of the pipeline does not retry (item 1 fixes that either
way); latency. Standard runs ~2.6 s a call. At a 30 s median the two runs would take ~33 hours even 8-wide.

If Simon picks it: Tuesday evening, after the upgrade and its tests, 10 Berakhot pages (~$0.10). Pass if 0 errors
after retries, **median call ≤ 8 s** (the schedule's limit, not a comfort number), and no `Stitch error` or
`clause-span LLM error` lines in the log. Ten pages cannot show the outputs match standard; that claim stays
**indicated**. Fail → standard.

### 5.4 Batch: not this week

Batch is asynchronous: send a file, wait up to 24 h, collect. The pipeline is **seven** rounds, each built from the
previous one's answers: triage → Stage 2 → "find more stories" (its prompt lists Stage 2's stories) → twin pass
(from the merged result) → 4d stitch (from all pages, sorted) → 4f continuation (only stories 4d did not stitch) →
4k clause spans. Batching means a submit-wait-collect per round and a replay of a frozen detector's code with the
answers filled in: a rewrite, worst case seven 24-hour waits, for the same 50% as Flex. Reconsider only for a much
larger future job, and only if Flex proves unusable.

---

## 6. What else you may not be thinking of

1. **The deadline risk is code, not compute.** The models are ~½ day. Every change is outside the detector, tested,
   with a fallback (hand-run the scripts if the driver breaks).
2. **Where it runs.** The cloud container cannot reach Sefaria or Gemini, so Simon's Mac: plugged in, awake, on a
   stable network, for about a day. The key stays in `.env`, never in chat.
3. **Quota sharing.** Other Gemini work on the same key shares the limits. Wednesday is Shas-only. Request limits
   (RPM/RPD) are unchecked: ~35k requests.
4. **Tractate structure.** *Tamid*: Gemara starts at 25b, ~17 amudim, not 64; the fetch derives pages from Sefaria's
   index, so it corrects itself. *Shekalim* is Yerushalmi (halakhot, not dapim); Daf Yomi learners count it in "Shas";
   recommend list v2 (§7 Q5). *Kinnim, Middot*: no Gemara. *Long tractates* (Bava Batra 350 pages, Shabbat 312,
   Chullin 282) start first. *Multi-word names* need slugs (§4 item 5).
5. **Few-shots come from Ketubot and Kiddushin.** Kodashim (sacrifices) is new ground; G5 watches it.
6. **The biblical filter carries more load outside Berakhot** (§2.5).
7. **The same story in several tractates** will show twice on the site. Fine for this week; counted after Sunday (§3).
8. **Review load on Jeff.** ~2,000 unreviewed stories cannot go to him. After Sunday: a random sample of ~50 shipped
   stories gives the site a *measured* precision with an error bar; the two-run disagreement list is the first thing
   to show him.
9. **Fewer stories than Daniel's ~3,000.** Shipped per page so far: Yevamot 0.34, Gittin 0.62, Berakhot 0.89. On
   4,276 pages that suggests ~1,500–2,100 more, ~2,000–2,600 in all, because only definite stories ship (§7 Q8).
10. **Reproducibility.** Both runs same day, same pinned code (Lessons 11, 22). Record Google's `model_version`:
    Google already re-routes a deprecated model silently (`gemini-2.5-flash` is billed as 3.5 Flash-Lite from
    1 December), and a "preview" model can change under the same name.
11. **Repository size.** ~27 KB a page per run: ≈ 300 MB more against 60 MB today. Under GitHub's limits; commit them
    anyway (a measurement nobody can re-read did not happen).
12. **Stale instructions.** `shas-finder-plan.md` §3–§4 and `shas-run-local-prompt.md` still say v11, one run,
    `results/v11/`. Point them here when this plan is approved.
13. **Bookkeeping.** Execute as `work/2026-11-08-shas-finder-run.md`; fill `writes:` (`site/`, `scripts/build_site_data.py`,
    `scripts/run_new_tractate.py`, `scripts/judge_detector_spans.py`, `results/v14/`, `results/consensus/`,
    `results/sefaria/`, `results/triage/`, `results/shas_run/`, `tests/`) and check `board.py lanes`: the sign-up work
    also writes `site/`.

---

## 7. Decide before starting (only Simon can answer these)

1. ~~Standard or Flex?~~ **Standard** (Simon, 2026-11-09).
2. ~~Budget?~~ **Billing alert at $200** (Simon, 2026-11-09).
3. ~~Merge #82 → #84 first?~~ Done 2026-11-09.
4. **Eruvin.** Held for Jeff. Should the site show it by Sunday? Two fresh v14 runs (~$5 standard), shipped
   `reviewed: false` like the others. Does "held" mean from the site too, or only from the scholarly record?
5. **Shekalim:** leave out this week (recommended)?
6. **Saturday:** may the machine run unattended, and is Saturday a working day or pure slack?
7. **Claude judge on the subset this week**, full arm later for Jeff? (Recommended; the site is identical, given G6.)
8. **Tell Daniel** to expect ~2,000–2,600 stories, not ~3,000?
9. **Cross-tractate repeats:** ship as they are this week? (Recommended.)
10. **Your Mac** free to run unattended on Wednesday?
11. **Biblical rule:** keep "both judges" this week (recommended), and decide "either judge" after Sunday, once it is
    measured against Jeff?

---

## Review log (2026-11-09)

Three independent reviewers, each given this doc and one angle. Changes made from what they found (each checked
against the files before it went in):
- **Failure handling.** The first draft's G3 baseline ("all 0") was wrong: pass-2 failures occur in 2 of the 4
  measured v14 runs. "The runner already retries 429s" was true only of Stage 2's first pass. → item 1 (retry every
  call), G3 relaxed for additions only, resumed runs amber.
- **Flex.** The installed `google-genai` 1.60.0 has no `service_tier`; the timeout is in milliseconds; the 30 s
  pass mark would have cost ~33 hours. → Flex demoted to an option, threshold 8 s.
- **Missing work:** the site front end (hard-coded names, loads every file), multi-word slugs, Berakhot's inputs not
  committed, request limits, `git_rev` fragility. → items 5–6, Tuesday tasks, G4 on fingerprints.
- **The Claude-subset shortcut** is exact only with Claude last and every flagged unit answered. → G6 refusal.
- **Biblical handling** is weakest where biblical material is densest. → targeted list for Simon, G5 rate, Q11.
- **Smaller:** cost figures made consistent; seven Batch rounds, not six; caching discount stated exactly; triage
  prompt size includes the page; evidence labels; terms defined; driver simplified; parallels deferred.

## Not done here

No API calls, runs or code. The cost is an estimate from two measured v14 runs and three unmeasured assumptions
(share of pages examined, triage tokens, implicit caching), each named above with its range.
