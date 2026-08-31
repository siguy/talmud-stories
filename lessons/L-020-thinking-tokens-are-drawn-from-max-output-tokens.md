# Lesson 20 — Thinking tokens are drawn from max_output_tokens

**2026-08-29**

Enabling `thinking_level=HIGH` on `gemini-3.7-flash` while leaving
`max_output_tokens=512` made **72 of 95 stories fail**. The model
spent 487 tokens thinking, hit `finish_reason=MAX_TOKENS`, and never
emitted the JSON. It looked like the new model was broken on the task.
It wasn't — the budget was.

The codebase already knew this: the Pro-model branch of `_call_google`
raises the budget to 32768 precisely because "Pro models require
thinking — give enough tokens for thinking + structured JSON output."
The `thinking_level` branch was added without carrying that lesson over.

**Rule:** Whenever you enable or raise model reasoning, raise the output
token budget in the same edit. Thinking and output share one budget.

**Why:** The failure is silent and misattributes cleanly to the wrong
cause — "the new model can't do this task" rather than "we gave it no
room to answer." A 75% failure rate is easy to read as a capability
result and act on.

**How to apply:** On any run with a non-trivial skip/error rate, check
`finish_reason` and `usage_metadata.thoughts_token_count` before
concluding anything about model quality. When adding a new config path
next to an existing one, read what the existing branch compensates for
— it usually encodes a bug someone already paid for.
