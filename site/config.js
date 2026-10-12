// feedbackEndpoint: the deployed worker URL (worker/README.md). Empty = fall back to a pre-filled GitHub issue.
// showDraftNotes: true shows unreviewed AI-drafted notes to everyone. Keep false; reviewers add ?notes=draft to the URL instead.
window.SEPTIMUS_CONFIG = window.SEPTIMUS_CONFIG || { feedbackEndpoint: "", repo: "siguy/talmud-stories", showDraftNotes: false };
