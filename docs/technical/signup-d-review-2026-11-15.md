# Sign-up step d: independent review, 2026-11-15

One Opus reviewer read `septimus/signup-c..septimus/signup-d` (My stories, mark as learned, the Progress page, stop /
delete / resume; all in `site/signup.js` and `site/signup.css`) against
[`septimus-signup-plan.md`](septimus-signup-plan.md) §3, §5 to §7a and §9 row d.

**Security: no findings.** Every database- or Google-derived string reaches the page as text; the My stories query
is filtered on the person's own id, satisfies the rules and needs no index.

| # | Sev | Finding | Outcome |
|---|---|---|---|
| 1 | P2 | After "Delete my data", signing in again before the daily run looked like a normal membership | Fixed: "Your data is being deleted." everywhere, with "Cancel deletion" |
| 2 | P2 | Ticks copied to the reader's per-device list were overwritten by `site/app.js` | Removed; moved to the deferred story-page work (needs `app.js`) |
| 3 | P2 | Each My stories visit read every row the person ever had | Fixed: reads open rows only; the "You have learned N" line is gone |
| 4 | P2 | "This week" meant "my newest rows", not the campaign week; "Week N of M" missing | Fixed: computed from the launch date, as the script does |
| 5 | P2 | Offline, a tap stayed on "Saving…" with no explanation | Fixed: after 8 seconds, "Not saved yet. You seem to be offline; it will save when you reconnect." |
| 6 | P3 | Tractates in home-page order, not Shas order | Fixed: a `SHAS_ORDER` list checked by a test against `scripts/tractates.py`; step s moves it into the data |
| 7 | P3 | Wording that claimed things the system does not do | Fixed (pause, stop, resume, delete, lapse wording) |
| 8 | P3 | The empty tick ring and the dark-scheme tick were too faint | Fixed |
| 9 | P3 | Screen readers could miss status messages; focus lost after confirm steps | Fixed |
| 10 | P3 | Two identical button names for two stories on one daf; progress card numbers hidden from screen readers | Fixed |
| 11 | P3 | One tractate file failing to load blanked the page | Fixed |
| 12 | P3 | "Your data" showed nothing when the record could not be read | Fixed |
| 13 | P3 | A non-number in the summary would print "NaN" | Fixed |
| 14 | P3 | Simplifications | Applied where they fell out |

## Deferred by design (needs `site/app.js`, which the Jeff-responses branch is editing)

- One "Mark as learned" button on the story page for a story that is yours; "Back to my stories"; "Next story".
- Keeping the reader's per-device tick in step with the signed-in tick.

## Known gap for step e

A tab still signed in after its account was deleted can, for up to an hour, re-create a `users` record at Join for an
account that no longer exists. When the script first looks up that person's email and the account is missing, it must
delete the record. Recorded here because the lookup arrives with the email step.

## Built without a mockup (show Simon)

The stop / delete / cancel-deletion controls on "Your data", the paused and stopped notices and "Resume" on My
stories. Plain buttons and notices in the reader's style.
