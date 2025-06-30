# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from pathlib import Path
import logging
import os
import sys
"""
Unicode-Safe Logger for Windows
==============================

This module provides a Unicode-safe logger that works on Windows systems
by replacing emoji characters with text equivalents.
"""


# Emoji to text mapping
EMOJI_TO_TEXT = {}
    '[INIT]': '[LAUNCH]',
    '[SEARCH]': '[SEARCH]',
    '[OK]': '[SUCCESS]',
    '[ERROR]': '[ERROR]',
    '[WARN]': '[WARNING]',
    '[SYNC]': '[PROCESS]',
    '[METRICS]': '[DATA]',
    '🏥': '[HEALTH]',
    '[TASK]': '[TARGET]',
    '[INFO]': '[INFO]',
    '[SETUP]': '[TOOL]',
    '🔨': '[BUILD]',
    '[TOOL]': '[REPAIR]',
    '[NETWORK]': '[NETWORK]',
    '[GROWTH]': '[METRICS]',
    '🛡️': '[SECURITY]',
    '🔐': '[AUTH]',
    '📁': '[FILE]',
    '[CELEBRATE]': '[CELEBRATION]',
    '🤖': '[AI]',
    '[STAR]': '[STAR]',
    '[ALERT]': '[ALERT]',
    '🧪': '[TEST]',
    '[HOT]': '[HOT]',
    '💎': '[PREMIUM]',
    '[FAST]': '[FAST]',
    '[ART]': '[DESIGN]',
    '[LOG]': '[NOTE]',
    '[CIRCUS]': '[DEMO]',
    '🔮': '[PREDICT]',
    '[START]': '[HIGHLIGHT]',
    '[THEATER]': '[MOCK]',
    '[SUCCESS]': '[WINNER]',
    '🌈': '[COLORFUL]',
    '[MUSIC]': '[MUSIC]',
    '[MOVIE]': '[MOVIE]',
    '[ART]': '[ART]',
    '[TASK]': '[GOAL]',
    '[CIRCUS]': '[EVENT]',
    '[THEATER]': '[THEATER]',
    '[ART]': '[CREATIVE]',
    '[METRICS]': '[CHART]',
    '[GROWTH]': '[GRAPH]',
    '📉': '[DOWNTREND]',
    '[HOT]': '[FIRE]',
    '💥': '[EXPLOSION]',
    '[FAST]': '[LIGHTNING]',
    '🌪️': '[TORNADO]',
    '🌊': '[WAVE]',
    '🏔️': '[MOUNTAIN]',
    '🌲': '[TREE]',
    '🌺': '[FLOWER]',
    '🌙': '[MOON]',
    '☀️': '[SUN]',
    '[STAR]': '[STAR]',
    '[START]': '[SPARKLE]',
    '✨': '[SPARKLES]',
    '💫': '[DIZZY]',
    '🔆': '[BRIGHT]',
    '🌍': '[EARTH]',
    '🌎': '[AMERICAS]',
    '🌏': '[ASIA]',
    '🗺️': '[MAP]',
    '🧭': '[COMPASS]',
    '[TASK]': '[BULLSEYE]',
    '🔎': '[MAGNIFY]',
    '[SEARCH]': '[SEARCH]',
    '🔭': '[TELESCOPE]',
    '🔬': '[MICROSCOPE]',
    '🧪': '[TEST_TUBE]',
    '🧬': '[DNA]',
    '🔬': '[SCIENCE]',
    '🧲': '[MAGNET]',
    '🧪': '[CHEMISTRY]',
    '🔬': '[BIOLOGY]',
    '🧬': '[GENETICS]',


def unicode_safe_text(text: str) -> str:
    """Convert emoji characters to text equivalents"""
    if not isinstance(text, str):
        return str(text)
    
    safe_text = text
    for emoji, replacement in EMOJI_TO_TEXT.items():
        safe_text = safe_text.replace(emoji, replacement)
    
    return safe_text

