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

**Their default is `gemini-2.0-flash`, which Google no longer serves, so running one
fails.** That is the accepted cost, confirmed 2026-09-04, and NOT a bug to fix: repointing
them would make them run under a model that produced none of their numbers, which is worse
than not running at all. If you need to reproduce an old result, pass `--model` explicitly
and record that you did -- the result is then attributable to the model you chose, not
silently to whichever one the file happened to name.
"""
import os

# MEASURED 2026-09-14 -- the experiment the comment below used to say was unrun. Same 20
# Yevamot dapim, 36 of Jeff's blind stories, the detection prompt verified byte-identical
# to the 2026-09-03 shipped run, no rate limiting, one run each (the runs are
# deterministic at this temperature; spread 0.0 over three repeats, same day):
#
#   gemini-3-flash-preview, thinking off    83.3%   1 empty page    0 truncations
#   gemini-3.8-flash,       thinking off    75.0%   0 empty        4 truncations
#   gemini-3.8-flash,       thinking high   27.8%   9 empty of 20  14 truncations
#
# The third row was this file's default. At thinking=high the model spends its output
# budget thinking and returns JSON cut off mid-object; the run prints "0 candidates, 0
# stories" and completes. Raising max_output_tokens to 32768 does not prevent it. 3.8
# with thinking off is simply stricter -- it drops borderline stories Jeff's list carries.
# Every number the board quotes was produced by the first row.
#
# -> docs/findings/2026-09-14-default-model-measured.md
DEFAULT_MODEL = "gemini-3-flash-preview"

# None means thinking OFF (`_call_google` sets thinking_budget=0). That is what the
# 2026-09-03 Yevamot run and every shipped run before it used; run_meta records
# thinking_level: null on each. An EMPTY env value also means off -- a dotfile with
# `GEMINI_THINKING_LEVEL=` must not silently become `high`.
DEFAULT_THINKING_LEVEL = None


def default_model() -> str:
    """The model to use when the caller has not chosen one. `GEMINI_MODEL` overrides."""
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


def default_thinking_level():
    """Reasoning effort when the caller has not chosen one; None is off.

    `GEMINI_THINKING_LEVEL` wins when set to a value. Set-but-empty is off, not the
    default: that is how a dotfile says "no".
    """
    value = os.getenv("GEMINI_THINKING_LEVEL")
    return value if value else DEFAULT_THINKING_LEVEL


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
