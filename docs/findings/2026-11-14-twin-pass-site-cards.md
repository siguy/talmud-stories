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
- **pesachim-49a-15-15, ketubot-86a-4-4, rosh_hashanah-18a-7-7 / yevamot-105a-13-13** wait for Simon's call.
- **ketubot-106a-2-3 holds two stories.** Likely cause: Jeff's 2026-05-25 boundary note was read 0-based where he
  meant 1-based (or the reverse), and `scripts/apply_jeff_2026-06-03_corrections.py` applied it. **Likely, not
  proven.** The other notes that script applied may have the same off-by-one; check them before trusting their
  boundaries.
