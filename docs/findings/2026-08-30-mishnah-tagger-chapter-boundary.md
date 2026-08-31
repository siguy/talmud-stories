# The Mishnah tagger read every chapter boundary as a mid-Mishnah page — 2026-08-30

**Why it mattered:** `filter_mishnah_only_stories()` moves stories it believes are
Mishnah-only out of `stories` and into `mishnah_stories`, which **no harness reads** —
not `evaluate_golden.py`, not `measure_recall_vs_expert_list.py`. Anything mis-filtered
there is deleted silently.

**Result:** two stories the golden accepts come back. On the immutable harness,
Ketubot **TP 149 → 151, FN 15 → 13, recall 90.9% → 92.1%, composite 0.9115 → 0.9136**,
with **precision and merge unchanged**. Found while executing `tasks/NEXT/02`; written up
as adjacent defect #2 in `tasks/PLAN_wave6.md`.

Scope note: this fixes the **tagger**. Whether a genuinely Mishnah-only *ma'aseh* should
be filtered at all is the separate open question (adjacent defect #1) and is untouched
here — Ketubot 14b seg 11 and 77a seg 8 are still filtered, exactly as before.

---

## 1. The mechanism

A page may legitimately open mid-Mishnah: the Mishnah began on the previous page and the
`גמ׳` closing it is this page's first marker. `_tag_mishnah_segments()` detected that with
a two-marker vocabulary — `מתני׳` and `גמ׳` — and the fallback
`in_mishnah = (first_marker == 'gemara')`.

At a chapter boundary that vocabulary is blind. Sefaria opens a new chapter's first
Mishnah with the **chapter incipit** in `<big><strong>` — `אַף עַל פִּי` on Ketubot 54b
seg 5 — *instead of* `מַתְנִי׳`. So the tagger found `גְּמָ׳` first, concluded
"mid-Mishnah page", and back-tagged everything before it.

Ketubot 54b, as the old code saw it:

| seg | text | old | new |
|---|---|---|---|
| 0-3 | previous chapter's Gemara tail (R. Yochanan's relatives, segs 1-3) | Mishnah ✗ | Gemara ✓ |
| 4 | `הֲדַרַן עֲלָךְ נַעֲרָה` — the chapter-end formula | Mishnah ✗ | Gemara ✓ |
| 5-6 | `אַף עַל פִּי` — the new chapter's opening Mishnah | Mishnah ✓ | Mishnah ✓ |
| 7+ | `גְּמָ׳` onwards | Gemara ✓ | Gemara ✓ |

Segs 5-6 were right by accident: the rule that back-tagged the Gemara tail also happened
to cover the real Mishnah.

## 2. The marker vocabulary is exactly four kinds — measured, not assumed

Over the 384 fetched Ketubot/Kiddushin pages, every `<big><strong>…</strong></big>` is one
of four things, and **all four occur only inside that markup** (0 bare occurrences of
`גמ׳`, `מתני׳` or `הדרן` anywhere else). The regex catches **141/141** `גמ׳` and
**124/124** `מתני׳` — no missed variants.

