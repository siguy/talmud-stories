# Design note: the reader-case set (Phase 5, not built)

Build only when about 20 reader reports are confirmed. Until then `ledger.json` (private repo) is enough.

- **Source:** ledger rows with an outcome and `decided_by`. A case is *confirmed* only when Simon, the two judges or Jeff
  ruled it so; each row records which. Tests (`test: true`) and staging never count.
- **Where:** the private feedback repo (it carries readers' claims). The main repo holds ids and outcomes only
  (`results/site_feedback/outcomes.json`).
- **Held out:** never a few-shot example, never in a prompt (Critical Rule 2). Reader reports are tips, not ground truth.
- **Biased sample, said plainly:** readers only see what we shipped, so it measures false positives and boundary errors,
  never missed stories. Report it beside golden recall, never instead of it.
- **`score_reader_cases.py` (later):** counts only, no composite (Critical Rule 5): of confirmed not-a-story cases, how many a
  new detector still ships; of confirmed boundary fixes, how many it now gets right unaided. `evaluate_golden.py` untouched.
- **Note writer:** each confirmed note mistake is a test; recurring types become a check in `build_site_notes.py`.
- **Jeff:** three or more confirmed reports on a pattern STORY_RULES.md does not settle -> one batched question in `comms/JEFF.md`.
