"""The model default is a provenance fact, so it is pinned rather than trusted.

Before 2026-09-03 four live entry points carried four different literal defaults and
`GEMINI_MODEL` was not set in `.env`. Anything that forgot `--model` fell back to
`gemini-2.0-flash`, which Google stopped serving in mid-2026 -- a silent wrong-model run,
which is the one failure this project cannot detect after the fact.
"""
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.model_config import DEFAULT_MODEL, default_model  # noqa: E402

LIVE_ENTRY_POINTS = [
    "src/story_detector_v11.py",
    "src/event_triage.py",
    "scripts/run_clause_labeling.py",
    "scripts/run_parallel_rule_experiment.py",
    "scripts/run_wave5_clause_spans.py",
    "scripts/measure_speech_act_blast_radius.py",
]

# v5-v10 are historical artifacts. Their literals are what they RAN with, and repointing
# them would rewrite the provenance of every number they produced.
FROZEN = [f"src/story_detector_v{n}.py" for n in (5, 6, 7, 8, 9, 10)]


def test_default_is_the_current_model():
    assert DEFAULT_MODEL == "gemini-3.8-flash"


def test_env_var_still_wins(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3-flash-preview")
    assert default_model() == "gemini-3-flash-preview"
    monkeypatch.delenv("GEMINI_MODEL")
    assert default_model() == DEFAULT_MODEL


def test_the_live_detector_and_triager_agree():
    """Detection and triage must not run on different models in one pipeline."""
    from src.event_triage import EventTriager
    from src.story_detector_v11 import V7StoryDetector
    os.environ.pop("GEMINI_MODEL", None)
    assert EventTriager(api_key="x").model_name == DEFAULT_MODEL
    assert V7StoryDetector(api_key="x").model_name == DEFAULT_MODEL


# A DEFAULT literal is the bug. A capability check -- `'gemini-3' in model_name`, or the
# THINKING_REQUIRED_MODELS set -- names a model on purpose and must stay.
_DEFAULT_LITERAL = re.compile(
    r"""(?:getenv\(\s*["']GEMINI_MODEL["']\s*,\s*|default\s*=\s*|model_name\s*=\s*)"""
    r"""["'](gemini-[0-9][^"']*)["']""")


@pytest.mark.parametrize("path", LIVE_ENTRY_POINTS)
def test_no_live_entry_point_hardcodes_a_default(path):
    """Four of these drifted to four different values, and nothing noticed."""
    hits = _DEFAULT_LITERAL.findall((ROOT / path).read_text())
    assert hits == [], f"{path} hardcodes default {hits}; use default_model()"


def test_the_default_is_recognised_as_a_thinking_model():
    """`gemini-3.8-flash` must satisfy the substring checks that gate thinking_level,
    or every call silently loses its thinking config."""
    from src.story_detector_v11 import _supports_thinking_level
    assert _supports_thinking_level(DEFAULT_MODEL)


@pytest.mark.parametrize("path", FROZEN)
def test_frozen_versions_keep_their_own_literal(path):
    """The other half of the rule: repointing these rewrites history silently."""
    src = (ROOT / path).read_text()
    assert "from src.model_config import" not in src, (
        f"{path} is frozen -- it must keep the literal it ran with")


def test_thinking_level_has_a_default():
    """Unset used to mean thinking OFF -- `_call_google`'s json_mode branch falls through
    to thinking_budget=0 under a comment written for 2.x flash. Nothing said so."""
    from src.model_config import DEFAULT_THINKING_LEVEL, default_thinking_level
    os.environ.pop("GEMINI_THINKING_LEVEL", None)
    assert DEFAULT_THINKING_LEVEL == "high"
    assert default_thinking_level() == "high"


def test_thinking_env_var_wins(monkeypatch):
    from src.model_config import default_thinking_level
    monkeypatch.setenv("GEMINI_THINKING_LEVEL", "low")
    assert default_thinking_level() == "low"


def test_detector_and_triager_agree_on_thinking():
    """They must not reason at different depths inside one pipeline."""
    from src.event_triage import EventTriager
    from src.story_detector_v11 import V7StoryDetector
    os.environ.pop("GEMINI_THINKING_LEVEL", None)
    assert EventTriager(api_key="x").thinking_level == "high"
    assert V7StoryDetector(api_key="x").thinking_level == "high"


def test_thinking_budget_is_large_enough_for_the_thinking():
    """The regression this nearly shipped with.

    Thinking tokens are drawn from max_output_tokens. At 8192 -- sized for 3.7-flash --
    gemini-3.8-flash at HIGH spent 7,867 on thinking and returned MAX_TOKENS with 321
    tokens of truncated JSON. Both call sites must raise the budget to 32768.
    """
    for path in ("src/story_detector_v11.py", "src/event_triage.py"):
        src = (ROOT / path).read_text()
        i = src.index("thinking_level=self.thinking_level.upper()")
        window = src[i:i + 600]
        assert "32768" in window, f"{path}: thinking branch does not raise the budget"


@pytest.mark.parametrize("path", ["scripts/run_new_tractate.py",
                                  "scripts/run_wave5_clause_spans.py",
                                  "scripts/run_clause_labeling.py",
                                  "scripts/run_parallel_rule_experiment.py"])
def test_run_scripts_share_one_thinking_default(path):
    """Two of these defaulted to 'high' and two to None -- i.e. off -- including the one
    that runs a whole tractate."""
    src = (ROOT / path).read_text()
    assert "default=default_thinking_level()" in src, f"{path} sets its own --thinking default"
