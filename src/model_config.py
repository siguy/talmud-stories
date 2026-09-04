"""One place that names the model, so a run's provenance is a fact and not a habit.

Every Gemini-calling entry point used to carry its own literal default, and they had
drifted to four different values -- `gemini-2.0-flash` (deprecated by Google in mid-2026
and no longer served), `gemini-2.5-flash`, `gemini-3-flash-preview`, `gemini-3.7-flash`.
`GEMINI_MODEL` is not set in `.env`, so anything that forgot to pass `--model` on the
command line silently fell back to whichever literal that file happened to hold.

`GEMINI_MODEL` still wins when set. This only fixes what happens when it is not.

FROZEN VERSIONS ARE DELIBERATELY NOT IMPORTED HERE. `src/story_detector_v5.py` through
`v10.py` keep their own literals so that reading them tells you what they ran with. They
are historical artifacts; a shared constant would silently re-point them.
"""
import os

# Verified against the live model list 2026-09-03, and exercised with the project's own
# call config -- response_mime_type='application/json' plus thinking_level LOW and HIGH,
# both returning parseable JSON.
DEFAULT_MODEL = "gemini-3.8-flash"


def default_model() -> str:
    """The model to use when the caller has not chosen one. `GEMINI_MODEL` overrides."""
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
