You are examining one passage of the Babylonian Talmud for a scholarly catalogue of
Talmudic stories. The catalogue's editor is an expert on rabbinic narrative. Below is
his rule register: each rule in his own words, with the date he said it and the
passages he ruled on. Some entries also describe our software pipeline; ignore those
parts and use only what the rules say.

<rules>
{RULES}
</rules>

You will be shown a PASSAGE, segment by segment, in Hebrew/Aramaic and in the English
of the Steinsaltz translation (translator's additions are in plain type, the literal
text in bold). One segment before and one after are shown as CONTEXT so you can see
where the passage sits. Examine the PASSAGE only; the context is not part of it.

**Do not decide whether the passage is a story.** Answer each of the nine questions
below on its own, as if it were the only question you were asked. Do not answer one
question to fit another. A program combines your answers afterwards.

Each answer is `yes`, `no`, `unsure` (the text does not let you tell), or `n_a` (only
where the question says so).

1. `actual`: Does the passage narrate something that happened, an event in the past,
   rather than only a hypothetical case, a legal question, a rule, or an argument?
   A real incident brought before a rabbi for a ruling counts as something that happened
   (R-C0).
2. `event_beyond_speech`: Beyond people speaking (saying, asking, answering, sending a
   question, objecting), does someone **do** something or does something **happen**?
   (R-C2)
3. `conflict`: Only if question 2 is `no`: is there conflict between the speakers
   (a rebuke, a dispute with personal stakes, a confrontation)? If question 2 is `yes`,
   answer `n_a`. (R-C2)
4. `response_or_consequence`: Does someone respond to the event (a court, a rabbi's
   ruling, an action), or does something follow from it, rather than the passage only
   reporting what someone did with nothing following? (R-C0, R-C5)
5. `custom`: Is the core of the passage a custom or habitual practice ("he used to…",
   "he would…")? (R-C3)
6. `event_after_custom`: Only if question 5 is `yes`: does a specific one-time event
   follow the custom ("One day…")? If question 5 is `no`, answer `n_a`. (R-C3)
7. `alluded_only`: Is the incident only alluded to or cited in a phrase, as evidence
   in an argument, rather than narrated? (R-C5)
8. `commentary`: Is the passage the Gemara's commentary on a story told elsewhere (in
   the Mishnah or earlier), explaining or filling in that story, rather than the story
   itself? (R-B4)
9. `biblical_actors`: Are the actors biblical figures in a biblical episode, rather than
   rabbis or post-biblical figures? (R-S1)

Return JSON with exactly these fields:
- `features`: an object with the nine keys above; each value is
  `{"answer": "yes" | "no" | "unsure" | "n_a", "reason": "<one short sentence>"}`
- `segments`: the bracketed numbers `[n]` of the PASSAGE segments where the narrated event
  sits; an empty list if there is none. Never a CONTEXT segment.
