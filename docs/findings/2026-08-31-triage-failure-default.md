# A failed triage call was silently discarding the page — 2026-08-31

**Status: measured.** Found 2026-08-30 while writing
[`docs/capabilities/1_triage.md`](../capabilities/1_triage.md); fixed 2026-08-31.
**Effect on every published number: none, and that is proven below rather than assumed.**

## The defect

`EventTriager.triage_page()` returned `[DELIBERATION] * n` whenever the model's response
would not parse, under this comment:

```python
if not result:
    # Default: all DELIBERATION (safest — won't skip pages incorrectly)
    return [EventType.DELIBERATION] * len(segments)
```

**The comment is backwards.** `should_skip_page()` keeps a page only when
`NARRATIVE_EVENT ≥ 2`, or `NARRATIVE_EVENT ≥ 1 and VERBAL_ACT ≥ 2`. All-DELIBERATION gives
`narrative_count == 0`, so **both** conditions fail and the page is **skipped**. A failed
API call did not fail safe; it threw the page away.

## Why this one is worse than it looks

It sits in the one capability whose errors leave no trace. A page never examined produces
no record of what was lost ([`FRAMEWORK.md` §1.1](../../FRAMEWORK.md)), so nothing
downstream — not `evaluate_golden.py`, not `measure_recall_vs_expert_list.py`, not the
review UI — can see the loss. Triage recall is measurable only against an external blind
list, and only for the two tractates that have one.

This is **Lesson 21**'s exact shape: *a failure recorded with the value that also means a
considered judgment.* "Every segment is DELIBERATION" is a legitimate verdict about a
purely legal page. When a crash says the same words, no reader can tell them apart.

It is also the third member of a family this project keeps rediscovering — Lesson 21 (a
failed call stamped as a judgment), Lesson 23 (an exam that cannot see a regression),
Lesson 27 (a step that moves records out of the measured path). **In all three the
measurement, not the code, was the thing that was wrong.**

## What changed

- **`EventType.TRIAGE_FAILED`** — a distinguishable provenance value. A failure now says
  *"we could not look"*, never *"we looked and found nothing."*
- **`should_skip_page()` fails open**: any `TRIAGE_FAILED` segment keeps the page.
  Examining it costs one Stage 2 call; discarding it costs a story we can never find again.
  That asymmetry is the whole argument.
- **`summarize_triage()` counts *and names* failed pages** (`failed`, `failed_refs`). An
  error rate nobody counts is an error rate nobody notices, and you cannot re-run what you
  cannot identify. Nothing counted these before, so **the historical failure rate is
  unknown and unrecoverable.**

## Proof that no published number moves

The shipped triage decisions come from caches (`results/v7/event_triage_*.json`), so the
question is whether the new rule changes any decision recorded in them:

```
pages whose skip decision CHANGED under the fix : 0
TRIAGE_FAILED segments in the caches            : 0
```

The caches contain no failures, so the fix cannot alter them. Ketubot stays at 124 of 222
pages skipped and Kiddushin at 100 of 162.

*A discrepancy worth recording, since it looks like one and is not.* Replaying
`should_skip_page` over the caches alone gives **130**/222 Ketubot and **109**/162
Kiddushin, not 124 and 100. The gap is the **Wave 1 lexical override** (`eff0218`): pages
containing a canonical story introducer are forced through Stage 2 whatever triage said.
The run figures already include it; the raw rule does not. Anyone re-deriving skip rates
from the caches must apply `_page_has_story_introducer()` too, or they will report a
tractate as more aggressively triaged than it is.

## Guarded by

[`tests/test_triage_failure_default.py`](../../tests/test_triage_failure_default.py) — ten
tests, no API key, no network. Written **first** and watched fail: before the fix, four
failed, including the one that matters (*"a failed triage call caused the page to be
SKIPPED"*). They also pin the things the fix must not break — a genuinely legal page is
still skipped, the keep-rule is unchanged, and the three cached triage files still
deserialize now that the enum has a fifth member.

## Not fixed here

Inside a *successfully parsed* response, a segment whose `event_type` string is unknown
still falls back to `DELIBERATION` (`src/event_triage.py`, the `except ValueError` branch).
That is a per-segment default within a real answer rather than a whole-page failure, so it
is a much smaller hazard — but it is the same shape, and it is unmeasured.
