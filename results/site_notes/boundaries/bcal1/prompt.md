You are fixing where stories start and end on a family website for reading the stories of the Babylonian
Talmud. Readers want the story itself: the events, told from beginning to end. They do NOT need the legal argument
around it -- the Gemara's questions, proofs and rulings that come before or after the events.

Each file shows one story as the site shows it now (segments marked STORY) with the discussion around it
(BEFORE / AFTER). A segment that belongs to another story already on the site is marked "(site story <id>)". If there
is a line "Drafter's concern:", it says why someone doubted this story; its segment numbers refer to an earlier view
of the text, so use only the numbers in this file. The line "You may start no earlier than [n] and end no later
than [m]." gives the furthest the story may reach; never go beyond it.

Decide ONE of:
- "keep": the STORY segments are right as they are (or two different stories sharing one background, which is fine).
- "adjust": give new first and last segment numbers. You may DROP segments of legal argument at either end, and you
  may ADD segments to finish a story that is cut off, within the limits line. Never include a segment that belongs
  to another site story.
- "merge": this story and a nearby site story <id> are really ONE story split in two: the same events, not two
  stories. Only when nothing but at most 4 segments lies between them, and those segments are part of the same story.

When a ruling ends the story: KEEP the ruling if it is the outcome of the events (the judge's verdict in the case, what
the sage told the man to do); DROP the Gemara's discussion of that ruling (questions, proofs, other opinions).

If the card holds two separate stories that cannot be told apart by moving its ends, answer "keep" and start the
reason with "TWO STORIES:".

Answer with ONE JSON object per file, in one JSON file keyed by file number ("01", "02", ...):
{"code": "<the Story code on the first line>", "action": "keep" | "adjust" | "merge",
 "first": <segment number, for adjust>, "last": <segment number, for adjust>,
 "merge_with": "<site story id, for merge>", "reason": "<one sentence>"}

Prefer the smallest change that leaves a complete story with the legal argument removed. A segment that mixes the
end of the story with the start of the argument stays in (segments cannot be cut in the middle).
