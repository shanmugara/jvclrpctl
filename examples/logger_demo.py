"""
Logger Demo - Color-coded logging example
Demonstrates the use of the color-coded logger in jvclrpctl
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jvclrpctl.logger import get_logger, info, debug, warn, error, raw, set_logger_enabled, set_log_level, LogLevel

def main():
    """Demonstrate logger functionality"""
    
    # Get logger instance
    logger = get_logger()
    
    # Header
    raw("=" * 60)
    raw("JVClrpctl Logger Demo")
    raw("=" * 60)
    raw("")
    
    # Info messages (green with [INFO] prefix)
    logger.info("This is an info message")
    info("Connection successful!")
    info("Picture mode set to USER3")
    raw("")
    
    # Debug messages (yellow with [DEBUG] prefix)
    # Note: Debug messages won't show by default (level is INFO)
    logger.debug("This is a debug message (won't show yet)")
    debug("Sending command: 0x21 0x89 0x01 0x50 0x57 0x30 0x0A (won't show yet)")
    raw("")
    
    # Warning messages (yellow with [WARN] prefix)
    logger.warn("This is a warning message")
    warn("HDR status unchanged")
    warn("Retrying connection...")
    raw("")
    
    # Error messages (red with [ERROR] prefix)
    logger.error("This is an error message")
    error("Connection failed: timeout")
    error("Failed to set picture mode")
    raw("")
    
    # Demonstrate log levels
    raw("=" * 60)
    raw("Log Level Control Demo")
    raw("=" * 60)
    raw("")
    
    raw("Default level is INFO - debug messages are hidden")
    info("Info message - visible")
    debug("Debug message - HIDDEN")
    raw("")
    
    raw("Setting log level to DEBUG - all messages will show")
    set_log_level(LogLevel.DEBUG)
    info("Info message - visible")
    debug("Debug message - NOW VISIBLE!")
    debug("Sending command: 0x21 0x89 0x01 0x50 0x57 0x30 0x0A")
    raw("")
    
    raw("Setting log level to WARN - only warnings and errors")
    set_log_level(LogLevel.WARN)
    info("Info message - HIDDEN")
    debug("Debug message - HIDDEN")
    warn("Warning message - visible")
    error("Error message - visible")
    raw("")
    
    raw("Setting log level to ERROR - only errors")
    set_log_level(LogLevel.ERROR)
    info("Info message - HIDDEN")
    warn("Warning message - HIDDEN")
    error("Error message - visible")
    raw("")
    
    # Reset to INFO
    set_log_level(LogLevel.INFO)
    raw("=" * 60)
    raw("Log level reset to INFO")
    raw("=" * 60)
    raw("")
    
    # Disable logging
    raw("=" * 60)
    raw("Disabling logger...")
    set_logger_enabled(False)
    
    info("This message won't appear")
    warn("Neither will this")
    error("Or this")
    
    # Re-enable logging
    set_logger_enabled(True)
    raw("Logger re-enabled!")
    raw("=" * 60)
    info("Logger is back!")
    raw("")
    
    # Usage example
    raw("Usage in your code:")
    raw("  from jvclrpctl import info, debug, warn, error, set_log_level, LogLevel")
    raw("")
    raw("  # Set log level to DEBUG to see debug messages")
    raw("  set_log_level(LogLevel.DEBUG)")
    raw("  debug('This will now be visible')")
    raw("")
    raw("  # Default is INFO - hides debug messages")
    raw("  set_log_level(LogLevel.INFO)")
    raw("  info('Operation successful')")
    raw("  debug('This is hidden')")
    raw("")
    
    raw("=" * 60)
    raw("Demo completed")
    raw("=" * 60)


if __name__ == "__main__":
    main()
