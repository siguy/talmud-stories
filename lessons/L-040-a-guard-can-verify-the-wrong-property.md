# L-040 — A guard can verify the wrong property and pass forever

**Date:** 2026-09-01
**Found in:** `scripts/board.py` — three defects behind a passing `--check`
→ [`2026-09-01-board-guards-verify-the-wrong-property.md`](../docs/findings/2026-09-01-board-guards-verify-the-wrong-property.md)

## The rule

**A guard that compares a derivation against itself can never see an error in the
derivation. Before trusting a check, say out loud which property it verifies — then ask
which property you actually care about, and whether anything at all verifies that one.**

## What happened

`scripts/board.py` generates `STATE.md` so that no number in it is hand-typed. It has a
staleness guard, and the guard passed the whole time:

```
$ python3 scripts/board.py --check
STATE.md and WORK.md are up to date
```

`--check` regenerates the board and compares the checksum. So it verifies:

> *STATE.md matches what `board.py` computed.*

The property anyone reading `STATE.md` actually relies on is:

> *STATE.md describes the artifacts and the shipped code.*

Three defects lived in that gap. **If the generator misreads an artifact, it misreads it
identically on both sides of the comparison and the check passes.**

| defect | what the board said | what was true |
|---|---|---|
| stale recall artifact | Triage 98.0% / 95.6% | shipped rule gives 98.7% / 97.8% |
| two files collided on a dict key | one ground-truth row, all zeros | two files; the blind list was overwritten |
| verdicts counted by truthiness | 24 verdicts | 25, and the file says `"reviewed_count": 25` |

The middle one is the sharpest. It was filed as *"a file renders as three zeros"* — a
cosmetic complaint. Running the pre-fix loader showed the table had **never displayed the
Kiddushin blind list at all**: the 89-blind / 90-for-recall denominator behind every
Kiddushin recall number the project quotes, replaced by zeros belonging to a different
file. It presented as untidy and was in fact missing.

## Why the two other guards missed it too

`test_bookkeeping.py` pins the golden counts, the immutable harness's hash, and every
link. All real properties, all intact. **None of them is "the numbers on the board
describe the shipped code."** Nothing asserted that, anywhere — and it is the one a
checksum can never reach, because the generator is honest about an artifact that is stale
about the code.

## How to apply

- **Write down the property, in one sentence, before writing the guard.** *"STATE.md
  matches what board.py computed"* and *"STATE.md describes reality"* are different
  sentences. A guard is only as good as which one you wrote.
- **Never let a comparison have the same source on both sides.** Regenerate-and-diff
  catches a hand edit and nothing else. To catch a bad read you need a *second, independent*
  statement of the same fact — which is why the fix asserts the board's count against the
  **file's own `reviewed_count`** and against the **ruler's denominator**, not against
  another call to the same function.
- **Prefer the artifact's self-description.** `"reviewed_count": 25` sat unread in the
  file the entire time. When an input states its own size, check against that before
  deriving one.
- **Run the old code, do not read it.** All three were confirmed by executing
  `git show HEAD:scripts/board.py` against the real repo. Reading it had already been done
  — twice — and the collision was invisible both times, because `f.stem.split("_")[0]`
  looks like a tidy-up until you print the keys.
- **"Generated" is not "correct."** The board was built to end hand-typed numbers and it
  succeeded; the failure mode simply moved from *typing a wrong number* to *reading an
  artifact wrongly*, which is quieter. Provenance is a property to be tested, not inferred
  from how a file was produced.

## The general form

Lesson 31 says *verify a guard by simulating the failure it guards against*. This is the
question one step earlier, and the one that lesson assumes you have already answered:

> **Which failure is it guarding against?** Simulating the wrong failure passes just as
> convincingly as guarding against the right one.

Lesson 38's *absence is quiet* is the input-side twin: there, a loader dropped data
silently; here, a **guard** was silent about the drop as well, and its green result made
the silence look like health. A passing check is evidence about the property it tests, and
about nothing else.

Related: Lesson 31, Lesson 38, Lesson 27, Lesson 17 (a lesson must be a durable gate, not
a passive note — and a gate on the wrong property is a passive note wearing a gate's
clothing).
