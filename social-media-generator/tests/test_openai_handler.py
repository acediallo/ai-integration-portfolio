"""
Tests for OpenAIHandler.

All OpenAI API calls are mocked; no network requests are performed.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import config
from src.openai_handler import OpenAIError, OpenAIHandler


@pytest.fixture
def handler(monkeypatch: pytest.MonkeyPatch) -> OpenAIHandler:
    """Create an OpenAIHandler with a mocked client."""
    # Patch the OpenAI constructor used inside OpenAIHandler to avoid real SDK usage.
    mocked_openai_client = MagicMock()
    mocked_openai_client.chat.completions.create = MagicMock()

    def _mock_openai_ctor(*_args, **_kwargs):
        return mocked_openai_client

    monkeypatch.setattr("src.openai_handler.OpenAI", _mock_openai_ctor)
    return OpenAIHandler(api_key="test-key", model="gpt-4o-mini")


def _mock_response(content: str, prompt_tokens: int, completion_tokens: int):
    """Build a minimal OpenAI response-like object."""
    total_tokens = prompt_tokens + completion_tokens
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        ),
    )


def test_init_valid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Create handler with valid key; assert client initialized."""
    monkeypatch.setattr("src.openai_handler.OpenAI", lambda **_kwargs: MagicMock())
    h = OpenAIHandler(api_key="test-key", model="gpt-4o-mini")
    assert h.client is not None


def test_init_empty_key() -> None:
    """Try empty API key; assert raises ValueError."""
    with pytest.raises(ValueError, match="API key is required"):
        OpenAIHandler(api_key="")


def test_calculate_cost(handler: OpenAIHandler) -> None:
    """Assert cost calculated correctly using config per-1K constants."""
    cost = handler.calculate_cost(prompt_tokens=1000, completion_tokens=500)
    expected = round(
        (1000 / 1000.0) * config.INPUT_COST_PER_1K_TOKENS
        + (500 / 1000.0) * config.OUTPUT_COST_PER_1K_TOKENS,
        6,
    )
    assert cost == expected


def test_generate_post_success(handler: OpenAIHandler) -> None:
    """Mock successful OpenAI response; assert structured dict and cost."""
    handler.client.chat.completions.create.return_value = _mock_response(
        content="Hello world",
        prompt_tokens=10,
        completion_tokens=20,
    )
    result = handler.generate_post("Test prompt", max_tokens=50, temperature=0.1)
    assert result["content"] == "Hello world"
    assert result["prompt_tokens"] == 10
    assert result["completion_tokens"] == 20
    assert result["total_tokens"] == 30
    assert result["model"] == "gpt-4o-mini"
    assert isinstance(result["cost"], float)


def test_generate_post_retry_then_success(
    handler: OpenAIHandler, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mock: 1st call fails, 2nd succeeds; assert retries once."""
    monkeypatch.setattr("src.openai_handler.time.sleep", lambda *_args, **_kwargs: None)

    handler.client.chat.completions.create.side_effect = [
        OpenAIError("transient failure"),
        _mock_response("Recovered", 5, 5),
    ]
    result = handler.generate_post("Prompt")
    assert result["content"] == "Recovered"
    assert handler.client.chat.completions.create.call_count == 2


def test_generate_post_max_retries_exceeded(
    handler: OpenAIHandler, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mock: all 3 attempts fail; assert raises OpenAIError after 3 tries."""
    monkeypatch.setattr("src.openai_handler.time.sleep", lambda *_args, **_kwargs: None)
    handler.client.chat.completions.create.side_effect = OpenAIError("persistent failure")

    with pytest.raises(OpenAIError):
        handler.generate_post("Prompt")
    assert handler.client.chat.completions.create.call_count == 3


def test_generate_variations(handler: OpenAIHandler) -> None:
    """Mock successful responses; assert list of 3 dicts with variation number."""
    handler.client.chat.completions.create.side_effect = [
        _mock_response("V1", 1, 1),
        _mock_response("V2", 1, 1),
        _mock_response("V3", 1, 1),
    ]
    results = handler.generate_variations("Prompt", num_variations=3, max_tokens=20)
    assert len(results) == 3
    assert results[0]["variation"] == 1
    assert results[1]["variation"] == 2
    assert results[2]["variation"] == 3

