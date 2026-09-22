---
title: Finish the 18 — twin pass on Kiddushin (3 cases) and Gittin (1)
capability: [detection]
tractate: [kiddushin, gittin]
blocked_by: []
awaiting: []
writes: [scripts/run_new_tractate.py, scripts/consolidate_legacy_pages.py, results/sefaria/kiddushin.json, results/triage/kiddushin.json, results/v11/kiddushin/, results/v11/gittin/, results/recall/kiddushin_jeff2005_matches_v11control.json, results/recall/kiddushin_jeff2005_matches_v11twinall.json, results/recall/gittin_jeff2005_matches_v11control.json, results/recall/gittin_jeff2005_matches_v11twinall.json, docs/findings/2026-09-22-twins-all-four-tractates.md]
finding:
superseded_by:
---

# Finish the 18

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md), then
[`miss-anatomy`](../docs/findings/2026-09-07-miss-anatomy.md),
[`twin-pass`](../docs/findings/2026-09-14-twin-pass.md) and
[`ketubot-twin-pass`](../docs/findings/2026-09-15-ketubot-twin-pass.md).
**Capability: 2 Detection.** **Depends on Jeff: no.**

## The problem

The 18 adjacent-class misses split **Ketubot 7 / Yevamot 7 / Kiddushin 3 / Gittin 1**.
Fourteen are measured — **6 of 7 recovered on each** of Ketubot and Yevamot. The remaining
four have never been run through the pass.

| tractate | cases | opening |
|---|---|---|
| Kiddushin 31b seg 3 | 1 | `אמר ליה רב יעקב בר אבוה לאביי` |
| Kiddushin 40a seg 0 | 1 | `גבורי כח עושי דברו` (R. Zadok — the twin of Rav Kahana and the noblewoman) |
| Kiddushin 72a seg 4 | 1 | `אמר רב איקא בר אבין אמר רב חננאל אמר רב: חלזון ניהוונד` |
| Gittin 47a seg 0 | 1 | `פירקן, אמר ליה, תנן: המוכר עצמו ואת בניו` |

**Gittin runs today.** **Kiddushin does not** — it is not in `KNOWN`, and its pages and
triage sit in the pre-2026-08 layout (`results/v7/kiddushin_pages.json`, 162 pages;
`results/v7/event_triage_kiddushin.json`, 162 entries), exactly as Ketubot's did.

## Method

1. **Wire Kiddushin** the way Ketubot was wired
   ([`ketubot-v11-runner`](done/2026-09-15-ketubot-v11-runner.md)): consolidate the two
   files into `results/sefaria/kiddushin.json` + `results/triage/kiddushin.json`,
   **never re-fetching**; add `kiddushin` to `KNOWN`; declare
   `FEW_SHOT_SOURCE['kiddushin'] = 'ketubot'`. That source is already loadable, so unlike
   Ketubot this needs no new ground-truth loader — but the **same guard applies and must
   fire**: a tractate is never scored on its own labels.
2. **Two arms per tractate**, as on Ketubot. The control is not optional: a shipped
   artifact built on different code or different few-shots cannot serve as one.
3. Score with `--matcher exact` **and no other matcher**, `--output` to a suffixed path —
   never the unsuffixed denominator.
4. **Report the four cases by name**, found or not, per tractate.
5. Report **proposals added and how many are not on Jeff's list**. Yevamot cost 9,
   Ketubot 16; two points do not make a rate, and four will not either — say so.

## How you know it worked

- All four cases named individually with their outcome.
- Kiddushin Detection recall (given the page survived triage) moves from **88.4%**,
  Gittin from **97.3%**.
- Proposals-not-on-his-list reported per tractate beside the recall change.
- The neutral boundary ruler has not fallen (`--by-direction`).
- `python3 -m pytest tests/ -q` green but for the 10 known environment failures.

## Guardrails

- **Never re-fetch from Sefaria** — the golden's segment indices are anchored to the text
  on disk.
- **The few-shot guard raises, never warns.** Kiddushin must not read Kiddushin labels.
- Kiddushin's recall denominator is the **flag-filtered** list, not the raw length —
  `--expert-filter recall` on `results/expert_lists/kiddushin_2005.json` (Lesson 29).
- Blind and corrections rulers reported apart (Lesson 24).
- **One run per arm is known to be thin** — Ketubot's arms differed in base detection
  (2026-09-15). Report any base churn rather than folding it into the headline.

## When done

Finding to `docs/findings/2026-09-22-twins-all-four-tractates.md` — the whole 18 in one
table — add `## Outcome` here, then
`python3 scripts/board.py finish 2026-09-22-finish-the-18-twins`.
