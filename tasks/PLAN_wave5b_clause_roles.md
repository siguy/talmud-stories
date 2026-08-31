# Wave 5b — Clause-role labelling (the judgment layer on top of Wave 5)

**Status: ON HOLD 2026-08-30.** Built (433 lines) but **must not run** until the
measurement is fixed and two correctness bugs are closed. Three independent reviews
(DHH / Kieran / simplicity) converged on the same verdict: the gate cannot currently
measure what this wave would be judged on, and the incumbent it replaces has never
been run without a known handicap.
**Relationship to Wave 5:** successor on the same axis, not a replacement.

> ## REVIEW OUTCOME 2026-08-30 — read before touching this wave
>
> **Full findings as an actionable fix list:**
> [`docs/findings/2026-08-30-wave5b-review.md`](../docs/findings/2026-08-30-wave5b-review.md)
> — every P0/P1/P2 item, the scope cuts, the 22 tests to write, and the claims in this
> plan that turned out to be wrong. **If the cheap path fails and Wave 5b is revived,
> start there.**
> **Plain-language decision record:**
> [`docs/findings/2026-08-30-wave5b-decision.md`](../docs/findings/2026-08-30-wave5b-decision.md)
>
> ### The core idea survived. The execution did not.
>
> All three reviewers endorsed the decomposition (label real units -> assemble
> deterministically) as the right answer to Lesson 16 and the right application of
> Lesson 10. Everything below is about scope, measurement, and correctness.
>
> ### P0 — a failed API call is recorded as a successful judgment
>
> Reproduced through the real runner with every model call stubbed to fail, 5 stories:
>
> ```
> counts: {'clause_roles': 0, 'clause_kept_full': 5, 'no_clause_split': 0, 'skipped': 7}  sum=12
> stories_labelled: 5
> text_span_source on failed stories: {'clause_kept_full'}
> speech_profile fabricated:  {'all_speech': False, 'speech_ratio': None}
> needs_review flags set: 0
> ```
>
> `clause_kept_full` means "the model read this segment and judged all of it in-story."
> In a total outage every story gets that stamp. `speech_profile` is fabricated with a
> confident `all_speech: False` and written into `results/clause_labels/` — the dataset
> that is supposed to produce the Wave 6 speech-act number for Jeff. Counts sum to 12
> for 5 stories, so no reported figure is a partition of anything.
>
> **This is the v10 silent-regex-fallback failure re-introduced.**
> `src/story_detector_v11.py` gets it right (writes `'skipped'`); the new runner
> regressed against the file it was forked from. See Lesson 21.
>
> The scorer compounds it: a completely dead run scores **6% HIT / 38% HIT+NEAR** —
> numerically identical to the no-trim baseline. A run that half-failed on quota reads
> as a run that made deliberate no-trim choices.
>
> ### CORRECTION — "English sentences nest over Hebrew clauses" is FALSE
>
> That claim was generalised from three hand-checked examples and is wrong on
> **21% of boundary segments** (26/126 have MORE English sentences than Hebrew
> clauses; worst is 6 clauses vs 10 sentences). Nesting is impossible there, so at
> least one clause is claimed by multiple sentences. The cross-language consistency
> check rests on this and is therefore much weaker than claimed. A further 36% of
> segments are more fragmented in English than Hebrew purely from tokenizer
> asymmetry (Hebrew splits on `. : ? !`, English on `. ! ?`), so part of any measured
> "disagreement" is not disagreement at all.
>
> ### The gate cannot measure what this wave would be judged on
>
> - 52 targets are **47 distinct** (5 duplicates, so 3 expert judgments are double-weighted)
> - **2 are self-contradictory** (Ketubot 67b seg15 wants 5 and 6; Kiddushin 12b seg4
>   wants 0 and 1) -> **a perfect run scores 50/52**, and nothing says so
> - only **16 are scorable** on Kiddushin; 29 of the 36 N/A are Ketubot targets, and
>   Wave 5 was simply never run on Ketubot
> - `anchor_verified` is false on all 52; only 7 of the 16 scorable are polarity
>   `include`. `NEAR` tolerance (±1 clause) is exactly the size of the suspected
>   anchoring error, so for the other 9 only HIT+NEAR carries information.
>
> Effective n is **~14 distinct non-contradictory boundaries**. "Beat ~50%" means
> "get 8 right instead of 7." That is one case — the same shape as the 8-case fixture
> and the model recommendation, both already overturned this session.
>
> ### Attribution — the strongest strategic objection
>
> As built, this wave changes the taxonomy, adds an English channel, AND introduces an
> assembly-rule choice **simultaneously**, then judges all three on ~14 cases. If the
> number moves we will not know which change moved it; if it does not, we will not know
> which to drop. That is exactly the reasoning used to separate Wave 4 from Wave 6,
> violated here.

