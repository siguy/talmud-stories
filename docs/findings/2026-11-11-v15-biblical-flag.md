# Detector v15: a biblical flag that agrees with the judges (2026-11-11)

**Bird's-eye.** Biblical stories now ship on the Septimus site with an `out_of_scope: "biblical"` flag, and the flag is what keeps
them out of Jeff's scholarly catalogue (R-S1, "rabbis and post-biblical figures"). So the detector's own biblical
filter (Stage 4j) has to *flag* accurately rather than delete. v14's 4j caught 20 of the 141 passages the judges call
biblical. v15's rule catches 135, flags nothing Jeff calls in scope, and on the site it removes five wrong flags and
adds none the judges had not already set.

Code: `src/story_detector_v15.py` (`biblical_flag`; v14 copied, only 4j changed). Measurement:
`scripts/measure_biblical_flag_reach.py` (no model calls). Tests: `tests/test_biblical_flag_v15.py`.

## 1. What v14 got wrong (read off the evidence strings)

4j reads `criteria.identifiable_characters.evidence`, the actor list Stage 2 writes. v14 flags when every actor
part names a listed biblical figure or a generic person. Reading every part across all 68 runs showed five faults:

| fault | example (run on disk) |
|---|---|
| a group actor blocks the flag | "Esther and the Sages" (Megillah 7a:2-3) |
| God, angels, Satan count as non-biblical actors | "Moses, the Holy One Blessed be He, and the ministering angels" |
| a minor biblical name not on the list blocks it | "Ahab, Elijah, Hiel" (Sanhedrin 113a:10-13); Doeg, Joab, Balaam, Korah ... |
| generic words matched as **substrings** | `man` inside "Roman", so "a Roman official" read as an anonymous person |
| a biblical name inside a post-biblical one | "Elisha (Man of Wings)", the tanna; "Miriam of Tarmod" |

## 2. The v15 rule

