# `skip_triage` fixed and renamed: bypassing Stage 1 no longer fabricates its output — 2026-09-01

**Capability: 1 Triage.** **Status: measured (0 shipped decisions change), and SHIPPED** —
`src/story_detector_v11.py` changed.
**Follows:** [`2026-09-01-contaminated-no-triage-ablation.md`](2026-09-01-contaminated-no-triage-ablation.md),
which proved the defect and retracted the conclusion built on it. This is the repair.
Item: [`work/2026-09-01-fix-skip-triage-flag.md`](../../work/done/2026-09-01-fix-skip-triage-flag.md).

## What changed

```python
- skip_triage: bool = False
+ examine_all_pages: bool = False,  skip_triage: Optional[bool] = None   # deprecated alias

- if triage_results is None and not skip_triage:
-     triage_results = triager.triage_all_pages(pages, delay=delay)
- elif skip_triage:
-     # Generate default triage (all DELIBERATION) so detection still works
-     triage_results[ref] = [EventType.DELIBERATION] * n_segs
+ if triage_results is None:
+     triage_results = triager.triage_all_pages(pages, delay=delay)
```

The flag now gates **only** the `pages_to_process` branch. Stage 1 runs whenever labels
were not supplied, including under `examine_all_pages`; supplied labels are never
overwritten.

**A second instance of the same fabrication, in the Stage 2 loop:**

```python
- events = triage_results.get(ref, [EventType.DELIBERATION] * len(segments))
+ events = triage_results.get(ref, [])          # renders as "[UNKNOWN] Seg N"
```

A page with no triage entry has not been judged deliberative; it has not been judged.
`[]` reaches `build_prompt`'s own `"UNKNOWN"` fallback, which is what the cross-page
context blocks eight lines below were already doing.

## Why the labels matter even when every page is examined

The old flag's name suggested the labels were inert once you stopped skipping. They are
not — four consumers read them:

| consumer | what the stub told it |
|---|---|
| `detect_stories()` → Stage 2 prompt | `[DELIBERATION] Seg N:`, under a header stating each segment "has been pre-classified by event type" |
| cross-page context blocks | the same, for the neighbouring daf |
| `refine_boundaries_with_event_tags()`, `merge_cross_page_stories_v7()` | no narrative anywhere to anchor on |
| post-processing `rule3_v6_ensemble` | "page has only 0 NARRATIVE_EVENT(s)" — true of every page by construction |

So `skip_triage=True` did not remove Stage 1's influence. It replaced Stage 1's verdict
with the most confident wrong one available and passed it to all four.

## Guarded

`tests/test_examine_all_pages.py` — **10 tests, written first and watched fail** (Lesson
31); 9 of 10 failed before the change. No API key, no network, no model. They pin:

- supplied labels survive the bypass, and no page arrives as uniform DELIBERATION;
- the labels are **identical with and without** the flag — it selects pages, it is not an
  input to how a page is read;
- the flag **only ever adds** pages (`off ⊆ on`) — the property whose violation exposed the
  original contamination;
- an unjudged page arrives `[]`, not DELIBERATION;
- the `skip_triage` alias still works, warns, and does **not** resurrect the stub; passing
  both spellings is a `TypeError`;
- **v7–v10 still contain the stub.** They are frozen ship points (CLAUDE.md), and
  `results/v7/ablation_v7_no_triage.json` must stay reproducible from the code that made
  it, or the retraction loses its evidence.

## What does not move

**No published or shipped number.** Every shipped run used cached triage labels and never
touched this flag; the 2026-08-31 pricing deliberately routed around it, and the `N>=1`
rule change is in `event_triage.py`, untouched here. The full suite is 125 passed against
main's 115 — the difference is exactly these 10 tests — with the same 6 pre-existing
`textutil` failures (a macOS-only binary).

**And the retracted claim stays retracted.** Fixing the flag does not re-measure anything.
Replacing the struck 2026-02-13 row needs a corrected run, for which
`scripts/run_triage_recall_price.py` already implements the right shape (real labels, skip
decision the only variable) — now reproducible through the flag itself rather than around it.
