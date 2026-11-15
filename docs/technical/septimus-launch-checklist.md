# Sign-up launch checklist

Everything between today and real people signing up. Written 2026-11-15. Tick items here as they are done; this is
the one list. Background: [`septimus-signup-plan.md`](septimus-signup-plan.md),
[`septimus-staging.md`](septimus-staging.md), work item `work/2026-11-08-septimus-signup.md`.

**Where things stand:** steps b, c and d and the simplified flow are built (draft pull requests #97 to #101) and
running on staging, where a real Google sign-in and a nine-week test of the weekly script have worked. Nothing is
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

## 2. Answers from Daniel (asked 2026-11-13, no reply yet)

- [ ] What "finishing" means (built on rounds of Shas meanwhile).
- [ ] Launch date (must be a Sunday: stories and the email go out Sunday morning).
- [ ] Yahrzeit date: Friday 10 September 2027?
- [ ] Weekly email: whose name it comes from, and any wording.
- [ ] Reading pace feels right (75 words a minute).
- [ ] The list of communities and what each is called.
- [ ] A few paragraphs about his father for the About page.

## 3. Unblocked 2026-11-15: the Jeff-responses branch merged (#96; 1,811 stories, permanent ids)

Main is merged into all five sign-up branches; staging runs the new list.

- [x] Step s, first half: a test checks the story-data fields the sign-up reads.
- [ ] Step s, second half (with freezing the list at launch): list version, publish date and Shas order in the data.
- [x] Clean-ups: the reader's old "read" feature deleted at the source; two links fixed; version numbers bumped.
- [x] Resolve the one expected merge conflict (the plan document).
- [x] My stories and the learned list follow `site/data/redirects.json` when a story's id was merged into another.

## 4. Still to build

- [ ] **Step e, the weekly email** (being built in a separate session, on its own branch cut from
      `septimus/signup-flow`; it adds a module and a small hook in `scripts/septimus_weekly.py` and the workflow)**:** "Your stories this week", one-click unsubscribe, a link that marks a story
      learned without signing in, the "still with us?" email for paused people.
- [ ] **The weekly counts email to Simon** (the alarm if a week is missed).
- [ ] Script: remove a sign-up record whose Google account no longer exists (found in the d review).
- [ ] Script: delete everyone's personal data six months after the yahrzeit.
- [ ] About Joe Septimus page: put in Daniel's text.
- [ ] Freeze the story list (ids and order) as list v1.

## 5. Testing still needed (all on staging)

- [x] One real Google sign-in, Join, and a record written.
- [x] One real run of the weekly script; a second run changes nothing.
- [ ] Simon: walk the three flow changes on staging (links under the title; front page is My stories when signed
      in; "Mark as learned" on a story that is yours).
- [ ] **A real iPhone and a real Android phone:** sign in, Join, mark a story learned.
- [ ] **A link opened inside WhatsApp, Gmail and Instagram:** the "open in your browser" notice appears and
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

## 6. Launch day, in order

- [ ] Merge the pull requests: #97, then #98, #99, #100, #101.
- [ ] Put the launch date, yahrzeit, contact address and communities into `site/config.js`.
- [ ] Add the real site's address to the live project's authorised sign-in domains (exact address only).
- [ ] Restrict the public web key in the Google Cloud console to Firebase and the site's addresses.
- [ ] Email: sending domain records (SPF, DKIM, DMARC) in place and a test send received.
- [ ] Create the live service-account key; store it as the GitHub secret `FIREBASE_SERVICE_ACCOUNT`; delete the
      downloaded file.
- [ ] Deploy the real site. Sign up once yourself.
- [ ] Set the repository variable `SEPTIMUS_WEEKLY_ENABLED` to `true`. Run the workflow once by hand as a dry run.
- [ ] Send the community links.

## Parked on purpose (Simon, 2026-11-15: keep the site as simple as possible)

- Sample stories or a visual on the front page.
- "Give me another story" for people who want more (agreed; after launch).
- Marking your stories inside the tractate lists; "Next story" on the story page.

## 7. After launch

- [ ] Each Sunday: the counts email arrived and the numbers look sane.
- [ ] GitHub switches a scheduled workflow off after 60 days with no activity in the repository: check it is still on.
- [ ] Watch sign-ups against the free database limit; decide about the paid plan if they near 500 people.
