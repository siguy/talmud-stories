# Wave 5b Review Record — 2026-08-30

**What this is:** the full findings from three independent reviews of the Wave 5b
clause-role labelling design and code, captured as an **actionable fix list**.

**Why it exists:** Wave 5b was put on hold in favour of a cheaper path (fix two bugs,
then tune the existing approach — see [decision record](2026-08-30-wave5b-decision.md)).
**If that path does not work, Wave 5b gets revived — and this file is what makes that
possible.** Without it the review evaporates and the same 433 lines get run with the
same defects. This is the Lesson 17 pattern applied to a code review.

**Reviewers:** three parallel agents — a simplicity/YAGNI reviewer, a DHH-style
overengineering reviewer, and a Kieran-style code-quality reviewer. They were told the
project is Python (not Rails) and given the same files.

**Status of each finding below:** `VERIFIED` = reproduced against real data or code in
this repo. `REPORTED` = asserted by a reviewer, not independently checked.

---

## 1. Verdict — all three agreed

**The core design is right.** Splitting a paragraph into real units, having the model
label units instead of emitting positions, and computing offsets in code is the correct
answer to Lesson 16. `_assert_word_boundary` was singled out as the right way to turn a
guarantee into something checkable.

**The execution and the measurement are not.** Everything below is scope, correctness,
and whether the gate can measure anything.

---

## 2. P0 — must fix before Wave 5b runs at all

> **STATUS 2026-08-30: 2.1, 2.2 and 2.4 are FIXED** in
> `scripts/run_clause_labeling.py`, guarded by
> [`tests/test_wave5b_runner_outcomes.py`](../../tests/test_wave5b_runner_outcomes.py)
> (failure-injection test written first, watched fail, then fixed). Same fixture,
> model failing on every call: before `{kept_full: 6, no_split: 2, skipped: 6}` =
> 14 counts for 6 stories, all 6 stamped `clause_kept_full`, 6 fabricated speech
> profiles; after `{no_split: 1, skipped: 5}` = 6 counts, 0 success stamps, 0
> profiles, 5 `needs_review`. **2.3 (the scorer) is still open** — it is a
> different file and was out of scope for that commit.

### 2.1 A failed API call is recorded as a successful judgment — VERIFIED — **FIXED 2026-08-30**

`scripts/run_clause_labeling.py` — failure path `continue`s the inner **per-side** loop,
then falls through to an unconditional success write after the loop.

Reproduced by stubbing every model call to fail, 5 stories:

```
counts: {'clause_roles': 0, 'clause_kept_full': 5, 'no_clause_split': 0, 'skipped': 7}  sum=12
stories_labelled: 5
text_span_source on failed stories: {'clause_kept_full'}
needs_review flags set: 0
```

`clause_kept_full` also means "the model read this and judged all of it in-story", so a
total outage is indistinguishable from 5 considered judgments. Counters are not a
partition (12 ≠ 5).

**Fix:** write `text_span_source='skipped'`, set `needs_review`, `continue` the *story*
loop so buckets stay mutually exclusive. `src/story_detector_v11.py` already does this
correctly — the new runner regressed against the file it was forked from. → Lesson 21.

### 2.2 `speech_profile` fabricated on stories that were never labelled — VERIFIED — **FIXED 2026-08-30**

Same fall-through. Failed stories receive
`{'in_story_clauses': 0, 'speech_clauses': 0, 'speech_ratio': None, 'all_speech': False}`
— `all_speech` is `False`, not `None` — and it is written into
`results/clause_labels/`, the dataset intended to produce the **Wave 6 speech-act
number for Jeff**. `speech_profile()` in `src/clause_roles.py` correctly returns `None`
when there is no data; the runner's aggregation discards that care.

**Fix:** do not write the key at all when no labels were obtained.

### 2.3 The scorer rates a completely dead run as a normal result — VERIFIED — **STILL OPEN**

A fully-failed run scores **6% HIT / 38% HIT+NEAR** — numerically identical to the
legitimate no-trim baseline. `boundary_clause()` falls back to "clause 0 / last clause"
whenever spans are absent, which is right for a genuine kept-full and indistinguishable
from a crash.

**Fix:** `scripts/score_boundary_targets.py` should read `wave5b_stats.counts`, refuse
to score (or banner loudly) when `skipped` is non-trivial, and add a `FAIL` bucket for
stories whose `text_span_source == 'skipped'`. The scorer already models exactly this
distinction for detection gaps (`N/A`) — apply the same reasoning to run failures.

