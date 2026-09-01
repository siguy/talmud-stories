# L-038 — A guard that skips silently looks exactly like empty input

**Date:** 2026-08-31
**Found in:** the 2026-01-08 review round, unread for eight months
→ [`2026-08-31-january-round-recovered.md`](../docs/findings/2026-08-31-january-round-recovered.md)

## The rule

**Every `continue`, `if not isinstance(...)`, and silent `except` that drops an input must
count what it dropped and name it. An input skipped without a count is indistinguishable
from an input that was never there — and nobody investigates a zero.**

## What happened

`build_ruler.load_reviews()` walks every feedback file and reads its verdicts:

```python
items = data.get('reviews') or data.get('feedback')
if not isinstance(items, dict):
    continue                      # <- eight months of expert work, gone quietly
```

Every round stores verdicts as a dict keyed `"<ref>_<start>-<end>"`. One does not: the
**2026-01-08 Ketubot round — 25 verdicts, 24 with notes, signed by Jeff by name** — stores
a *list* of `{ref, feedback_type, notes, …}`. The guard drops it.

The file was never hidden. It sat in `validation/feedback/`, and `STATE.md` listed it by
name for months under *"Expert verdicts on disk that no ruler reads"*. It was still not
investigated, because **the note listed two other files alongside it that contain nothing
at all** — one has an empty `validations` dict, the other is an automated eval trace with
no expert judgement in it. Three names with no counts reads as a filing backlog. One name
with "**25 verdicts**" beside it reads as a problem.

Lost with it: 9 cross-page refs covered by no other round — aimed squarely at the
project's known weakest area — and structured `length_adjustment` / `spans_multiple_pages`
fields that no later round has.

## Three instances of the same shape, all found on one day

| where | what was silently dropped | how it presented |
|---|---|---|
| `build_ruler.load_reviews()` | a whole review round, wrong container type | file looks empty |
| `measure_recall_vs_expert_list.py` | miss-cause buckets need not sum to the miss count | a plausible split that is wrong |
| `board.py unfolded_verdict_files()` | listed files without counting their contents | signal buried among empties |

None of these was a crash. All three produced output that looked entirely reasonable.

## How to apply

- **Count at every skip.** `skipped_wrong_shape`, `skipped_no_verdicts`,
  `skipped_unparseable` — then print the counts. A loader that cannot say how many inputs
  it declined is not reporting, it is asserting.
- **Never let an empty result and a rejected input share a representation.** Zero verdicts
  because the file is empty, and zero verdicts because the parser did not recognise it, are
  different facts and must be printed as different facts.
- **In an inventory, print the size of each item.** A list of names invites triage by
  eyeball; a list of names with counts does the triage for the reader. This is why
  `board.py` now counts verdicts and omits files holding none.
- **Accept more than one shape, or fail loudly on an unknown one.** Silently accepting only
  the shape you expected is the worst of the three options.

## The general form

This is Lesson 21 (*a failed call must never be recorded as a decision*) and Lesson 27
(*a step that moves records out of the measured path*) applied at the **input** boundary
rather than the output one. The family rule across all three:

> **Absence is quiet.** Any code path that can make data disappear must be made to make
> noise instead — a count, a warning, a named bucket. Nothing else will surface it, because
> the symptom of missing data is that there is nothing to look at.

Related: Lesson 21, Lesson 27, Lesson 36 (which found the same shape in a *join*: matching
verdict spans by exact key made a re-bounded story read as a deleted one).
