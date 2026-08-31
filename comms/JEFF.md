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
| `jeff:boundary-end-rule` | When a ruling is what makes a passage a story at all, is that ruling part of the story we display, or the discussion that follows it? | Blocks the end rule for capability 4. His 2005 lists keep the ruling; his 2026 review notes say cut it — and both are his (Lesson 24). | **ASKED 2026-08-30** ([email](sent/2026-08-30-email-jeff.md)). Reply: *"I will get to all this soon."* |
| `jeff:mishnah-scope` | Is a story quoted inside a **Mishnah** part of this project at all, or does the database begin at the Gemara? | Our filter currently deletes them, and no harness or UI can see the loss. His two sources disagree: his blind 2005 list holds no Mishnah-only story, but he marked **correct** in review every Ketubot case the filter removes. | drafted, not sent — [`draft_next_email.md`](draft_next_email.md) §1 |
| `jeff:review-error-rate` | At what error rate does reviewing our output become worse than working from scratch? | **Sets the Classification gate**, and only he can answer it. Every other gate is provisional partly because this one is unanswered (FRAMEWORK §2b). | drafted, not sent — §2 |
| `jeff:speech-act-policy` | Passages where rabbis only speak are LOW_CONFIDENCE stories today, per his 2026-03-17 rulings; his 2026-07-06 rule reads as *not stories at all*. Should they become NOT_A_STORY, stay LOW_CONFIDENCE, or take a new **borderline** status? | It is a redefinition of a large share of the golden, so it is his call and not ours. Blocks `work/2026-08-30-story-criteria.md` phase 6c **by design**. **Two concrete cases to show him, found 2026-08-31:** Kiddushin **44a** `ר' אסי לא על לבי מדרשא` and **58a** `בעא מיניה ר' חייא בר אבין מרב הונא` — both on *his* blind list, both proposed by us and then classified `NOT_A_STORY`, neither in our golden, so no review round has ever put them in front of him. They are why Kiddushin's recall reaching output is 91.1% rather than 93.3% ([finding §4](../docs/findings/2026-08-31-kiddushin-recall.md)). Ask about these two rather than the policy in the abstract. | not drafted — needs the 6a count first, but the two cases are ready |
| `jeff:appendix-separate` | Please keep your appendix of "stories you and Claude found" a **separate file**, or mark its entries. | Costs him nothing and **cannot be reconstructed afterwards**. Five Kiddushin entries were merged in unmarked and we caught it only because the appendix survived separately (Lesson 29). Gittin, Yevamot and Eruvin are still clean — the window closes the moment we send him results for them. | not sent — **say it before the first review round on a new tractate, not after** |

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
