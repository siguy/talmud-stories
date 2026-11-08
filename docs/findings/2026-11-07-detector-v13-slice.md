# Detector v13 on the Yevamot slice, beside v11 — 2026-11-07

**Recommendation: do not run Eruvin on v13 as it stands.** On the 20-page slice it finds
one fewer of Jeff's list stories than v11, makes two errors v11 does not make (a biblical
episode and a piece of Gemara commentary, both kept as stories), merges two incidents into
one, and the 2026-10-25 lines pull one case-before-a-rabbi passage *in* as borderline,
the opposite of what they were written for. A third arm (§ "Third arm") puts each of these
on the 2026-10-07 or the 2026-10-25 wording. All of this is **indicated**: two runs per arm,
the same day.

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

## Third arm — which wording does what

**v12wording** = v11 code + v12's 2026-10-07 lines only, no 2026-10-25 lines: the v13 file
as of commit `df29904` (step 1), loaded from a scratch copy by a scratch copy of the runner
(neither committed; `SERIES_RULE` is still in that file but off, so its prompt is the
step-1 prompt). Same slice, same config, same day, two runs side by side, scored the same
way; Stage 1 cache byte-identical before and after. Its `run_meta.git_rev` reads `1ea3c2e`
because the PR branch moved while it ran; the module it ran is the `df29904` file
regardless.

| arm | run 1 | run 2 | mean recall | spread | proposals | span repairs |
|---|---|---|---|---|---|---|
| v11 | 35/36 | 35/36 | 97.2% | 0.0 | 41.5 | 0 |
| v12wording | 35/36 | 35/36 | 97.2% | 0.0 | 41.0 | 0 |
| v13 | 34/36 | 34/36 | 94.4% | 0.0 | 41.0 | 0 |

Each passage, the six runs in order v11 r1, r2 · v12wording r1, r2 · v13 r1, r2
(Y / H / L / N = YES / HIGH / LOW / NOT_A_STORY, – = not proposed):

| passage | v11 | v12wording | v13 | introduced by |
|---|---|---|---|---|
| 78b:13–20 David and the Gibeonites (R-S1 error) | N N | N **H** | **Y Y** | **both**: the 10-07 wording starts it (1 of 2 runs drops "Biblical narrative"), the 10-25 lines make it 2 of 2 and YES |
| 105b:14–15 Gemara commentary (R-B4 error) | – – | **L L** | **L L** | **the 2026-10-07 wording** |
| 90b:9 + 90b:10 merged into one | L+L L+L | **H H** | **H H** | **the 2026-10-07 wording** |
| 78b:9 R. Eliezer's question and answer (list story dropped) | L L | L L | **– –** | **the 2026-10-25 lines** |
| 65b:12 case before R. Yoḥanan, he orders a divorce | – Y | – – | **L L** | **the 2026-10-25 lines** add it as borderline |
| 63a:13, YES → HIGH | Y Y | H H | H H | the 2026-10-07 wording (confidence only) |
| 34b:6, YES → HIGH | Y Y | Y Y | H H | the 2026-10-25 lines (confidence only) |

Moved in one run of an arm only, not read: 115b:1, 45b:8, 57a:6, 57a:12 (v12wording r1),
120a:10, 84a:2, 65b:14–15, 121b:5.

## What this says

1. **No single sentence is to blame.** The two errors and the merge come mostly from
   v12's 2026-10-07 wording; the list-story drop and the 65b:12 addition come from the
   2026-10-25 lines. Within each block, which sentence does it is **suspected, not shown**:
   no arm here removes one sentence at a time.
2. **The 2026-10-25 lines moved two passages, both the wrong way or unproven.** They drop
   78b:9, which R-C2 supports and Jeff has not ruled on (now `jeff:question-and-answer`).
   And they *add* 65b:12 as borderline — a case brought to a rabbi who orders the husband
   to divorce: by his 2026-10-25 words, an order is not a change (*"not really stated
   explicitly"*), so the rule says `NOT_A_STORY`. **The likely cause is our wording, not
   his:** step 2 wrote *"he allots, hands over **or enforces** something"* for his
   *"apportions"*. "Enforces" is ours, and an ordered divorce is exactly an enforcement.
3. **The 2026-10-07 errors line up with two of its sentences** (suspected): 105b:14–15 is
   the Gemara discussing an incident the Mishnah tells in full, which matches the R-C6 line
   (*"an incident the Talmud only ALLUDES to as evidence… reconstruct from context →
   LOW_CONFIDENCE"*) — and v12wording gives it exactly `LOW_CONFIDENCE`. David matches the
   R-C0 *"Contrast: an incident that happened… followed by a ruling IS a story"*, which
   says nothing about who the actors are.

## Recommendation

**Do not ship v13 for Eruvin, and do not keep the runner on v13 by default** until a v14
is measured. v11 stays the measured detector on this evidence; it carries none of the
October rulings, but on this slice it makes fewer errors the register can name.

**Proposed v14 (not written)** — three one-line edits, one per suspected sentence, each
small enough to revert alone. Ranked by how directly the evidence points at it:

1. *2026-10-25 borderline line* — `he allots, hands over or enforces something` →
   `he himself apportions or hands over something`. Drops our word "enforces"; restores his.
   Target: 65b:12 back out.
2. *R-C6 line (2026-10-07)* — append: `This is not an incident told in full elsewhere (in
   the Mishnah, or earlier on the page) that the Gemara only discusses: that is commentary
   on a story, not a story (R-B4).` Target: 105b:14–15 out.
3. *R-C0 contrast (2026-10-07)* — `an incident that happened (someone stole, sold, fled, was
   injured…)` → `an incident that happened to rabbis or post-biblical figures (someone
   stole, sold, fled, was injured…)`. Target: 78b:13–20 back to `NOT_A_STORY`.

Measure v14 the same way (two v14 runs and two v11 runs, same slice, same day); read 78b:13–20, 105b:14–15, 65b:12, 90b and 78b:9 by name. The 90b
merge has no candidate sentence yet. 78b:9 waits on Jeff: `jeff:question-and-answer` in
`comms/JEFF.md`.

## Files

- `results/v11/v13_slice/{v11,v12wording,v13}_r{1,2}.json` — the six runs; `*.score.json` — recall per story
- `slice.txt` — the 20 refs
