"""
Color-coded logger for jvclrpctl
Provides colored console output for different log levels
"""

import os
import sys
from enum import IntEnum
from typing import Optional


# Discover DEBUG mode from environment variable
DEBUG = os.getenv('DEBUG', 'false').lower() in ('true', '1', 'yes')


class LogLevel(IntEnum):
    """Log level enumeration"""
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40


class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class Logger:
    """Simple color-coded logger that outputs to stdout"""
    
    def __init__(self, enabled: bool = True, level: LogLevel = LogLevel.INFO):
        self.enabled = enabled
        self.level = level
    
    def _format_message(self, prefix: str, color: str, message: str) -> str:
        """Format a message with color and prefix"""
        return f"{color}{Colors.BOLD}[{prefix}]{Colors.RESET}{color} {message}{Colors.RESET}"
    
    def _log(self, prefix: str, color: str, message: str, level: LogLevel):
        """Internal log method"""
        if self.enabled and level >= self.level:
            formatted = self._format_message(prefix, color, message)
            print(formatted, file=sys.stdout)
            sys.stdout.flush()
    
    def info(self, message: str):
        """Log an info message (green)"""
        self._log("INFO", Colors.GREEN, message, LogLevel.INFO)
    
    def debug(self, message: str):
        """Log a debug message (yellow)"""
        self._log("DEBUG", Colors.YELLOW, message, LogLevel.DEBUG)
    
    def warn(self, message: str):
        """Log a warning message (yellow)"""
        self._log("WARN", Colors.YELLOW, message, LogLevel.WARN)
    
    def error(self, message: str):
        """Log an error message (red)"""
        self._log("ERROR", Colors.RED, message, LogLevel.ERROR)
    
    def raw(self, message: str):
        """Print a raw message without formatting (for headers, separators, etc.)"""
        if self.enabled:
            print(message, file=sys.stdout)
            sys.stdout.flush()


# Global logger instance
_logger: Optional[Logger] = None


def _get_initial_log_level() -> LogLevel:
    """Get initial log level based on DEBUG setting"""
    return LogLevel.DEBUG if DEBUG else LogLevel.INFO


def get_logger() -> Logger:
    """Get the global logger instance"""
    global _logger
    if _logger is None:
        _logger = Logger(level=_get_initial_log_level())
    return _logger


def set_logger_enabled(enabled: bool):
    """Enable or disable logging globally"""
    global _logger
    if _logger is None:
        _logger = Logger(enabled=enabled)
    else:
        _logger.enabled = enabled


def set_log_level(level: LogLevel):
    """
    Set the minimum log level to display
    
    Args:
        level: LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, or LogLevel.ERROR
        
    Example:
        >>> set_log_level(LogLevel.DEBUG)  # Show all messages including debug
        >>> set_log_level(LogLevel.INFO)   # Hide debug, show info and above (default)
        >>> set_log_level(LogLevel.ERROR)  # Only show errors
    """
    global _logger
    if _logger is None:
        _logger = Logger(level=level)
    else:
        _logger.level = level


# Convenience functions for direct access
def info(message: str):
    """Log an info message"""
    get_logger().info(message)


def debug(message: str):
    """Log a debug message"""
    get_logger().debug(message)


def warn(message: str):
    """Log a warning message"""
    get_logger().warn(message)


def error(message: str):
    """Log an error message"""
    get_logger().error(message)


def raw(message: str):
    """Print a raw message without formatting"""
    get_logger().raw(message)
