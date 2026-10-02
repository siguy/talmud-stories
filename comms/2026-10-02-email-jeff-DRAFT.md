# Email to Jeff — 2026-10-02 (DRAFT, in Simon's Gmail drafts)

**To:** Jeffrey.Rubenstein@nyu.edu
**Subject:** Talmud stories: how the system works now, some results, and 8 quick rulings

Generated from `results/consensus/contrast_pairs.json` (examples and links) — the Gmail draft is this text verbatim, unwrapped. Questions map to `comms/JEFF.md`: 1 `jeff:alluded-incident`, 2 `jeff:speech-conflict-line`, 3 `jeff:report-vs-incident`, 4 `jeff:custom-without-event`.

---

Dear Jeff,

Here's a short update on the story-finding project. There's also a small request at the end: eight passages, each needing one word from you. It should take about ten minutes.

In one sentence: the AI now reliably recognises the clear stories. What's left is the borderline cases, and those need your rulings rather than more engineering.

How the system has changed

Over the last few months we have rebuilt the process around two ideas, both meant to make each of your answers go much further.

1. Rules that scale. Every time you rule on a passage, we write the principle down as a numbered rule, in your own words, with the date and the passages you ruled on. There are 12 so far. Examples: an incident followed by a ruling can be a story (your stolen-cow case); speech alone is borderline only when there is conflict; a bare report of what someone did is not a story. The AI then applies those rules to every passage in every tractate, so one answer from you now decides many passages, not one. It also gives the project a written, consistent standard: rules for scholars that anyone can read and apply the same way, instead of judgments that live in one person's head.

2. AI as the judge, with you as the final word. Two different AI models, one from Google and one from Anthropic, each read every passage against your rules on their own. Where they agree, the passage is a strong candidate. Where they disagree, it comes to you. We also slip a few of the agreed passages into each page you review, unmarked, so we keep measuring how often the agreed answers are wrong. Nothing goes into the final collection on the AI's word alone.

The aim is that your time goes only to the genuinely hard passages, and every answer you give becomes a rule the AI applies everywhere.

Some results

1. Recognising stories. Your 2005 lists for Ketubot, Kiddushin, Gittin and Yevamot hold 444 stories. Our AI judge accepts 434 of them (98%) as stories or borderline. When both models are asked, they agree on rejecting only 9, and every one is a genuine edge case: a habit with no single event, a sharp scholarly exchange, an incident mentioned in passing, or the Gemara's commentary on a Mishnah story. Those are the questions below.

2. Finding stories. The detector, which scans every page, finds 90% to 97% of your listed stories, depending on the tractate. The largest group of misses was a story's near-twin sitting right next to one we found (R. Zadok and the noblewoman, then Rav Kahana and the noblewoman). A second, targeted pass now recovers these; on Yevamot it recovered all six such misses.

3. Accuracy. When the detector says "story", you have agreed about 92% to 95% of the time across your review rounds.

So the clear stories are now found and recognised with high confidence. What remains is to draw the lines on the borderline cases, make sure your rulings are written into the AI's instructions, and then run it across the rest of the Talmud.

Things we tried, and what we learned

1. We gave the AI your corrections as worked examples. It memorised those pages rather than learning the principle, so we stopped.

2. We asked the AI to mark exactly where a story starts and ends, letter by letter. It can't count characters reliably, so we now mark boundaries by whole sentences.

3. Our first AI judge rejected many of your listed stories. The fault was ours: your July rule about the stolen cow was missing from our rulebook, and a note of ours said the opposite. Restoring your words fixed most of it.

4. We broke "is this a story?" into nine smaller questions: did something happen, is it only speech, is it a habit, and so on. That made a worse judge, but it showed exactly which four lines need your ruling. Two of the four are lines we drew ourselves, and your 2005 lists disagree with them.

Eight passages to rule on

