# Raspberry Pi Setup Guide

## Hardware Requirements

- **Raspberry Pi 3** (Model B or B+)
- **MicroSD Card**: 8GB+ with Raspberry Pi OS
- **USB Cable**: USB-A to USB-B for Lumagen connection
- **Network**: Ethernet or WiFi for JVC projector access
- **Power**: 5V 2.5A power supply

## Software Installation

### 1. Update System

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Python and pip (if not already installed)

```bash
# Check Python version (should be 3.7+)
python3 --version

# Install pip if needed
sudo apt install python3-pip python3-venv -y
```

### 3. Clone or Copy Project

```bash
# Option A: If using git
git clone <your-repo-url> jvclrpctl
cd jvclrpctl

# Option B: Copy files via SCP from your Mac
# On your Mac:
# scp -r /Users/speriya/PycharmProjects/jvclrpctl pi@<raspberry-pi-ip>:~/
```

### 4. Create Virtual Environment

```bash
cd ~/jvclrpctl
python3 -m venv venv
source venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install pyserial
# Or install from requirements.txt
pip install -r requirements.txt
```

### 6. Serial Port Permissions

```bash
# Add your user to the dialout group (required for serial access)
sudo usermod -a -G dialout $USER

# Logout and login again for changes to take effect
# Or reboot:
sudo reboot
```

### 7. Find Your Serial Port

```bash
# List USB serial devices
ls -l /dev/ttyUSB* /dev/ttyACM*

# Or use dmesg to see what was detected
dmesg | grep tty

# Common ports on Raspberry Pi:
# - /dev/ttyUSB0 (USB-to-serial adapter)
# - /dev/ttyACM0 (USB device with CDC-ACM)
```

## Configuration

### 1. Update Configuration

Edit `examples/hdr_automation.py`:

```python
JVC_IP = "192.168.1.100"              # Your JVC IP
LUMAGEN_PORT = "/dev/ttyUSB0"         # Your Lumagen serial port
POLL_INTERVAL = 2.0
```

### 2. Test Connections

#### Test JVC Connection
```bash
cd examples
python basic_control.py
```

#### Test Lumagen Connection
```bash
python test_lumagen.py
```

## Running HDR Automation

### Manual Start

```bash
cd ~/jvclrpctl/examples
source ../venv/bin/activate
python hdr_automation.py
```

### Run as Systemd Service (Auto-start on boot)

Create service file:

```bash
sudo nano /etc/systemd/system/jvc-lumagen.service
```

Add this content:

```ini
[Unit]
Description=JVC Lumagen HDR Automation
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/jvclrpctl/examples
Environment="PATH=/home/pi/jvclrpctl/venv/bin"
ExecStart=/home/pi/jvclrpctl/venv/bin/python /home/pi/jvclrpctl/examples/hdr_automation.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable jvc-lumagen.service

# Start service now
sudo systemctl start jvc-lumagen.service

# Check status
sudo systemctl status jvc-lumagen.service

# View logs
sudo journalctl -u jvc-lumagen.service -f
```

### Service Management Commands

```bash
# Stop service
sudo systemctl stop jvc-lumagen.service

# Restart service
sudo systemctl restart jvc-lumagen.service

# Disable auto-start
sudo systemctl disable jvc-lumagen.service

# View recent logs
sudo journalctl -u jvc-lumagen.service -n 50
```

## Troubleshooting

### Serial Port Not Found

```bash
# Check if USB device is detected
lsusb

# Check kernel messages
dmesg | tail -20

# Verify port exists
ls -l /dev/ttyUSB* /dev/ttyACM*
```

### Permission Denied on Serial Port

```bash
# Check current groups
groups

# Add to dialout group (if not already)
sudo usermod -a -G dialout $USER

# Or temporarily change permissions (not recommended)
sudo chmod 666 /dev/ttyUSB0
```

### Cannot Connect to JVC

```bash
# Test network connectivity
ping 192.168.1.100

# Test if port is open
nc -zv 192.168.1.100 20554

# Check if firewall is blocking
sudo iptables -L
```

### Service Won't Start

```bash
# Check logs
sudo journalctl -u jvc-lumagen.service -n 50

# Test manually first
cd ~/jvclrpctl/examples
source ../venv/bin/activate
python hdr_automation.py

# Verify paths in service file
which python  # Should show venv path
```

### Memory/Performance Issues

```bash
# Check memory usage
free -h

# Check CPU usage
top

# The automation is very lightweight and should use <1% CPU
```

## Performance Notes

- **CPU Usage**: <1% (just polling every 2 seconds)
- **Memory**: ~30-50MB for Python + libraries
- **Network**: Minimal (small command packets)
- **Latency**: ~2 seconds (based on poll interval)

The Raspberry Pi 3's quad-core 1.2GHz processor is more than sufficient for this automation task.

## Network Configuration Tips

### Static IP for JVC (Recommended)

Configure your JVC projector with a static IP so the Raspberry Pi can always find it.

### WiFi Configuration

If using WiFi instead of Ethernet:

```bash
# Edit WiFi config
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf

# Add your network
network={
    ssid="YourNetworkName"
    psk="YourPassword"
}

# Restart WiFi
sudo systemctl restart dhcpcd
```

## Remote Access

### SSH Access

```bash
# Enable SSH (if not already enabled)
sudo systemctl enable ssh
sudo systemctl start ssh

# Connect from another computer
ssh pi@<raspberry-pi-ip>
```

### VNC Access (Optional)

```bash
# Enable VNC server
sudo raspi-config
# Navigate to: Interface Options → VNC → Enable
```

## Headless Operation

The Raspberry Pi can run this automation completely headless (no monitor, keyboard, or mouse needed) as a dedicated automation server. Just:

1. Configure the scripts once
2. Set up the systemd service
3. Reboot
4. The automation starts automatically on boot

## Power Management

For 24/7 operation:
- Raspberry Pi 3 uses ~2.5W idle, ~5W under load
- Very power efficient for continuous automation
- Consider a UPS for uninterrupted operation

## Backup & Updates

```bash
# Backup your configuration
cp examples/hdr_automation.py examples/hdr_automation.py.backup

# Update code
cd ~/jvclrpctl
git pull  # If using git

# Restart service
sudo systemctl restart jvc-lumagen.service
```

## Why Raspberry Pi is Perfect for This

✅ **Always On**: Can run 24/7 as a dedicated automation server  
✅ **Low Power**: ~2.5W power consumption  
✅ **Quiet**: Completely silent operation  
✅ **Small**: Fits anywhere in your theater  
✅ **Reliable**: Linux-based, very stable  
✅ **Affordable**: ~$35 for the board  
✅ **USB Ports**: 4 USB ports for multiple devices  
✅ **Network**: Built-in Ethernet + WiFi  

This is an ideal use case for a Raspberry Pi!
