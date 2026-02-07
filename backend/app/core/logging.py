from __future__ import annotations

import logging
import sys
from pathlib import Path

from loguru import logger
from loguru_config import LoguruConfig

from app.core.settings import get_app_settings

LOG_CONFIG_PATH = Path("backend/mlog.yaml")
LOG_DIR = Path("logs")


class InterceptHandler(logging.Handler):
    """Redirect standard logging records to Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(
            depth=depth,
            exception=record.exc_info,
        ).log(level, record.getMessage())


def _configure_standard_logging() -> None:
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.INFO)

    for name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
        "starlette",
    ):
        logging_logger = logging.getLogger(name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False


def configure_logging() -> None:
    """Configure loguru using a config file and runtime settings."""
    settings = get_app_settings()

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if not LOG_CONFIG_PATH.exists():
        logger.warning("Log config not found: {}", LOG_CONFIG_PATH)
        return

    config = LoguruConfig.load(str(LOG_CONFIG_PATH), configure=False)
    if config is None:
        return

    config = config.parse()
    if not settings.debug and config.handlers:
        config.handlers = [
            handler
            for handler in config.handlers
            if getattr(handler.get("sink"), "write", None) is None
        ]

    config.configure()
    _configure_standard_logging()

    if settings.debug:
        logger.debug("Loguru configured (debug mode).")
    else:
        logger.info("Loguru configured (production mode).")
