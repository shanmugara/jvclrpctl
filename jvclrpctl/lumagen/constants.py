"""
Constants and command codes for Lumagen Radiance control
Based on Radiance Tech Tip 11 RS232 Command Interface
"""

import enum

import serial

# Serial connection defaults
DEFAULT_BAUDRATE = 9600
DEFAULT_BYTESIZE = serial.EIGHTBITS
DEFAULT_PARITY = serial.PARITY_NONE
DEFAULT_STOPBITS = serial.STOPBITS_ONE
DEFAULT_TIMEOUT = 2.0

# Query commands - Input status
CMD_QUERY_INPUT_BASIC = b'ZQI00'  # Basic input info
CMD_QUERY_INPUT_VIDEO = b'ZQI01'  # Input video details
CMD_QUERY_INPUT_ASPECT = b'ZQI20'  # Input aspect ratio
CMD_QUERY_FULL_STATUS_V2 = b'ZQI22'  # Full status v2 (includes HDR flag)
CMD_QUERY_FULL_STATUS_V3 = b'ZQI23'  # Full status v3 (includes HDR flag)
CMD_QUERY_FULL_STATUS_V4 = b'ZQI24'  # Full status v4 (most comprehensive)
CMD_QUERY_HDR_STATUS = b'ZQI52'  # HDR status query

# Query commands - Output status
CMD_QUERY_OUTPUT_BASIC = b'ZQO00'  # Basic output info
CMD_QUERY_OUTPUT_MODE = b'ZQO01'  # Output mode details

# Query commands - System
CMD_QUERY_ALIVE = b'ZQS00'  # Check if alive
CMD_QUERY_ID = b'ZQS01'  # Device ID and firmware
CMD_QUERY_POWER = b'ZQS02'  # Power status

# Control commands
CMD_POWER_ON = b'%'
CMD_POWER_STANDBY = b'$'
CMD_MENU = b'M'
CMD_EXIT = b'X'

# Set commands
CMD_SET_OUTPUT_MODE = b'ZY530'  # Set output mode, CMS, style

# Response markers
RESPONSE_PREFIX = b'!'
RESPONSE_TERMINATOR = b'\x0d\x0a'  # <CR><LF>

# HDR status values (from F field in ZQI22/23/24)
HDR_STATUS_SDR = 0
HDR_STATUS_HDR = 1

class LRPInputModes(enum.Enum):
    """HDR mode values for ZQI22/23/24 F field"""
    SDR = 0
    HDR = 1
    NA = 2  # Not applicable (e.g., no input)
    ERR = 3  # Error retrieving status