class UnicodeLogger:
    """Unicode-safe logger for Windows systems"""
    
    def __init__(self, name: str, log_file: str = None, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Configure formatter
        formatter = logging.Formatter()
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        
        # Console handler with UTF-8 encoding
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # For Windows, try to set UTF-8 encoding
        if sys.platform.startswith('win'):
            try:
                # Try to set console to UTF-8
                os.system('chcp 65001 > nul')
            except:
                pass
        
        self.logger.addHandler(console_handler)
          # File handler if specified
        if log_file:
            try:
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            except Exception as e:
                print(f"Warning: Could not create file handler: {e}")
    
    def _safe_log(self, level, message, *args, **kwargs):
        """Log message with Unicode safety"""
        try:
            # Convert message to Unicode-safe text
            safe_message = unicode_safe_text(str(message))
            
            # Ensure the message can be encoded in the system's default encoding
            try:
                # Try to encode with the console's encoding first
                console_encoding = sys.stdout.encoding or 'utf-8'
                safe_message.encode(console_encoding, errors='replace')
            except (UnicodeEncodeError, AttributeError):
                # Fallback to ASCII-safe encoding
                safe_message = safe_message.encode('ascii', errors='ignore').decode('ascii')
            
            # Convert args to Unicode-safe text
            safe_args = []
            for arg in args:
                safe_arg = unicode_safe_text(str(arg))
                try:
                    safe_arg.encode(console_encoding, errors='replace')
                except (UnicodeEncodeError, AttributeError):
                    safe_arg = safe_arg.encode('ascii', errors='ignore').decode('ascii')
                safe_args.append(safe_arg)
            
            # Log with safe text
            getattr(self.logger, level)(safe_message, *safe_args, **kwargs)
        except Exception as e:
            # Fallback to basic logging
            try:
                fallback_message = f"[LOG_ERROR] {str(message)[:100]}..."
                # Ensure fallback message is also safe                fallback_message = fallback_message.encode('ascii', errors='ignore').decode('ascii')
                getattr(self.logger, level)(fallback_message)
            except:
                print(f"Critical logging error: {e}")
    
    def debug(self, message, *args, **kwargs):
        self._safe_log('debug', message, *args, **kwargs)
    
    def info(self, message, *args, **kwargs):
        self._safe_log('info', message, *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        self._safe_log('warning', message, *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        self._safe_log('error', message, *args, **kwargs)
    
    def critical(self, message, *args, **kwargs):
        self._safe_log('critical', message, *args, **kwargs)

def safe_print(message: str, level: str = 'INFO'):
    """Safe print function that handles Unicode issues on Windows"""
    try:
        # Convert emojis to text
        safe_message = unicode_safe_text(str(message))
        
        # Try to encode with console encoding
        console_encoding = sys.stdout.encoding or 'utf-8'
        try:
            safe_message.encode(console_encoding, errors='replace')
        except (UnicodeEncodeError, AttributeError):
            # Fallback to ASCII
            safe_message = safe_message.encode('ascii', errors='ignore').decode('ascii')
        
        print(f"[{level}] {safe_message}")
    except Exception as e:
        # Ultimate fallback
        try:
            ascii_message = str(message).encode('ascii', errors='ignore').decode('ascii')
            print(f"[{level}] {ascii_message}")
        except:
            print(f"[{level}] [MESSAGE_ENCODING_ERROR]")

def get_unicode_safe_logger(name: str, log_file: str = None, level: int = logging.INFO) -> UnicodeLogger:
    """Get a Unicode-safe logger instance"""
    return UnicodeLogger(name, log_file, level)

# Example usage
if __name__ == "__main__":
    logger = get_unicode_safe_logger("test", "test.log")
    logger.info("[INIT] Testing Unicode safety")
    logger.error("[ERROR] This should work on Windows")
    logger.warning("[WARN] No more encoding errors")
    logger.info("[OK] All emojis converted to text")