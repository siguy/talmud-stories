You are fixing where stories start and end on a family website for reading the stories of the Babylonian
Talmud. Readers want the story itself: the events, told from beginning to end. They do NOT need the legal argument
around it -- the Gemara's questions, proofs and rulings that come before or after the events.

Each file shows one story (segments marked STORY) with the discussion around it (BEFORE / AFTER). A segment that
belongs to another story already on the site is marked "(site story <id>)". The line "Drafter's concern:" says why
this story was flagged. Its segment numbers refer to an earlier view of the
text; use only the numbers in this file.

Decide ONE of:
- "keep": the STORY segments are right as they are (or two different stories sharing one background, which is fine).
- "adjust": give new first and last segment numbers. You may DROP segments of legal argument at either end, and you
  may ADD segments to finish a story that is cut off -- at most 2 segments before the current first STORY segment and
  at most 4 after the current last one. Never include a segment that belongs to another site story.
- "merge": this story and the adjacent site story <id> are really ONE story split in two. Only when that other story
  is directly next to this one (no segment between them), and only if they are the same events, not two stories.

Answer with ONE JSON object per file:
{"code": "<the Story code on the first line>", "action": "keep" | "adjust" | "merge",
 "first": <segment number, for adjust>, "last": <segment number, for adjust>,
 "merge_with": "<site story id, for merge>", "reason": "<one sentence>"}

Prefer the smallest change that leaves a complete story with the legal argument removed. A segment that mixes the
end of the story with the start of the argument stays in (segments cannot be cut in the middle).
