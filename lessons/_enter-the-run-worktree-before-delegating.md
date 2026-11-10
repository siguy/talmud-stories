# Move the session into the worktree it writes to before launching subagents

**Date:** 2026-11-10
→ [`2026-11-10-shas-run.md`](../docs/findings/2026-11-10-shas-run.md)

## The rule

**When a run lives in its own worktree, the first step of the run is to switch the session into it
(`EnterWorktree` with `path`). Only then start subagents that write there.** A subagent inherits the worktree
its session was in when it was launched. A worktree-isolation hook then refuses its writes anywhere else, and
that includes the run's own output folder.

## What happened

The Shas run worktree (`shas-run`) was made with `git worktree add` from the planning session, which stayed in
its own worktree. Commands outside the dedicated tools still worked, so nothing looked wrong until 8 judge
subagents were launched to write `answers/` into the run worktree. A hook refused 7 of them. They saved their
answers to a scratchpad (one pasted its answers inline) and those were copied in, with each batch's count
checked against its keys. The session was moved into the run worktree halfway through, and the hook then
blocked the parent's own writes until that move. The data is intact, but it took three paths to get there.
