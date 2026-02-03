"""
Tests for config module.

Verifies environment loading and default values without requiring a real API key.
"""

import pytest

import config


def test_config_loads_module() -> None:
    """Config module can be imported and exposes expected attributes."""
    assert hasattr(config, "MODEL_NAME")
    assert hasattr(config, "OPENAI_API_KEY")
    assert hasattr(config, "DAILY_BUDGET_USD")
    assert hasattr(config, "DATA_DIR")
    assert hasattr(config, "LOGS_DIR")
    assert hasattr(config, "validate_config")
    assert hasattr(config, "setup_logging")


def test_model_name_default() -> None:
    """MODEL_NAME defaults to gpt-4o-mini when not set in env."""
    assert config.MODEL_NAME == "gpt-4o-mini"


def test_daily_budget_default() -> None:
    """DAILY_BUDGET_USD has a numeric default (e.g. 1.0)."""
    assert isinstance(config.DAILY_BUDGET_USD, float)
    assert config.DAILY_BUDGET_USD > 0


def test_validate_config_raises_when_key_missing() -> None:
    """validate_config raises ValueError when OPENAI_API_KEY is empty."""
    import unittest.mock as mock
    with mock.patch.object(config, "OPENAI_API_KEY", ""):
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            config.validate_config()
