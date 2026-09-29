You are judging one passage of the Babylonian Talmud for a scholarly catalogue of
Talmudic stories. The catalogue's editor is an expert on rabbinic narrative. Below is
his rule register: each rule in his own words, with the date he said it and the
passages he ruled on. Some entries also describe our software pipeline; ignore those
parts and use only what the rules say about what counts as a story.

<rules>
{RULES}
</rules>

You will be shown a PASSAGE, segment by segment, in Hebrew/Aramaic and in the English
of the Steinsaltz translation (translator's additions are in plain type, the literal
text in bold). One segment before and one after are shown as CONTEXT so you can see
where the passage sits. Judge the PASSAGE only; the context is not part of it.

Answer one question: **under these rules, is the PASSAGE a story?**

- `story` — the passage is, or contains, a story in the catalogue's sense.
- `borderline` — the expert's own category (R-C2).
- `not` — there is no story here under these rules (for example R-C5, R-C2 without
  conflict, R-B4).
- `out_of_scope` — a story, but about biblical characters rather than rabbis or
  post-biblical figures (R-S1).
- `unsure` — you cannot decide from the text given.

Return JSON with exactly these fields:
- `verdict`: one of `story`, `borderline`, `not`, `out_of_scope`, `unsure`
- `rules`: the rule ids you relied on (e.g. `["R-C5"]`); an empty list if none applies
- `segments`: the bracketed numbers `[n]` of the PASSAGE segments the story occupies. Required for `story`,
  `borderline` and `out_of_scope`; may be empty for `not` and `unsure`. Never a
  CONTEXT segment.
- `reason`: one or two sentences.
