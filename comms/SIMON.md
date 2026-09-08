# Simon Brief — the decisions that are his, not Jeff's and not ours

Companion to [`JEFF.md`](JEFF.md), and it exists for the same reason: a question with no
home gets carried in prose, and prose is invisible to
[`board.py`](../scripts/board.py). A work item may name any question here as
`simon:<slug>` in `blocked_by` or `awaiting`, and
`tests/test_bookkeeping.py::test_blocked_by_and_awaiting_resolve` will resolve it.

**Created 2026-09-04, after the gap bit twice in one day.**
[`rerun-all-tractates`](../work/2026-09-03-rerun-all-tractates.md) needed to say *"blocked
until Simon says which tightening he means"* and could not: `awaiting` accepted only an
item slug or a `jeff:` question. Both orderings lived in prose, in a file whose own
frontmatter then read as unblocked. That is precisely the failure the `blocked_by` graph
was built to prevent, and the schema had a hole where half the deciding happens.

**What belongs here and what does not.** A question is Simon's when it trades cost,
throughput or scope — money, calls, wall-clock, reviewer attention, what ships. It is
Jeff's when it is a claim about the tradition or about scholarly completeness, and those
go in `JEFF.md`. FRAMEWORK §2b once assigned `jeff:miss-rate` to Simon and was corrected;
the boundary is worth keeping sharp in both directions.

## Open questions

| slug | question | why it blocks | status |
|---|---|---|---|
| `simon:end-to-end-target` | What end-to-end recall must the pipeline hit for the corpus to be publishable? | **Every gate below it is invented.** FRAMEWORK §2b: Triage ≥98% and Detection ≥95% are "our current value, which is circular reasoning in a principle's clothing". They compose, so only the end-to-end number needs defending — and it is a product decision, not a technical one. Jeff's `jeff:miss-rate` answers the *scholarly* half; this is the half about what we are willing to pay for it. | **open** |
| `simon:review-throughput-price` | How many false proposals per tractate is one recovered story worth, in Jeff's reading time? | Decides [`examine-all-pages`](../work/2026-09-03-examine-all-pages.md) and every future triage-threshold trade. Measured: examining every page buys 1–3 stories per tractate for ~24 extra false proposals. Simon accepted the **call** cost on 2026-09-03; the cost that matters is Jeff's attention, and **that half is still unpriced**. | **open** — partly answered |

## Answered

| slug | answer | date |
|---|---|---|
| `simon:which-tightening` | The "story finder was too loose" means the **quasi-speech-act rule**, not the recall aligner's window. *"Story finder — tighten it per what I suggested. Then rerun it so we can see the actual score."* Ruled out in the same breath: the aligner was also too loose, but it is a scoring defect over artifacts already on disk and a re-run cannot fix it. → [`tighten-story-finder`](../work/2026-09-03-tighten-story-finder.md) | 2026-09-03 |
| `simon:frozen-model-defaults` | v5–v10 keep `gemini-2.0-flash`, which Google no longer serves, so running one fails. **Deliberate.** Repointing them would make them run under a model that produced none of their numbers — the failure is loud, the wrong attribution would be silent. Recorded in `src/model_config.py` and in the test's failure message. | 2026-09-04 |
| `simon:model-and-thinking` | Switch to `gemini-3.8-flash` at `thinking_level=high` (#42). The `high` half is **unjustified by evidence** and its experiment is filed and unrun → [`thinking-level-experiment`](../work/2026-09-03-thinking-level-experiment.md). | 2026-09-03 |

## How to use it

1. Add a row above with a slug, the question, and **why it blocks** — the third column is
   the one that stops a question sitting here for five weeks.
2. Name it in the work item's `blocked_by` (cannot start) or `awaiting` (cannot conclude).
3. When answered, move the row to **Answered** with the date and the actual words. Do not
   delete it: an answer that cannot be found gets re-asked, and Simon's time is the
   resource this file exists to protect.
