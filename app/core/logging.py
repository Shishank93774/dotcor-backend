import logging
from pathlib import Path

from app.core.config import config

ENVIRONMENT_NAME = config.ENVIRONMENT_NAME


def get_logger(namespace):
    # Ensure logs directory exists
    log_dir = Path(f"{ENVIRONMENT_NAME}_logs")
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger(name=namespace)
    logger.setLevel(logging.INFO)

    # Avoid adding multiple handlers if get_logger is called multiple times for the same namespace
    if not logger.handlers:
        # File Handler: All logs to a central file
        file_handler = logging.FileHandler(f"{ENVIRONMENT_NAME}_logs/app.log")
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - [%(name)s] - %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Disable propagation to prevent printing to terminal via root logger
        logger.propagate = False

    return logger
