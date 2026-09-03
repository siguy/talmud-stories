# Detection is worst where a story stands alone — the attention hypothesis is refuted, backwards

**2026-09-03.** After two dead ends — R-C3/R-C4 measured no effect, the translator screen
came back null — the standing hypothesis was that Detection's constraint is **attention per
page**: Stage 2 sees one daf at a time, so a daf holding four of Jeff's stories asks more
of it than a daf holding one, and the fix would be a second pass. Gittin 57a Beitar is not
proposed even as `NOT_A_STORY`, which no wording change can reach.

**The measurement refutes it, and points the opposite way.** No API calls.

```bash
python3 scripts/audit_detection_density.py --out results/recall/detection_density.json
```

## Recall by how many of his stories share the daf

| stories on the daf | his stories | we found | recall |
|---|---|---|---|
| **1** | 84 | 70 | **83.3%** |
| 2 | 74 | 71 | 95.9% |
| 3 | 63 | 56 | 88.9% |
| **4+** | 129 | 117 | **90.7%** |

**Recall is *lowest* where a story is alone on its daf**, and it holds up on the dense
ones. Per tractate, the two with real misses agree:

| | 1 story | 4+ stories |
|---|---|---|
| Ketubot | **75.0%** | 89.2% |
| Kiddushin | **76.2%** | 84.6% |
| Gittin | 100% | 97.4% |

Gittin shows nothing, and should not be expected to — it is at 97.3% overall, with three
misses in the whole tractate. There is no signal to carry.

## It is not story length

The obvious alternative: a daf with one story is a daf whose one story is thin, and we
miss thin stories. Measured rather than argued (Lesson 18):

- expert stories we **found**: median **46** words. Expert stories we **missed**: median
  **44**. We are not simply missing short stories.
- and inside a single length band, the density gap survives:

| | alone on the daf | 4+ stories |
|---|---|---|
| long (> 25 words) | **84%** (n=73) | **94%** (n=108) |
| short (≤ 25 words) | 82% (n=11) | 76% (n=21) |

For substantial stories the gap is **ten points** with the length variable held. The short
band reverses, but n=11 against n=21 and it should not be read.

## What this relocates

**The problem is not budget, it is salience.** A daf carrying four of Jeff's stories is an
aggadic stretch where narrative is the default mode; a daf carrying one is mostly legal
give-and-take with a single story embedded in it. We find the story when it is among its
own kind and miss it when it is surrounded by halakhah.

That is consistent with everything else on record and explains why two attempts failed:

- **R-C3/R-C4 measured nothing** because they change how a candidate is *described*, and
  the failure happens before there is a candidate.
- **Beitar is never proposed at all.** 57a carries four of his stories, so it is not a
  density case — but it is the same shape: a passage whose opening looks like halakhic
  framing (a custom) rather than narrative.
- **A second pass over the page would help least where we are worst.** Re-reading a
  4-story daf that we already score 90.7% on is effort spent where the ceiling is nearest.

## What it does not establish

**Correlational, and the mechanism is not isolated.** "Alone on the daf" and "surrounded
by legal material" are the same dapim in this data — nothing here separates *isolation*
from *context*, and the proposed mechanism is the second. Testing it needs a measure of
how much of a daf is halakhic, which the triage labels can probably supply and this does
not use.

**And the direction of causation is open in one respect:** Jeff's list is sparse on those
dapim too. A daf where he found one story may be one where stories are genuinely marginal
— harder for anyone, not just for us. That would make the profile a fact about the
material rather than about the detector.

Both are checkable and neither is checked here. The claim that survives is narrow and
useful: **whatever the next Detection attempt is, it should be aimed at the isolated story
in legal surroundings, and not at re-reading dense dapim.**

## The value of a refuted hypothesis

This was the top-ranked item on the strength of an argument, not a measurement — the
argument was clean, mechanical, and pointed at a specific fix. It is wrong, and it cost
one script and no API calls to find that out.

**Three hypotheses have now been screened cheaply before any run:** criteria wording
(measured, no effect), translator expansion (screened, null), attention per page
(refuted, reversed). That is the pattern worth keeping — the screen is much cheaper than
the run, and two of the three would have consumed a full tractate arm to reach the same
answer.
