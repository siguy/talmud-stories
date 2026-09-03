# Jeff Rubenstein — one file

Every open question, every correction we owe him, and everything we have sent. **One
correspondent, one file.** Before 2026-08-30 the open questions lived in three places at
once — `STATUS.md`, `FRAMEWORK.md` §2b, and an ad-hoc draft — three sessions wrote
competing drafts, and one draft went out carrying a factual error about Ketubot 77a.

**What this file is not.** `validation/feedback/*_ledger.md` stays exactly where it is and
is not replaced. It tracks the per-item disposition of what Jeff *said*, which is a
different job from tracking what we have *asked*, and it exists because of Lesson 1.

Each open question has a **slug**. A work item that cannot conclude without his answer
names that slug in its `awaiting:` field; one that cannot start names it in `blocked_by:`.
`scripts/board.py` reads the table below and cross-references both.

---

## Open questions

| slug | question | why it matters | status |
|---|---|---|---|
| `jeff:boundary-end-rule` | When a ruling is what makes a passage a story at all, is that ruling part of the story we display, or the discussion that follows it? | Blocks the end rule for capability 4. His 2005 lists keep the ruling; his 2026 review notes say cut it — and both are his (Lesson 24). | **ASKED 2026-08-30**, unanswered — *"I will get to all this soon."* **Email 1, item 2**, sharpened with the start-vs-end split |
| ~~`jeff:mishnah-scope`~~ **ANSWERED 2026-09-01** | A Mishnah story belongs to the **Mishnah** corpus; the Talmud's quotation of it is a **Talmudic** story, and eventually both, cross-referenced. | **Our pipeline was already doing exactly this** — Stage 4g withholds 10a/45b/74a and keeps 10b/46a/74b. The Gittin 'double count' was not a defect but the two halves of his answer. What changes: `mishnah_stories[]` must become a **catalogued bucket rather than a deletion**, and Ketubot 14b/77a stop being Talmud false negatives. | closed — [answers](../docs/findings/2026-09-02-jeff-answers-gittin.md) |
| `jeff:review-error-rate` | At what error rate does reviewing our output become worse than working from scratch? | **Sets the Classification gate**, and only he can answer it. Every other gate is provisional partly because this one is unanswered (FRAMEWORK §2b). | **Email 2, item 7** — hold until 6a gives it an anchor |
| `jeff:speech-act-policy` **PARTLY ANSWERED 2026-09-01** | *"Sometimes dialogue can be counted as stories… when there is conflict and implied change. But these would always be borderline. Unfortunately there are no real hard and fast rules."* So: **no general rule, and `borderline` is the right column** — which the axis UI already emits. He ruled the three Gittin cases individually: **57a Beitar is clearly a story** (a custom framing a one-time event — our HABITUAL rejection stops at the frame); **57a the fertility exchange is NOT a story and his list was wrong** ("Great to have the AI correct it!"); **38b IS a story**, embedded inside Rabba's dictum as R. Yoḥanan's two uprooted families. Recall corrected to **108 of 111**. What remains open is the *general* policy for the ~12 thin case-and-ruling passages, and his answer says that may need us to propose a rule rather than ask for one. | two of the three are now OUR defects — [answers](../docs/findings/2026-09-02-jeff-answers-gittin.md) |
| `jeff:miss-rate` | If we publish this as "the stories in tractate X", what miss rate would make that claim false — 1 in 20? 1 in 50? | **Sets the Triage and Detection gates**, which are currently invented (FRAMEWORK §2b). It is a claim about scholarly completeness, so it is his to make, not ours — an earlier draft of FRAMEWORK wrongly assigned it to Simon. | **Email 2, item 7** — ask beside the six misses, not as a bare threshold |
| `jeff:deliverable-shape` | Does a published, citable corpus **with a feedback channel** meet your need for the first version — scholars flag *not a story* / *borderline* / *missing*, you or a small group adjudicate, and corrections land in the next release? | Decides what Publication has to be, which sets how right Boundaries and Classification must be. Asked as a **proposal to confirm**, not as "corpus or database?" — the second is a design question we should not outsource to a busy reader. | **Email 1, item 4** — a yes/no on the proposal below |
| ~~`jeff:axes-round`~~ **ANSWERED 2026-09-02** | He reviewed all 25 Gittin passages not on his 2005 list. **3 `yes`, 4 `borderline`, 18 `no`** — three stories we found that his list does not have (19a:16, 43b:4, 70a:22), and the first **negative** labels this project has ever had on a tractate that was never in a prompt. No extra is a `YES`, so the top-band claim in the email survives; the middle band produced zero yeses from five `HIGH_CONFIDENCE` extras. **The instrument failed even though the round succeeded:** every structured field came back empty and five boundary corrections arrived as prose ([`axis-fields-unused`](../work/2026-09-02-axis-fields-unused.md)). Unblocks [`classification-point-estimate`](../work/done/2026-08-31-classification-point-estimate.md). | closed — [verdicts](../docs/findings/2026-09-02-gittin-25-verdicts.md) |
| ~~`jeff:opening-formula`~~ **ANSWERED 2026-09-01** | *"not technically part of the stories. But they are important… If not too much trouble, we should include them."* | **Reverses our 2026-09-01 rejection.** We measured the rule at 9 fixes / 8 breaks and dropped it; his answer re-reads the 8 — those are targets where his own start sits after the formula, and he says the lists 'were sloppy and preliminary'. Re-measured on all four blind sets: **10 of our late starts fixed, 10 targets corrected in the ruler**, 17 late for other reasons and still unexplained. Now a **principled** rule, not a tuned one (Lesson 37). | closed — [answers](../docs/findings/2026-09-02-jeff-answers-gittin.md) |
| `jeff:appendix-separate` | Please keep your appendix of "stories you and Claude found" a **separate file**, or mark its entries. | Costs him nothing and **cannot be reconstructed afterwards**. Five Kiddushin entries were merged in unmarked and we caught it only because the appendix survived separately (Lesson 29). Gittin, Yevamot and Eruvin are still clean — the window closes the moment we send him results for them. | **Email 1, item 5** — one sentence, and the window closes when we send new-tractate results |