| | Wave 5 | **Wave 5b** |
|---|---|---|
| Claim | boundaries are **well-formed** | boundaries are **correct** |
| Mechanism | model picks a clause range (2 integers) | model labels every clause's role |
| Status | built (`src/story_detector_v11.py`), A/B'd, ~50% on expert targets | designed only |
| Gate | 0% mid-word / 100% clause-edge — **passes** | beat ~50% on the 52 expert targets |

Wave 5 made a mid-word cut structurally impossible. It did **not** make the boundary
right. Wave 5b is the judgment layer.

---

## Why the architecture changes

Wave 5 asks one open question — *"which clauses does the story occupy?"* — and returns
**two integers**. One judgment, wide answer space, and when it is wrong we cannot see why.

This contradicts three of the project's own lessons:
- **Lesson 10:** narrow questions beat open-ended ones (3 found / 0 FP vs 28 FP).
- **Lesson 7:** post-hoc layers beat cramming more rules into one prompt.
- **v7's own architecture** is a 4-stage decomposition — decomposition is what works here.

The replacement decomposes it:

| Layer | Does what | By |
|---|---|---|
| 0 | split into clauses on `. : ? !` | deterministic (built, Wave 5) |
| 1 | **label each clause's role + is_speech** | model — one narrow judgment per real unit |
| 2 | assemble the boundary from labels | deterministic rule |
| 3 | cross-language consistency check | deterministic comparison |

**Cost is roughly flat.** Same input, output goes from 2 integers to ~5 labels.
Adding English roughly doubles input. Kiddushin cost pennies and 6 minutes; double
is still pennies. Cost has never been the constraint on this project.

## Why it should scale (and the honest caveat)

Clause structure is a property of Sefaria's Davidson edition, not of one tractate —
verified across both:

| | Kiddushin | Ketubot |
|---|---|---|
| median clauses/segment | 4 | 4 |
| median words/clause | 5 | 5 |
| segments with no split possible | 8.7% | 9.3% |

The approaches that failed before — the regex trimmer (Lesson 15), the hardcoded
introducer lists — keyed on **surface words**, which Jeff showed are story content
about half the time. Clause labelling splits on punctuation (unambiguous) and asks
the model to judge **meaning** per unit. That is what Lesson 15 said the fix had to be.

**Caveat: none of this is tested.** It is reasoning from design and project history.
Two recent confident claims (that 3.7-flash was better; that the 8-case fixture meant
something) were both overturned by more data. Treat as a hypothesis with a cheap test.

## Label taxonomy

Every role traced to Jeff's own recurring language, plus frequency measured over
21,381 clauses across both tractates.

| Role | From Jeff | Freq (marker proxy) |
|---|---|---|
| `narrative` | "Stories are about events that happened"; "a rabbi's concluding reflection IS the story's closure" | — |
| `framing` | "adjusted to the story alone without the transition to the story" | — |
| `comment` | "the last line is the Talmud's comment on the story and not part of the story itself" | — |
| `legal` | "There are no events. This is just a legal discussion" | — |
| `source` | "It is the end of the baraita" | 2.6% |
| `parallel` | 30a cl.8 — Rabbah bar Rav Huna does the same thing; Jeff **excludes** it | 3.1% |
| `variant` | `אִיכָּא דְּאָמְרִי` "some say" — Jeff **keeps** it (22b_18); both models wrongly trimmed it | 0.4% |
| `unclear` | Jeff: mark borderline, "let database users decide" | — |

Plus a boolean **`is_speech`** on every clause — NOT a role, because speech cuts across
roles (a character speaking is story; rabbis debating is not). Explicit dialogue
markers alone appear in 4.9% of clauses, the most common category measured.

