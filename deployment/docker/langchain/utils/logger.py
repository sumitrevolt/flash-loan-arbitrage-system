"""
Logger Utility
==============

Centralized logging configuration for the LangChain multi-agent system.
"""

import logging
import sys
from typing import Optional
import os

def setup_logger(name: str, level: Optional[str] = None, log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with consistent formatting and configuration.
    
    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    
    # Get log level from environment or use default
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level, logging.INFO))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level, logging.INFO))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        try:
            # Ensure log directory exists
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, level, logging.INFO))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not create file handler for {log_file}: {e}")
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get an existing logger or create a new one."""
    return logging.getLogger(name)

class LoggerMixin:
    """Mixin class to add logging capability to any class."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        if not hasattr(self, '_logger'):
            self._logger = setup_logger(self.__class__.__name__)
        return self._logger