### 2.4 `no_clause_split` provenance destroyed — VERIFIED — **FIXED 2026-08-30**

The unconditional post-loop write overwrites `text_span_source`, so the no-split case
never survives. [`tasks/PLAN_wave5.md`](../../tasks/PLAN_wave5.md) explicitly requires
this be "a named, logged outcome (`text_span_source: 'no_clause_split'`), never a silent
accident." Wave 5b regresses against its predecessor's stated requirement.

---

## 3. P1 — high

### 3.1 `reassemble()` produces a different artifact from the fresh path — VERIFIED — **FIXED 2026-08-30**

Same input, same rule, same stories:

| | fresh | `--from-labels` |
|---|---|---|
| `version` | `…-wave5b` | **not stamped** |
| `speech_profile` | present | **absent** |
| `needs_review` | set | **never set** |
| `no_clause_split` count | 1 | 0 |

This destroys the premise that `--from-labels` is a free equivalent — someone will diff
a reassembled `longest_run` against a fresh `first_last` and attribute shape differences
to the assembly rule.

**Keep the feature, fix the implementation.** It is not merely an optimisation: the model
is nondeterministic (Lesson 11), so comparing two assembly rules requires the *same*
labels. Re-running produces different labels and confounds the comparison. **Fix:**
extract one `emit_span(...)` called by both paths. Also guard `segs[blk['segment']]`,
which `KeyError`s if reassembling against a different `--in` file than the labels came
from.

### 3.2 `build_prompt()` parses Markdown by string-splitting — VERIFIED (reviewer test)

`body.split('## PROMPT', 1)[1].split('---', 1)[0]`. Inserting a single `---` inside the
prompt body cut the extracted template from **3,351 chars to 489** — dropping every role
definition and the JSON schema — with no exception raised. A markdown table (`|---|`)
does the same. Also: substitution happens *before* `{{`→`{`, so braces in the data are
rewritten; and nothing checks that all placeholders were filled.

**Keep prompts in a reviewable file; stop parsing prose.** Move the prompt to its own
`.txt` with no surrounding markdown, keep rationale in the `.md` beside it, use
`str.format_map`/`string.Template` so unfilled placeholders raise, and assert the
rendered prompt still contains a sentinel from the END of the template.

### 3.3 The test set cannot support the gate — VERIFIED

`tests/expert_boundary_targets.json`, grouped by `(located_on, segment, direction)`:

| key | target clauses | |
|---|---|---|
| Ketubot 103b seg3 end | 0, 0 | duplicate |
| Ketubot 91b seg3 end | 1, 1 | duplicate |
| Kiddushin 8a seg10 start | 2, 2 | duplicate |
| **Ketubot 67b seg15 end** | **5, 6** | **contradictory** |
| **Kiddushin 12b seg4 end** | **1, 0** | **contradictory** |

Consequences: 3 expert judgments are double-weighted (11.5% of slots), and **the ceiling
is 50/52 = 96% HIT** with nothing saying so. Only 16 targets are scorable on Kiddushin;
29 of the 36 N/A are Ketubot, never run. **Effective n ≈ 14 distinct non-contradictory
boundaries** — "beat ~50%" means 8 right instead of 7.

The Kiddushin 12b pair is substantive: clause 1 (`exclude` polarity, 2026-05-26) vs
clause 0 (`include`, 2026-07-06). That is either Jeff refining a judgment across rounds
or the polarity heuristic reading one note backwards. **Needs a human decision, not a
silent double-count.**

### 3.4 `anchor_verified` is false on all 52 and the scorer never reads it — VERIFIED

Polarity: `include` 23, `exclude` 10, `unclear` 14, `mixed` 5. So **24 of 52 (46%)** may
be anchored one clause off in a known direction. And `NEAR` tolerance is `abs(got-want)
<= 1` — *exactly* the size of the suspected error. For those 24, HIT and NEAR are not
distinguishable claims; only HIT+NEAR carries information, yet `hit%` is the headline.

**Fix:** scorer reads `quote_polarity` and breaks results out by it, or restricts
headline `hit%` to the 23 `include` targets. Then get the 24 human-verified.

### 3.5 Nothing validates that `clause_index` still means the same thing — REPORTED

