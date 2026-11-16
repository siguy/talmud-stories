You are writing the short background note that sits above one story on a family website for reading the stories of the Babylonian Talmud. The readers are curious adults, many with little or no Talmud background. They will read the story itself (Hebrew/Aramaic with the William Davidson English translation) right below your note.

The file shows numbered segments. Segments marked `STORY` are the story. Segments marked `BEFORE` and `AFTER` are the discussion around it, shown so you can see where the story sits; they are not part of the story.

Write ONE JSON object and nothing else:

{
  "code": "the Story code printed on the first line of the file, copied exactly",
  "note": "2-4 plain-English sentences: what happens IN the story, with just enough setting to follow it (who these people are to each other, what the situation is). Tell the story; do not explain the legal debate around it -- that is the job of `why`. No more than 800 characters.",
  "why": "1-2 sentences: why the Gemara tells this story HERE. What question, ruling or teaching in the surrounding discussion does it support, illustrate, challenge or follow from? Must add something the note does not already say. No more than 300 characters. Empty string if the segments shown do not tell you, or if it would only repeat the note.",
  "people": [{"name": "a person named in the STORY segments", "about": "who they are, in under 160 characters"}],
  "terms": [{"term": "a word or concept a newcomer would stumble on", "meaning": "a plain explanation, under 300 characters"}],
  "flag": "empty string, OR one sentence for the project team if the STORY segments are not really a story, start or stop in the middle, combine unrelated passages, or look garbled"
}

Rules:
- Answer from the text shown. Do not add events, motives or outcomes the text does not contain. If the ending is not in the STORY segments, say the text does not give it, rather than supplying one from memory.
- The note and the why do different jobs and must not overlap. The note is the story: who, what happened, how it ended. The why is the frame: the legal or other question the Gemara is discussing, and how this story bears on it. For a story told to settle a legal question, put the question in `why`, not in `note`. Bad pair -- note: "To settle a legal problem about contradictory witnesses, Rav Nahman cites a case..."; why: "The Gemara is debating contradictory witnesses and cites this case as a precedent." Good pair -- note: "A man with bouts of insanity sold his land. Two witnesses said he was insane at the time, two said he was sane. Rav Ashi ruled ..."; why: "The Gemara is asking whether two witnesses can cancel two others; Rav Nahman cites this sale as the precedent that they do, leaving the land with its owner."
- `why` is about the surrounding discussion as the BEFORE/AFTER segments show it, not about the law in general. Good: "The Gemara has just ruled that a condition can fail for reasons outside a man's control; this case is brought as a precedent for that ruling." Bad: "It teaches the importance of keeping promises." If you cannot see the connection from what is shown, leave `why` empty. An empty `why` is better than a guessed one.
- `people`: at most 5, only people who appear in the STORY segments, spelled as the English translation spells them. God and biblical figures may be included when they act in the story.
- `terms`: at most 4, and only terms that actually appear in the STORY segments. Skip ones the note already explains.
- Plain text only: no Hebrew, no markdown, no HTML. Write for a reader, not a scholar: say "the Sages" rather than "Ḥazal", and explain "baraita", "mishna", "get" and the like if you use them.
- Do not refer to "the segments", "the passage shown", "STORY", "BEFORE" or "AFTER" in any field except `flag`. Say "the Gemara" or "the discussion".
- Use `flag` sparingly. A story told to make a legal point is still a story; flag it only if it has no events at all, or is cut off so badly that a reader could not follow it.
