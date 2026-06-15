# Email Draft — Reply to Jeff (2026-06-03)

**To:** Jeff Rubenstein <jr6@nyu.edu>
**Subject:** Re: Wave 3 — applied your Ketubot fixes; one favor on the Kiddushin set

---

Hi Jeff,

Thank you — your boundary-fix diagnosis is exactly right. Wave 3's
text-trim used hand-built regex rules (the word **אלא**, a rabbi's
name, the **תניא** marker, etc.) to guess where the framing ends and
the story begins. As you saw, that works fine when those markers
really are stam framing, and it cuts story content when they're not.
The regex can't tell the difference; only meaning can. That confirms
this whole post-processor needs to be replaced with the LLM emitting
the slice directly, which we'll build in the next iteration (Wave 4).

For now, **two quick updates** and **two asks**.

**1. I applied your four Ketubot corrections to the golden dataset
just now:**

- **7a seg 1** → reclassified NOT_A_STORY → **LOW_CONFIDENCE** (the
  detector already had it as LOW, so this also recovers one
  false-positive against the golden).
- **26a seg 9** → confirmed NOT_A_STORY (no change; we already had it
  that way).
- **102a seg 6** → confirmed not a story (no change; not in golden).
- **106a** → I extended the existing 3-3 story back one segment to
  **2-3** per your "the story is segments 2-3, not really 1." The
  detector had flagged 1-2 separately; your boundary supersedes that.

Net: classification F1 ticked up from **0.910 → 0.914**, composite
**0.9170 → 0.9171** (essentially flat — the 7a recovery + the 106a
boundary cancel out). Detailed writeup:
`docs/golden/v9/wave3_round2_ketubot_rescore.md`.

**2. Wave 4 plan (for your awareness):** I'm going to retire the regex
boundary trimmer and replace it with the LLM emitting the
`text_span_start` / `text_span_end` directly during detection — same
slice idea, but the model itself decides what's framing and what's
story. The seven cases you flagged as over-trimmed (8b 2, 9a 1, 9a 2,
13a 3, 31b 4, 33a 15, and 8a 9-10 / 12b 4 as under-trims) become my
held-out test set — the new system has to recover those before I ship.

**The two asks, in order of importance:**

**(a) Could you finish verdicting the Kiddushin set when you have
time?** You marked ~10 of the 95 stories with notes; the
classification verdicts (YES / HIGH / LOW / NOT_A_STORY) for the
remaining ~85 are what move the composite score. Same UI as before:
**https://siguy.github.io/talmud-stories/validation/ui/kiddushin_review_wave3.html**

**(b) Most critically, please verdict the seven NEW Kiddushin
candidates** the detector picked up that v8 had missed. They're the
ones with the green "NEW IN WAVE 3" tag in the UI:

- **33a seg 5** (Rabbi Hiyya in bathhouse — the one you flagged as
  missed in April)
- **12b seg 8** (Rav Sheshet flogs man who passed mother-in-law's door)
- **20a segs 12-14** (Abaye boasts in market)
- **39a seg 1** (Levi asks Shmuel for orla produce)
- **51a seg 11** (Sabbatical figs / five women)
- **52a seg 4** (parallel)
- **69b segs 8-9** (Ezra and returning priests)

If even half of these are real, the Kiddushin composite "regression"
flips into a meaningful improvement.

Yes — please complete all the boundary annotations when you can. They
become the labeled test set for Wave 4. Thank you for being so
specific about *why* the regex went wrong; that's exactly the kind of
diagnostic that lets me actually fix it instead of just tuning around
it.

Thanks again,
Simon

---

## Sending checklist (for Simon)

- [ ] Read draft top-to-bottom
- [ ] Optional: trim Wave 4 internals if too technical
- [ ] Send via `gws gmail` or copy-paste into Gmail
- [ ] Log send date in `tasks/todo.md`
