import sys
from loguru import logger
from src.utils.config import get_settings

def setup_logging():
    settings = get_settings()
    # Remove default handler
    logger.remove()

    # Add standard output handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG" if settings.DEBUG else "INFO",
    )

    # Add file handler for persistence
    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="1 week",
        level="INFO",
    )

setup_logging()
