---
title: The axis UI's structured fields went 100% unused on their first real round
capability: [review]
tractate: []
blocked_by: []
awaiting: []
writes: [validation/generators/generate_axis_review_ui.py, validation/generators/review_ui_core.py, tests/test_review_ui_axes.py]
finding:
superseded_by:
---

# The axis UI's structured fields went 100% unused on their first real round

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) first, then this.
**Capability: 5 Review.** **Cost:** free. No API calls.

## The problem

The per-axis review UI exists to stop boundary corrections being mined out of prose. 16 of
the 70 banked boundary targets are `mixed` or `unclear` for exactly that want, and the
Hebrew quote box with a stated `include`/`exclude` polarity was built to fix it.

**On its first real round, every structured field came back empty.** All 25 Gittin
verdicts: `extent`, `confidence`, `grouping` null; `quote`, `quote_start`, `quote_end`
blank; `quote_polarity` null. He answered `is_story` — the one required question — and
wrote everything else in `notes`.

Five of those notes carry an explicit boundary correction (10b, 19b, 20a, 43b, 70a), two
quoting the Hebrew to cut. **The data arrived; the schema did not capture it.** We are
back to mining prose, which is the state the UI was built to end.

`display_problem` was false on all 25, so this is not a renderer bug. The disclosure
simply went unused.

## The claim to test

We do not know **why**, and the fix depends entirely on which it is:

1. **He never opened the disclosure** — it is behind a control he did not notice or did
   not think was for him. Fix: surface it, or make a note that looks like a boundary
   correction prompt for one.
2. **He opened it and preferred prose** — typing a sentence beat operating three
   dropdowns and a highlight. Fix: accept prose as the interface and make the *parser*
   better, not the form.

**Do not guess.** Reading (2) into a (1) problem produces a worse UI and a parser we did
not need; reading (1) into a (2) problem produces a form he will keep ignoring.

## Method

1. **Open `validation/ui/axis_gittin_unlisted.html` in a browser and use it as he did** —
   CLAUDE.md critical rule 1. Answer `no` on an entry and see what the extent control
   does. Verify the disclosure is reachable and independent of the `is_story` answer
   (`tests/test_review_ui_axes.py` pins that it is — check the test still describes the
   page you are looking at).
2. **Ask him.** One sentence, and it rides along with the next email at no cost: *"when
   you wrote that the last sentence is not part of the story — did you see the highlight
   box, and would you have used it?"* This is the only thing that separates (1) from (2),
   and it is cheaper than any experiment.
3. Only then change the page.

## How you know it worked

The next round returns **at least one** populated `quote` + `quote_polarity` pair — or a
recorded answer from him that prose is what he wants, in which case the finding is that
the form was the wrong instrument and the item closes with the schema unchanged.

## Guardrails

- **Do not gate extent/confidence/grouping behind a `no` on `is_story`.** A passage can
  be a story *and* be mis-bounded; that is the commonest correction he gives us, and a
  test fails if it regresses (CLAUDE.md).
- Both review pages import `review_ui_core.py` so neither can drift —
  `tests/test_review_ui_symmetry.py` guards it. A change here touches both.
- **A round that returns prose is not a failed round.** He answered all 25 and gave us
  three new stories. This item is about the instrument, not the reviewer.

## When done

Write the finding to `docs/findings/<date>-axis-fields-unused.md`, update the
**5 Review** row in [`docs/capabilities/5_review.md`](../docs/capabilities/5_review.md),
add an `## Outcome` below, and `python3 scripts/board.py finish 2026-09-02-axis-fields-unused`.
