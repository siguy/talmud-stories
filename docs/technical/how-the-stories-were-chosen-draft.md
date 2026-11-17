# "How the stories were chosen": draft wording for Simon to approve

Drafted 2026-11-17. **Not on the site.** Facts come from the project's own records (`docs/STORY_RULES.md`,
`docs/technical/septimus-story-filter.md`, `docs/findings/2026-11-16-full-boundary-review.md`, `STATUS.md`) and, for
Prof. Rubenstein, from public sources listed at the end. Numbers marked {like this} are read from the story data when
the page is drawn, never typed in. Open points for Simon are at the bottom.

---

## How the stories were chosen

### What this is

The Babylonian Talmud is mostly legal argument, but stories are scattered through it: rabbis travelling,
quarrelling, getting things wrong, being kind. No index says where they are. This site gathers them:
{1,786} stories from all {37} tractates, in Hebrew and English.

### What counts as a story

We follow rules set by Prof. Jeffrey Rubenstein, a scholar of these stories (more about him below). In short:

- **Something happened.** A story tells of an event, even a legendary one. "If a man steals a cow…" is a legal
  case. "A certain man stole a cow…" may be a story.
- **There is action, and something changes.** Talk alone is not a story, however sharp the exchange. In his words,
  a story needs "at least two actions and change".
- **A bare report is not enough.** "Rabbi Akiva once did such-and-such" tells us what he did. A story goes somewhere.
- **It is about the sages and their world.** Retellings of events from the Bible are left out. They are stories,
  but of a different kind.
- **It is told in the Talmud's own discussion.** A story that appears only in the Mishnah printed on the page is
  left out, unless the Talmud itself retells it.
- **Only clear cases.** Where a scholar could reasonably say "maybe", the passage is left off this site.

A story begins with the line that introduces it ("Rabbi X said in the name of Rabbi Y…") and ends where the telling
ends. The legal discussion that follows is left out where we could separate it.

### How they were found

1. The text and translation come from Sefaria (William Davidson Edition).
2. Software, an AI language model, read every page and marked the passages that look like stories. It worked from a
   written rulebook built from Prof. Rubenstein's rulings.
3. It then looked beside every story it found, because the Talmud often tells two or three similar stories in a row.
4. Each tractate was read twice, independently. Only passages marked as clear stories both times are shown.
5. A second AI model checked for passages outside the rules above.
6. Every story was then re-read for where it starts and ends. 110 were trimmed, extended or joined to a neighbour.

The "Background" note under a story was drafted with AI from the passage itself and passed automatic checks before
being shown. It can still be wrong.

### What a scholar has checked

In Ketubot, Kiddushin and Gittin, Prof. Rubenstein went through what the software found, passage by passage: Is
this a story? Does it start and end in the right place? Is it one story or two? In those three tractates only
passages he accepted are shown, and his answers became the rulebook the software works from.

The other {34} tractates are marked "not yet reviewed". No scholar has gone through them.

### How good is it

- **Stories are missing.** Because only clear cases are shown, real stories have been left out, probably several
  hundred across the Talmud.
- **A few things here are not stories,** or start or end in the wrong place. When we checked a sample of 60, 54
  were clearly stories.

If you spot a mistake, use "Report a problem" under any story. Reports are read.

### Prof. Jeffrey Rubenstein

Jeffrey L. Rubenstein is the Skirball Professor of Talmud and Rabbinic Literature at New York University, where he
has taught since 1993. His research is on the stories of the Babylonian Talmud. His books include *Talmudic
Stories: Narrative Art, Composition, and Culture*, *Rabbinic Stories*, *The Culture of the Babylonian Talmud*,
*Stories of the Babylonian Talmud* and *The Land of Truth: Talmud Tales, Timeless Teachings*.

He advises this project. He has not reviewed every story on the site.

### Who made this

Simon Brief built this site. I am not a Talmud scholar or a professional programmer. I set out to find every story
in the Talmud and make them easy to read, with a scholar keeping the work honest. More about the project:
simonbrief.com/talmud-stories.

Text and translation: Sefaria. The AI that reads the pages: Google Gemini. The second AI, which also helped build
the site: Anthropic Claude.

---

## For Simon to settle before this goes on the site

1. **Show Prof. Rubenstein the two sections that name him** ("What a scholar has checked" and the paragraph about
   him) before publishing. They describe his role and use his name; he should agree to the wording.
2. **"Who made this" is a guess at your voice.** Rewrite it as you like. I left out your background and Daniel
   Septimus's name; say if you want either in.
3. **The two accuracy statements.** "Probably several hundred missing" rests on an estimate the records call
   *indicated*, a lower bound of about 700 (range 520 to 940). "54 of 60" is a sample where you graded 53 and
   Prof. Rubenstein 7; the records say site precision is "not measured". Keep them, soften them, or cut the section.
4. **"In those three tractates only passages he accepted are shown"** is the site's rule
   (`septimus-story-filter.md`), with one nuance: a story on his own 2005 list also counts. His later review rounds
   were samples, not every passage. If that is too strong, say "passages he accepted, or that are on his own lists".
5. **A National Jewish Book Award** for *Talmudic Stories* appears in one search summary. I left it out because I
   could not confirm it on the publisher's or the Jewish Book Council's page.

## Sources for the paragraph about Prof. Rubenstein

- Jewish Book Council author page: https://jewishbookcouncil.org/jeffrey-l-rubenstein
- Johns Hopkins University Press author page: https://www.press.jhu.edu/books/authors/jeffrey-l-rubenstein
- *Talmudic Stories*, JHU Press: https://www.press.jhu.edu/books/title/2434/talmudic-stories
- *Stories of the Babylonian Talmud*, JHU Press: https://press.jhu.edu/books/title/10105/stories-babylonian-talmud
- Profile, Jewish Standard: https://jewishstandard.timesofisrael.com/learning-from-our-stories/
