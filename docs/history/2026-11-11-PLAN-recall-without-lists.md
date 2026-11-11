# Plan: knowing whether we found the stories in the 32 tractates with no expert list

*Written 2026-11-11. Planning only: no model calls and no runs were made writing it. Answers Simon's 2026-11-10
"We'll need a solve for this" on §4.2 of [`docs/findings/2026-11-10-shas-accuracy.md`](../findings/2026-11-10-shas-accuracy.md).
Page counts below are **measured** from `results/v14/*/run1.json`. Every cost is **estimated** and gets a `--dry-run`
before any money is spent.*

## The short version

1. **Only a new expert list gives a BLIND recall number.** Nothing we can run ourselves does. So the first move costs
   nothing: **one line in the email to Jeff that is already drafted** (the precision sample, not yet sent). Do he or
   his 2005 colleague have lists for any tractate besides the five? Does he know a published catalogue of Talmudic
   stories? He has never been asked whether the five are *all* there is. In August he was asked for "lists for other
   tractates" and sent four the same day.
2. **Two things on the list of options are already on record as declined by Jeff** (2026-07-06): a cold read of random
   pages, and Ein Yaakov as a recall probe. Both are covered below. Neither is in the recommendation. The cold read
   also fails on arithmetic: the pages triage skips hold so few stories that an expert would read about 50 pages to
   find one.
3. **What we can do without a list: screen with Gemini, then have Jeff confirm.** Do this on six sample tractates, two
   per tractate type. A second detector pass on the pages triage skipped finds what triage lost. A new "what's missing
   here?" pass on the pages we examined finds what Detection missed. Both screens are first tested on Eruvin and
   Yevamot, where Jeff's lists say what the right answer is. Jeff then confirms only what the screens flag: about
   **1–2 hours** of his time, not 8–16. **Gemini cost about $35** (range $25–45 billed).
4. The result is a **per-type estimate of missed stories with an interval**, labelled **indicated**. The confirmed
   finds are a **measured lower bound**. It is not a BLIND recall figure, and the plan says so wherever it reports
   one.

## Terms

- **Amud / page:** one side of a daf (2a, 2b). Every "page" count here is amudim, as in the run files.
- **Triage loss:** a story on a page triage skipped, so Stage 2 never looked at it. **Detection loss:** a story on a
  page we examined that Stage 2 never proposed. They add up to end-to-end recall. Losses to the site's
  "definite in both runs" rule are a third thing (grading). The accuracy finding measured those separately, and they
  are out of scope here.
- **Screen:** a cheap, automatic first pass that flags candidates for a human. **Sensitivity:** of the stories really
  there, the share the screen flags.
