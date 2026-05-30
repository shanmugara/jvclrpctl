# macOS USB Serial Connection Guide

## Yes! Your Mac works perfectly with Lumagen USB connection

macOS has full support for USB serial devices via the pyserial library.

## Finding Your Lumagen Serial Port on macOS

### When Lumagen is Connected

```bash
# List all USB serial devices
ls /dev/cu.* | grep -iE "usb|serial"

# Common port names on macOS:
# /dev/cu.usbserial
# /dev/cu.usbserial-<unique-id>
# /dev/cu.usbmodem<number>
```

### Alternative Method

```bash
# Before connecting Lumagen
ls /dev/cu.* > /tmp/before.txt

# Connect Lumagen USB cable

# After connecting
ls /dev/cu.* > /tmp/after.txt

# See what was added
diff /tmp/before.txt /tmp/after.txt
```

### Using System Information

1. Click  (Apple menu) → **About This Mac**
2. Click **System Report**
3. Under **Hardware**, select **USB**
4. Look for your USB-to-Serial device

## Quick Test

Once you find your port (e.g., `/dev/cu.usbserial`):

```python
from jvclrpctl import LumagenRadiance, LumagenCommands

# Replace with your actual port
LUMAGEN_PORT = "/dev/cu.usbserial"

with LumagenRadiance(LUMAGEN_PORT) as radiance:
    commands = LumagenCommands(radiance)
    
    # Test connection
    is_hdr = commands.is_hdr()
    print(f"Connection successful! HDR: {is_hdr}")
```

## Example Configuration

Edit `examples/hdr_automation.py`:

```python
# macOS Configuration
JVC_IP = "192.168.1.100"                    # Your JVC projector IP
LUMAGEN_PORT = "/dev/cu.usbserial"          # Your Mac serial port
POLL_INTERVAL = 2.0
```

## Testing from Terminal

```bash
# Activate venv (if not already active)
source venv/bin/activate

# Test Lumagen connection
cd examples
python test_lumagen.py
```

## Common macOS Serial Port Names

| Device Type | Port Name |
|------------|-----------|
| Generic USB-Serial | `/dev/cu.usbserial` |
| FTDI Adapter | `/dev/cu.usbserial-<ID>` |
| Silicon Labs | `/dev/cu.SLAB_USBtoUART` |
| Prolific | `/dev/cu.PL2303-<ID>` |
| USB Modem | `/dev/cu.usbmodem<number>` |

## Troubleshooting

### Port Not Found

1. **Check USB cable is connected** (USB-A to USB-B)
2. **Check Lumagen is powered on**
3. **Try different USB port** on your Mac
4. **List all devices**: `ls /dev/cu.*`

### Permission Issues (rare on macOS)

macOS usually handles serial port permissions automatically, but if needed:

```bash
# Check permissions
ls -l /dev/cu.usbserial*

# Should show: crw-rw-rw-  (world readable/writable)
```

### Driver Installation (if needed)

Some USB-to-serial adapters may require drivers:

- **FTDI**: Usually built into macOS
- **Silicon Labs CP210x**: [Download from Silicon Labs](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers)
- **Prolific PL2303**: [Download from Prolific](http://www.prolific.com.tw/US/ShowProduct.aspx?p_id=229&pcid=41)

Most modern USB devices work without additional drivers on macOS.

## Why Use Your Mac?

✅ **Development**: Test and develop on your Mac  
✅ **Debugging**: Easy access to console output  
✅ **Quick Tests**: Faster iteration than Raspberry Pi  
✅ **Built-in Screen**: See output immediately  

## Production Deployment

While your Mac works great for development and testing, for 24/7 automation consider:

- **Raspberry Pi**: Dedicated, always-on, low-power
- **Mac Mini**: If you have one that's always on
- **Your Mac**: If it stays on near your theater

## Example Workflow

1. **Develop on Mac**: Write and test code on your Mac
2. **Test with Hardware**: Connect Lumagen via USB to Mac
3. **Deploy to Pi**: Copy working code to Raspberry Pi for 24/7 operation

```bash
# Copy project to Raspberry Pi from Mac
scp -r ~/PycharmProjects/jvclrpctl pi@raspberrypi.local:~/
```

## Running on macOS

### Manual Start

```bash
cd ~/PycharmProjects/jvclrpctl/examples
source ../venv/bin/activate
python hdr_automation.py
```

### Keep Running (using screen)

```bash
# Start screen session
screen -S jvc-automation

# Run your script
cd ~/PycharmProjects/jvclrpctl/examples
source ../venv/bin/activate
python hdr_automation.py

# Detach: Press Ctrl+A, then D

# Reattach later
screen -r jvc-automation
```

### macOS LaunchAgent (Auto-start on login)

Create `~/Library/LaunchAgents/com.jvc.automation.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jvc.automation</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/speriya/PycharmProjects/jvclrpctl/venv/bin/python</string>
        <string>/Users/speriya/PycharmProjects/jvclrpctl/examples/hdr_automation.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/speriya/PycharmProjects/jvclrpctl/examples</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/speriya/Library/Logs/jvc-automation.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/speriya/Library/Logs/jvc-automation-error.log</string>
</dict>
</plist>
```

Load the agent:

```bash
# Load agent
launchctl load ~/Library/LaunchAgents/com.jvc.automation.plist

# Check status
launchctl list | grep jvc

# Unload
launchctl unload ~/Library/LaunchAgents/com.jvc.automation.plist

# View logs
tail -f ~/Library/Logs/jvc-automation.log
```

## Summary

✅ **Yes, your Mac works perfectly!**  
✅ **Port**: Usually `/dev/cu.usbserial*`  
✅ **No special configuration needed**  
✅ **Great for development and testing**  
✅ **Can run 24/7 if Mac stays on**  

Just connect the Lumagen via USB-A to USB-B cable, find the port with `ls /dev/cu.* | grep usb`, and update your configuration!
