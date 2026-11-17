# Sign-up step c: independent review, 2026-11-15

One Opus reviewer read `septimus/signup-b..septimus/signup-c` (the weekly hand-out: `scripts/septimus_assign.py`,
`scripts/septimus_weekly.py`, tests, the scheduled workflow) against [`septimus-signup-plan.md`](septimus-signup-plan.md)
§4 to §8, wrote its own simulations (200 people over 40 weeks on the real list) and mutated the rules to see which
tests noticed. Separately, the real database code was run against the local Firebase emulators (10 tests, no bugs).

| # | Sev | Finding | Outcome |
|---|---|---|---|
| 1 | P1 | A person was handed a story they still held open (597 times in the simulation) | Fixed: never hand out a story the person holds |
| 2 | P1 | Every daily run read every row ever written; past 50,000 reads a day (the free limit) from about week 23 with 200 people | Fixed: read only rounds not yet complete, plus open rows |
| 3 | P2 | A story that each eligible person had let lapse once was never offered again, so the round could never complete | Fixed: only the person who lapsed it *in this run* is skipped |
| 4 | P2 | A story marked learned at the moment of release was still handed to someone else | Fixed: releases are applied first, then the hand-out is computed from what really happened |
| 5 | P2 | People were paused after one round of lapses, not two; a non-reader's pile grew by one story a week | Fixed: at-least-one applies only when holding nothing; pause needs lapses at least 3 weeks apart |
| 6 | P2 | A paused person had no way back | Fixed: the rules let a person clear their own `pausedAt`; step d adds the "Resume" button |
| 7 | P2 | One failing deletion stopped the whole job every day | Fixed: logged and skipped |
| 8 | P2 | User ids appeared in the Action log (the repository is public) | Fixed: counts only |
| 9 | P2 | "Delete my data" left the user id inside each row's document id | Fixed: rows are re-created under a neutral id |
| 10 | P2 | The job can stop silently (GitHub disables schedules after 60 days of repository inactivity; the counts email is not built; no overlap guard) | Partly: overlap guard and a note added. **The counts email waits for the email service (step e)** |
| 11 | P3 | A crash mid-write left a person part-served for the week | Fixed: one person's rows are written together |
| 12 | P3 | Someone who stopped and restarted was paused at once | Fixed: only lapses count, not stop-releases |
| 13 | P3 | Nothing checked that the launch date is a Monday | Fixed: refuses otherwise |
| 14 | P3 | No test for the 120-minute cap or the last week; a logic slip could loop forever | Fixed |
| 15 | P3 | Dead code and duplication | Fixed |

## After the fixes (same simulation, 200 people over 40 weeks, real list)

- Person handed a story they hold: 0. Story covered twice in a round: 0. Over budget beyond one at-least-one story: 0.
- 32 rounds of Shas completed by week 40. A story two people each lapsed is offered again and its round completes.
- A person who never reads: stories in week 1, again in week 4, paused at the week 7 run.
- **Reads per daily run: about 21,000, some 42% of the free 50,000.** Not small: hand-outs run about ten rounds ahead
  of the last fully learned round, and all of those rows are read. Fine for 200 very committed people; it would not
  hold for 500. If sign-ups get near that, either read only rows changed since the last run on ordinary days, or
  move to the paid plan (a decision for Simon then, not now).
- Tests: 40 logic, 24 runner, 15 against the emulators with the real database code, 54 rules.

## Builder's choices to confirm with Simon

1. **Pause state lives on the person's record** as two script-written fields, `everLearned` and `lapses`, so the
   script never needs the whole history (finding 2). Plan §5 updated.
2. **Resuming is the person's own action** (clearing `pausedAt`), not automatic. Step d needs a "Resume" button.
3. **A lapsed story may come back to the same person in a later week** if nobody else took it. It only has to go to
   someone else in the week it lapses.
4. **"At least one story" applies only to someone holding nothing.** A person holding unread stories gets more only
   if they fit the remaining minutes.

5. **When the script pauses someone it clears their lapse history**, so a person who resumes starts fresh instead of
   being paused again at once.
6. **Known oddity:** a person who lets story X lapse in round 1 can be handed X again as part of round 2 in the same
   run. Allowed by the rules as written; rare; left alone.
7. **Known limit:** a round counted as complete stays complete. If stories are added to the list later, earlier
   rounds are not reopened for them (the list is frozen at launch, plan §7, so this should not arise).

## Not built in step c

- The **counts email to Simon** (plan §6, §8e): needs the email service chosen for step e. Until then a failed run
  emails the repository owner through GitHub, but a run that never starts is silent.
- **Deleting everyone's personal data six months after the yahrzeit** (plan §6 Leaving): marked `TODO(before launch)`.
- A run against the **live database**: waits for a service-account key in GitHub secrets, a launch date, and Daniel.
