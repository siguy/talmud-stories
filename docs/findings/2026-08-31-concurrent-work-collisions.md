# Concurrent work collides — measured, and what it costs

**2026-08-31**

Simon's question was "all of the work is colliding — confirm this." It is. This records
what was measured, what turned out to be worse than a collision, and what changed.

---

## 1. Three worktrees of work exist on one laptop and nowhere else

`WORK.md` on trunk carries a live block generated from `git worktree list`:

```
| jeff-ask-order                    | talmud-stories                    |  4 FILES |
| kiddushin-recall-boundary-c52c91  | kiddushin-recall-boundary-c52c91  | 20 FILES |
| state-work-review-40b153          | state-work-review-40b153          |  6 FILES |
```

Thirty uncommitted files. And:

```
$ git ls-remote --heads origin
9d6b5d3...  refs/heads/main
```

**One ref. None of those three branches exists on the remote.** They are not stale
entries in a generated file — the file is generated, so they were live when it ran. That
work is uncommitted, on branches that have never been pushed, on a single machine.

This is the finding that has to be acted on before any of the rest matters, because
`kiddushin-recall-boundary` overlaps two of the items the board currently recommends as
the cheapest next steps. Handing those to a fresh session duplicates twenty files of
someone's uncommitted work, and the duplicate will merge cleanly (§4).

**Measured, not inferred.** *Whether that work is still wanted is Simon's call; this
finding only establishes that it is unbacked-up and unmergeable as it stands.*

## 2. The collision rate on real history is 51%

Over the last 14 non-merge commits — a fair proxy for 14 concurrent branches, since that
is roughly what the last two days produced:

```
47 of 91 commit pairs touch at least one common file  (51%)

 21 pairs   STATUS.md
 15 pairs   CLAUDE.md
 10 pairs   docs/capabilities/6_publication.md
 10 pairs   docs/capabilities/3_classification.md
  6 pairs   WORK.md · STATE.md · FRAMEWORK.md · docs/capabilities/1_triage.md
  3 pairs   tests/test_bookkeeping.py · comms/JEFF.md
```

Every one of those pairs is two sessions that would have conflicted. Note what is at the
top: **none of it is the actual work.** It is bookkeeping.

## 3. `blocked_by` is the ordering graph. Nothing recorded contention.

Every work item declared `blocked_by` — what must finish *before* it starts. Nothing
declared what it *writes*. Those are different graphs, and only one existed, so two items
with no dependency between them were presented as concurrently runnable by `STATE.md`,
`WORK.md` and `STATUS.md` alike, whether or not they wrote the same file.

Adding `writes:` to the frontmatter and computing the graph (`board.py lanes`) gives:

```
31 open items -> 15 lanes that can actually run concurrently
39 colliding pairs over 11 contended paths

  src/story_detector_v11.py   <- 6 items   (both detection campaigns, opener-lexicon,
                                            second-story-guard, triage-recall-price)
  tests/test_bookkeeping.py   <- 6 items   (every item that grows a golden must bump
                                            the same hardcoded GOLDEN_COUNTS dict)
  validation/generators/      <- 4 items
  results/canonical/kiddushin_canonical.json  <- golden-completeness +
                                                 kiddushin-comments-harvest
  results/expert_lists/kiddushin_2005.json    <- two-amud-header-parser +
                                                 kiddushin-parse-open-calls
  results/rulers/                             <- golden-completeness +
                                                 kiddushin-comments-harvest
  scripts/measure_recall_vs_expert_list.py    <- kiddushin-recall + triage-recall-price
  src/prompts/                                <- opener-lexicon + story-criteria
```

**The number to hold on to is 15, not 31.** Four of the pairs above are items `STATUS.md`
listed together as the cheapest things to do next.

## 4. The dangerous collisions are the ones git will not report

Per Lesson 32, the pairs that *conflict* are the safe ones — somebody gets stopped. Three
here do not conflict:

- **`golden-completeness` and `kiddushin-comments-harvest`** both add entries to
  `results/canonical/kiddushin_canonical.json`. Both must then bump `GOLDEN_COUNTS` in
  `tests/test_bookkeeping.py`. If they bump it in one commit each, the merged constant
  matches neither branch's data, and the assertion that exists to catch silent golden
  loss becomes the thing asserting the wrong number.
- **The derivational chain.** `results/canonical/*.json` → `results/rulers/*.json` →
  `STATE.md`'s coverage matrix → `STATUS.md`'s scoreboard. A branch that grows a golden
  makes every other branch's ruler stale, and git reports nothing. This is not
  hypothetical: it is exactly the failure recorded in Lesson 32 §2, which happened to
  `ketubot_ruler.json` on 2026-08-30.
- **`kiddushin-12a-dedup` and `kiddushin-recall`** — one rewrites
  `results/v10/wave4_notrim/kiddushin_v10_notrim.json`, the other measures recall
  *against* it. Ordering changes the answer; nothing records the ordering.