### On `jeff:deliverable-shape` — what we would propose

His 2026-07-06 answer asked for a living, crowd-sourced, editable database with contested
cases kept and flagged. That is the right end state and it is a large build. A **published
corpus with a feedback channel** is the same thing minus write access, and it is reachable
now:

- the corpus is versioned, citable and static — which is what makes it usable in
  scholarship at all, and what an editable database is *worse* at
- feedback is a per-story channel (flag *not a story* / *borderline* / *missing*, with a
  note), which is the crowd-sourcing he asked for on the reading side
- adjudication stays with him or a small group, and accepted corrections ship in the next
  release — so the corpus keeps the property that a citation resolves to fixed text
- it needs the `borderline` flag the pipeline does not yet emit, and it reuses the review
  UI we already build every round

The honest tradeoff to put to him: **a citable release cannot also be silently mutable.**
Live edits and stable citation are in tension, and versioned releases are how every other
scholarly corpus resolves it. If he wants edits visible immediately, that is a different
product and worth knowing before we build.

## Ask order — seven questions is two emails, not one

**The constraint that decides this:** he answered a single question with *"I will get to
all this soon."* Seven will get the same reply, or none. The sent log shows the same
curve from another angle — 187 verdicts, then 96, then **1**, then 15.

Six principles, applied below:

1. **Open by giving, not asking.** The 77a correction goes first. We owe it, and a message
   that starts by fixing our own error reads differently from one that starts with a list.
2. **One hard question per email.** Abstract judgment calls are what stall; more than one
   and none get answered.
