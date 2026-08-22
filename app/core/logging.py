import logging
from pathlib import Path

from app.core.config import config

ENVIRONMENT_NAME = config.ENVIRONMENT_NAME


def _build_formatter() -> logging.Formatter:
    return logging.Formatter(
        "%(asctime)s - %(levelname)s - [%(name)s] (%(module)s:%(lineno)d in %(funcName)s) - %(message)s"
    )


def get_logger(namespace):
    # Ensure logs directory exists
    log_dir = Path(f"{ENVIRONMENT_NAME}_logs")
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger(name=namespace)
    logger.setLevel(logging.DEBUG if config.DEBUG else logging.INFO)

    # Avoid adding multiple handlers if get_logger is called multiple times for the same namespace
    if not logger.handlers:
        # File Handler: All logs to a central file only; nothing on the terminal
        file_handler = logging.FileHandler(f"{ENVIRONMENT_NAME}_logs/app.log")
        file_handler.setFormatter(_build_formatter())
        logger.addHandler(file_handler)

        # Disable propagation to prevent printing to terminal via root logger
        logger.propagate = False

    return logger
