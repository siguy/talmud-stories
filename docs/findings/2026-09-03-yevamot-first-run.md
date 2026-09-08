# Yevamot, detected for the first time — 94.1% loose / 89.2% strict, and two crashes that ate the run twice

**2026-09-03.** The second tractate detected with no prior contact of any kind, measured
against Jeff's blind list on the day it ran. Work item:
[`2026-09-03-yevamot-detection-run`](../../work/done/2026-09-03-yevamot-detection-run.md).
Method identical to [`gittin-first-run`](2026-08-31-gittin-first-run.md) — same command,
same Ketubot-only few-shots (cross-tractate, Lesson 2), same two recall harnesses.

## The run

`python3 scripts/run_new_tractate.py --tractate yevamot` — **21 minutes** on the successful
attempt, `gemini-3-flash-preview`. Output: `results/v11/yevamot/yevamot_v11.json`.

| | |
|---|---|
| pages | 242 (Yevamot 2a–122b, 3,865 segments) |
| Stage 1 | 141 skipped, 101 kept — **58% skip rate** (Gittin 49%, Ketubot 46%, Kiddushin 41%) |
| Stage 2 examined | **106** — the 101 kept plus 5 forced by the story-introducer override |
| proposals | 190; **168 stories**, 22 `NOT_A_STORY` |
| Stage 4 | 10 trimmed, 5 cross-page extended, 8 withheld by the Mishnah filter, 2 starts snapped, 1 end trimmed, 27 starts extended over an opening formula |
| spans | 96 narrowed, 49 kept full, 1 unsplittable, **0 repairs** |
| structural gate | 126 cuts, **0 mid-word, 100% clause-edge**; `audit_text_spans.py --strict` passes |

**The 58% skip rate is the highest of the four tractates**, and Yevamot is also the
tractate with the lowest `NARRATIVE_EVENT` density on record (246 of 3,865 segments, 6.4%).
Triage lost nothing by it — see below — but the rate is worth watching as the sample grows.

## Recall against Jeff's blind list — 102 stories, every entry blind

| | loose | strict |
|---|---|---|
| **Yevamot** | **94.1%** (96/102) | **89.2%** (91/102) |
| *Gittin, same method* | *100.0%* | *97.3%* (111 after the retraction) |
| *Kiddushin, same method* | *93.3%* | *83.3%* |
| *Ketubot, same method* | *96.0%* | *87.9%* |

Quote the strict figure. Five stories are credited by the loose window only and are named
in `results/recall/yevamot_strict.json` — all five are in dense narrative runs (63a, 64b,
122a) where the window reaches a neighbouring story on the same daf, the failure mode
STATUS warns about. They want checking by name before anyone quotes 94.1%.

**Triage lost 0 of the 102** while examining 106 of 242 pages (44%). Detection *given the
page survived triage* therefore equals end-to-end here, as on Gittin: **every miss is
Detection's**, none is Triage's.

### The six loose misses

| miss | what it is |
|---|---|
| **14b** R. Yohanan b. Nuri on the co-wives | deliberation that ends in an enactment; no event |
| **34b** Rava to bat Rav Hisda — *"the rabbis are gossiping about you"* | a two-line exchange, pure speech |
| **63b** *"the Persians have come to Babylonia"* — R. Yohanan faints | 15 words, an event, and a real miss |
| **121b** x2 — the crier and the widow remarried by Rav Yosef | two `ההוא דהוה קאמר ואזיל` cases on one daf |
| **122b** the innkeeper | inside the Mishnah filter's territory — see below |

Three of the six (14b, 34b, and arguably 63b) are the **speech-act class**: talk without
action, which Jeff's 2005 list includes and his 2026-07-06 rule tells us to reject. This is
the same split Gittin produced and is the same evidence for the same open question,
`jeff:speech-act-policy` — not a defect to fix in the detector.

### Classification and the Mishnah filter, reported apart

- **3** located stories are covered only by a span this run classified `NOT_A_STORY`
  (61b, 85a, 91b). They count as FOUND above, because Detection proposes and does not
  judge — but they are Classification's to answer for once Jeff reviews the tractate.
- The Mishnah filter withheld **8** stories; 7 overlap an expert entry and **1 of those is
  otherwise undetected** (122b, the innkeeper). Unlike Gittin, where the answer was 0, the
  Mishnah scope question **costs one story of recall here**. Strict recall would be 92/102
  if that key were folded in.

## Two crashes, both of which threw away a full stage

Neither is a model failure; both are unhandled response shapes, and the Gittin lesson —
*v11 had never been run end to end* — repeated in a different place.

1. **Stage 1, page 228 of 242.** The model returned the segment index as a string; the
   bounds check `0 <= idx < len(segments)` raised `TypeError` and killed Stage 1 outright.
   The index is now coerced, and an unreadable one is dropped rather than raised.
2. **Stage 2, page 35 of 106.** A `PROHIBITED_CONTENT` finish came back with
   `candidates[0].content.parts = None` and iterating it raised. It now logs
   `EMPTY RESPONSE` with the finish reason and records it on the detector — a failed call
   must be visible, never silently converted into "no stories found" (Lesson 21).

**The Stage 1 crash cost 18 minutes of triage because the cache was written only after all
242 pages.** It now checkpoints every 10 pages, so a re-run resumes instead of restarting.
That is the durable fix: the bug will recur in some new shape, and the run should survive it.

**Stage 2 still has no checkpoint** — a crash there discards every page detected so far.
It did, twice today. Worth doing before Eruvin.

## What is not measured

No Classification precision and no Boundaries score: both need expert verdicts, and Jeff
has never reviewed a Yevamot page. `report_mishnah_filter_delta.py` cannot run either — it
scores against a golden, and Yevamot has none. **Ask him to keep any appendix of "stories
you and Claude found" separate before the first round** (Lesson 29).

The Gittin confidence-tier result (every `YES` on his list, monotonic ordering) is **not**
replicated here — it needs a per-proposal join the strict harness does not emit, and doing
it properly is its own item. Yevamot's label mix is 34 `YES` / 56 `HIGH` / 56 `LOW` / 22
`NOT_A_STORY`, so the material for that test is on disk.
