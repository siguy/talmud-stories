# Plan: the reader feedback loop (2026-11-15)

**Owner:** Simon. **Status:** plan only, nothing built. Drafted by a Fable planning agent, 2026-11-15.
**Question it answers (Simon):** "We DEFINITELY need to use this. How could we use this to improve results?"

## In one paragraph

Every story page has a "Report a problem" form. Today a report becomes a GitHub issue in the
private repo `siguy/talmud-stories-feedback`, and then nothing happens to it. This plan adds
the missing half: once a week a script reads the open reports, sorts them, and each kind of
report goes to a fixing tool we already have. Every report ends with a recorded outcome. The
outcomes pile up into a set of "reader cases" that we use to check whether a change to the
detector or the note writer made things better or worse, and to find rule questions worth
asking Jeff.

## Three rules this plan never breaks

1. **A reader's report is a tip, not a verdict.** It is "suspected" until Simon confirms it
   ("indicated"). Only Jeff's ruling is expert evidence. Reader reports never enter
   `results/canonical/*` and are never used as few-shot examples.
2. **Every fix from a report is display-only**: `site/data/boundary_extensions.json`,
   `results/shas_run/septimus_site_decisions.json`, and the notes files. Goldens, detector
   runs and story ids are untouched.
3. **Nothing is silently dropped.** A report the script cannot read is counted and named
   (Lesson 21). Reader text is data: it is never treated as an instruction, even when it is
   placed in front of a drafting or review agent.

## What exists today (checked 2026-11-15)

- Form: `site/app.js` (`feedbackMarkup`, `wireFeedback`). Categories: hebrew, translation,
  not_story, boundary, other. A reader can report on the whole story or flag one passage.
- Endpoint: `worker/feedback-worker.js`, deployed on Google Cloud Run (`site/config.js`
  `feedbackEndpoint`). It files an issue labelled `story-feedback` and `tractate:<name>`
  with a JSON block.
- Proof it works: issue #3, a test on Avodah Zarah on 2026-11-15, after the redeploy that
  opened the form to all 37 tractates.
- **4 issues so far, all ours.** #1-#3 are closed tests. **#4 is open, came from staging through
  the fallback link, and has no labels** — a label filter would never see it.
- **No GitHub Actions workflow is involved in feedback**, in any repo: the path is browser ->
  Cloud Run -> GitHub REST API -> issue. Abuse limits already in place include
  `--max-instances 2` (`worker/gcp/deploy.sh`).
- **The main repo `siguy/talmud-stories` is PUBLIC; the feedback repo is private.** Anything this
  plan writes into the main repo is public.
- Fixing tools: `scripts/review_site_boundaries.py` (trim / extend / merge),
  `septimus_site_decisions.json` (`remove`, `keep`, `merge`), `scripts/draft_site_notes.py`
  + `build_site_notes.py` + `approve_notes.py`, `results/site_notes/held.json`.
- Expert channel: `comms/JEFF.md` (question queue), `docs/STORY_RULES.md` (rule register).

## Gaps found

| Gap | Why it matters |
|---|---|
| No "background note" category | The note says "Spot a mistake? Use Report a problem", but a note mistake can only be sent as "Something else" |
| A report does not say which note version or boundary the reader saw | By the time we read it the note may be redrafted or the boundary moved; we cannot tell if it is already fixed |
| `review_site_boundaries.py export` only reads the drafters' flag list | There is no way to send it one reader-reported story |
| No rate limit on the endpoint | A script could file many issues; honeypot, size caps and the 2-instance cap are the only defence |
| Staging reports fail the endpoint's origin check and fall back into the real queue | `deploy.sh` allows only `https://talmud-stories.vercel.app`; issue #4 came from `talmud-stories-staging.vercel.app` |
| The "Send via GitHub instead" fallback is a dead end for readers | The feedback repo is private, so anyone but Simon gets a 404 |
| Fallback reports bypass the worker's checks | Their JSON is built in the browser; triage must re-check id, category and caps itself |
| Half-migrated and dead pieces (see Phase 0) | Cloudflare instructions in `worker/README.md` (pointing at the public repo), stale comments, orphaned workflows |
| The reader never hears back | Reports are anonymous and readers cannot see the private repo |
| "Send via GitHub instead" issues have a different, sometimes cut-off body | The triage script must read both shapes |
| ~~Boundary tool's text says "4 forward", its code allows 6~~ | Fixed 2026-11-15: 6 is the rule (Simon: "make the changes you see fit"); the worker comment still says 4 |

