# Wave 3 Results — Kiddushin fixes (round 2) and Ketubot recall lift

**Session date:** 2026-05-24 / 2026-05-25
**Detector:** `src/story_detector_v9.py` (forked from v8; Stage 2 prompt changes + new text-internal post-processor)
**Plan:** `docs/history/2026-05-24-PLAN-wave3.md`
**Approach:** `docs/history/2026-05-24-wave3-approach.md`

---

## TL;DR for Jeff

Wave 3 makes two real changes and one cosmetic one. On **Ketubot**, the
detector now catches **7 more of your stories** that v7/v8 missed (recall
jumps from 89.2% to 93.7%), with classification F1 up +1.6 points. On
**Kiddushin**, the same prompt changes surfaced **7 additional candidate
stories that v8 had not detected** — including the bathhouse incident on
33a (Rabbi Hiyya / Rabbi Shimon bar Rabbi) that you flagged as missed in
the 2026-04-23 review. Because the current Kiddushin golden was built
from v8's output plus your prior reviews, these new finds register as
"false positives" against that frozen golden even though several look
like real rabbinic stories. We ship and ask you to confirm on the next
review pass — your classifications will determine whether the composite
moves up or down on the next iteration. The third change (text-span
edits to trim halakhic framing inside the first/last segment of a story)
is qualitative only — the review UI now shows the trimmed Hebrew text
inline so you can confirm whether the canonical introducer / trailing
stam marker we identified matches your intended boundary.

---

## What we shipped

### Item 1 — Multi-story-per-page (prompt + iterative Stage 2 fallback)

Stage 2 prompt now includes a "MULTIPLE STORIES PER PAGE" section
instructing the model to detect every distinct story on a page. After
the first Stage 2 pass, a second "find more stories" pass is made with
the already-detected ranges listed, asking only for non-overlapping
additions. Capped at one extra pass per page to bound cost.

Effect on the targeted 71a fixture: the page still returns one story —
the "Babylon dough" segs 2-3 sequence is more debate than narrative and
the model does not promote it. Effect elsewhere: drove several new
candidate detections on Kiddushin (see Lesson-13 framing below) and
contributed to the Ketubot recall lift.

### Item 2 — Embedded-story few-shots (prompt)

Stage 2 prompt now includes an "EMBEDDED STORIES" section with two
worked examples (chosen from Ketubot canonical so no Kiddushin
pages are used as training data per Lesson 2):

- **Baraita-embedded** (`תניא / דתניא + מעשה ב`): Ketubot 111b seg 13.
- **Objection-embedded** (`תא שמע / מיתיבי + narrative`): Ketubot 91a
  segs 19-20.

Effect on the targeted 33a fixture: the bathhouse incident is now
detected at 33a seg 5 (Wave 2 caught only seg 6, the parallel bar
Kappara variant). 81b seg 9 (R. Tarfon "beware me re my daughter-in-law"
baraita-embedded) still missed — the lead-in `אלא תנאי היא. דתניא, אמר
רבי מאיר…` does not match the few-shot pattern closely enough for the
model to promote it without an explicit anchor.

### Item 3 — Sharper not-a-story rules (prompt)

Three abstract rules added to the disqualifier section (per Lesson 8 —
no Kiddushin-specific examples used):

- All-verbal exchanges with no physical action → NOT_A_STORY.
- Biblical-actor-only narratives → NOT_A_STORY (mirrors Wave 2
  biblical-actor filter at prompt time too).
- Fewer than 2 distinct actions or no change/conflict → NOT_A_STORY.