For each one, please reply with its code and one word: story, borderline, or not. Add a line on why if you like. For example: "1A story, 1B not". The links open the passage on Sefaria in Hebrew and English.

Question 1. An incident told in a line or two inside a legal argument, as evidence for one side. Is it a story? This line is ours, not yours. Your lists keep these incidents, so we suspect we are wrong.

1A. Kiddushin 80b (the last segment): The Rabbis worry about temptation even in mourning, "like that incident": a widow at her husband's grave sleeps with the guard of an executed man's body, and when that body is stolen she has her husband dug up to replace it. https://www.sefaria.org/Kiddushin.80b.9-12?lang=bi

1B. Yevamot 107b: Beit Hillel cite the wife of Pishon the camel driver, who refused him in his absence; Beit Shammai answer that he cheated her, so the Sages cheated him. https://www.sefaria.org/Yevamot.107b.8?lang=bi

Question 2. In a scholarly exchange, when does a sharp remark make it conflict (borderline, under your rule) rather than ordinary discussion (not a story)? Both passages are on your 2005 lists, and our two AI judges split on exactly this point.

2A. Ketubot 21b: Ameimar praises a ruling. Rav Ashi: "Because your mother's father praised it, you praise it too? Rava already refuted it." https://www.sefaria.org/Ketubot.21b.1?lang=bi

2B. Ketubot 53a: Ravin bar Ḥanina repeats a ruling in R. Elazar's name; Rav Ḥisda answers: "Had you not said it in the name of a great man, I would have called it an injustice." https://www.sefaria.org/Ketubot.53a.12?lang=bi

Question 3. A case brought to a rabbi who rules: when is it a story, and when is it "a legal problem and answer"? You accepted Toviya (Ketubot 85b: a man leaves his property "to Toviya", Toviya comes, R. Yoḥanan rules). You rejected Gittin 80b, a question about a get sent to Rabba by letter, as "a legal discussion at a distance". You marked both passages below "not a story" in February, before your July rule, and under that rule we would now call them stories. Were those "no"s about the passage itself, or about how much text we showed you?

3A. Ketubot 50b: Orphans' property is held by R. Banai; the orphan daughters come before Shmuel, who tells him to support them from it. (The Gemara then analyses the ruling.) https://www.sefaria.org/Ketubot.50b.5-6?lang=bi

3B. Ketubot 50a: R. Yitzḥak bar Yosef finds R. Abbahu in the assembly at Usha, asks who taught the Usha ordinance, and learns it from him forty times until it is "as if in his pocket". https://www.sefaria.org/Ketubot.50a.11?lang=bi

Question 4. A rabbi's habit, with no single "one day…" event. Is it a story? Your Beitar rule covers a habit followed by a one-time event. The idea that a habit alone is not a story is our note, not yours, and your 2005 lists keep both passages below.

4A. Ketubot 61a: Two pious men: one fed the waiter before the meal, the other after it. Elijah spoke with the first and not with the second. https://www.sefaria.org/Ketubot.61a.15?lang=bi

4B. Ketubot 67b: R. Abba would tie coins in his scarf and toss it over his shoulder to the poor, watching from the corner of his eye for swindlers. https://www.sefaria.org/Ketubot.67b.17?lang=bi

The project website

I have put up a short public page about the project, with a scroll-through of two stories surfacing from the text: https://simonbrief.com/talmud-stories. It's a work in progress, so please forgive the rough edges.

What happens next

1. Your answers to these eight passages become rules, in your words, and go into the AI's instructions.

2. We run the next review round, on Yevamot. You will see only the passages the two AI judges disagree on, plus a few unmarked spot checks: about 35 passages, with Hebrew and English side by side.

3. Once the spot checks hold up, we extend to the remaining tractates, keeping Eruvin aside as a final, untouched test.

Thank you, as always. The short version of what we've learned is that the AI handles the clear cases well, and the hard cases are exactly where your judgment matters. Each ruling you give now carries across the whole Talmud.

Best,
Simon
