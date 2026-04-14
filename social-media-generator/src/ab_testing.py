"""
A/B testing utilities for social media prompt templates.

This module compares multiple templates by generating variations with the same
input variables, scoring the outputs, and selecting a winner based on average
quality score.
"""

from __future__ import annotations

import logging
from typing import Any

import config
from src.openai_handler import OpenAIHandler
from src.quality_scorer import QualityScorer
from src.template_manager import TemplateManager


logger = logging.getLogger(__name__)


class ABTester:
    """Compare template performance and identify winners."""

    def __init__(self, openai_handler: OpenAIHandler, quality_scorer: QualityScorer) -> None:
        """
        Create an A/B tester with dependencies for generation and scoring.

        Args:
            openai_handler: OpenAIHandler instance used to generate post variations.
            quality_scorer: QualityScorer instance used to score generated posts.
        """
        config.setup_logging()
        self.openai_handler = openai_handler
        self.quality_scorer = quality_scorer

    def compare_templates(
        self,
        template_ids: list[str],
        variables: dict[str, Any],
        template_manager: TemplateManager,
        num_variations: int = 3,
    ) -> dict[str, Any]:
        """
        Compare multiple templates by generating and scoring variations.

        For each template:
        - Fill the template prompt with the same variables
        - Generate `num_variations` outputs
        - Score each output with QualityScorer
        - Aggregate average quality and cost

        Args:
            template_ids: Template IDs to compare.
            variables: Variables used to fill each template prompt.
            template_manager: TemplateManager for loading/filling templates.
            num_variations: Variations to generate per template.

        Returns:
            Results payload including per-template stats, winner, and summary.

        Raises:
            ValueError: If a template is not found, variable validation fails,
                or no results are produced.
            Exception: OpenAI errors are logged and re-raised.

        Example:
            >>> ab = ABTester(openai_handler, quality_scorer)
            >>> report = ab.compare_templates(
            ...     [\"menu_showcase_v1\", \"promotion_v1\"],
            ...     variables={\"dish_name\": \"Pasta\", ...},
            ...     template_manager=tm,
            ...     num_variations=3,
            ... )
            >>> report[\"winner\"][\"template_id\"]
            'menu_showcase_v1'
        """
        if not template_ids:
            raise ValueError("template_ids must not be empty.")
        if num_variations <= 0:
            raise ValueError("num_variations must be >= 1.")

        logger.info(
            "Starting template comparison: templates=%s, variations_per_template=%d",
            template_ids,
            num_variations,
        )

        results: list[dict[str, Any]] = []
        total_cost_all_templates = 0.0

        for template_id in template_ids:
            # Template not found should raise ValueError from TemplateManager.
            template = template_manager.get_template(template_id)
            template_name = str(template.get("name", template_id))

            # Fill template; TemplateManager will validate variables and raise ValueError.
            prompt = template_manager.fill_template(template_id, variables)

            try:
                generated = self.openai_handler.generate_variations(
                    prompt=prompt,
                    num_variations=num_variations,
                    max_tokens=300,
                )
            except Exception as e:
                logger.exception("OpenAI generation failed for template %s: %s", template_id, e)
                raise

            variations_payload: list[dict[str, Any]] = []
            quality_scores: list[float] = []
            costs: list[float] = []

            for variation in generated:
                content = str(variation.get("content", "") or "")
                scoring = self.quality_scorer.score_post(content)
                quality_score = float(scoring.get("overall_score", 0.0) or 0.0)
                metrics = dict(scoring.get("metrics", {}) or {})

                cost = float(variation.get("cost", 0.0) or 0.0)

                variations_payload.append(
                    {
                        "variation": int(variation.get("variation", len(variations_payload) + 1)),
                        "content": content,
                        "quality_score": quality_score,
                        "cost": cost,
                        "metrics": metrics,
                    }
                )
                quality_scores.append(quality_score)
                costs.append(cost)

            if not variations_payload:
                raise ValueError(f"Empty results for template {template_id}")

            avg_quality = sum(quality_scores) / len(quality_scores)
            total_cost = sum(costs)
            avg_cost = total_cost / len(costs) if costs else 0.0

            total_cost_all_templates += total_cost

            template_result = {
                "template_id": template_id,
                "template_name": template_name,
                "variations": variations_payload,
                "avg_quality_score": round(avg_quality, 2),
                "avg_cost": round(avg_cost, 6),
                "total_cost": round(total_cost, 6),
            }
            results.append(template_result)

            logger.info(
                "Completed template %s (%s): avg_score=%.2f, total_cost=$%.6f",
                template_id,
                template_name,
                template_result["avg_quality_score"],
                template_result["total_cost"],
            )

        if not results:
            raise ValueError("No results produced.")

        winner = self._determine_winner(results)
        summary = {
            "total_templates_tested": len(template_ids),
            "total_variations_generated": len(template_ids) * num_variations,
            "total_cost": round(total_cost_all_templates, 6),
        }

        logger.info(
            "Template comparison complete. Winner=%s total_cost=$%.6f",
            winner.get("template_id"),
            summary["total_cost"],
        )

        return {"results": results, "winner": winner, "summary": summary}

    def _determine_winner(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Determine the winning template based on highest average quality score.

        Args:
            results: List of per-template result dicts produced by compare_templates().

        Returns:
            Winner dict with template_id, template_name, reason, and avg_quality_score.

        Raises:
            ValueError: If results is empty.
        """
        if not results:
            raise ValueError("Cannot determine winner from empty results.")

        best = max(results, key=lambda r: float(r.get("avg_quality_score", 0.0) or 0.0))
        avg = float(best.get("avg_quality_score", 0.0) or 0.0)
        winner = {
            "template_id": best.get("template_id"),
            "template_name": best.get("template_name"),
            "reason": f"Highest average quality score: {avg:.1f}/10",
            "avg_quality_score": round(avg, 2),
        }
        logger.info("Winner determined: %s (%s)", winner["template_id"], winner["reason"])
        return winner

    def run_ab_test(
        self,
        template_a_id: str,
        template_b_id: str,
        variables: dict[str, Any],
        template_manager: TemplateManager,
        num_variations: int = 5,
    ) -> dict[str, Any]:
        """
        Run a simplified two-template A/B test.

        Args:
            template_a_id: First template ID.
            template_b_id: Second template ID.
            variables: Variables used to fill each template prompt.
            template_manager: TemplateManager used to fill prompts.
            num_variations: Variations to generate per template.

        Returns:
            Same structure as compare_templates().

        Example:
            >>> report = ab.run_ab_test(\"menu_showcase_v1\", \"promotion_v1\", vars, tm)
            >>> report[\"winner\"][\"template_id\"]
            'menu_showcase_v1'
        """
        return self.compare_templates(
            template_ids=[template_a_id, template_b_id],
            variables=variables,
            template_manager=template_manager,
            num_variations=num_variations,
        )

