# Ketubot can run on v11 — and it reads Kiddushin's labels, not its own

**2026-09-15.** Status: **wiring, verified; no detector run, so no score.**
Item: [`ketubot-v11-runner`](../../work/done/2026-09-15-ketubot-v11-runner.md).
Reproduce with

```bash
python3 scripts/consolidate_ketubot_pages.py --check
python3 scripts/run_new_tractate.py --tractate ketubot --dry-run
```

Neither makes an API call.

## Why Ketubot could not be measured

The twin pass recovered 6 of Yevamot's 7 adjacent-class misses
([`twin-pass`](2026-09-14-twin-pass.md)). **Ketubot holds 7 of the 18 adjacent cases —
the largest single share** — and no entry point could run the current detector on it.
Three separate blockers, of which only the first looked like the problem:

| | before | now |
|---|---|---|
| entry point | `run_new_tractate.py` took `choices=('gittin','yevamot','eruvin')`; every Ketubot runner was pinned to v7 or v8, and the twin pass lives in v11 | `ketubot` admitted, last, so it could not be run before the other two were fixed |
| inputs | 222 dapim split across `results/v5/pages_{2-39,40-60}.json` and `results/v7/ketubot_pages_61-112.json`; triage across `results/v7/event_triage_{2-60,61-112}.json` | `results/sefaria/ketubot.json` + `results/triage/ketubot.json`, consolidated, **never re-fetched** |
| few-shot labels | all 128 are **Ketubot** (`Ketubot 2a_5-6`, `Ketubot 3a_9-10`, …) | Ketubot runs read the **Kiddushin golden**; everything else keeps the Ketubot set |

**The third was the real one.** `load_ground_truth()` loaded Ketubot labels only, and said
why in its own docstring: *"Running on Gittin/Yevamot/Eruvin, every example is
cross-tractate, so no page being scored can appear in its own prompt."* That premise fails
the moment the tractate is Ketubot. Admitting Ketubot to `choices` without touching the
few-shots would have put Ketubot's answers into Ketubot's prompts — **Critical Rule #2 and
Lesson 2** — and produced a number that looked like every other tractate's.

## What was built

**`scripts/consolidate_ketubot_pages.py`** — merges the five files into the current layout.
It copies the pages already on disk and never calls Sefaria: the golden's segment indices
are anchored to that text, and a re-fetch can renumber them silently. It carries `ref` and
`segments` only; the `v5` files also hold a `stories` key, which is v5 *detector output*
and has no business in a text cache. It refuses on a duplicate ref, on a page/triage ref
mismatch, and on a label list longer than its page — that last being the renumbering it
exists to prevent. `--check` rebuilds from the sources and compares a **digest over the
text alone**, so a metadata edit cannot mask a text change (Critical Rule #5: hashes and
counts, never a composite).

Result: **222 pages, 3038 segments, 222 triage entries**, text byte-identical to all three
sources, digest `35794dc72ab1`.

**`FEW_SHOT_SOURCE`** in the runner — an explicit per-tractate map, Ketubot → Kiddushin and
everything else → Ketubot. `load_ground_truth(db, tractate)` **raises** on a same-tractate
source, on an undeclared tractate, and on labels that turn out to carry entries from the
tractate being run. It does not warn and fall back: a fallback to Ketubot labels on a
Ketubot run yields a plausible, wrong, CIRCULAR number with nothing downstream to flag it
— the shape of [Lesson 38](../../lessons/).

The last check reads `db.tractates` **off the entries**, not off the filename. A filename
comparison would have called the blind Kiddushin boundary set a corrections set.

**`GroundTruthDB.load_from_canonical()`** — reads `results/canonical/<t>_canonical.json`
as few-shot labels. The canonical files carry the same three things the feedback loader
needs (Jeff's verdict, his note, what the detector had classified the passage as) under
different key names, so every entry lands in the same shape and the existing taggers are
reused unchanged. A story with no `review_key` was never put to Jeff; it is **counted and
returned**, never silently skipped. On Kiddushin: **96 entries, 0 skipped.**

`GroundTruthEntry._parse_key` was Ketubot-only (`r'Ketubot (\d+[ab])_…'`), which left
`page_ref` `None` for every other tractate — read downstream as *this entry has no text*
rather than as a parse failure. Now any tractate, and a test asserts every Kiddushin key
parses.

## The partition it reports

```
Ketubot: 222 pages, 3038 segments
  triage cached:  222; would triage now: 0
  under the live rule: 97 examined, 125 skipped
  ground truth: 96 entries from kiddushin (cross-tractate for ketubot)
```

**Stage 1 costs nothing** — every page is already in the cache, so the measured run is
Stage 2+4 only. The 56% skip rate sits with Gittin's 51% and Yevamot's 58%.

## What this does NOT establish

- **No detector has run.** There is no Ketubot v11 artifact and no score here. Whether
  the twin pass recovers Ketubot's 7 adjacent cases is the next item, and it needs a
  `GOOGLE_API_KEY`.
- **Kiddushin few-shots are a different prompt from Ketubot few-shots**, so a Ketubot v11
  number is not directly comparable to the v7–v10 Ketubot numbers, which were built on
  Ketubot labels. Say which, when one exists.
- **The Kiddushin pool is smaller** — 96 entries against 128 — and skews differently
  (31 `incorrect` of 96). Untested whether that changes how many examples the detection
  prompt can draw.
- **Nothing here re-measures triage.** The 97/125 partition is the live rule over the
  *cached* v7 labels, and the caveat in
  [`1_triage.md`](../capabilities/1_triage.md) still applies.

## Unrelated, found while running the suite

`tests/test_expert_doc_span_headers.py` (9 tests) shells out to **`textutil`**, which is
macOS-only, and fails with `FileNotFoundError` on Linux. `test_wave4_ship_gate` calls
`gemini-2.0-flash`, which the API now returns 404 for. Both fail identically at `HEAD`
and are environment, not regressions — but the expert-doc suite is the guard on the
ground-truth parsers, so on Linux **it is not guarding anything**.
