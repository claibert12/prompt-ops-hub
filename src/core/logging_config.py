import os
import logging
from logging.config import dictConfig

import sentry_sdk


def setup_logging() -> None:
    """Configure application logging and optional error monitoring."""
    level = os.getenv("LOG_LEVEL", "INFO")
    dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": level,
                }
            },
            "root": {"handlers": ["console"], "level": level},
        }
    )

    dsn = os.getenv("SENTRY_DSN")
    if dsn:
        sentry_sdk.init(dsn=dsn, traces_sample_rate=1.0)
        logging.getLogger(__name__).info("Sentry initialized")
