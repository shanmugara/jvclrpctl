"""
Example: Using DEBUG in your own module
Shows how any module can import and use the global DEBUG variable
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import DEBUG and logger functions
from jvclrpctl import DEBUG, info, debug, warn

def connect_to_device(host: str, port: int):
    """Example function that uses DEBUG"""
    info(f"Connecting to {host}:{port}")
    
    # Debug messages only show when DEBUG=true
    debug(f"Connection details: host={host}, port={port}, timeout=5s")
    debug("Establishing TCP socket...")
    debug("Sending handshake...")
    
    info("Connected successfully!")

def process_data(data: dict):
    """Another example function"""
    if DEBUG:
        # You can also check DEBUG flag directly
        debug(f"Processing data: {data}")
    
    info(f"Processed {len(data)} items")

if __name__ == "__main__":
    print(f"\n=== Module Example ===")
    print(f"DEBUG = {DEBUG}\n")
    
    connect_to_device("192.168.1.100", 20554)
    print()
    
    process_data({"item1": "value1", "item2": "value2"})
    
    print(f"\nTo see debug messages, run:")
    print(f"  DEBUG=true python {__file__}")
