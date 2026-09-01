# The parallel-practice rule deletes second stories — sized, and the prompt split (2026-09-01)

**Status: the two measurements below are done and free. The prompt change they justify
is written but UNMEASURED — no `GOOGLE_API_KEY` in the session that made it, so the
Wave 5 re-run has not happened.** Do not quote a score for it. The gate is in
[`work/2026-09-01-parallel-story-rule.md`](../../work/2026-09-01-parallel-story-rule.md).

Capability 4 Boundaries. Companion to
[`docs/capabilities/4_boundaries.md`](../capabilities/4_boundaries.md).

---

## 1. The blind boundary score, split by direction — the aggregate was hiding this

`score_boundary_targets.py` reports one pooled number per run. Split by
`target['direction']` on the two **blind** 2005 rulers, same runs, same day:

| | starts | ends |
|---|---|---|
| **Ketubot** — Wave 5 clause spans | 85% / 90% (n=124) | **74% / 77%** (n=105) |
| Ketubot — untrimmed | 76% / 85% | 74% / **80%** |
| **Kiddushin** — Wave 5 clause spans | 86% / 93% (n=69) | 84% / 89% (n=61) |
| Kiddushin — untrimmed | 75% / 84% | 79% / 85% |

**Ketubot's entire deficit is end boundaries, and on that axis trimming is a net
loss** — 77% hit+near against untrimmed's 80%, with HIT identical at 74%. Trimming
earns its keep on starts (+9 points HIT on Ketubot, +11 on Kiddushin) and on
Kiddushin ends (+5). Ketubot ends are the one cell where it does not.

Two consequences:

- **`jeff:boundary-end-rule` is not a side question, it is the main one** — but the
  disagreement is smaller than first written here. **Correction, same day:** an
  earlier version of this line read *"the axis where his 2005 list and his 2026 notes
  disagree (starts agree 7/7, ends 16/19)"*, taking 16/19 for a disagreement count.
  [`kiddushin-boundary-set` §5](2026-08-31-kiddushin-boundary-set.md) counts
  **agreement**: on Ketubot his two sources agree on **7/7 starts and 16/19 ends** —
  so they disagree on **3 ends**, not 16. The same error sat in `comms/JEFF.md` and is
  fixed in #22.

  The direction of the argument survives and its magnitude does not: every stated
  disagreement between his two standards is on an **end**, and none is on a start — but
  that is 3 cases, and on Kiddushin the pattern does not reproduce (starts 2/3, ends
  8/11, on 14 shared boundaries). So the honest claim is that the end rule is
  **unsettled and unanswered**, not that his sources widely conflict. Until he answers,
  a movement on Ketubot ends still cannot be read as better or worse.
- **Anything proposed for boundaries should say which direction it targets.** The
  English-as-context idea from [`PLAN-wave5`](../history/2026-08-28-PLAN-wave5.md) is
  measured at 6/8 on ends and **0/8 on starts** — so its known signal lands on the
  contested axis and is uninformative on the clean one. That is not a reason to drop
  it; it is a reason not to run it until the end rule is settled.

*Method: `scripts/score_boundary_targets.py --by-direction`. No API calls.*

## 2. Sizing the second-story deletion — 2 of 50, not 13 of 50

[`work/2026-08-30-second-story-guard.md`](../../work/2026-08-30-second-story-guard.md)
was written from two cases. Lesson 18 says a sample locates a defect and never sizes
it, so `scripts/screen_end_trim_depth.py` counts every end-trim in the three shipped
v11 runs by depth. Structural only — no lexical rule, no model.

```
end-trims                       50
depth >= 4 (candidates)         13   (26%)
judged by eye a second story     2   ( 4%)   Ketubot 62a seg 7, 105b seg 9
```

**Depth over-selects about 6x, and the false candidates are the dangerous kind.**
Four of the 13 are **amoraic legal debate** — Ketubot 67b seg 3 (`לִיטְרָא בָּשָׂר מַאי
רְבוּתָא? אָמַר רַב הוּנָא`), 77b seg 11 (`אָמַר אַבָּיֵי ... אֲמַר לֵיהּ רַב אַדָּא בַּר מַתְנָא`),
Kiddushin 72a seg 3 (a chain of attributions), and in part Ketubot 60b seg 9. They
carry **names and dialogue**, and the prompt trims them correctly today.

**This changed the fix.** A first draft of the new rule said a parallel is a second
story when it has *"its own characters and its own events or dialogue"* — which
describes all four of those, and would have kept them. That is Jeff's Wave 3
complaint in mirror image: *"crude criteria, such as the word אלא or a rabbi's name
automatically signalling the story's end."* The shipped wording keys on **events**
and adds a second line naming amoraic debate as the case that looks like narrative
and is not.

**The screen independently surfaced Kiddushin 12a seg 13** (depth 4), the subject of
the open [`kiddushin-12a-dedup`](../../work/2026-08-30-kiddushin-12a-dedup.md) item —
two stories in one detection. The two items are the same family seen from opposite
ends.

## 3. The change

`src/story_detector_v11.py`, `_TEXT_SPAN_PROMPT_TEMPLATE`. One rule became two:

- a **bare mention** of a parallel practice is trimmed, as before;
- a parallel that is a **full incident — someone does something, events happen to
  named people** — is a second story and is kept, because nothing downstream picks up
  the discarded clauses and an over-long boundary is recoverable by a reader while a
  deleted story is not;
- **judge on events, never on names or speech** — amoraic debate about the story is
  not a second incident however much dialogue it carries.

## 4. What this fix is not

It produces a **merged entry**, not two stories. The text becomes visible again
inside story one; correct separation would need two stories to share one segment,
which the segment-indexed detector cannot represent. That is a Detection change and
is out of scope here.

It is also the cheap attempt at the outcome
[`second-story-guard`](../../work/2026-08-30-second-story-guard.md) proposes via a
~40-line clause-role labeller. If the prompt cannot hold the distinction, that item
is the answer — and will have earned it against a measured alternative rather than
by assumption.

## 5. Correction to a claim made in this session

An earlier reading treated the ~87% / 88% clause-edge ceiling as a cap on the
boundary **score**, and reasoned that only ~7 points of Ketubot HIT were reachable.
That is wrong. `build_boundary_testset_2005.py` records `clause` as the index of the
clause **holding** Jeff's letter position, so all 294 Ketubot and 176 Kiddushin
targets are scored; `exact_clause_edge` (257/294, 154/176) records only how
character-exact a *displayed* boundary could be. The ceiling bounds display fidelity,
not the score, and the two must not be subtracted from one another.
