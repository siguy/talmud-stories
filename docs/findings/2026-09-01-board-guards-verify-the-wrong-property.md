# The board's guards verify the wrong property: three defects behind a passing check — 2026-09-01

**Capability: cross-cutting** (measurement bookkeeping; the worst of the three lands on
**1 Triage**).
**Status: measured.** Two defects **FIXED** — `scripts/board.py` changed. One is a
measurement decision and is **OPEN**:
[`work/2026-09-01-board-reads-stale-triage.md`](../../work/2026-09-01-board-reads-stale-triage.md).
**Items:** [`board-loaders-report-absence`](../../work/done/2026-09-01-board-loaders-report-absence.md),
[`board-reads-stale-triage`](../../work/2026-09-01-board-reads-stale-triage.md).

---

## The shape

Three defects in the generated board, found while reading `STATE.md` against the
artifacts it claims to summarise. Throughout, **both guards passed**:

```
$ python3 scripts/board.py --check
STATE.md and WORK.md are up to date
$ python3 -m pytest tests/test_bookkeeping.py -q
passed
```

Neither guard is broken. Each verifies a real property. Neither verifies **the property
that matters**, and the gap between the two is where all three defects sat:

| the guard checks | the defect lives in |
|---|---|
| STATE.md matches what `board.py` computed | whether what `board.py` computed matches the artifact |
| the golden counts, hashes and links are intact | whether the numbers on the board describe the shipped code |

`--check` recomputes the board and compares the checksum. If the generator misreads an
artifact, it misreads it identically on both sides and the check passes. **A checksum over
a derivation cannot see an error in the derivation.**

---

## 1 · The board reports the triage rule that was replaced — OPEN

```
STATE.md      Ketubot 98.0%   Kiddushin 95.6%
shipped code  Ketubot 98.7%   Kiddushin 97.8%
```

`should_skip_page()` has kept any page with `>=1 NARRATIVE_EVENT` since 2026-08-31
([`triage-single-narrative`](2026-08-31-triage-single-narrative.md)). But
`board.py recalls()` reads `results/recall/<t>_jeff2005_matches.json`, whose
`survived_triage` flag was computed from the *shipped run's* examined-page set — produced
under the **old corroboration rule**. Recomputed from the artifacts:

```
ketubot    n=149  survived_triage=146 (98.0%)   in_detector=143  det|surv 143/146 (97.9%)
kiddushin  n=90   survived_triage=86  (95.6%)   in_detector=84   det|surv  84/86  (97.7%)
```

Exactly the numbers STATE.md prints. The generated panel is faithful to its artifact and
the artifact is stale — in the one capability FRAMEWORK §2 calls invisible and permanent,
and the only one whose cell was below its gate.

The hand-written `STATUS.md` has the right values. So **the file that promises it types no
numbers is the one that is wrong, and the file that is typed by hand is right** — the
opposite of the reliability the split was built to give.

**The Detection cells inherit it.** `detection_given_triage` divides by the same
`survived_triage` set, so both rows on both tractates are conditioned on a partition the
detector no longer uses.

**Not fixed here, deliberately.** The repair is to re-run
`measure_recall_vs_expert_list.py` under the live rule, which rewrites the file CLAUDE.md
calls *"always the recall denominator"*. That changes what every recall cell means and is a
measurement decision, not a cleanup. Method and guard are in the open item.

---

## 2 · Two Kiddushin files collided on a key, and the blind list lost — FIXED

The sharper half of what first looked like a formatting problem.

```python
out[f.stem.split("_")[0]] = {...}      # kiddushin_2005            -> 'kiddushin'
                                       # kiddushin_comments_harvested -> 'kiddushin'
```

Both files key to `'kiddushin'`, and `sorted()` puts the harvest second, so it
**overwrote** the story list. Confirmed against the pre-fix code:

```
files on disk : ['kiddushin_2005', 'kiddushin_comments_harvested']
board rows    : ['kiddushin']  -> LOST 1 row to key collision
   kiddushin: parsed=0 blind=0 cfr=0  path=.../kiddushin_comments_harvested.json
```

