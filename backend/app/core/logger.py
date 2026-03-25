# backend/app/core/logger.py
from loguru import logger
import sys

# Remove default loguru handler
logger.remove()

# Add custom stdout handler
logger.add(
    sys.stdout,
    format="{time} | {level} | {message}",
    level="INFO"
)