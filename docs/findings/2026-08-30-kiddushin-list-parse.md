# Parsing Jeff's Kiddushin list — 2026-08-30

**Why:** `NEXT/05`. A line-based read of `jeff comms/8-30-2026/kidushin.doc` returns
**105 stories**. Nine of them are Jeff's English review notes, which inherit whatever
daf reference preceded them in the flattened text — Kiddushin 81b came out holding
**eleven** stories. Everything in `NEXT/06`, `/07` and `/08` is built on this file.

**Result — measured:** **95 story paragraphs**, **10 expert remarks** (9 Word comments
with exact anchors + 1 in the notes column), **1 entry Jeff marked as his own 2026
addition**, and a recall denominator of **89–94** rather than a single number. The
parser reproduces Ketubot's established **149** as its regression check.

Artifacts: [`scripts/parse_kiddushin_list.py`](../../scripts/parse_kiddushin_list.py) ·
[`results/expert_lists/kiddushin_2005.json`](../../results/expert_lists/kiddushin_2005.json) ·
[`tests/test_kiddushin_list_parse.py`](../../tests/test_kiddushin_list_parse.py)

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

**The five in `Kiddushin missed stories.docx` are NOT blind.** That file is the appendix
Jeff refers to as *"additional stories that you and Claude found that were not on my
list"* — a set of cases drawn from across many of our runs, which he annotated
`Yes` / `Low confidence` and then merged into his list. They are in his list **because of
our output**, which is the definition of circular (FRAMEWORK §3). All five are
`blind: false` and excluded from recall.

```
recall_denominator = 89        95 parsed - 1 he added himself - 5 appendix
```

### 4a. What we actually detected, per run — a separate question

Provenance says these five are ours. It does not say we *found* them, and the two are
worth keeping apart: `NEXT/06` needs to know which of the five it should expect to score
as misses. Reproduce with `scripts/check_appendix_coverage.py`:

| run | 33a | 45a | 53a | 71a | 81b |
|---|---|---|---|---|---|
| v7 | PART | – | – | – | – |
| v8 wave1 / wave2 | PART | **full** | PART | – | – |
| v9 wave3 | PART | **full** | PART | – | – |
| canonical (golden) | PART | – | – | – | – |
| v10 wave4 / notrim | PART | **full** | PART | – | – |
| v11 wave5 / summaryfix | PART | **full** | PART | – | – |

`full` = one span covers every segment the case occupies · `PART` = a span overlaps but
does not cover it · `–` = nothing proposed there.

Three findings in that table:

- **45a is the one clean win.** Absent in v7, found from Wave 1 onward — a real
  improvement, visible only because the appendix recorded the case.
- **33a and 53a have never been fully caught in any run.** Both are permanently `PART`:
  we propose one segment of a two-segment story. That is a **boundary** failure sitting
  on top of a detection near-miss, not a detection miss, and it has survived every wave.
- **71a and 81b were never proposed by any run, ever.** At 71a we propose the *parallel*
  version (`בימי רבי פנחס`, segs 4-5) and never the one Jeff kept (`בימי רבי`, segs 2-3).
  At 81b the story sits at segment 9 and nothing has ever been proposed there.

The last point is the awkward one and it is stated rather than smoothed: the appendix is
described as cases we found, but two of its five are not in any run on disk. Either they
came from a run that was not kept, or from a reading pass rather than detector output.
It does not change the flags — they are in Jeff's list through our process either way —
but anyone using this file should know the sourcing is uneven.

### 4b. The same thing is about to happen to four more tractates

The merge already happened here, and we caught it only because the appendix survived as
a separate file. Jeff is preparing the same appendix for Gittin, Yevamot and Eruvin. If
those entries are merged into those lists without a marker, each list quietly loses the
ability to measure what we missed — **permanently and invisibly**, because a merged entry
looks like every other entry.

**One sentence to Jeff:** keep the appendix a separate file, or mark its entries. Costs
him nothing, and it cannot be reconstructed afterwards.

**And one for us:** every expert list from here on gets checked against whatever we sent
him before it is trusted as blind. `scripts/check_appendix_coverage.py` is that check.

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