The runner stores `clause_count`; the scorer recomputes clause counts but never compares
them. If the clause splitter is ever tuned — and there is live pressure to tune it, since
its own docstring argues about commas — every stored index silently shifts and all
historical artifacts re-score against a different tokenization with no error. Targets
carry `n_clauses` and it is never validated either. **Three-line assert** in the scorer
and in `audit_text_spans.py`.

---

## 4. P2 — medium

- **Cross-language check is never actually reported — VERIFIED.** `covered` is computed
  and never read; `disagreements` is appended only when non-empty so agreeing segments
  are discarded, meaning the denominator is thrown away, not missing. `clauses_covered`
  counts *(sentence, clause) pairs*, not clauses, so any clause claimed by two sentences
  double-counts. No `start != end` guard, so single-segment stories run the check twice
  on cached labels. **Emit `n_disagreements`, `n_pairs`, `rate` as three distinct stats.**
- **`parse_labels` coercion — split the two cases.** Filling a *skipped* clause with
  `unclear` is right (fails conservative). Coercing an *unknown role string* to `unclear`
  is not: `"NARRATIVE"` (case change) and `"story"` (synonym) both silently become
  `unclear`, so a model that starts capitalising after a version bump degrades the entire
  corpus while reporting a plausible pile of `clause_kept_full`. Count unknown roles, log
  distinct values, fail above a few percent. Also separate *model formatting failure*
  (retryable prompt bug) from *API failure* — currently both land in `skipped`.
- **`isinstance(c, int)` accepts booleans — VERIFIED.** `covers: [true, false, 0]` parses
  to indices `[1, 0, 0]`. Use `type(c) is int`.
- **No coverage tracking.** A model labelling 1 of 12 clauses is indistinguishable
  downstream from a complete response. Store `n_labeled / n_clauses` and flag low coverage.
- **`assemble()` nits:** `best = run = [...]` aliases two names to one list (safe today,
  one `.append()` from silent corruption); the `>` tie-break means the *earliest* of two
  equal runs wins — a real editorial decision, undocumented; two of four `needs_review`
  checks are dead (`first`/`last` are in `IN_STORY` by construction, so never `unclear`);
  `assemble(labels, 0)` returns `{'first': 0, 'last': -1}`.
- **Segment-index contract disagreement.** Runner uses `s.get('index', i)` (falls back to
  enumeration order); scorer uses `s['index']` (hard require). If the fallback ever fires,
  spans refer to positions while targets refer to indices. Pick one — hard-require both.
- **Scorer picks arbitrarily among overlapping stories** (`cover[0]`), so the score depends
  on detector output ordering. Count and print `len(cover) > 1`; prefer the tightest bracket.
- **Minor:** `--limit` uses `continue` not `break` (walks the whole corpus; stories past
  the limit get no `text_span_source`, so a smoke artifact silently mixes processed and
  untouched stories); `needs_review` is set but never cleared, so a flag from an earlier
  wave survives and looks like this wave's judgment; scorer `main()` returns `None` so a
  missing run file still exits 0; English sentence splitting breaks `"R. Akiva"` into two.

---

## 5. Scope — what to cut if Wave 5b is revived

| Ship | Cut, add back only on evidence |
|---|---|
| 3 roles: `story` / `not_story` / `unclear` | the other 5 — `assemble()` reads only `IN_STORY`, so they are inert at the point of use |
| `is_speech` boolean | English labelling, `covers`, cross-language check |
| Hebrew only, English as prompt **context** | `longest_run` (keep `first_last` — the conservative under-trim matching our stated risk preference) |
| one assembly rule | separate `results/clause_labels/` artifact for consumers that do not exist yet |

Estimated 433 → ~150 Python lines. For scale, the thing being replaced is 179 lines.

