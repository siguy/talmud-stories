# STATUS — where the project is today

**Last rewritten: 2026-08-30 (evening).** Rewritten every session, never appended.
Read this first. Companion: [`FRAMEWORK.md`](FRAMEWORK.md) — how we measure and what
counts as good enough. Language and capability names come from there.

---

## The headline

**Jeff sent expert lists for four more tractates** (`jeff comms/8-30-2026/`), with:
*"I will get to all this soon. But here is the kiddushin list I have."* — so **the
boundary question is still unanswered** and capability 4 stays blocked.

Rough parse: **Gittin 112, Yevamot 102, Eruvin 73** — indicated, not measured.
**Kiddushin is now parsed properly: 95 stories, measured** (`NEXT/05` done). The rough
figure was 105, of which 9 were Jeff's own English review comments and 4 were
parallels-column citations. 81b no longer appears to hold 11 stories; it holds 4.
→ [`docs/golden/v11/kiddushin_list_parse_2026-08-30.md`](docs/golden/v11/kiddushin_list_parse_2026-08-30.md)

Why it matters: a **blind** dataset is one the detector had no hand in creating, so it
can measure *recall* — what we never found. We had exactly one (Ketubot, 149 stories).
Kiddushin now has one too, so three scoreboard cells that read "unmeasured" for the life
of the project are unblocked — **06, 07 and 08 are ready to run.**

One correction to yesterday's reading: `הוספתי--י.ר.` marks **one** entry Jeff added in
2026, not stories taken from our output. The contamination that exists runs the *other*
way — five entries are stories he told us in April we had missed, so counting them
biases recall **down**. Recall must be quoted over both denominators, **89 and 94**.

## Scoreboard — capabilities per [`FRAMEWORK.md`](FRAMEWORK.md) §1

| capability | metric | Ketubot | Kiddushin | gate |
|---|---|---|---|---|
| **1 Triage** | stories surviving | **98.0%** at 44% of pages | unmeasured → **ready, `NEXT/06`** | ≥98% *(provisional)* |
| **2 Detection** | recall, BLIND | **96.0%** | unmeasured → **ready, `NEXT/06`** | ≥95% *(provisional)* |
| **3 Classification** | precision, CIRCULAR | 86% *(Mar 2026, stale)* | 68% *(Apr 2026, stale)* | ≥85% *(provisional)* |
| **4 Boundaries** | hit / near, BLIND | **80% / 84%** (ceiling ~87%) | 60%/73% ±7pt, circular | ≥75% *(provisional)* |
| **5 Review** | days per tractate | not started | not started | days, not weeks *(derived)* |
| **6 Publication** | — | not started | not started | — |

**Four of five gates are provisional** — see FRAMEWORK §2b. They compose
(`triage × detection = end-to-end`), so only the end-to-end number needs defending, and
that is a product decision, not a technical one. Two questions are open there: one for
Simon, one for Jeff.

**The weakest capability is Classification, and we cannot currently see it** — both
precision numbers are from March/April on older detector versions. There is no current
measurement of the capability furthest from its gate.

## What changed today

- **Measurement became honest.** The boundary test set was built entirely from Jeff's
  corrections, so it could never reveal a boundary we had right and broke. Rebuilt from
  his blind 2005 list: **35 gradeable targets → 249**, run-to-run noise **7 points → 0**.
  → [`docs/golden/v11/boundary_ruler_rebuild_2026-08-30.md`](docs/golden/v11/boundary_ruler_rebuild_2026-08-30.md)
- **Boundary trimming is worth much less than claimed.** The old ruler said it doubled
  us on Ketubot 61-112 (33%→67%). The blind ruler says untrimmed was already 79% right.
  → [`docs/golden/v11/trim_asymmetry_2026-08-30.md`](docs/golden/v11/trim_asymmetry_2026-08-30.md)
- **Triage is a trade, not a defect.** 98% recall while examining 44% of pages. Worth
  pricing, not reflexively fixing.
- **The six recall misses split into two populations.** Five were missed *and* absent
  from our golden; one (Ketubot 77a) is in our golden and still never proposed — a
  **Detection** failure, since nothing was proposed at all, not even a rejected candidate.
  → [`docs/golden/workflow/recall_miss_diagnosis_2026-08-30.md`](docs/golden/workflow/recall_miss_diagnosis_2026-08-30.md)
- **A runner bug was fixed and guarded:** a failed API call could be recorded as a
  considered judgment. → Lesson 21, `tests/test_wave5b_runner_outcomes.py`
- **Wave 5b shelved.** Its trigger was measured on the biased ruler. Salvage list in
  `tasks/NEXT/03`.
