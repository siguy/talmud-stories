# Gittin, detected for the first time — 100% loose / 96.4% strict, and the pipeline bug that nearly ate the run

**2026-08-31.** The first tractate this project has detected on since Kiddushin, and the
first ever measured against a blind list on the day it was run. Work item:
[`2026-08-31-gittin-detection-run`](../../work/done/2026-08-31-gittin-detection-run.md).

## The blocker, found before the spend

`run_pipeline()` Stage 4k called `self.extract_text_spans_via_llm(...)` — Wave 4's
char-offset mechanism, **removed from v11** when Wave 5's clause selection replaced it, as
that file's own docstring says at the top. With a client attached the pipeline raised
`AttributeError` at 4k: after Stage 1 triage, all of Stage 2 and the 4d/4f stitching calls.
On 178 pages that is the whole run, thrown away at the last step.

It survived because **v11 had never been run end to end.** Every v11 result on disk came
from `run_wave5_clause_spans.py`, which calls `extract_text_spans_via_clauses()` directly
on an existing output — so nothing had ever reached 4k with a client attached. Fixed, and
pinned by `tests/test_pipeline_stage4k_wiring.py`.

## The run

`python3 scripts/run_new_tractate.py --tractate gittin` — **20 minutes**, `gemini-3-flash-preview`,
few-shots from Ketubot only (cross-tractate, so no page being scored appears in its own
prompt — Lesson 2). Output: `results/v11/gittin/gittin_v11.json`.

| | |
|---|---|
| pages | 178 (Gittin 2a–90b, 2,990 segments) |
| Stage 1 | 88 skipped, 90 kept — **49% skip rate** (Ketubot 46%, Kiddushin 41%) |
| Stage 2 examined | **93** — the 90 kept plus 3 forced by the story-introducer override |
| proposals | 158; **147 stories**, 11 `NOT_A_STORY` |
| Stage 4 | 2 cross-page stories extended, 5 withheld by the Mishnah filter, 3 starts snapped, 1 end trimmed |
| spans | 59 narrowed, 84 kept full, 4 unsplittable, **0 failed** |
| structural gate | 69 cuts, **0 mid-word, 100% clause-edge**; `audit_text_spans.py --strict` passes |

**The span validator fired on its first live run.** Gittin 38a proposed `16..0`, a reversed
span on a 19-segment page — the same shape as `Ketubot 22a`, found by audit hours earlier.
It collapsed to `16..16` and is stamped `needs_review`, and the run file carries the repair
in `span_repairs`. Two days ago this would have sliced `segments[16:1]`, silently produced
an empty story, and left no trace.

## Recall against Jeff's blind list — quote the strict figure

112 stories, all blind, checked against the appendix.

| | loose | strict |
|---|---|---|
| **Gittin** | **100.0%** (112/112) | **96.4%** (108/112) |
| *Kiddushin, same method* | *93.3%* | *83.3%* |
| *Ketubot, same method* | *96.0%* | *87.9%* |

**100% is not the result.** The loose test credits a proposal anywhere in a search window
up to 14 segments wide; on Kiddushin it was shown to credit a *different passage on the
same daf* in 2 of 6 cases checked by name. `scripts/measure_strict_recall.py` applies the
ruler's own narrowing — a segment belongs to the story if either side is mostly the other
— without needing a golden or a review round, so a tractate can be measured strictly on
the day it is first run. It reproduces Kiddushin's banked 93.3% / 83.3% exactly, which is
what makes the Gittin figure comparable.

**The four loose-only cases were checked by name on 2026-09-01.** The loose window had
credited a neighbouring story on the same daf in every one — exactly the failure mode
STATUS warns about — so **108/112 is the figure that survives checking**.

**They are one thing, and it is not a bug.** Three of the four are passages where nothing
happens except speech or custom: the class Jeff's 2026-07-06 rule tells us to reject and
his 2005 list includes. Stage 1 labelled them `VERBAL_ACT` and `HABITUAL`, and Stage 2
rejected them as instructed. A same-code re-run of 57a reproduces both of its misses
exactly, so this is the rule and not nondeterminism (Lesson 22). **A targeted re-run cannot
recover a passage the classifier is correctly instructed to reject** — the only thing that
moves these is a ruling from Jeff, which is why they went into the email as evidence under
`jeff:speech-act-policy` rather than onto the board as defects:

| miss | Stage 1 label | why Stage 2 rejected it | kind |
|---|---|---|---|
| **38b** seg 6 — `אמר רבה: בהני תלת מילי נחתי בעלי בתים מנכסיהון` | `VERBAL_ACT` | a dictum; no event | **speech-act policy** |
| **57a** seg 12 — the exchange on the land of Israel's fertility | — | talk, no action | **speech-act policy** |
| **57a** seg 20 — `אשקא דריספק חריב ביתר` | `HABITUAL` | customary practice, not a single event | **speech-act policy** |
| **46b** — `פירקן…` in the redemption sugya | — | we propose segs 15-17; his unit starts at Rav Asi's ruling, seg 14 | **boundary standard** (Lesson 24) |

An earlier reading of this session called three of the four a second-story-on-a-page
coverage defect and pointed at `work/2026-08-30-second-story-guard.md`. **That was wrong**,
and the segment labels above are why: only 46b is a boundary case, and none is a coverage
gap. Drafted to Jeff as §0 of [`draft_next_email.md`](../../comms/draft_next_email.md).

**Triage lost nothing measurable:** 0 of the 112 sit on a page Stage 1 discarded, so
Detection *given the page survived triage* equals end-to-end here. The Mishnah filter
withheld 5 stories; 1 overlaps an expert entry, and **0 of the 5 are otherwise
undetected** — so nothing in the recall figure depends on that scope question.

## Read the comparison carefully

Gittin's strict 96.4% against Kiddushin's 83.3% is **not** a like-for-like improvement
claim. Three things differ at once: detector version (v11 vs v10 wave4_notrim), the
shipped triage rule (`N>=1`, which those runs predate), and the model. What is
measured is that **this pipeline, run today, finds 96.4% of a 112-story blind list it has
never seen** — the first number this project has produced on a tractate with no prior
contact of any kind. Attributing it to any one of the three changes needs a same-day
re-run of an old tractate (Lesson 22), which this did not do.

## What is not measured

No Classification precision and no Boundaries score — both need expert verdicts, and Jeff
has never reviewed a Gittin page. `report_mishnah_filter_delta.py` cannot run either: it
scores against a golden, and Gittin has none. **Ask him to keep any appendix of "stories
you and Claude found" separate before the first round** (Lesson 29) — once merged, the
list stops being able to measure what we missed.
