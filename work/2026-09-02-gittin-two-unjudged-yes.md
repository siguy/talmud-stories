---
title: Two YES-tier Gittin stories nobody has ever judged — and the loose window that hid them
capability: [detection, classification]
tractate: [gittin]
blocked_by: []
awaiting: [jeff:axes-round]
writes: [results/recall/gittin_listed_keys.json, results/recall/gittin_unlisted_screen.json, results/recall/gittin_unlisted_ask.json, validation/ui/, comms/JEFF.md]
finding:
superseded_by:
---

# Two YES-tier Gittin stories nobody has ever judged

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) first, then this.
**Capabilities: 2 Detection, 3 Classification.** **Cost:** free. No API calls.

## The problem

Building the Gittin golden on the **strict** match surfaced two proposals in our top
confidence tier that carry no expert evidence of any kind:

| | |
|---|---|
| **Gittin 57b:0-4** | Nebuzaradan and the bubbling blood of Zechariah |
| **Gittin 68a:7-12** | Solomon sends Benayahu to capture Ashmedai |

Both were counted as matching his 2005 list in `results/recall/gittin_listed_keys.json`,
which was built on the **loose** window. They are not on it. The window is up to 14
segments wide and credited a neighbour:

| his entry | loose window | what our span there actually is |
|---|---|---|
| `gittin_079` — the 400 captive children | 57a:22 → 57b:12 | 57b:0-4, Nebuzaradan |
| `gittin_097` — Resh Galuta and Rav Sheshet | 67b:18 → 68a:9 | 68a:7-12, Ashmedai |

**Consequences, all of them ours:** the unlisted screen held 30 entries and should have
held 32; the page we sent him asked 25 questions and should have asked 27; and the email
told him *"all 59 we called certain are on your list"*, which is false for two of them.

## The claim to test

These are almost certainly stories — famous aggadot of exactly the kind his lists carry.
**That is a prediction, not a result.** This project has just been reminded, twice in one
week, that a passage is settled only by a ruling on that passage
([lesson](../lessons/_a-policy-answer-does-not-certify-a-case.md)), so they stay
`indicated` until he says otherwise.

## Method

1. **Rebuild `gittin_listed_keys.json` on the strict test**, and regenerate the unlisted
   screen from it. Expect 32; check the two new arrivals **by name** and confirm nothing
   else moved — a count that lands on 32 for the wrong reason is worse than one that
   lands on 31.
2. **Sweep the other tractates for the same defect.** Kiddushin and Ketubot have
   `listed_keys` built the same way, and the loose window is known to mis-credit there
   too (2 of 6 hand-checked on Kiddushin). **Do this before concluding anything about
   Gittin** — if the same script mis-credits everywhere, the fix is the script, and the
   Gittin cases are a symptom.
3. Put both passages on the next review page, with the correction owed to him
   (`comms/JEFF.md`).

## How you know it worked

- Every entry in a rebuilt `listed_keys` survives the strict test, and the count is
  reconciled by name against the previous one — additions and removals both listed, not
  netted.
- The two passages appear in the unlisted set with the rest.
- The sweep reports a number for Kiddushin and Ketubot, **even if it is zero.** A silent
  "nothing found" is what Lesson 38 is about.

## Guardrails

- **Do not add these to the golden as accepted.** They have no expert label, and a golden
  in which we labelled two entries ourselves is no longer a golden.
- **Do not quietly re-run the recall figure.** Detection recall is measured against *his*
  denominator; two proposals leaving the "listed" column change **precision**, not recall,
  and nothing about 108/111 moves.
- Report the correction to him plainly. Half of a claim we made was wrong, and the sent
  email is a record — annotate `comms/JEFF.md`, never the sent file.

## When done

Write the finding to `docs/findings/<date>-gittin-listed-keys-loose.md`, add an
`## Outcome` below, and `python3 scripts/board.py finish 2026-09-02-gittin-two-unjudged-yes`.