3. **Anchor every number question in real cases.** Do not ask him to produce a tolerance
   from nothing — show him what we actually miss and ask whether *that* is acceptable.
   This is the change that makes `jeff:miss-rate` answerable at all.
4. **Free asks ride along.** `jeff:appendix-separate` costs him one line and cannot be
   reconstructed later. It goes in every email until he acts on it.
5. **Never ask what our own work can answer first.** `jeff:speech-act-policy` without the
   6a count is a vague question about an unnamed number of passages.
6. **Time-critical goes now regardless of size.**

### Email 1 — send now

| # | item | why here |
|---|---|---|
| 1 | **The 77a correction** (see below) | We owe it. It also sets up #3 — same daf. |
| 2 | `jeff:boundary-end-rule` | **Already asked, still blocking capability 4.** Not a re-ask: we now have evidence he has not seen — on the 32 Ketubot boundaries the two sources share, they **agree** on starts 7/7 and **agree** on ends 16/19 — so the disagreement is **3 of 19 ends and 0 of 7 starts** (84% overall). *Phrasing corrected 2026-09-01: this line previously read "split on ends 16/19", which reads as 16 disagreements when 16 is the agreement count — it was misread that way while drafting the email.* That still sharpens the ask from "what do you think" to "your two sources disagree, and only on the end edge" — but the honest magnitude is 3 cases. The Ketubot pattern does **not** reproduce on Kiddushin, where the overlap is 14 boundaries and 3 starts is not a sample ([kiddushin_boundary_set §5](../docs/findings/2026-08-31-kiddushin-boundary-set.md)). |
| 3 | `jeff:mishnah-scope` | Concrete: two named passages, drafted in [`draft_next_email.md`](draft_next_email.md) §1. Pairs with #1. |
| 4 | `jeff:deliverable-shape` | Looks big, is cheap — it is a yes/no on a proposal, not an open design question. Answering it is one line. |
| 5 | `jeff:appendix-separate` | One sentence. **The window closes the moment we send him results for Gittin, Yevamot or Eruvin**, and it cannot be reconstructed afterwards (Lesson 29). |

