// feedbackEndpoint: the deployed worker URL (worker/README.md). Empty = fall back to a pre-filled GitHub issue.
// showDraftNotes: true shows unreviewed AI-drafted notes to everyone. Keep false; reviewers add ?notes=draft to the URL instead.
window.SEPTIMUS_CONFIG = window.SEPTIMUS_CONFIG || { feedbackEndpoint: "https://septimus-feedback-oumost3ajq-uc.a.run.app", repo: "siguy/talmud-stories-feedback", showDraftNotes: false,
  // readingWpm: reading speed for story minutes ("study pace"). scripts/build_site_data.py reads it from here.
  readingWpm: 150,
  // firebase: public web config for project septimus-stories (Spark, no billing). Not a secret; access is set by
  // Firestore security rules and the authorised-domain list (docs/technical/septimus-signup-plan.md section 8).
  firebase: {
    apiKey: "AIzaSyB37--NXCHCEorUX5S0gWiz56_vkrEgw4c",
    authDomain: "septimus-stories.firebaseapp.com",
    projectId: "septimus-stories",
    storageBucket: "septimus-stories.firebasestorage.app",
    messagingSenderId: "833890592463",
    appId: "1:833890592463:web:e788e740dd532c3ea9f9ba"
  },
  // signup: settings for the sign-up pages (signup.js). Empty values show a [placeholder] on the page.
  signup: {
    wpm: 75,                    // reading pace for the weekly hand-out (plan section 4). Not readingWpm.
    launchDate: "",             // ISO date of the Monday everyone starts, e.g. "2026-12-07". Empty = not set yet (asked Daniel).
    yahrzeit: "2027-09-10",     // 8 Elul 5787; to confirm with Daniel
    yahrzeitLabel: "8 Elul",
    maxMinutes: 120,
    contactEmail: "",           // shown under the sign-in button for people without a Google account. Empty = placeholder.
    communities: ["hadar", "dn", "kesher"]    // allowed ?src= values; placeholder list until Daniel confirms
  }
};
// Staging: the copy of the site at talmud-stories-staging.vercel.app uses its own Firebase project, so test
// sign-ups and test runs of the weekly script never touch real people's records. Also public, not a secret.
if (/^talmud-stories-staging[a-z0-9-]*\.vercel\.app$/.test(location.hostname)) {
  window.SEPTIMUS_CONFIG.staging = true;
  window.SEPTIMUS_CONFIG.firebase = {
    apiKey: "AIzaSyBbTAAbLf7l6O8hIzG4RiqsNgkTtJ-8znk",
    authDomain: "septimus-stories-staging.firebaseapp.com",
    projectId: "septimus-stories-staging",
    storageBucket: "septimus-stories-staging.firebasestorage.app",
    messagingSenderId: "83308377990",
    appId: "1:83308377990:web:299bc891f9d11cc80dde07"
  };
}
