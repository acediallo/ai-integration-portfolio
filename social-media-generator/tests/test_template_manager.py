"""
Tests for TemplateManager: load, get, validate_variables, fill_template.
"""

from pathlib import Path

import pytest

from src.template_manager import TemplateManager


@pytest.fixture
def template_manager() -> TemplateManager:
    """Create a TemplateManager instance pointing at the project templates dir."""
    templates_dir = Path(__file__).resolve().parent.parent / "templates"
    return TemplateManager(templates_dir)


def test_load_templates_success(template_manager: TemplateManager) -> None:
    """Create TemplateManager; assert templates loaded and count matches files."""
    assert len(template_manager.templates) > 0
    json_count = len(list((Path(__file__).resolve().parent.parent / "templates").glob("*.json")))
    assert len(template_manager.templates) == json_count


def test_get_template_exists(template_manager: TemplateManager) -> None:
    """Get 'menu_showcase_v1'; assert returned dict has correct structure."""
    t = template_manager.get_template("menu_showcase_v1")
    assert t["template_id"] == "menu_showcase_v1"
    assert t["name"] == "Menu Item Showcase"
    assert "prompt_template" in t
    assert "variables" in t
    assert isinstance(t["variables"], list)
    assert len(t["variables"]) >= 1


def test_get_template_not_found(template_manager: TemplateManager) -> None:
    """Try to get 'nonexistent_template'; assert raises ValueError."""
    with pytest.raises(ValueError, match="Template not found"):
        template_manager.get_template("nonexistent_template")


def test_validate_variables_all_present(template_manager: TemplateManager) -> None:
    """Valid variables dict; assert validation passes."""
    variables = {
        "dish_name": "Truffle Carbonara",
        "key_ingredient": "black truffle",
        "price_point": "$18",
        "restaurant_vibe": "cozy Italian bistro",
        "unique_feature": "house-made pasta",
    }
    is_valid, missing = template_manager.validate_variables(
        "menu_showcase_v1", variables
    )
    assert is_valid is True
    assert missing == []


def test_validate_variables_missing_required(
    template_manager: TemplateManager,
) -> None:
    """Missing required variable; assert validation fails and missing var in list."""
    variables = {
        "dish_name": "Pasta",
        "key_ingredient": "truffle",
        # missing: price_point, restaurant_vibe, unique_feature
    }
    is_valid, missing = template_manager.validate_variables(
        "menu_showcase_v1", variables
    )
    assert is_valid is False
    assert "price_point" in missing
    assert "restaurant_vibe" in missing
    assert "unique_feature" in missing


def test_fill_template_success(template_manager: TemplateManager) -> None:
    """Provide all required variables; call fill_template(); assert placeholders replaced."""
    variables = {
        "dish_name": "Truffle Carbonara",
        "key_ingredient": "black truffle",
        "price_point": "$18",
        "restaurant_vibe": "cozy Italian bistro",
        "unique_feature": "house-made pasta",
    }
    result = template_manager.fill_template("menu_showcase_v1", variables)
    assert "Truffle Carbonara" in result
    assert "black truffle" in result
    assert "$18" in result
    assert "{dish_name}" not in result
    assert "{key_ingredient}" not in result


def test_fill_template_missing_vars(template_manager: TemplateManager) -> None:
    """Missing required variable; assert raises ValueError."""
    variables = {"dish_name": "Pasta"}
    with pytest.raises(ValueError, match="Missing or invalid variables"):
        template_manager.fill_template("menu_showcase_v1", variables)
