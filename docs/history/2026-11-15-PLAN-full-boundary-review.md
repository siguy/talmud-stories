# PLAN: review the boundaries of every story on the site

Date: 2026-11-15. Status: plan, not started. Drafted by a Fable planning agent. Owner decisions are in the last section.

## What this is for

The site shows 1,792 stories in 37 tractates. Many carry legal argument before or after the story (Simon: "we don't need the legal argument"), and some are cut off or split across two cards. On 2026-11-15 the 154 stories a note-drafter had flagged were reviewed (run `bfix1`; `work/done/2026-11-15-shas-background-notes.md`). This plan reviews the rest the same way.

Everything here is display only. It writes `site/data/boundary_extensions.json` and the merge list in `results/shas_run/septimus_site_decisions.json`. It never touches `results/canonical/*`, `scripts/evaluate_golden.py`, the detector runs or story ids, and it never uses the composite score.

## 1. Scope

- **Review all 1,792 stories**, minus the 148 that `bfix1` already decided (see Decision 3). That leaves about 1,640.
- **The three tractates with Jeff's golden (Ketubot, Kiddushin, Gittin; 246 stories) are reviewed too, but first and separately.** They are the only place we can check the reviewer against an expert, so they are the calibration set. Their decisions are then applied like any other, because the change is display only and `bfix1` already trimmed stories there.
- **Yevamot (84 stories) joins the calibration set.** Its site boundaries come straight from the detector, like the other 33 tractates, and Jeff's 2005 list exists for it. It is the closest test of the real job.
- The main run is therefore about 1,340 stories in 33 tractates.

## 2. Changes to `scripts/review_site_boundaries.py`

- [ ] **Export any set of stories.** Add `--all`, `--ids-file` and `--only <tractate>` (same names as `draft_site_notes.py`). The "Drafter's concern" line appears only when there is one.
- [ ] **Skip what is already decided.** `--after bfix1` leaves out every id in that run's `decisions.json`. A run name can still be exported only once.
- [ ] **Say the limits in each story file.** The real limits are 2 back and 6 forward from the *original* span. Each file gets one line: "You may start no earlier than [n] and end no later than [m]."
- [ ] **Re-deciding a story that already has an extension.** The reviewer sees the story as the site shows it now. "Keep" leaves the entry alone. "Adjust" replaces the entry with the new numbers. **Bug to fix:** an adjust back to exactly the original span currently leaves the old entry in place; it must delete it.
- [ ] **Refuse, by name, instead of breaking the build or skipping silently:**
  - an adjust on a card that is part of a merge (the site build stops on this today);
  - two stories whose new ranges would share a segment;
  - a merge where the other card's own review said keep or adjust (goes to the second reader);
  - a merge that would join a third card to an existing pair.
- [ ] **`apply --dry-run`** prints the plan and writes nothing. **`apply --hold <file>`** leaves out ids the second reader rejected.
- [ ] **Write `applied.json`** per run: before and after for every changed id, so a run can be undone.
- [ ] **`calibrate --run <r> --targets <files>`** scores a run's decisions against the expert lists (step 3). It reads decisions only and applies nothing.

`build_site_data.py` needs no change.

## 3. Calibration, before the full run

**What we can measure.** Jeff's 2005 lists give the first and last segment of each of his stories. Today 204 of his stories sit wholly inside one site card (Ketubot 78, Kiddushin 45, Gittin 81). Of those, 175 cards match him exactly at segment level, and the other 29 carry 78 extra segments in total (Ketubot 54, Kiddushin 4, Gittin 20). The reviewer never sees these lists. Target files: `tests/expert_boundary_targets_2005.json` (Ketubot), `..._kiddushin.json`, `..._gittin.json`.

Steps:
- [ ] Build the Yevamot target file with the existing `build_boundary_testset_2005.py` (`--expert-json results/expert_lists/yevamot_2005.json --tractate Yevamot --out tests/expert_boundary_targets_2005_yevamot.json`). Recount the figures above with Yevamot added.
- [ ] Export and review **Ketubot only** (86 stories, 5 batches). Run `calibrate`. If the prompt needs changing, change it here and re-run Ketubot under a new run name.
- [ ] Freeze the prompt. Review **Kiddushin, Gittin and Yevamot once** (244 stories, 13 batches). Do not tune on these; if they fail, stop and ask Simon.

What `calibrate` reports, per tractate and overall:
- **A. Starts kept:** his first segment is still shown.
- **B. Ends kept:** his last segment is still shown. Every end the reviewer cut is read by hand and sorted into: discussion his 2005 list ran on into (fine under rule R-B2 in `docs/STORY_RULES.md`: for ends the 2005 list is an upper bound), a ruling (the open question `jeff:boundary-end-rule`), or narrative lost (a defect).
- **C. Left alone:** of the cards that already match him exactly, how many the reviewer kept.
- **D. Benefit:** how many of the extra segments were removed. Information only.

**Go / no-go** (on the frozen prompt, the three hold-out tractates and Ketubot together):
- Narrative lost (A plus the defect pile of B): **at most 2%** of expert stories (4 of 204 before Yevamot is added), and no tractate above 5%.
- C: **at least 90%** kept unchanged.
- Zero invalid answers left after one retry of a failed batch.
- If any line fails: no full run. Report the cases to Simon.

