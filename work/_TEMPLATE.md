---
title:
capability: []          # slugs, a LIST, editable: triage detection classification boundaries review publication
tractate: []            # ketubot kiddushin gittin yevamot eruvin; empty = cross-cutting
blocked_by: []          # cannot START — item slugs, or jeff:<question-slug>
awaiting: []            # can finish, cannot CONCLUDE — usually jeff:<question-slug>
writes: []              # paths this item MODIFIES. Two items sharing one cannot run
                        # concurrently. Declare GENEROUSLY: over-declaring costs a
                        # serialized lane, under-declaring costs a silent corruption.
                        # A trailing / means the whole directory. `board.py lanes`
finding:                # docs/findings/YYYY-MM-DD-slug.md, once written
superseded_by:          # set when reverted or replaced
---

# <title>

**Self-contained.** A fresh session executes this with no other context.
Read [`FRAMEWORK.md`](../FRAMEWORK.md) first, then this.

## The claim to test / the problem

## Method

## How you know it worked

## Guardrails

## When done

Write the finding to `docs/findings/<date>-<slug>.md`, add an `## Outcome` section
below, and `git mv` this file to `work/done/`. **Never delete it.**
