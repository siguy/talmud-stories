# Sign-up plan review, 2026-11-14

Four reviewers (simplicity, architecture, security and privacy, user flows) read
[`septimus-signup-plan.md`](septimus-signup-plan.md) as of commit `b62f25d`. This is the merged list. Nothing here
is applied to the plan yet; "Decision" items wait for Simon.

## A. Two design changes that remove most of the other findings

**A1. Replace the Cloud Function with a Python script on a schedule** (simplicity P1).
`scripts/septimus_weekly.py`, run by a scheduled GitHub Action (and by hand when needed), using the Firebase Admin
SDK. The browser never needs a server; the only server work is the weekly hand-out, the email and the totals.
- Gains: no Blaze plan, no Cloud Functions, no Node, no triggers. Python, as the project prefers.
- Costs: GitHub's scheduler can run late or skip, so the script must detect and report a missed week. A
  service-account key (a real secret) lives in GitHub secrets. Group totals update when the script runs (run it daily
  for totals, weekly for hand-out), not the instant someone taps done; a person's own tick is still instant.

**A2. Work out the pool from the assignment rows; store no pool state** (simplicity P1).
One pure function, `assign_week(story_order, assignments, users, week) -> new rows`. A story is "covered" in round N
if a row for it exists in round N that was not released. Each person gets the first uncovered stories in list order.
- Removes `pool/state`, the pointer, the released queue, and every special case in plan §7 for added or removed
  stories: they fall out of "first uncovered in order".
