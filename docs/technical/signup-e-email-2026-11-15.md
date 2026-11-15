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

## Not built (each needs a decision)

1. **One-click unsubscribe.** Resend has no unsubscribe of its own for this kind of email (the plan, section
   8d, assumed it had). The standard header needs a small web address of ours that accepts the click. Until
   that exists, the footer link goes to My stories ("Change my minutes or stop my stories"), and the script
   already skips anyone whose `users` record has `emailOff: true`. Nothing sets that field yet.
2. **The link that marks a story learned without signing in.** Needs the same kind of web address.
3. **Sender name and Daniel's line** in the dedication. The dedication reads "In memory of Joe Septimus." for now.

## To switch it on

Repository variables: `SEPTIMUS_EMAIL_FROM`, `SEPTIMUS_SITE_URL`, `SEPTIMUS_SITE_URL_STAGING`.
Repository secret: `SEPTIMUS_COUNTS_TO` (Simon's address).
Then run the workflow by hand with "staging" and "send_email" ticked and "dry_run" unticked: on staging only the
counts address can be emailed. (GitHub only offers "Run workflow" once the workflow file is on `main`.)

Set on 2026-11-15: `SEPTIMUS_EMAIL_FROM`, `SEPTIMUS_SITE_URL_STAGING`, `SEPTIMUS_COUNTS_TO`. Still to set: the
live `SEPTIMUS_SITE_URL`.

**Test send, 2026-11-15:** `python scripts/septimus_email.py --test-send` ran once in a GitHub Action on a
throwaway branch (since deleted) and Resend reported the sample weekly email as delivered to Simon, who confirmed it
looks right. Not yet done: a full staging run of the job with email on, and running the new `Store`
methods against the Firestore emulator.

Resend's free plan stops at 100 emails a day. A Sunday with more people than that needs the paid plan; if the
limit is hit, the rest are sent by the next daily run.
