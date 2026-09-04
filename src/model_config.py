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

# The same failure one layer down. `thinking_level` was read from GEMINI_THINKING_LEVEL
# with NO default, and an unset value falls through `_call_google`'s json_mode branch to
# `thinking_budget=0` -- thinking explicitly OFF -- under a comment written for 2.x flash.
# The four run scripts disagreed too: run_clause_labeling and run_parallel_rule_experiment
# defaulted to 'high', while run_new_tractate -- the one that runs a whole tractate --
# and run_wave5_clause_spans defaulted to None, i.e. off.
#
# Setting a level makes `_call_google` raise max_output_tokens to 8192, which is the fix
# for the failure measured 2026-08-29: a 2,042-char prompt spent 487 thinking tokens
# against a 512 budget and 72 of 95 stories returned MAX_TOKENS with no JSON.
DEFAULT_THINKING_LEVEL = "high"
# ...and `high` is a CHOICE MADE WITHOUT EVIDENCE. Unset meant thinking off, which was
# clearly nobody's decision, but that does not make `high` right. The experiment that
# would justify it is work/2026-09-03-thinking-level-experiment.md, and it is unrun.
# Stated prediction: the effect, if any, is on precision rather than recall -- thinking
# plausibly helps the model REJECT a legal passage that looks narrative more than it helps
# it NOTICE a story it missed. If that holds, detection wants `high` and triage does not,
# and these two should stop sharing one default.


def default_model() -> str:
    """The model to use when the caller has not chosen one. `GEMINI_MODEL` overrides."""
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


def default_thinking_level() -> str:
    """Reasoning effort when the caller has not chosen one. `GEMINI_THINKING_LEVEL` wins."""
    return os.getenv("GEMINI_THINKING_LEVEL", DEFAULT_THINKING_LEVEL)


def supports_thinking_level(model_name: str) -> bool:
    """Gemini 3.x exposes thinking_level; 2.x only thinking_budget.

    Verified 2026-08-29 against the live model list: gemini-3.7-flash accepts
    thinking_level=HIGH together with response_mime_type='application/json'; re-verified
    2026-09-03 for gemini-3.8-flash at both LOW and HIGH.

    Lives here, not in the detector, because event_triage needs it too and importing the
    detector from the triager is a cycle. It is also a substring match, so a model name
    that fails it does not error -- it silently drops the thinking config, which is why
    tests/test_model_default.py pins the default against it.
    """
    m = (model_name or '').lower()
    return any(tag in m for tag in ('gemini-3', 'gemini-4'))
