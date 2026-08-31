# Capability 6 — Publication

**Definition:** the resource itself — every story with its boundaries, classification and
stated accuracy, plus the columns Jeff asked for, editable by scholars. See
[`FRAMEWORK.md` §1.6](../../FRAMEWORK.md).
**Gate:** not yet defined.
**Current:** **not started.** No metric, no schema in code, no editable surface. What
exists is a public *explainer* site and a set of per-round review pages — neither of which
is the resource.

*Written 2026-08-30 from the sources in `work/done/2026-08-30-capability-histories.md`. History, not status.*

---

## Waves are not capabilities

No wave belongs to Publication. It has never had one, and that is the honest state: this
capability is the **goal**, and its requirements set everyone else's bars
([`FRAMEWORK.md` §1.6](../../FRAMEWORK.md)) — but nothing has been built toward it except
the explainer site below.

That inversion is worth naming. What the published page must *show* is what determines how
right the boundaries need to be, how a borderline classification is displayed, and what
"we found every story" is allowed to mean. Four of the five gates in FRAMEWORK are
provisional precisely because that question has not been answered
([§2b](../../FRAMEWORK.md)).

---

## What we tried

| when | what | outcome | evidence |
|---|---|---|---|
| 2026-01-22 | Embedded-JSON HTML at the repo root so GitHub Pages can serve it with no build step | shipped; still the delivery mechanism | `9e37d93`, `0a9dcd5` |
| 2026-01-26 | **Public site redesigned for a non-technical audience** — `index.html` (mission, team, credits), `approach.html` (pipeline), `validation.html` (the expert validator), `history.html` (version timeline), plus [`docs/WEBSITE_PLAN.md`](../WEBSITE_PLAN.md) as the maintenance contract. Sefaria, Google Gemini and Anthropic credited | shipped | `9e3b85c` |
| 2026-02-16 | Site updated to the v7 / Gemini 3 Flash era: 222 pages, 153 stories, 92.1%; a "The Journey: 50% to 92%" section | shipped | `76cab37` |
| 2026-02-22 | Site updated again for v8: 172 stories, 96.3% | shipped — **and never updated since** | `e3f2957` |
| 2026-07-06 | **Jeff re-specifies the end product.** Not a static published corpus: a **living, crowd-sourced, editable database**. Any scholar can flag *not a story* / *remove*, mark **borderline**, or suggest additions, gradually; he or a small editor group finalises; **contested and borderline cases are kept and flagged, not silently resolved**. Three extra per-story columns: **notes, references to scholarship, Yerushalmi parallels** | recorded as a decision; **nothing built** | [ledger Part 2(d)](../../validation/feedback/jeff_2026-07-06_feedback_ledger.md) |
| 2026-08-28 | **Jeff has already designed the schema he asked for.** His 2005 Ketubot table has four columns — מיקום / טקסט / מקבילות / הערות (location / text / parallels / notes) — with the parallels column already populated with Yerushalmi and midrashic references | measured, and it is a free design input: adopt his shape rather than inventing one | [`recall_measurement` §2](../findings/2026-08-28-recall-measurement-ketubot.md) |
| 2026-08-30 | The accuracy claim the resource would carry becomes quotable: recall stated as **loose *and* strict**, precision as a **range**, every number naming its dataset and saying BLIND or CIRCULAR | this is the substrate a published error rate is made of; see [`FRAMEWORK.md` §3](../../FRAMEWORK.md) | `4de7135`, `2cd1094` |

## What we reverted, and why

**Nothing — because nothing has been built.** But two decisions were *reversed on the
specification*, and both came from Jeff:

**1. Static published corpus → living crowd-sourced database (2026-07-06).**
The roadmap had assumed a corpus that gets published once with a stated error rate. Jeff's
model is an open editable interface where contested cases are surfaced rather than
decided. This is not a delivery-format preference; it changes what the upstream
capabilities owe. A **borderline** verdict stops being an evasion and becomes a legitimate
output — which is exactly why
[`FRAMEWORK.md` §1.3](../../FRAMEWORK.md) singles Classification out as the one capability
where "mark it borderline and let database users decide" is a real answer.

**2. Fixed validation panel → open crowd-sourcing (same reply).**
Recorded in [Review](5_review.md); its consequence here is that the published artifact
must carry per-story verdict state, editable by people who are not us.

**And one thing that was never decided and should have been:** the site's numbers.
`index.html` still says **172 stories / 96.3%**, last touched 2026-02-22 (`e3f2957`) — six
months and four detector versions ago, from a v8-era review statistic that is not any
current measure of anything. It sits on the public GitHub Pages site. This is exactly the
failure mode `CLAUDE.md` forbids for the repo's own docs ("nothing may carry a count, a
score, or an 'active version' claim"), applied to the one surface strangers actually read.
**Measured 2026-08-30 by reading the file.**

## Current best — the exact configuration

There is no publication artifact. There are two things that are sometimes mistaken for
one:

- **The explainer site** — `index.html`, `approach.html`, `validation.html`,
  `history.html` at the repo root, served by GitHub Pages, maintained per
  [`docs/WEBSITE_PLAN.md`](../WEBSITE_PLAN.md). It describes the project. It does not
  contain the stories, and its statistics are stale (above).
