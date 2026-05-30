"""
Simple example showing log level control
Run with DEBUG_MODE=True to see debug messages
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jvclrpctl import info, debug, warn, error, set_log_level, LogLevel

# Example 1: Default behavior (INFO level - debug hidden)
print("\n=== Example 1: Default (INFO level) ===")
info("Application started")
debug("This debug message is HIDDEN")
warn("This warning is visible")
error("This error is visible")

# Example 2: Enable debug mode
print("\n=== Example 2: Debug Mode (DEBUG level) ===")
set_log_level(LogLevel.DEBUG)
info("Application started")
debug("This debug message is NOW VISIBLE")
debug("Connection details: host=192.168.1.100, port=20554")
warn("This warning is visible")
error("This error is visible")

# Example 3: Quiet mode (only errors)
print("\n=== Example 3: Quiet Mode (ERROR level) ===")
set_log_level(LogLevel.ERROR)
info("This info is HIDDEN")
debug("This debug is HIDDEN")
warn("This warning is HIDDEN")
error("Only errors show up")

# Example 4: Using environment variable
print("\n=== Example 4: Using environment variable ===")
import os
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

if DEBUG:
    set_log_level(LogLevel.DEBUG)
    info("Debug mode enabled via environment")
else:
    set_log_level(LogLevel.INFO)
    info("Normal mode")

debug("This only shows if DEBUG=true environment variable is set")
