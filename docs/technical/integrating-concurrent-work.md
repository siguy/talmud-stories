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

```sh
python3 scripts/board.py capture          # dry run: shows what it would do
python3 scripts/board.py capture --go     # branch, commit and push every dirty worktree
```

That is the whole phase. It walks `git worktree list`, and for each worktree with
uncommitted work it creates `wip/<name>-<date>`, commits everything as-is, and pushes.

**It is a command and not a procedure on purpose.** This repo already ran the other
experiment: `git config core.hooksPath .githooks` was documented as a one-line fresh-clone
step in `9be0586`, and on 2026-08-31 a clone was found with it unset — the guard
`CLAUDE.md` called active was not active. A five-command procedure, run correctly in three
worktrees, under time pressure, with unpushed work at stake, was not going to do better.

What it does for you, each of which lost work at least once when it was prose:

- **Re-running is safe and additive.** If a worktree is already on its `wip/` branch it
  commits onto it rather than failing. You never have to remember whether you already ran it.
- **It refuses to commit credential-shaped files** — `.env`, `*.pem`, `*.key`,
  `id_rsa`, and friends — and captures *nothing anywhere* when it finds one. `git add -A`
  will happily sweep a secret into a commit and push it, and a pushed secret is in history
  forever. (Found by testing `capture` end to end: a worktree branched before `.gitignore`
  gained `.env` had the secret committed and pushed.)
- **It warns about ignored-but-present files**, which `git add -A` silently leaves behind.
  Ignored on purpose most of the time; irreplaceable the rest of the time. Copy those out
  of the repo yourself — it will not commit them.
- **It stops at the first failure** rather than half-capturing a set of worktrees.

Deliberately *not* tidy: no squashing, no fixing the failing test, no resolving anything.
A messy commit that exists beats a clean one that does not. You are buying the right to be
careless later.

One thing the command cannot do for you: **`git stash` is banned here** (`CLAUDE.md`
Rule 6) and this is exactly why. `refs/stash` is shared across every worktree, so a stash
made in one is poppable from another, and `git stash create` drops untracked files
silently. If you have already stashed, `git stash list` and pop it before capturing.

Stop here. Do not proceed until `board.py capture` reports every worktree clean.

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
