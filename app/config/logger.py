# app/config/logger_config.py
import sys
from loguru import logger
from pathlib import Path

# Setup paths
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

# Remove default handler
logger.remove()

# Console output
logger.add(
    sys.stdout,
    colorize=True,
    # serialize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
           "<level>{message}</level>",
    level="INFO",
)

# File output (rotating)
logger.add(
    LOG_FILE,
    rotation="10 MB",
    retention="14 days",
    compression="zip",
    serialize=True,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="DEBUG",
    enqueue=True,
)

def get_logger(name: str = None):
    """Bind logger with a custom module name."""
    if name:
        return logger.bind(module=name)
    return logger
