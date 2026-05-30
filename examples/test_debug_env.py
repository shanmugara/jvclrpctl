"""
Test DEBUG environment variable
This script demonstrates how DEBUG is automatically discovered from the environment
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jvclrpctl import DEBUG, info, debug, warn, error

print(f"\n=== DEBUG Environment Variable Test ===")
print(f"DEBUG environment variable: {os.getenv('DEBUG', 'not set')}")
print(f"DEBUG module variable: {DEBUG}")
print(f"Log level: {'DEBUG' if DEBUG else 'INFO'}\n")

info("This info message is always visible")
debug("This debug message is only visible when DEBUG=true")
warn("This warning is always visible")
error("This error is always visible")

print(f"\nTo enable debug mode, run:")
print(f"  DEBUG=true python examples/test_debug_env.py")
