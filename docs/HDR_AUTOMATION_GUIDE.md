# HDR Automation Setup Guide

## Overview

This project now supports **automated HDR detection and JVC picture mode switching** by monitoring a Lumagen Radiance video processor via **USB serial connection** and controlling a JVC projector over the network.

## How It Works

1. **Lumagen Monitoring**: The automation polls your Lumagen Radiance via USB serial at regular intervals (default: 2 seconds)
2. **HDR Detection**: Checks the "F" field from the Lumagen status query (0=SDR, 1=HDR)
3. **JVC Control**: When content type changes, automatically switches JVC picture mode:
   - **SDR Content** → USER1 (or your configured mode)
   - **HDR Content** → USER2 (or your configured mode)

## Hardware Requirements

- **Lumagen Radiance**: Connected to your computer via USB-A to USB-B cable
- **JVC Projector**: Connected to your network (supports models: DLA-NX7, N8, V7, NX9, NX5, RS2000, etc.)

## Quick Start

### 1. Update Configuration

Edit the settings in `examples/hdr_automation.py`:

```python
JVC_IP = "192.168.1.100"              # Your JVC projector IP
LUMAGEN_PORT = "/dev/ttyUSB0"         # Your Lumagen serial port
                                       # Linux/Mac: /dev/ttyUSB0, /dev/cu.usbserial
                                       # Windows: COM3, COM4, etc.
POLL_INTERVAL = 2.0                    # Check every 2 seconds
```

#### Finding Your Serial Port

**Linux/Mac:**
```bash
ls /dev/tty* | grep -E 'USB|usbserial'
```

**Windows:**
Check Device Manager → Ports (COM & LPT)

**macOS Common Ports:**
- `/dev/cu.usbserial`
- `/dev/cu.usbserial-<id>`
- `/dev/tty.usbserial`

### 2. Run the Automation

```bash
cd examples
python hdr_automation.py
```

The script will:
- Connect to both devices
- Start monitoring in the background
- Display status updates when content type changes
- Continue running until you press Ctrl+C

### 3. Customize Picture Modes

You can change which picture modes are used for SDR and HDR:

```python
automation = HDRAutomation(
    jvc_ip=JVC_IP,
    lumagen_port=LUMAGEN_PORT,
    poll_interval=2.0,
    sdr_mode=PictureMode.CINEMA,    # Use CINEMA for SDR
    hdr_mode=PictureMode.HDR,        # Use HDR for HDR content
)
```

Available picture modes:
- `FILM`, `CINEMA`, `NATURAL`, `HDR`, `THX`
- `FRAME_ADAPT_HDR`, `HLG`
- `USER1` through `USER6`

## Project Structure

```
jvclrpctl/
├── jvclrpctl/
│   ├── automation.py          # ← HDR automation logic
│   ├── jvcctl/               # ← JVC-specific modules
│   │   ├── connection.py
│   │   ├── commands.py
│   │   ├── picture_modes.py
│   │   └── constants.py
│   └── lumagen/              # ← Lumagen-specific modules
│       ├── connection.py
│       ├── commands.py
│       └── constants.py
└── examples/
    ├── hdr_automation.py      # ← Main automation script
    ├── test_lumagen.py        # ← Test Lumagen connection
    ├── basic_control.py       # ← JVC control examples
    └── ...
```

## Testing Individual Components

### Test Lumagen Connection

```bash
cd examples
python test_lumagen.py
```

This will:
- Connect to Lumagen
- Query device information
- Check HDR status
- Display full status information

### Test JVC Control

```bash
cd examples
python picture_mode_control.py
```

This will:
- Connect to JVC projector
- Demonstrate picture mode switching
- Show available picture modes

## Advanced Usage

### Using as a Library

```python
from jvclrpctl import HDRAutomation, PictureMode

# Create automation with custom callback
def on_change(content_type, mode):
    print(f"Changed to {content_type}: {mode.display_name}")

automation = HDRAutomation(
    jvc_ip='192.168.1.100',
    lumagen_port='/dev/ttyUSB0',  # Serial port
    poll_interval=1.5,
    sdr_mode=PictureMode.USER1,
    hdr_mode=PictureMode.USER2,
    on_mode_change=on_change
)

# Start (runs in background thread)
automation.start()

# Check status
status = automation.get_status()
print(status)

# Stop when done
automation.stop()
```

### Context Manager

```python
from jvclrpctl import HDRAutomation, PictureMode

# Automatically stops when exiting the block
with HDRAutomation(
    jvc_ip='192.168.1.100',
    lumagen_port='/dev/ttyUSB0',  # Serial port
    poll_interval=2.0,
    sdr_mode=PictureMode.USER1,
    hdr_mode=PictureMode.USER2
) as automation:
    # Automation is now running
    import time
    time.sleep(60)  # Run for 1 minute
# Automatically stopped here
```

## Troubleshooting

### "Cannot connect to Lumagen" / "Serial port not found"
- Verify the USB cable is connected (USB-A to USB-B)
- Check the serial port path is correct (see "Finding Your Serial Port" above)
- On Linux, you may need permissions: `sudo usermod -a -G dialout $USER` (then logout/login)
- Try a different USB port on your computer
- Verify the baud rate is correct (default: 9600)

### "Permission denied" on Linux/Mac
- Add your user to the dialout group: `sudo usermod -a -G dialout $USER`
- Or run with sudo (not recommended for production)
- Check port permissions: `ls -l /dev/ttyUSB0`

### "Cannot connect to JVC"
- Verify JVC IP address
- Ensure network control is enabled on the projector
- Check port 20554 is accessible

### "Mode not switching"
- Check console output for error messages
- Verify both devices are connected
- Try increasing `poll_interval` to reduce network load

### "Delayed switching"
- Decrease `poll_interval` (minimum recommended: 1.0 second)
- Check network latency between devices

## Configuration File

You can create a configuration file for easy management:

```python
# config.py
from jvclrpctl import PictureMode

JVC_IP = "192.168.1.100"
LUMAGEN_PORT = "/dev/ttyUSB0"  # Update to your serial port
POLL_INTERVAL = 2.0
SDR_MODE = PictureMode.USER1
HDR_MODE = PictureMode.USER2
```

Then use it in your script:

```python
import config
from jvclrpctl import HDRAutomation

automation = HDRAutomation(
    jvc_ip=config.JVC_IP,
    lumagen_port=config.LUMAGEN_PORT,
    poll_interval=config.POLL_INTERVAL,
    sdr_mode=config.SDR_MODE,
    hdr_mode=config.HDR_MODE
)
automation.start()
```

## Running as a Service

For continuous operation, you can run the automation as a system service. See the documentation for your operating system on how to create a service that runs Python scripts.

## Support

For issues or questions:
1. Check the README.md for full API documentation
2. Review the JVC and Lumagen specification PDFs in the `docs/` folder
3. Examine the example scripts for usage patterns
