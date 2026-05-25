# Kiddushin Feedback Analysis — Jeff Rubenstein, 2026-04-23

**Source files:**
- `validation/feedback/kiddushin_review_2026-04-23.json` (96 stories rated in UI)
- `validation/feedback/Kiddushin missesd stories.docx` (5 stories the AI missed)
- Detector output: `results/kiddushin/kiddushin_v7.json`

## 1. Kiddushin vs. Ketubot — how did we scale?

### Ketubot baseline (golden, post-corrections)
- Classification F1: **0.918** (P 0.857 / R 0.987)
- Boundary mean IoU: **0.977** (94.9% above 0.8)
- Merge F1: **0.865**
- **Composite: 0.931**

### Kiddushin (this round, before any fixes)
- Raw verdict accuracy: **65/96 = 67.7%**
- Stripping confidence-level judgment calls (Jeff excludes them): ~80–83% effective
- 5 stories missed by detector → ~78% recall against Jeff's expected set
- Boundaries: **~30 of 96 entries had boundary problems** (most on entries Jeff marked "correct"). On Ketubot post-correction we were near-perfect (IoU 0.98); on Kiddushin we have not been scored yet but qualitatively boundaries are clearly worse.
- Continuation/cross-page: **directionally better** ("much better" per Jeff) — but with two bugs (false continuations + first-segment-of-next-page glitch).

### Verdict: scaled partially
| Dimension | Ketubot | Kiddushin | Delta |
|---|---|---|---|
| Classification F1 | 0.92 | ~0.78–0.84 (est.) | **↓** |
| Boundary quality | 0.98 IoU | ~30 issues flagged | **↓ significantly** |
| Cross-page merge | 0.86 F1 | "much better" qualitatively, 12 detected, 2 bug classes | **mixed** |
| Recall (no missed) | 0.99 | ~0.95 (5 missed of ~101) | **↓ slightly** |

**Net:** generalization is real but the composite score will be meaningfully below 0.93. The biggest under-reported regression is **boundaries**, which my first pass to Simon glossed over.

## 2. Complete error taxonomy (all 96 entries + 5 missed)

### Category 1 — Boundary errors (~30; the biggest unaddressed finding)

**1a. Start boundary wrong** (~11): #1, 2, 16, 20, 34, 38, 45, 52, 64, 72, 73.
Detector typically starts BEFORE the introducer (`מַעֲשֶׂה ב…` / `כִּי הָא ד…`) and includes the preceding halakhic discussion, OR omits the introducer entirely.

**1b. End boundary overshoots into Talmud commentary** (~9): #7, 18, 19, 33, 61, 80, 81, 86, 87.
Detector sweeps in the stam-Talmud's interpretive follow-up (markers: `שְׁמַע מִינַּהּ`, `מַאי טַעְמָא`, `וְאִי`, attribution chains, register shift to dialectic).

**1c. Cross-page bugs — TWO distinct issues**

*Bug A — false continuations* (continuation check joins non-continuous text): #11 (12b→13a), #21 (29b→30a), #26 (31a→31b), #47 (39b→40a). All four cases have intervening non-story material that the check missed.

*Bug B — the "glitch" Jeff named explicitly* (skipping segment 0 of the second page): #75 (70b), #77 (71b). Off-by-one in stitching code.

### Category 2 — Confidence-level disagreements (16; Jeff: "not errors")

- **LOW underrated → should be HIGH/YES** (10): #3, 12, 17, 23, 28, 32, 33, 46, 71, 96. Detector under-confident on rich narratives.
- **HIGH overrated → should be LOW** (4): #9, 19, 39, 65. Mostly legal with thin narrative wrap.
- **YES → LOW** (2): #30, 70. Single-event vignettes flagged as full stories.

### Category 3 — False positives (10; "not a story" per Jeff)