- Tested with plain pytest on a fixture; the emulator is needed only for the access rules.
- Dissolves architecture findings 1, 4, 6 and part of 5 (transaction locking, undetectable "added behind the pointer",
  the released array's shape, the vanished pointer id).

## B. Decisions for Simon (recommended default first)

1. **Server:** adopt A1 and A2? *Recommend yes.*
2. **Order through Shas:** the site's tractate order starts with Ketubot (the reviewed tractates first), not Berakhot.
   "In order through Shas" needs one fixed order, frozen in the list version. *Recommend the traditional order,
   starting at Berakhot.*
3. **A story longer than someone's weekly minutes** (longest is about 36 minutes at 75 wpm; a budget can be 5):
   *recommend assigning it anyway, labelled "longer than usual"; that person gets nothing new until it is read or
   released.* Alternative: give long stories only to people with large budgets.
4. **Leaving:** the plan has no way to leave and says nothing is ever deleted. *Recommend "Stop my stories" (releases
   open stories at once) and "Delete my data" (removes the account and name/email, keeps anonymous totals), and a
   date after the yahrzeit when personal data is deleted.*
5. **What people are told before sign-in:** one line is not enough. *Recommend a short linked note: what is stored
   (Google name and email, community link, which stories you read and when), who sees it (Simon; Daniel and the
   family get community counts and names, not reading logs), nothing about a person is public, how to leave.*
6. **People who go quiet:** with a 2-week rollover, someone who never reads gets new stories and emails every two
   weeks for 40 weeks. *Recommend pausing a person after two full rollovers with nothing marked learned, with one
   "still with us?" email.*
7. **No Google account:** *recommend a line under the button, "No Google account? Email [contact]", and add them by
   hand; email-link sign-in later if it comes up often.*
8. **After the yahrzeit:** *recommend no hand-outs after the yahrzeit week; the landing page shows the final total and
   a thank-you; reading stays open.*

## C. Folded in as defaults unless Simon objects

Step b (landing, sign-in, minutes):
- The account record is written when the person taps Join, not at sign-in. Abandoning the question shows it again.
- A "You're in" screen after Join: minutes, start date, Change, Browse the stories. (My stories arrives in step d.)
- After launch, the minutes screen says "Your first stories arrive Monday <date>", not "Everyone starts together".
- A returning signed-in person sees "Signed in, 10 min a week" and a link, not the sign-in button.
- The landing page takes `/`; the tractate list moves to `#/browse`; old story links keep working.
- "[N] people have joined" is written by the script; hidden until it exists.
- `?src=` is kept in the URL and in the browser's storage so it survives the hop out of an in-app browser; checked
  against an allowlist; never shown raw.
- In-app browsers (WhatsApp, Instagram, Gmail): detect, show a big "Copy link" button and one picture of
  "Open in browser". No tricks to force it.
- "Other" minutes: whole number 1 to 120.
- The minutes screen shows the email address and "Not you? Switch account".
- The sign-in popup opens directly from the tap. PR preview sites cannot sign in; accepted.
- Names from Google and `src` are inserted as text, never as HTML (the site builds pages with `innerHTML`).
- Aa control on every new page; 44 px targets; the minutes choice is a labelled radio group.

Access rules (step b):
- A person can write only their own record, only the listed fields: `minutesPerWeek` whole number 1 to 120; `src`
  short, lowercase, set once; `createdAt` set by the server clock, never changed. Name and email are never taken from
  the record: the script reads them from the sign-in system, so nobody can make it email a stranger.
- A person can read and update only their own assignment rows, and only `doneAt`, set to the server time or cleared.
- No listing other people's records. No client deletes.
- The script also caps minutes, because the rules are not the only guard.
- `firestore.rules` and `firebase.json` go in the repo. **Before anything else: confirm in the Firebase console that
  the live database currently denies everything** (no rules file exists in the repo today, so its state is unknown).

Step c (weekly hand-out):
- One record per week (`runs/<campaign week>`), created so a second run for the same week does nothing; each
  assignment row has a fixed id `<week>_<uid>_<storyId>`.
- Weeks are campaign week numbers (1 to about 40), not calendar week numbers (the campaign crosses a New Year, and
  2026 has 53 calendar weeks).
- Rollover boundary: assigned in week W, still open in W+1 and W+2, released by the W+3 run.
- A release re-checks that the story was not marked learned in the meantime.
- Reading time is computed from `words` at the script's own 75 wpm. The data's `minutes` field is at 150 wpm and is
  not used.
- "Learned" for group progress = distinct stories with at least one done mark in the current round.
- A round is complete when every story on its list has a done mark; the progress page shows "N stories still open in
  round 2". The round records its list version and size when it starts.
- No hand-outs while the launch date is unset or in the future.
- A new person joining mid-week waits for the next Monday run.
- The script's tests use a fixture copy of the story data, not live `site/data` (another branch is editing it).
- The script emails Simon its counts each run (new sign-ups, total minutes, stories handed out) and honours a pause
  flag.

Plan hygiene:
- Delete or clearly retire §8a (old browser-side claim design, Spark budgets) and fix `firebase/setup.sh` and
  `firebase/LOCAL_CLAUDE_PROMPT.md`, which still say "never link billing" and "no secret exists".
- Drop `meta/list` (duplicates `config.js` and `index.json`) and `assignments.list`. One field for pause
  (`minutesPerWeek: 0`), not two.
- §7a: one test asserting the fields the sign-up uses, instead of a separate schema file.
- §7: defer the v1 to v2 migration until a v2 exists. Keep only: rows hold a story id; an id not in the current list
  shows "no longer on the list". Freeze the list (ids and order) at launch.

## D. For later steps (recorded so they are not lost)

Step d (My stories):
- One "Mark as learned" button when signed in and the story is yours; it also sets the old per-device tick.
  Stories not assigned to you keep the per-device tick only.
- "Back to my stories" and "Next story" on the story page.
- "Saved" only after the write is confirmed; clear messages for offline, popup blocked, popup closed.
- A minutes change takes effect at the next Monday run.

Step e (email):
- A "sent" marker per person per week, written before sending, so a re-run cannot double-send.
- Unsubscribe is the email provider's own, with the standard one-click header; a confirm page, because mail scanners
  open links. Unsubscribe stops email only; it is not leaving.
- A dedicated sending subdomain with SPF, DKIM and DMARC. Stop emailing an address that hard-bounces.
- A week with nothing new still gets a short email ("Nothing new; 2 still open").
- A link in the email that marks a story learned without signing in (people open email on other devices).
- English only. Copy says "each Monday" (it is Sunday evening in Israel).

Owner housekeeping:
- Restrict the browser API key in the Google Cloud console to Firebase APIs and the site's addresses.
- Authorised sign-in domains: exact hosts only, never a `vercel.app` wildcard.
- Exports of names and emails live in a restricted Sheet, not email attachments, and are deleted afterwards.
- Under-13s and readers outside the US: collecting little and offering deletion covers it; add "13 or older" to the note.

## E. Not adopting

- App Check and rate limiting: not warranted at this size (security reviewer agrees).
- A content-security-policy header: worth doing, but separate from this work.
- Capping long stories by splitting them: a story is the unit.

## F. What the reviewers could not check

The live database rules, authorised domains, API-key restrictions and billing state (console only); how the sign-in
popup behaves on a real iPhone; GitHub's scheduler reliability for this repo; email-provider specifics.
