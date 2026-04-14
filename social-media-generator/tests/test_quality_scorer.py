"""
Tests for QualityScorer.
"""

import pytest

from src.quality_scorer import QualityScorer


@pytest.fixture
def scorer() -> QualityScorer:
    """Provide a QualityScorer instance."""
    return QualityScorer()


def _make_words(n: int) -> str:
    """Create a deterministic n-word string."""
    return " ".join(["word"] * n)


def test_score_perfect_post(scorer: QualityScorer) -> None:
    """Mock post with all good metrics; assert overall_score >= 8.0."""
    text = (
        f"{_make_words(180)}\n\n"
        "Fresh crispy delicious and aromatic flavors you’ll love. 🍕🍝\n\n"
        "Visit us today and try it while it’s hot!\n"
        "#food #yum #delicious #restaurant"
    )
    result = scorer.score_post(text)
    assert result["overall_score"] >= 8.0
    assert "metrics" in result
    assert "feedback" in result
    metrics = result["metrics"]
    for key in (
        "length_score",
        "has_cta",
        "hashtag_count",
        "hashtag_score",
        "emoji_count",
        "emoji_score",
        "structure_score",
        "food_descriptor_score",
    ):
        assert key in metrics


def test_score_poor_post(scorer: QualityScorer) -> None:
    """Too short, no CTA, no hashtags; assert low score and feedback present."""
    text = "Great food."
    result = scorer.score_post(text)
    assert result["overall_score"] < 5.0
    assert isinstance(result["feedback"], list)
    assert len(result["feedback"]) > 0


def test_score_length_optimal(scorer: QualityScorer) -> None:
    """200-word post => length_score == 10.0."""
    text = _make_words(200)
    assert scorer._score_length(text) == 10.0


def test_score_length_too_short(scorer: QualityScorer) -> None:
    """50-word post => length_score < 5.0."""
    text = _make_words(50)
    assert scorer._score_length(text) < 5.0


def test_has_call_to_action_true(scorer: QualityScorer) -> None:
    """Post with CTA should return True."""
    assert scorer._has_call_to_action("Visit us today for lunch!") is True


def test_has_call_to_action_false(scorer: QualityScorer) -> None:
    """Post without CTA should return False."""
    assert scorer._has_call_to_action("We have great lunch specials.") is False


def test_count_hashtags(scorer: QualityScorer) -> None:
    """Count hashtags by # occurrences."""
    assert scorer._count_hashtags("#food #yum #delicious") == 3


def test_score_hashtags_optimal(scorer: QualityScorer) -> None:
    """4 hashtags => score == 10.0."""
    assert scorer._score_hashtags(4) == 10.0


def test_count_emojis(scorer: QualityScorer) -> None:
    """Count emojis via regex heuristic."""
    assert scorer._count_emojis("🍕🍝😋") == 3


def test_score_emojis_optimal(scorer: QualityScorer) -> None:
    """2 emojis => score == 10.0."""
    assert scorer._score_emojis(2) == 10.0


def test_score_food_descriptors(scorer: QualityScorer) -> None:
    """3+ descriptors => score == 10.0."""
    assert scorer._score_food_descriptors("fresh crispy delicious") == 10.0


def test_generate_feedback(scorer: QualityScorer) -> None:
    """Low scores should generate improvement tips."""
    metrics = {
        "length_score": 0.0,
        "has_cta": False,
        "hashtag_score": 0.0,
        "emoji_score": 0.0,
        "structure_score": 5.0,
        "food_descriptor_score": 0.0,
    }
    feedback = scorer._generate_feedback(metrics, overall_score=2.0)
    assert any("aim for 150-250 words" in f for f in feedback)
    assert any("call-to-action" in f for f in feedback)
    assert any("hashtags" in f for f in feedback)
    assert any("emojis" in f for f in feedback)
    assert any("paragraph breaks" in f for f in feedback)
    assert any("food descriptors" in f for f in feedback)

