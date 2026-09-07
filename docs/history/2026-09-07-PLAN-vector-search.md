# Vector search over the story corpus (PLAN — not started)

**Status: planning only, 2026-09-07.** Simon is not ready to execute; this records the
design so the decisions don't have to be re-made cold. Nothing in `work/` yet — see
*Future work items* at the end for the split when he is.
**Capability: Publication (6).** This is the discovery surface on top of the resource
itself, not a new detection capability. It inherits Publication's open question below and
should get its own row in `docs/capabilities/6_publication.md`'s "What we tried" table
once execution starts — not before, per the project's own rule about this file describing
history, not intent.

## Open dependency — read before building the schema

`jeff:deliverable-shape` (`comms/JEFF.md`) is unanswered: static citable release, or live
editable database with his notes/references/Yerushalmi-parallels columns and contested
cases kept-and-flagged. This plan builds the parts that are the same either way (corpus
freeze, embeddings, retrieval, testing) and defers the parts that aren't (whether a search
result shows a fixed citation or a live-edited one; whether notes/parallels are searchable
fields). If his answer lands before Phase 5, revisit the schema in Phase 3 first — it's
one migration now, a painful one after the index is full of real queries.

The static architecture below is the natural fit for the citable-release half of his
answer. It doesn't rule out the editable half: edits happen at review-round frequency, not
per-visitor, so if he wants live editing, that's one small separate write path (a form
that appends to a file, reviewed like everything else here) bolted onto an otherwise
unchanged static reader — not a reason to reach for a database now on the strength of a
maybe.

## Goal

Let a researcher search the validated story corpus by theme, keyword, sage, or narrative
type — in English or Hebrew — and get back real stories with real citations, ranked by
relevance, not just by whether a word matches.

## Scope: what's indexed today

Counted directly from `results/canonical/*.json`, filtering `classification !=
NOT_A_STORY` (this is the CLAUDE.md-defined story count, not the count of rows in the
file — those include rejected candidates):

| tractate | indexable stories | median story length | mishnah_stories |
|---|---|---|---|
| Ketubot | 164 | ~840 chars | 0 |
| Kiddushin | 85 | ~830 chars | 0 |
| Gittin | 121 | ~910 chars | 5 |
| **total** | **370** | | |

All comfortably inside any embedding model's context window — no chunking needed, one
vector per story.

Two things any indexer has to decide about explicitly, per CLAUDE.md's data-structure
rule, rather than by accident:

1. **`mishnah_stories[]` is a separate key**, withheld by Stage 4g. Index it, badge it
   `mishnah` in the UI and make it filterable — don't silently fold it into or drop it
   from the main set. `validation/generators/generate_axis_review_ui.py` already does
   this; reuse the same convention rather than inventing a second one.
2. **Confidence tier is data, not a threshold.** `classification` is `YES` /
   `HIGH_CONFIDENCE` / `LOW_CONFIDENCE` / `BORDERLINE`, not just yes/no — Gittin alone has
   4 `BORDERLINE` stories. Store the tier as a filterable field so a researcher can choose
   to exclude `LOW_CONFIDENCE`; don't pre-filter it out at index time, and don't collapse
   it to a boolean.

**Yevamot and Eruvin have expert lists (`results/expert_lists/`) but no canonical file
yet** — they're not in this count and won't be indexed until a canonical dataset exists
for them. Phase 1 should read `results/canonical/*.json` by glob, not a hardcoded
tractate list, so they join automatically without a code change.

## Architecture

**Revised 2026-09-07 — no server, no database.** The first draft of this plan reached for
Cloud SQL by reflex, the way most "vector search" writeups do, without asking whether this
corpus needs a server at all. It doesn't. See *The actual ceiling* below.

