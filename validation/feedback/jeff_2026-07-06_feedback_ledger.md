# Jeff Rubenstein — Complete Feedback Ledger, 2026-07-06

**Purpose:** Single durable record of *everything* Jeff said in his 2026-07-06
reply, so nothing is processed partially and then lost on a context clear.
Every item has a status. This ledger is the source of truth for what still
needs doing — check it before replying to Jeff or shipping any change.

**Why this file exists:** We have a documented, repeated failure of dropping
Jeff's feedback (see [lessons/](../../lessons/README.md) Lesson 1 and
Lesson 16/17 added this session; and memory `feedback_boundary_corrections.md`:
"we systematically ignored boundary/merge feedback from Jeff; never split
feedback processing again"). This ledger is the mechanism that stops it.

> ## STATUS UPDATE 2026-08-28 — audit, revert, and the first real recall number
>
> Three things changed since this ledger was written. Where they conflict with
> text below, **these win.**
>
> 1. **Cause A is ~10x larger than recorded here.** A full audit of every emitted
>    cut (not just Jeff's 15 reviewed stories) found **104 of 189 cuts (55%) sever
>    a Hebrew word**, across all three v10 outputs — ~100 of them in the two
>    Ketubot files nobody has reviewed. Of the 9 reviewed stories that were
>    actually trimmed, **9 of 9 were marked incorrect**. The mechanism has zero
>    observed successes.
>    → [`docs/findings/2026-08-28-wave4-span-failure-audit.md`](../../docs/findings/2026-08-28-wave4-span-failure-audit.md)
> 2. **The spans are reverted, shipped, and verified.** `results/v10/wave4_notrim/`
>    restores segment-level boundaries. Composite unchanged (0.9171 → 0.9171,
>    proven by running the harness both ways); zero mid-word cuts remain.
>    Wave 5 is therefore **no longer urgent** — nothing corrupt is live.
> 3. **True recall is measured for the first time: 96% on Ketubot.** Jeff's
>    Ketubot list (`jeff comms/b.ketubot (1).doc`, created 2005) is a genuinely
>    detector-blind ground truth. 143/149 of his stories are found by v10.
>    The six misses cluster into the categories Jeff's own criteria predict.
>    → [`docs/findings/2026-08-28-recall-measurement-ketubot.md`](../../docs/findings/2026-08-28-recall-measurement-ketubot.md)
>
> **Consequence for sequencing:** the misses are Wave 6 (criteria) territory, not
> Wave 5 (boundaries) territory. Wave 6 is now first. See
> [`tasks/PLAN_wave6.md`](../../tasks/PLAN_wave6.md).

## Source files (everything this ledger is built from)

- Jeff's returned Wave 4 review (15 of 95 stories verdicted):
  [`jeff comms/wave4_kiddushin_review_2026-07-06.json`](../../jeff%20comms/wave4_kiddushin_review_2026-07-06.json)
- Jeff's Part 2 strategic answers (Word doc):
  [`jeff comms/Simon Brief Questions.docx`](../../jeff%20comms/Simon%20Brief%20Questions.docx)
- The email he was replying to:
  [`comms/sent/2026-07-06-email-jeff-wave4-and-roadmap.md`](../../comms/sent/2026-07-06-email-jeff-wave4-and-roadmap.md)
- Wave 4 detector output he reviewed:
  [`results/v10/wave4/kiddushin_v10.json`](../../results/v10/wave4/kiddushin_v10.json)
- Review UI he used:
  [`validation/ui/wave4_kiddushin_review.html`](../ui/wave4_kiddushin_review.html)
- Detector that produced the spans:
  [`src/story_detector_v10.py`](../../src/story_detector_v10.py) (`extract_text_spans_via_llm`)
- Cached Sefaria source text (basis for the fix):
  [`results/v7/kiddushin_pages.json`](../../results/v7/kiddushin_pages.json)

---

## PART 1 — Story review (15 of 95 verdicted: 4 correct, 11 incorrect)

**Headline:** Wave 4 passed 14/14 on Jeff's hand-picked fixture but fails
**11 of 15** on fresh stories. This is Lesson 9 live and the reason we now
distrust fixture metrics. Failures split into two root causes:

### Cause A — LLM character-offset text-spans are unreliable (8 cases) → the v11 fix

Root cause verified this session: the Wave 4 mechanism asks Gemini for a
*character offset*; the nikud-mapping is provably faithful, so the wrong cuts
come from the model's raw offset numbers. LLMs quote text well but count
characters badly. Fix = anchor boundaries to Sefaria punctuation/clauses, not
characters (see [tasks/PLAN_wave5.md](../../tasks/PLAN_wave5.md)).

| Ref | Category | Jeff's note (verbatim intent) | Status |
|---|---|---|---|
| Kiddushin 9a seg 2 | different_trim | Story cut off; must include `מִיקַּדְּשַׁתְּ לִי״? … לָאו כְּלוּם הוּא`; English right, Hebrew doesn't match | OPEN → v11 |
| Kiddushin 12b seg 4 | different_trim | Continue 3 more words: `וּפְרַשׁוּ רַבָּנַן מִינַּהּ` is part of story; else too brief | OPEN → v11 |
| Kiddushin 12b seg 8 | new_trim | Story is `הָהוּא חַתְנָא … וְנַגְּדֵיהּ רַב שֵׁשֶׁת!` — trim boundaries wrong | OPEN → v11 |
| Kiddushin 12b seg 10 | new_trim | Story is `הָהוּא גַּבְרָא דְּקַדֵּישׁ … שְׁקַלְתַּהּ וְאִישְׁתִּיקָא.` — end cut too early | OPEN → v11 |
| Kiddushin 13a seg 3 | different_trim | Continues: `לַהּ: אִי יָהֵיבְנָא לִיךְ … שְׁקַלְתֵּיהּ וְאִישְׁתִּיקָה` | OPEN → v11 |
| Kiddushin 22b seg 18 | new_trim | **Nothing should have been trimmed** — all of seg 18 is the story | OPEN → v11 |
| Kiddushin 25a seg 3 | new_trim | Crossed-out words `לֵיהּ: מַתְנִיתָא בְּעוֹ מִינָּךְ. דִּתְנַן…` are part of story; else ends at `אֲמַר` | OPEN → v11 |
| Kiddushin 30a seg 7 | new_trim | **Cuts mid-word.** Must include `…ךָ בְּחֹרֵב״? מִכָּאן וְאֵילָךְ … לְיָנוֹקָא וּמוֹסְפֵיהּ` | OPEN → v11 |

### Cause B — Pre-existing segment-level / cross-page issues, not text-spans (3 cases)

These are older, separate problems the char-offset work did not touch. They
must NOT be folded into the v11 text-span fix — they need segment-boundary and
cross-page-merge work.

| Ref | Category | Jeff's note | Status |
|---|---|---|---|
| Kiddushin 8a seg 9-10 | different_trim | First words `כֹּהֵן עִילָּוֵיהּ` not part of story; Rav Ashi statement (seg 10) not part of story; should start `כִּי הָא דְּמָר בַּר רַב אָשֵׁי`. (This is the segment-level case already deferred pre-Wave-4.) | OPEN → segment-boundary pass |
| Kiddushin 8b seg 14 | both_full | English right but Hebrew cut off; continues to seg 0 of next page (9a) | **CLOSED 2026-08-30 — display bug, not a merge defect.** The detector had already merged this correctly (`spans_pages: [8b, 9a]`); the UI rendered an English-only continuation block. Fixed in `tasks/NEXT/04`. |
| Kiddushin 20a seg 12-14 | both_full | Seg 14 is the end of the baraita, not the story; story ends `עִמְּךָ בַּמַּאֲכָל וְעִמְּךָ בַּמִּשְׁתֶּה`. Also flags this as **very low confidence** as a story | OPEN → segment-boundary + classification |

### Correct verdicts (4) — with one structural note

| Ref | Verdict | Note |
|---|---|---|
| Kiddushin 7b seg 9-10 | correct | — |
| Kiddushin 8b seg 2 | correct | — |
| Kiddushin 12b seg 5 | correct | — |
| Kiddushin 12a seg 13-15 | correct | **But**: repeats much of `12a seg 13-13`, and contains **two** stories, each beginning `הָהוּא גַּבְרָא` (secs 13 and 14) → duplicate + multi-story-splitting issue. Status: OPEN → merge/dedup + multi-story |

---

## PART 2 — Strategic answers (these reshape the roadmap)

### (a) Measuring what the detector misses → Jeff already has independent lists

Jeff and a colleague, ~20 years ago, went tractate-by-tractate listing **all
stories in the Talmud** (before abandoning the effort). That IS the
detector-blind independent read we proposed. It's how he found the Kiddushin
45a/53a/71a misses. His lists are imperfect and cover only some masekhtot, and
**the AI has found stories his lists missed** (he cites this as proof of the
project's value).

- **Decision:** Drop the "have Jeff cold-read 10 random pages" proposal. Instead
  **obtain Jeff's existing lists** and use them as independent ground truth to
  finally measure true recall (fixes the circular-recall problem in
  [docs/findings/2026-07-06-approach-review-and-scaling.md](../../docs/findings/2026-07-06-approach-review-and-scaling.md) §3.1).
- **Action (OPEN):** Ask Jeff for the full lists + which tractates they cover.
- **CORRECTION 2026-08-28 — the Kiddushin docx is NOT a recall probe.**
  [`validation/feedback/Kiddushin missesd stories.docx`](Kiddushin%20missesd%20stories.docx)
  contains exactly **5 entries** (33a, 45a, 53a, 71a, 81b) — which are precisely
  the 5 already listed in `known_missing_stories` in
  `results/canonical/kiddushin_canonical.json`, two of them already recovered in
  Wave 1. It is a 5-item regression checklist, not ground truth, and cannot
  produce a recall *rate*. The earlier claim here overstated it.
- **THE REAL ASSET (2026-08-28):** `jeff comms/b.ketubot (1).doc` — Jeff's
  **Ketubot** list, created 2005-02-02, 149 stories across 55 dapim, with
  מקבילות (parallels) and הערות (notes) columns already populated. Genuinely
  detector-blind. Measured: **v10 finds 143/149 = 96.0%.**
  → [`docs/findings/2026-08-28-recall-measurement-ketubot.md`](../../docs/findings/2026-08-28-recall-measurement-ketubot.md)
  Note he has therefore already designed the DB schema he asked for in (d).

### (b) Ein Yaakov as answer key → weaker than I claimed; Jeff is right

Two limits I under-weighted: (1) Ein Yaakov is *all* aggada, so it would need
filtering and a human judgment on every gap; (2) **the database includes
halakhic stories, which Ein Yaakov omits** — so it structurally cannot catch
those. Jeff: fine as a cheap partial cross-check on aggadic material, low value
overall; his own lists are better.

- **Decision:** Demote Ein Yaakov from "primary corpus-wide recall probe" to
  "cheap optional aggadic-only cross-check." Correct the roadmap doc
  [docs/findings/2026-07-06-approach-review-and-scaling.md](../../docs/findings/2026-07-06-approach-review-and-scaling.md) §4.2 accordingly.
- **Scope fact to propagate everywhere:** the target is **all stories incl.
  halakhic**, not just aggadic.

### (c) The story-definition criterion → captured as a rubric

Jeff gave the sharp rule the detector has been missing. Extracted in full to
[docs/findings/2026-07-06-jeff-story-definition-criteria.md](../../docs/findings/2026-07-06-jeff-story-definition-criteria.md).
Summary:
- **Hypothetical → not a story; actually-happened → story** (even if fictional).
  Legal cases are theoretical ("*if* I steal a cow…") even with action; a legal
  case built on a real event ("A man stole a cow. Rava ruled…") *can* be a story.
- **Speech-acts alone don't count** — needs some action beyond the speech;
  borderline "jumped up and stated" cases → explicit criteria or mark borderline.
- **Emotional reactions ("was embarrassed") do count** as events.
- **Action (OPEN):** encode into detector criteria (v11 Stage 2 prompt) + build a
  criteria-conformance test set.

### (d) Distributed validation → Jeff wants crowd-sourcing, not a fixed panel

His preferred model: a **Google-Doc-style shared interface** with all tractates
from our final run; any scholar can flag "not a story / remove," mark
borderline, or suggest additions; done gradually as people encounter stories;
he (or a small editor group) checks before finalizing. **Output keeps contested
/ borderline cases, flagged as such.** He can recruit a few colleagues to seed
some tractates and cross-check with his old lists. He wants **three extra
per-story columns: notes, references to scholarship, Yerushalmi parallels.**

- **Decision:** Re-spec the end-product from "static published corpus" to a
  **living, crowd-sourced, editable database** with borderline flags + the three
  columns. Update roadmap §5.2 / §5.4.
- **Action (OPEN):** design the crowd-source interface + schema (must include:
  per-story verdict field, borderline flag, notes, scholarship refs, Yerushalmi
  parallels).

---

## OPEN ITEMS TRACKER (nothing here is done until checked off)

- [x] **Cause A contained** — spans reverted to segment-level (`results/v10/wave4_notrim/`), score-neutral, 0 mid-word cuts. Gate: `scripts/audit_text_spans.py --strict`.
- [ ] **v11 clause-anchored spans** (Wave 5) — DEPRIORITIZED behind Wave 6; nothing corrupt is live. Plan: [tasks/PLAN_wave5.md](../../tasks/PLAN_wave5.md)
- [x] **Fix the review UI Hebrew/English asymmetry** (2026-08-30, `tasks/NEXT/04`) — there were **two** asymmetries, not one. (1) The Hebrew was cut at the LLM char-offsets while the English showed full segments. (2) Cross-page stories rendered an *English-only* continuation block, so the Hebrew appeared to stop at the page break — **35 stories** across the three outputs, and the direct cause of the `8b seg 14` note in Cause B below, which is therefore a display bug and **not** a cross-page-merge defect. Both fixed by rendering each segment as one row carrying both languages; the story is now **highlighted inside the full text**, never trimmed to. Verified in a browser over all 262 stories (0 truncations, 0 strikethrough, 35/35 bilingual continuations) and on all 9 of Jeff's flagged cases. Guard: `tests/test_review_ui_symmetry.py`.
- [ ] **Segment-boundary + cross-page pass** (Cause B: 8a, 8b_14, 20a) — separate from v11
- [ ] **Multi-story / dedup** (12a_13-15 two `הָהוּא גַּבְרָא` stories + repeat)
- [ ] **Encode Jeff's (c) criteria — WAVE 6, now the FIRST wave, ahead of Wave 5** ([tasks/PLAN_wave6.md](../../tasks/PLAN_wave6.md)); the 6 recall misses seed its conformance set (Stage 2 rewrite around hypothetical-vs-actual + conformance test set + golden re-check against the rubric). Deliberately NOT in Wave 5 — different axis (classification, not boundary). Do not let it slip to "never" (Lesson 17).
- [x] **Ketubot list obtained and used** — `jeff comms/b.ketubot (1).doc`; recall measured at 96.0%
- [ ] **Ask Jeff which OTHER tractates he has lists for** — highest-value, lowest-cost ask; a Kiddushin list gives a generalization estimate on a less-tuned tractate
- [ ] **Add the 5 expert-list stories missing from the Ketubot golden** (20a, 53a, 67b, 72b, 82b), flagged with expert-list provenance
- [ ] **Investigate Ketubot 77a** — present in golden, missed by the v10 detector (a false negative against our own labels)
- [ ] **Demote Ein Yaakov** to optional aggadic cross-check; propagate "incl. halakhic stories" scope
- [ ] **Design crowd-sourced editable DB** (borderline flags + notes/scholarship/Yerushalmi columns)
- [ ] **Reply to Jeff** — only after the above are digested; thank him, confirm the offset diagnosis, share the v11 direction, respond to Part 2 (lists, crowd-sourcing, criteria)
- [ ] **Update roadmap** [docs/findings/2026-07-06-approach-review-and-scaling.md](../../docs/findings/2026-07-06-approach-review-and-scaling.md) §3.1/§4.2/§5.2/§5.4 per (a),(b),(d)