| # | Page | Sub-pattern |
|---|---|---|
| 13 | 20a | Pure dialogue / legal back-and-forth |
| 22 | 29b | Statement about rabbi's past, no narrative |
| 31 | 32a | All dialogue, legal rebuke |
| 40 | 38a | Mid-line of legal discussion about biblical past |
| 41 | 38a | Biblical character + verses (not rabbinic) |
| 42 | 39a | Single event, no change/conflict |
| 44 | 39a | One action + legal discussion |
| 51 | 41a | Two independent events, not a single narrative |
| 69 | 60b | Bare report of a legal tradition |
| 82 | 72b | Biblical story, not rabbinic |

Sub-patterns: (a) dialogue-only ≠ story; (b) biblical content; (c) single event without change/conflict.

### Category 4 — Wrong corpus (2)
- #58 50b — Mishnah story (should be tallied separately, not under Talmud)
- #59 52a — only a *reference* to a Mishnah story, not the story itself

### Category 5 — Missed stories (5)

| Daf | Story | Where it lives in output | Root cause |
|---|---|---|---|
| **33a** | R. Chiyya in bathhouse / R. Shimon doesn't stand | seg 5–6, Stage 2 ran (4 stories found) | Stage 2 absorbed it into the surrounding sugya — story-as-objection blindspot |
| **45a** | Two drinking under poplars, betrothal offer | seg 5 | `skipped_by_triage: True` — Stage 1 false negative |
| **53a** | One who snatched portions / "ben Chamtzan" | seg 8 (introduced by `מַעֲשֶׂה בְּאֶחָד`) | `skipped_by_triage: True` — Stage 1 missed the `מַעֲשֶׂה ב…` cue |
| **71a** | "Babylon dough to Israel" in days of Rabbi | seg 2–5, Stage 2 ran (1 story found) | Multi-story-per-page under-recall |
| **81b** | R. Tarfon "beware me re my daughter-in-law" | seg 9 | Baraita-embedded narrative blindspot |

### Category 6 — Jeff's freeform observations
1. ✅ "AI thought low confidence that were certainly stories" — matches 10 LOW-underrated cases.
2. ✅ "Called low confidence that were just legal traditions" — matches FP cluster (#13, 22, 31, 42, 44, 69, 51).
3. ✅ "Finding stories that went from one page to the next was much better" — 12 continuations detected; continuation-check feature is working directionally.
4. ⚠️ "Glitch — sometimes skipped lines from the next page" — Bug B above (#75, #77).
5. ⚠️ "Five stories missed" — itemized in Category 5.

## 3. Counts at a glance

| Bucket | Count |
|---|---|
| Fully clean (correct, no notes) | ~37 / 96 (39%) |
| Correct verdict but boundary issue flagged | ~28 / 96 (29%) |
| Confidence-level disagreements (don't count per Jeff) | 16 |
| False positives — not a story | 10 |
| Wrong corpus | 2 |
| Other classification flips | ~3 |
| Missed stories | 5 (out of ~101 true) |

**"Errors that count"** = 10 FPs + 2 corpus + 5 missed + ~28 boundary refinements ≈ **45 substantive issues across ~101 items**.

## 4. Where the gap to Ketubot lives

| Failure mode | In Ketubot? | In Kiddushin? | Why the regression |
|---|---|---|---|
| Story-START boundary off | rare (training data) | ~11 cases | New introducer patterns (`מַעֲשֶׂה ב…`, `כִּי הָא ד…`) not handled |
| Story-END sweeps in commentary | rare (training data) | ~9 cases | No trim rule for stam-Talmud follow-up |
| Cross-page false bridge | n/a (new feature) | 4 cases | Continuation check doesn't verify continuity of intervening material |
| Cross-page first-segment skip | n/a (new feature) | 2 cases | Off-by-one in stitching code |
| Triage false negative | low | 2 missed pages | `מַעֲשֶׂה ב…` / `הָנְהוּ בֵּי תְרֵי` not in Stage 1 cues |
| Embedded-story miss | rare | 3 missed (33a/71a/81b) | Multi-story-per-page; baraita-embedded; objection-embedded |
| "Not a story" FPs | seen | 10 cases | Discrimination on dialogue-only / biblical / no-change |

The two new feature areas (continuation check, broader tractate coverage) account for most of the regression. The core Stage-2 detector held up reasonably; the failure surface moved to **boundaries and continuation mechanics**.