| piece | choice | why |
|---|---|---|
| Embeddings | **`gemini-embedding-001`**, called through the `google-genai` SDK already in `requirements.txt`, with the existing `GOOGLE_API_KEY` | Same client the detector already uses. **No new GCP project, no Vertex AI SDK, no service account.** This is the only "Google Cloud" piece left, and it's a one-time offline batch job, not a running service. |
| Storage + serving | **One static file** (embeddings + metadata + tokenized Hebrew/English text), committed to the repo, served by **GitHub Pages** — the exact mechanism `index.html` already uses (`docs/capabilities/6_publication.md`: "Embedded-JSON HTML at the repo root so GitHub Pages can serve it with no build step") | At a few MB total, the whole index can just be downloaded by the visitor's browser. |
| Query execution | **Client-side JavaScript** — cosine similarity over the embeddings + a keyword score over the tokenized text, fused by reciprocal rank fusion, filtered by tractate/tier/mishnah-flag | Brute-force cosine over a few hundred to a few thousand vectors is sub-100ms *in JS*. No ANN index (HNSW/IVFFlat) is needed at this size — that machinery exists to avoid brute force at millions of vectors, which this corpus will never reach (below). |
| **Not** Cloud SQL / Cloud Run | — | A running database costs $10-90/month forever to hold data that fits in single-digit megabytes and changes maybe once a review round. Paying monthly, indefinitely, for a fixed problem is the mismatch — parking a 5-page PDF on a rented server rack because "a server can serve files." Recorded here so a later session doesn't re-propose it without seeing why it was dropped (same reason `docs/capabilities/` exists for the detection side). |
| **Not** Vertex AI Vector Search | — | Built for 10M+ vectors; its always-on index endpoint runs ~$300-700/mo to hold what fits in 5 MB here. |

### The actual ceiling

This isn't "small for now" — it's structurally small forever. Story density measured
directly off the three canonical datasets: Ketubot 0.74, Gittin 0.68, Kiddushin 0.53
stories per amud (`indexable / pages`, same filter as the counts table above). The entire
Talmud Bavli is ~2,711 dapim, ~5,422 amudim. At this density, **the whole Talmud, every
tractate, ever, tops out around 3,000-4,000 stories** — there is no growth trajectory
here that reaches "big data." At 3,500 stories × 768-dim embeddings × 4 bytes, the raw
vector matrix is **~11 MB**; today's 370-story corpus is **~1 MB**. A phone downloads that
without noticing.

## What gets embedded, per story

- **Embedding text** = `one_sentence_summary` (already in every story object) +
  the joined English text of `page_segments[start_segment : end_segment+1]` — the exact
  join CLAUDE.md already mandates for flattening (`page_segments: page.segments`).
  Concatenating the summary in front biases the vector toward the *point* of the story,
  not just its vocabulary — cheap to do since the summary is already computed, no new LLM
  pass required.
- **Hebrew text** is stored and tokenized for exact-phrase/idiom keyword matching
  client-side, not embedded. This isn't a claim that Hebrew embeds worse — it's that idiom
  and proper-noun search wants exact lexical matching regardless of embedding quality, and
  a token-overlap score over a few hundred documents is a few lines of JS, not a database
  feature.
- **Metadata columns**: tractate, daf ref (`page.ref`, e.g. `"Gittin 2a"`), segment range,
  classification tier, `is_mishnah_story` flag, source canonical file + its content hash
  (so a search result can cite exactly which dataset version it came from — matters if
  the corpus is still growing while people are already searching it).
