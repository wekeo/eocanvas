import logging
import sys

logger = logging.getLogger(__package__)


def setup_logger(level: int = logging.INFO) -> None:
    logger.setLevel(level)
    stdout_handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(stdout_handler)