---

## Phase 0. Bookkeeping and cleanup (before any work)

**Cleanup (Simon: "we may need to clean all of this up").**
- [ ] `worker/README.md`: delete the Cloudflare section (it tells you to set `REPO = siguy/talmud-stories`,
      the public repo). `worker/feedback-worker.js`: fix the "Cloudflare Worker" header and the stale
      "end_forward <= 4" comment (the rule is 6).
- [ ] Disable the orphaned GitHub workflows: "Septimus email test" (its branch is gone) and
      `pages-build-deployment` (failing since September; Pages is off). `gh workflow disable`, with Simon's yes.
- [ ] `septimus-weekly.yml` (the sign-up weekly hand-out) lives on five `septimus/*` branches and never on
      main, so it has never run. Not part of this plan: name it to Simon as the sign-up work's decision.
- [ ] Staging: see D10.
- [ ] Fallback: see D11.

- [ ] Read `STATE.md`, `STATUS.md`, and `docs/capabilities/` for publication and review.
- [ ] Copy `work/_TEMPLATE.md` to `work/2026-11-15-reader-feedback-loop.md`. Fill `writes:`
      generously: `site/app.js`, `worker/`, `scripts/feedback_triage.py`,
      `scripts/review_site_boundaries.py`, `results/site_feedback/`,
      `results/site_notes/held.json`, `results/shas_run/septimus_site_decisions.json`,
      `site/data/boundary_extensions.json`, `site/data/notes/`, `tests/`.
- [ ] Run `python3 scripts/board.py lanes`. This item shares files with the notes and
      boundary work, so it cannot run beside them. The full boundary review
      (`docs/history/2026-11-15-PLAN-full-boundary-review.md`) owns `scripts/review_site_boundaries.py`;
      the boundary route below waits for it to merge.

## Phase 1. Intake: make each report carry what triage needs

