# NEXT 09 — Fetch Gittin, Yevamot and Eruvin from Sefaria

**Self-contained.** Read `STATUS.md` and `FRAMEWORK.md` first.
**Capability: ground truth / prerequisite for everything on these tractates.**
**No LLM calls — pure I/O.** **Independent of every other brief.**

## Why now

Jeff sent expert story lists for three tractates we have never touched:
**Gittin 112 · Yevamot 102 · Eruvin 73.** Unlike the Kiddushin list, all three parse
cleanly with the existing `parse_expert_doc` — 0 English entries, same shape as Ketubot.

But a list is only useful against text. We have no Sefaria text for these tractates, so
nothing can be measured or run on them. Fetching is the prerequisite, it is cheap, and
it depends on nothing.

## Method

1. Follow `docs/golden/workflow/new_tractate_workflow.md` step 1 only — **fetch, do not
   run the detector.** Reuse the existing Sefaria client; do not write a new one.
2. Fetch the full daf range for each tractate, both Hebrew and English, in the same
   page/segment shape as `results/v10/wave4_notrim/*.json` (`pages[].segments[]` with
   `index`, `hebrew`, `english`).
3. Cache to `results/sefaria/{gittin,yevamot,eruvin}.json`. Never re-fetch what is cached.
4. Verify each tractate's daf range covers every reference in Jeff's list — if his list
   cites a daf we did not fetch, the range is wrong. Report any gaps.

## How you know it worked

Three cached files, and for each: number of dapim, number of segments, and a
confirmation that **every reference in Jeff's list resolves to a fetched page.** That
last check is the point of the task.

## Guardrails

- Fetch only. Running the detector on a new tractate is a separate, larger decision that
  should wait until Kiddushin shows what these lists are worth.
- Be polite to the Sefaria API — reuse existing rate limiting.
- Do not touch `results/v10/wave4_notrim/` — that is Ketubot and Kiddushin output.

## When done

Update the ground-truth block in `STATUS.md`. Note that `scripts/build_boundary_testset_2005.py`
can now build blind boundary sets for all three, since their lists already parse.
