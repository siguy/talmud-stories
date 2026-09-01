---
title: Parse the Gittin, Yevamot and Eruvin expert lists to JSON
capability: [detection]
tractate: [gittin, yevamot, eruvin]
blocked_by: []
awaiting: []
finding: docs/findings/2026-09-01-new-tractate-expert-lists.md
superseded_by:
---

# Parse the Gittin, Yevamot and Eruvin expert lists to JSON

**Self-contained. No API calls.** The half `STATUS.md` named as missing: the boundary
builder and the recall harness accept a list that is not the Ketubot `.doc` **only** as
pre-parsed JSON (`--expert-json`, Lesson 28), and none of the three existed.

## Method

Point the table-aware parser at each list, generalising it where it was Kiddushin-shaped:
detect each document's column order from its own header row, resolve multi-label rows by
anchoring against Sefaria, and assert the blindness flags as properties rather than
inferring them from a filename.

## Guardrails

- **Ketubot 149 and Kiddushin 95 may not move**, nor Kiddushin's denominator of 90 — the
  generalisation must change references and nothing else.
- **Never move an unambiguous label.** It is Jeff's statement about where a passage
  belongs; a disagreement with the text is a question for him, not a defect to fix.
- Assert blindness by the `blind` / `counts_for_recall` flags, never by the filename.

## Outcome

**DONE 2026-09-01.** Gittin **112**, Yevamot **102**, Eruvin **74** — all wholly blind, all
in the recall denominator, no appendix and no review remarks in any of the three.
→ `results/expert_lists/{gittin,yevamot,eruvin}_2005.json`

**Eruvin has 74, not the 73 on record.** Its table stores the columns right-to-left, so in
`textutil`'s flattened stream the location cell follows its story — and the document's
first story precedes any location cell at all, so the line-based parser dropped it
silently (`מעשה באדם אחד מבקעת בית חורתן`, Eruvin 11a). The parser now reads column order
off each document's header row instead of assuming it.

References are resolved only where the document is ambiguous (3 Gittin rows moved, marked
`text_anchored`). A single-label reference is never moved: 1 Gittin, 3 Yevamot, 1 Eruvin
and 1 Kiddushin entry disagree with where their own text sits, and each is flagged for
Jeff rather than corrected by us. The same pass **independently validates the existing
Kiddushin list** — re-parsed with anchoring, **0 references move**, and the three
hand-written `REF_OVERRIDES` are replaced by the measurement they encoded.

Guard held: Ketubot 149, Kiddushin 95 / 90 / 89 unmoved; `kiddushin_2005.json` gains two
verification fields and no ground-truth field; Kiddushin recall reproduces at
**93.3 / 95.6 / 97.7** with every measurement field identical. Suite 180 -> 210.

**Unblocks** blind boundary sets and per-daf measurement on all three: **288 blind
stories**, against 239 for Ketubot and Kiddushin combined. Still to do before a run's
results reach Jeff: `jeff:appendix-separate` (Lesson 29) — these lists are clean now.
