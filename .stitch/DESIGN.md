# Design system: Stories of the Talmud (Septimus reader)

Extracted from `site/style.css` and `site/index.html`. The sign-up screens must look like part of this reader, not a new product.

## 1. Visual theme and atmosphere

A quiet, bookish, mobile-first reading site in memory of Joe Septimus. Light, warm off-white paper surface; one deep navy bar at the top; a thin antique-gold accent used as a left edge on cards and as an underline on section headings. Calm and respectful, never promotional. Low density, generous line height, a single narrow reading column. No photography, no illustrations, no gradients, no drop shadows, no emoji, no floating pills or badge dots.

## 2. Color palette and roles

Primary foundation
- Paper (#fbfbfa): page background.
- Card White (#ffffff): cards, rows, form surfaces.
- Hairline (#e6e4df): 1px borders on cards, rows, inputs, dividers.
- Chip Stone (#f1efe9): notices, chips, empty progress track, pressed card.

Accent and interactive
- Septimus Navy (#18345d): top bar background, links, selected tab or segmented button, outline buttons.
- Antique Gold (#ccb479): 6px left edge on cards, 4px left edge on the dedication and notes, 2px underline on section headings. Decorative only, never a text color.
- Gold Ink (#7a6422): section heading text and Hebrew tractate names.

Typography hierarchy
- Ink (#222222): body and headings.
- Muted (#666666): meta lines, summaries, footers.

Functional status
- Learned Green (#2e7d4f): progress bar fill, the filled "done" check, the primary "Mark as learned" button.

A dark scheme exists (background #121316, card #1b1d22, ink #ececec, accent #9db7e3); design light first.

## 3. Typography rules

- Headings, card names, summaries, English story text: Cardo (serif), Georgia fallback. Page title 700 at 1.7rem, line height 1.2. Section heading 700 at 1.15rem in Gold Ink with gold underline. Card name 700 at 1.3rem. Dedication and story summary: Cardo italic 1.05rem.
- Hebrew and Aramaic: Frank Ruhl Libre, right-to-left, 1.45rem, line height 1.75, with vowels.
- UI text (buttons, meta, notices, forms): Helvetica Neue / Helvetica / Arial, 1rem, line height 1.5. Meta 0.9rem, chips 0.75rem, footer 0.8rem.
- No uppercase labels, no letter-spaced eyebrows.

## 4. Component stylings

- Top bar: sticky, Septimus Navy, white Cardo bold title "Stories of the Talmud" at left, one outlined "Aa" settings button at right (1px translucent white border, 6px radius).
- Card: Card White, 1px Hairline border, 6px Antique Gold left edge, 10px radius, padding 0.9rem 1rem, 0.7rem vertical gap. English name left in Cardo bold, Hebrew name right in Gold Ink, a muted meta line, then a 6px progress track (Chip Stone) with Learned Green fill and a muted "N of M read" line.
- Story row: Card White, 1px Hairline, 10px radius, a 1.4rem circular check at left (empty ring, or filled Learned Green with a white tick), bold reference ("Ketubot 8b") and a muted one-sentence summary.
- Buttons: 48px minimum height, 10px radius. Outline button: Card White with 1px Septimus Navy border and navy bold text. Primary action: solid Learned Green with white bold text. Buttons sit in a row and stretch to share width; full width on a phone.
- Tabs and choice pills: 999px radius, 1px Hairline border, 44px minimum height; selected is solid Septimus Navy with white text.
- Segmented control: joined buttons in a 1px Hairline frame, 8px radius; selected segment is solid navy.
- Dedication block: 4px Antique Gold left edge, Cardo italic, no background ("In memory of Joe Septimus.").
- Notice: Chip Stone background, 8px radius, small muted text.
- Inputs: full width, Paper background, 1px Hairline border, 8px radius, 44px minimum height.
- Footer: small muted text above a 1px Hairline top border, crediting Sefaria and Prof. Jeff Rubenstein.

## 5. Layout principles

- Mobile first, designed at 390px wide. One column, maximum width 42rem, centered, 1rem side padding.
- Spacing on a 4px / 8px rhythm; cards 0.7rem apart; sections separated by a gold-underlined heading with 1.5rem above.
- All touch targets at least 44px tall.
- Nothing overlaps content: no floating buttons, no modals, no carousels.

## 6. Stitch generation notes

Atmosphere keywords: quiet, bookish, memorial, scholarly, warm paper, restrained, mobile reading.

Canonical colors: Paper #fbfbfa, Card White #ffffff, Hairline #e6e4df, Chip Stone #f1efe9, Septimus Navy #18345d, Antique Gold #ccb479, Gold Ink #7a6422, Ink #222222, Muted #666666, Learned Green #2e7d4f.

Component prompts
- "A white card with a thin hairline border, a 6px antique-gold left edge and 10px corners, with a bold Cardo serif title, a muted one-line meta, and a thin green progress bar."
- "A story row: an empty circular check at left, a bold reference like 'Ketubot 8b', and a muted one-sentence summary beneath."
- "A full-width 48px button with 10px corners: solid green with white bold text for the main action, or white with a navy outline for secondary actions."
