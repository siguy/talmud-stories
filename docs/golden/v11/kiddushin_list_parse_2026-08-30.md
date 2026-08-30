# Parsing Jeff's Kiddushin list — 2026-08-30

**Why:** `NEXT/05`. A line-based read of `jeff comms/8-30-2026/kidushin.doc` returns
**105 stories**. Nine of them are Jeff's English review notes, which inherit whatever
daf reference preceded them in the flattened text — Kiddushin 81b came out holding
**eleven** stories. Everything in `NEXT/06`, `/07` and `/08` is built on this file.

**Result — measured:** **95 story paragraphs**, **10 expert remarks** (9 Word comments
with exact anchors + 1 in the notes column), **1 entry Jeff marked as his own 2026
addition**, and a recall denominator of **89–94** rather than a single number. The
parser reproduces Ketubot's established **149** as its regression check.

Artifacts: [`scripts/parse_kiddushin_list.py`](../../../scripts/parse_kiddushin_list.py) ·
[`results/expert_lists/kiddushin_2005.json`](../../../results/expert_lists/kiddushin_2005.json) ·
[`tests/test_kiddushin_list_parse.py`](../../../tests/test_kiddushin_list_parse.py)

---

## 1. The document is a table, and the comments are Word annotations

The brief assumed the English notes "sit in a trailing block, so they inherit the
preceding reference." That is a description of the *symptom*, not the cause. The cause
is worth stating because it changes what is recoverable:

`.doc` keeps the main body, footnotes, headers and **annotations** in one character
stream, addressed by CP, with the FIB's `ccp*` fields giving each sub-document's length.
`textutil` flattens them in stream order, so the comments land at the end of the .txt.
But the annotations are not orphaned — `PlcfandRef` holds each comment's **anchor CP in
the main text**, and `PlcfandTxt` delimits the bodies.

```
ccpText 30663 · ccpAtn 841 · PlcfandRef lcb=310 -> (310-4)/34 = 9 anchored comments
```

So every note can be put back exactly where Jeff put it. Reading the OLE streams
directly also recovers the table: `0x07` terminates every cell and again the row, giving
the four columns (מיקום | טקסט | מקבילות | הערות) exactly instead of by heuristic.

```
355 cells / 5 = 71 rows   (1 header + 70 data rows)
```

The old parser needed a citation-word heuristic to keep the parallels column out of the
story stream. Column-aware reading makes that unnecessary — and the heuristic was
load-bearing: four parallels entries are long enough to pass a word-count filter.

## 2. What the two parsers disagree about

| | line-based | table-aware |
|---|---|---|
| entries | 105 | **95** |
| Kiddushin 81b | **11** | 4 |
| max stories on one daf | 11 (81b) | 6 (81a) |
| English notes counted as stories | 9 | 0 |
| parallels counted as stories | 4 | 0 |

The remaining differences are reference assignment. The line-based reader does not
handle Hebrew range labels, so a story under `כב ע"ב-כג ע"א` stayed on the previous daf.

