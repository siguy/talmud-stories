---
title: Detector v15 -- a biblical-actor flag (Stage 4j) accurate enough for the site
capability: [classification, publication]
tractate: []
blocked_by: []
awaiting: []
writes: [CLAUDE.md, docs/technical/VERSION_HISTORY.md, src/story_detector_v15.py, scripts/measure_biblical_flag_reach.py, scripts/build_site_data.py, site/data/, tests/test_biblical_flag_v15.py, docs/technical/septimus-story-filter.md, docs/findings/2026-11-11-v15-biblical-flag.md]
finding: docs/findings/2026-11-11-v15-biblical-flag.md
superseded_by:
---

# Detector v15 -- a biblical-actor flag (Stage 4j) accurate enough for the site

**Self-contained.** A fresh session executes this with no other context.
Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then this.

## The claim to test / the problem

Biblical stories ship on the Septimus site, flagged `biblical: true`, and the flag excludes them from Jeff's
scholarly catalogue (Simon 2026-11-10; R-S1). v14's Stage 4j is a fixed name list that misses group actors,
biblical peoples and places, and reads "God" as a non-biblical actor. The accuracy review found two biblical stories
no automatic flag caught (Megillah 7a:2-3, Sanhedrin 113a:10-113b:0). Plan §2.5 of
`docs/history/2026-11-09-PLAN-shas-run.md` asks for a v15 rule, no model calls, re-appliable to every run on disk.

## Method

Copy v14 to v15, change only 4j. Measure the reach on every run (`scripts/measure_biblical_flag_reach.py`), read
every changed story, check against Jeff's scope edges (`jeff:scope-edges`) and his yes verdicts, and against the
units the judges flag. Wire it into `build_site_data.py`, rebuild, diff the site.

## How you know it worked

No story Jeff said yes to is flagged; none of his scope edges is flagged; the judges' biblical passages are caught;
the site's story count is unchanged.

## Guardrails

Never edit v14. No model calls. If the reach shows the rule flags a story Jeff calls in scope, stop and report.

## When done

Write the finding to `docs/findings/<date>-<slug>.md`, add an `## Outcome` section
below, and `git mv` this file to `work/done/`. **Never delete it.**

## Outcome

**Adopted for flagging only** (2026-11-11). Finding:
[`2026-11-11-v15-biblical-flag.md`](../../docs/findings/2026-11-11-v15-biblical-flag.md). Of the 141 passages the
judges flag biblical, v15 catches 135 (v14: 20). It flags 0 passages Jeff said yes to and none of his scope edges.
Of the 20 passages it flags that the judges do not, 18 were called `out_of_scope` by Gemini (Claude said `not`);
the other two are plainly biblical and LOW. On the site: 1,897 stories unchanged; flagged 102 -> 97, the five removed all
post-biblical people v14's list mistook for biblical. The runner stays on v14: v15 differs only in 4j, and the site
re-applies the rule to the actor list every run already holds. **Why only for flagging:** switching the runner would
change nothing for runs on disk and would make the next run's version stamp differ from the 37 on the site for no
gain; it is a one-line change when a new run is due.
