"""
Tests for ABTester.

All generation/scoring is mocked; no OpenAI calls are performed.
"""

from unittest.mock import MagicMock

import pytest

from src.ab_testing import ABTester


@pytest.fixture
def mock_openai_handler() -> MagicMock:
    """Mock OpenAIHandler dependency."""
    return MagicMock()


@pytest.fixture
def mock_quality_scorer() -> MagicMock:
    """Mock QualityScorer dependency."""
    return MagicMock()


@pytest.fixture
def mock_template_manager() -> MagicMock:
    """Mock TemplateManager dependency."""
    return MagicMock()


@pytest.fixture
def ab_tester(
    mock_openai_handler: MagicMock, mock_quality_scorer: MagicMock
) -> ABTester:
    """Create ABTester with mocked dependencies."""
    return ABTester(openai_handler=mock_openai_handler, quality_scorer=mock_quality_scorer)


def test_compare_templates_two_templates(
    ab_tester: ABTester,
    mock_openai_handler: MagicMock,
    mock_quality_scorer: MagicMock,
    mock_template_manager: MagicMock,
) -> None:
    """Mock 2 templates, 3 variations each; assert winner is template A."""
    template_a = {"template_id": "A", "name": "Template A"}
    template_b = {"template_id": "B", "name": "Template B"}

    mock_template_manager.get_template.side_effect = [template_a, template_b]
    mock_template_manager.fill_template.side_effect = ["prompt A", "prompt B"]

    # 3 variations for A then 3 for B
    mock_openai_handler.generate_variations.side_effect = [
        [
            {"variation": 1, "content": "A1", "cost": 0.01},
            {"variation": 2, "content": "A2", "cost": 0.01},
            {"variation": 3, "content": "A3", "cost": 0.01},
        ],
        [
            {"variation": 1, "content": "B1", "cost": 0.02},
            {"variation": 2, "content": "B2", "cost": 0.02},
            {"variation": 3, "content": "B3", "cost": 0.02},
        ],
    ]

    # Score calls in content order; A gets 8s, B gets 7s
    mock_quality_scorer.score_post.side_effect = (
        [{"overall_score": 8.0, "metrics": {"m": 1}}] * 3
        + [{"overall_score": 7.0, "metrics": {"m": 1}}] * 3
    )

    report = ab_tester.compare_templates(
        template_ids=["A", "B"],
        variables={"x": "y"},
        template_manager=mock_template_manager,
        num_variations=3,
    )

    assert report["winner"]["template_id"] == "A"
    assert report["summary"]["total_templates_tested"] == 2
    assert report["summary"]["total_variations_generated"] == 6
    assert len(report["results"]) == 2
    assert report["results"][0]["template_id"] == "A"
    assert len(report["results"][0]["variations"]) == 3


def test_compare_templates_three_templates(
    ab_tester: ABTester,
    mock_openai_handler: MagicMock,
    mock_quality_scorer: MagicMock,
    mock_template_manager: MagicMock,
) -> None:
    """Mock 3 templates; assert all 3 in results and winner has highest avg."""
    templates = [
        {"template_id": "T1", "name": "T1"},
        {"template_id": "T2", "name": "T2"},
        {"template_id": "T3", "name": "T3"},
    ]
    mock_template_manager.get_template.side_effect = templates
    mock_template_manager.fill_template.side_effect = ["p1", "p2", "p3"]
    mock_openai_handler.generate_variations.side_effect = [
        [{"variation": 1, "content": "c1", "cost": 0.01}] * 2,
        [{"variation": 1, "content": "c2", "cost": 0.01}] * 2,
        [{"variation": 1, "content": "c3", "cost": 0.01}] * 2,
    ]
    # Avg scores: T1=6, T2=9, T3=7
    mock_quality_scorer.score_post.side_effect = (
        [{"overall_score": 6.0, "metrics": {}}] * 2
        + [{"overall_score": 9.0, "metrics": {}}] * 2
        + [{"overall_score": 7.0, "metrics": {}}] * 2
    )

    report = ab_tester.compare_templates(
        template_ids=["T1", "T2", "T3"],
        variables={},
        template_manager=mock_template_manager,
        num_variations=2,
    )

    assert {r["template_id"] for r in report["results"]} == {"T1", "T2", "T3"}
    assert report["winner"]["template_id"] == "T2"


def test_determine_winner(ab_tester: ABTester) -> None:
    """Assert correct winner selected and reason string format correct."""
    results = [
        {"template_id": "A", "template_name": "A", "avg_quality_score": 7.0},
        {"template_id": "B", "template_name": "B", "avg_quality_score": 8.5},
    ]
    winner = ab_tester._determine_winner(results)
    assert winner["template_id"] == "B"
    assert winner["reason"] == "Highest average quality score: 8.5/10"


def test_run_ab_test(
    ab_tester: ABTester,
    mock_openai_handler: MagicMock,
    mock_quality_scorer: MagicMock,
    mock_template_manager: MagicMock,
) -> None:
    """Assert simplified interface works and returns same structure."""
    mock_template_manager.get_template.side_effect = [
        {"template_id": "A", "name": "A"},
        {"template_id": "B", "name": "B"},
    ]
    mock_template_manager.fill_template.side_effect = ["pa", "pb"]
    mock_openai_handler.generate_variations.side_effect = [
        [{"variation": 1, "content": "a", "cost": 0.0}],
        [{"variation": 1, "content": "b", "cost": 0.0}],
    ]
    mock_quality_scorer.score_post.side_effect = [
        {"overall_score": 6.0, "metrics": {}},
        {"overall_score": 5.0, "metrics": {}},
    ]

    report = ab_tester.run_ab_test(
        template_a_id="A",
        template_b_id="B",
        variables={},
        template_manager=mock_template_manager,
        num_variations=1,
    )
    assert "results" in report and "winner" in report and "summary" in report
    assert report["summary"]["total_templates_tested"] == 2


def test_compare_templates_invalid_template(
    ab_tester: ABTester, mock_template_manager: MagicMock
) -> None:
    """Template not found should raise ValueError."""
    mock_template_manager.get_template.side_effect = ValueError("Template not found")
    with pytest.raises(ValueError):
        ab_tester.compare_templates(
            template_ids=["missing"],
            variables={},
            template_manager=mock_template_manager,
            num_variations=1,
        )


def test_total_cost_calculation(
    ab_tester: ABTester,
    mock_openai_handler: MagicMock,
    mock_quality_scorer: MagicMock,
    mock_template_manager: MagicMock,
) -> None:
    """Assert total_cost sums known costs correctly."""
    mock_template_manager.get_template.side_effect = [
        {"template_id": "A", "name": "A"},
        {"template_id": "B", "name": "B"},
    ]
    mock_template_manager.fill_template.side_effect = ["pa", "pb"]
    mock_openai_handler.generate_variations.side_effect = [
        [{"variation": 1, "content": "a1", "cost": 0.01}, {"variation": 2, "content": "a2", "cost": 0.02}],
        [{"variation": 1, "content": "b1", "cost": 0.03}, {"variation": 2, "content": "b2", "cost": 0.04}],
    ]
    mock_quality_scorer.score_post.side_effect = [
        {"overall_score": 5.0, "metrics": {}},
        {"overall_score": 5.0, "metrics": {}},
        {"overall_score": 5.0, "metrics": {}},
        {"overall_score": 5.0, "metrics": {}},
    ]

    report = ab_tester.compare_templates(
        template_ids=["A", "B"],
        variables={},
        template_manager=mock_template_manager,
        num_variations=2,
    )
    assert report["summary"]["total_cost"] == pytest.approx(0.10, abs=1e-6)