**81a holding 6 is not a new anomaly** — it is the yetzer hara cluster (Rav and Rav
Yehuda on the road, Rav Bibi, the captives at Neharde'a, R. Meir, R. Akiva, Plimo).

## 3. The count, and how it was checked

Three independent checks, because the count is the whole deliverable:

1. **Known answer.** The same parser on `b.ketubot (1).doc` returns **149** — the count
   the Ketubot recall measurement was built on. Asserted by `--self-test`.
2. **Independent renderer.** All **95/95** story texts appear character-for-character in
   Apple's `textutil` output. The six that first failed differed by exactly one
   character — the retained annotation marker, now stripped.
3. **The residual is explained.** `textutil` yields 99 Hebrew paragraphs of ≥8 words:
   95 stories + the 4 long parallels entries. Nothing unaccounted for.

Five entries were also read against the document by hand, chosen to cover the hard
cases: a plain row, a range label, a row holding four stories, the multi-label row, and
one on 81b.

## 4. Blindness — and the brief's guess was the wrong way round

`NEXT/05` read `הוספתי--י.ר.` as "very likely marks stories he took from **our**
output," which would inflate recall. The document says otherwise.

**The one marked addition.** Exactly one comment carries the marker, anchored in the
45a–46b row, reading `מה ע"ב` / `הוספתי--י.ר.` — *"45b — I added — J.R."* The entry he
added is the only **vocalized** paragraph in the document. That matters: Jeff's 2005
typing is unvocalized throughout (Ketubot: 149 of 149 unvocalized), while Sefaria's text
carries nikud. One paste, and he labelled it.

It is also a **duplicate** — a shorter form of an entry he already had four paragraphs
below, trimmed before the `אמר אביי` scriptural coda. Given that his other 2026 comments
are boundary corrections, the likeliest reading is that this is one too. Flagged
`blind: false` either way; it never enters a recall denominator.

**The five in `Kiddushin missed stories.docx`.** All five appear in the list. These are
*not* ours: per
[`kiddushin_feedback_analysis_2026-04-23.md`](../v7/kiddushin_feedback_analysis_2026-04-23.md)
they are the five stories **Jeff flagged that our detector missed**, in April 2026. So
they are not circular — but they were selected *precisely because we missed them*, so a
denominator that includes them is biased **downward**, the opposite of the brief's fear.

Nothing in the document says whether they were in the 2005 original. Two of them (33a,
53a) carry 2005-era parallels annotations, none carries an addition marker, and Jeff did
mark the one thing he added — so the balance of evidence is that they were always there.
That is **indicated, not measured**, so the artifact refuses to collapse it:

```
recall_denominator_max = 94   all blind, unique entries
recall_denominator_min = 89   minus the five expert-flagged misses
```

**`NEXT/06` must report recall over both and quote the range.** On 94 the five count as
misses; on 89 they are excluded. The true value is one of the two, not between them.

## 5. The ten remarks, each attached to its passage

Nine Word comments plus one in the notes column. Six anchor inside the story text; three
sit at the end of a location cell (labelling the row); one is the notes cell. The
attachments are self-verifying — the note names what is in the passage it points at:

| | note | attaches to | check |
|---|---|---|---|
| `c_00` | "very minimal story… dialogue *sent* through messengers or letters" | 10b | the passage **is** an exchange of letters (Yochanan b. Bag Bag ↔ R. Yehuda b. Beteira) |
| `c_01` | "these words should be omitted… the Talmud's comment on the alternative story" | 22b | the entry ends in `איכא דאמרי… ואיכא דאמרי…` |
| `c_02` | "a few more words should be included: `סֵירוּס דְּמַאי?…`" + "These seem to be the words of Rav Hisda" | 25a | the entry ends at `רבי אומר: אף הסירוס` |
| `c_05` | "this *response* (teirutz)… part of the dialectical argumentation" | 39b | the entry ends `ר' יעקב מעשה חזא` — a teirutz |
| `c_note_28` | "example *hada ve'od* that looks Amoraic" | 33b | the passage runs `חדא, ד… ועוד, …` |

`c_02` is **two** remarks in one annotation — a boundary instruction and an attribution
note. `NEXT/08` should sort at the sentence level, not the comment level.

## 6. Two loose ends for `NEXT/08`

- **A dangling `מו ע"ב` (46b) label with no story beside it**, in the row Jeff edited.
  He wrote a location and did not fill it in. Worth asking about, or checking what sits
  at 46b.
- **`c_02` quotes vocalized Hebrew** — Sefaria text, so it can be aligned to segments
  directly. Mind `quote_polarity`: this quote is text to **keep**, not to cut.

## 7. What was left ambiguous, deliberately

One row carries three labels (`מה ע"א` / `מה ע"ב` / `מו ע"ב`) for four stories, so the
document alone cannot say which belongs to which — paragraph-index alignment across
cells gets 2 of 4 right, because a long story occupies many visual lines and a label
occupies one. Those four were resolved by anchoring the text against Sefaria's Kiddushin
and reading off the daf (all matches ≥0.92 coverage), and carry
`ref_source: text_anchored` so the resolution is auditable. That is an objective fact
about where a passage sits in the Talmud, not a judgement about what counts as a story,
so it does not make the list less blind. Every other reference comes from Jeff's own
label.
