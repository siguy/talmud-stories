# Lesson 21 — A failed call must never be recorded as a decision

**2026-08-30**

Wave 5b's runner, written the same day as Lessons 18-19, reintroduced the
exact failure the v10 regex fallback taught us. Reproduced by stubbing
every model call to fail:

```
counts: {'clause_roles': 0, 'clause_kept_full': 5, 'skipped': 7}  sum=12
stories_labelled: 5
text_span_source on failed stories: {'clause_kept_full'}
speech_profile fabricated: {'all_speech': False}
needs_review set: 0
```

`clause_kept_full` means "the model read this and judged all of it
in-story." In a total outage every story got that stamp, a fabricated
`speech_profile` was written into the dataset intended to answer Jeff's
speech-act question, and the counters summed to 12 for 5 stories. The
scorer then rated the dead run at 6% HIT / 38% HIT+NEAR — identical to
the legitimate no-trim baseline.

The cause was structural, not careless: the failure path `continue`d an
inner (per-side) loop, then fell through to an unconditional
"success" write after the loop. `src/story_detector_v11.py` avoids this
by `continue`ing the *story* loop, keeping the buckets mutually
exclusive. The new code regressed against the file it was forked from.

**Rule:** Every outcome bucket must be mutually exclusive and must sum
to the number of items processed. Assert it. A failure must write a
distinguishable provenance value — never the value that also means a
considered judgment — and must never emit derived data (ratios, flags,
profiles) computed from absent inputs.

**Why:** A wrong answer gets caught. A *confident* answer with the
provenance stripped off does not — it flows into results docs, datasets,
and expert-facing artifacts as though it were a judgment. This is the
same shape as the v10 regex fallback, and it is quieter, which makes it
worse.

**How to apply:** (a) `assert sum(counts.values()) == n_processed` in
any runner that reports counts. (b) Write the failure-injection test
FIRST: stub the model to raise, assert no item acquires a
success-provenance value and no derived field is written. (c) When
forking a file, diff the failure paths specifically — that is where the
hard-won handling lives and where a rewrite silently drops it.
(d) Scorers must read the run's own failure counts and refuse to score,
or quarantine failures in their own bucket, rather than silently folding
them into the metric.

**Status:** the runner was fixed 2026-08-30 and is guarded by
`tests/test_wave5b_runner_outcomes.py` — the failure-injection test was
written first and watched fail. Same fixture, model failing every call:
before `{kept_full: 6, no_split: 2, skipped: 6}` = 14 counts for 6
stories with 6 fabricated speech profiles; after `{no_split: 1,
skipped: 5}` = 6 counts, 0 profiles, 5 `needs_review`. Point (d) —
the scorer — is **still open**.

**A second instance, found 2026-08-30 and fixed 2026-08-31 — in Stage 1, which
is the worst place for it.** `EventTriager.triage_page()` returned
`[DELIBERATION] * n` on an unparseable response, commented *"safest — won't
skip pages incorrectly."* The comment was backwards: all-DELIBERATION gives
`narrative_count == 0`, which fails both keep-conditions, so **a failed call
silently discarded the page.**

Two things make this instance instructive beyond the first:

- **The comment asserted the opposite of the behaviour**, and nobody checked.
  It read as a considered safety decision, which is the most effective possible
  disguise for a defect. A stated intention is not a test.
- **No harness could ever have caught it.** The wave 5b instance at least
  corrupted an artifact somebody scores. A triage discard leaves no trace
  anywhere downstream (FRAMEWORK §1.1), so the only instrument that can see it
  is an external blind list — which exists for two tractates out of thirty-seven.

Fixed by giving failure its own value (`EventType.TRIAGE_FAILED`), failing
**open** on it, and counting and naming the failed pages. Proven to change 0 of
the shipped skip decisions. **The historical failure rate is unknown and
unrecoverable, because nothing ever counted it** — which is the durable cost of
this class of bug and the reason to fix it before you need the number.
→ `docs/findings/2026-08-31-triage-failure-default.md`,
`tests/test_triage_failure_default.py`

**The generalisation, now that there are two:** when a failure path picks a
fallback value, ask *"is this value also something a successful run could
legitimately produce?"* If yes, it is not a fallback — it is a disguise.
