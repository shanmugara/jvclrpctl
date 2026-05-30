"""
Color-coded logger for jvclrpctl
Provides colored console output for different log levels
"""

import sys
from typing import Optional


class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class Logger:
    """Simple color-coded logger that outputs to stdout"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
    
    def _format_message(self, prefix: str, color: str, message: str) -> str:
        """Format a message with color and prefix"""
        return f"{color}{Colors.BOLD}[{prefix}]{Colors.RESET}{color} {message}{Colors.RESET}"
    
    def _log(self, prefix: str, color: str, message: str):
        """Internal log method"""
        if self.enabled:
            formatted = self._format_message(prefix, color, message)
            print(formatted, file=sys.stdout)
            sys.stdout.flush()
    
    def info(self, message: str):
        """Log an info message (green)"""
        self._log("INFO", Colors.GREEN, message)
    
    def warn(self, message: str):
        """Log a warning message (yellow)"""
        self._log("WARN", Colors.YELLOW, message)
    
    def error(self, message: str):
        """Log an error message (red)"""
        self._log("ERROR", Colors.RED, message)
    
    def raw(self, message: str):
        """Print a raw message without formatting (for headers, separators, etc.)"""
        if self.enabled:
            print(message, file=sys.stdout)
            sys.stdout.flush()


# Global logger instance
_logger: Optional[Logger] = None


def get_logger() -> Logger:
    """Get the global logger instance"""
    global _logger
    if _logger is None:
        _logger = Logger()
    return _logger


def set_logger_enabled(enabled: bool):
    """Enable or disable logging globally"""
    global _logger
    if _logger is None:
        _logger = Logger(enabled)
    else:
        _logger.enabled = enabled


# Convenience functions for direct access
def info(message: str):
    """Log an info message"""
    get_logger().info(message)


def warn(message: str):
    """Log a warning message"""
    get_logger().warn(message)


def error(message: str):
    """Log an error message"""
    get_logger().error(message)


def raw(message: str):
    """Print a raw message without formatting"""
    get_logger().raw(message)
