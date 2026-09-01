# The 27 nobody had read: 15 are legal, 4 are candidates, and all 4 sit on questions Jeff hasn't answered — 2026-09-01

**Capability: 1 Triage (and ground truth).** **Status: screened, not adjudicated.**
**No API calls.** First pass over the population left open by
[`2026-09-01-corrected-triage-ablation.md`](2026-09-01-corrected-triage-ablation.md):
the proposals that exist only because Stage 1 was overridden, scored as false positives
purely because the golden cannot contain a story from a page triage never let anyone see.

**Reproduce:** `python3 scripts/merge_triage_recall_run.py --tractate {ketubot,kiddushin}`,
then the screen in
[`results/v11/triage_precision/unread_proposals_screened.json`](../../results/v11/triage_precision/unread_proposals_screened.json).

**The screen below is this session applying the project's own `NARRATIVE_EVENT`
criterion — a named person doing a specific thing. It is not an expert verdict, and its
job is to decide which passages deserve Jeff's scarce attention, not to pre-empt it.**

---

## The population is smaller than "27" suggested

The corrected ablation counted a **+27 golden false-positive delta**. At proposal level
the picture is cleaner, and better for triage:

| | Ketubot | Kiddushin | total |
|---|---|---|---|
| proposals that exist only without triage | 36 | 24 | **60** |
| …the detector **itself** classified `NOT_A_STORY` | 18 | 14 | **32** |
| **would actually reach a reviewer** | 18 | 10 | **28** |

**More than half never reach a human at all** — Stage 3/4 rejects them. Any cost stated
as "60 extra proposals" overstates the reviewer burden by a factor of two. 28 is the real
number, and it matches the 2026-08-31 finding's own count exactly.

## The screen

| | count | what they are |
|---|---|---|
| **clearly legal** | **15** | baraita hypotheticals, Mishna, give-and-take, one parable. Stage 1 was right about these |
| already on Jeff's list | 5 | the 4 known recoveries (Ketubot 72b; Kiddushin 10b, 14a, 69a); 10b drew two proposals |
| his story, re-bounded or ambiguous | 4 | Ketubot 22b, 51a, 102b; Kiddushin 58b — each lands on a daf his list already covers |
| **genuinely absent from his list, and narrative** | **4** | below |

So of 28 reviewer-facing proposals, **15 are noise, 9 are Jeff's own material re-found or
re-bounded, and 4 are real questions.** The 8 points of precision Stage 1 buys is mostly
genuine — but it is not *entirely* genuine, and the residue is not random.

## The four candidates — and why none is simply "Jeff missed one"

| passage | what it is | why it may be out of scope |
|---|---|---|
| **Ketubot 71a** — the incident of Beit Ḥoron | a genuine `מעשה`: a man vows his father out of benefit, then gifts his property to evade it | a **Mishnaic** story, and one native to Nedarim, quoted here as precedent → `jeff:mishnah-scope` |
| **Ketubot 112b** — R. Ḥiyya bar Gamda rolling in the dust; sages moving between sun and shade | the tractate's closing Eretz Yisrael aggada; named rabbis, physical acts | habitual/aggadic rather than a single event. **Also malformed**: `start_segment -2` |
| **Kiddushin 25b** — Shmuel finds Rav's students and questions them | a specific encounter between named people | the content is pure legal Q&A → `jeff:speech-act-policy` |
| **Kiddushin 27a** — Rabban Gamliel assigns tithe to Yehoshua ben Ḥananya and Akiva ben Yosef, renting the land | a real transaction between named people | cited as legal precedent, not told as a story |

**That pattern is the finding.** Four candidates, and every one falls inside a scope
question already open with him — Mishnaic stories, speech-only passages, and stories
quoted as precedent rather than narrated. **None of them suggests his 2005 lists are
careless.** They suggest the lists encode a scope rule he has never written down, and
that our detector does not share it.

## What this settles, and what it does not

**Settles:** the blind lists are **not badly incomplete**, and Stage 1's precision gain is
**mostly real**. The worry that "96% recall" might be 96% of an exam missing many
questions is not supported — on this population, at least, the exam looks close to
complete.

**Does not settle:** whether it is missing *any*. That needs Jeff on four passages, and
the answer is a scope ruling, not a count. Note the sampling limit: these 4 come only from
pages Stage 1 discarded, so they cannot give a corpus-wide rate for what his list omits —
only existence, and even that is now contingent on scope.

**And it re-points the ask.** The four candidates are worth almost nothing as four
separate questions and quite a lot as evidence inside `jeff:mishnah-scope` and
`jeff:speech-act-policy`, which are already drafted and queued. They are **concrete
passages for questions currently asked in the abstract** — which is the form his last two
rounds actually answered (1 verdict and 15). Added to [`comms/JEFF.md`](../../comms/JEFF.md)
as evidence under the existing slugs, **not as new questions**.

## Two defects confirmed on the way

- **The negative segment index is real and still unfixed.** `Ketubot 112b` proposes
  `start_segment -2`. The 2026-08-31 finding reported it; nothing validates that a
  proposed span lies within its page, and this screen hit it again independently.
- **A proposal can duplicate a story the run already has on a neighbouring daf.**
  Ketubot 51a and Kiddushin 58b are almost certainly Jeff's own entries re-proposed from
  the other side of a daf boundary. That is a cross-page merge gap, not a discovery, and
  it inflates any raw count of "new" proposals.