- **The review UIs** — `validation/ui/*.html`, generated per round by
  `validation/generators/*.py`. These *do* contain stories with text in both languages,
  and since `b394489` they render both languages from one code path with the proposed span
  **highlighted inside the full text** rather than trimmed to. But they are per-round
  snapshots aimed at one reviewer, with verdicts in `localStorage`. They are not editable
  by anyone else, they carry no notes/parallels/scholarship columns, and they show no
  accuracy statement.

**The nearest thing to the resource is the goldens** —
`results/canonical/ketubot_canonical.json` (187 entries, 164 accepted) and
`kiddushin_canonical.json` (96 / 85), which hold expert-validated stories with boundaries,
classifications and Jeff's notes. The 2026-07-06 review called these "the real asset…
a scholarly resource independent of any detector"
([§2](../findings/2026-07-06-approach-review-and-scaling.md)). They are a *record*,
not a publication: no reader-facing surface, no stated error rate, no edit path.

One structural fact about them, stated because it is the difference between a record and a
resource: **a golden built from detector output can only contain what we proposed.** Five
stories on Jeff's blind Ketubot list were in no golden at all until 2026-08-30 (`2e61035`),
and the ruler now names 6 more for Ketubot and 6 for Kiddushin that are still absent
(`4de7135`, `work/2026-08-30-golden-completeness.md`). Until that third source is folded in,
"golden" means *our proposals, corrected* rather than *the best available answer for what
is in this tractate*.

## Distance to gate

**No gate exists, and inventing one here would repeat the mistake FRAMEWORK §2b was
written to stop.** The gate is downstream of a question that is Simon's, not a technical
one:

> if we publish "every story in the Talmud," what miss rate makes that claim false?
> 1 in 20? 1 in 50?

That single number sets Triage and Detection by backward allocation
(`triage × detection = end-to-end`), and it is a claim about the product, which is this
capability ([`FRAMEWORK.md` §2b](../../FRAMEWORK.md)). A second, Jeff's, sets
Classification: at what error rate does reviewing our output become worse than working
from scratch? Both are drafted in ask-order
([`email_jeff_next_open_questions.md`](../../comms/email_jeff_next_open_questions.md));
neither is answered.

**What is already known about the scale being published:** 37 tractates, 2,711 dapim;
194 dapim validated so far (~7%); a naive density extrapolation from Ketubot+Kiddushin
(1.38 stories/daf) gives ≈3,700 stories, realistically 2,500–4,500, since density varies
enormously by seder ([§5.1](../findings/2026-07-06-approach-review-and-scaling.md)).
Compute for the whole corpus is ~$10–25.

## Ceiling

**None known** — nothing has been attempted, so nothing has hit a limit.

The one constraint that is already visible is **inherited, not intrinsic**: whatever the
resource claims about its own completeness is bounded by the blind ground truth available
to check it. Today that is Ketubot (149) and Kiddushin (90), with Gittin (112), Yevamot
(102) and Eruvin (73) parsed but never run. Beyond those five tractates there is no blind
list at all, so a corpus-wide accuracy statement would have to be extrapolated and said to
be extrapolated.

## Untried

Everything. Listed in the order the dependencies fall, not by size:

- **Answer the product question** — the acceptable miss rate for "every story in the
  Talmud." It is the cheapest item on this page and it unblocks four provisional gates.
- **Design the schema, from Jeff's own table.** Per-story: location, text (both
  languages), boundaries, classification, **borderline flag**, **notes**, **references to
  scholarship**, **Yerushalmi parallels**, plus per-story verdict state for editing. His
  2005 columns already give four of these; the borderline flag and verdict state are what
  the crowd-sourcing model adds
  ([ledger Part 2(d)](../../validation/feedback/jeff_2026-07-06_feedback_ledger.md),
  [`recall_measurement` §2](../findings/2026-08-28-recall-measurement-ketubot.md)).
- **Emit a `borderline` flag from the pipeline.** Nothing in the detector produces one
  today, so the resource cannot show what Jeff asked it to show. Blocked in part on his
  Wave 6b answer — see [Classification](3_classification.md).
- **Build the editable interface** — open, gradual, multi-scholar, with an editor group
  finalising. This is also [Review](5_review.md)'s throughput answer; the two capabilities
  meet here.
- **State the error rate on the page.** The measurement vocabulary now exists (loose vs
  strict recall, a precision range, BLIND vs CIRCULAR named per number). Publishing a
  number without its dataset is the mistake FRAMEWORK §3 says cost this project months.
- **Make the goldens complete** before calling them a resource — fold in every verdict,
  and add the stories we never proposed (`work/2026-08-30-golden-completeness.md`).
- **Fix or retire the public site's statistics.** Either update `index.html` from a
  current measurement or remove the numbers; a stale 96.3% on a public page is worse than
  no number.
- **Decide what happens to Mishnah stories.** They are currently deleted from the output
  by a filter nothing catalogues, scores or displays — while Jeff asked for them to be
  *catalogued separately*. That is a publication-shape question (one bucket or two) as
  much as a classification one
  ([`mishnah_filter_delta`](../findings/2026-08-30-mishnah-filter-delta.md)).
- **Nothing here has been declined.** Unlike the other five capabilities, this one has no
  failures to record and no dead ends to avoid — which is precisely why it is the least
  understood of the six.
