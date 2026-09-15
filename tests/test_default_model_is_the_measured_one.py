"""The default model config must be the one that produced the board's numbers.

Measured 2026-09-14 on 20 Yevamot dapim with an intact prompt: preview/off 83.3%,
3.8/off 75.0%, 3.8/high 27.8% with 9 of 20 pages returning nothing. The last was the
default. This pins the first, and pins that an EMPTY env value means thinking off rather
than falling back to a level.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import model_config  # noqa: E402


def test_default_model_is_the_one_every_shipped_run_used(monkeypatch):
    monkeypatch.delenv('GEMINI_MODEL', raising=False)
    assert model_config.default_model() == 'gemini-3-flash-preview'


def test_default_thinking_is_off(monkeypatch):
    monkeypatch.delenv('GEMINI_THINKING_LEVEL', raising=False)
    assert model_config.default_thinking_level() is None


def test_empty_env_value_means_off_not_default(monkeypatch):
    monkeypatch.setenv('GEMINI_THINKING_LEVEL', '')
    assert model_config.default_thinking_level() is None


def test_env_value_still_wins(monkeypatch):
    monkeypatch.setenv('GEMINI_THINKING_LEVEL', 'low')
    assert model_config.default_thinking_level() == 'low'
    monkeypatch.setenv('GEMINI_MODEL', 'gemini-3.8-flash')
    assert model_config.default_model() == 'gemini-3.8-flash'
