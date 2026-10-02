# The public site moved to the hub, and its old numbers were withdrawn

**Date:** 2026-10-02 · **Capability:** [6 Publication](../capabilities/6_publication.md) ·
**Item:** [`public-site-refresh`](../../work/done/2026-10-02-public-site-refresh.md)

## What happened

The project's public face was a four-page GitHub Pages site (`index.html`, `approach.html`,
`history.html`, `validation.html`), linked from a card on the Simon Brief hub. Both still
described **February 2026**: one tractate, v7/v8, and a single "accuracy" figure (92.1% on
the card, 96.3% on the site).

**The site had not deployed since 2026-05-25** (*measured*: `gh api
repos/siguy/talmud-stories/pages/builds`). Every build after that errored. So the
2026-08-31 hand-correction recorded in the Publication history as "FIXED" was committed but
**never reached a reader**. The likely cause is Liquid syntax (`{{` / `{%`) in markdown
added on 2026-08-30, which the legacy Jekyll build cannot parse (*indicated*: not
verified, and moot now).

**Decision (Simon):** retire GitHub Pages and put the project on the hub as one
plain-language page. It is now live at **https://simonbrief.com/talmud-stories** (hub repo
`simonbrief-hub`, `app/talmud-stories/`, deployed at `a427d40`). GitHub Pages is
disabled. The three sub-pages were removed from this repo, and `index.html` is now a
pointer to the new page.

## Numbers withdrawn, and why

| withdrawn | what it actually was | why it can't be the headline |
|---|---|---|
| **92.1% accuracy** (card) | expert agreement on 127 passages the v7 detector proposed, Feb 2026 | Measures how often our picks are right. It says nothing about what we missed, and it was computed on the same pages we tuned on |
| **96.3% accuracy** (site) | the same kind of agreement, v8, Ketubot 61–112, Feb 2026 | Same problem. It was also four detector versions stale |
| **96% recall** (unpublished 2026-08-31 edit) | recall vs Jeff's 2005 list under the 4-gram window | That matcher was retired on 2026-09-03 because it credited nearby passages ([`exact-matcher-cutover`](2026-09-03-exact-matcher-cutover.md)) |
| **"153 / 172 stories"** | detector-run counts on Ketubot | A count of what we proposed, not of what is there |

The old figures survive on the new page only as history ("For months the headline number
was 'the expert agreed 96% of the time'…"), with the number struck through.

## What the page says now

All figures as of October 2026, typed by hand and dated (Simon's decision, not generated):

| on the page | the measurement behind it | source |
|---|---|---|
| **about 9 in 10** stories found | end-to-end strict recall vs Jeff's 2005 lists, BLIND, pooled: 404 / 452 (89%) across Ketubot 87.2 · Kiddushin 83.3 · Gittin 97.3 · Yevamot 89.2 | `STATE.md` end-to-end block |
| **more than 9 in 10** calls of "story" right | classification precision ~0.92–0.95, verdicts read against the call shown | [`verdicts-read-against-the-call-shown`](2026-09-29-verdicts-read-against-the-call-shown.md) |
| **about 4 in 5** start and end points exact | boundary HIT rate vs the 2005 lists, BLIND: 80 / 85 / 85% | `STATUS.md` scoreboard |
| Yevamot **89% → about 93%** with the second look | twin pass, three runs 92.2–94.1 | [`detector-is-not-deterministic`](2026-09-27-detector-is-not-deterministic.md) |
| 804 pages, four tractates | 222 + 162 + 178 + 242 amudim | the v11 run files |

The spread behind "9 in 10" (83–97%) and the run-to-run noise are both stated in the
page's "How we measured" note. The page is written for general readers, so the
BLIND/CIRCULAR vocabulary stays here, not there.

## What broke, on purpose

Old review links in emails already sent to Jeff (the last one was 2026-06-03;
`comms/sent/` keeps them) no longer resolve. Every round since 2026-06-15 has been sent as
attached files, and Jeff's later rounds came back that way, so no open review depended on
a Pages URL. `comms/sent/` was left unedited because it records what was sent.
`docs/communication/*` now carries a note.

## What will go wrong next

The numbers are hand-typed, so **they will drift**. The page's `AS_OF` constant is the
only guard. Whoever moves a headline number in `STATE.md` or `STATUS.md` should update the
hub page in the same session, or at least change its date. Generating the figures was
considered and declined for now; it remains listed under *Untried* in the
[Publication history](../capabilities/6_publication.md).

**Not yet done:** Jeff has not seen the page. Its sentences about him are the quote he gave
in his first review, already public on the old site, plus his title and books.
