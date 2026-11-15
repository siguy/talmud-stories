You are reading a passage of the Babylonian Talmud (Hebrew/Aramaic with an English translation) in order to retell it.

The text is shown as numbered segments `[1]`, `[2]`, ... Some are marked PASSAGE and some CONTEXT. The PASSAGE is the part someone proposed as a unit; CONTEXT segments are the text just before and after it. The proposed unit may be too short, too long, or not a narrative at all. You are the judge of that.

Your task is to try to narrate it as a story: someone does or undergoes something, something turns, and it ends somehow. Be honest about whether you can. Many Talmudic passages cannot be narrated: a legal argument, a rule with its reasoning, a hypothetical case, a description of a habit or custom, a bare citation of what a sage said. If all you can truthfully write is "X argued that..." with no event, answer `no`. Do not invent events the text does not contain.

Answer with ONE JSON object and nothing else:

{
  "can_narrate": "yes" | "partial" | "no",
  "actor": "who the story is about (empty if none)",
  "event": "what happened, in one sentence (empty if nothing happened)",
  "turn": "what changed or went wrong or was revealed (empty if none)",
  "outcome": "how it ended (empty if it does not end)",
  "needed_segments": [bracket numbers of every segment you actually relied on to tell it, CONTEXT segments included; [] if can_narrate is "no"],
  "summary": "2-4 sentences retelling it in plain English for a reader who has not seen the text (empty if "no")",
  "missing": "what your retelling needed that the segments shown did not contain, or \"\" if nothing"
}

- `yes`: you can retell a complete narrative (event, turn, outcome) from the text shown.
- `partial`: there is a narrative, but part of it (its start, or its ending) is not within the text shown, or the passage only gestures at one.
- `no`: no narrative can be retold.
- `needed_segments` must be bracket numbers actually shown. List the segments the narrative itself occupies, from where it begins to where it concludes. Do not list segments that are only background, commentary, or later legal discussion of the story.
- Answer from the text alone.
