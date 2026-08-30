# NEXT 09 — The judgment calls left open by the Kiddushin parse

**`NEXT/05` is done.** These are the decisions taken under uncertainty while building
[`results/expert_lists/kiddushin_2005.json`](../../results/expert_lists/kiddushin_2005.json),
recorded so they are revisited rather than inherited. Read
[the finding](../../docs/golden/v11/kiddushin_list_parse_2026-08-30.md) first.
**Capability: ground truth for 1, 2, 4.** **No API calls except item 2.**

Each is stated as: what was decided · what it rests on · what it costs if wrong · what
would settle it. None of them blocks `06`, `07` or `08` — but **item 1 changes the
headline number `06` produces**, so read it before quoting that number anywhere.

---

## 1. Were the five expert-flagged stories in Jeff's 2005 original? — **the big one**

**Decided:** kept `blind: true`, and emitted **two** denominators (89 and 94) rather
than picking one.

**Rests on:** he marked the one thing he did add (`הוספתי--י.ר.`), none of these five
carries a marker, and two of them (33a, 53a) sit in rows with parallels annotations that
look like 2005 scholarly work. **Indicated, not measured.**

**Costs if wrong:** about **5 points of Kiddushin detection recall** — the headline of
`NEXT/06`. On 94 the five count as misses; on 89 they are excluded. The true value is
one of the two numbers, not between them.

**Settles it:** one sentence to Jeff. *"The five Kiddushin stories you flagged in April
as ones we'd missed — were those already in your own list, or did you add them after
seeing our output?"* Nothing else can answer it; there is no earlier copy of the
Kiddushin document on disk. **Add to the next email** (STATUS "Waiting on Jeff").

## 2. Four references resolved from outside the document

**Decided:** the row labelled `מה ע"א` / `מה ע"ב` / `מו ע"ב` holds four stories, and the
document cannot say which belongs to which — paragraph-index alignment across cells gets
2 of 4 right, because a long story occupies many visual lines and a label occupies one.
Resolved by aligning each story's text and reading off the daf; marked
`ref_source: text_anchored`, and `REF_OVERRIDES` in the parser is the audit trail.

**Rests on:** 4-gram alignment at ≥0.92 coverage against the Hebrew segments in
`results/v9/wave3/kiddushin_v9.json` — **our own detector's Sefaria cache**. The segment
text is Sefaria's, not ours, so this is not circular in substance; but the check was run
through our artifact and should not stay that way.

**Costs if wrong:** triage-recall attribution in `NEXT/06` — which *page* a story sits
on. Detection recall is unaffected, since that matches by text, not by reference.

**Settles it:** re-verify the four against Sefaria directly (or a printed edition) rather
than via the cache. Ten minutes. Result → the finding doc, §7.

## 3. Is the `הוספתי--י.ר.` entry a new story, or a boundary correction?

**Decided:** `blind: false` and `duplicate_of` set — which is correct under either
reading, so nothing downstream is at risk.

**Rests on:** it is a *shorter* form of an entry he already had, cut before the
`אמר אביי` scriptural coda, and his other 2026 comments on this document are boundary
corrections.

**Costs if wrong:** nothing breaks, but value is left unclaimed — if it is a correction,
it is a boundary target Jeff stated **by example rather than in words**, and the
corrections ruler is the smaller of the two Kiddushin rulers.

**Settles it:** `NEXT/08` step 6. Confirm before using it as a target.

## 4. A `מו ע"ב` (46b) label with no story beside it

**Decided:** left as-is; it produces no entry.

**Costs if wrong:** the ground truth may be **missing a story**, which would make the
denominator 95 rather than 94 and turn an unrecorded passage into a silent non-miss.
This is the one item here that could make the list *incomplete* rather than merely
imprecise.

**Settles it:** look at what sits at Kiddushin 46b and whether it reads as a story; if it
does, ask Jeff whether he meant to add it. `NEXT/08` step 6.

## 5. The 8-word cutoff, when this parser meets a new tractate

**Decided:** `MIN_STORY_WORDS = 8` separates stories from labels and stray fragments.

**Rests on:** a check that neither document contains a story paragraph of 3–7 words —
**true for Kiddushin and Ketubot, unverified anywhere else.**

**Costs if wrong:** silently dropped stories, in the denominator, with no error. The same
failure shape as Lesson 25.

**Settles it:** before running this parser on Gittin, Yevamot or Eruvin, print the 3–7
word paragraphs in the text column and confirm the bucket is empty. If it is not, the
cutoff needs a better rule than word count.

---

## How you know it worked

Items 1 and 4 answered (both need Jeff or the text, not code), 2 re-verified
independently, 3 and 5 checked at the point they are used. Update the finding doc in
place for 2; anything that changes a count also updates `STATUS.md` and the artifact.

## Guardrails

- Item 1 is a **question, not a task.** Do not resolve it by argument — the honest
  output until he answers is the pair 89/94, and any number quoted from this list says
  which denominator it used (FRAMEWORK §3).
- Label every outcome measured / indicated / suspected.