So `STATE.md`'s **Ground truth on hand** table did not merely mis-size a file. It **never
showed the Kiddushin blind list at all** — the 89-blind / 90-for-recall denominator behind
every Kiddushin number on the board — and printed a row of zeros where it should have been.

The second defect is the one that made it unreadable: the harvest was then sized with the
story-list formula, so a file holding **11 sentence-level remarks** — including the 2005
margin note that retired an open question with Jeff without spending one of his answers —
rendered as `0 parsed · 0 blind · 0 count for recall` under a heading reading **BLIND**.

**Fixed:** rows are keyed by full stem; each shape is sized in its own units; an
unrecognised shape is named with its keys and marked `**UNKNOWN**` rather than sized at
zero. Zero-because-empty and zero-because-unrecognised no longer share a representation
(Lesson 38).

**And the fix had to adopt the harness's filter, or it would have introduced the same
drift it removes.** `load_expert()` drops `duplicate_of` entries *before* applying the
flag. Counting the flag over the raw list gives **91** where the harness's denominator is
**90**; the board now drops the duplicate first and prints the duplicate it dropped. A test
pins the board, the harness and the ruler to the same number.

```
before   (row absent)
after    94 parsed (1 duplicate dropped) · 89 blind · 90 count for recall
```

---

## 3 · A null verdict with a note was not counted — FIXED

```
board.py     24 verdicts
the file     25   ("reviewed_count": 25, feedback: [25 entries])
```

`_verdict_count()` counted list entries with a **truthy** `feedback_type`. One of Jeff's
25 has `feedback_type: null`. The function's own docstring says the file holds *"25 real
verdicts"* three lines above the code that printed 24.

The dropped entry is not filler. It is **Ketubot 17a**:

> "Here the English and Hebrew/Aramaic do not exactly correlate. There is more in the
> Hebrew/Aramaic. But this excerpt contains one story: רַב שְׁמוּאֵל בַּר רַב יִצְחָק מְרַקֵּד אַתְּלָת…"

He declined the dropdown and answered in prose — stating a display defect, then **quoting
the Hebrew of the story he says the excerpt contains**. The single most informative verdict
in the round is the one the inventory could not see.

This is the same round that `build_ruler.load_reviews()` skipped for eight months on an
`isinstance` guard (Lesson 38). The fix written *for* that lesson reproduced its shape one
level down: the round was recovered, then miscounted.

**Fixed:** an entry counts if it carries a judgement **field** (`verdict`,
`feedback_type`, `is_story`, `classification`) or a note — not if that field is truthy.
A null verdict with a note is an expert answering in prose, not an absent verdict.

---

## Guarded

`tests/test_board_reports_what_it_holds.py`, 12 tests. Every one was watched fail against
`git show HEAD:scripts/board.py` before the fix (Lesson 31):

- every file in `results/expert_lists/` gets its own row — the collision, directly;
- the Kiddushin blind list is present and is not the harvest;
- a harvest is sized in remarks, and `0 parsed` never appears for one;
- an unrecognised shape is **named with its keys**, never sized at zero (a synthetic
  `gittin_something_new.json` in `tmp_path`);
- the board's count for recall equals the harness filter **and** the ruler's denominator;
- the January round counts 25, and any file stating its own `reviewed_count` must match it;
- four shapes of expert judgement all count; a row carrying none still does not.

---

## What this says about the guards

The board was built on 2026-08-30 to end hand-typed numbers, and it did — every value in
`STATE.md` is read from disk. But **"generated" was allowed to stand in for "correct"**,
and three defects lived comfortably inside a passing check because the check compares the
generator against itself.

What none of the existing guards ask:

1. **does the artifact describe the shipped code?** (defect 1 — nothing anywhere asserts
   this, and it is the one that matters most)
2. **did the loader see every input?** (defect 2 — a collision silently halves a table)
3. **does the count match what the file says about itself?** (defect 3 — `reviewed_count`
   was sitting in the file the whole time, unread)

(3) is now a test. (2) is now a test. (1) is the open item, and it is the one a checksum
can never reach: the generator is honest about the artifact; the artifact is stale about
the code.

→ **Lesson: a guard can verify the wrong property and pass forever.**
