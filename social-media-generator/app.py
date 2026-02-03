"""
Social Media Generator application entrypoint.

Validates configuration and runs the app (Streamlit or CLI).
"""

import logging
from typing import NoReturn

import config

logger = logging.getLogger(__name__)


def main() -> None:
    """
    Validate config, set up logging, and run the application.
    """
    config.setup_logging()
    config.validate_config()
    logger.info("Social Media Generator starting (model=%s)", config.MODEL_NAME)
    # TODO: Launch Streamlit or CLI flow
    print("Run with: streamlit run app.py")


if __name__ == "__main__":
    main()
