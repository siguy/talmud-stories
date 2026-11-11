# The 7 Eruvin misses, read against Jeff's current rules (2026-11-11)

**Question (Simon):** v14 proposed 67 of the 74 stories on Jeff's 2005 Eruvin list (90.5%, under the 95%
gate). His 2005 lists predate his 2026 rulings. How many of the 7 misses are still stories under those rulings?

**Source:** `measure_recall_vs_expert_list.py --expert-json results/expert_lists/eruvin_2005.json --tractate eruvin
--detected results/v14/eruvin/run1.json`. `superseded_by_rule.json` has **no Eruvin entries**: Jeff has never
ruled on an Eruvin item. Every reading below is **ours**, applying his rules (`docs/STORY_RULES.md`), so it is
**indicated**, not measured. His lists are evidence, so nothing is removed from the list. These are candidates
for annotation, and questions for him.

| list id | where | lost at | what the passage is | under the current rules |
|---|---|---|---|---|
| eruvin_007 | 13b:11 | detection (the neighbouring 13b:9-10 was found) | elders of Beit Shammai and Beit Hillel visit R. Yohanan ben HaHoranit in his sukkah and dispute | **story** (incident plus conflict). A real miss |
| eruvin_054 | 63a:0-3 | detection (63a:4 found, LOW) | Ravina inspects a knife in Babylon; Rav Ashi challenges him; Ravina justifies it | **story** (an act, a challenge, a justification). A real miss, at the boundary |
| eruvin_008 | 14b:17-18 | triage | "Did you say it?" "No." Rava: "By God, he said it and I learned it from him" | **borderline**, by R-C2 (speech with conflict). Borderline stays in the corpus, so still a miss |
| eruvin_019 | 32b:3-6 | triage | rabbis sit and work through a legal question; R. Nahman approves | **not**, by R-C2: scholarly dialogue is "standard rabbinic dialogue" (his Ketubot 21b and 53a rulings, 2026-10-07) |
| eruvin_041 | 53b:10-11 | detection | how R. Yosei bar Asiyan *would* speak in riddling language | **not**, by R-C3 and R-C2: a habitual frame with no event following, and speech only |
| eruvin_042 | 53b:12-13 | detection | R. Abahu's riddling speech; asked where R. Ilai is, he answers in a riddle | **not / borderline at most**, by R-C2: speech, with no conflict or change |
| eruvin_052 | 60a:15-16 | detection | Abaye asks Rav Yosef whether a dictum is tradition or reasoning, and gets a quip | **not**, by R-C2: scholarly dialogue |

**Recount if the 4 "not" readings hold** (indicated):

| | 2005 list as written | 2005 list under the current rules |
|---|---|---|
| denominator | 74 | 70 |
| triage keeps the page | 72 (97.3%) | 69 (98.6%) |
| detection, given triage | 67/72 (93.1%) | 67/69 (97.1%) |
| end to end | 67/74 (90.5%) | **67/70 (95.7%)** |

Under Jeff's current rules, Eruvin **meets** the provisional 95% recall gate, and triage meets 98%. The real
misses are 3: two in detection (13b and 63a, one of them a boundary miss beside a found story) and one borderline
dropped by triage (14b).

**What makes this measured:** Jeff confirming the four "not" readings. They are 32b, 53b (twice) and 60a, all the
"scholarly dialogue" or "habitual speech" shape he ruled on for Ketubot. They are cheap questions to add to
`comms/JEFF.md`. Until he answers, quote both columns.