- **Kiddushin has a blind list.** 95 stories, parsed from the .doc's own table structure
  rather than a converter's line dump; the parser reproduces Ketubot's established 149
  as its regression check, and all 95 texts match an independent renderer character for
  character. Jeff's 9 review comments came back with their **exact anchor positions**, so
  each attaches to the passage he was looking at — which is what makes them usable to
  `NEXT/08`. → Lesson 25

## Waiting on Jeff — email sent 2026-08-30

**The question:** when a ruling is what makes a passage a story at all, is that ruling
part of the story we display, or the discussion that follows it? His 2005 lists keep it;
his review notes say cut it. Blocks the end rule for capability 4.
→ draft: [`docs/golden/v11/email_jeff_2026-08-30.md`](docs/golden/v11/email_jeff_2026-08-30.md)

**To add when we next write:** at what error rate does reviewing our output become worse
than working from scratch? That number sets the Classification gate and only he can
answer it.

## Next — briefs in [`tasks/NEXT/`](tasks/NEXT/), each self-contained

**Lead with Kiddushin only.** It is the sole new tractate where we already have a mature
detector output (95 stories, a golden set, 8 review rounds), so its list pays off
immediately with zero API calls. Gittin, Yevamot and Eruvin have **no detector output at
all** — their lists are worth nothing until the detector runs there, which is a larger
job that should wait until Kiddushin shows what we get.

```
              ┌── 06 Kiddushin recall (triage + detection)
05 parse DONE ┼── 07 Kiddushin blind boundary set        all three now unblocked,
              └── 08 harvest the embedded review comments  and independent of each other

fully independent, start any time:   00 · 02 · 04
lower value until the above land:    01 · 03
```

| | task | capability | needs | Jeff? |
|---|---|---|---|---|
| ~~05~~ | ~~Parse the Kiddushin list~~ — **done**, 95 stories + 10 remarks | ground truth | — | no |
| **06** | Kiddushin recall: triage + detection — report over **both** denominators (89 / 94) | 1, 2 | — | no |
| **07** | Kiddushin blind boundary set (~190 targets, kills the ±7pt noise) | 4 | — | no |
| **08** | Harvest Jeff's **10** embedded remarks — criteria + boundary corrections | 3, 4 | — | no |
| 00 | Per-capability history: what we tried, reverted, current best | all | — | no |
| 02 | Why is Ketubot 77a never proposed | 2 | — | no |
| 04 | Fix the review UI Hebrew/English asymmetry | 5 | — | no |
| 01 | Price the triage trade over the 124 discarded pages | 1 | — | no |
| 03 | Stop discarding a second story sharing a segment | 4 | — | **blocked** |
| — | Wave 6 — encode Jeff's criteria (08 feeds it) | 3 | 08 | no |

## Where things live — one job each

| file | its one job |
|---|---|
| **`STATUS.md`** | where we are. Rewritten each session. **Start here.** |
| **`FRAMEWORK.md`** | the six capabilities, how each is measured, what the gates are and why. |
| `tasks/NEXT/*.md` | one self-contained brief per ready task. Delete when done. |
| `tasks/lessons.md` | 25 durable rules. Append-only. |
| `docs/golden/**` | dated findings. Immutable once written. |
| `docs/capabilities/` | per-capability history — **not written yet, see `NEXT/00`**. |
| `validation/feedback/jeff_*_ledger.md` | everything Jeff has said, and its disposition. |
| `CLAUDE.md` | how to work in this repo. Not status. |
| `FOR_SIMON.md` | the plain-English narrative. |

**The rule:** status here and nowhere else. Findings in a dated `docs/golden/` file.
Rules in `lessons.md`. Ready work in `tasks/NEXT/`. Never append status to a plan.

## Ground truth on hand

```
BLIND   (can measure recall)
  Ketubot    149 stories (2005 list) · 294 derived boundary targets
  Kiddushin   94 stories, MEASURED  -> results/expert_lists/kiddushin_2005.json
                 95 parsed, minus 1 Jeff marked as his own 2026 addition
                 recall denominator 89-94: five entries are stories he told us in
                 April we had missed, so counting them biases recall DOWN. Quote both.
                 ~190 boundary targets derivable (NEXT/07)
  Gittin 112 · Yevamot 102 · Eruvin 73   ← INDICATED only; each needs its own parse,
                                            and no detector output exists there yet
CIRCULAR (precision and consistency only — never recall)
  Ketubot   182 golden stories · Kiddushin 85
  70 boundary corrections across 8 review rounds
  10 Kiddushin review remarks, each anchored to its passage (NEXT/08)
```
