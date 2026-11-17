# Step e, the weekly email: what is built and what is not (2026-11-15)

Branch `septimus/signup-e-email`, cut from `septimus/signup-flow`. Built in a separate session so the sign-up
build could carry on; this note is for whoever merges it.

## Decided by Simon, 2026-11-15

- Email service: **Resend**.
- Sending domain: **projects.simonbrief.com**, for staging now (it can stay for launch). Verified in Resend on
  2026-10-19; the SPF, DKIM and DMARC records are live at GoDaddy (DMARC is in report-only mode, `p=none`).
- From-address: **talmud-stories@projects.simonbrief.com**. The sender *name* still waits for Daniel.
- The GitHub secret `RESEND_API_KEY` is set on the repository.

## Built

- `scripts/septimus_email.py`: the three emails (weekly, "still with us?", counts to Simon) and the sending.
- `scripts/septimus_weekly.py`: step 5 calls it after the hand-out and the summary are saved; four new `Store`
  methods (`claim_sent`, `unclaim_sent`, `sent_keys`, `contacts`) plus `mark_emails_done`; "delete my data" now
  also removes the person's `sent/` records.
- `.github/workflows/septimus-weekly.yml`: the email settings, and a "send_email" box for runs started by hand.
- `tests/test_septimus_email.py`: 21 tests, no network.
- Preview without sending: `python3 scripts/septimus_email.py --preview /tmp/weekly.html`. A phone-width
  picture of it is in `signup-screens/5-weekly-email-built.png`.

How a double send is prevented: `sent/<week>_<uid>` is created before each send (create fails if it exists) and
the same key goes to Resend as its Idempotency-Key. Resend clearly refusing an email removes the record, so the
next daily run retries; a timeout or server error keeps it, so that email is never retried.

## Unsubscribe and "Mark as learned" without signing in (built 2026-11-16)

Simon chose where the click lands (2026-11-16): **on the Vercel site, with no stored password**, over a separate
Cloud Run service holding a database key.

How it works:

- Each person has a **private code**, `users/<uid>.mailToken`, made by the script the first time it emails them
  and never changed, so links in old emails keep working.
- Every weekly and "still with us?" email carries the code in three places:
  1. the standard one-click headers (`List-Unsubscribe`, `List-Unsubscribe-Post`), which put an Unsubscribe
     button in the mail program itself. They point at `site/api/unsubscribe.js`, a small Vercel function;
  2. a footer link to `site/unsubscribe.html`, a confirm page with an Undo;
  3. a "Mark as learned" link under each story, to `site/learned.html`, also a confirm page.
- Nothing changes on a plain visit, only on a button press (or the mail program's own POST), because mail
  scanners open links.
- The function and the pages hold **no key**. They write to Firestore as a signed-out visitor, and
  `firestore.rules` has two narrow new openings (marked `EMAIL LINK`): with the right code, switch `emailOff`
  on or off, or tick that person's story once. Nothing else, and no reading.
- Unsubscribing stops email only (`users/<uid>.emailOff: true`); it is not leaving. The send step skips those people.
- A week with nothing new still gets a short email when the person holds open stories.

Worth a reviewer's eye: the two rule openings. Anyone holding a person's email can unsubscribe them or tick
their stories; that is what such a link is. The code is 32 random characters, is never logged, and opens
nothing else. `mailTokenUsed` (a copy of the code) is written next to the change because a rule can only check
what is being written.

Tested: 33 new rule tests and 4 new Store tests in the emulators; 6 Node tests for the function; and on
staging, with a throwaway record, the one-click POST, both pages' buttons in a browser, and wrong codes refused.

## Not built

1. **Sender name and Daniel's line** in the dedication. The dedication reads "In memory of Joe Septimus." for now.
2. **Turning emails back on from My stories.** Today the way back is the Undo on the unsubscribe page, or any
   later use of the same link. A switch on My stories would need `site/signup.js` and one more rule.
3. **Hard bounces.** The script does not track them. To check: whether Resend stops sending to an address that
   hard-bounced on its own.

## To switch it on

Repository variables: `SEPTIMUS_EMAIL_FROM`, `SEPTIMUS_SITE_URL`, `SEPTIMUS_SITE_URL_STAGING`.
Repository secret: `SEPTIMUS_COUNTS_TO` (Simon's address).
Then run the workflow by hand with "staging" and "send_email" ticked and "dry_run" unticked: on staging only the
counts address can be emailed. (GitHub only offers "Run workflow" once the workflow file is on `main`.)

Set on 2026-11-15: `SEPTIMUS_EMAIL_FROM`, `SEPTIMUS_SITE_URL_STAGING`, `SEPTIMUS_COUNTS_TO`. Still to set: the
live `SEPTIMUS_SITE_URL`.

**Test send, 2026-11-15:** `python scripts/septimus_email.py --test-send` ran once in a GitHub Action on a
throwaway branch (since deleted) and Resend reported the sample weekly email as delivered to Simon, who confirmed it
looks right. Not yet done: a full staging run of the job with email on (GitHub offers "Run workflow" only
once the workflow file is on `main`).

**The rules tests need Java.** This Mac had none, so `tests/test_firestore_rules.py` had been skipping here.
`brew install openjdk` was run on 2026-11-16; put `/opt/homebrew/opt/openjdk/bin` on the PATH to run them.
`firestore.rules` from this branch is deployed to **staging only**. The live rules are unchanged.

Resend's free plan stops at 100 emails a day. A Sunday with more people than that needs the paid plan; if the
limit is hit, the rest are sent by the next daily run.
