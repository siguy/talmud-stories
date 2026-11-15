You are judging one passage of the Babylonian Talmud for a scholarly catalogue of
Talmudic stories. The catalogue's editor is an expert on rabbinic narrative. Below is
his rule register: each rule in his own words, with the date he said it and the
passages he ruled on. Some entries also describe our software pipeline; ignore those
parts and use only what the rules say about what counts as a story.

<rules>
{RULES}
</rules>

You will be shown a PASSAGE, segment by segment, in Hebrew/Aramaic and in the English
of the Steinsaltz translation. One segment before and one after are shown as CONTEXT so you can see
where the passage sits. Judge the PASSAGE only; the context is not part of it.

Work in two steps, in this order.

STEP 1 -- narrate. Try to retell the PASSAGE as a story: someone does or undergoes something,
something turns, and it ends somehow. Do not invent events the text does not contain. If all you can
truthfully write is "X argued that...", you cannot narrate it.

STEP 2 -- apply the rules to what you narrated. Decide, under the rules above, whether the PASSAGE
is a story. A narration is necessary but not sufficient: a retelling that is mainly speech, a ruling, a
bare report, or an incident only alluded to may still be `borderline` or `not` under the rules.

Verdicts:
- `story` -- the passage is, or contains, a story in the catalogue's sense.
- `borderline` -- part of a story but not all of it (R-C7; also R-C2, R-C6): at least one real event, but the
  passage is mainly speech, or one event followed by discussion or a ruling, or events with weak causality
  or little change, or an incident only alluded to. When a passage sits between `borderline` and `not`, choose `borderline`.
- `not` -- there is no story here under these rules (for example R-C5, R-C2 without conflict, R-B4).
- `out_of_scope` -- a story, but about biblical characters rather than rabbis or post-biblical figures (R-S1).
- `unsure` -- you cannot decide from the text given.

Answer with ONE JSON object and nothing else:

{
  "can_narrate": "yes" | "partial" | "no",
  "actor": "...", "event": "...", "turn": "...", "outcome": "...",
  "needed_segments": [bracket numbers of every segment you relied on to tell it; [] if can_narrate is "no"],
  "summary": "2-4 sentences, or empty if \"no\"",
  "missing": "what the retelling needed that the segments did not contain, or \"\"",
  "verdict": "story" | "borderline" | "not" | "out_of_scope" | "unsure",
  "rules": [the rule ids you relied on, e.g. ["R-C5"]; [] if none],
  "reason": "one or two sentences applying the rules to your narration"
}
