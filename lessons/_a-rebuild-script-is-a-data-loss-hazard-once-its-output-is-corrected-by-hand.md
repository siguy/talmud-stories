# Lesson — A rebuild script becomes a data-loss hazard the moment its output is corrected by hand

**2026-08-31**

`scripts/build_canonical.py` builds the Ketubot golden from the base detector runs plus
three 2026-02 feedback files and the 2026-03 canonical review. It was a build step, and
for a while that was true.

Then the golden was corrected *outside* it — a 2026-06-03 review round, and on
2026-08-30 five stories from Jeff's blind 2005 list that no detector run had ever
proposed. The script knows about none of them. Running it would have silently deleted
work no rerun could reproduce, from the most valuable artifact in the project.

**The trap is that the obvious safety check points the wrong way.** Re-score after the
rebuild and confirm nothing got worse — that is the instinct, and it is exactly
backwards here. Measured through the immutable harness, removing the five stories:

```
golden as it is now (187 stories)   classification recall  0.9085
golden after the loss (182)         classification recall  0.9371   ← the score RISES
```

Of course it does. The five are stories the detector cannot find, so deleting them
deletes five false negatives. **Silent data loss presents as a 2.9-point improvement.**
A guard keyed to "did the score drop" would have waved it through, and the composite
would have gone up in the same motion.

**Rule:** once an artifact accepts corrections that its build script does not consume,
the script is no longer a build step — it is a historical reconstruction. Make it refuse
to write, name exactly what would be lost, and require an explicit flag to override.
Do not rely on a downstream metric to notice.

**Why:** the value in a hand-corrected artifact is precisely the part no input can
regenerate. That is also the part a rebuild destroys first, and the part every
aggregate metric is least able to see — because expert corrections tend to *add
difficulty*, so losing them makes the numbers look better. The direction of the error
and the direction of the metric agree, which is the worst possible arrangement.

**How to apply:** (a) A script that writes a hand-corrected artifact should compare
against what is on disk and refuse anything that is not a strict addition — the current
guard does this; an earlier version of mine guessed by looking for a provenance string
and was replaced (`6b7fcae`). (b) Simulate the loss and look at the metric before
trusting the metric (Lesson 31). If the metric improves under the failure, it cannot be
the guard. (c) Say in the module docstring what the script has *become*, not what it was
written to be — the next reader's default assumption is that a build script builds.
