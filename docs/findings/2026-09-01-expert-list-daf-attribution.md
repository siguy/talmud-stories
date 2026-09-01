# Per-daf attribution in the expert lists: two silent defects, one much larger than the filed one

**2026-09-01.** Capability: Detection (and every per-daf measurement on a new tractate).
No API calls. Item: [`two-amud-header-parser`](../../work/done/2026-08-30-two-amud-header-parser.md).

## What was filed

`parse_expert_doc` matched only single-amud headers (`סה ע"ב`), so a story Jeff headed
with a two-amud span (`סה ע"ב-סו ע"א`) never reset the current daf and inherited the
**preceding** header. 21 stories across Gittin, Yevamot and Eruvin; 15 such headers in
Ketubot.

## What was actually there

Fixing the span headers and then anchoring **every** entry against Sefaria — asking, for
each story, whether the daf its header names is anywhere in the window its text occupies —
gave this:

| list | entries | header daf is in the text's window | mis-attributed |
|---|---|---|---|
| Gittin | 112 | 107 | **5** |
| Yevamot | 102 | 98 | **4** |
| **Eruvin** | 73 | **20** | **53** |

Eruvin is not a span-header problem. Its table stores the columns **right-to-left**
(`הערות | מקבילות | טקסט | מיקום`), so `textutil`'s flattened stream puts each location
cell *after* the story it labels, and every entry took the **previous row's** daf. The
errors run forward by +1 to +35 amudim. Nothing about the output looks wrong: the parse
returns the right *number* of stories, each labelled with a real, nearby daf.

That is Lesson 28 in a second costume — the converter's output is not the source format —
and Lesson 38's shape, because the failure is quiet. Eruvin detection was one of the three
new-tractate campaigns queued behind this item; it would have been measured per daf
against a list where **71% of the labels were wrong**.

## What changed

- **Two-amud headers are read**, and a story under one is anchored to the daf its own text
  starts on (`ref_source: text_anchored`, with the coverage recorded) — the treatment
  `parse_kiddushin_list.py` already gave its one multi-label row. Which daf a passage sits
  on is an objective fact about the Talmud, not a judgement about what counts as a story,
  so the list stays as blind as it was (FRAMEWORK §3).
- **A story anchored outside its own header's span is kept at the anchored daf and
  flagged**, not silently corrected: the text is the better evidence, and a mistyped
  header in the ground truth should be visible.
- **A reversed-column list is refused**, by name, pointing at `parse_kiddushin_list.py`.
  Refusing rather than warning is the point — a warning on a parse that looks healthy is
  a warning nobody acts on.
- `SPAN_HEADER` now has **one** definition. `fetch_tractate_pages.py` imported a second
  copy to report the defect it could not fix; two patterns could not have stayed honest
  about each other.
- Amud **gimel/dalet** (`יד ע"ד-טו ע"א`, a Yerushalmi four-column form with no Bavli
  equivalent — one Gittin header) maps provisionally onto the daf's second half and is
  then resolved by anchoring, so nothing rests on the guess.

## The regression guard

The fix must move **labels and nothing else**. Re-running Ketubot recall through the
immutable path:

- **RECALL 96.0% · TRIAGE 98.0% · DETECTION 97.9%** — identical to the published figures.
- Every measurement field in `results/recall/ketubot_jeff2005_matches.json`
  (`coverage`, `in_detector`, `survived_triage`, `only_rejected`, `in_golden`,
  `in_mishnah_filtered`, `pages_touched`) is **byte-identical**.
- **11 `ref` labels changed**, the largest by 21 dapim (`Ketubot 28b` → `49b`).
  34 Ketubot entries sit under two-amud headers, more than the 15 headers first counted.
- Entry counts unmoved: **Ketubot 149**, Gittin 112, Yevamot 102 — asserted per list.

This is why the defect survived: `locate()` matches Hebrew 4-grams over the whole corpus
and never reads `ref`, so a corpus-wide recall number is blind to it. Only a **per-daf**
analysis is affected — which is exactly what a new tractate's triage and detection
measurement is.

## What it unblocks, and what it does not

`gittin-detection` and `yevamot-detection` can now be measured per daf. **Eruvin cannot**
until its list is parsed by the table-aware parser — the campaign is not unblocked, it is
correctly blocked, which it was not before.

17 tests in `tests/test_expert_doc_span_headers.py`; suite 170 → 180.
