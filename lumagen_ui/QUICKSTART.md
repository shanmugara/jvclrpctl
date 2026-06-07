# Lumagen Web UI - Quick Start Guide

## What is This?

A browser-based control interface for your Lumagen Radiance Pro video processor, running on your Raspberry Pi. Access it from any device on your network - phone, tablet, laptop!

## Quick Setup (5 minutes)

### 1. Install on Raspberry Pi

```bash
cd /path/to/jvclrpctl/lumagen_ui
sudo ./install.sh
```

### 2. Configure Serial Port

Find your Lumagen's serial port:
```bash
ls -l /dev/ttyUSB*
```

Edit `app.py` and set the port (around line 14):
```python
LUMAGEN_PORT = '/dev/ttyUSB1'  # Change this to your port
```

### 3. Start the Service

```bash
sudo systemctl start lumagen-ui.service
```

### 4. Open in Browser

Find your Pi's IP address:
```bash
hostname -I
```

Open your browser to: `http://YOUR_PI_IP:5001`

Example: `http://192.168.1.100:5001`

## Features at a Glance

### Main Controls
- **Power**: On/Standby
- **Inputs**: Quick switch between sources (1-10)
- **Memories**: Switch between A/B/C/D configurations
- **Aspect Ratios**: 4:3, Letterbox, 16:9, 1.85, 2.35, NLS

### Advanced
- **Output Resolution**: Set 480p, 720p, 1080p, 4K (24/60Hz), or Auto
- **Zoom**: Zoom in/out controls
- **Test Patterns**: Display calibration patterns
- **Save**: Persist your settings

### Status
- Real-time status display
- Current input and configuration info
- Connection status indicator

## Keyboard Shortcuts

- `1-8`: Switch to input 1-8
- `A, B, C, D`: Select memory A, B, C, or D
- `+`: Zoom in
- `-`: Zoom out
- `Ctrl+S`: Save configuration

## Common Tasks

### Change Input Source
1. Click the input button (e.g., "Input 1")
2. Wait for confirmation
3. Done!

### Switch HDR Configuration
1. Click "MEM C" (or your HDR memory)
2. Lumagen will switch to HDR settings
3. Click "💾 Save Configuration" to persist

### Set Output Resolution
1. Click desired resolution (e.g., "4K60")
2. Or use "Auto" for automatic detection
3. Save if you want to keep this setting

### View Current Status
1. Click "📊 Get Status"
2. View detailed info in the status box
3. See current input, resolution, and more

## Troubleshooting

### Can't access web UI
- Check Pi is on: `ping YOUR_PI_IP`
- Check service: `sudo systemctl status lumagen-ui.service`
- Check firewall: `sudo ufw allow 5001/tcp`

### Commands not working
- Verify serial connection: `ls -l /dev/ttyUSB*`
- Check logs: `sudo journalctl -u lumagen-ui.service -f`
- Restart service: `sudo systemctl restart lumagen-ui.service`

### Permission denied on serial port
- Add user to dialout: `sudo usermod -a -G dialout $USER`
- Log out and back in
- Restart service

## Service Management

Start service:
```bash
sudo systemctl start lumagen-ui.service
```

Stop service:
```bash
sudo systemctl stop lumagen-ui.service
```

Restart service:
```bash
sudo systemctl restart lumagen-ui.service
```

View logs:
```bash
sudo journalctl -u lumagen-ui.service -f
```

Enable auto-start on boot:
```bash
sudo systemctl enable lumagen-ui.service
```

## Integration Notes

This web UI runs **independently** from the main jvclrpctl automation:

- **Main jvclrpctl**: Automatic HDR/SDR detection and JVC switching
- **Lumagen Web UI**: Manual control of Lumagen settings

Both can run at the same time without conflicts (they use different serial ports).

## Mobile Access

The web UI is responsive and works great on mobile:

1. Connect phone/tablet to same network as Pi
2. Open browser
3. Navigate to `http://YOUR_PI_IP:5001`
4. Add to home screen for quick access

## Security Note

The web UI has no authentication. It's designed for use on a trusted home network. If you need security:

1. Use firewall rules to restrict access
2. Consider setting up a VPN
3. Or add authentication to Flask app

## Getting Help

- Check logs: `sudo journalctl -u lumagen-ui.service -f`
- See full README: `lumagen_ui/README.md`
- Verify Lumagen connection and baud rate (115200)

## Uninstall

To remove the service:
```bash
cd /path/to/jvclrpctl/lumagen_ui
sudo ./uninstall.sh
```

This stops the service but keeps your files for reference.