One hard question (#2), two concrete ones, one yes/no, one freebie — and it opens with a
correction rather than a request.

### Email 2 — after phase 6a runs

| # | item | why it waits |
|---|---|---|
| 6 | `jeff:speech-act-policy` | Needs the 6a blast-radius count. With it: *"N stories currently in your golden would be demoted by your newer rule — here are four."* Without it, unanswerable. **Send the mirror image alongside it:** Kiddushin **44a** is on *his* 2005 list and we reject it as `NOT_A_STORY` — the rule cuts both ways. **Do not send 58a**: his own margin note on it says *"Not sure this is a story. Very minimal."*, so asking would spend a scarce verdict on a question he answered in 2005 (2026-08-31). |
| 7 | `jeff:miss-rate` **and** `jeff:review-error-rate`, asked together | Both ask the same thing — *what error can you live with* — one about what we miss, one about what we wrongly include. Answering either primes the other, and splitting them across emails wastes that. |

**How to ask #7 so it is answerable.** Not *"what miss rate makes the claim false?"* — that
is a number from nothing, and it is the shape of question he has already deferred once.
Instead show him the six Ketubot stories on his own 2005 list that we miss, with their
openers, and ask: *would a published corpus that misses these six still be honest as "the
stories in Ketubot"?* Same for precision: show him a sample at the current rate and ask
whether reviewing it beats starting from scratch. **A judgment on real cases is a
different, much easier act than producing a threshold.**

## Corrections owed

| what we told him | what is true | where |
|---|---|---|
| The 2026-09-01 email said *"All 59 we called 'certain' are on your list."* | **False for two of them.** Gittin **57b:0-4** (Nebuzaradan and Zechariah's blood) and **68a:7-12** (Solomon and Ashmedai) are `YES`-tier and on no list of his. They were counted as matches by the **loose** window, which is up to 14 segments wide and credited a neighbouring story on the same daf — the third and fourth known instance of that failure. The second half of the claim — *"none of the extras we propose is one"* — still stands. Both passages go on the next page he sees. | [`gittin_golden`](../docs/findings/2026-09-02-gittin-golden.md), [`two-unjudged-yes`](../work/2026-09-02-gittin-two-unjudged-yes.md) |
| The 2026-08-30 email said Ketubot 77a is a story "our own set has." | It is not. Our golden holds a **different** 77a story — the Sidon tanner at seg 8 — while his 2005 entry is at segs 13-14. Two stories on one daf, conflated by our locator's coarse window. **The substance stands** (we do miss his); the claim did not. | [`2026-08-30-recall-miss-diagnosis.md`](../docs/findings/2026-08-30-recall-miss-diagnosis.md) |

Pair this with `jeff:mishnah-scope` in the same email — the correction and the scope
question are about the same daf, and the pairing is the clearest way to show why it matters.

## Sent log

Everything in [`sent/`](sent/), dated. What was asked, and what came back.

| date | what we sent | what came back |
|---|---|---|
| 2026-01-08 | first Ketubot review UI | 25 verdicts |
| 2026-01-25 | v5.1 package — three drafts (comprehensive / direct / executive) | the 50%-false-positive verdict on v4.1 that reset the project |
| 2026-02-14 | v7 update | — |
| 2026-02-22 | v8 delta review — only what changed, in 3 tiers | 49 verdicts |
| 2026-03-17 | canonical review, all 189 stories in 3 sections | **187 verdicts** — the round the Ketubot golden is built on |
| 2026-03-25 | v10 golden-dataset update | — |
| 2026-04-07 | Kiddushin run | **96 verdicts** (2026-04-23), plus the missed-stories appendix |
| 2026-05-25 | Wave 3 Kiddushin UI | **1 verdict** |
| 2026-06-03 | Wave 3 round 2 | 4 Ketubot corrections |
| 2026-06-15 | Wave 4 UI + roadmap questions | **15 verdicts**, 11 of them negative, plus his Part 2 strategic answers: use his old blind lists, demote Ein Yaakov, crowd-source the database |
| 2026-08-30 | the boundary question, and four tractate lists requested | four expert lists (Kiddushin, Gittin, Yevamot, Eruvin) and *"I will get to all this soon"* |
| 2026-09-01 | [Email 1](../comms/2026-09-01-email-jeff-gittin.md) — Gittin 108/112, the four capabilities, **five questions** | **two replies in two days.** 2026-09-01: prose answers to questions 1-4 ([findings](../docs/findings/2026-09-02-jeff-answers-gittin.md)). 2026-09-02: **all 25 verdicts** on the review page ([findings](../docs/findings/2026-09-02-gittin-25-verdicts.md)) |

**The pattern worth seeing in that last column:** after the two exhaustive rounds, review
stopped being exhaustive. 1 verdict on 95 stories, then 15. Review throughput is the
project's bottleneck, and it is capability 5's whole subject.

**And the 2026-09-01 row is the counter-example, which is more useful than the pattern.**
A page of 25 came back complete in one day, after a year in which 95 stories drew 1
verdict. The two rounds that got answered were the two that were **short and bounded**;
the ones that starved were open-ended. Send him 25, not 150.

## Things he decided that we should not re-propose

- **Ein Yaakov as a recall probe** — declined 2026-07-06. It is all aggada and structurally
  omits the halakhic stories this database explicitly includes. It was proposed anyway
  after the decision was recorded, which is one of the reasons `docs/capabilities/` exists.
- **A cold-read of 10 random dapim** — declined in favour of his existing detector-blind
  lists, which he then sent.
- **A fixed validation panel** — declined in favour of open crowd-sourcing, with contested
  cases kept and flagged rather than silently resolved.
