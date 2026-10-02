# Draft copy: `/talmud-stories` on the hub

For Simon's review before building. Every figure is as of 2026-10-02, with its source in
a `<!-- -->` note that is **not** shown on the page. Sentences marked **[Jeff]** quote or
describe Prof. Rubenstein and go to him before deploy.

---

## Homepage card

**Talmud Stories**
An AI that finds the stories hidden inside the Talmud's legal debates. It finds about
9 in 10 of the stories a leading scholar listed by hand.
*Tags: AI, Talmud, Academic Research*

---

## Page

<sub>eyebrow</sub> **IN PROGRESS · AI + TALMUD SCHOLARSHIP**

# Finding the stories in the Talmud

The Babylonian Talmud is mostly legal argument, but stories are scattered through it:
rabbis travelling, quarrelling, getting things wrong, being kind. No index tells you
where they are. This project teaches an AI to find them, and checks its work against a
scholar who has spent his career on exactly these stories.

---

### 1 · What this is

<sub>eyebrow</sub> THE PROBLEM

A story in the Talmud doesn't announce itself. It can be two sentences long or run
across several pages. It often starts in the middle of a legal point. The same Hebrew
words turn up in a ruling and in a story. Scholars learn to spot them over years of
reading.

The goal is a complete catalogue of every story in every tractate, free for anyone to
read in Hebrew and English side by side. So far the tool has read **four tractates,
804 pages**: Ketubot, Kiddushin, Gittin and Yevamot.
<!-- page counts: results/sefaria/*.json and the v11 runs; 222+162+178+242 -->

---

### 2 · How it works

<sub>eyebrow</sub> FIVE STEPS

1. **Skim for events.** Every sentence on every page is labelled: is something
   *happening* here, or is it argument? Pages with no events at all are set aside, which
   saves most of the work.
2. **Ask which passages are stories.** The AI reads each remaining page and marks the
   passages that are stories. It works from a written rulebook built from the expert's
   own rulings.
3. **Look again, right next door.** The Talmud often tells the same kind of story two or
   three times in a row with different people. The AI tended to find one and stop. So a
   second pass looks at the passage beside every story it found and asks: *is there
   another one here?*
4. **Set the edges.** Each story gets a clear start and end, so it doesn't swallow the
   legal discussion around it.
5. **Join what the page split.** Page breaks in the Talmud are arbitrary. Stories that
   run across one are joined back together.

> **An example of step 3.** In Ketubot, the Talmud describes the people of Upper Galilee
> buying a poor man meat. Right beside it is a more famous story: Hillel buying a poor man
> who had come down in the world a horse, and a servant to run before him. The AI found
> the first and missed the second. The second look now catches pairs like this.
<!-- docs/findings/2026-09-07-miss-anatomy.md, Ketubot 67b -->

---

### 3 · How well it works

<sub>eyebrow</sub> THE NUMBERS, AS OF OCTOBER 2026

| | | |
|---|---|---|
| **About 9 in 10** | **More than 9 in 10** | **About 4 in 5** |
| of the stories on the expert's own lists are found | of the passages it calls a story really are one | of its story start and end points land exactly where the expert put them |

**The second look is working.** On Yevamot, adding step 3 raised the share found from
**89% to about 93%**.

<details> **How we measured** (small print)

The expert, Prof. Jeffrey Rubenstein, wrote lists of the stories in these tractates in
2005, twenty years before this tool existed. So the first number can't be flattered by
anything we did: it is the share of his 452 listed stories that the tool finds, across
four tractates (from 83% on Kiddushin to 97% on Gittin). The second comes from his reviews
of passages the tool proposed. The third compares start and end points with those same
2005 lists. These are not yet as good as we want, and the tool isn't perfectly
repeatable: two identical runs can differ by a story or two in a hundred. So we compare
runs in pairs before believing a change.
</details>
<!-- 1st: STATE.md end-to-end strict 87.2/83.3/97.3/89.2 on 149/90/111/102 → 404/452 = 89%
     2nd: docs/findings/2026-09-29-verdicts-read-against-the-call-shown.md, ~0.92–0.95
     3rd: STATUS.md Boundaries hit 80/85/85
     twin: docs/findings/2026-09-27-detector-is-not-deterministic.md, three runs 92.2–94.1 -->

---

### 4 · How an expert keeps it honest

<sub>eyebrow</sub> HUMAN IN THE LOOP

**[Jeff]** Prof. Jeffrey Rubenstein of New York University, one of the world's leading
scholars of Talmudic stories, reviews what the tool finds. He reads each passage in
Hebrew and English and answers a few short questions. *Is this a story? Does it start and
end in the right place? Is it one story or two?*

**His rulings become a written rulebook, in his own words.** When he decides a hard case,
for instance that a bare report of something isn't a story but *"a man stole another
man's cow and sold it. Rava ruled…"* may be, the decision is written down and the AI
works from it from then on.

**Next: two AIs, one expert.** He can't read every passage in the Talmud. The plan is to
have two different AI models judge every passage against his rulebook, so he only needs
to see the passages they disagree on, plus a random sample to keep them honest. The first
test was a no-go. The models disagreed with him in a pattern that pointed to a rule
missing from our rulebook. It's added now, and the test runs again next.
<!-- docs/findings/2026-09-28-consensus-phase1.md; docs/STORY_RULES.md R-C0 -->

> **[Jeff]** "The AI was confusing attribution with characters. When it sees 'Rabbi X said
> that Rabbi Y said…', it thought there was a story with characters, but it's just legal
> attribution."
> — from his first review. That one insight removed 53 false alarms.
<!-- already public on the old site, incl. the 53 -->

---

### 5 · What we got wrong along the way

<sub>eyebrow</sub> LESSONS

**At first, half its picks were wrong.** The first version, in January 2026, flagged
legal citations ("Rabbi X says in the name of Rabbi Y") as stories. The expert's first
review showed us why. Each review since has made it better.

**We were measuring the wrong thing.** For months the headline number was *"the expert
agreed 96% of the time."* That only tells you how good the tool's picks are, not how many
stories it **missed**. The expert's 2005 lists, written long before the tool, let us
measure the misses. It's a humbler number, and the honest one.

**Our test was too generous.** The way we matched the tool's stories to the expert's
gave credit for a nearby passage, not the right one. When we tightened it, two scores
fell by about 7 points. The tool hadn't changed; the scores were just finally accurate.

**We took back our own best result.** We once credited the skimming step with the
biggest improvement in the whole project. Re-checking it, we found the experiment had
been set up wrong. We withdrew the claim.

**The same run twice doesn't give the same answer.** Two identical runs on Yevamot
disagreed on 3 of 102 stories. A one-story change between two runs means nothing, so now
we always compare in pairs.
<!-- lessons/ L-35..L-43; docs/findings/2026-09-01-contaminated-no-triage-ablation.md;
     2026-09-03-exact-matcher-cutover.md; 2026-09-27-detector-is-not-deterministic.md -->

---

### 6 · The team

<sub>eyebrow</sub> WHO'S BEHIND IT

**Jeffrey L. Rubenstein, Ph.D.**: scholarship and validation.
Skirball Professor of Talmud and Rabbinic Literature, New York University.
*Talmudic Stories: Narrative Art, Composition, and Culture* (1999) · *The Culture of the
Babylonian Talmud* (2003) · *Rabbinic Stories* (2002) · *Stories of the Babylonian Talmud* (2010)

**Simon B.**: technical development.
Not a software engineer, but plays one on TV, with Claude Code as co-star.

**Built with** [Sefaria](https://www.sefaria.org) (the free library of Jewish texts:
Hebrew and English, aligned sentence by sentence) · Google Gemini (the AI that reads the
pages) · Anthropic Claude (the second AI judge, and the development assistant)

[View the code on GitHub →](https://github.com/siguy/talmud-stories)

---

## Notes for Simon

- **Dates fixed:** the old site's history says "January 2025". The first commit is
  2026-01-05, so the copy says January 2026.
- **"About 9 in 10"** is pooled across four tractates (404/452 = 89%). It hides a spread
  of 83–97%, which the small print states.
- **Dropped from the old site:** the "6 story criteria" (replaced by the rulebook), the
  YES/HIGH/LOW confidence labels, and links to old review pages. Readers don't need them.
- **No screenshot change** unless you want one.