| marker | meaning | state |
|---|---|---|
| `מתני׳` | a Mishnah block opens | Mishnah |
| `גמ׳` | the Gemara on it opens | Gemara |
| `הדרן עלך …` | chapter-end formula | Gemara (and the next chapter's Mishnah opens after it) |
| the chapter name | a new chapter's **first** Mishnah | Mishnah |

The fix reads all four, in both the first-marker probe and the walk. A `chapter_end` or
`chapter_start` seen first means the page opened in **Gemara**, not Mishnah. The bare
substring check is kept as a fallback, so any page whose markup differs behaves exactly as
before.

## 3. What changed, corpus-wide

**72 segments on 12 pages** (of 5,443 segments / 384 pages).

- **62 Mishnah → Gemara** on the 7 pages the report identified — Ketubot 54b, 65b, 70a,
  95b, 101b; Kiddushin 41a, 58b. These are previous chapters' Gemara tails.
- **10 Gemara → Mishnah** on 5 more — Ketubot 15b, 41b, 90a, 104b; Kiddushin 69a. These are
  chapter incipits that open a new Mishnah at the *end* of a page, which the old code never
  recognised at all. Each was checked by eye and is unmistakably Mishnaic
  (`האשה שנתארמלה או שנתגרשה…`, `שני דייני גזירות היו בירושלים…`, `עשרה יוחסים עלו מבבל…`).

Every one of the 72 changes is a correction. None is a regression.

## 4. Before / after on `scripts/evaluate_golden.py` (immutable, unmodified)

Two stories stop being filtered: **Ketubot 54b segs 1-3** (`YES`; in the golden *and* in
Jeff's blind 2005 list) and **Ketubot 95b seg 0** (`LOW_CONFIDENCE`;
`דההוא גברא דמישכן ליה פרדיסא`, plain Gemara). Both match golden entries, so both become
true positives.

| | before | after | Δ |
|---|---|---|---|
| TP / FP / FN | 149 / 18 / 15 | **151 / 18 / 13** | +2 / 0 / −2 |
| Precision | 0.8922 | **0.8935** | +0.13 pt |
| Recall (golden, CIRCULAR) | 0.9085 | **0.9207** | +1.22 pt |
| F1 | 0.9003 | **0.9069** | +0.66 pt |
| Boundary mean IoU | 0.9500 | 0.9485 | −0.15 pt |
| Merge F1 | 0.8571 | 0.8571 | 0 |
| **Composite** | **0.9115** | **0.9136** | **+0.21 pt** |

IoU dips because two more stories entered the IoU pool, not because any boundary moved.
The "before" figure reproduces the 90.9% golden recall already recorded in `STATUS.md`.

**Blind recall is unchanged: 96.0% (143/149), the same six misses.** The recall locator's
coarse window already found 54b via a neighbouring detection even while the story itself
was deleted — which is *why this survived*: the only harness that could see the defect was
the one nobody reads for recall.

### Method — no API calls, noise floor zero

The filter and the three post-processors after it (4g-4j) are deterministic. Both arms were
produced by restoring `mishnah_stories` into `stories` on the frozen
`results/v10/wave4_notrim/` output and replaying 4g-4j with the old and new tagger. Per
Lesson 22, a **same-code repeat run was made and is byte-identical** — noise floor is 0,
so the delta is attributable to the code change.

The replay reproduces production exactly on 380 of 383 pages; on 3 (Ketubot 67b, 85a, 111b)
re-applying `snap_start_to_introducer` shifts a start by one segment. That artifact is
present **identically in both arms**, so it cancels. The headline table above avoids it
entirely: it compares the untouched production file against the same file with only the two
un-filtered stories restored — and those two pass through 4h-4j unchanged, so that arm is
exactly what a re-run would produce.

## 5. Forward — the tractates queued next

The same four markers hold on all three newly-fetched tractates, with real chapter names as
incipits (`מבוי`, `המביא גט`, `חמש עשרה נשים`). Had the detector run there on the old code:

| tractate | pages that would have been mis-tagged | segments |
|---|---|---|
| Gittin | 7 | 39 |
| Yevamot | 13 | 86 |
| Eruvin | 0 | 0 |

Eruvin escapes because its chapter breaks happen to fall at page ends, where the old rule
was accidentally right.

## 6. Files

- `src/story_detector_v11.py` — `_segment_structural_marker()` (new) and
  `_tag_mishnah_segments()` (rewritten). **v11 only**; v8/v9/v10 carry the identical old
  function and stay frozen as their ship points.
- `tests/test_mishnah_tagger_chapter_boundary.py` — 6 tests, real Sefaria text. Covers both
  directions: the boundary pages that were wrong, a page that genuinely opens mid-Mishnah
  (Ketubot 42a) so the fix can't be "delete the continuation rule", and a real Mishnah-only
  story that must still be filtered.
- `tests/fixtures/mishnah_tagger_chapter_boundary.json` — 4 real pages, verbatim.

Full suite: **32 passed** (was 26), same 14 pre-existing failures before and after — those
are missing-data and missing-API-key errors in `test_ground_truth.py` /
`test_event_triage.py`, unrelated.
