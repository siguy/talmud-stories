# Sign-up step b: independent review, 2026-11-15

One Opus reviewer read the diff `septimus/signup-mockups..septimus/signup-b` against
[`septimus-signup-plan.md`](septimus-signup-plan.md) §5, §6 and the §9 b checklist, without the builder's opinion.

**No P1.** The access rules were walked field by field: no signed-in or signed-out client can read or write what the
plan forbids; no HTML injection path (`signup.js` has one constant `innerHTML`, the Google "G"); the emulator and
in-app test switches need `localhost`; `?src=` is allowlisted and never displayed.

| # | Sev | Finding | Outcome |
|---|---|---|---|
| 1 | P2 | Automatic redirects added history entries, so Back looped between `#/` and `#/join` | Fixed: redirects use `location.replace` |
| 2 | P2 | "Switch account" could sign the same Google account straight back in | Fixed: `prompt: "select_account"` |
| 3 | P2 | "Your data" said nobody but you sees your reading record; Simon's export does | Fixed: "Only you and Simon see which stories you read." |
| 4 | P2 | No test caught a loosened update rule (`minutesPerWeek` -1, 10.5, "10"; `deleteRequested` "yes") | Fixed: four tests added, each shown to fail when its clause is removed |
| 5 | P3 | Rules tests skip silently on a Mac with only the Java stub | Fixed: checks `java -version`; `REQUIRE_RULES_TESTS=1` turns a skip into a failure |
| 6 | P3 | A person can mark a row learned after it was released to someone else | **Decided (Simon, 2026-11-15): leave it allowed**; step d drops released rows from My stories |
| 7 | P3 | Account changed in another tab not noticed on the minutes screen | Fixed |
| 8 | P3 | A save finishing after the person left the screen still navigated | Fixed |
| 9 | P3 | Record failed to load: wrong message, no retry | Fixed: "Could not load your sign-up." and Try again |
| 10 | P3 | `#/join`, `#/joined` blank while loading or if the SDK fails | Fixed |
| 11 | P3 | Community link lost when browser storage is blocked | Fixed: falls back to the URL |
| 12 | P3 | After the yahrzeit `#/join` still offered Join | Fixed |
| 13 | P3 | `config.js?v=4` not bumped although the file changed | **Deferred**: the line sits next to one the Jeff-responses branch changes; bump after that merges. Vercel revalidates static files, so the risk is low |
| 14 | P3 | Redundant `hasAll` in the create rule; "← Back" under 44 px | Fixed |

**Decision on 6 (Simon, 2026-11-15).** Marking a story learned stays allowed after the row is released: a late
reader still gets credit, and doubling-up already permits a story being learned twice in a round. Step d must
therefore drop released rows from the My stories list.

Not covered by the review: no automated test of `signup.js`; real Google sign-in (needs the rules deployed and Simon
signing in once).
