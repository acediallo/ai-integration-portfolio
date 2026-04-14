"""
Automated quality scoring for generated social media posts.

This module provides lightweight, heuristic-based metrics to score a post on a
0-10 scale and generate actionable feedback. It is intentionally simple and
deterministic so it can be used in tests, CI, and UI without external calls.
"""

from __future__ import annotations

import re
from typing import Any


class QualityScorer:
    """
    Automated quality metrics for generated social media posts.

    The scoring system is heuristic-based and optimized for quick validation of
    common social post best practices (CTA, hashtags, emojis, readability).
    """

    def __init__(self) -> None:
        """
        Create a QualityScorer instance.

        No initialization is required; the class is stateless.
        """

    def score_post(self, post_text: str, post_type: str = "general") -> dict[str, Any]:
        """
        Score a social media post and return metrics + feedback.

        Args:
            post_text: The generated post text to score.
            post_type: Reserved for future template-specific scoring adjustments.

        Returns:
            Dict with an overall score (0-10), detailed metrics, and feedback:
            {
              "overall_score": float,
              "metrics": {
                "length_score": float,
                "has_cta": bool,
                "hashtag_count": int,
                "hashtag_score": float,
                "emoji_count": int,
                "emoji_score": float,
                "structure_score": float,
                "food_descriptor_score": float
              },
              "feedback": list[str]
            }

        Example:
            >>> scorer = QualityScorer()
            >>> result = scorer.score_post(\"Visit us today! #food 🍕\")
            >>> result[\"overall_score\"]
            5.0
        """
        _ = post_type  # currently unused; kept to satisfy the public API

        length_score = self._score_length(post_text)
        has_cta = self._has_call_to_action(post_text)
        hashtag_count = self._count_hashtags(post_text)
        hashtag_score = self._score_hashtags(hashtag_count)
        emoji_count = self._count_emojis(post_text)
        emoji_score = self._score_emojis(emoji_count)
        structure_score = self._score_structure(post_text)
        food_descriptor_score = self._score_food_descriptors(post_text)

        metrics: dict[str, Any] = {
            "length_score": float(length_score),
            "has_cta": bool(has_cta),
            "hashtag_count": int(hashtag_count),
            "hashtag_score": float(hashtag_score),
            "emoji_count": int(emoji_count),
            "emoji_score": float(emoji_score),
            "structure_score": float(structure_score),
            "food_descriptor_score": float(food_descriptor_score),
        }

        overall_score = self._calculate_overall_score(metrics)
        feedback = self._generate_feedback(metrics, overall_score)

        return {
            "overall_score": overall_score,
            "metrics": metrics,
            "feedback": feedback,
        }

    def _score_length(self, text: str) -> float:
        """
        Score post length on a 0-10 scale based on word count.

        Target range: 150-250 words => 10 points.
        <100 or >300 words => 0 points.
        Linear scaling between:
        - 100..150 words ramps from 0..10
        - 250..300 words ramps from 10..0

        Args:
            text: Post text.

        Returns:
            Length score from 0 to 10.
        """
        words = self._word_count(text)

        if 150 <= words <= 250:
            return 10.0
        if words < 100 or words > 300:
            return 0.0

        if 100 <= words < 150:
            # Map 100..150 -> 0..10
            return round(((words - 100) / 50.0) * 10.0, 2)

        # 250 < words <= 300
        # Map 250..300 -> 10..0
        return round(((300 - words) / 50.0) * 10.0, 2)

    def _has_call_to_action(self, text: str) -> bool:
        """
        Detect whether the post contains a call-to-action.

        CTA phrases include: visit, order, try, book, call, reserve, come, stop by.
        Matching is case-insensitive.

        Args:
            text: Post text.

        Returns:
            True if any CTA phrase is found, otherwise False.
        """
        cta_phrases = ("visit", "order", "try", "book", "call", "reserve", "come", "stop by")
        lowered = (text or "").lower()
        return any(phrase in lowered for phrase in cta_phrases)

    def _count_hashtags(self, text: str) -> int:
        """
        Count hashtags by counting '#' characters.

        Args:
            text: Post text.

        Returns:
            Number of '#' characters.
        """
        return (text or "").count("#")

    def _score_hashtags(self, count: int) -> float:
        """
        Score hashtag usage on a 0-10 scale.

        - 3-5 hashtags => 10 points
        - 1-2 or 6-7 => 5 points
        - 0 or 8+ => 0 points

        Args:
            count: Number of hashtags.

        Returns:
            Hashtag score from 0 to 10.
        """
        if 3 <= count <= 5:
            return 10.0
        if 1 <= count <= 2 or 6 <= count <= 7:
            return 5.0
        return 0.0

    def _count_emojis(self, text: str) -> int:
        """
        Count emoji characters using a regex heuristic.

        Note:
            Emoji detection is non-trivial; this regex targets common emoji blocks
            and works well for typical food/engagement emojis.

        Args:
            text: Post text.

        Returns:
            Number of emoji characters found.
        """
        if not text:
            return 0

        emoji_pattern = re.compile(
            "["  # common emoji ranges
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F680-\U0001F6FF"  # transport & map
            "\U0001F700-\U0001F77F"  # alchemical symbols
            "\U0001F780-\U0001F7FF"  # geometric extended
            "\U0001F800-\U0001F8FF"  # arrows-c
            "\U0001F900-\U0001F9FF"  # supplemental symbols & pictographs
            "\U0001FA70-\U0001FAFF"  # symbols & pictographs extended-a
            "\u2600-\u26FF"  # misc symbols
            "\u2700-\u27BF"  # dingbats
            "]+",
            flags=re.UNICODE,
        )
        matches = emoji_pattern.findall(text)
        return sum(len(m) for m in matches)

    def _score_emojis(self, count: int) -> float:
        """
        Score emoji usage on a 0-10 scale.

        - 1-3 emojis => 10 points
        - 4-5 => 5 points
        - 0 or 6+ => 0 points

        Args:
            count: Emoji count.

        Returns:
            Emoji score from 0 to 10.
        """
        if 1 <= count <= 3:
            return 10.0
        if 4 <= count <= 5:
            return 5.0
        return 0.0

    def _score_structure(self, text: str) -> float:
        """
        Score structure/readability based on paragraph breaks.

        - Has paragraph breaks (multiple '\\n') => 10 points
        - Single block => 5 points

        Args:
            text: Post text.

        Returns:
            Structure score from 0 to 10.
        """
        normalized = text or ""
        # Count non-empty paragraphs separated by blank lines or newlines.
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", normalized) if p.strip()]
        if len(paragraphs) >= 2:
            return 10.0
        return 5.0

    def _score_food_descriptors(self, text: str) -> float:
        """
        Score presence of appetizing food descriptors on a 0-10 scale.

        Descriptors: fresh, crispy, delicious, savory, tender, juicy, aromatic,
        flavorful, homemade, authentic (case-insensitive).

        - 3+ descriptors => 10 points
        - 2 descriptors => 7 points
        - 1 descriptor => 4 points
        - 0 => 0 points

        Args:
            text: Post text.

        Returns:
            Descriptor score from 0 to 10.
        """
        descriptors = (
            "fresh",
            "crispy",
            "delicious",
            "savory",
            "tender",
            "juicy",
            "aromatic",
            "flavorful",
            "homemade",
            "authentic",
        )
        lowered = (text or "").lower()

        count = 0
        for word in descriptors:
            if re.search(rf"\b{re.escape(word)}\b", lowered):
                count += 1

        if count >= 3:
            return 10.0
        if count == 2:
            return 7.0
        if count == 1:
            return 4.0
        return 0.0

    def _calculate_overall_score(self, metrics: dict[str, Any]) -> float:
        """
        Calculate the overall quality score (0-10) using a weighted average.

        Weights:
            - length_score: 20%
            - has_cta: 20% (10 if True, 0 if False)
            - hashtag_score: 15%
            - emoji_score: 10%
            - structure_score: 20%
            - food_descriptor_score: 15%

        Args:
            metrics: Metrics dict as produced by score_post().

        Returns:
            Overall score from 0 to 10, rounded to 1 decimal.
        """
        length_score = float(metrics.get("length_score", 0.0) or 0.0)
        cta_score = 10.0 if bool(metrics.get("has_cta", False)) else 0.0
        hashtag_score = float(metrics.get("hashtag_score", 0.0) or 0.0)
        emoji_score = float(metrics.get("emoji_score", 0.0) or 0.0)
        structure_score = float(metrics.get("structure_score", 0.0) or 0.0)
        food_descriptor_score = float(metrics.get("food_descriptor_score", 0.0) or 0.0)

        weighted = (
            0.20 * length_score
            + 0.20 * cta_score
            + 0.15 * hashtag_score
            + 0.10 * emoji_score
            + 0.20 * structure_score
            + 0.15 * food_descriptor_score
        )
        return round(weighted, 1)

    def _generate_feedback(self, metrics: dict[str, Any], overall_score: float) -> list[str]:
        """
        Generate improvement suggestions based on metrics and overall score.

        Args:
            metrics: Metrics dict from score_post().
            overall_score: Overall score (0-10).

        Returns:
            List of actionable feedback strings.
        """
        feedback: list[str] = []

        length_score = float(metrics.get("length_score", 0.0) or 0.0)
        if length_score < 7.0:
            feedback.append("Post is too short/long - aim for 150-250 words")

        if not bool(metrics.get("has_cta", False)):
            feedback.append("Add a call-to-action (visit, order, try)")

        hashtag_score = float(metrics.get("hashtag_score", 0.0) or 0.0)
        if hashtag_score < 10.0:
            feedback.append("Use 3-5 hashtags for better reach")

        emoji_score = float(metrics.get("emoji_score", 0.0) or 0.0)
        if emoji_score < 10.0:
            feedback.append("Add 1-3 emojis to increase engagement")

        structure_score = float(metrics.get("structure_score", 0.0) or 0.0)
        if structure_score < 10.0:
            feedback.append("Add paragraph breaks for readability")

        descriptor_score = float(metrics.get("food_descriptor_score", 0.0) or 0.0)
        if descriptor_score < 10.0:
            feedback.append("Include food descriptors (fresh, crispy, delicious)")

        # If the score is very high, provide a brief reinforcement message.
        if overall_score >= 9.0 and not feedback:
            feedback.append("Great post — strong structure, engaging tone, and solid reach signals.")

        return feedback

    @staticmethod
    def _word_count(text: str) -> int:
        """
        Count words in text using a simple whitespace/punctuation split.

        Args:
            text: Input text.

        Returns:
            Number of words.
        """
        if not text:
            return 0
        # Treat sequences of letters/numbers/apostrophes as words.
        return len(re.findall(r"[A-Za-z0-9']+", text))

