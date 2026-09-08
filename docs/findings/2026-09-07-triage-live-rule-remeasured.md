# Triage under the live rule *and* the current matcher — and the splice that froze the cell

**2026-09-07.** Status: **measured.** No API calls — the discarded-page Stage 2 output has
been on disk since 2026-08-31. Item:
[`board-reads-stale-triage`](../../work/done/2026-09-01-board-reads-stale-triage.md).

The board's Triage cells were the last on the coverage matrix mixing two changes: the
keep-rule shipped 2026-08-31 (`>=1 NARRATIVE_EVENT`) and the exact-anchor matcher shipped
2026-09-03. The item's standing warning was that 98.7% / 97.8% could not be copied across
from the earlier finding, because those were measured with the retired 4-gram window.

## The numbers, both changes separated by name

| | Triage | Detection given examined | end-to-end |
|---|---|---|---|
| **Ketubot** shipped artifacts, exact matcher | 96.6% (144/149) | 90.3% | 87.2% |
| **Ketubot** live rule, exact matcher | **98.0%** (146/149) | 90.4% | **88.6%** |
| *Ketubot live rule, retired 4-gram matcher (previously quoted)* | *98.7%* | — | — |
| **Kiddushin** shipped artifacts, exact matcher | 95.6% (86/90) | 88.4% | 84.4% |
| **Kiddushin** live rule, exact matcher | **97.8%** (88/90) | 88.6% | **86.7%** |
| *Kiddushin live rule, retired matcher (previously quoted)* | *97.8%* | — | — |

**Ketubot: the rule is worth +1.4 points, the matcher −0.7.** The 98.7% on record was
0.7 points of search window. **Kiddushin: the rule is worth +2.2 and the matcher nothing** —
97.8% under both, which is the coincidence that makes the Ketubot gap readable as the
matcher rather than as noise.

The rows compose again: 98.0 × 90.4 ≈ 88.6, 97.8 × 88.6 ≈ 86.7.

**Ketubot Triage now sits exactly on its ≥98% gate** — on it, not above it, on a
denominator of 149. Kiddushin is 0.2 below.

## The bug that kept the cell frozen

Running the splice before this fix moved **end-to-end** by two stories per tractate and
left **Triage unchanged**. `merge_triage_recall_run.py --live-rule` spliced the Stage 2
output onto each rescued page and left `skipped_by_triage: True` on it. The harness
derives `survived_triage` from that flag, so Ketubot 51a and 72b came back as
`survived_triage=False, in_detector=True` — **lost at Triage and found by Detection at the
same time**, which is not a state the pipeline can produce.

Fixed: the splice now sets `skipped_by_triage: False` and records the shipped decision as
`skipped_by_triage_shipped`, so the counterfactual is measurable without erasing what
actually shipped.

**This is the same defect family as the item it belongs to** — a generator faithfully
reporting a stale artifact, with `board.py --check` passing throughout because it compares
the generator against itself
([`board-guards`](2026-09-01-board-guards-verify-the-wrong-property.md)).

## Which stories the rule rescues, and which it does not

Of the **9 Triage misses on the whole board** — all of them in the single cell identified
by [`miss-anatomy`](2026-09-07-miss-anatomy.md), a story alone on a daf carrying no other
narrative label — the live rule examines **4**, and Stage 2 then finds all four:

| rescued | | still lost | why |
|---|---|---|---|
| Ketubot 51a | N=1 | Ketubot 20a | N=0, V=9 |
| Ketubot 72b | N=1 | Ketubot 27a | N=0, V=7 |
| Kiddushin 14a | N=1 | Ketubot 82b | N=0, **H=4** |
| Kiddushin 69a | N=1 | Kiddushin 10b | N=0, V=5 |
| | | Kiddushin 21b | N=0, V=4 |

**Ketubot 82b is the one worth looking at.** It carries four `HABITUAL` segments and zero
`NARRATIVE_EVENT`, and `should_skip_page()` counts only the latter. *"In the beginning they
would write two hundred for a virgin…until Shimon ben Shetah came and enacted"* is
labelled habitual by our own Stage 1 and then discarded as though the daf held nothing.
Whether `HABITUAL` is narrative evidence is a **definitional** question — the kind
[Lesson 37](../../lessons/) says to ship, unlike `V>=4`, which was a threshold fitted to
one story and rejected with a test pinning the rejection. It is **1 story in the measured
corpus**, so the case for it is the principle, not the count. Not shipped here: it changes
the shipped rule, and that belongs in its own item with its precision cost priced.

The other four are all `N=0` with verbal acts only — the case the 2026-08-31 finding
explicitly declined to buy.

## Artifacts, and what is *not* promoted

Written as **suffixed sensitivity variants**, per CLAUDE.md's rule that the unsuffixed
name is always the recall denominator:

```
results/recall/ketubot_jeff2005_matches_liverule.json
results/recall/kiddushin_jeff2005_matches_liverule.json
```

**`board.py` still reads the unsuffixed files, and STATE.md still reports the shipped
artifacts.** That is deliberate and it is the open decision: the live-rule figures are a
*splice* — the shipped runs were produced under the old rule, and the merged file says of
itself *"MEASUREMENT ARTIFACT… not a ship candidate"*. Making the board report them means
choosing to describe **the code as it is today** rather than **the artifacts we hold**,
which is a defensible choice and not one to make silently inside a measurement.

Until that is decided, quote Triage as **96.6% / 95.6% for the artifacts** and
**98.0% / 97.8% for the shipped rule**, and say which.
