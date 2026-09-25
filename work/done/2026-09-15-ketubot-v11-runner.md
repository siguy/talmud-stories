---
title: Wire Ketubot to the v11 runner — cross-tractate few-shots, consolidated inputs
capability: [detection]
tractate: [ketubot]
blocked_by: []
awaiting: []
writes: [scripts/run_new_tractate.py, scripts/consolidate_ketubot_pages.py, src/ground_truth.py, results/sefaria/ketubot.json, results/triage/ketubot.json, tests/test_ketubot_v11_runner.py]
finding: docs/findings/2026-09-15-ketubot-v11-runner.md
superseded_by:
---

# Wire Ketubot to the v11 runner

**Self-contained.** A fresh session executes this with no other context.
Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then
[`twin-pass`](../../docs/findings/2026-09-14-twin-pass.md) and
[`miss-anatomy`](../../docs/findings/2026-09-07-miss-anatomy.md).
**Capability: 2 Detection.** **Depends on Jeff: no.** **Cost: no API calls in this item.**

## The problem

The twin pass recovered 6 of Yevamot's 7 adjacent-class misses
([`twin-pass`](../../docs/findings/2026-09-14-twin-pass.md)). **Ketubot holds 7 of the 18
adjacent cases on the board — the largest single share — and cannot be measured**, because
no entry point runs the current detector on it:

| blocker | detail |
|---|---|
| no v11 entry point | `run_new_tractate.py` has `KNOWN = ('gittin','yevamot','eruvin')` and `--tractate` is `choices=KNOWN`. Every Ketubot runner is pinned to a frozen detector: `run_ketubot_61_112.py` -> v7, `run_ketubot_v8*.py` -> v8. The twin pass lives in v11 |
| inputs in the old layout | the runner reads `results/sefaria/<tractate>.json`; Ketubot's 222 dapim are split across `results/v5/pages_2-39.json` (76), `results/v5/pages_40-60.json` (42) and `results/v7/ketubot_pages_61-112.json` (104). Triage likewise: `results/v7/event_triage_{2-60,61-112}.json` |
| **few-shots are Ketubot** | `load_ground_truth()` loads Ketubot labels only, deliberately — *"Running on Gittin/Yevamot/Eruvin, every example is cross-tractate, so no page being scored can appear in its own prompt."* All 128 entries are Ketubot (`Ketubot 2a_5-6`, `Ketubot 3a_9-10`, ...). Pointing it at Ketubot puts Ketubot's answers into Ketubot's prompts |

The third is the one that matters. It is **Critical Rule #2** and **Lesson 2**, and it is
why this is not a `choices` edit.

## Method

1. **Consolidate the inputs, never re-fetch.** All three page files are already
   `{ref, segments}`, the same shape the sefaria layout carries, so this is a merge and a
   metadata wrapper — no Sefaria API calls, and no risk of the text moving under the
   golden. Same for the two triage caches. `scripts/consolidate_ketubot_pages.py`,
   idempotent, `--check` verifies without writing.
2. **Give Ketubot a cross-tractate few-shot source.** Add a Kiddushin loader to
   `GroundTruthDB` reading `results/canonical/kiddushin_canonical.json`, and have the
   runner select the source by tractate: Ketubot gets Kiddushin, everything else keeps
   Ketubot. **The runner must refuse to run a tractate on its own labels** — not warn,
   refuse — so this cannot regress silently the way Lesson 38's `isinstance` guard did.
3. **Admit Ketubot to `KNOWN`.** Last, so it is impossible to run before (1) and (2).
4. **No detector run in this item.** It ends when `--dry-run` reports the right page
   partition and the guard tests pass. The measured run is a separate item.

## How you know it worked

- `results/sefaria/ketubot.json` holds **222** pages, refs unique, every page carrying
  segments; `results/triage/ketubot.json` covers the same refs.
- Page text is **byte-identical** to the three sources — assert with `git hash-object`
  over the extracted segments, not by eye (Critical Rule #5: counts and hashes, never a
  composite).
- `run_new_tractate.py --tractate ketubot --dry-run` reports the partition and makes
  **no API call**.
- A test asserts the few-shot source for every known tractate is **not** that tractate,
  and that requesting a same-tractate source **raises**.
- `python3 -m pytest tests/ -q` green, `test_bookkeeping.py` included.

## Guardrails

- **Never re-fetch from Sefaria.** The golden's segment indices are anchored to the text
  already on disk; a re-fetch can silently renumber them.
- **The few-shot guard raises, it does not warn.** A quiet fallback to Ketubot labels
  produces a plausible, wrong, CIRCULAR number that nothing downstream would flag.
- **No API calls in this item**, so nothing here can be attributed a score.
- Do not touch `scripts/evaluate_golden.py` or `docs/golden/v7/baseline_ketubot.json`.

## When done

Write the finding to `docs/findings/<date>-ketubot-v11-runner.md`, add `## Outcome`
here, then `python3 scripts/board.py finish 2026-09-15-ketubot-v11-runner`.

## Outcome

**Done, 2026-09-15. Wiring only — no detector run, so no score.**

`--tractate ketubot` now runs the v11 pipeline. **222 pages / 3038 segments** consolidated
into `results/sefaria/ketubot.json` from the three v5/v7 files, text byte-identical
(digest `35794dc72ab1`), triage from the two v7 caches; nothing re-fetched. Dry run
reports **97 examined / 125 skipped** under the live rule, and Stage 1 needs no API call
because every page is already cached.

**The few-shot problem was the substance, not the `choices` line.** All 128 existing
labels are Ketubot, so admitting Ketubot without changing the source would have scored it
on its own answers (Critical Rule #2, Lesson 2). `FEW_SHOT_SOURCE` now maps Ketubot →
Kiddushin, and `load_ground_truth` **raises** — never warns and falls back — on a
same-tractate source, an undeclared tractate, or labels carrying the run tractate's own
entries. The last is checked against `db.tractates`, read off the entries rather than a
filename. New `GroundTruthDB.load_from_canonical()` reads the Kiddushin golden: 96 entries,
0 skipped for want of a `review_key`. `_parse_key` was Ketubot-only and silently left
`page_ref` `None` for every other tractate; now general, and pinned.

10 new guard tests. Suite: **347 passed**, with the same 10 failures that fail at `HEAD` —
9 in `test_expert_doc_span_headers.py`, which shells out to the macOS-only `textutil`, and
`test_wave4_ship_gate`, which calls the retired `gemini-2.0-flash`. Verified against a
worktree at `HEAD`, not assumed. **On Linux the expert-doc suite guards nothing** — that
is worth an item of its own.

→ [`ketubot-v11-runner`](../../docs/findings/2026-09-15-ketubot-v11-runner.md)
