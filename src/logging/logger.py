import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from src.config.settings import get_settings

settings = get_settings()

def setup_logger(name: str) -> logging.Logger:
    """Configure and return a logger instance with both file and console handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL)
    
    # Create formatters
    formatter = logging.Formatter(settings.LOG_FORMAT)
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler (if log file is specified)
    if settings.LOG_FILE:
        log_path = Path(settings.LOG_FILE)
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Create pipeline logger
pipeline_logger = setup_logger("tender_pipeline")