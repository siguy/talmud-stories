# Kiddushin recall: Detection generalizes, Triage does not — 2026-08-31

**Capabilities: 1 Triage, 2 Detection.** **Status of every number below: measured**, on
`results/expert_lists/kiddushin_2005.json` (**BLIND**) against
`results/v10/wave4_notrim/kiddushin_v10_notrim.json`. No API calls; no detector was run.

Fills the Kiddushin **Triage** cell, which has read "unmeasured" for the life of the
project, and re-derives the Kiddushin **Detection** figure through a second, independent
script.

**The result in one line:** Kiddushin's end-to-end recall is 2.7 points below Ketubot's,
and **none of that gap is Detection**. Detection, measured on pages that survived triage,
is 97.7% on Kiddushin against 97.9% on Ketubot — a difference of one story. The whole gap
is **Triage**, 95.6% against 98.0%.

---

## 1. The numbers

Same script both sides, run today (Lesson 11). Ketubot's published 96.0% / 98.0% / 44%
reproduce exactly, which is what licenses the comparison.

| | Ketubot | Kiddushin |
|---|---|---|
| blind denominator | 149 | **90** |
| pages examined | 98 / 222 (**44%**) | 62 / 162 (**38%**) |
| **1 Triage — stories surviving** | **98.0%** (146/149) | **95.6%** (86/90) |
| **2 Detection — given the page survived** | 97.9% (143/146) | **97.7%** (84/86) |
| end-to-end, loose | **96.0%** (143/149) | **93.3%** (84/90) |
| end-to-end, strict (`results/rulers/`) | 87.9% | 83.3% |
| …and surviving Classification to reach output | 96.0% (143) | **91.1%** (82/90) |

`triage × detection = end-to-end` (FRAMEWORK §2b) holds on both: 0.980 × 0.979 = 0.960,
and 0.956 × 0.977 = 0.934. The framework asks that this composition be **re-checked**
rather than assumed after its single Ketubot check. It now holds on two tractates.

**Reproduce:**

```bash
python3 scripts/measure_recall_vs_expert_list.py \
  --expert-json results/expert_lists/kiddushin_2005.json --expert-filter recall \
  --detected results/v10/wave4_notrim/kiddushin_v10_notrim.json \
  --golden results/canonical/kiddushin_canonical.json --tractate Kiddushin \
  --out results/recall/kiddushin_jeff2005_matches_recall.json
```

## 2. The denominator, and why 90 rather than 89

The brief for this work said 89 and told us to use the file's own `recall_denominator`.
Those are two different numbers — `recall_denominator` is **90** — because the brief
predates
[`appendix-provenance-correction`](2026-08-30-appendix-provenance-correction.md), which
separated *blind* from *counts for recall*. 90 is used here, and the other two readings
are reported so the choice can be seen rather than trusted:

| filter | n | end-to-end | triage | detection |
|---|---|---|---|---|
| `--expert-filter recall` (`counts_for_recall`) | **90** | **93.3%** | **95.6%** | **97.7%** |
| `--expert-filter blind` (`blind`) | 89 | 93.3% | 95.5% | 97.6% |
| `--expert-filter all` (everything but the duplicate) | 94 | 93.6% | 95.7% | 97.8% |

**The denominator choice moves nothing** — 0.3 points across the full range, and every
conclusion below is identical under all three. That is worth recording, because the
provenance argument that produced 90 was expensive and contentious (Lesson 29), and it
turns out not to have been load-bearing for the headline. It remains load-bearing for
*which stories* count, which is the part that matters for the miss analysis in §4.

## 3. Triage is where Kiddushin loses, and it is a trade

**Kiddushin examines 38% of its pages; Ketubot examines 44%.** Kiddushin skips more, and
pays for it: 4 of Jeff's 90 stories are lost outright against Ketubot's 3 of 149.

|  | Ketubot | Kiddushin |
|---|---|---|
| stories touching a discarded page | 19 | 14 |
| …surviving because the other half of the daf pair was kept | 16 | 10 |
| …**lost outright** | **3** | **4** |

Per FRAMEWORK §1.1 the exchange rate is the point, not the recall figure alone.
**Kiddushin buys 6 more points of pages skipped for 2.4 more points of triage recall** —
roughly one story per 1.5 points of corpus not examined. Whether that is a good trade is
the open product question for Simon (FRAMEWORK §2b), not a defect to patch. It does say
that the single 98% gate was set on the tractate that happens to skip less.

**All four Kiddushin losses have the same shape as Ketubot's three:** every page the
story's text occupies was discarded, so no Stage 2 prompt could have reached it.

| | Jeff's ref | text sits on | both discarded? |
|---|---|---|---|
| `kiddushin_005` | 10b | 10a + 10b | yes |
| `kiddushin_011` | 14a | 13b + 14a | yes |
| `kiddushin_012` | 21b | 21b | yes (21a too) |
| `kiddushin_070` | 69a | 68b + 69a | yes |

