# Detector v13 on the Yevamot slice, beside v11 — 2026-11-07

**Recommendation: do not run Eruvin on v13 as it stands.** On the 20-page slice it finds
one fewer of Jeff's list stories, makes two errors v11 does not make (a biblical episode
and a piece of Gemara commentary, both kept as stories), and the 2026-10-25 rule it was
built to carry changes nothing that can be seen. All of this is **indicated**: two runs per
arm, the same day.

Item: [`work/done/2026-11-07-detector-v13-october-rulings.md`](../../work/done/2026-11-07-detector-v13-october-rulings.md).
Code: `src/story_detector_v13.py` = the fixed v11 (PRs #69–#71) + v12's 2026-10-07 wording,
byte for byte + the 2026-10-25 rulings (R-C0, R-C7 shape 2) + no `SERIES_RULE`, no
`skip_triage` alias. `tests/test_v13_code_is_v11_code.py` pins that only five functions
differ from v11, all of them prompt or version text.

## Configuration

| | |
|---|---|
| pages | `results/v11/v13_slice/slice.txt` — the 20-page Yevamot slice of `results/v11/twin_pass/` |
| model | `gemini-3-flash-preview`, thinking off, twin pass on (`TWIN_TRIGGER=all`) |
| Stage 1 | cached `results/triage/yevamot.json`, which covers all 20 pages; the file was byte-identical before and after (0 triage calls) |
| arms | **v13**: `scripts/run_new_tractate.py` as committed. **v11**: the same runner with its two imports pointed at v11 (scratch copy, not committed). Same git rev `65646da` |
| repeats | 2 per arm, the two arms run side by side, all four on 2026-11-07 |
| ruler | Jeff's 2005 Yevamot list, **BLIND** (no detector had run on Yevamot when he wrote it), `--expert-filter recall`, exact matcher, via `scripts/score_noise_floor_slice.py`. 36 list stories sit on these dapim; neither of the two he has since ruled out (107b, 45a, `superseded_by_rule.json`) is on the slice |

*Caveat on the slice:* the list is blind, but these 20 pages were used to tune the twin pass
in 2026-09, so the slice is not held-out data for the twin pass. It is held-out for the
October wording, which was written from Ketubot, Kiddushin, Gittin and two other Yevamot
pages (45a, 107b).

## Numbers (measured)

| arm | run 1 | run 2 | mean recall | spread | proposals | span repairs | Stage 2 errors | twin failures |
|---|---|---|---|---|---|---|---|---|
| v11 | 35/36 | 35/36 | 97.2% | 0.0 | 41.5 | 0 | 0 | 0 |
| v13 | 34/36 | 34/36 | 94.4% | 0.0 | 41.0 | 0 | 0 | 0 |

A zero spread on both arms says each arm repeated itself, not that one story is a
reliable difference: n = 2 and one story = 2.8 points (Lesson 43). So everything below is
read **by name**, and it is a story that moved in **both** runs of one arm and **neither**
of the other unless said otherwise.

Classification counts (`stories[]`): v11 L 21/21, Y 11/13, H 8/7, N 1/1; v13 L 20/19,
Y 11/10, H 9/12, N 1/0.

## The delta, by name

### List stories (BLIND ruler)

| story | v11 | v13 | Jeff's ruling | reading |
|---|---|---|---|---|
| `yevamot_051` Yevamot 78b:9 — the students ask R. Eliezer about a *mamzeret* after ten generations; he answers "who will give me a third generation…" | found, `LOW_CONFIDENCE`, 2/2 | **not proposed**, 0/2 | **none on this passage.** On his 2005 list | A question and its answer, nothing else. By R-C2 as settled on 2026-09-23 (speech, no conflict → not a story) and v12's "a challenge and its answer… is not a story", v13's call is the register applied. But Jeff has not ruled on it, and the brief's test is "not ruled on → wording defect". **Count it as a loss until he answers; it is a question for him, not a deletion** (principle: his lists are evidence, a rule that contradicts one is an annotation) |

No other list story moved. Nothing v13 dropped is one of his `not`s — the slice has none.

### Proposals not on the list (no ground truth — judged against the register)

| passage | v11 (r1, r2) | v13 (r1, r2) | reading |
|---|---|---|---|
| Yevamot 78b:13–20 — David, the three-year famine and the Gibeonites (II Samuel 21), retold | `NOT_A_STORY`, disqualifier "Biblical narrative" ×2 | **`YES`** ×2, no disqualifier | **v13 error.** R-S1 (Jeff 2026-09-23): biblical figures are out of scope. v11 applied it; v13 did not, in both runs |
| Yevamot 105b:14–15 — the Gemara's questions about the Mishnah's prison-ḥalitza incident before R. Akiva | not proposed | **`LOW_CONFIDENCE`** ×2 | **v13 error.** R-B4 (Jeff 2026-09-23): the Gemara's commentary on a story is not a story. The incident itself is the Mishnah's (R-C1) |
| Yevamot 90b:9 and 90b:10 — two separate court-flogging incidents | two stories, L + L ×2 | **merged into one**, H ×2 | v13 groups two incidents as one. The list story (`yevamot_058`, seg 9) is credited either way, so recall hides it |
| Yevamot 65b:12 — a woman's case comes before R. Yoḥanan in Caesarea; he rules the husband must divorce | absent / `YES` | `LOW_CONFIDENCE` ×2 | **The shape the 2026-10-25 rule is about** (a case before a rabbi and his ruling). If nothing else is narrated, the rule says `NOT_A_STORY`; v13 still says borderline. Jeff has not ruled on this passage |
| Yevamot 78b:11 (R. Ami's *mamzer*), 34b:6, 63a:13 | `YES`/`HIGH` | one grade lower ×2 | confidence only; all still kept |
| 65b:14, 65b:15, 84a:2, 120a:10, 121b:5 | — | — | moved in one v13 run only: noise, not read |

## What this says

1. **The 2026-10-25 change did not show up on the slice.** v13 sent no `LOW_CONFIDENCE`
   proposal to `NOT_A_STORY` in both runs, and the one passage of that shape on these pages
   (65b:12) stayed borderline. Either the shape is rare on these 20 pages or the wording
   does not bite. This slice cannot tell those apart — **indicated** that the rule is
   inert, not measured.
2. **v13 lost two disqualifiers that v11 applies** (biblical scope, Gemara commentary). The
   biblical disqualifier line is present in both prompts word for word; what changed is
   what surrounds it. Which of the ~40 added lines does it is **not known**: no arm here
   separates v12's wording from the 2026-10-25 lines. *Suspected*, not shown: the new
   "Contrast: an incident that happened… followed by a ruling IS a story" sentence, which
   pulls toward keeping incident-plus-response passages and says nothing about who the
   actors are.
3. **Recall: one story, which the register says v13 is right to drop** and Jeff has not
   ruled on. On its own that would not stop v13. Points 1 and 2 do.

## Recommendation

**Do not ship v13 for Eruvin as is.** It costs one list story (pending Jeff), adds two
errors that existing rules already forbid, and the rule it was built for has no visible
effect. v11 does not carry the October rulings, but on this slice it makes fewer errors
the register can name.

Before deciding, the cheapest next step is **one more arm on the same slice: v13 without
the step-2 lines** (v11 code + v12's wording only, from commit `df29904`). That splits the
two errors between the 2026-10-07 and the 2026-10-25 wording, and costs two runs (~10 min,
a few cents). If the errors come from one sentence, fix that sentence in a v14 and rerun
this comparison. Separately, 78b:9 should be added to `comms/JEFF.md` as a question (not done here): a question to a
sage and his answer — story, borderline, or not?

## Files

- `results/v11/v13_slice/{v11,v13}_r{1,2}.json` — the four runs; `*.score.json` — recall per story
- `slice.txt` — the 20 refs