**`is_speech` is the highest-value field in this design and its value is not
boundaries.** It makes Jeff's speech-act question computable: "how many golden stories
are nothing but speech?" stops being a judgment call and becomes a query — which is
exactly the Wave 6 blast-radius number we need before writing to him.

Rejected after measuring: `attribution` (0.2%, too rare); scripture as its own role
(2.4%, but a verse quoted *by a character* is story while a proof-text is not — the
role logic already handles it).

## English

English is **not** currently boundary-marked. Correction to an earlier claim in this
project's notes: the review UI *does* display and highlight English, but at **segment**
level (`generate_wave4_review_ui.py`, `buildTextDisplay`), while Hebrew gets
sub-segment trim marking via `renderHebrew`. Jeff comparing a segment-level English
highlight against a sub-segment Hebrew trim is a large part of "the English is right
but the Hebrew is cut off."

Verified: English sentences **nest** over Hebrew clauses (each English sentence covers a
contiguous run of Hebrew clauses), so Hebrew boundary points are a subset of English
ones. On 30a seg 7, English sentence 3 is exactly Hebrew clause 8 — the parallel Jeff
excludes — flagged in English as "Similarly,".

**Do not trust English framing markers as a rule.** "The Gemara comments:" marks a
correct cut on 12b seg 4 and a wrong one on 22b seg 18. Same marker, opposite answers —
Lesson 15 in English. Evidence for a judgment, never a rule.

Label English sentences with the same taxonomy. Because the two nest, **disagreement
between the Hebrew and English labelling is an error signal** — no second model, no
extra call, no expert time. This is the sub-segment verification the project currently
lacks.

## Where results are stored

Per-clause labels **outlive the wave that produces them** — they are features for the
false-positive classifier (Lesson 7), input to Wave 6, and the basis of English spans
in the published database. So they are a first-class artifact, not a wave by-product:

```
results/clause_labels/<tractate>_<detector-version>_<model>.json   # the labels themselves
results/v11/wave5b/<tractate>_<variant>.json                       # boundary outputs
tests/expert_boundary_targets.json                                 # the 52-target test set
src/prompts/clause_roles_v*.md                                     # versioned prompts
docs/golden/v11/wave5b_results.md                                  # the writeup
```

Each labels file records model, thinking level, prompt version, and date, so runs stay
attributable (roadmap 5.3: pin and record external versions).

## REVISED SEQUENCING (supersedes the phases implied above)

**Step 0 — fix correctness. Own commit, no new features.**
1. Failure semantics: `text_span_source = 'skipped'` on API failure, set `needs_review`,
   never write a fabricated `speech_profile`, exactly one counter per story.
2. Preserve `no_clause_split` provenance — currently overwritten, violating
   [PLAN_wave5.md](PLAN_wave5.md)'s own "named, logged outcome, never a silent accident."
3. Extract one `emit_span()` used by both `main()` and `reassemble()`; they have already
   diverged (reassembled artifacts lack `speech_profile`/`needs_review` and are not even
   stamped `-wave5b`).
4. Regression test: stub the model to fail; assert no story reads as a judgment, no
   `speech_profile` is written, and `sum(counts.values()) == stories_labelled`.

**Step 1 — fix the measurement, before any Wave 5b run.**
5. Run **existing Wave 5** on the two Ketubot no-trim files (both already on disk).
   Scored n goes **16 -> ~45**. Two commands.
6. **One-hour human anchor pass** over the 52 targets. Resolve the 2 contradictions,
   drop or merge the 3 duplicates, set `quote_polarity` and `anchor_verified` by hand.
7. Scorer: read `wave5b_stats.counts` and refuse to score (or banner loudly) when
   `skipped` is non-trivial; add a `FAIL` bucket; break results out by polarity;
   assert stored `clause_count` still matches a fresh `_split_into_clauses`.

**Step 2 — tune the incumbent before replacing it.**
8. Fix the summary bug in `src/story_detector_v11.py` (`_llm_text_span_for_story`) —
   one line, put `one_sentence_summary` first. Verified: `summary` is present on
   **0 of 95** stories, so the prompt has always fallen back to a joined events list
   that **drops the story's resolution** — while 35 of 52 targets are END boundaries.
   The handicap is biased against precisely the axis being measured.
