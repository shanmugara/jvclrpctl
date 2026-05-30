# USB Serial Migration

## Overview

The Lumagen Radiance control has been updated to use **USB serial communication** instead of network/telnet, as the Lumagen only supports:
- Direct RS-232 serial connection
- USB connection via USB-A to USB-B cable

## What Changed

### 1. Connection Method
**Before (Network):**
```python
radiance = LumagenRadiance('192.168.1.50', 23)  # IP and port
```

**After (USB Serial):**
```python
radiance = LumagenRadiance('/dev/ttyUSB0')  # Serial port
```

### 2. Dependencies
Added `pyserial` library for USB serial communication:
```bash
pip install pyserial
```

### 3. Updated Files

#### Core Changes
- **`jvclrpctl/lumagen/connection.py`**
  - Replaced `socket` module with `serial` (pyserial)
  - Changed from TCP/IP connection to serial port connection
  - Updated default parameters (removed `host`/`port`, added `port` as serial port path)
  - Uses 9600 baud by default

- **`jvclrpctl/lumagen/constants.py`**
  - Removed `DEFAULT_PORT = 23` (network port)
  - Added serial settings: `DEFAULT_BAUDRATE`, `DEFAULT_BYTESIZE`, `DEFAULT_PARITY`, `DEFAULT_STOPBITS`

- **`jvclrpctl/automation.py`**
  - Changed `lumagen_ip` parameter to `lumagen_port` (serial port path)
  - Changed `lumagen_port` parameter to `lumagen_baudrate` (serial baud rate)
  - Updated connection initialization

#### Examples & Documentation
- **`examples/hdr_automation.py`** - Updated to use serial port
- **`examples/test_lumagen.py`** - Updated to use serial port
- **`config_example.py`** - Updated Lumagen config section
- **`README.md`** - Updated all examples and documentation
- **`docs/HDR_AUTOMATION_GUIDE.md`** - Complete rewrite for serial connection
- **`requirements.txt`** - Added pyserial dependency

## How to Find Your Serial Port

### macOS
```bash
ls /dev/cu.* | grep -i usb
# Common: /dev/cu.usbserial or /dev/cu.usbserial-<id>
```

### Linux
```bash
ls /dev/ttyUSB*
# Common: /dev/ttyUSB0, /dev/ttyUSB1
```

### Windows
Check **Device Manager → Ports (COM & LPT)**
- Common: COM3, COM4, COM5, etc.

## Updated Configuration Examples

### HDR Automation
```python
from jvclrpctl import HDRAutomation, PictureMode

automation = HDRAutomation(
    jvc_ip='192.168.1.100',           # JVC network IP
    lumagen_port='/dev/ttyUSB0',       # Lumagen USB serial port
    poll_interval=2.0,
    sdr_mode=PictureMode.USER1,
    hdr_mode=PictureMode.USER2
)
automation.start()
```

### Direct Lumagen Control
```python
from jvclrpctl import LumagenRadiance, LumagenCommands

with LumagenRadiance('/dev/ttyUSB0') as radiance:
    commands = LumagenCommands(radiance)
    is_hdr = commands.is_hdr()
    print(f"HDR: {is_hdr}")
```

## Hardware Requirements

- **USB Cable**: USB-A to USB-B cable (standard printer cable)
- **Lumagen Port**: Rear USB-B port on Lumagen Radiance
- **Computer Port**: USB-A port (or USB-C with adapter)

## Troubleshooting

### Permission Denied (Linux/Mac)
```bash
# Add your user to dialout group
sudo usermod -a -G dialout $USER
# Then logout and login again
```

### Port Not Found
- Verify USB cable is connected
- Check cable is USB-A to USB-B (not USB-C to USB-C)
- Try different USB port on computer
- List available ports: `ls /dev/tty* | grep -i usb`

### Communication Errors
- Verify baud rate is 9600 (Lumagen default)
- Check serial settings match Lumagen configuration
- Ensure no other program is using the serial port

## Migration Checklist

- [x] Updated Lumagen connection from network to serial
- [x] Added pyserial dependency
- [x] Updated all example scripts
- [x] Updated documentation
- [x] Updated configuration examples
- [x] Removed network-specific code (socket module)
- [x] Added serial port discovery instructions
- [x] Added troubleshooting guide

## Notes

- JVC projectors still use **network connection** (TCP/IP on port 20554)
- Only Lumagen uses USB serial connection
- Both devices can be controlled simultaneously in HDR automation
