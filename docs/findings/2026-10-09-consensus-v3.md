# Consensus v3: Jeff's 2026-10-07 rulings made both judges stricter — Claude much more so

**Date:** 2026-10-09 · **Item:** `work/done/2026-10-09-consensus-v3-after-jeff-rulings.md`
**Evidence:** CIRCULAR / rule-informed (labels as in `full_v2_*`); **measured**, one run per
judge (no repeat). Script: `scripts/compare_consensus_v3.py` → `results/consensus/phase1/compare_v3.json`.

Only the register changed from v2 (`docs/STORY_RULES.md` with his 2026-10-07 rulings). Same
prompt file, labels, Gemini model and settings, subagent seed and batches.

## The §4 criteria

| (current labels: his 2026-10-07 verdicts applied) | v2 | v3 | §4 bar |
|---|---|---|---|
| judges agree on review passages | 291/363 = 80.2% | **275/364 = 75.5%** | ≥ 80% |
| both say `story` where he said no | 3 | **1** | ≤ 2 |
| both say `not` on a list story | 8 of 441 | **14 of 443** | ≤ 2 |
| — same, the 8 ruled passages excluded | 5 of 438 | **13 of 440** | |

Whole set (current labels): both right 831 → **801**; split 115 → **140**; both wrong 46 → 54.

## What moved

- **The eight passages he ruled on: 8/8 now answered his way by both judges** (4B, blank,
  both `not`). They are quoted in the register, so this is partly reading the answer.
- **Claude moved ~17% of its answers** (story→borderline 66, story→not 48, borderline→not 31);
  Gemini far less (story→not 44, story→borderline 13). v2's same-prompt repeat moved Claude
  5.8–7.6%, so this is well above noise. Claude now says `not` 291 times (Gemini 172).
  The judges drifted **apart** — that is the agreement drop.
- **Ten list stories newly rejected by both.** Two are ones he ruled out (Ketubot 21b, 53a —
  correct). The other eight, mostly citing R-C5 / the R-C0 limit:
  - *case brought to a rabbi, ruled on* — Ketubot 65a:10, Yevamot 45a:16, Gittin 89a:19;
  - *a single report / habit* — Ketubot 60b:9 (alluded incident), 67b:3 (Galileans' habit),
    Gittin 52a:14, Yevamot 63a:7;
  - *scholarly exchange* — Yevamot 78a:13.
- **His `no`s called `story` by both:** 3 → 1 (only Ketubot 111a:23-25 remains).

## Reading

The rulings did what they say on his own cases and on the "his no → story" error. But the
"case + ruling needs another action or change" line is being applied **wider than he drew
it**, and Claude applies all of the new lines harder than Gemini. Whether the eight are
correct rejections (his 2005 list being provisional) or over-reach is **his call, on cases**
— not something to tune away (L-044: don't move §4 or the register to pass a test).
§4 still fails, now on agreement as well.

## Not done

- No repeat run; the per-model shift is above noise, individual list cases are not.
- Detector v12 (`src/story_detector_v12.py`) is written, not run.