## 5. The guaranteed collision has nothing to do with the work

Every item that is opened, finished, or edited changes `STATE.md` and `WORK.md`. So every
pair of concurrent branches conflicts on them regardless of what the items are about.
Measured, in two identical repositories differing only in whether the fix was installed —
three sessions, each opening **one unrelated work item**:

| | merges that conflicted | conflict markers committed | items on board | `board.py --check` |
|---|---|---|---|---|
| **without the fix** | **2 of 3** | **5** | 3/3 | **FAIL** |
| **with the fix** | 0 | 0 | 3/3 | PASS |

The `FAIL` in that table is the part worth dwelling on: after a clean-looking integration
of three green branches, `tests/test_bookkeeping.py` fails **on trunk**. And because a
hand-resolved generated file no longer matches its own checksum, `board.py` then *refuses*
to regenerate for whoever runs it next — a failure two steps removed from its cause.

## 6. A fresh clone cannot run the gate, and its guard is off

Both found by trying it, not by reading:

- `requirements.txt` lists `requests` and `google-genai`. It does not list **`pytest`** or
  **`olefile`**. `python3 -m pytest tests/ -q` — which `CLAUDE.md` makes mandatory before
  stopping — fails at *collection* in a fresh clone. Every cloud session would hit this.
- `git config core.hooksPath` was **unset** in this clone. The pre-commit guard on
  `evaluate_golden.py` and `baseline_ketubot.json` that `CLAUDE.md` describes as active
  was not active. The one-time setup command exists and had not been run — which is what
  a remembered setup step does.

---

## What changed

Following Lesson 33 — the requirement is "two sessions must not corrupt each other", and
a reservation protocol *creates* that problem and then defends it — none of this is a
lock.

1. **`writes:` in the item frontmatter**, populated for all 30 pre-existing items, plus
   `board.py lanes` to compute the contention graph and group items into lanes that can
   safely run at once. Contention becomes visible *before* the work starts, which is the
   thing nothing did.
2. **`.gitattributes` routes `STATE.md` and `WORK.md` to merge drivers that regenerate
   rather than merge.** The correct content of a generated file is never a blend of two
   sides. The same file marks the goldens, rulers and expert lists `-merge`, so a textual
   merge of one of them stops being possible at all.
3. **`.githooks/post-merge` regenerates the board after every merge.** The driver alone is
   not enough and the distinction matters: a merge driver runs *while* the merge is in
   progress, when `work/` on disk does not yet hold the other side's items, so it resolves
   the conflict but produces a stale board. The driver's job is keeping conflict markers
   and a broken checksum out of a generated file; the hook's job is producing the truth.
   This is Lesson 32's rule — regenerate everything derived, after every merge — made
   automatic rather than remembered.
4. **`board.py setup`** registers the hooks path and both merge drivers in one idempotent
   command. A fresh clone needed one remembered command before this and needs one after:
   adding a *second* setup step is how a setup step stops being run at all.
5. **`requirements.txt`** gains `pytest` and `olefile`, and two tests stopped being
   Mac-only. The suite went from **1 failed / 5 errors** to **100 passed, 2 skipped** in a
   Linux container — it had never been green in one:
   - `test_story_text_matches_an_independent_renderer` shells out to Apple's `textutil`
     and now *skips with a reason* off macOS instead of raising `FileNotFoundError`. It is
     the check that caught Lesson 28, so it is not deleted — it is stated as a gap.
   - `test_review_ui_symmetry` passed the whole display layer to `node -e` as an argv
     entry and blew `ARG_MAX`, five times, as `OSError: [Errno 7] Argument list too long`.
     Now written to a temp file. Nothing about the assertions changed.
6. Three tests in `tests/test_bookkeeping.py`: every open item declares `writes:`; the
   drivers and the hook stay wired; and `overlap()` treats a trailing `/` as a subtree —
   verified by simulating the failure it guards, per Lesson 31.

## What did not change, and is a judgment call for Simon

- **`STATUS.md` is still a guaranteed serial collision.** It is hand-written and
  "rewritten every session, never appended", so no merge driver can help: the correct
  result genuinely requires a human to read both sides. The honest resolution is that
  rewriting `STATUS.md` is an **integration step, not a lane** — one session does it after
  merging, not each session on its own branch. Stated in `CLAUDE.md`; not enforced,
  because enforcing it would fire on legitimate trunk work.
- **`GOLDEN_COUNTS` forces all five golden-growing items into one lane.** Deriving it from
  the goldens would decouple them, but `CLAUDE.md` Rule 5 pins those counts *deliberately*
  as the guard against silent loss, and a guard that derives its expectation from the
  thing it guards is not a guard. Moving the dict to its own small file would make the
  conflict tiny and obvious instead of tangled in a 300-line test module. Not done here;
  it changes a guard, and that is worth being asked about first.
- **The three unpushed worktrees.** Nothing in this change can reach them.
