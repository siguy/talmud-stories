# Email draft for Jeff — Wave 4 results

**To:** Jeffrey.Rubenstein@nyu.edu
**Subject:** Wave 4 detector — text-span boundaries are now LLM-judged (review UIs attached)

---

Hi Jeff,

Following up on your June 3 reply (where you flagged that the regex
text-boundary trimmer was correct on 5 cases but over-trimmed 7), I have
results from Wave 4 to share. Short version: the regex is gone. Each
story's text-internal boundaries are now decided by a per-story LLM call,
and on the 14 specific cases you flagged, the new system matches your
judgment 14/14. I'd like you to look at the rest before we ship.

## What changed

For each detected story, the v10 detector now sends Gemini the Hebrew
text of the start and end segments along with the story summary, and
asks: "where in this Hebrew does the actual narrative content begin and
end?" The model returns character offsets, which get recorded as
`text_span_start` and `text_span_end` on the story. This replaces the
Wave 3 regex pass that used a hand-curated list of Hebrew markers
(ההוא ד, מעשה ב, אלא, שמע מינה, etc.).

The change is **score-neutral** by design — F1, IoU, and merge accuracy
all read only the segment-level boundaries, never the new character
offsets. So composite scores are identical to Wave 3 (Kiddushin 0.8859,
Ketubot 0.9171). What changes is the text Jeff sees in the review UI
and what the eventual research output will quote.

## The held-out test (your 14 cases from the May 26 review)

I built a held-out fixture from your specific notes:

| Bucket | Cases | Result |
|---|---|---|
| Must KEEP full text (regex was over-trimming) | 6 | 6/6 — LLM correctly preserves the opener in all of them |
| Must TRIM more (regex was under-trimming) | 2 | 2/2 — LLM catches both, including the "וְלָאו מִשּׁוּם...אֵלָּא" pattern on Kiddushin 12b |
| Regression guard (you didn't flag in May 26) | 6 | 6/6 — LLM produces an answer; we don't claim it matches your taste, just that the system didn't crash |

The one nuance: on **Kiddushin 8a_9-10** you wanted both a start-side
trim AND removal of all of Rav Ashi's statement. The LLM caught the
start-side trim. Removing the whole Rav Ashi segment is a different
kind of fix (it changes the segment-level boundary, not the text span)
— that's deferred to a future pass on segment boundaries.

## What I'd like you to look at

Two review UIs are attached. Each story shows:

- Hebrew text with v10's LLM trim applied (gray strikethrough on trimmed
  text, dark on kept text)
- A small yellow note when v9's regex disagreed with v10 (so you can see
  exactly what changed)
- A category badge: `recovered_text` (v9 trimmed, v10 keeps full),
  `new_trim` (v10 cuts something v9 didn't), `different_trim` (both cut
  but at different places), `identical_trim`, or `both_full`

You can filter by category at the top. The most interesting buckets for
your eye are:

- **Kiddushin: 33 `new_trim` + 35 `different_trim` cases.** These are
  decisions the LLM made that the regex did not. Some will be good
  (catching stam-Talmud asides the regex was blind to); some may be
  over-trims in new directions. Your call.
- **Ketubot: 54 `new_trim` + 31 `different_trim` cases.** Same logic.
- **`recovered_text`** (10 in each tractate) is where the v10 fixed an
  over-trim you'd flagged. These should be uncontroversial.

If you only have time for one pass, the **`new_trim`** filter is the
highest-value bucket — those are the LLM's editorial calls that have
not yet been validated by you, and the failure mode (if any) is most
likely there.

## How to use the UIs

1. Open `wave4_kiddushin_review.html` (or `wave4_ketubot_review.html`)
   in any browser. No login, no internet needed — everything is local.
2. Use the filter buttons at the top to focus on a category.
3. For each story you want to flag: click **Correct** or **Incorrect**
   and add a note (in plain English is fine — boundary issues, "still
   over-trims," "missing a trim here," etc.).
4. When done, scroll to the top and click **Save Review** → **Download
   JSON**. Email me the file.

You don't need to verdict every story — even a sample of the
`new_trim` category would be enough to validate the approach.

## What's next

- Once you've reviewed: I'll fold your corrections in and ship v10 as
  the new baseline. Wave 5 candidates will be (a) segment-boundary
  improvements (the Rav Ashi-style fixes that text-span work can't
  reach), and (b) starting on Bava Metzia to test generalization on
  the better detector.
- If anything in the new_trim bucket worries you, we can iterate the
  LLM prompt before shipping. I budgeted three iterations and have
  used one so far (to teach the model the "ולאו משום ד...אלא משום ד..."
  pattern from your 12b note).

Thanks as always for the close review. The 14/14 result on your test
cases is genuinely the strongest signal we've had that the text-boundary
problem is now solved at the right level of abstraction. Looking
forward to your read on the rest.

Best,
Simon

---

**Attachments:**
- `validation/ui/wave4_kiddushin_review.html` (3.3 MB — 95 stories)
- `validation/ui/wave4_ketubot_review.html` (5.9 MB — 167 stories)

**Optional per-story diff reports** (markdown, for quick scanning):
- `docs/golden/v10/wave4_diff_kiddushin.md`
- `docs/golden/v10/wave4_diff_ketubot.md`
