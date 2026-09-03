# The parallel-practice rule, measured: it does exactly what it was written for and costs nothing

**2026-09-03.** The rule shipped on 2026-09-01 (`7299db0`) **unmeasured** — the session
that wrote it had no `GOOGLE_API_KEY`. It has been live in the detector ever since,
carrying a stated prediction that it would *lose* points. Measuring it before running a
new tractate was the whole reason to run this now: otherwise the next tractate's numbers
confound a known change with an unknown one.

Full log: [`results/v11/parallel_rule/REPORT.txt`](../../results/v11/parallel_rule/REPORT.txt).

**The six arm outputs are deliberately not committed** — 13MB, and their conclusion is
"no effect, keep the base run", so they are not a ship point and nothing downstream reads
them. `REPORT.txt` carries every number, and the one command above regenerates the arms.
A reader who needs the spans themselves should re-run rather than trust a two-day-old
artifact of an arm we did not adopt.

```bash
python3 scripts/run_parallel_rule_experiment.py          # 3 arms + 3 same-code repeats
```

## The rule

A clause that merely notes a parallel practice — *"and so-and-so did the same"*, with no
events of its own — is not part of the story. But when the parallel material is itself a
**full incident**, it is a **second story**, not an aside: keep it. Nothing downstream
picks it up, so trimming deletes the passage outright, and a boundary that runs long is
recoverable by a reader while a deleted story is not.

## Measured — blind rulers, split by direction, with same-code repeats

| set | run | hit | hit+near | starts | ends |
|---|---|---|---|---|---|
| **Ketubot 2-60** | base | 80% | 85% | 88% / 94% | 72% / 76% |
| | **new** | **80%** | **85%** | 88% / 94% | 72% / 76% |
| | repeat | 80% | 85% | 88% / 94% | 72% / 76% |
| **Ketubot 61-112** | base | 80% | 84% | 84% / 89% | 75% / 78% |
| | **new** | **80%** | **84%** | 84% / 89% | 75% / 78% |
| | repeat | 80% | 84% | 85% / 89% | 75% / 78% |
| **Kiddushin** | base | 85% | 91% | 86% / 93% | 84% / 89% |
| | **new** | **85%** | **91%** | 86% / 93% | 84% / 89% |
| | repeat | 85% | 91% | 87% / 93% | 84% / 89% |
| *Corrections (CIRCULAR)* | base / new | 71% | 79% | 83% / 83% | 62% / 75% |

**Base and new are identical on every row.** The same-code repeats move by one target on
two of the three blind sets — so the noise floor here is **±1 target**, and the change is
**0**.

## And the five case checks all pass

| | |
|---|---|
| Ketubot 62a seg 7 — second story **kept** | PASS |
| Ketubot 105b seg 9 — second story **kept** | PASS |
| Ketubot 67b seg 3 — lookalike **still trimmed** | PASS |
| Ketubot 77b seg 11 — lookalike **still trimmed** | PASS |
| Kiddushin 72a seg 3 — lookalike **still trimmed** | PASS |

The rule does precisely what it was written to do, and the three lookalikes that would show
it keying on speech rather than events are untouched. The end-trim screen still finds 48
candidates at depth ≥4 — the candidate list did not balloon.

## The prediction was wrong, in the useful direction

The work item predicted: *"this change will probably cost points on the Ketubot end ruler,
and that may not mean it is wrong"*, because keeping a second story makes an entry end
**later** than Jeff's 2005 boundary, and the ruler scores later as wrong.

**It cost nothing.** The reason is worth stating: the two passages the rule rescues are not
scorable targets in the blind sets. The ruler cannot see the change at all.

That is the honest reading and it is a limitation, not a victory: **the instrument is blind
to the thing the rule fixes.** What the rulers prove is only that the rule breaks nothing
elsewhere — which was the real risk, and which the prediction said would be the hard part.
What proves the rule works is the five case checks, and those are five cases.

## Ranked item 3, folded in — the end axis

The end edge remains the weak one and this measurement re-confirms it with the numbers
side by side:

| | starts | ends |
|---|---|---|
| Ketubot 2-60 | **88%** | **72%** |
| Ketubot 61-112 | 84% | 75% |
| Kiddushin | 86% | 84% |

Ketubot's ends are **16 points** below its starts. Kiddushin's gap is 2. Whatever is wrong
is far more Ketubot than Kiddushin, which argues against a general end rule and for
something specific to that material — and it is the axis `jeff:boundary-end-rule` has
frozen, because his 2005 lists keep the ruling and his 2026 notes say cut it.

**No separate item is opened for the end axis.** It is not a measurement gap — it is
measured, here and in three prior findings. It is one unanswered question, and more
measurement will not answer it.

## What this unblocks

The parallel rule is now measured, so **the next tractate run is clean**: R-B1 (the opening
formula, +4-5 points) is the only change since Gittin with a measured effect, and nothing
live is unaccounted for.
