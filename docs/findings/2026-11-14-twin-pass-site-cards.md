# Twin-pass cards on the Septimus site (2026-11-14)

Simon, 2026-11-14, on the cards a rules triage marked SURE_REMOVE: *"just remove them if you are sure."*

**17 cards removed; the site went from 1,864 to 1,847 stories.** Every one was a twin-pass addition
(`source: twin_pass`, story_detector_v14 `_find_adjacent_twins`) in an unreviewed tractate. None had a Jeff
verdict; the call is a rules-based triage against [`STORY_RULES.md`](../STORY_RULES.md), so these are
**indicated** not-stories, not expert-measured ones. Recorded per card, with rule and reason, in
`results/shas_run/septimus_site_decisions.json` (`remove`), applied by `scripts/build_site_data.py`.

## What was measured

- **All 20 unreviewed cards flagged while writing summaries were twin-pass additions**, and in each the second
  run made the same twin addition. The site's both-runs rule did not filter them out. **Two runs agreeing is weak
  evidence for a twin-pass card**: both runs share the twin prompt, so they make the same mistake together.
- **79 twin-pass cards shipped in the 1,864-story build** (the triage brief said 78). Each is a single segment on
  its page (`start_segment == end_segment`). Three continue onto the next page (eruvin-53b-24-24,
  beitzah-22a-16-16, sanhedrin-29b-21-21). No card had a reader-facing summary from the detector: v14 fills a twin
  addition's summary with the twin judge's reasoning, so the site shows a hand-written summary or none.
- The triage looked at **about 76** twin-pass cards and judged **about 20** of them not stories. That is the
  triage's own count, not a re-measurement here. 17 are removed below; 3 wait for Simon.

| rule | cards |
|---|---|
| R-C0 (no event, or a hypothetical one) | taanit-28a-6-6, yoma-35b-5-5, sanhedrin-29b-21-21, taanit-23b-8-8 |
| R-C2 (teaching, debate, Q&A, rulings, sayings) | chullin-128a-9-9, shabbat-156a-4-4, avodah_zarah-69a-1-1, chullin-56a-10-10, yevamot-42b-8-8, megillah-28a-19-19, moed_katan-12b-13-13 |
| R-C2 / R-C3 / R-C5 (speech act, habit, description) | bava_metzia-73a-9-9, megillah-28a-7-7, sukkah-28a-3-3, sukkah-53a-2-2, pesachim-57a-7-7, berakhot-44a-4-4 |

Where the real story next to a removed card is its own card, it still ships unchanged: yoma-35b-6-7,
chullin-56a-11-11, moed_katan-12b-14-14, taanit-23b-9-9. taanit-23b-9-9 was **not widened** to take 8-8.

Per tractate: chullin, megillah, sukkah, taanit -2 each; avodah_zarah, bava_metzia, berakhot, moed_katan,
pesachim, sanhedrin, shabbat, yevamot, yoma -1 each. Every other story is byte-identical to the build before;
`out_of_scope` unchanged at 102, no overlap with `stories`.

## Open

- **62 twin-pass cards are still on the site** after this removal. About 56 have not been reviewed by anyone, and
  they carry the same risk: about one in four of those looked at was not a story (indicated).
- **pesachim-49a-15-15, ketubot-86a-4-4, rosh_hashanah-18a-7-7 / yevamot-105a-13-13** wait for Simon's call. *Decided the same day: keep (second pass, below).*
- **ketubot-106a-2-3 holds two stories.** *Fixed the same day (b43deb2: back to 3-3); its summary and note now match.* Likely cause: Jeff's 2026-05-25 boundary note was read 0-based where he
  meant 1-based (or the reverse), and `scripts/apply_jeff_2026-06-03_corrections.py` applied it. **Likely, not
  proven.** The other notes that script applied may have the same off-by-one; check them before trusting their
  boundaries.

## Second pass, later on 2026-11-14

Simon: *"just remove them if you are sure"*; on the four cards above, *"if they're stories, which they seem to be,
keep them."* A second rules-based triage (against `STORY_RULES.md`, no Jeff verdict on any card) read **60** of the
remaining twin-pass cards:

| verdict | cards | what happened |
|---|---|---|
| SURE_REMOVE | 32 | `remove`, rule and reason per card; ids `retired` |
| FIX_NOT_REMOVE | 5 | 1 removed as a duplicate, 1 extended, 3 merged (below) |
| KEEP | 12 | shipped unchanged |
| SHOW_SIMON | 11 | **held, untouched**, for Simon |

**The site went from 1,847 to 1,811** (−33 removed, −3 absorbed by merges); `out_of_scope` unchanged at 102. Every
other story is byte-identical to the build before, except the summaries changed on purpose (below).

- **Removed as a duplicate:** chagigah-13a-10-10, the Gemara's one-line allusion to the youth burned by the electrum;
  the full story ships as chagigah-13a-12-12.
- **Extended (display only):** rosh_hashanah-25a-11-11 to 25a:11-13 (`boundary_extensions.json`, `end_forward: 2`);
  25a:12-13 complete the Akiva-consoles-Yehoshua episode and are on no other card.
- **Merged** (new `merge` decision list, applied by `build_site_data.py`; the absorbed id redirects): megillah-29a-4-4
  into **megillah-29a-5-5** (29a:4-5), sanhedrin-11a-8-8 into **sanhedrin-11a-7-7** (11a:7-8), sanhedrin-104a-7-7 into
  **sanhedrin-104a-8-8** (104a:7-8). In each the flagged card is the one absorbed. Each merged card has a summary
  written for the whole story.
- **Kept by Simon:** pesachim-49a-15-15, ketubot-86a-4-4, rosh_hashanah-18a-7-7, yevamot-105a-13-13, recorded in a new
  `keep` list; a `remove` overlapping one is refused.
- **bava_batra-30b-5-5 lies inside bava_batra-30b-5-7**, another shipped card. Its removal is marked `exact: true`
  (remove only the card with exactly this span), so 30b-5-7 stays; the registry then records 30b-5-5 as a `redirect`
  to 30b-5-7, not `retired`, because its passage is still on the site inside that card.
- **Summaries fixed:** ketubot-106a-2-3 (span 3-3 since b43deb2) now describes only the Rav Yosef famine story, and so
  does its note (rewritten, `approved: false`); eruvin-53b-24-24 said the same thing twice (two runs' summaries
  concatenated by the cross-page merge), replaced through a new `overrides` key in `site_summaries_written.json`.

**Open.**
- **11 SHOW_SIMON cards** wait for Simon: avodah_zarah-65b-5-5, bava_batra-8a-16-16, bava_metzia-85b-4-4,
  bava_metzia-85b-7-7, berakhot-19a-9-9, makkot-16b-6-6, moed_katan-21a-6-6, moed_katan-25b-2-2, moed_katan-25b-9-9,
  taanit-21b-8-8, yoma-38b-2-2.
- **Shipped neighbours with the same shape as a removed card, not triaged:** bava_batra-30b-5-7 (contains the removed
  30b:5) and yevamot-15a-15-15. Two others named in the brief, sukkah-26a-7-7 and yoma-79a-2-2, are **not on the site**
  (no registry entry: they never shipped), and bava_batra-30b-6-7 does not exist; 30b-5-7 is the card at that spot.
