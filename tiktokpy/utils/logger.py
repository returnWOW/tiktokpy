import logging
import sys

from loguru import logger as base_logger

logger = base_logger


def init_logger():
    global logger
    logging.disable(logging.CRITICAL)
    logger.remove()
    logger.add(
        sink=sys.stdout,
        level=logging.DEBUG,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level}</level> | "
        "<level>{message}</level>",
    )
    logger.add("tiktokpy.log", rotation="500 MB", level=logging.DEBUG, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level}</level> | "
        "<level>{message}</level>")
