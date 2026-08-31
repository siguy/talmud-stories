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
| `jeff:mishnah-scope` | Is a story quoted inside a **Mishnah** part of this project at all, or does the database begin at the Gemara? | Our filter currently deletes them, and no harness or UI can see the loss. His two sources disagree: his blind 2005 list holds no Mishnah-only story, but he marked **correct** in review every Ketubot case the filter removes. | **Email 1, item 3** — drafted, [`draft_next_email.md`](draft_next_email.md) §1 |
| `jeff:review-error-rate` | At what error rate does reviewing our output become worse than working from scratch? | **Sets the Classification gate**, and only he can answer it. Every other gate is provisional partly because this one is unanswered (FRAMEWORK §2b). | **Email 2, item 7** — hold until 6a gives it an anchor |
| `jeff:speech-act-policy` | Passages where rabbis only speak are LOW_CONFIDENCE stories today, per his 2026-03-17 rulings; his 2026-07-06 rule reads as *not stories at all*. Should they become NOT_A_STORY, stay LOW_CONFIDENCE, or take a new **borderline** status? | It is a redefinition of a large share of the golden, so it is his call and not ours. Blocks `work/2026-08-30-story-criteria.md` phase 6c **by design**. **Two cases measured 2026-08-31 that point the other way**, and they are his call rather than ours: Kiddushin **44a** `ר' אסי לא על לבי מדרשא` and **58a** `בעא מיניה ר' חייא בר אבין מרב הונא` are on *his own blind list*, we proposed both and then classified both `NOT_A_STORY`, and neither is in our golden — so no review round has ever shown them to him. They are why Kiddushin's recall reaching output is 91.1% rather than 93.3% ([finding §4](../docs/findings/2026-08-31-kiddushin-recall.md)). | **Email 2, item 6** — blocked on our own phase 6a, not on him |
| `jeff:miss-rate` | If we publish this as "the stories in tractate X", what miss rate would make that claim false — 1 in 20? 1 in 50? | **Sets the Triage and Detection gates**, which are currently invented (FRAMEWORK §2b). It is a claim about scholarly completeness, so it is his to make, not ours — an earlier draft of FRAMEWORK wrongly assigned it to Simon. | **Email 2, item 7** — ask beside the six misses, not as a bare threshold |
| `jeff:deliverable-shape` | Does a published, citable corpus **with a feedback channel** meet your need for the first version — scholars flag *not a story* / *borderline* / *missing*, you or a small group adjudicate, and corrections land in the next release? | Decides what Publication has to be, which sets how right Boundaries and Classification must be. Asked as a **proposal to confirm**, not as "corpus or database?" — the second is a design question we should not outsource to a busy reader. | **Email 1, item 4** — a yes/no on the proposal below |
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
| 2 | `jeff:boundary-end-rule` | **Already asked, still blocking capability 4.** Not a re-ask: we now have evidence he has not seen — his 2005 list and his 2026 notes agree on **start** boundaries 7/7 and split on **ends** 16/19. That sharpens it from "what do you think" to "your two sources disagree, and only on one edge." |
| 3 | `jeff:mishnah-scope` | Concrete: two named passages, drafted in [`draft_next_email.md`](draft_next_email.md) §1. Pairs with #1. |
| 4 | `jeff:deliverable-shape` | Looks big, is cheap — it is a yes/no on a proposal, not an open design question. Answering it is one line. |
| 5 | `jeff:appendix-separate` | One sentence. **The window closes the moment we send him results for Gittin, Yevamot or Eruvin**, and it cannot be reconstructed afterwards (Lesson 29). |

One hard question (#2), two concrete ones, one yes/no, one freebie — and it opens with a
correction rather than a request.

### Email 2 — after phase 6a runs

| # | item | why it waits |
|---|---|---|
| 6 | `jeff:speech-act-policy` | Needs the 6a blast-radius count. With it: *"N stories currently in your golden would be demoted by your newer rule — here are four."* Without it, unanswerable. **Send the mirror image alongside it:** Kiddushin 44a and 58a are on *his* 2005 list and we reject both as `NOT_A_STORY` — the rule cuts both ways, and these two cost us 2.2 points of Kiddushin recall at the output (measured 2026-08-31). |
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

**The pattern worth seeing in that last column:** after the two exhaustive rounds, review
stopped being exhaustive. 1 verdict on 95 stories, then 15. Review throughput is the
project's bottleneck, and it is capability 5's whole subject.

## Things he decided that we should not re-propose

- **Ein Yaakov as a recall probe** — declined 2026-07-06. It is all aggada and structurally
  omits the halakhic stories this database explicitly includes. It was proposed anyway
  after the decision was recorded, which is one of the reasons `docs/capabilities/` exists.
- **A cold-read of 10 random dapim** — declined in favour of his existing detector-blind
  lists, which he then sent.
- **A fixed validation panel** — declined in favour of open crowd-sourcing, with contested
  cases kept and flagged rather than silently resolved.
