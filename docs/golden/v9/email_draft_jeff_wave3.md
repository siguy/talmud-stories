# Email Draft: Jeff — Wave 3 results, two small review buckets

**To:** Jeff Rubenstein
**Subject:** Talmud story detector — Wave 3: caught your 33a bathhouse + 7 more (Kiddushin) + recall lift on Ketubot

---

Hi Jeff,

Quick update — I just shipped Wave 3 of the story detector. Two
things to flag, one bigger thing to ask of you.

**What changed since you last looked:**

1. Multi-story / embedded-story prompt — the detector now actively
   looks for second-and-third stories on the same page, and for stories
   embedded inside a `תניא` or `תא שמע` frame.
2. Text-internal boundary trimming — for cases where you asked the
   story to start at a `מעשה ב`/`כי הא ד` introducer that sits *inside*
   the same segment as the surrounding halakhic framing, the UI now
   greys out the framing and highlights the slice that should count
   as story. Ten of your seventeen boundary requests now show that way
   automatically; the other seven need text patterns we haven't covered
   yet.
3. (Internal: I forked the detector to a new file — v7→v8→v9 — so the
   prior Wave 2 baseline stays frozen for comparison.)

**Headline result on Ketubot:** the detector now catches seven stories
it had been missing. Recall jumped from 89.2% → 93.7%, classification
F1 from 0.895 → 0.911. No new review work — those seven are already in
the golden, the detector just finally found them.

**The thing I want you to look at — seven new Kiddushin candidates the
detector now finds that v8 didn't.** The biggest one:

- **33a seg 5** — Rabbi Hiyya sits in the bathhouse, Rabbi Shimon bar
  Rabbi passes and doesn't stand. This is **the exact story you said
  was missed** in the April 23 review. The detector now picks it up.

The other six:

- **12b seg 8** — Rav Sheshet flogs a man who merely passed his
  mother-in-law's door (rumor-based)
- **20a segs 12-14** — Abaye boasts in the market that he's
  comparable to Ben Azzai
- **39a seg 1** — Levi asks Shmuel for uncertain-orla produce while
  other rabbis are present
- **51a seg 11** — A man uses a basket of Sabbatical figs to try to
  betroth five women
- **52a seg 4** — Parallel betrothal narrative (likely the same
  incident retold)
- **69b segs 8-9** — Ezra addresses returning priests whose
  genealogical records were lost

I'd love YES / HIGH / LOW / NOT_A_STORY on each. If you confirm even
half of these are real stories, the agreement-score "regression" you'll
see in the numbers (-0.01 composite vs. v8) flips into a meaningful
improvement on the next iteration — the golden was built from v8's
output, so any new story v9 finds counts as a false positive against it
until you weigh in.

**And four new Ketubot candidates** — same dynamic, smaller number:

- **Ketubot 7a seg 1** — Rav Ami permits a groom to consummate on
  Shabbat; the Sages object (https://www.sefaria.org/Ketubot.7a)
- **Ketubot 26a seg 9** — Hypothetical legal case re: priestly status
  from rumor (likely NOT a story by your rules?)
  (https://www.sefaria.org/Ketubot.26a)
- **Ketubot 102a seg 6** — A guarantor-liability case before Rabbi
  Yishmael, leading to a disagreement with Ben Nannas
  (https://www.sefaria.org/Ketubot.102a)
- **Ketubot 106a segs 1-2** — Elijah stops visiting Rav Anan after a
  legal error; Rav Anan fasts until he returns
  (https://www.sefaria.org/Ketubot.106a)

**Review UI (Kiddushin):** the standard HTML browser app, now also
showing the trimmed-text slices for the boundary cases. I'll attach /
share separately.

**Time estimate:** the seven Kiddushin candidates are the priority and
should take ~10 minutes. The four Ketubot are ~5 minutes. The ten
boundary-slice confirmations are quick (eyeball whether the
green-highlighted Hebrew matches what you meant) — ~10 minutes if you
want to do them, optional.

I'll plan the next wave around whatever you find — particularly
whether the seven Kiddushin candidates are real (which would tell me
the prompt change is working) or false positives (which would tell me
to bisect).

Thanks,
Simon
