You are reading a window of consecutive segments of the Babylonian Talmud (Hebrew/Aramaic with an English translation), numbered `[1]`, `[2]`, ... in order. Nothing in the window is marked as a proposed unit: the window may contain one story, several, or none, and a story may begin before the window's first segment or run past its last.

Your task: find every story in the window and retell each one. A story is: someone does or undergoes something, something turns, and it ends somehow. Many Talmudic passages are not stories: a legal argument, a rule with its reasoning, a hypothetical case, a description of a habit or custom, a bare citation of what a sage said. Do not invent events the text does not contain, and do not list something as a story if all you can truthfully write is "X argued that...".

For each story, name the segments it occupies: from the segment where the narrative begins to the segment where it concludes, so that someone reading only those segments could retell it. Do not include segments that are only background, commentary, or later legal discussion of the story. A story that is cut off by the edge of the window should list the segments up to the edge.

Answer with ONE JSON object and nothing else:

{
  "stories": [
    {
      "actor": "who the story is about",
      "event": "what happened, in one sentence",
      "turn": "what changed or went wrong or was revealed",
      "outcome": "how it ended",
      "needed_segments": [bracket numbers of every segment the story occupies, first to last],
      "summary": "2-4 sentences retelling it in plain English"
    }
  ]
}

`stories` is an empty list if the window contains no story. Use only the bracketed numbers shown. Answer from the text alone.
