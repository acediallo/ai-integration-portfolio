"""
Load, validate, and fill prompt templates from JSON files.

TemplateManager scans a templates directory, validates schema and variables,
and fills prompt_template placeholders with provided values.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any

# Optional: ensure logging is configured when used from app
try:
    import config
    config.setup_logging()
except Exception:  # noqa: S110
    pass

logger = logging.getLogger(__name__)

# Required top-level keys for a valid template JSON
_REQUIRED_TEMPLATE_KEYS = (
    "template_id",
    "name",
    "description",
    "category",
    "version",
    "prompt_template",
    "variables",
    "output_specs",
    "created_date",
)


class TemplateManager:
    """
    Load, validate, and manage prompt templates from a directory of JSON files.

    Scans the given directory for .json files, validates each against a schema,
    and stores them by template_id. Supports variable validation and
    placeholder filling for prompt generation.
    """

    def __init__(self, templates_dir: Path) -> None:
        """
        Initialize the manager and load all templates from the directory.

        Args:
            templates_dir: Path to the folder containing .json template files.

        Raises:
            FileNotFoundError: If templates_dir does not exist.
        """
        self.templates_dir = Path(templates_dir)
        if not self.templates_dir.is_dir():
            raise FileNotFoundError(f"Templates directory not found: {self.templates_dir}")
        self.templates: dict[str, dict[str, Any]] = {}
        self.load_templates()

    def load_templates(self) -> None:
        """
        Scan the templates directory for .json files, load and validate each,
        and store in self.templates keyed by template_id.

        Raises:
            FileNotFoundError: If templates_dir does not exist.
            json.JSONDecodeError: If a template file is invalid JSON.
            ValueError: If a template is missing required fields.
            ValueError: If no .json files are found in the directory.
        """
        json_files = list(self.templates_dir.glob("*.json"))
        if not json_files:
            raise ValueError(
                f"No .json template files found in {self.templates_dir}"
            )

        loaded = 0
        for path in json_files:
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON in %s: %s", path, e)
                raise

            missing = [k for k in _REQUIRED_TEMPLATE_KEYS if k not in data]
            if missing:
                logger.error("Template %s missing required fields: %s", path, missing)
                raise ValueError(
                    f"Template {path.name} missing required fields: {missing}"
                )

            template_id = data["template_id"]
            self.templates[template_id] = data
            loaded += 1

        logger.info("Loaded %d template(s) from %s", loaded, self.templates_dir)

    def get_template(self, template_id: str) -> dict[str, Any]:
        """
        Return the full template data for the given ID.

        Args:
            template_id: Unique template identifier (e.g. "menu_showcase_v1").

        Returns:
            Template dict with keys such as name, prompt_template, variables.

        Raises:
            ValueError: If template_id is not found.

        Example:
            >>> mgr.get_template("menu_showcase_v1")["name"]
            'Menu Item Showcase'
        """
        if template_id not in self.templates:
            logger.warning("Template not found: %s", template_id)
            raise ValueError(f"Template not found: {template_id}")
        return self.templates[template_id]

    def list_templates(self) -> list[dict[str, Any]]:
        """
        Return a list of summary dicts for all loaded templates.

        Intended for UI dropdowns: each dict includes template_id, name,
        description, and version.

        Returns:
            List of dicts with keys: template_id, name, description, version.
        """
        return [
            {
                "template_id": t["template_id"],
                "name": t["name"],
                "description": t["description"],
                "version": t["version"],
            }
            for t in self.templates.values()
        ]

    def validate_variables(
        self, template_id: str, variables: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """
        Check that all required template variables are present and types match.

        Args:
            template_id: Template to validate against.
            variables: Dict of variable names to values (e.g. {"dish_name": "Pasta"}).

        Returns:
            (is_valid, missing_or_invalid): True if all required vars present
            and types match; otherwise False and list of missing or type-mismatch
            variable names.

        Example:
            >>> mgr.validate_variables("menu_showcase_v1", {"dish_name": "Pasta"})
            (False, ['key_ingredient', 'price_point', ...])
        """
        template = self.get_template(template_id)
        var_specs = template.get("variables", [])
        missing_or_invalid: list[str] = []

        for spec in var_specs:
            name = spec.get("name")
            if not name:
                continue
            required = spec.get("required", False)
            expected_type = (spec.get("type") or "string").lower()
            value = variables.get(name)

            if required and (value is None or value == ""):
                missing_or_invalid.append(name)
                continue

            if value is None:
                continue

            # Type check: string, int, number/float, bool
            if expected_type == "string" and not isinstance(value, str):
                missing_or_invalid.append(name)
            elif expected_type in ("int", "integer") and not isinstance(value, int):
                missing_or_invalid.append(name)
            elif expected_type in ("number", "float") and not isinstance(
                value, (int, float)
            ):
                missing_or_invalid.append(name)
            elif expected_type == "bool" and not isinstance(value, bool):
                missing_or_invalid.append(name)

        is_valid = len(missing_or_invalid) == 0
        if not is_valid:
            logger.debug(
                "Validation failed for template %s: %s",
                template_id,
                missing_or_invalid,
            )
        return is_valid, missing_or_invalid

    def fill_template(
        self, template_id: str, variables: dict[str, Any]
    ) -> str:
        """
        Validate variables and replace {placeholders} in the prompt template.

        Args:
            template_id: Template to use.
            variables: Dict of variable names to values.

        Returns:
            Filled prompt string with all {variable_name} replaced.

        Raises:
            ValueError: If template_id not found or variable validation fails.

        Example:
            >>> mgr.fill_template("menu_showcase_v1", {"dish_name": "Pasta", ...})
            'Write an Instagram-style post for ... Pasta ...'
        """
        template = self.get_template(template_id)
        is_valid, missing_or_invalid = self.validate_variables(
            template_id, variables
        )
        if not is_valid:
            msg = f"Missing or invalid variables: {missing_or_invalid}"
            logger.warning("fill_template failed for %s: %s", template_id, msg)
            raise ValueError(msg)

        prompt_template = template["prompt_template"]
        # Build substitution dict from template variable names only
        var_names = {spec["name"] for spec in template["variables"]}
        subs = {
            k: (v if isinstance(v, str) else str(v))
            for k, v in variables.items()
            if k in var_names
        }
        try:
            filled = prompt_template.format(**subs)
        except KeyError as e:
            logger.error("Placeholder key error in %s: %s", template_id, e)
            raise ValueError(f"Missing placeholder value: {e}") from e

        # Sanity check: no unfilled {placeholders} left
        if "{" in filled and "}" in filled:
            remaining = re.findall(r"\{[^}]+\}", filled)
            if remaining:
                logger.warning("Unfilled placeholders in output: %s", remaining)
                raise ValueError(f"Unfilled placeholders: {remaining}")

        return filled
