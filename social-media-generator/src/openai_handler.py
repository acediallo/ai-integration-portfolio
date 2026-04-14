"""
OpenAI API integration with retries, timeouts, and cost tracking.

This module provides a small wrapper around the OpenAI Python SDK to:
- Send prompts and return structured usage/cost metadata
- Retry transient failures with exponential backoff
- Track estimated USD cost using configured per-1K token pricing
"""

from __future__ import annotations

import logging
import time
import traceback
from typing import Any, Optional

import config

try:
    # OpenAI SDK v1+
    from openai import OpenAI
    from openai import OpenAIError, RateLimitError
except Exception:  # pragma: no cover
    # Allows tests to run with mocks even if the SDK isn't installed in the env.
    OpenAI = object  # type: ignore[assignment]

    class OpenAIError(Exception):
        """Fallback OpenAIError when SDK is unavailable."""

    class RateLimitError(OpenAIError):
        """Fallback RateLimitError when SDK is unavailable."""


logger = logging.getLogger(__name__)


class OpenAIHandler:
    """Manage OpenAI API calls with retries and cost tracking."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        """
        Initialize an OpenAI client wrapper.

        Args:
            api_key: OpenAI API key string.
            model: Model name to use for requests.

        Raises:
            ValueError: If api_key is empty.

        Example:
            >>> handler = OpenAIHandler(api_key="sk-...", model="gpt-4o-mini")
        """
        config.setup_logging()

        normalized_key = (api_key or "").strip()
        if not normalized_key:
            raise ValueError("API key is required (OPENAI_API_KEY is empty).")

        self.api_key = normalized_key
        self.model = model
        self.client = OpenAI(api_key=self.api_key)  # type: ignore[call-arg]

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate estimated cost in USD based on token usage.

        Uses `config.INPUT_COST_PER_1K_TOKENS` and `config.OUTPUT_COST_PER_1K_TOKENS`.

        Args:
            prompt_tokens: Number of prompt/input tokens.
            completion_tokens: Number of completion/output tokens.

        Returns:
            Estimated cost in USD, rounded to 6 decimals.

        Example:
            >>> handler.calculate_cost(prompt_tokens=1000, completion_tokens=500)
            0.00045
        """
        input_cost = (prompt_tokens / 1000.0) * config.INPUT_COST_PER_1K_TOKENS
        output_cost = (completion_tokens / 1000.0) * config.OUTPUT_COST_PER_1K_TOKENS
        return round(input_cost + output_cost, 6)

    def generate_post(
        self, prompt: str, max_tokens: int = 300, temperature: float = 0.7
    ) -> dict[str, Any]:
        """
        Generate a social media post from a prompt using OpenAI.

        Retries up to 3 attempts with exponential backoff (1s, 2s, 4s).
        Rate limits wait 60 seconds before retrying.

        Args:
            prompt: The prompt string to send to the model.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            Dict including generated content, token usage, model name, and cost:
            {
              "content": str,
              "prompt_tokens": int,
              "completion_tokens": int,
              "total_tokens": int,
              "model": str,
              "cost": float
            }

        Raises:
            OpenAIError: After 3 failed attempts for OpenAI-related errors.
            TimeoutError: After 3 failed attempts for timeouts.
            ConnectionError: After 3 failed attempts for connection errors.

        Example:
            >>> result = handler.generate_post(\"Write an Instagram post about tacos\")
            >>> result[\"content\"]
            '...'
        """
        prompt_preview = (prompt or "").replace("\n", " ")[:120]
        last_error: Optional[BaseException] = None

        for attempt in range(1, 4):
            try:
                logger.info(
                    "OpenAI call attempt %d/3 (model=%s, max_tokens=%d): %s...",
                    attempt,
                    self.model,
                    max_tokens,
                    prompt_preview,
                )

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=30,
                )

                content = response.choices[0].message.content  # type: ignore[index]
                usage = getattr(response, "usage", None)
                prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
                completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
                total_tokens = int(getattr(usage, "total_tokens", 0) or 0)
                cost = self.calculate_cost(prompt_tokens, completion_tokens)

                logger.info(
                    "OpenAI success (tokens=%d, cost=$%.6f)", total_tokens, cost
                )

                return {
                    "content": content,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "model": self.model,
                    "cost": cost,
                }

            except RateLimitError as e:
                last_error = e
                logger.error(
                    "Rate limit error on attempt %d/3: %s\n%s",
                    attempt,
                    e,
                    traceback.format_exc(),
                )
                if attempt >= 3:
                    raise
                time.sleep(60)

            except (OpenAIError, TimeoutError, ConnectionError) as e:
                last_error = e
                logger.error(
                    "OpenAI error on attempt %d/3: %s\n%s",
                    attempt,
                    e,
                    traceback.format_exc(),
                )
                if attempt >= 3:
                    raise
                # Exponential backoff: 2^(attempt-1) => 1s, 2s, 4s
                time.sleep(2 ** (attempt - 1))

            except Exception as e:
                # Unexpected errors should still include context and avoid silent failure.
                last_error = e
                logger.error(
                    "Unexpected error on attempt %d/3: %s\n%s",
                    attempt,
                    e,
                    traceback.format_exc(),
                )
                if attempt >= 3:
                    raise
                time.sleep(2 ** (attempt - 1))

        # Defensive: the loop always returns or raises, but keep a clear error if not.
        raise RuntimeError(f"OpenAI call failed after retries: {last_error}")

    def generate_variations(
        self, prompt: str, num_variations: int = 3, max_tokens: int = 300
    ) -> list[dict[str, Any]]:
        """
        Generate multiple variations of a post by calling generate_post repeatedly.

        Args:
            prompt: Prompt to send to the model.
            num_variations: Number of variations to generate.
            max_tokens: Maximum tokens per variation.

        Returns:
            List of dicts, each including a variation number:
            [{"variation": 1, "content": ..., "cost": ...}, ...]

        Example:
            >>> variations = handler.generate_variations(\"Promo post\", num_variations=3)
            >>> variations[0][\"variation\"]
            1
        """
        results: list[dict[str, Any]] = []
        total_cost = 0.0

        for i in range(1, num_variations + 1):
            result = self.generate_post(prompt=prompt, max_tokens=max_tokens)
            result_with_variation = {"variation": i, **result}
            results.append(result_with_variation)
            total_cost += float(result.get("cost", 0.0) or 0.0)

        logger.info(
            "Generated %d variation(s); total estimated cost=$%.6f",
            num_variations,
            round(total_cost, 6),
        )
        return results

