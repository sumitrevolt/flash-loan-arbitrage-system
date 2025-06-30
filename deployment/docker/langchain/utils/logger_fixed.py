# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
Logger Utility
==============

Centralized logging configuration for the LangChain multi-agent system.
"""

from pathlib import Path
from typing import Optional
import logging
import os


# Global flag to ensure logging is configured only once
_logging_configured = False


class UnicodeFormatter(logging.Formatter):
    """Custom formatter that handles Unicode characters safely"""
    
    def format(self, record):
        try:
            return super().format(record)
        except UnicodeEncodeError:
            # Fallback to ASCII if Unicode fails
            record.msg = str(record.msg).encode('ascii', 'ignore').decode('ascii')
            return super().format(record)


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with consistent formatting and configuration.
    
    Args:
        name: Logger name (usually __name__)
        level: Log level override
        
    Returns:
        Configured logger instance
    """
    global _logging_configured
    
    # Get log level from environment or use default
    log_level = level or os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Configure logging if not already done
    if not _logging_configured:
        _configure_logging()
        _logging_configured = True
    
    # Get or create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level, logging.INFO)
    
    return logger


def _configure_logging():
    """Configure root logging settings"""
    
    # Create logs directory
    log_dir = Path("/app/logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create custom formatter
    formatter = UnicodeFormatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'

    
    # Configure handlers
    handlers = [
        logging.StreamHandler(),
        logging.FileHandler(str(log_dir / 'langchain.log'))

    
    # Apply formatter to all handlers
    for handler in handlers:
        handler.setFormatter(formatter)
    
    # Basic logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=handlers,
        force=True  # Override existing configuration

    
    # Log configuration completion
    logger = logging.getLogger(__name__)
    logger.info("Logging configuration initialized")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance (alias for setup_logger)"""
    return setup_logger(name) 