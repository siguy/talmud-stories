# 35 proposals read as "on his list" and are not — the loose window, measured in the other direction

**2026-09-03.** The Gittin golden turned up two `YES`-tier proposals credited to expert
stories they do not overlap ([`gittin_golden`](2026-09-02-gittin-golden.md)). Two is not a
rate (Lesson 18), so this measures it on all three tractates.

Reproduce:

```bash
python3 scripts/audit_proposal_credit.py --out results/recall/proposal_credit_audit.json
```

## Measured

| tractate | proposals | strict | **loose-only** | unlisted | of the loose-only, top-confidence |
|---|---|---|---|---|---|
| **Ketubot** | 183 | 127 | **19** | 37 | **6** |
| **Kiddushin** | 106 | 74 | **9** | 23 | **3** |
| **Gittin** | 158 | 110 | **7** | 41 | **2** |
| | | | **35** | | **11** |

**Not a Gittin accident.** Ketubot is the worst of the three in absolute terms and the
defect has been there since the first recall measurement.

The top-confidence cases are the ones to look at, because a `YES` or `HIGH_CONFIDENCE`
proposal credited to his list is exactly the claim that gets quoted:

| | credited to | what our span actually is |
|---|---|---|
| Ketubot 81b:3-10 `YES` | `ketubot_088` | the man in Pumbedita stopping his brother |
| Ketubot 103b:20-25 `YES` | `ketubot_121` | Rabbi's last days, summoning his sons |
| Ketubot 25b, 50b, 65a, 106a | 4 entries | `HIGH_CONFIDENCE` |
| Kiddushin 12b:4 `YES` | 3 entries at once | the blue stone and Rav Ḥisda |
| Kiddushin 39b, 45a | 5 entries | `HIGH_CONFIDENCE` |
| Gittin 57b:0-4 `YES` | `gittin_079` | Nebuzaradan and Zechariah's blood |
| Gittin 68a:7-12 `YES` | `gittin_097` | Solomon and Ashmedai |

Several are credited to **three of his entries at once**, which is the signature: one
window covering a run of consecutive stories on a daf, and our span landing somewhere
inside it.

## What is and is not wrong here

**The recall figure is not wrong.** Recall asks *did we find HIS stories*, and a generous
window is the right instrument for that — it is the strict/loose split that keeps it
honest, and both are already reported. Nothing in this finding moves 87.9% / 83.3% /
97.3%.

**What is wrong is reading the same association backwards.** "This proposal sits in the
window of one of his stories" was silently taken to mean "this proposal is on his list."
It is not the same claim, and 35 spans are the difference.

The consequences are all on the precision side:

- **The unlisted-extras populations were understated.** Gittin's screen held 30 and should
  have held 37; the page sent to Jeff asked 25 questions and should have asked 32.
- **An email told him** every one of our top-confidence Gittin proposals was on his list.
  Already recorded as a correction owed; this finding says the same shape exists on the
  other two tractates, where no such claim has been sent.
- **`results/recall/gittin_listed_keys.json` is built this way** and should not be read as
  a list of corroborated proposals.

## What is unaffected, and why that is the useful part

**The Gittin golden is correct as built.** It used the strict test, put its 110 strict
matches in `expert_blind_list` and left the 7 loose-only in `unlabelled_proposals`. The
Classification point estimate (83.7–86.7%) is computed from that golden, so it is right
too.

That was not luck. The golden was built strictly on the principle that an entry has to
carry an expert label, and `unlabelled_proposals` exists to hold the residue instead of
guessing at it. **The design decision that felt fussy at the time is the one that kept
this defect out of the golden**, and it is worth noticing which kind of care paid off:
not extra checking, but refusing to write down a label nobody had given us.

## Loose-only does not mean wrong

It means **unverified**, and the two are constantly confused. A loose-only proposal is one
of:

- a real story of ours that his list happens not to name (Nebuzaradan almost certainly);
- our mis-bounding of a story that *is* his, landing outside its segments;
- a false positive.

Nothing here distinguishes them, and nothing should try to — that is a verdict, and
verdicts come from Jeff. The 11 top-confidence cases go on the next review page:
[`work/2026-09-03-loose-credited-proposals.md`](../../work/2026-09-03-loose-credited-proposals.md).

## The rule worth keeping

**An association built for one direction does not survive being read in the other.** The
window is deliberately generous because recall should be hard to fail by a technicality.
That same generosity, read backwards, is a free pass. Any future measure that joins our
output to an expert's list should state which direction it is asking in, and use the
matching test.