**Disputed among reviewers, unresolved:**
- **`is_speech`** — simplicity said defer to Wave 6; DHH said keep ("the one field with a
  use that isn't circular"). *Our call: keep* — it produces the blast-radius number needed
  before writing to Jeff, and it is one boolean if the labeller runs at all.
- **`variant`** — DHH called it unearned: its whole evidence base is one case (22b_18) and
  it is a literal string (`איכא דאמרי`, 4 of 95 stories); a two-line lexical rule buys the
  same outcome. Counter-argument: Lesson 15 is precisely that lexical rules on Aramaic
  markers fail ~half the time. **Unresolved — decide with data, not argument.**
- **`parallel`'s 3.1% is a marker-proxy count**, measuring how often `כי הא|וכן|נמי`
  appear, not how often a clause is a parallel story. Lesson 15 says such markers are
  unreliable — so that number is not evidence for the role. **The role may still be right;
  the justification given for it was not.**

## 6. The attribution objection — the strongest strategic point

As built, Wave 5b changes the taxonomy, adds an English channel, **and** introduces an
assembly-rule choice simultaneously, then judges all three on ~14 effective cases. If the
number moves we will not know which change moved it; if it does not, we will not know
which to drop — and the likely outcome is shipping all eight roles because none can be
individually blamed. This is exactly the reasoning used to keep Wave 4 score-neutral and
to split Wave 6 from Wave 5. **Change one thing at a time.**

## 7. Corrections to claims made in the plan

- **"English sentences nest over Hebrew clauses" is FALSE — VERIFIED.** Generalised from
  three hand-checked examples; wrong on **21% of boundary segments** (26/126 have more
  English sentences than Hebrew clauses; worst 6 vs 10). Nesting is impossible there.
- **Tokenizer asymmetry inflates any cross-language signal — VERIFIED.** Hebrew splits on
  `. : ? !`, English on `. ! ?` only, and English is HTML-stripped before splitting while
  Hebrew is split on the raw string. English is more fragmented than Hebrew in **36% of
  segments**, so part of any measured "disagreement" is tokenizer mismatch, not model
  disagreement. The rate has a floor that is not error.

## 8. The test suite to write (none exist today)

All pure, no API, milliseconds. Ordered by value.

**Write first — the regression guard for §2:**
1. Stub the model to raise; assert **no** story gets `text_span_source == 'clause_kept_full'`,
   **no** `speech_profile` is written, and `sum(counts.values()) == stories_labelled`.
2. `reassemble` parity: fresh run with a stubbed model, then reassemble from its labels;
   assert the two artifacts are identical modulo stats.
3. Golden round-trip: segment → clauses → labels → assemble → offset →
   `_assert_word_boundary` passes → sliced Hebrew equals the expected story text.

**`assemble()` — the thesis of the wave:**
4. `[framing, narrative, narrative, comment]` → `(1,2)` under both rules.
5. `[framing, narrative, comment, comment, narrative, legal]` → `first_last (1,4)`,
   `longest_run (1,1)` — **the case the two rules exist to disagree on.**
6. `[narrative, narrative, comment, narrative, narrative]` → `longest_run (0,1)` — pins
   the undocumented earliest-wins tie-break.
7. `[legal, legal, comment]` → `kept_full`, `reason='no_in_story_clause'`,
   `needs_review` — never trim to nothing.
8. `[framing, variant, narrative]` → `(1,2)` — `variant` counts as in-story. This is
   Jeff's 22b_18 rule and it is one word in `IN_STORY` away from silently regressing.
9. `[narrative, parallel, narrative]` → `first_last (0,2)`, `longest_run (0,0)`.
10. `[unclear, narrative, unclear]` → `needs_review`; `[framing, narrative, framing]` → not.
11. `assemble(labels, 0)` and an unknown rule both raise.
12. Every role in `ROLES` exercised at least once — catches a role added to the prompt
    but not the code.

**`parse_labels()` — the trust boundary:**
13. Model labels 1 of 12 clauses → the other 11 are `unclear`, never narrative.
14. `"NARRATIVE"` / `"story"` → assert the chosen behaviour (raise or count), not silent.
15. `covers: [true, false, 0]` must not become `[1, 0, 0]`.
16. `i` out of range / `"3"` / `3.7` / duplicates / `hebrew: []` / missing / `None` /
    non-dict input.

**`build_prompt()`:**
17. All placeholders substituted; no literal `{…}` remains.
18. A `---` inserted mid-prompt must **raise**, not silently truncate — assert a sentinel
    from the END of the template survives.
19. A summary containing `{` survives unmangled.
20. Missing `## PROMPT` raises with the filename in the message.

**Test-set integrity (run in CI):**
21. No `(located_on, segment, direction)` key appears twice with conflicting `clause` —
    **fails today** on Ketubot 67b and Kiddushin 12b, which is the point.
22. Every target's `n_clauses` matches a fresh split of the actual segment text.

## 9. Operational

The "expensive artifact" is written once, at the very end. `_assert_word_boundary` raises,
so any assertion, quota exhaustion or Ctrl-C after story 90 discards every label paid for.
Write labels incrementally or flush on exit. (Pre-existing in Wave 5 too.)
