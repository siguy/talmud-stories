# Sign-up launch checklist

Everything between today and real people signing up. Written 2026-11-15. Tick items here as they are done; this is
the one list. Background: [`septimus-signup-plan.md`](septimus-signup-plan.md),
[`septimus-staging.md`](septimus-staging.md), work item `work/2026-11-08-septimus-signup.md`.

**Where things stand:** steps b, c and d and the simplified flow are on `main` (#101) and running on staging, where a real Google sign-in and a nine-week test of the weekly script have worked. Nothing is
on the real site.

## 1. Decisions from Simon

- [x] Should someone who learned once and then stopped reading also be paused? **Yes** (2026-11-15), built.
- [ ] Look at the built screens on staging, especially those that had no mockup: stop / delete / cancel deletion,
      paused / resume, "How the stories were chosen", "Your data", the in-app-browser notice.
- [ ] Confirm the seven builder's choices in [`signup-c-review-2026-11-15.md`](signup-c-review-2026-11-15.md).
- [x] Email service and sending domain: **Resend**, sending from `projects.simonbrief.com` (Simon, 2026-11-15; as
      reported by the email session, which says the domain is verified and the secret `RESEND_API_KEY` is set).
- [ ] The contact address shown as "No Google account? Email …".
- [ ] The final site address, if it will not be `talmud-stories.vercel.app`.

## 2. From Daniel (follow-up drafted 2026-11-16: `comms/drafts/2026-11-16-daniel-followup-email.md`)

Simon, 2026-11-16: only two things need Daniel; the rest we decide and he can change later.

- [ ] **When the learning starts** (a Sunday).
- [ ] **A few paragraphs about his father** for the About page.
- [ ] He tries the staging link and says what feels wrong.

Decided without him (changeable): finishing = going through Shas together, again and again; the weekly email
comes from `talmud-stories@projects.simonbrief.com`; 75 words a minute; yahrzeit Friday 10 September 2027 (asked
him to correct it if wrong); community links are added as communities are named.

## 3. Unblocked 2026-11-15: the Jeff-responses branch merged (#96; 1,811 stories, permanent ids)

Main is merged into all five sign-up branches; staging runs the new list.

- [x] Step s, first half: a test checks the story-data fields the sign-up reads.
- [ ] Step s, second half (with freezing the list at launch): list version, publish date and Shas order in the data.
- [x] Clean-ups: the reader's old "read" feature deleted at the source; two links fixed; version numbers bumped.
- [x] Resolve the one expected merge conflict (the plan document).
- [x] My stories and the learned list follow `site/data/redirects.json` when a story's id was merged into another.

## 4. Still to build

- [x] **Step e, the weekly email** (merged 2026-11-16, pull request #105; notes:
      [`signup-e-email-2026-11-15.md`](signup-e-email-2026-11-15.md)): "Your stories this week", a short "nothing new"
      email, one-click unsubscribe, a link that marks a story learned without signing in, the "still with us?" email
      for paused people. Tested with one real send to Simon and, on staging, the unsubscribe and mark-learned clicks.
      **Full weekly run on staging with email on, 2026-11-16:** with a test start date (the workflow's
      "launch_date" box, staging only) the job handed out week 17, paused two test accounts, sent one weekly email
      (to Simon; the test accounts' made-up addresses were skipped) and the counts email; a second run sent nothing.
      Simon confirmed both emails arrived.
- [x] **The weekly counts email to Simon** (the alarm if a week is missed): built with step e; sent after each
      hand-out to the address in the secret `SEPTIMUS_COUNTS_TO`.
- [ ] Script: remove a sign-up record whose Google account no longer exists (found in the d review).
- [ ] Script: delete everyone's personal data six months after the yahrzeit.
- [ ] About Joe Septimus page: put in Daniel's text.
- [ ] **Rewrite "How the stories were chosen"** (Simon, 2026-11-17): more about what was done and the rules a
      story must meet; more about Prof. Jeff Rubenstein's background; a little about Simon. Draft the wording for
      Simon to approve before it goes on the site; check every fact about Jeff against a source.
- [ ] Freeze the story list (ids and order) as list v1.

## 5. Testing still needed (all on staging)

- [x] One real Google sign-in, Join, and a record written.
- [x] One real run of the weekly script; a second run changes nothing.
- [ ] Simon: walk the three flow changes on staging (links under the title; front page is My stories when signed
      in; "Mark as learned" on a story that is yours).
- [ ] **A real iPhone and a real Android phone:** sign in, Join, mark a story learned.
- [x] **A link opened from WhatsApp** (Simon, 2026-11-16: worked). Gmail and Instagram not tried**:** the "open in your browser" notice appears and
      "Copy link" works.
- [x] **Several weeks, several people:** four or five test accounts, the script run for pretend weeks 1 to 8
      (`--date`), checking that an unread story is handed back at week 4 and goes to someone else, a non-reader is
      paused at week 7, Resume works, and Stop works.
- [x] **Delete my data, for real:** the account, the record and the name on the rows are all gone after the run.
      This has only ever run against the local test database.
- [ ] **A second person** (not Simon) signs up from their own phone with a community link (`?src=`).
- [ ] **The scheduled workflow on GitHub**, run by hand against staging, before it is trusted with the real one.
- [x] **Many people at once** (300 on staging: under a tenth of the free reads; `septimus-staging.md`)**:** a few hundred pretend sign-ups on staging, to see the real read counts against the
      free limit (simulated only so far: about 21,000 of 50,000 a day at 200 people).
- [ ] The weekly email on a real phone, including unsubscribe (after step e).
- [ ] Dark mode, larger text ("Aa") and a screen reader (VoiceOver) on the new pages.
- [x] The reader still works after the Jeff-responses branch is merged in (checked on staging, signed out).

## 6. Going live: two separate moments

**How it works.** Everything is tried on staging (`./scripts/deploy_staging.sh`, any branch). The real site only ever
gets what is on `main` (`./scripts/deploy_prod.sh`, which refuses anything else). Nothing moves between the two
databases: staging's accounts are test accounts and stay there; real people sign up on the real site.

**Moment 1: open sign-ups** (can happen before the start date is known; nobody is handed stories yet).

- [x] Merge the sign-up work into `main` (2026-11-16, one pull request, #101; #97 to #100 closed as included).
- [x] The real site's address is on the live project's authorised sign-in domains (checked 2026-11-17:
      `talmud-stories.vercel.app`).
- [ ] Restrict the public web key in the Google Cloud console to Firebase and the site's addresses.
- [x] **The real site already runs the sign-up** (found 2026-11-17): a production deploy on 2026-11-17, about
      04:23 UTC, put everything on `main` live, so `talmud-stories.vercel.app` opens on the join page and anyone can
      sign up. Not done from this session. The live database held 0 sign-ups when checked. Simon to decide: leave
      it, or roll the real site back until launch.
- [ ] Sign up once yourself on the real site.
- [ ] Share the link (with `?src=` for each community).

**Moment 2: start the learning** (needs the start date, and the email finished).

- [ ] Put the start date (a Sunday) in `site/config.js`; freeze the story list as list v1; deploy.
- [ ] Create the live service-account key; store it as the GitHub secret `FIREBASE_SERVICE_ACCOUNT`; delete the
      downloaded file.
- [x] Merge the email work (done 2026-11-16, pull request #105).
- [ ] **Deploy `firestore.rules` to the live project** (`firebase deploy --only firestore:rules --project
      septimus-stories`). The merge did not do this. The rules add two openings for the email's unsubscribe and
      mark-learned links; until they are live, those links are refused on the real site. Staging already has them.
- [ ] Set the repository variable `SEPTIMUS_SITE_URL` to the real site's address (the email's links are built
      from it). Already set: `SEPTIMUS_EMAIL_FROM`, `SEPTIMUS_SITE_URL_STAGING`, and the secrets `RESEND_API_KEY`
      and `SEPTIMUS_COUNTS_TO`.
- [ ] Resend: move to the paid plan before the first Sunday with more than 100 people (the free plan stops at
      100 emails a day; anyone over the limit is emailed by the next daily run instead).
- [ ] Run the job once by hand as a dry run (Actions → Septimus weekly → Run workflow).
- [ ] Set the repository variable `SEPTIMUS_WEEKLY_ENABLED` to `true`. The first Sunday run hands out and emails.

## Parked on purpose (Simon, 2026-11-15: keep the site as simple as possible)

- Sample stories or a visual on the front page.
- "Give me another story" for people who want more (agreed; after launch).
- Marking your stories inside the tractate lists; "Next story" on the story page.

- Updating the separate Talmud stories page on the simonbrief.com hub (Simon, 2026-11-17: consider it, not yet).

## 7. After launch

- [ ] Each Sunday: the counts email arrived and the numbers look sane.
- [ ] GitHub switches a scheduled workflow off after 60 days with no activity in the repository: check it is still on.
- [ ] Watch sign-ups against the free database limit; decide about the paid plan if they near 500 people.