- **Calibrate:** run the screen where the answer is already known (a tractate with Jeff's list) to measure its
  sensitivity before trusting it anywhere else.
- **Stratum:** a group of similar tractates, sampled separately. Here they are the three groups the precision sample
  already uses (`scripts/build_precision_sample.py`): **aggadic** (Sanhedrin, Megillah, Taanit, Sotah, Berakhot,
  Chagigah), **Kodashim + Niddah** (10 tractates), and **halakhic** (everything else).
- BLIND / CIRCULAR, measured / indicated / suspected: as in [`FRAMEWORK.md` §7](../../FRAMEWORK.md).

## 1. What the 32 tractates look like (measured, v14 run 1)

| stratum | tractates | amudim | examined | skipped | skip rate | list tractates like it |
|---|---|---|---|---|---|---|
| aggadic | 6 | 616 | 380 | 236 | 38% | none. Gittin's aggadic block (55b–58a) is the nearest |
| Kodashim + Niddah | 10 | 1,240 | 417 | 823 | **66%** | **none** |
| halakhic | 16 | 2,482 | 1,064 | 1,418 | 57% | Eruvin (47% skipped), Yevamot (56%), and Nashim generally |
| **total** | **32** | **4,338** | **1,861** | **2,477** | 57% | |

Two facts from the same files change the options:

- **Of the 1,861 pages we examined, only 89 have no proposal at all.** "Read the pages where nothing was found" is a
  pool of 89, so it cannot tell us about Detection loss. Detection misses sit on pages that *do* have proposals.
  Measuring them means reading examined pages against what we proposed there.
- **The lists cover four Nashim tractates and one Moed tractate.** No list covers Kodashim, where triage skips two
  pages in three (Zevachim 80%, Temurah 88%, Meilah 88%), or the aggadic tractates, where stories are densest. These
  are the two places where "indicated from the five" (Lesson 18) is weakest.

**What we would expect if the five tractates generalise** (indicated, and exactly the assumption to be tested). On
Eruvin, triage lost 2 of Jeff's 74 stories over 98 skipped amudim, and Detection missed 5 on 109 examined ones.
Applied to the 32 tractates, that is roughly **50 stories lost to triage and 85 to Detection**, against about 3,100
proposals. The plan exists to find out whether Kodashim and the aggadic tractates are anything like this.

## 2. What is already on record (read before re-proposing)

- **Cold read of random pages — declined by Jeff, 2026-07-06**
  ([ledger Part 2(a)](../../validation/feedback/jeff_2026-07-06_feedback_ledger.md)). His reason was that his
  detector-blind lists were better. That reason expires once the lists are exhausted, so it can be asked again, but
  only after Ask A below, and only in the screened form in §4.
- **Ein Yaakov as a recall or triage probe — declined by Jeff, 2026-07-06** (ledger Part 2(b);
  [`1_triage.md`](../capabilities/1_triage.md) "Untried"). It is all aggada and leaves out the halakhic stories this
  database includes. He allowed it only as a "cheap optional aggadic-only cross-check". The capability doc says not
  to re-propose it as a probe, and this plan does not.
- **"Lists for other tractates"** was asked on 2026-08-30 and answered the same day with four lists
  ([`comms/sent/2026-08-30-email-jeff.md`](../../comms/sent/2026-08-30-email-jeff.md)). Jeff said in July that he and a
  colleague "went tractate-by-tractate… before abandoning the effort" and that the lists cover "only some masekhtot".
  **Nobody has asked whether the five are all of them, or whether the colleague kept others.**
- Jeff offered in July to recruit "a few colleagues to seed some tractates and cross-check with his old lists"
  (ledger Part 2(d)). That offer covers the confirmation step in §4.
- `scripts/run_triage_recall_price.py` is **hard-wired to detector v11 and to Ketubot/Kiddushin** (`RUNS`,
  `TRIAGE_CACHES`, the `story_detector_v11` import). The step in §4 needs it generalised to v14 and to any tractate.
  It does not run as it stands.
- On discarded pages, the triage-price run found **4 real stories in 28 proposals (14%)**
  ([finding](../findings/2026-08-31-triage-recall-price.md)). A second pass on skipped pages is therefore mostly
  noise, and it has to go through the judges before anything reaches Jeff.

## 3. The options, weighed

| option | Jeff's time | Gemini cost | BLIND? | label | what it can show | what it cannot |
|---|---|---|---|---|---|---|
| **A. Ask Jeff whether he or his colleague has more lists, and whether he knows a catalogue** | ~5 min to answer | $0 | **BLIND** if a list exists (check with `check_appendix_coverage.py`; we have never run on these tractates, so a 2005 list cannot contain our output) | **measured**, for that tractate | true recall, triage and detection, with the existing harness, at no model cost | anything, if the answer is no |
| **B. Published indexes and anthologies** (§5) | ~0, or one question folded into A | $0 to align, if the work is digitised | BLIND by date: printed before the detector existed | **indicated**: each work's idea of a "story" differs from Jeff's | recall against that work's story set, after calibrating its coverage of Jeff's five lists | halakhic stories, for every aggadic anthology (Jeff's objection to Ein Yaakov applies to all of them) |
| **C. Jeff cold-reads random skipped pages and examined pages** | **~8–16 h** for ~50–100 amudim (at ~10 min per amud, **suspected**; ask him) | $0 | BLIND (he reads without our output) | **measured** on the sample | the only unscreened miss rate | anything precise: at ~2 lost stories per 100 skipped amudim, 50 amudim find about **one**, a 95% interval of roughly 0.05%–11%. **Declined once already** |
| **D. Second detector pass on skipped pages** (generalised `run_triage_recall_price.py`), sample of 6 tractates | 0 to run; it feeds E | **~$13** (769 amudim), plus ~$4 to calibrate on Eruvin and Yevamot. **All of Shas: ~$42** (2,477 amudim) | **CIRCULAR**: the detector grades the pages triage threw away | **indicated** | triage loss *relative to Detection*, per stratum, the cheap way. On Eruvin it must re-find 14b and 32b, the two stories triage lost | Detection's own misses; and whether a proposal is real, until judged and confirmed |
| **E. "What's missing" audit on examined pages**: Gemini is given a page and our proposals on it, and asked to list any story not covered | 0 to run; it feeds F | **~$10** for the sample's 516 examined amudim, ~$4.50 to calibrate | **CIRCULAR-adjacent**: same model family as the detector, so its misses may be correlated. Calibration measures how much | **indicated** | Detection loss, the larger of the two losses (5 vs 2 on Eruvin) | anything, if calibration shows it finds no more than the detector does |
| **F. Jeff (or a colleague) confirms what D and E flag** | **~1–2 h**: about 30–60 passages after the judges, at 1–2 min each in the axis review UI | ~$1–2 for the judges on new proposals | CIRCULAR selection (we chose what he sees), with an independent verdict | the confirmed finds are a **measured lower bound**; the sensitivity-corrected total is **indicated** | per-stratum missed-story counts with an interval | stories that both screens miss. That residual is what calibration bounds |
| **G. Stratify by tractate type** | — | — | — | — | a design choice, not an option: applied to D, E and F, and already used by the precision sample | — |

## 4. Recommendation

Do **A at once**, and **D + E + F on six tractates**, in this order:

**Step 0. Free, no calls (~half a day of code).** Generalise `run_triage_recall_price.py` to v14 and any tractate.
Keep its guarantees: cached triage labels, the skip decision as the only variable, and the page partition asserted
before any call. Write the audit script (E) with a `--dry-run`, and the estimator that turns confirmed finds and
calibrated sensitivity into per-stratum counts with intervals. Tests come first, as always, with the failure-injection
tests in the Lesson 21 shape.

**Step 1. Ask A (Jeff, 5 min).** One paragraph in the [precision-sample draft](../../comms/2026-11-10-email-jeff-precision-sample-DRAFT.md),
which is not yet sent: *Are the five lists everything you and your colleague finished? Did your colleague keep any
others? Is there a published catalogue of Talmudic stories, aggadic or halakhic, that you would trust as a
cross-check?* Add it to `comms/JEFF.md` as `jeff:more-lists`. **If a list comes back, it replaces D–F for its
tractate**, and its stratum gets a BLIND number.

**Step 2. Calibrate the screens where the answer is known (~$8).** Run D on the skipped pages and E on the examined
pages of **Eruvin and Yevamot**, and score both against Jeff's lists. **Freeze E's prompt on Yevamot, then test it
once on Eruvin**, so Eruvin stays held out (Lesson 2: none of the known misses go into the prompt). Go / no-go,
written down before the run:
- D must re-find Eruvin 14b and 32b, the two stories triage lost there.
- E must flag at least half of the known Detection misses on Eruvin and Yevamot (about 10 between them) without
  flagging so much that Jeff's confirmation step goes past ~2 hours on the sample.
- If E fails, report Detection loss as unmeasured and do not spend the sample run on it.

**Step 3. Run the screens on six tractates (~$23).** Two per stratum, picked to be **unlike the five lists**:

| stratum | tractates | skipped | examined | why these |
|---|---|---|---|---|
| aggadic | **Sanhedrin**, **Sotah** | 150 | 170 | most stories in the stratum; Sotah is also red on G4 (two-run agreement) |
| Kodashim + Niddah | **Chullin**, **Zevachim** | 345 | 174 | Chullin is the stratum's densest; Zevachim skips 80% of its pages |
| halakhic (no Nashim) | **Bava Batra**, **Shevuot** | 274 | 172 | Nezikin, which no list covers; Shevuot skips 80% |
| | | **769** | **516** | |

D runs once on the skipped pages, and E once on the examined pages. Both judges see every new proposal before
anything goes on Jeff's page. The judges narrow, and never promote (L-045).

**Step 4. Confirmation (Jeff or a colleague, ~1–2 h).** Use one review page built by the existing axis review UI,
with stories highlighted in the full Hebrew and English (Critical Rule 1). Send it **after** the precision sample
comes back, not alongside it, so he is never holding two asks at once.

**Step 5. Report.** Per stratum: confirmed triage losses and confirmed Detection losses (measured lower bounds), and
the total divided by calibrated sensitivity, with an interval (indicated). Then one line on whether the stratum looks
like the five list tractates. That last line is the answer to Simon's question. Write it as a finding. **It does not
change the pipeline.**

### Why not all of Shas

D on every skipped page (~$42) and E on every examined page (~$37) is affordable. But running D on every skipped page
**is a triage loosening, without the review cost priced**, and the capability doc says not to do that
([`1_triage.md`](../capabilities/1_triage.md), "What we reverted"). It would also send Jeff ~5× the confirmation
work. If the six-tractate sample shows a stratum losing materially more than the five list tractates, that result
makes the case for a Shas-wide run of that stratum, priced by then in reviewer minutes as well as dollars.

## 5. Published indexes — candidates, none checked yet

*No web lookups were made while planning. Each entry is **suspected** usable until someone checks access, licence and
format.* Pre-2026 print cannot contain our output, so Lesson 29 cannot bite through the text. Run
`check_appendix_coverage.py` anyway on any digital edition annotated after 2026. **Before using any of them on the 32
tractates, measure its own coverage of Jeff's five lists** (free). That says what its silence means.

| work | covers | halakhic stories? | licence (to verify) | note |
|---|---|---|---|---|
| Ein Yaakov (16th c.) | aggadic passages of the Bavli, on Sefaria with links | **no** | Hebrew text public domain; check the Sefaria version licence | **declined by Jeff as a probe**; at most his "cheap optional aggadic cross-check" |
| Bialik & Ravnitzky, *Sefer HaAggadah* (1908–11) | an aggadic anthology with sources | no | Hebrew likely public domain (authors died 1934 and 1944); Braude's English (1992) is in copyright | selective; much of it is biblical legend, out of scope under R-S1 |
| Dov Noy (Neuman), *Motif-Index of Talmudic-Midrashic Literature* (dissertation, 1954) | motifs, with source references | partly | unknown; probably microfilm only | a motif is not a story, so alignment needs judgment |
| Hyman, *Toldot Tannaim ve-Amoraim* (1910) | every sage, with citations | **yes, incidentally**: it catches a ma'aseh about a sage | public domain | a biography index, not a story list; useful mainly to flag skipped pages that name a sage acting |
| Jeff's own field | — | — | — | **cheapest route to the right one: ask him (folded into Ask A)** |

None of these is in the recommendation. Only a catalogue Jeff vouches for, or one whose calibration on his five lists
holds up, earns a run.

## 6. Decisions Simon must make

1. **Send Ask A in the precision-sample email?** *Recommended: yes.* It is one paragraph, and the only route to a
   BLIND number. Simon decides on sending that email in any case.
2. **Is a screened, indicated estimate the solve, or only a stopgap until lists appear?** *Recommended: run Steps
   0–3 now*, because they cost ~$35 and no expert time, and the answer to A takes weeks. Step 4 is the one that waits.
3. **Six tractates (~$35) or all of Shas (~$80 + calibration)?** *Recommended: six.* All of Shas is a triage
   decision and should be taken as one.
4. **Jeff's time for Step 4 (~1–2 h), or one of his colleagues** (his July offer)? A colleague per stratum also
   avoids his queue.
5. **The gate itself** — what miss rate makes "the stories in tractate X" false — is `jeff:miss-rate`, already queued
   for Jeff in `comms/JEFF.md`. Without it, Step 5 can report a number but cannot call it pass or fail.

*Not offered, by the brief's constraint:* using Claude Code subagents as the auditor in E. A different model family
would be a more independent second reader than Gemini. If Simon lifts "Gemini-only", it is the obvious swap for E,
calibrated the same way.

## 7. Cost and time

| step | Gemini (billed, est.) | Jeff | our work | wall time | blocked by |
|---|---|---|---|---|---|
| 0. generalise D, write E and the estimator, with tests | $0 | — | ~½–1 day | — | — |
| 1. Ask A | $0 | ~5 min | 15 min | his reply: days to weeks | Simon sends the email |
| 2. calibrate D and E on Eruvin + Yevamot | ~$8 | — | ~2 h to score | ~1–2 h of calls | step 0 |
| 3. D + E on six tractates, plus judges | ~$25 | — | ~2 h | ~3–4 h of calls | step 2 passes |
| 4. confirmation page | $0 | **~1–2 h** | ~3 h to build and check in a browser | his reply | step 3; after the precision sample returns |
| 5. finding | $0 | — | ~½ day | — | step 4 |
| **total** | **~$35** (range $25–45) | **~1–2 h + 5 min** | **~2½ days** | **2–4 weeks, set by Jeff** | |
| *option: D + E on all of Shas* | *~$80 more* | *~5–10 h* | | | *decision 3* |

Costs are per-amud rates from the 2026-11-10 Shas run: $51.18 metered for two detector runs over ~1,850 examined
amudim, about $0.014 a call, ×1.22 for the gap between meter and bill
([lesson](../../lessons/_quote-the-bill-not-the-meter.md)). E's prompt carries our proposals as well, so it is costed
~20% higher. Each run does a `--dry-run` first, which prints its exact call count.

## 8. What done looks like, and what this plan does not license

**Done** (written before measuring, as the accuracy finding did): for each of the three strata, a confirmed count of
triage losses and Detection losses on its two sample tractates, a sensitivity-corrected estimate with an interval,
and a statement of whether it falls within the range measured on the five list tractates. Any tractate for which Jeff
supplies a list gets a BLIND measurement through the existing harness instead.

**Not licensed:**
- No change to triage, the detector or the site follows from this plan. A large loss in one stratum is evidence for a
  separate, priced decision.
- **Never quote the estimate as recall** without its label. It is *indicated*, built on a CIRCULAR screen, and the
  only BLIND figures remain those from expert lists.
- Confirmed finds go into the catalogue under the normal review rules. They do not go into any recall denominator:
  they were found by our own system (the Lesson 29 shape).
