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

| piece | choice | why |
|---|---|---|
| Embeddings | **`gemini-embedding-001`**, called through the `google-genai` SDK already in `requirements.txt`, with the existing `GOOGLE_API_KEY` | Same client the detector already uses. **No new GCP project, no Vertex AI SDK, no service account** — this is the one piece of the plan that costs zero new infrastructure. |
| Vector + lexical store | **Cloud SQL for Postgres + `pgvector`**, plus a `tsvector` column | 370 vectors (growing toward maybe 800-1,000 with Yevamot/Eruvin) is small enough that brute-force cosine in Postgres is sub-millisecond. One system holds the vector search, the Hebrew/English full-text search, and the SQL filters (tractate, daf, confidence tier) — no second database to keep in sync. |
| API | Cloud Run | Stateless, scales to zero, cents/month at research-project traffic. |
| **Not** Vertex AI Vector Search | — | Built for 10M+ vectors; its always-on index endpoint runs ~$300-700/mo to hold what fits in 5 MB here. Revisit only if the corpus reaches six figures. |

## What gets embedded, per story

- **Embedding text** = `one_sentence_summary` (already in every story object) +
  the joined English text of `page_segments[start_segment : end_segment+1]` — the exact
  join CLAUDE.md already mandates for flattening (`page_segments: page.segments`).
  Concatenating the summary in front biases the vector toward the *point* of the story,
  not just its vocabulary — cheap to do since the summary is already computed, no new LLM
  pass required.
- **Hebrew text** is stored and put in the `tsvector` column for exact-phrase/idiom
  search, not embedded. This isn't a claim that Hebrew embeds worse — it's that idiom and
  proper-noun search wants exact lexical matching regardless of embedding quality, and
  Postgres full-text gives that for free once it's the same row.
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
4. **Load Postgres** — `pgvector` column + `tsvector` column + the metadata columns above.
5. **Hybrid query layer** — vector search + full-text search, fused by reciprocal rank
   fusion, filtered by tractate/tier/mishnah-flag. ~30 lines of SQL, not a new service.
6. **Minimal UI** — bilingual result display, story text highlighted. This is the same
   requirement Critical Rule 1 already puts on every validation UI in this project; a
   public search surface shouldn't be held to a lower bar than an internal review page.
   Reuse `validation/generators/review_ui_core.py`'s shared display core rather than
   building a third bilingual renderer.
7. **Testing gate** — below. Nothing ships past this point without it.
8. **Publish.**

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
- Cloud SQL (smallest tier) + Cloud Run: **~$15-35/month.**
- Jeff's time: **1-2 sessions** to write and judge queries.

## Future work items (not created — copy `work/_TEMPLATE.md` when starting each)

Split so they can run concurrently without colliding on `writes:` — the corpus-build and
query-set items touch disjoint paths and don't block each other:

1. Build flattened corpus + contract tests (`writes: results/search_index/`,
   `scripts/build_story_index_corpus.py`)
2. Embedding generation + content-hash cache (`writes: results/search_index/embeddings/`,
   `scripts/embed_story_corpus.py`)
3. Postgres schema + loader (needs 1 and 2 done first — `blocked_by`)
4. Hybrid query API (needs 3)
5. Query set + `score_retrieval.py` harness — **no shared `writes` with 1-4**, can start
   immediately and run in parallel
6. Minimal UI, reusing `review_ui_core.py`