Effect on Kiddushin FPs: didn't reduce them. Some legitimate
narrative incidents the model now finds (and the existing golden
doesn't cover) outweigh any tightening this rule produced.

### Item 4 — Text-internal boundary post-processor (NEW Stage 4 step)

`edit_text_internal_boundaries` runs at Stage 4 after the biblical-actor
filter. For each real story:

- Search the FIRST segment for the EARLIEST canonical Hebrew introducer
  (`מעשה ב`, `כי הא ד`, `הנהו בי תרי`, `ההוא ד / גברא`, `ההיא`,
  `כדתניא`, `תניא`) at a word boundary. If found at offset > 0, record
  `text_span_start = {segment: i, char_offset: N, introducer: str}`.
- Search the LAST segment for the LATEST canonical trailing-stam marker
  (`שמע מינה`, `מאי טעמא`, `אי הכי`, `הכי קאמר`, `שאני`, `תא שמע`,
  `איתיביה / מיתיבי`, `אלא`, `ואי`, `מתקיף`, `תניא נמי הכי`,
  `תנו רבנן`) at a full word boundary. If found, record `text_span_end =
  {segment: j, char_offset: M, marker: str}`.

Char offsets are in the ORIGINAL (with-nikud) Hebrew text. The score
harness reads only `start_segment` / `end_segment`, so these fields are
**score-neutral by design** — the change is qualitative review-debt
repayment for the Lesson-12 text-internal feedback.

**Audit on Jeff's 17 flagged text-internal cases: 10/17 land cleanly**
(passes the ≥10 plan gate). The 7 misses are either non-canonical
introducers (e.g. "רבי יוחנן הוה קאי" on 33a), Jeff-specified end phrases
that don't start with a canonical stam marker (52b, 72a×2, 32b_2), or a
false-friend ("שאני" matched inside a story-internal word on 26b_10).

The validation UI generator (`validation/generators/generate_kiddushin_review_ui.py`)
now renders the trimmed prefix/tail with strikethrough and the kept
slice highlighted in green when `text_span_*` is present.

---

## How we know it worked (gate table)

Today's regenerated Wave 2 numbers are the gate per Lesson 11. Both
matched the frozen wave2_results.md exactly (apply_wave2 is pure Python).

| | Kiddushin |   | Ketubot |   |
|--|--|--|--|--|
| | Wave 2 (today) | Wave 3 | Wave 2 (today) | Wave 3 |
| Classification F1 | 0.9257 | 0.9000 (−0.026) | 0.8952 | **0.9108 (+0.016)** |
| &nbsp;&nbsp;Precision | 0.9000 | 0.8526 | 0.8981 | 0.8862 |
| &nbsp;&nbsp;Recall    | 0.9529 | 0.9529 | 0.8924 | **0.9367 (+0.044)** |
| &nbsp;&nbsp;FP count  | 9 | 14 | 16 | 19 |
| &nbsp;&nbsp;FN count  | 4 | 4 | 17 | **10 (−7)** |
| Boundary IoU | 0.9815 | 0.9815 | 0.9563 | 0.9531 |
| Merge F1 | 0.6667 | 0.6667 | 0.8780 | 0.8571 |
| **Composite** | **0.8962** | **0.8859** | **0.9162** | **0.9170 (+0.0008)** |

Gate result: Ketubot ✓ (+0.0008), Kiddushin ✗ (−0.0103). Item 4 audit ✓
(10/17). Items 1/2/3 fixtures: item 2a ✓ (33a), item 1 ✗ (71a still 1),
item 2b ✗ (81b seg 9), item 3 ✗ (FPs went up not down).

### Why we shipped despite the Kiddushin gate failure (Lesson 13)

Inspection of all 7 new Kiddushin FPs shows:

| Ref | v9 detection | Status |
|---|---|---|
| 12b seg 8 | "Rav Sheshet flogged a man at the mother-in-law's door" | Real narrative incident |
| 20a seg 12-14 | "Abaye boasts to Ben Azzai in the market" | Borderline (talk-heavy) |
| 33a seg 5 | "Rabbi Hiyya in bathhouse, Rabbi Shimon bar Rabbi passes" | **Jeff explicitly flagged this as missed on 2026-04-23** |
| 39a seg 1 | "Levi asks Shmuel for uncertain-orla produce" | Real incident |
| 51a seg 11 | "Man uses Sabbatical figs to betroth five women" | Real incident |
| 52a seg 4 | parallel betrothal narrative | Real incident |
| 69b seg 8-9 | "Ezra addresses returning priests" | Biblical actor — borderline |

The score gate measures agreement with the current golden, which was
built from v7 outputs + Jeff's prior reviews. v9 found stories v7
hadn't surfaced, so they aren't in the golden — they score as FPs
even when they're real. Per Lesson 13, the right move is ship + flag
for expert review, not disable the improvement to hit a tenth of a
percent of golden agreement on a frozen target.

Ketubot tells the same story from the other side: the new prompt
recovered 7 stories the golden DOES have, so the recall lift translates
to a real composite gain.

---

## What's deferred to Wave 4+

- **71a multi-story under-recall.** Iterative Stage 2 plus the prompt
  change still returns one story. The "Babylon dough" segs 2-3 sequence
  is more academy debate than narrative incident; getting the model to
  promote it likely needs either a fine-tuned scorer or an explicit
  baraita-embedded few-shot for the `בימי רבי בקשו לעשות בבל עיסה` style.
- **81b seg 9 baraita-embedded miss.** Lead-in `אלא תנאי היא. דתניא, אמר
  רבי מאיר... אמר רבי טרפון: הזהרו בי` requires recognition that the second
  rabbi's statement opens a narrative (mocking student, etc.). Item 2's
  few-shot is structurally too similar to Ketubot 111b (clear `מעשה ב`
  after `תניא`) to generalize here.
- **Item 4 misses (7/17 Jeff cases).** Pattern-by-pattern in
  `scripts/audit_wave3_item4.py`. Mostly require either non-canonical
  introducers or text patterns outside the stam-marker list.
- **FP count target (Item 3, ≤4) not met.** The "sharper rules"
  prompt addition didn't help on the metric. The added FPs came from
  the multi-story / embedded recall lift, not from item 3 being too lax.
  Real reduction probably needs the post-processing classifier path
  (Lesson 7) rather than more prompt rules.

---

## Methodology notes

### Why we didn't bisect to "save" the Kiddushin gate

Plan 3d.6 says: "If Ketubot regresses: bisect by disabling items 3c →
3b → 3a". Ketubot did NOT regress. The Kiddushin regression is
unexpected per plan; per Lesson 13 it is a signal that v9 is finding
new stories rather than misclassifying existing ones. Disabling item 1
(iterative Stage 2 — likely cause of the new candidates) would also
risk part of the Ketubot recall lift, which is the headline win of the
wave.

### How item 4 stays score-neutral

The `text_span_*` fields live alongside `start_segment` / `end_segment`,
not in place of them. `scripts/evaluate_golden.py` reads only segment
indices for IoU. Verified by scoring `results/v9/wave3_item4/*.json`
against the canonical goldens — composites bit-identical with vs without
item 4 on both tractates.

### Item 1 cost: iterative Stage 2

Stage 2 is now called up to twice per page: once for initial detection,
and once with the already-detected ranges listed asking only for
additions. Skipped on pages where the first pass found zero stories.
Net ~1.5x LLM cost over Wave 2.

### Few-shot source for item 2 (Lesson 2 compliance)

Both few-shots come from Ketubot canonical (`results/canonical/ketubot_canonical.json`):
Ketubot 111b 13-13 and Ketubot 91a 19-20. Neither overlaps Kiddushin
content, so the Kiddushin eval is not contaminated.

---

## Files

**New:**
- `src/story_detector_v9.py` — forked from v8 with prompt changes + item 4
- `scripts/run_wave3.py` — parameterized runner (tractate + range + --refs)
- `scripts/apply_wave3_item4.py` — score-neutrality fast path
- `scripts/audit_wave3_item4.py` — 17-case audit (`AUDIT_INPUT` env override)
- `scripts/verify_wave3.py` — per-item pass/fail
- `scripts/compare_v8_v9.py` — side-by-side metrics
- `results/v9/wave3/{kiddushin_v9,ketubot_v9_2-60,ketubot_v9_61-112}.json`
- `results/v9/wave3_item4/*.json` — score-neutrality artifact
- `docs/golden/v8/baselines/{kiddushin,ketubot}_wave2_baseline_today.json`
- `docs/findings/2026-05-25-wave3-results.md` — this file

**Modified:**
- `validation/generators/generate_kiddushin_review_ui.py` — renders `text_span_*`
- `lessons/` — Lesson 14 added
- `tasks/todo.md` — Wave 3 items checked off
- `CLAUDE.md` — Key Files table updated
- `docs/technical/VERSION_HISTORY.md` — Wave 3 row
- `docs/technical/HOW_IT_WORKS.md` — Wave 3 changes documented
