# work/ — one item per task, named by date and slug

**`work/<YYYY-MM-DD>-<slug>.md` is open. `work/done/` is finished and is never emptied.**

Copy [`_TEMPLATE.md`](_TEMPLATE.md), fill in the frontmatter, branch `work/<same-slug>`.
Nothing to reserve, no counter, no allocator — two sessions cannot collide on a name they
each chose. On 2026-08-30 four concurrent sessions each wrote a "Lesson 26", and two wrote
a different `09` and a different `10`; because the slugs differed, git merged all four
cleanly and silently. That is the failure this layout removes.

**Finishing:** add `## Outcome` saying what happened *and why*, then
`python3 scripts/board.py finish <slug>`. **Never delete it.**

Use the command rather than a bare `git mv`: items link out with `../`, and `work/done/`
is one level deeper, so a plain move breaks every one of those links at the moment the
item becomes a permanent record. That is not hypothetical — the first item anyone finished
broke its own link to `FRAMEWORK.md`, with 60 more one move away.
`tests/test_bookkeeping.py` checks both that no link is broken and that the closing step
would leave every open item's links resolvable. A revert we cannot explain will be re-tried — it has
happened here at least once already.

## Frontmatter

| field | meaning |
|---|---|
| `title` | one line |
| `capability` | list of slugs — `triage detection classification boundaries review publication`. **Editable**: diagnosing which capability is at fault *is* the work (`abdc4af` moved Ketubot 77a from Detection to Classification), so it cannot be a precondition for starting |
| `tractate` | list; empty means cross-cutting |
| `blocked_by` | cannot **start** — item slugs, or `jeff:<question-slug>` |
| `awaiting` | can finish, cannot **conclude** — usually a question out with Jeff |
| `finding` | `docs/findings/YYYY-MM-DD-slug.md`, once written |
| `superseded_by` | set when reverted or replaced |

## Where the old numbered briefs went

`tasks/NEXT/NN_*.md` was retired on 2026-08-30. Documents written before then cite briefs
by number; resolve them here.

| old | now |
|---|---|
| `tasks/NEXT/00` capability records | [`done/2026-08-30-capability-histories.md`](done/2026-08-30-capability-histories.md) |
| `tasks/NEXT/01` triage recall | [`done/2026-08-30-triage-recall-price.md`](done/2026-08-30-triage-recall-price.md) |
| `tasks/NEXT/02` Ketubot 77a | [`done/2026-08-30-ketubot-77a.md`](done/2026-08-30-ketubot-77a.md) |
| `tasks/NEXT/03` second-story guard | [`2026-08-30-second-story-guard.md`](2026-08-30-second-story-guard.md) |
| `tasks/NEXT/04` review UI asymmetry | [`done/2026-08-30-review-ui-display-asymmetry.md`](done/2026-08-30-review-ui-display-asymmetry.md) — **and then the name was reused.** `4de7135` repointed "NEXT/04" at a different job with no brief behind it; that job is now [`2026-08-30-review-verdict-axes.md`](2026-08-30-review-verdict-axes.md). A citation of `NEXT/04` means one or the other depending on its date — which is the reuse-after-deletion problem this layout exists to end |
| `tasks/NEXT/05` Kiddushin list parse | [`done/2026-08-30-kiddushin-list-parse.md`](done/2026-08-30-kiddushin-list-parse.md) |
| `tasks/NEXT/06` Kiddushin recall | [`done/2026-08-30-kiddushin-recall.md`](done/2026-08-30-kiddushin-recall.md) |
| `tasks/NEXT/07` Kiddushin boundaries | [`done/2026-08-30-kiddushin-boundary-set.md`](done/2026-08-30-kiddushin-boundary-set.md) |
| `tasks/NEXT/08` comments harvest | [`2026-08-30-kiddushin-comments-harvest.md`](2026-08-30-kiddushin-comments-harvest.md) |
| `tasks/NEXT/09` fetch new tractates | [`done/2026-08-30-fetch-new-tractates.md`](done/2026-08-30-fetch-new-tractates.md) |
| `tasks/NEXT/09` parse open calls | [`2026-08-30-kiddushin-parse-open-calls.md`](2026-08-30-kiddushin-parse-open-calls.md) — *two different briefs were both numbered 09* |
| `tasks/NEXT/10` golden additions | [`done/2026-08-30-ketubot-golden-additions.md`](done/2026-08-30-ketubot-golden-additions.md) |
| `tasks/NEXT/10` golden completeness | [`2026-08-30-golden-completeness.md`](2026-08-30-golden-completeness.md) — *and two were both numbered 10* |
| `tasks/NEXT/11` Kiddushin 12a | [`2026-08-30-kiddushin-12a-dedup.md`](2026-08-30-kiddushin-12a-dedup.md) |
| `tasks/PLAN_wave6.md` | [`2026-08-30-story-criteria.md`](2026-08-30-story-criteria.md) — live handle; the plan itself is in [`docs/history/`](../docs/history/2026-08-29-PLAN-wave6-story-criteria.md) |
| `tasks/PLAN_wave7.md` | [`2026-08-30-opener-lexicon.md`](2026-08-30-opener-lexicon.md) — same shape |

Every other `tasks/PLAN_*.md` moved to [`docs/history/`](../docs/history/) unchanged.
Dated findings and lessons still cite the old numbers **as written**: they were true when
written, and editing a finding so it reads as though it had always been right is the habit
this repo avoids.
