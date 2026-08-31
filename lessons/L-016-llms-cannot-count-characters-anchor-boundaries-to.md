# Lesson 16 — LLMs cannot count characters; anchor boundaries to real text units

**2026-08-28**

Wave 4 followed Lesson 15's advice — "emit the slice from the LLM
with an explicit text_span_start/text_span_end schema" — but
implemented it as **character offsets**. Jeff's 2026-07-06 review
(`validation/feedback/jeff_2026-07-06_feedback_ledger.md`) proved it
broken: 8 of 15 reviewed Kiddushin stories were mis-trimmed, one
(30a seg 7) cut in the middle of a word, inside a Biblical quotation.

Verified root cause: the nikud-stripping position map is faithful
(`stripped[i] == hebrew[map[i]]` for every i in
`src/story_detector_v10.py`), so the wrong cuts come from the model's
raw offset numbers, not the mapping. LLMs reproduce text reliably but
**do not count characters reliably**.

**Rule:** Never ask an LLM for a character offset / index into text.
When you need a sub-segment boundary, have the model **select a real
text unit** (a punctuation-delimited clause) or **quote the boundary
words verbatim**, then locate that unit deterministically. Sefaria's
Davidson text is fully punctuated and its English is aligned and
already-correct — use those units.

**Why:** Character counting is a known LLM weakness; text
reproduction is a known strength. The whole point of Lesson 15 (let
the model judge meaning) was right — the failure was the numeric
*interface*, not the idea of LLM emission.

**How to apply:** See `docs/history/2026-08-28-PLAN-wave5.md` — clause-index selection
anchored to punctuation, with a verbatim-quote fallback, plus an
assertion that every emitted boundary sits at a clause/word boundary
(a mid-word cut becomes a build error, not a silent corruption).
