"""
Logger Demo - Color-coded logging example
Demonstrates the use of the color-coded logger in jvclrpctl
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jvclrpctl.logger import get_logger, info, warn, error, raw, set_logger_enabled

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
    
    # Raw messages (no prefix, no color)
    raw("Raw messages are useful for:")
    raw("  - Headers and separators")
    raw("  - Tables and formatted output")
    raw("  - Plain informational text")
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
    raw("  from jvclrpctl import info, warn, error")
    raw("  info('Operation successful')")
    raw("  warn('Low memory warning')")
    raw("  error('Connection timeout')")
    raw("")
    
    raw("=" * 60)
    raw("Demo completed")
    raw("=" * 60)


if __name__ == "__main__":
    main()
