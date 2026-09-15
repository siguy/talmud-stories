# Ketubot: 6 of 7 twins recovered, and the reviewer cost is not single digits

**2026-09-15.** Status: **measured, one run per arm.** Item:
[`ketubot-twin-measure`](../../work/done/2026-09-15-ketubot-twin-measure.md).
Artifacts `results/v11/ketubot/`. Reproduce:

```bash
python3 scripts/run_new_tractate.py --tractate ketubot --output results/v11/ketubot/ketubot_v11.json
TWIN_PASS=1 TWIN_TRIGGER=all python3 scripts/run_new_tractate.py --tractate ketubot \
    --output results/v11/ketubot/ketubot_v11_twinall.json
```

Confirms [`twin-pass`](2026-09-14-twin-pass.md) on a second tractate, and **corrects one
thing it asserted**: on Ketubot the runs are *not* deterministic.

## The two arms

Both v11, `gemini-3-flash-preview`, thinking off, **Kiddushin few-shots**. Scored against
Jeff's 2005 list, `--matcher exact` and no other.

| arm | end-to-end | given the page was examined | proposals |
|---|---|---|---|
| **control** (twin off) | 132/149 = **88.6%** | 132/146 = **90.4%** | 178 |
| **twin, `all`** | 139/149 = **93.3%** | 139/146 = **95.2%** | 201 |
| *v10 shipped, for reference* | *130/149 = 87.2%* | *130/144 = 90.3%* | — |

**The control is the load-bearing row.** v10 ran on **Ketubot** few-shots; the control runs
on Kiddushin's. They score the same, so the cross-tractate swap costs nothing and the twin
arm's gain is attributable to the pass rather than to the prompt change underneath it
([`ketubot-v11-runner`](2026-09-15-ketubot-v11-runner.md)).

## The 7 adjacent cases, by name

The [miss anatomy](2026-09-07-miss-anatomy.md) named seven Ketubot misses sitting one
segment from a proposal. **Six recovered.**

| case | opening | control | twin |
|---|---|---|---|
| Ketubot 53a seg 11 | `יתיב רבין בר חנינא קמיה דרב חסדא` | missed | **found** |
| Ketubot 61a seg 13 | `אבוה בר איהי ומנימין בר איהי` | missed | **found** |
| Ketubot 61a seg 14 | `הנהו תרתין חסידי` | missed | **found** |
| Ketubot 67b seg 2 | `אמרו עליו על הלל הזקן` (Hillel buys the horse) | missed | **found** |
| Ketubot 67b seg 16 | `רבי אבא הוה צייר זוזי בסודריה` | missed | **found** |
| Ketubot 112a seg 10 | `א"ל ההוא צדוקי לר' חנינא` (the Sadducee) | missed | **found** |
| **Ketubot 111a seg 12** | `ההוא דנפק מפומבדיתא לבי כובי` | missed | **missed** |

Six of seven, against Yevamot's six of seven. The mechanism reproduces on a second
tractate, which is what this run existed to establish.

**Ketubot 53a is the case in full.** Three of Jeff's stories share segments 11-14, all the
same formula — a sage sits or arrives, recites a ruling in someone's name, gets a barbed
reply. The control proposes on seg 12 alone, as every shipped run has. Asked whether the
segment next door is a separate incident, the pass says yes.

## What it cost, which is the number that decides shipping

**The pass added 23 proposals. 7 are on Jeff's list. 16 are not.**

Yevamot added 12, of which 9 were not on his list, and the item's bar was *single digits*.
**Ketubot misses that bar.** Sixteen extra items per tractate in front of the reviewer, for
seven stories, against a bottleneck that is Jeff's attention. Whether they are false
positives or stories his 2005 list does not carry is unknown until he sees them — three of
the Gittin extras turned out to be real — but the count is nearly double Yevamot's and
the honest reading is that the price varies by tractate and one tractate did not price it.

API calls rose roughly 30% (24 min -> 32 min).

## Boundaries did not fall

294 detector-blind 2005 targets, `--by-direction`, `--standard jeff-2026`:

| arm | scored | hit | hit+near | N/A | **MISS** | start hit | end hit |
|---|---|---|---|---|---|---|---|
| control | 232 | 81% | 83% | 62 | **39** | 88% | 73% |
| twin | 248 | 82% | 84% | 46 | **39** | 88% | 75% |

**The MISS count is identical.** The pass scored 16 more targets — recovering a story gives
the ruler something to grade — without producing a single new boundary error. Starts are
unchanged; ends move 73% -> 75%, inside noise.

## The correction: these runs are not deterministic

`twin-pass` justified one run per arm on *"spread 0.0 established 2026-09-09"*. That was a
20-page Yevamot slice. **On Ketubot the two arms' base detection differs**: 178 base
proposals against 177, with **5 only in the control and 4 only in the twin arm** — and the
twin pass cannot cause this, because `tests/test_twin_pass.py` pins the detection prompt
byte-identical with the gate on or off.

One expert story moved because of it: **Ketubot 103b** (`כשחלה רבי` — when Rabbi fell ill)
is found by the control at segs 14-15 and never proposed in the twin arm. Yevamot saw the
same shape and recorded it as a one-off (36b seg 13); two tractates in a row is a property,
not an accident.

**It does not overturn the result** — 7 of the 8 gained stories come from `twin_pass`
proposals, base churn nets +1/-1 — but it does mean **the +4.7 point headline carries an
unmeasured noise term**, and that a same-code repeat is now owed on any Ketubot comparison
smaller than this one (Lesson 22). The named-case table is the durable evidence here; the
headline is the softer number.

## What is not established

- **One run per arm**, and now known to be insufficient. The repeat is the next item.
- **The 16 non-listed additions are proposals, not errors.** They need a review page before
  `TWIN_PASS` becomes a default, and they are what `jeff:review-error-rate` prices.
- **Ketubot 111a seg 12 is unexplained.** It survived triage, sits one segment from a
  proposal, and neither arm proposes it.
- **Kiddushin's 3 and Gittin's 1** adjacent cases remain unmeasured.
- **Reach is still 1.** The 11 NEAR misses (2-6 segments) are untouched, and at least four
  of them have named non-reach blockers — Ketubot 77a is rejected by Classification,
  Gittin 38b and 57a are R-C4 and R-C3.

`TWIN_PASS` and `TWIN_TRIGGER` **stay default off.**
