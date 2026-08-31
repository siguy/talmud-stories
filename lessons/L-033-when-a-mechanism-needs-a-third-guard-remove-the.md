# Lesson 33 — When a mechanism needs a third guard, remove the mechanism

**2026-08-31**

The first draft of the repo reorganization kept sequential IDs — `CLS-002`, `DET-004` —
and built coordination around them so concurrent sessions could not collide. Read the
highest number on main; allocate the next; **commit a stub to main to reserve it**; handle
the race between two sessions reading the same maximum; retry on loss; and add a check
that the reservation mechanism is installed.

Then two facts arrived, both verified:

- `git checkout main` from a worktree fails — *"already used by worktree at
  /Users/simonbrief/talmud-stories"*. The reservation step could not run in the place where
  every session in this repo actually runs.
- Even if it could, two sessions picking the same number with different slugs write
  different filenames, so git merges both cleanly and warns about nothing (Lesson 32). The
  lock would have had to be perfect, because the backstop did not work.

The fix was not a better lock. It was **deleting the counter.** Work items and lessons
became dated slugs, which cannot collide because nobody has to agree on them. The race,
the worktree write, and the reservation protocol all disappeared at once — three of the
four hardest problems in the draft, none of which came from the requirement.

**Rule:** when a mechanism accumulates guards — a lock, then a retry, then a check that
the lock is installed — stop and ask whether the mechanism is load-bearing or merely
familiar. **Guard count is a design smell, not a robustness metric.** List which problems
are inherent to the requirement and which exist only because of the mechanism you chose;
if the second list is longer, change the mechanism.

**Why:** the requirement was "two sessions must not collide." Sequential numbering does
not serve that requirement at all — it *creates* the collision and then needs protecting.
Every hour spent on the reservation protocol was spent defending a choice nobody had
examined, and the choice was inherited from how the repo already happened to name things.

**How to apply:**
(a) **Prefer making the bad state unrepresentable over detecting it.** A design where
collision is impossible needs no lock, no retry, and no test.
(b) **Notice the tell.** The moment a design needs a mechanism to protect the mechanism —
a check that the hook is installed, a lock on the lock — the layer underneath is probably
wrong.
(c) Numbers were kept for *existing* lessons because 313 citations across 65 files depend
on them (`lessons/README.md`). Keeping a legacy identifier stable is a different decision
from minting new ones that way, and conflating the two is what kept the counter alive.
(d) This is FRAMEWORK's recoverability principle turned on process instead of gates: an
error nobody can see gets the strictest treatment, and the strictest treatment available
is making it impossible.
