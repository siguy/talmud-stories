# Integrating concurrent work without losing any

**Written 2026-08-31**, when three worktrees held 30 uncommitted files on branches that
existed on no remote. The first half is the one-time recovery. The second half is the
standing procedure, and it is the same procedure.

The governing rule, and the reason for the ordering below:

> **Capture is not integration. Do all of the capturing before any of the integrating.**
> A commit is recoverable forever, even a broken one on a dead branch. An uncommitted
> working tree is one `git checkout` from gone, and `git checkout` is step one of every
> integration you are about to do.

---

## Phase 0 — Capture everything, decide nothing

Do this in **every** worktree, before merging, rebasing, pulling, or switching branches
anywhere. It is mechanical and it is not reversible in the wrong order.

```sh
git worktree list                     # find them all; do not work from memory
```

Then, in each one:

```sh
cd <worktree>
git status --porcelain --untracked-files=all      # LOOK first. Note anything surprising.
git checkout -b wip/<worktree-name>-$(date +%m%d) # a branch of its own, always
git add -A
git commit -m "WIP capture: <worktree-name>, uncommitted state at $(date +%F)"
git push -u origin HEAD
```

**Do not** tidy, squash, fix a failing test, or resolve anything first. A messy commit
that exists beats a clean one that does not. You are buying the right to be careless
later.

Three things that quietly lose work at this step:

- **`git stash` is banned here** (`CLAUDE.md` Rule 6) and this is exactly why:
  `refs/stash` is shared across every worktree, so a stash made in one is poppable from
  another, and `git stash create` drops untracked files silently.
- **`git add -A` does not add ignored files.** If something real is caught by
  `.gitignore` — a `.env`, a generated dataset, a scratch notebook you care about — copy
  it somewhere outside the repo now. `git status --ignored` will show you.
- **Untracked directories** are easy to miss in a truncated `git status`. Use
  `--untracked-files=all`.

Stop here. Do not proceed until every worktree is pushed and `git status` is clean in
all of them.

## Phase 1 — Land the machinery before you merge anything into it

Concurrent branches conflict on `STATE.md` and `WORK.md` whatever they contain, and a
hand-resolved generated file breaks its own checksum, which makes `board.py` refuse to
regenerate for whoever runs it next. So the merge drivers have to exist *before* the
merges, not after.

```sh
git checkout main
git merge <the branch carrying .gitattributes and .githooks/post-merge>
python3 scripts/board.py setup        # in EVERY worktree and clone. Idempotent.
pip install -r requirements.txt
python3 -m pytest tests/ -q           # expect green before you start
```

## Phase 2 — Find out what you actually captured

For each `wip/*` branch, two questions, in this order.

**Is any of it already on main?** A branch that was partly landed will otherwise be
re-applied or, worse, revert what landed. `git cherry` compares by patch, not by SHA:

```sh
git cherry -v main wip/<name>         # `+` = not in main yet.  `-` = already there
git diff --stat main...wip/<name>     # note the three dots
```

*This is not hypothetical: on 2026-08-31 `comms/JEFF.md` work was on main as `a94183e`
(1 file) while a worktree named `jeff-ask-order` still held 4 uncommitted files. Neither
"already done" nor "all new" was the right assumption.*

**Which lane does it belong to?**

```sh
python3 scripts/board.py lanes
```

Map the branch's changed paths onto the contended paths that command prints. A branch
whose name spans two work items usually spans two lanes — split it before integrating,
or you serialize both lanes on one merge.

## Phase 3 — Merge in derivation order, not in the order you made them

This is the ordering that matters, and it is not obvious. Git will let you merge in any
order and report success; the damage is that an artifact merged early goes stale when its
source changes later, **with no conflict** (Lesson 32, which already cost
`results/rulers/ketubot_ruler.json` once).

Merge sources before the things derived from them:

| order | what | why it goes here |
|---|---|---|
| 1 | `results/expert_lists/` | blind ground truth; every recall number is measured against it |
| 2 | `results/canonical/` | the goldens |
| 3 | `results/rulers/` | **regenerate, never merge** — derived from 1 + 2 |
| 4 | `results/v*/` | detector outputs |
| 5 | `src/`, `src/prompts/` | the detector and its prompts |
| 6 | `scripts/` | harnesses that read all of the above |
| 7 | bookkeeping | `STATE.md`, `WORK.md` — automatic now; `STATUS.md` last, by hand |

One merge at a time. After each:

```sh
python3 -m pytest tests/ -q
git diff --stat HEAD~1                # did anything change that you did not expect?
```

## Phase 4 — Regenerate what is derived, and diff it

**The absence of conflicts is not a reason to skip this. It is the reason the problem is
invisible.** After any merge that touched a golden, a list or a run:

```sh
python3 scripts/board.py                          # STATE.md, WORK.md
python3 scripts/build_ruler.py                    # results/rulers/ — do not hand-merge
python3 -m pytest tests/ -q
git diff --stat
```

A number that moves here and that you cannot explain is the finding, not the noise.
Note it before continuing — `docs/findings/`, dated.

## Phase 5 — `STATUS.md`, once, at the end

`STATUS.md` is hand-written and rewritten each session, so two branches always conflict
over the whole file and no driver can help: the correct result genuinely needs someone to
read both sides. Treat rewriting it as **the integration step, not a lane** — one person,
once, after everything else is merged. Do not let branches carry their own rewrite of it.

*(That it is contended at all is a design problem, raised as*
[`work/2026-08-31-status-facts-are-typed-twice.md`](../../work/2026-08-31-status-facts-are-typed-twice.md)
*— most of the file is hand-typed copies of generated content.)*

---

## Standing procedure, once the backlog is clear

1. `python3 scripts/board.py lanes` — take **one lane**, not one item.
2. Branch `work/<slug>`. Fill in `writes:` before starting; declare generously.
3. Commit and **push daily**, even mid-thought. See Phase 0 for why.
4. Do not rewrite `STATUS.md` on the branch.
5. Merge back in the Phase 3 order; regenerate per Phase 4.

The lane count from `board.py lanes` — not the number of unblocked items — is how many
sessions the work supports. Today those differ by a factor of three.
