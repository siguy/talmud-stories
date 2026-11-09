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
  }
};