**1a. Confirm the path end to end (10 minutes, Simon or Claude with Simon's yes).**
- [ ] On the live site, send one whole-story report and one passage report on a story in a
      tractate added in November. Mark both "TEST, please close".
- [ ] Check both appear in the feedback repo with labels `story-feedback` and `tractate:<name>`.
- [ ] Send one from a phone. Most readers are on phones.
- [ ] Break it on purpose once (airplane mode): the fallback must appear, and it must be the
      reader-usable one decided in D11 (not a link to a private repo).
- [ ] Check the address the family actually opens matches the worker's allowed origin
      (`worker/README.md`, "Redeploying"). A preview address or custom domain fails silently
      with "did not send".

**1b. Add what is missing to the form and the worker.**
- [ ] **Test first:** there is no test that the app's and the worker's category lists agree
      (`feedback-worker.test.mjs` hardcodes 4). Write one that parses `CATS` from `site/app.js` and
      `CATEGORIES` from the worker and asserts they are equal; then add the category.
- [ ] New category `note`: "The background note is wrong". Put it in `site/app.js` (`CATS`)
      and `worker/feedback-worker.js` (`CATEGORIES`).
- [ ] Add to the payload, and to the worker's copied-and-capped field list:
  - `span` (the segments shown right now) and `extended` (was the boundary already adjusted)
  - `note_drafted` and `note_approved` (the note's existing `drafted` stamp and approval; empty if none)
  - `site`: `prod` or `staging` (from the page address), and `test: true` when the reporter ticks a
    hidden-to-readers test box or the comment starts with "TEST" — tests never become reader cases
  - nothing else. The detector grade stays out (Simon 2026-11-14); triage looks it up by id.
- [ ] Do **not** add sign-in identity in this step (see Decisions, D6).
- [ ] Redeploy the worker (`worker/gcp/deploy.sh`, needs Simon's Google login) and the site.
      The service address does not change.

**1c. Spam and abuse (keep it light until there is a problem).**
- Already in place: hidden honeypot field, every field capped, story id must match the id
  pattern, GitHub token limited to Issues on the one private repo, site not indexed by
  search engines.
- Already done: the Cloud Run service is capped at 2 instances (`deploy.sh`).
- [ ] Add: triage marks junk with a `spam` label and closes it; duplicates collapse (Phase 2).
- [ ] Only if abused: a per-address limit in `worker/gcp/server.js` (a few per minute).
- Token expires 2027-10-15. Put a reminder in the calendar now.

**Done when:** a test report of each of the 6 categories arrives as an issue carrying story
id, passage (if flagged), category, span, note version, site and the test flag.

## Phase 2. Triage: one script, one ledger

New file `scripts/feedback_triage.py`. It reads; it changes nothing on the site.

    python3 scripts/feedback_triage.py pull      # read open issues, write the queue
    python3 scripts/feedback_triage.py report    # print the weekly list for Simon
    python3 scripts/feedback_triage.py close --issue 12 --outcome fixed --what "..."   # Phase 4

What `pull` does (logs to `project.log` with the count at each step, per Simon's standard):
- [ ] Reads **every** open issue in the feedback repo, with **no label filter**:
      `gh issue list -R siguy/talmud-stories-feedback --state open --limit 500 --json number,title,body,createdAt,labels`.
      Fallback issues arrive unlabelled (#4 today); a label filter would drop them silently.
- [ ] Sorts each issue into **worker report / fallback report / unreadable**, and counts and names
      each group. An issue it cannot read is listed under "could not read"; it is never skipped.
- [ ] Re-checks every report against the worker's own rules (story id pattern, known category,
      field caps), **from one shared definition** rather than a copy, because fallback reports
      never passed through the worker.
- [ ] Tags (never drops) reports from staging and reports flagged as tests.
- [ ] Follows `site/data/redirects.json`, so a report on a story since merged lands on the
      story that now holds it.
- [ ] Looks up the story's state today: detector grade, `reviewed` (Jeff-validated
      tractate or not), whether it is in `keep` / `remove` / `merge`, whether its boundary is
      already adjusted, whether its note is held, approved, or redrafted since the report.
- [ ] Marks "may already be fixed" when the span or note version in the report differs from
      today's.
- [ ] De-duplicates: same story + same category + same passage = one item with a count. The
      count is shown, but one careful report is not outvoted by silence and five identical
      reports are not proof.
- [ ] Writes `results/site_feedback/queue.json` and appends new issues to
      `results/site_feedback/ledger.json`.

**The ledger** is the durable record: one entry per issue with the report, the outcome, who
decided, what changed, the commit, the date. **Because the main repo is public, the full ledger
(reader comments, names) lives in the private feedback repo**, committed there by the script.
The main repo gets only a scrubbed `results/site_feedback/outcomes.json`: issue number, story id,
category, outcome, date and who decided — **no comment text, no names**. `queue.json` (which
quotes comments) is written to a git-ignored local folder, never committed.

What `report` prints: counts by category and by tractate, then one line per story,
grouped as: act now / needs Simon / route elsewhere / could not read.

## Phase 3. What each kind of report triggers, and who approves

| Report | What it triggers | Tool (already exists) | Who approves |
|---|---|---|---|
| **boundary** | A boundary review of that one story | `review_site_boundaries.py` -> `boundary_extensions.json` or a `merge` | Simon's standing rules (trim to the narrative; extend a little; merge two halves). Simon sees the before/after list. In a Jeff-reviewed tractate the same rule as the full boundary review applies (its Decision 1): display-only changes allowed, and any trim that cuts a segment Jeff listed goes to Simon |
| **not_story** | A candidate removal | `septimus_site_decisions.json` -> `remove` | **Simon, always.** Jeff only if it exposes a rule question |
| **note** | Pull the note and redraft it | add to `held.json` -> `draft_site_notes.py` -> `build_site_notes.py` -> `approve_notes.py --ids` | Simon spot-checks the redraft (or a standing rule, D2) |
| **hebrew / translation** | Check whose mistake it is; usually Sefaria's | none of ours, see below | Simon decides whether we forward it |
| **other** | Claude reads it and re-files it as one of the above, or as a site bug | n/a | n/a |

**Boundary, step by step**
- [ ] **Waits for the full boundary review to merge**: that work owns `review_site_boundaries.py`
      and adds `--flags <file>` (default `passage_flags.json`) and `apply` marking changed notes
      for redraft. Until then, boundary reports are queued, not acted on. Triage writes
      `results/site_feedback/boundary_flags.json` in the same `{id: concern}` shape, where the
      concern is the reader's comment, capped and marked as a reader's words.
- [ ] Run export -> review -> import -> apply -> `build_site_data.py`, exactly as for the
      drafters' flags.
- [ ] A changed boundary can make the note stale. Add those ids to the note redraft list.
- [ ] If the story is in `keep`, or the reviewer says "leave it", the outcome is "no change"
      with the reason.

**Not a story, step by step**
- [ ] If the story is in the `keep` list: Simon already looked. Outcome "kept", unless the
      reader gives a reason Simon has not seen. (The build refuses a `remove` that overlaps
      a `keep`, on purpose.)
- [ ] If Jeff called it a story: no removal. Record the disagreement. It is a data point
      about how readers see that kind of story, not a fix.
- [ ] Otherwise: get a second opinion from the two existing judges (the same twin-pass
      used for the unreviewed tractates). Show Simon one screen per case: the text, the
      reader's words, both judge verdicts, and the rule in `docs/STORY_RULES.md` it turns on.
- [ ] Simon says remove -> one `remove` entry with `decided_by: "Simon <date>, reader
      report #N"`. Simon says keep -> a `keep` entry, so it is not raised again.
- [ ] If no rule in `STORY_RULES.md` settles it, it becomes a candidate question for Jeff
      (Phase 5), not an ad-hoc email.

**Note mistake, step by step**
- [ ] Add the story id to `results/site_notes/held.json` with the reason "reader report #N:
      <their words>". A held note is off the site at the next build, which is the right
      reflex for a note a reader says is wrong.
- [ ] Redraft with `draft_site_notes.py export --ids-file` -> import -> `build_site_notes.py`
      (a held note takes the new draft whole; this already works and is tested).
- [ ] Claude checks the redraft against the reader's point. If the redraft repeats the
      mistake, it stays held and goes to Simon.
- [ ] `approve_notes.py --ids ...` once approved.
- [ ] A wrong one-line summary (the card text) arrives as "other". The fix is
      `results/shas_run/site_summaries_written.json`.

**Hebrew / translation, step by step**
The text is Sefaria's; we display it.
- [ ] Compare the passage text inside the report with a fresh copy from Sefaria.
  - Different -> our copy is stale or our display mangled it (lost formatting, Hebrew and
    English out of step). That is our bug: refetch or fix the build.
  - Same -> it is in Sefaria's text. Reply "this is Sefaria's text", label `sefaria`, and
    add it to a short list.
- [ ] Once a month Simon decides whether to send the list to Sefaria through their own
      corrections channel (confirm the address before first use). We never edit the text
      ourselves.
- [ ] "The English is unclear" is often not an error. If a term is the problem, the fix is a
      "Words to know" entry: send it down the note path.

## Phase 4. Closing the loop

- [ ] `feedback_triage.py close` writes the outcome to the ledger, comments on the issue in
      plain words ("Fixed: the story now ends after Rav Ahai's verdict", or "No change: ..."),
      adds one outcome label, and closes it. Labels: `fixed`, `no-change`, `duplicate`,
      `sefaria`, `asked-jeff`, `spam`.
- [ ] An issue waiting on Jeff stays open with `asked-jeff` and the question's slug.
- [ ] **Changelog:** generated from the ledger, never hand-written:
      `docs/site-feedback-log.md` (date, story, category, what changed). It is public, so it never
      quotes a reader or names one.
- [ ] The reader cannot see any of this (anonymous form, private repo). If Simon wants
      readers to see it, the same ledger can feed a small "Recently fixed, thanks to
      readers" list on the site, first names only and only with consent (D5).

**Done when:** no `story-feedback` issue is open for more than two weeks without an outcome
or an `asked-jeff` label.

## Phase 5. Improving RESULTS, not just patching

Patching fixes one story. These five uses make the next run better.

**5a. The reader-case set.** Built from the ledger and kept in the **private** feedback repo
(it carries the readers' claims); the main repo gets only ids and outcomes. One row per resolved report: story, kind, what the reader claimed, the outcome
(confirmed / rejected / unclear), and **who confirmed it** (Simon, the judges, or Jeff).
- It is a **held-out** set: never shown to the detector or note writer as examples
  (Critical Rule 2).
- It is labelled plainly as a biased sample: readers only see stories we shipped, so it can
  measure false positives and boundary errors, **never missed stories**. People report what
  annoys them, not a random sample.
- Only "confirmed" rows count in any measurement, and the report always says how many were
  Simon-confirmed and how many Jeff-ruled.

**5b. A regression check for detector changes.** Before a new detector, judge or boundary
version replaces what the site ships, run `scripts/score_reader_cases.py` (new, small):
- Of the confirmed not-a-story cases, how many does the new version still ship?
- Of the confirmed boundary fixes, how many does it now get right unaided (its span against
  the span we settled on)?
- Reported as **counts**, never folded into the composite score (Critical Rule 5), and
  beside the golden numbers, not instead of them. `evaluate_golden.py` is not touched.

**5c. A regression check for the note writer.** Every confirmed note mistake is a test case.
- Sort confirmed mistakes by type (wrong person, wrong term, misread plot, says more than
  the text does).
- A type that recurs becomes either a check in `build_site_notes.py` (which already holds
  notes that fail a check) or a line in the next note prompt.
- Before a new prompt version ships, redraft the reported stories with it and count how many
  of the old mistakes are gone.

**5d. Where is the site weakest?** From the ledger, monthly: confirmed problems per
tractate, per detector grade, and per inclusion route (for example the `promote` batch,
which can be removed in one step). A batch with a high confirmed not-a-story rate is a
case for tightening that route. Also compare with the drafters' flags: when a reader
reports a boundary the drafter did not flag, that is a miss by the flagging step.

**5e. Rule questions for Jeff.** When three or more confirmed reports share a pattern that
`docs/STORY_RULES.md` does not settle, write **one** question in `comms/JEFF.md` with a
slug, the cases, and the Hebrew openings, and send it in his next regular batch. Never
forward raw reader reports to him. His answer becomes a rule in `STORY_RULES.md` through the
normal route. That, not the reader's report, is what may change the detector prompt. This
is also the working prototype of the open question `jeff:deliverable-shape` (a corpus with a
feedback channel).

## Phase 6. Cadence, cost, who does what

**Weekly, about 15 minutes of Simon's time.** Suggested: Sunday, the site's week start.

| Step | Who |
|---|---|
| Pull, parse, de-duplicate, look up state, print the list | Automatic: a **local** scheduled task on Simon's Mac, or a workflow in the **private** feedback repo that prints counts only. **Never** a GitHub Action in the public main repo: its logs are public and would show reader text |
| Sefaria comparison for text reports | Automatic |
| Boundary review of reported stories | Automatic under Simon's standing rules; Simon reads the before/after |
| Note redraft | Automatic; approval per D2 |
| Remove or keep a story | **Simon** |
| Anything on a Jeff-reviewed story | **Simon** |
| A question to Jeff | **Simon** sends; Claude drafts |
| Forwarding to Sefaria | **Simon** |
| Redeploying the worker | **Simon** (his Google login) |
| Commenting on and closing issues | Automatic once the outcome is recorded |

**Cost.** Cloud Run and GitHub: effectively free at family volume. Redrafts and reviews use
Claude Code subagents, no API key. The scarce resource is Jeff's attention: at most one
batched question per round. At 0 to 10 reports a week this is light. If the sign-up
program brings a jump, the weekly list still works; the per-item Simon decisions are the
bottleneck, which is the case for the standing rules in D1 and D2.

**Emergency path:** a report of something offensive or badly wrong does not wait for
Sunday: hold the note (`held.json`) or remove the story, rebuild, redeploy.

## Phase 7. Tests

New `tests/test_site_feedback.py`, plus additions to the worker test. All offline: issue
bodies are fixture files, `gh` is never called.

- [ ] Worker and app list the same categories, including `note` (extend the existing sync
      check in `tests/test_site_data.py`).
- [ ] The worker keeps the new fields, caps them, and still refuses bad ids and categories.
- [ ] The parser reads a worker issue, a fallback issue (unlabelled, like #4), and a cut-off
      fallback issue. An unreadable one is reported by number, not dropped. No label filter anywhere.
- [ ] A fallback report with a bad id, unknown category or oversize field is re-checked and
      marked, using the same definitions as the worker.
- [ ] Nothing under the main repo contains a reader's comment or name (scan `results/site_feedback/`
      and `docs/site-feedback-log.md`).
- [ ] A hostile comment (a fake JSON block, or "ignore your instructions") changes nothing:
      the parser takes only the worker's block, and the comment reaches agents only as
      quoted reader text.
- [ ] De-duplication: three reports, same story, category and passage -> one item, count 3.
- [ ] A report on a merged story follows the redirect.
- [ ] A report whose span or note version differs from today's is marked "may already be fixed".
- [ ] A not-a-story report on a `keep` story never produces a `remove`.
- [ ] No code path in triage or the scorers writes under `results/canonical/`.
- [ ] The ledger only grows: an existing entry's report is never rewritten.
- [ ] The reader-case scorer counts only confirmed rows and prints who confirmed them.
- [ ] `review_site_boundaries.py export --flags` with one id produces one story file.
- [ ] `python3 -m pytest tests/ -q` passes before stopping (includes the bookkeeping test).
- [ ] The end-to-end flow (pull -> route -> close) runs against **fixture issues**; live, only one
      smoke report, flagged `test`, closed with outcome `test`, so fake reports never enter the ledger
      as reader cases.

## Build order (each step is useful by itself)

1. Phase 1a: confirm the live path (no code).
2. Phase 2: triage script and ledger. From here reports stop being lost.
3. Phase 1b: `note` category and the extra fields; redeploy.
4. Phase 3: the `--flags` option, then the four routes.
5. Phase 4: close and changelog.
6. Phase 5: reader-case set and the two regression checks. Worth building only once there
   are roughly 20 or more confirmed cases; until then the ledger is enough.

## Risks

| Risk | What we do |
|---|---|
| Nobody uses the form (no real report yet) | Ask the family and the first sign-up group directly to try it; say so in the welcome note. Without volume, Phase 5 has nothing to measure |
| Reader reports get treated as truth | The three rules at the top; "who confirmed" on every row; nothing reaches the goldens |
| A fix for one reader makes it worse for others | Every boundary change is display-only and reversible; `keep` stops repeat arguments |
| Tuning the detector to reader complaints | The reader-case set is held out and only a check; prompt changes come from Jeff's rules |
| The set only shows false positives, so "improvement" could mean finding fewer stories | Always report it beside recall on the goldens; never by itself |
| Reader text steering an agent | Comments are capped, quoted as reader words, and never executed as instructions |
| Spam or a flood | Honeypot, caps, instance cap, `spam` label; rate limit if needed |
| Names in reports | Full ledger only in the private repo; the public repo holds ids and outcomes; a test enforces it |
| Staging reports polluting the real queue | Tagged by `site`, reported separately (D10) |
| Worker token expires (2027-10-15) or origin mismatch | Calendar reminder; the fallback link; Phase 1a check after any address change |
| Overloading Jeff | One batched question per round, three confirmed cases minimum |
| Collision with other open work on the same files | `writes:` in the work item and `board.py lanes` |

## Decisions for Simon

- **D1. Boundary fixes from readers:** apply automatically under your existing rules and show
  you the before/after list (recommended), or wait for your yes on each one?
- **D2. Redrafted notes:** approve automatically when the redraft passes the checks and
  addresses the reader's point (recommended, with a monthly spot check by you), or your yes on each?
- **D3. Stories in Jeff-reviewed tractates:** agree that a reader report can change how we
  display them only with your yes, and never changes Jeff's label?
- **D4. Sefaria text problems:** should we forward confirmed ones to Sefaria monthly, or just
  tell the reader it is Sefaria's text?
- **D5. Telling readers:** a small "Recently fixed, thanks to readers" list on the site? If
  yes, with first names when given, or no names?
- **D6. Signed-in readers:** when someone is signed in, attach their account to the report so
  we can reply and spot repeat reporters? It helps the loop but stores who said what; today
  the form is anonymous unless they type a name.
- **D7. "A story is missing":** readers cannot report this today, and it is the one thing the
  reader-case set cannot measure. Add a simple site-wide link for it later? (Not in this plan.)
- **D8. Extension limit:** settled 2026-11-15: 6 segments forward (Simon: "make the changes you see fit").
- **D10. Staging reports:** allow the staging site as a second origin and tag its reports `site: staging`
  (recommended), or give staging its own endpoint and feedback repo?
- **D11. The fallback when the endpoint fails:** today it links to a private repo, a 404 for readers.
  Replace it with a "copy this report" box plus a mailto link to an address you choose (recommended),
  or keep it, labelled as working for you only?
- **D12. Where triage runs:** a local scheduled task on your Mac (recommended: simplest, nothing
  public), or a workflow in the private feedback repo?
- **D9. Cadence:** weekly on Sunday, with you giving about 15 minutes. OK?

## Plan Review — 2026-11-15
VERDICT: READY (after the changes below; it was FIX FIRST)
Mode: code
Biggest risk: reports silently skipped (label filter) and reader text committed to the public main repo. Both fixed in Phase 2.
False premises: "all 3 issues are tests" (there are 4; #4 is open and unlabelled); "fallback issues carry the label" (they don't); "the fallback works for readers" (private repo, 404); "cap Cloud Run instances" (already done); "extend the existing sync check" (none exists); "the ledger is private" (the main repo is public); `note_run` (no such field).
Accepted changes:
- `pull` reads every open issue, no label filter; worker / fallback / unreadable counted and named.
- Full ledger and reader cases in the private feedback repo; main repo keeps ids and outcomes only, with a test.
- Fallback reports re-checked against the worker's rules from one shared definition.
- Phase 0 cleanup: Cloudflare docs, stale comments, orphaned workflows; staging (D10) and fallback (D11) decided before 1a.
- Triage never runs as a GitHub Action in the public repo (D12).
- New app/worker category sync test written before adding `note`; `note_drafted` instead of `note_run`; `site` and `test` flags at intake; end-to-end on fixtures.
- Boundary route waits for the full boundary review to merge (shared file); Jeff-tractate rule made consistent with that plan.
Deferred / NOT in scope: Phase 5 until ~20 confirmed cases; the Sefaria monthly list; D5; `septimus-weekly.yml` (sign-up work's decision).
Open questions: D1-D7, D9-D12, asked first by the executing session.
