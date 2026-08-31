# Lesson 24 — Two expert sources can encode two different tasks

**2026-08-30**

We built a neutral boundary ruler from Jeff's 2005 story list and treated
it as a bigger, better version of the ruler built from his 2026 review
notes. It is bigger. It is not the same question.

Capping end-trims scores:

```
                        neutral 2005 (n=229)   corrections 2026 (n=20)
  trim both ends            80% / 84%              70% / 80%
  end-trim capped at 3      81% / 86%              65% / 75%
```

Helps one, hurts the other. Reading the disputed cases explains why: the
model removes stam-Talmud legal discussion after a story, exactly as our
prompt says. Jeff's 2005 list KEEPS it. His 2026 notes say "the legal
discussions that follow the story need not be quoted."

Both are Jeff. Neither is wrong. In 2005 he was building a story INDEX —
where to find a story in its sugya — so the legal frame belonged. In 2026
he is reviewing a tool that DISPLAYS stories, so it does not. Split by
edge: START boundaries agree 7/7, END boundaries 16/19.

**Rule:** before pooling two expert sources into one metric, check what
each was PRODUCED FOR. Agreement on the aggregate can hide a systematic
split on one sub-question. Report them separately until you have shown
they answer the same question, and break agreement out by sub-question
(here, by edge) rather than trusting a single headline rate.

**Why:** we had an 84% agreement number and nearly used it to justify
pooling. The 16% that disagreed was not noise — it was the entire END
boundary definition, which is most of what the wave was tuning. Tuning
against the pooled number would have optimised toward whichever source
happened to have more targets (2005, 14x larger) without anyone choosing
that.

**How to apply:** (a) Ask "what was this artifact made for?" of every
expert input, not just "is it accurate?". (b) When two rulers disagree,
that is a PRODUCT question — which definition are we building? — and it
goes to the human, not into a tuning loop. (c) A metric that can be moved
by choosing a ruler is not yet a metric.
