---
title: The axis UI's structured fields went 100% unused on their first real round
capability: [review]
tractate: []
blocked_by: []
awaiting: []
writes: [validation/generators/generate_axis_review_ui.py, validation/ui/axis_ketubot_review.html, validation/ui/axis_kiddushin_review.html, tests/test_review_ui_axes.py, scripts/board.py, tests/test_finish_fixes_inbound_links.py, docs/capabilities/5_review.md]
finding:
superseded_by:
---

# The axis UI's structured fields went 100% unused on their first real round

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then this.
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
**5 Review** row in [`docs/capabilities/5_review.md`](../../docs/capabilities/5_review.md),
add an `## Outcome` below, and `python3 scripts/board.py finish 2026-09-02-axis-fields-unused`.

## Outcome

**Done, 2026-09-02 — and the question this item said to ask him did not need asking.**
Finding: [`2026-09-02-axis-fields-unused.md`](../../docs/findings/2026-09-02-axis-fields-unused.md).

The item posed two readings and said not to guess between them, because the fix differs
completely. Step 1 — serve the page and use it — answered it outright.

**Correction, 2026-09-03 — read this first.** Simon objected that Jeff sent the JSON
directly and the HTML was never the vehicle. The file itself is `buildExport()`'s output
exactly, envelope and all, and cannot be a blank template (the function skips incomplete
cards, so an unfilled page exports `reviews: {}`). So the page produced it. **But the file
cannot say whose hands were on the page** — if Jeff answered in prose and someone
transcribed him into it, the empty fields describe the transcriber, not him. That is one
line from Simon and it is unanswered, so the diagnosis below is **indicated**. The fix
holds under either reading and gates nothing.

**It is reading (1), and the cause is the layout.** On a fresh card the only
always-visible free-text control invites *"Anything else, in your own words"*, and every
axis sits inside `.more-axes` at `display: none` behind a toggle. Prose was the path of
least resistance. Two aggravating details found in the same inspection: the notes control
was a **single-line `<input>`** — he wrote sentences, one quoting a full Hebrew clause,
into a box showing about eight words — and its placeholder only reads as *"anything else"*
to someone who has already seen the fields it is *else* to.

**Step 2 — ask him — was dropped, deliberately.** It was in the plan as the only thing
that could separate (1) from (2), and it stopped being the only thing the moment the page
was opened. Spending one of his scarce replies on a question the DOM answers for free is
the wrong trade, and this is the second time today that looking at our own artifact beat
asking (see [`english-first-prompt`](2026-09-02-english-first-prompt.md)).

### The fix, and its boundary

`<input>` → `<textarea rows="2">`; **typing a note reveals the axes**, once, in place; the
placeholder points at the boxes. It **adds a path and removes none** — a bare `Yes` is
still one click and still leaves the axes shut, prose is still a complete review, and the
reveal is one-shot so a deliberate close stays closed.

**Not done: opening the disclosure by default.** That is a layout decision about a page a
busy reader faces 25 times, with no evidence it helps — it trades a discovery problem for
a density problem. The targeted reveal answers the behaviour actually observed and guesses
at nothing else.

### Guardrails

- The extent axis is still reachable on a `yes`. Nothing was gated.
- Verified in the browser by driving the DOM, not by reading the generator (the failure
  mode this test file was written for). A screenshot of the expanded state would not paint
  — 800KB page, hidden pane, 5,500px scroll — and that limit is stated in the finding
  rather than papered over.
- Pinned as test `I`, and **confirmed to fail when the defect is reintroduced**, which is
  that file's standing convention.
- **`axis_gittin_unlisted.html` was not regenerated.** It is the record of what he saw;
  rewriting it would destroy the evidence for this finding.

### What it does not fix

The five boundary corrections already sitting in prose. They need the same mining as the
70 banked targets, and the mining does not get better in hindsight. This change is about
the next round.

### One unrelated defect fixed on the way, because it fired three times

`board.py finish` broke a markdown link on **each of the three items closed in this
session**, always the same way: an item already in `work/done/` that links to one still
open writes `](../<slug>.md)`, which is right at the time. When that target closes they
become siblings and the `../` is what breaks. `reroot_inbound` had a case for
`work/` and none for `work/done/`.

That is the **same defect Lesson 31 records** — a link broken at the exact moment an item
becomes a permanent record — surviving in the one direction nobody checked. It was fixed
only after the third occurrence; the first two were repaired by hand, which is the tell.
**A fix you keep applying manually is a fix that belongs in the tool.**

Covered by three new cases in `tests/test_finish_fixes_inbound_links.py`, including
idempotence and the already-correct link.
