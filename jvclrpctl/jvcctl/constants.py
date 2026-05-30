"""
Constants and command codes for JVC projector control
Based on JVC D-ILA External Command Communication Specification Ver. 1.2
"""

# Connection defaults
DEFAULT_PORT = 20554
DEFAULT_TIMEOUT = 15
BAUDRATE = 19200  # For RS-232C

# Protocol characters
HEADER_OPERATION = b'!'
HEADER_REFERENCE = b'?'
HEADER_RESPONSE = b'@'
HEADER_ACK = b'\x06'
UNIT_ID = b'\x89\x01'  # Default unit ID
END_MARKER = b'\x0A'  # Line feed
AUTH_COMMAND =  b'PJREQ_' + b'\x00' * 16 # 3 way handshake with empty password

# Power commands
CMD_POWER = b'PW'
POWER_OFF = b'0'
POWER_ON = b'1'

# Input selection commands
CMD_INPUT = b'IP'
INPUT_HDMI_1 = b'6'
INPUT_HDMI_2 = b'7'

# Picture mode commands
CMD_PICTURE_MODE = b'PMPM'

# Picture mode values (ASCII representation as returned by JVC)
# From JVC spec Table 4-19: Values are sent as ASCII characters
# Example: USER3 = "0E" (ASCII chars '0' and 'E', hex 0x30 0x45)
class PictureModes:
    """Picture mode command values (ASCII)"""
    FILM = b'00'          # 0x30 0x30
    CINEMA = b'01'        # 0x30 0x31
    NATURAL = b'03'       # 0x30 0x33
    HDR = b'04'           # 0x30 0x34 (HDR10)
    THX = b'06'           # 0x30 0x36
    FRAME_ADAPT_HDR = b'0B'  # 0x30 0x42
    USER1 = b'0C'         # 0x30 0x43
    USER2 = b'0D'         # 0x30 0x44
    USER3 = b'0E'         # 0x30 0x45
    USER4 = b'0F'         # 0x30 0x46
    USER5 = b'10'         # 0x31 0x30
    USER6 = b'11'         # 0x31 0x31
    HLG = b'14'           # 0x31 0x34

# LAN setup commands
CMD_LAN = b'LS'
LAN_DHCP = b'DS'
LAN_IP = b'IP'
LAN_SUBNET = b'SM'
LAN_GATEWAY = b'DG'
LAN_MAC = b'MA'
LAN_PORT = b'PT'
LAN_RESTART = b'RS'

# Response codes
ACK = b'\x06'
PJACK = b'PJACK'
PJNAK = b'PJNAK'
PJ_OK = b'PJ_OK'