9. Add English and `classification_reasoning` as **context** to the existing one-shot
   prompt (~6 lines). No labels, no `covers`.
10. Re-score at n~45. **If a properly-fed one-shot still stalls near 50%, Wave 5b has
    earned its place — against a trustworthy baseline.**

Total for Steps 1-2: **under 10 lines of diff** against the 433 already written.

**Step 3 — only then, and cut down.**

| Ship | Cut (add back only when data demands) |
|---|---|
| 3 roles: `story` / `not_story` / `unclear` | the other 5 roles — `assemble()` reads only `IN_STORY`, so they are inert at the point of use |
| `is_speech` boolean | English labelling, `covers`, cross-language check |
| Hebrew only; English as prompt context | `longest_run` (keep `first_last`, the conservative under-trim matching our stated risk preference) |
| one assembly rule | separate `results/clause_labels/` artifact for consumers that do not exist yet |

Estimated: 433 -> ~150 Python lines. Change **one thing at a time** so the result is
attributable.

`variant` is the closest call: its whole evidence base is one case (22b_18) and it is a
literal string (`איכא דאמרי`, 4 of 95 stories). A two-line lexical rule buys the same
outcome without spending a model-facing role — but note Lesson 15 before trusting any
lexical rule.

## Gates

| Gate | Threshold |
|---|---|
| Structural | 0% mid-word, 100% clause-edge (inherited from Wave 5) |
| **Expert targets** | beat Wave 5's ~50% exact on the same 52-target scorer |
| Cross-language | report Hebrew/English label disagreement rate; it is a signal, not a threshold |
| Composites, regenerated today | Ketubot ≥ 0.9171, Kiddushin ≥ 0.8859, both ranges (Lessons 6, 11) |
| Segment boundary vs Jeff's 2005 list | ≥ 69% exact — must not regress |

**Bias warning that travels with every expert-target number:** all 52 targets are cases
Jeff flagged as WRONG. They measure fixing known failures, not avoiding new ones. Pair
with a RANDOM sample of currently-correct stories.

**Unverified anchors:** the targets are anchored on the longest Hebrew quote in each
note, which is right for "the story ends with X" and wrong for "X should be crossed
out." Polarity is recorded per target (`include` 23 / `exclude` 10 / `mixed` 5 /
`unclear` 14) and `anchor_verified` is false on all 52. A one-hour human pass would
make these numbers gate-grade. Until then, treat absolute scores as provisional — the
trim-vs-no-trim gap survives this, model-vs-model differences do not.

## Open questions to settle by testing, not argument

- **Assembly rule:** first→last `narrative`, or longest unbroken run? They differ when a
  `comment` interrupts a story. Both are one line; test both.
- **English on/off:** doubles input cost, untested as a help. It failed as a
  *verification* signal (0/8 on start boundaries) — that says nothing about its value
  as *context*.
- **Do `legal` and `comment` earn separate labels?** For boundaries both mean "trim."
  Kept because they are raw material for the FP classifier and Wave 6.

## How this fits the broader work

| Consumer | What it takes from here |
|---|---|
| **Wave 6** (criteria, blocked on Jeff) | `is_speech` gives the speech-act blast-radius count — the number we need BEFORE writing to him |
| **FP classifier** (Lesson 7) | clause-composition ratios as real features, replacing thin ones (criteria count, disqualifier list) |
| **Crowd-sourced DB** | English spans are a deliverable; today Hebrew is trimmed and English is not, so published spans would not match |
| **Wave 7** (lexicon) | `framing` labels show which openers actually introduce stories |
| **Segment selection** | untouched — solved since v7 (median IoU 1.000, flat across 5 versions). Do not disturb it. |

## Dependency to flag early

If clause labels become the unit of truth, **the golden dataset has no sub-segment
ground truth to check them against.** The 52 expert targets are enough to develop and
test, but a published corpus with clause-level spans eventually needs Jeff's sign-off on
the taxonomy itself. Not a blocker; a real dependency, and it belongs in the same
message as the Wave 6 question rather than a separate ask.
