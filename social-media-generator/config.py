"""
Application configuration for the Social Media Generator.

Loads environment variables via python-dotenv, validates required settings
(e.g., OpenAI API key), and exposes typed configuration with defaults.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env from project root (directory containing config.py)
_PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(_PROJECT_ROOT / ".env")


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _path_from_env(key: str, default_subdir: str) -> Path:
    """
    Resolve a path from environment or project root subdir.

    Args:
        key: Environment variable name (e.g. DATA_DIR).
        default_subdir: Subdirectory under project root if env not set.

    Returns:
        Resolved absolute Path.
    """
    raw = os.getenv(key)
    if raw:
        return Path(raw).resolve()
    return (_PROJECT_ROOT / default_subdir).resolve()


DATA_DIR: Path = _path_from_env("DATA_DIR", "data")
LOGS_DIR: Path = _path_from_env("LOGS_DIR", "logs")

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# OpenAI & model settings
# ---------------------------------------------------------------------------

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
"""OpenAI API key; must be set for API calls."""

MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
"""Model identifier for chat completions."""

# Token cost configuration (USD).
#
# The application primarily uses per-1K token constants for cost calculations
# while also keeping per-token values for compatibility.
COST_PER_INPUT_TOKEN: float = float(os.getenv("COST_PER_INPUT_TOKEN", "0.00000015"))
"""Approximate cost per input token in USD."""

COST_PER_OUTPUT_TOKEN: float = float(os.getenv("COST_PER_OUTPUT_TOKEN", "0.0000006"))
"""Approximate cost per output token in USD."""

INPUT_COST_PER_1K_TOKENS: float = float(
    os.getenv("INPUT_COST_PER_1K_TOKENS", str(COST_PER_INPUT_TOKEN * 1000.0))
)
"""Cost per 1,000 input tokens in USD."""

OUTPUT_COST_PER_1K_TOKENS: float = float(
    os.getenv("OUTPUT_COST_PER_1K_TOKENS", str(COST_PER_OUTPUT_TOKEN * 1000.0))
)
"""Cost per 1,000 output tokens in USD."""


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------

DAILY_BUDGET_USD: float = float(os.getenv("DAILY_BUDGET", "2.00"))
"""Maximum allowed spend per day in USD."""


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_LEVEL_RAW: str = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_LEVEL: int = getattr(logging, LOG_LEVEL_RAW, logging.INFO)
LOG_FILE: Optional[Path] = (LOGS_DIR / "app.log") if LOGS_DIR else None


def setup_logging(
    level: Optional[int] = None,
    log_file: Optional[Path] = None,
) -> None:
    """
    Configure root logger with console and optional file handler.

    Args:
        level: Logging level (defaults to config LOG_LEVEL).
        log_file: Optional file path for log output (defaults to config LOG_FILE).
    """
    lvl = level if level is not None else LOG_LEVEL
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=lvl,
        format=fmt,
        datefmt=date_fmt,
        force=True,
    )
    root = logging.getLogger()

    # Remove existing handlers to avoid duplicates
    for h in root.handlers[:]:
        root.removeHandler(h)

    console = logging.StreamHandler()
    console.setLevel(lvl)
    console.setFormatter(logging.Formatter(fmt, datefmt=date_fmt))
    root.addHandler(console)

    file_path = log_file if log_file is not None else LOG_FILE
    if file_path:
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(file_path, encoding="utf-8")
            fh.setLevel(lvl)
            fh.setFormatter(logging.Formatter(fmt, datefmt=date_fmt))
            root.addHandler(fh)
        except OSError:
            root.warning("Could not create log file at %s", file_path)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_config() -> None:
    """
    Validate required configuration (e.g., API key).

    Raises:
        ValueError: If OPENAI_API_KEY is missing or empty.
    """
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is not set. "
            "Copy .env.example to .env and add your OpenAI API key."
        )


# Call validate_config() from app entrypoint before using the API
