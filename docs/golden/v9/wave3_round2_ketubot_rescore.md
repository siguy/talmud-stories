# Wave 3 Round 2 — Ketubot rescore after Jeff's 2026-06-03 corrections

**Date:** 2026-06-03
**Source:** Jeff email reply to Wave 3 review (4 Ketubot golden corrections)
**Script:** `scripts/apply_jeff_2026-06-03_corrections.py`
**Detector unchanged:** v9 Wave 3 (`results/v9/wave3/ketubot_v9_{2-60,61-112}.json`)

## Corrections applied

| Story | Action | Notes |
|---|---|---|
| Ketubot 7a_1-1 | NOT_A_STORY → LOW_CONFIDENCE | v9 already detects this as LOW — agreement improves |
| Ketubot 26a_9 | confirmed NOT_A_STORY | no change to golden; v9 still detects as LOW (residual FP) |
| Ketubot 102a_6 | confirmed not a story | no change; not in golden, not detected |
| Ketubot 106a_3-3 → 2-3 | extend_start | Jeff: "the story is segments 2-3, not really 1" (v9 detected 1-2) |

## Score comparison (v9 unchanged; golden updated)

| Metric | Wave 3 (pre) | Round 2 (post) | Δ |
|---|---|---|---|
| Composite | 0.9170 | **0.9171** | +0.0001 |
| Classification F1 | 0.9105 | **0.9141** | +0.0036 |
| Classification precision | 0.886 | 0.892 | +0.006 |
| Classification recall | 0.9367 | 0.9371 | +0.0004 |
| TP / FP / FN | 148 / 19 / 10 | **149 / 18 / 10** | +1 TP, −1 FP |
| Boundary IoU mean | 0.95 | 0.95 | flat |
| Boundary >0.8 pct | 0.9054 | 0.8993 | −0.006 (106a slice change) |
| Merge F1 | 0.8571 | 0.8571 | flat |

## Interpretation

- **One FP flipped to TP** (7a_1-1) — the LOW_CONFIDENCE re-add directly aligns with what v9 was already saying. This is a "the golden was wrong, fix it" win.
- **Boundary IoU pct above 0.8 dropped slightly** — expected from the 106a 1-2 → 2-3 shift; v9's 1-2 detection only partially overlaps the new 2-3 boundary (overlap = 1 segment).
- **Composite is essentially unchanged** — the FP recovery and the IoU drop cancel out.
- **Classification F1 +0.0036** — small but real win on the metric Jeff cares about most.

## What Jeff did NOT do (still blocking the bigger movement)

- Did **NOT verdict the 7 new Kiddushin candidates** — they're still all FPs against the Kiddushin golden (composite stuck at 0.8859).
- Did **NOT verdict the 4 new Ketubot candidates** from the Wave 3 email — they remain in v9 but not in golden.
- Did **NOT complete the other ~85 Kiddushin stories** in the review (he reviewed ~10, flagged 7 boundary issues, confirmed 1 boundary correct).

Per Lesson 13/14, the Ketubot ceiling here is bounded by golden coverage, not detector quality. The next round 2 rescore depends on Jeff completing the Kiddushin pass and/or verdicting the 11 new candidates we sent.

## Next

See `tasks/PLAN_wave3_round2.md` Step 2-4 and `tasks/PLAN_wave4.md` (to be drafted).
