# Lesson — An ablation must remove the thing, not replace it with a lie

**2026-09-01**

`run_pipeline(pages, skip_triage=True)` reads as "run without Stage 1". It does not. It
substitutes a **false** Stage 1 output — every segment on every page stamped
`DELIBERATION` — and Stage 2 renders that straight into its prompt:

```python
# story_detector_v7.py:658-664, and unchanged in v8, v9, v10, v11
elif skip_triage:
    # Generate default triage (all DELIBERATION) so detection still works
    triage_results[ref] = [EventType.DELIBERATION] * n_segs
```

```
[DELIBERATION] Seg 4:            <- story_detector_v7.py:75, under a prompt header saying
  English: ...                      each segment "has been pre-classified by event type"
```

The comment says the quiet part: *"so detection still works."* A downstream stage needed a
value, so the flag invented one, and the invented value is the most confident wrong answer
available — "nothing happens here" — asserted about all 118 pages.

The ablation built on it ran for six months as *"triage is the single largest accuracy
driver: 87.4% with, 83.5% without."* The contest it actually ran was **true labels against
uniformly false ones**, which is a much easier contest to win, and which nobody chose to
run. Triage may well help. That file never showed it.

**What exposed it was an impossible result, not a code review.** Turning triage off can
only ever *add* pages to examine, so it cannot subtract a story found on a page that was
examined either way. Scoring both arms against the blind list, the no-triage arm **lost 6
such stories**. One arithmetic impossibility is worth more than any amount of reading the
diff, and it cost one assertion to find:

```python
assert not [r for r in lost if r['survived_triage']], \
    'a story lost on a page both arms examined — the ablation changed more than the page set'
```

**The rule.** Before trusting an ablation, ask what the disabled stage's *consumers* were
given in its place. If the answer is a default rather than nothing, the experiment measures
"real input vs fake input", not "with vs without" — and name the flag for what it does:
`examine_all_pages`, not `skip_triage`. Then write down the direction the removal can move
the result, and assert it. This is Lesson 21's shape one stage over: there a failed call
was recorded as a decision, here a *skipped* stage is recorded as a decision, and both
launder an absence into confident data.
