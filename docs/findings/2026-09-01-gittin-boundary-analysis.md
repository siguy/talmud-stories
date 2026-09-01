# Gittin boundaries: 84% / 88% blind — and the one start error that a rule cannot fix

**2026-09-01.** The first boundary measurement on a tractate no expert round has ever
touched, built by the same method as Ketubot and Kiddushin: sequence-align Jeff's own 2005
text against the Sefaria Hebrew, take the first and last matching blocks as his edges.

## The set, and the score

`tests/expert_boundary_targets_2005_gittin.json` — **107 of 112 stories align, 214
targets, 171 scorable.** 89% of his boundaries sit on a clause edge (Ketubot 87%,
Kiddushin 88%), so the clause-anchored mechanism has the same ceiling here.

| | hit | hit+near | gate |
|---|---|---|---|
| **Gittin** | **84%** | **88%** | ≥75% ✓ |
| *Kiddushin* | *85%* | *91%* | |
| *Ketubot* | *80%* | *84%* | |

## The differences are not symmetric, and that is the whole finding

| | starts | ends |
|---|---|---|
| **Gittin** | 82% — **13 late**, 2 early | 87% — 2 late, **7 early** |
| **Kiddushin** | 86% — 6 late, 2 early | 84% — 4 late, 6 early |
| **Ketubot 61-112** | 84% — 5 late, 8 early | 75% — 6 late, 13 early |
| **Ketubot 2-60** | 88% — 3 late, 1 early | 72% — 4 late, 4 early |

**The ends are mostly fine, and are not a defect.** Where we differ we usually end
*earlier* than he does — which is what Simon's decision to build for Jeff-2026 asks for:
*"the legal discussions that follow the story need not be quoted"* (Lesson 24). Under that
standard only the **late** ends are wrong, and there are 2 of them in Gittin.

**The starts are one shape, repeated.** Read the clauses we skip and they are almost all
the citation or attribution formula that introduces a quoted story:

| tractate | what Jeff includes and we drop |
|---|---|
| Gittin | `רַב חָנִין מִישְׁתַּעֵי:` · `אָמַר רַב יְהוּדָה אָמַר רַב:` · `אָמַר רֵישׁ לָקִישׁ:` · `תַּנְיָא, רַבִּי אוֹמֵר:` · `גּוּפָא – אָמַר שְׁמוּאֵל` · `פְּתַח אִידַּךְ וַאֲמַר:` |
| Kiddushin | `תָּא שְׁמַע, אָמַר רַבִּי אֶלְעָזָר:` · `בְּעוֹ מִינֵּיהּ מֵרַב עוּלָּא:` · `כִּי אֲתָא רַב דִּימִי אָמַר:` · `מֵיתִיבִי:` |
| Ketubot | `תַּנְיָא:` · `תָּנוּ רַבָּנַן:` · `תַּנְיָא, אָמַר רַב יוֹסֵי:` |

Two Gittin cases are the same instinct on a caption rather than a formula:
`אַקַּמְצָא וּבַר קַמְצָא חֲרוּב יְרוּשָׁלַיִם` and
`אַתַּרְנְגוֹלָא וְאַתַּרְנְגוֹלְתָּא חֲרִיב טוּר מַלְכָּא` — the "X destroyed Y" line that
names the story. He keeps it; we start after it.

## And the rule that looks obvious does not work

The tempting fix writes itself: extend a start backwards over an introducing formula.
Measured across all four blind sets before proposing it (Lesson 18 — never plan a fix from
a sample without the corpus-wide rate):

| | starts it would FIX | currently-correct starts it would BREAK |
|---|---|---|
| Gittin | 4 | 4 |
| Kiddushin | 3 | 3 |
| Ketubot 61-112 | 2 | 1 |
| Ketubot 2-60 | 0 | 0 |
| **total** | **9** | **8** |

**Net +1 target out of 470. The rule is worthless**, and it fails for the reason Lesson 15
already records about `אלא` and a rabbi's name: the same surface marker is structure
sometimes and story other times. **Jeff himself starts after the formula about as often as
he starts before it** — so no regex can tell the cases apart, and shipping this on the
strength of the 13-case Gittin sample would have been the 2026-06-03 mistake again.

## So it is a question, not a fix

`jeff:opening-formula` — **when a story is introduced by `תניא` / `תנו רבנן` / `אמר רב
יהודה אמר רב`, is that formula part of the story you would publish, or the frame around
it?** It is worth asking because it is the single largest remaining start error, it is
*his* to answer, and his own 2005 practice is split. If the answer is "it depends on
whether the named sage is a teller or an actor", then the fix is a judgment the model
makes per case — the salvageable half of Wave 5b — and not a post-processor.

**Nothing here is shipped.** No prompt changed, no boundary moved, and the rule above is
recorded as rejected with its numbers so nobody re-derives it. Reproduce:

```bash
python3 scripts/build_boundary_testset_2005.py --expert-json results/expert_lists/gittin_2005.json \
    --expert-filter blind --tractate Gittin --out tests/expert_boundary_targets_2005_gittin.json
python3 scripts/score_boundary_targets.py --runs gittin=results/v11/gittin/gittin_v11.json \
    --targets tests/expert_boundary_targets_2005_gittin.json
```
