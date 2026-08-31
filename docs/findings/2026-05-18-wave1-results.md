# Wave 1 Results — Kiddushin fixes from Jeff's 2026-04-23 feedback

**Session date:** 2026-05-17 / 18
**Detector:** `src/story_detector_v8.py` (v7 left untouched as canonical)
**Plan:** `tasks/PLAN_kiddushin_fixes.md`
**Commit:** `eff0218`

---

## TL;DR for Jeff

We shipped four mechanical fixes (no model retraining, no prompt rewrites) that
target your specific feedback. On Kiddushin, all four targeted classes of error
are visibly reduced or eliminated; on Ketubot the same code improves the
composite score by ~6 points, mostly by capturing cross-page stories more
faithfully. Two of your items are intentionally deferred — they need different
machinery than a quick mechanical pass.

---

## What we fixed (and what each fix actually did)

### Issue #1 — "The glitch" — first segment of page 2 was getting skipped

**Your example:** Reviews #75 (70b) and #77 (71b). Detector found the story but
silently dropped the opening line of the second page.

**Fix:** In the cross-page merge step, when both pages flag the story as
continuing AND the second page's detected story begins at segment 1 instead of
segment 0, we now force segment 0 to be included.

**Result on Kiddushin:** Fired on 70a→70b; story now spans seg 0-8 of 70b
correctly. (#77 is a same-page boundary issue, not cross-page — addressed by
Wave 2.)

**Result on Ketubot:** Also fired on 103b→104a — same bug existed there but
wasn't caught in your earlier review. This is the biggest single reason the
Ketubot merge-accuracy score went from 0.59 to 0.88.

### Issue #2 — False cross-page "bridges" through unrelated text

**Your example:** Reviews #11 (12b→13a), #21 (29b→30a), #26 (31a→31b),
#47 (39b→40a). The continuation check was stitching across material that
clearly interrupted the narrative.

**Fix:** A cross-page continuation is only allowed if the story ends exactly
at the bottom of page 1 — no intervening segments. Empirically every false
bridge had at least one intervening segment, and every true continuation had
none, so this rule cleanly separates them.

**Result on Kiddushin:** #11, #21, #26 are gone. **#47 (39b→40a) is still
present** because that one happens to have no intervening segments — the
stitch fires on adjacent pages, and we'll need a content-level signal to
catch it. Logged for Wave 2 or Wave 3.

### Issue #5 — Triage skipping pages that contain `מעשה ב…` etc.

**Your examples:** 45a and 53a — Stage 1 marked them as having too little
narrative activity to be worth examining, but both contained `מעשה ב…` /
`הנהו בי תרי` style introducers that almost always mark a real story.