### 3a. The Wave 1 lexical override is worth one story here — measured for the first time

The shipped skip decision is the one *after* Wave 1's story-introducer override, which
forces Stage 2 on a page carrying a canonical opener whatever Stage 1 said. Stage 1 alone
skips **109** of 162 Kiddushin pages; the shipped figure is **100**. The 9 recovered pages
are 7b, 26a, 42a, 43a, 45a, 49b, 51a, 53a, 69b.

**One of the 90 sits on a page only the override kept** — `kiddushin_053` (Kiddushin 49b),
and it is found. Without the override Kiddushin triage recall would be **85/90 = 94.4%**
instead of 95.6%. The override's previously recorded wins (45a, 53a) are appendix cases
and sit outside this denominator, so this is the first time it has been priced against a
blind set: **+1.1 points of triage recall for 9 extra Stage 2 calls.**

## 4. The two Detection misses, and two Classification rejections kept apart

Of the 6 end-to-end misses, 4 are triage (§3). **Two are Detection misses** — the page was
examined and Stage 2 proposed nothing in range:

- **`kiddushin_016`, Jeff's 26a** (window 26a:8 – 26b:1). Opens `איבעיא להו` — a legal
  question frame, not a narrative opener. Note 26a is one of the 9 pages the *override*
  rescued, so triage did its job and detection still missed it.
- **`kiddushin_094`, 81b** (window 81b:4–10, 100% text alignment). Rav Hanan of Nehardea
  visiting Rav Kahana. **This is not the 81b case already on record**: that one is
  `kiddushin_093` (R. Meir / R. Tarfon, segs 3–9), an appendix entry. **Kiddushin 81b
  carries two of Jeff's stories, and prior documents discuss only one.**

**Separately, and never inside the recall figure: two stories are covered *only* by a span
this run classified `NOT_A_STORY`.** Detection proposed them; Classification threw them
away (FRAMEWORK §1.2, Lesson 30):

- **44a** — `ר' אסי לא על לבי מדרשא` (R. Assi did not go to the study house)
- **58a** — `בעא מיניה ר' חייא בר אבין מרב הונא` (R. Hiyya b. Avin asked R. Huna)

Both are rabbis-in-conversation passages, which is exactly the material sitting under the
open `jeff:speech-act-policy` question. Neither is in our golden. **They are why the
Kiddushin figure that reaches output is 91.1%, not 93.3%** — Ketubot loses nothing this
way. Ketubot's own equivalents (20a, 53a) were rejected as `NOT_A_STORY` by *other* runs,
not this one, which is why the same script shows 0 for Ketubot here.

## 5. What this changes

**The scoreboard has been reading the Kiddushin deficit in the wrong column.**
[`2_detection.md`](../capabilities/2_detection.md) records Kiddushin as "93.3% loose —
**below the 95% gate where Ketubot is above**", framed as the first like-for-like
comparison of the two tractates. It is like-for-like on the *end-to-end* number, which
bundles Triage. Split, Detection is **97.7% vs 97.9%** — indistinguishable, on a
difference of one story, and both far above the 95% gate. Kiddushin's deficit is Triage's,
and Triage on Kiddushin has never been measured until now.

**Detection generalizes across tractates; that is the finding.** It is the first evidence
either way, since Ketubot was the only blind list the project had. It is also weaker than
it looks in one specific respect: the *loose* test is doing work on both sides
(96.0→87.9 and 93.3→83.3 strict), so what generalizes is demonstrated at the loose end.
Whether the strict gap generalizes is a separate question and this measurement does not
answer it.

**Caveats, stated as such.** (a) One run per tractate; recall has no measured noise floor
(Lesson 22), and this model is known to move ~3% of its own outputs between identical
runs. (b) The loose window over-credits — `kiddushin_093` at 81b is the project's proven
case, credited on segments 1–3 for a story at segment 9. (c) `ref` labels come from Jeff's
list; the ruler labels the same six misses 10a/13b/21b/26a/68b/81b from the located
window. Same six stories.

## 6. What the script now does

`scripts/measure_recall_vs_expert_list.py` gained three things, all additive — the
Ketubot `--expert-doc` path is unchanged and reproduces 96.0% / 98.0% / 44% exactly, which
was verified before any Kiddushin number was read:

- `--expert-json` / `--expert-filter`, so a pre-parsed list is used instead of re-parsing
  a `.doc` (Lesson 28 — the line parser returns 105 entries on this document).
- **Triage recall**, which had no committed script at all. The published 98.0% was
  computed by hand while writing FRAMEWORK (`c900ee4`); it is now reproducible, and it
  reproduces — along with Ketubot's 19 / 16 / 3 triage exposure breakdown.
- The **cause split** — triage-discarded vs examined-and-nothing-proposed — and the
  `NOT_A_STORY` overlay reported apart from both.