Each actor part is one of: **B** biblical figure, people or place; **E** Elijah; **D** God, angels, a heavenly voice,
the Israelites; **N** a group that takes its era from the others (the Sages, the king, the priests) or a name that is
also a rabbi's (Levi, Eliezer, Samuel); **G** an anonymous person; **X** anything else. Flag when there is no
rabbinic signal and no X, and either a B part (Elijah counts only beside D, never beside a person — Jeff's edge 1),
or only D parts ("God and the Jewish people", no rabbi present). Details in the code's comment block; every rule
there cites the run it came from.

The rule leans conservative where it is unsure: a patronymic whose father shares a rabbi's name is X ("Joshua ben
Levi", "Doeg ben Yosef"); an unnamed description is G, which never triggers. Jericho and "the ark" were taken off the
place list after Pesachim 57a (Second-Temple Jericho) read as biblical.

## 3. Reach (Lesson 27), every run the site reads

37 tractates, 68 runs plus the three reviewed goldens, **6,122 story rows**. Counted as distinct passages
(a passage in both runs counts once):

| | passages |
|---|---|
| flagged by v14's rule | 31 |
| flagged by v15's rule | 155 |
| **newly flagged** by v15 | **132** (100 graded YES/HIGH) |
| **unflagged** by v15 | **7** |

Newly flagged by tractate: Sanhedrin 47 (Perek Ḥelek), Sotah 15, Megillah 10, Pesachim 10, Shabbat 7, then 1-5 each in
18 more. **Measured** on the runs; every one was read.

**Unflagged (all read):** Shabbat 49a and 130a (Elisha "Man of Wings", a tanna), Nazir 47a (Miriam of Tarmod), Bava
Batra 7b (a pious man and Elijah), Sanhedrin 63b (Elijah and a starving child after the Destruction), Makkot 11a:16
(Rabbi Joshua ben Levi), Sanhedrin 64a:3-8 (the people in Nehemiah's day and Zechariah capture the evil
inclination). The first six are post-biblical and right to unflag. The seventh is an era edge: the judges flag it,
the site still does (the judges' flag stands), and the parallel in Yoma 69b, whose actor list names "the Men of the
Great Assembly", v15 flags. **Indicated**, not measured: one case.

**Sample read of the new flags:** David and the Sages of Israel (Berakhot 3b), Hezekiah and Isaiah (Berakhot 10a),
Og and Moses (Berakhot 54b), Satan and Moses (Shabbat 89a), Ahasuerus and the Sages (Megillah 12b), the Sodom
stories (Sanhedrin 109a-b), Balaam and Balak (Sanhedrin 106a), Othniel and Achsah (Temurah 16a). All biblical.

## 4. Against Jeff (L-045)

- **His yes:** 0 passages v15 flags overlap a passage Jeff said yes to or listed in 2005. *Limit:* only Ketubot's
  golden carries actor lists (144 rows); the Gittin and Kiddushin goldens carry none, so v15 cannot reach them and
  the site keeps v14's record there (none is flagged).
- **His scope edges** (`jeff:scope-edges`): 169 rows across the runs name Elijah, Titus, Yannai, Agrippa, Herod,
  Helene, Ḥoni, Shimon HaTzaddik and the like. v15 flags 2, both "Ahab, Elijah, Hiel" — 1 Kings 17, the miss the
  accuracy review found. Elijah with a rabbi, a biblical figure cited in a rabbinic story, and the post-biblical
  kings are pinned as not-flagged in the tests.

## 5. Against the judges

Passages a judge flags biblical (both say out of scope, Claude alone, or a hand flag): **141. v15 catches 135
(96%); v14 caught 20 (14%).** The 6 v15 misses: two lepers with no name (Berakhot 54a), the prophets instituting
Torah reading (Bava Kamma 82a; "the prophets among them" is a description), Eliezer and a wedding guest (Sanhedrin
109b:7; Eliezer is also a rabbi's name), Elijah and the widow's son (Sanhedrin 113a:13-15; "the woman's son" is a
person, so Elijah does not trigger), Onias's temple (Menachot 110a; Second Temple, so the judges are wrong there),
and Sanhedrin 113b:0, Elijah and Rabbi Yosei, which overlaps a judge-flagged unit and which Jeff's edge puts IN. The
site still flags the judges' passages: the flag is judges OR hand OR v15.

Passages v15 flags that the judges do not: **20.** In 18 the Gemini judge said `out_of_scope` and Claude said `not`
(not a story at all), so the site drops them whatever the flag says. The other two are Sotah 33a:8 (Gabriel teaches
Joseph seventy languages) and Eruvin 104b:4 (the exiles return with Haggai, Zechariah and Malachi): both biblical,
both LOW, neither on the site.

## 6. On the site

`build_site_data.py` now reads `biblical_flag()` on each story's actor list (falling back to v14's record where a
story has none), and writes the flag as `out_of_scope: "biblical"` (null when in scope; was `biblical: true`).
Rebuilt `site/data`:

- **stories: 1,897 → 1,897**, every id unchanged (the flag never narrows or promotes);
- **flagged biblical: 102 → 97.** The five removed are the post-biblical stories in §3 that ship (Shabbat 49a,
  130a; Nazir 47a; Bava Batra 7b; Sanhedrin 63b). v15 adds no flag the judges and hand flags had not already set:
  on what ships, they already covered it. Its value on the site today is the five corrections; its value next is a
  tractate whose judges miss one, since Gemini is the detector's own model (plan §2.5's weak spot).

## 7. What this does not settle

- The "only God and the people" rule also flags timeless heavenly scenes (angels ask God about Hallel, Arakhin 10b)
  and an eschatological trial (Avodah Zarah 3a). Neither is about rabbis or post-biblical figures, so R-S1 puts them
  outside Jeff's scope too, but "biblical" is the wrong word for them. None ships today. Simon's answer (2026-11-11):
  the site field is `out_of_scope: "biblical"`, so a reason such as these can later get its own value without a
  new key. All flags carry `"biblical"` for now.
- v15 is adopted **for flagging only**: the runner still imports v14 (§ Outcome of
  `work/done/2026-11-11-v15-biblical-flag.md`).
