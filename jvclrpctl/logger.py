"""
Color-coded logger for jvclrpctl
Provides colored console output for different log levels
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
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
    """Simple color-coded logger that outputs to stdout and optionally to file with daily rotation"""
    
    def __init__(self, enabled: bool = True, level: LogLevel = LogLevel.INFO, log_dir: Optional[str] = None):
        self.enabled = enabled
        self.level = level
        self.file_handler = None
        self.file_logger = None
        
        # Set up file logging if log_dir is provided
        if log_dir is not None:
            self._setup_file_logging(log_dir)
    
    def _setup_file_logging(self, log_dir: str):
        """Set up file logging with daily rotation"""
        try:
            # Create log directory if it doesn't exist
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            
            # Set up Python's logging with TimedRotatingFileHandler
            # Creates a new file every 24 hours (midnight)
            log_file = log_path / "jvclrpctl.log"
            self.file_handler = logging.handlers.TimedRotatingFileHandler(
                filename=str(log_file),
                when='midnight',  # Rotate at midnight
                interval=1,       # Every 1 day
                backupCount=30,   # Keep 30 days of logs
                encoding='utf-8'
            )
            
            # Set up formatter for file output (without colors)
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            self.file_handler.setFormatter(formatter)
            
            # Create a logger for file output
            self.file_logger = logging.getLogger('jvclrpctl')
            self.file_logger.setLevel(logging.DEBUG)  # Capture all levels, filter in _log
            self.file_logger.addHandler(self.file_handler)
            self.file_logger.propagate = False  # Don't propagate to root logger
            
        except (OSError, PermissionError) as e:
            # If we can't create the log directory or file, just continue without file logging
            # Print to stderr instead of using self.error() since logger isn't fully initialized
            print(f"Warning: Failed to set up file logging in {log_dir}: {e}", file=sys.stderr)
            self.file_handler = None
            self.file_logger = None
    
    def _format_message(self, prefix: str, color: str, message: str) -> str:
        """Format a message with color and prefix"""
        return f"{color}{Colors.BOLD}[{prefix}]{Colors.RESET}{color} {message}{Colors.RESET}"
    
    def _log(self, prefix: str, color: str, message: str, level: LogLevel):
        """Internal log method"""
        if self.enabled and level >= self.level:
            # Console output with colors
            formatted = self._format_message(prefix, color, message)
            print(formatted, file=sys.stdout)
            sys.stdout.flush()
            
            # File output without colors (if file logging is enabled)
            if self.file_logger is not None:
                # Map our LogLevel to Python's logging levels
                log_level_map = {
                    LogLevel.DEBUG: logging.DEBUG,
                    LogLevel.INFO: logging.INFO,
                    LogLevel.WARN: logging.WARNING,
                    LogLevel.ERROR: logging.ERROR
                }
                py_level = log_level_map.get(level, logging.INFO)
                self.file_logger.log(py_level, message)
    
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
_default_log_dir: str = "/var/log/jvclrpctl"


def _get_initial_log_level() -> LogLevel:
    """Get initial log level based on DEBUG setting"""
    return LogLevel.DEBUG if DEBUG else LogLevel.INFO


def get_logger(log_dir: Optional[str] = None) -> Logger:
    """
    Get the global logger instance
    
    Args:
        log_dir: Directory for log files. If None, uses the default /var/log/jvclrpctl.
                 Pass False to disable file logging.
                 
    Returns:
        Logger instance
    """
    global _logger
    if _logger is None:
        # Use default log directory unless explicitly disabled
        effective_log_dir = _default_log_dir if log_dir is None else log_dir
        if effective_log_dir is False:
            effective_log_dir = None
        _logger = Logger(level=_get_initial_log_level(), log_dir=effective_log_dir)
    return _logger


def set_logger_enabled(enabled: bool):
    """Enable or disable logging globally"""
    global _logger
    if _logger is None:
        _logger = Logger(enabled=enabled, log_dir=_default_log_dir)
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
        _logger = Logger(level=level, log_dir=_default_log_dir)
    else:
        _logger.level = level


def set_log_dir(log_dir: str):
    """
    Set or change the log directory for file logging
    
    Args:
        log_dir: Directory path for log files, or None to disable file logging
        
    Example:
        >>> set_log_dir("/var/log/jvclrpctl")
        >>> set_log_dir("/custom/log/path")
        >>> set_log_dir(None)  # Disable file logging
    """
    global _logger, _default_log_dir
    _default_log_dir = log_dir if log_dir is not None else ""
    
    if _logger is not None:
        # Re-initialize file logging with new directory
        if _logger.file_handler is not None:
            _logger.file_handler.close()
            if _logger.file_logger is not None:
                _logger.file_logger.removeHandler(_logger.file_handler)
        
        if log_dir is not None:
            _logger._setup_file_logging(log_dir)
        else:
            _logger.file_handler = None
            _logger.file_logger = None


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