- **No structured sage/entity field exists yet** — `criteria.identifiable_characters.
  evidence` is free text (e.g. `"a certain man, agents"`), not a linked name. MVP relies on
  names appearing literally in the text and hitting the lexical arm. Entity extraction as
  a first-class filter is a real Phase-2 idea, not in this plan — don't build it
  speculatively before knowing whether hybrid search already handles named-sage queries
  well enough (that's exactly what the test set below checks).

## Pipeline

1. **Freeze the input contract** — one function, `classification != NOT_A_STORY` →
   indexable, badge `mishnah_stories`, tag confidence tier. Write it once, test it against
   the counts table above so a future canonical-file change can't silently change what
   "indexable" means without the test noticing.
2. **Build the flattened corpus** — one deterministic script,
   `results/canonical/*.json` → `results/search_index/story_corpus_v1.json`. Every row
   traceable back to (tractate, page ref, segment range).
3. **Embed** — batch call to `gemini-embedding-001`, cached by content hash so a rerun
   after a corpus change only re-embeds what changed. Whole corpus is under $1 one-time.
4. **Build the static index file** — embeddings + metadata + tokenized Hebrew/English text,
   one JSON artifact, committed like every other generated asset this project ships.
5. **Client-side hybrid search** — cosine similarity + keyword score, fused by reciprocal
   rank fusion, filtered by tractate/tier/mishnah-flag. Runs in the visitor's browser;
   ~50-100 lines of vanilla JS, no backend, no per-query cost, nothing to keep running.
6. **Minimal UI** — bilingual result display, story text highlighted. This is the same
   requirement Critical Rule 1 already puts on every validation UI in this project; a
   public search surface shouldn't be held to a lower bar than an internal review page.
   Reuse `validation/generators/review_ui_core.py`'s shared display core rather than
   building a third bilingual renderer.
7. **Testing gate** — below. Nothing ships past this point without it. Storage-agnostic:
   the qrels harness scores whatever the query layer returns, whether it's a SQL query or
   a JS function.
8. **Publish** — to GitHub Pages, same as the existing site.

## Testing — built in, not bolted on at the end

Same discipline as the golden datasets: blind queries, expert judgments, a held-out set,
scored by a harness nobody hand-tunes against.

- **Query set**: 30-40 queries. Jeff writes his **blind** — before seeing any search
  output, so he can't unconsciously pick queries the system already handles. A second,
  non-expert writer (Simon, or a grad student) covers the vaguer phrasing an actual "anyone
  can search" user would type. Categories: thematic, named-sage, Hebrew
  phrase/idiom, narrative type, cross-tractate, and at least a few **negative controls**
  (something that shouldn't retrieve anything confident) — that last category is the only
  way to catch a system that returns confident garbage instead of "nothing found."
- **Dev/test split fixed at authoring time.** Tune embedding concatenation, hybrid
  weights, and reranking only against the dev queries. The test queries aren't looked at
  until final scoring — this is Rule 2 (no examples from the pages being evaluated),
  relabeled for retrieval instead of detection.
- **Relevance judgments (qrels)**: pool the top ~15 results from 2-3 candidate configs
  (vector-only / hybrid / hybrid+rerank) per query, Jeff marks the pooled set relevant or
  not. ~30 queries × ~25-30 pooled results is a couple of focused sessions, not an
  open-ended ask of his time.
- **Metrics**: Recall@20 as the headline (a researcher is hurt more by a missed story than
  by three extra ones), NDCG@10 for ranking quality, MRR on the named-sage/phrase queries
  specifically.
- **Harness**: `scripts/score_retrieval.py`, immutable once it exists — same rule as
  `evaluate_golden.py`. Always run with an explicit output path; never let it overwrite
  the qrels file it's scoring against.
- **Gate**: genuinely undefined right now, same as Publication's gate in
  `docs/capabilities/6_publication.md`. Don't pre-commit to a number with no data behind
  it (Lesson 18) — run the first dev-set pass, look at where real failures cluster, then
  agree a bar with Jeff. The number belongs in a findings doc when it exists, not in this
  plan.
- **Sanity checks per phase**, not just at the end: Phase 2 output row count matches
  Phase 1 input count exactly; a known near-duplicate pair of stories retrieves each other
  as nearest neighbors (cheap smoke test that the embedding call is actually working
  before spending Jeff's time on the real query set).

## Cost

- Embeddings: **under $1**, one-time, cents to re-embed after a corpus change.
- Hosting: **$0/month, indefinitely** — GitHub Pages, same as the existing site. Nothing
  runs, nothing to renew, nothing that goes down because a bill lapsed after the grant
  that's funding this ends.
- Jeff's time: **1-2 sessions** to write and judge queries.

**Rejected alternative, for the record:** Cloud SQL + Cloud Run, ~$10-90/month depending
on tier (shared-core vs. dedicated-core — see git history on this doc for the full
breakdown). Dropped once the actual data volume made a running server obviously the wrong
tool. Written down so a later session doesn't have to rediscover this.

## Future work items (not created — copy `work/_TEMPLATE.md` when starting each)

Split so they can run concurrently without colliding on `writes:` — the corpus-build and
query-set items touch disjoint paths and don't block each other:

1. Build flattened corpus + contract tests (`writes: results/search_index/`,
   `scripts/build_story_index_corpus.py`)
2. Embedding generation + content-hash cache (`writes: results/search_index/embeddings/`,
   `scripts/embed_story_corpus.py`)
3. Static index file builder — embeddings + metadata + tokenized text → one JSON artifact
   (needs 1 and 2 done first — `blocked_by`)
4. Client-side hybrid search module — cosine + keyword + RRF fusion, vanilla JS, no
   backend (needs 3)
5. Query set + `score_retrieval.py` harness — **no shared `writes` with 1-4**, can start
   immediately and run in parallel
6. Minimal UI, reusing `review_ui_core.py`