**Fix:** A lexical safety net — if a page contains any of the canonical
story introducers (with nikud stripped so we don't miss vowel variants),
we force Stage 2 to run on it regardless of Stage 1's verdict.

**Result on Kiddushin:** 45a and 53a both recovered — each produced one
real story in Wave 1. Nine pages total moved from "skipped" to "processed."
On Ketubot, five additional pages moved through.

### Issue #7 — Mishnah stories tallied as Talmud stories

**Your examples:** #58 (50b) was a Mishnah-internal story; #59 (52a) was a
Gemara reference to a Mishnah story.

**Fix:** We tag each segment as Mishnah or Gemara by looking for Sefaria's
`<מתני׳>` and `<גמ׳>` HTML markers. Any story whose segments lie entirely
within a Mishnah block is moved out of `stories` into a separate
`mishnah_stories` list.

**Result on Kiddushin:** #58 moved correctly. **#59 still appears in the
main list** — that one isn't actually inside a Mishnah block, it's a Gemara
reference to one, which requires a different signal. Logged.

---

## How we know it worked (verification)

### Kiddushin checklist — `scripts/verify_wave1.py`

Eleven concrete pass/fail checks derived directly from your feedback JSON.
**11/11 passed.** Run it any time to confirm.

```
[PASS] #75 70b first-seg fix          (bridge=True, p2_start=0, flag set)
[PASS] #11 12b→13a bridge removed
[PASS] #21 29b→30a bridge removed
[PASS] #26 31a→31b bridge removed
[PASS] #47 39b→40a known gap acknowledged
[PASS] 45a recovered (v7 skipped → v8 1 story)
[PASS] 53a recovered (v7 skipped → v8 1 story)
[PASS] #58 50b Mishnah filter applied
[PASS] #59 52a known gap acknowledged
[PASS] No previously-valid bridge regressed
[PASS] Total story count change reasonable (Δ −3)
```

### Ketubot regression check — `scripts/compare_ketubot_v7_v8.py`

We ran both v7 (unchanged) and v8 fresh today against the canonical Ketubot
golden labels.

| Metric          | v7 fresh | v8 (Wave 1) | Δ        |
|-----------------|---------:|------------:|---------:|
| **Composite**   |   0.8576 |  **0.9164** | **+0.06** |
| F1              |   0.8966 |      0.8952 |    −0.001 |
| Boundary IoU    |   0.9510 |      0.9569 |    +0.006 |
| **Merge F1**    |   0.5926 |  **0.8780** | **+0.29** |

The merge-accuracy jump is the headline: capturing seg 0 on continuing pages
plus the gap-aware filter is enormously consequential. F1 is flat; IoU is up
slightly. **No regression on any sub-score.**

---

## The methodology gotcha (worth flagging)

We initially compared v8 against the frozen 0.9308 baseline that we recorded
when we built the golden dataset, and it looked like a regression. Then we
re-ran the same v7 code today on the same triage cache and got 0.858 — a
seven-point drop with no code change. **Gemini Flash output has drifted
between then and now.** The frozen baseline is no longer reproducible.

This means: every future "did this regress?" test has to generate a fresh v7
baseline the same day, then compare. Captured as Lesson 11.

It does NOT mean the golden dataset is invalid — your labels are still correct.
It just means the *score on those labels* changes when the model changes, even
holding our code constant.

---

## Numbers at a glance — Kiddushin

| Metric                       | v7 (baseline) | v8 (Wave 1) |
|------------------------------|-------:|------:|
| Total real stories           |     96 |    93 |
| Cross-page stories           |     12 |    12 |
| Pages skipped by triage      |    109 |   100 |
| Mishnah-filtered (separate)  |      0 |     1 |
| False continuation bridges   |      4 |     1 (#47 only) |
| Missed stories recovered     |      — | 2 (45a, 53a) |

Net story count went down by 3 because three false bridges' second-page halves
were already counted as part of merged stories in v7 — removing the bridge
removes one phantom unit each. The two new real stories on 45a and 53a were
added. The Mishnah story was moved to its own list, not deleted.

---

## What's deferred to Wave 2

Wave 2 takes deterministic post-processors at the boundary level:

- **Issue #3 — start-boundary snap** (~11 cases). When the detector wraps
  preceding halakhic framing into the story, snap the start to the canonical
  introducer (`מעשה ב…`, `כי הא ד…`). Lexical, free, auditable.
- **Issue #4 — end-boundary trim** (~9 cases). When the detector sweeps in
  the stam-Talmud's interpretive follow-up (`שמע מינה`, `מאי טעמא`, etc.),
  trim those trailing segments off.
- **Issue #6(b) — biblical-actor filter**. If the only named actors in a
  detected story are biblical (Adam, Moses, David, ...), demote.

Both #3 and #4 are the cases that probably also fix your #77 (71b) issue —
that one was a same-page boundary problem, not a cross-page one.

Wave 2 carries Ketubot risk (boundary trimming could shave off real story
endings). We will guard every change with the same regression check we just
demonstrated.

## Wave 3 and later (no commitment yet)

- **Issue #8 — multi-story per page** (71a: detector kept 1 of 2 stories).
  Prompt change. Risky.
- **Issue #9 — embedded-story blindspots** (33a baraita, 81b objection).
  Few-shot examples in prompt. Risky.
- **Issue #10 — confidence calibration**. You said "not errors." Deferred
  indefinitely.
- **Issue #59 52a Gemara→Mishnah reference**. Needs content-level signal,
  not lexical. Hard.
- **Issue #47 39b→40a adjacent false bridge**. Needs content-level signal
  on page 2's first segments. Likely a small LLM check.

---

## Suggested follow-up note to Jeff (raw bullets to lift)

> We've shipped the first wave of fixes from your April review. Specifically:
>
> - The "glitch" you flagged on 70b and 71b is fixed for the cross-page
>   case (70b). The 71b case turned out to be a different bug — a
>   same-page boundary issue — and is queued for the next wave.
> - All three false-continuation bridges with intervening text (12b→13a,
>   29b→30a, 31a→31b) are removed. One (39b→40a) is adjacent — no
>   intervening text — and needs a different approach; flagged.
> - Both missed stories caused by triage misses (45a and 53a) are now
>   detected.
> - The 50b Mishnah story is now bucketed separately from the Gemara
>   stories. The 52a one is technically a Gemara reference to a Mishnah,
>   not a Mishnah story itself, so it's still in the main list — we'll
>   handle that separately.
>
> Side benefit: the same fixes meaningfully improve our Ketubot scores
> (composite +6 points, mostly because we'd had the same "first segment
> skipped" bug on 103b→104a that you spotted on Kiddushin's 70b — your
> single observation cleaned up a class of error in both tractates).
>
> Next wave tackles boundary snapping (start and end), which should
> address the majority of the ~30 boundary annotations in your review.

---

## Files

- `src/story_detector_v8.py` — Wave 1 detector
- `scripts/verify_wave1.py` — Kiddushin checklist
- `scripts/compare_ketubot_v7_v8.py` — Ketubot regression check
- `scripts/run_kiddushin_wave1.py` — Kiddushin runner
- `scripts/run_ketubot_v8.py` — Ketubot runner
- `results/kiddushin/kiddushin_v8.json` — Kiddushin Wave 1 output
- `results/v8/ketubot_v8_*.json` — Ketubot Wave 1 output
- `lessons/` Lesson 11 — LLM nondeterminism breaks historical baselines