Rulings cut at the end are counted and shown to Simon, not scored (Decision 2).

## 4. The full run: size and cost

- Batches of 20 stories, one subagent each, as in `bfix1` and the notes run.
- Calibration: 18 batches. Main run: about 67 batches. Run in waves of at most 20 at once (4 waves).
- Each story file is about 10 KB. The main run is about 13 MB of text, roughly 5-6 million tokens read; calibration adds about 1.5 million.
- With the second reader (step 5) and note redrafts (step 6), expect 115-130 batches and 10-13 million tokens in total. The redraft share depends on how many stories change; the calibration rate gives the estimate before the main run starts.
- [ ] After each wave run `import`; re-run any batch with missing or wrong-code answers once; whatever is still invalid is listed and not applied.

## 5. Second reader, before anything is applied

An independent subagent sees each story before and after, without the first reviewer's reason, and answers: is the "after" a complete story, was any of the story lost, is legal argument still there?

- [ ] Reads **every** one of: trims that remove half or more of a story, all merges, all merge disagreements, every change in the four calibration tractates that cuts an expert segment.
- [ ] Reads a **random 100** of the remaining adjusts and a **random 40** keeps (to see how many cut-off stories the reviewer missed).
- [ ] Gate on the random 100: up to 10% disagreement, apply everything except the disagreed ones (held and listed). 10-20%, second-read every adjust first. Over 20%, stop.
- [ ] `apply --dry-run`, then `apply --hold <rejected ids>`, then `python3 scripts/build_site_data.py`.

This needs a small export/import pair in the same script, in the same file shape.

## 6. Notes

A note must be redrafted when its story's text changes. Existing tools only:
- [ ] `draft_site_notes.py export --run bfull1notes --ids-file <run>/changed.txt`, subagents, `import`. Before export, mark those notes `drafted: "boundary-changed"`, `approved: false` (as done for `bfix1notes`) so the builder takes the new draft whole.
- [ ] `build_site_notes.py <all earlier parts dirs> results/site_notes/bfull1notes/parts`.
- [ ] Merged cards get a written summary in `site_summaries_written.json`, as in `bfix1`.
- [ ] `approve_notes.py --all --unflagged` (Decision 5). Report approved and held counts from `build_site_notes.py --report`.

## 7. Tests

- [ ] `tests/test_site_data.py`: update the five pinned word counts in `SITE_WORDS` with a dated comment (and §2 of `docs/technical/septimus-signup-plan.md` if it quotes them). The story-count, removal and merge tests read the decisions file; confirm they follow.
- [ ] New tests for the script: `--all` exports every site id exactly once minus the skip list; an adjust back to the original span deletes the entry; an adjust on a merged card is refused; overlapping ranges are refused; `calibrate` gives the right counts on a tiny fixture; a second `apply` of the same run changes nothing.
- [ ] `tests/test_site_notes.py` still passes (every story has a note).
- [ ] `python3 -m pytest tests/ -q` before stopping.

## 8. Housekeeping

- [ ] Copy `work/_TEMPLATE.md` to `work/2026-11-15-full-boundary-review.md`, fill in `writes:`, run `python3 scripts/board.py lanes`.
- [ ] At the end: finding in `docs/findings/`, `## Outcome`, `board.py finish`.

## Risks

- **The reviewer cuts real story.** Calibration and the second reader exist for this. Residual risk is in the 33 tractates with no expert list; Yevamot is the only stand-in.
- **Calibration is easier than the real job** in the three golden tractates, where boundaries are already Jeff's. Read Yevamot's numbers separately.
- **Trimming a ruling that makes the passage a story.** Jeff has not answered. Display only, and `applied.json` makes it reversible.
- **Flip-flopping.** Re-reviewing a decided story can reverse it and force a second note redraft. Hence the skip list.
- **Notes churn.** Every changed story loses its approved note until redrafted. Do not publish between apply and note approval.
- **Splits are still impossible.** Two incidents joined in one card cannot be separated; these stay held, as the ones from `bfix1` do.
- **Cost overrun** if the change rate is high. Known after calibration, before the main run.

## Decisions for Simon

1. **May Jeff-validated stories (Ketubot, Kiddushin, Gittin) be trimmed on the site?** Recommended: yes, display only, as `bfix1` already did; trims that cut a segment Jeff listed all go to the second reader.
2. **When a ruling ends the story, keep it or cut it?** Jeff's answer is open. Recommended: keep the ruling when it is the outcome of the events, cut the Gemara's discussion of it. You see the calibration cases before the full run.
3. **Re-review the 148 stories `bfix1` decided?** Recommended: no. The catch is that any early `bfix1` mistakes stay.
4. **The go/no-go numbers** in step 3 (2% narrative lost, 90% left alone) and step 5 (10% / 20% disagreement). Recommended as written.
5. **Approval of redrafted notes.** Recommended: same rule as before, approved if checks pass and the drafter raised no flag.
6. **Do you want to read a sample yourself** (say 20 before/after pairs in the browser) before apply? Recommended: yes, after the second reader, before the main apply.
