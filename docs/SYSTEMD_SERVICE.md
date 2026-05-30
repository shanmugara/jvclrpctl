# Systemd Service Setup for Raspberry Pi

This guide explains how to set up the JVC-LRP Runner as a systemd service that starts automatically on Raspberry Pi boot.

## Prerequisites

- Raspberry Pi 3 (or newer)
- Raspbian/Raspberry Pi OS
- User account: `speriya`
- Project installed at: `/home/speriya/jvclrpctl`
- Python virtual environment at: `/home/speriya/jvclrpctl/venv`

## Installation

### 1. Copy the service file

```bash
sudo cp systemd/jvc-lrp-runner.service /etc/systemd/system/
```

### 2. Update the service file (if needed)

If your installation path is different from `/home/speriya/jvclrpctl`, edit the service file:

```bash
sudo nano /etc/systemd/system/jvc-lrp-runner.service
```

Update these lines:
- `User=` - Your username
- `WorkingDirectory=` - Path to your project
- `Environment="PATH=..."` - Path to your venv/bin
- `ExecStart=` - Full paths to python and runner.py

### 3. Enable debug mode (optional)

To enable debug logging, uncomment this line in the service file:

```ini
Environment="DEBUG=true"
```

### 4. Reload systemd

```bash
sudo systemctl daemon-reload
```

### 5. Enable the service to start on boot

```bash
sudo systemctl enable jvc-lrp-runner.service
```

### 6. Start the service now

```bash
sudo systemctl start jvc-lrp-runner.service
```

## Managing the Service

### Check service status

```bash
sudo systemctl status jvc-lrp-runner.service
```

### View logs in real-time

```bash
# Follow logs (like tail -f)
sudo journalctl -u jvc-lrp-runner.service -f

# Follow logs with color
sudo journalctl -u jvc-lrp-runner.service -f --output=cat
```

### View recent logs

```bash
# Last 50 lines
sudo journalctl -u jvc-lrp-runner.service -n 50

# Last 100 lines
sudo journalctl -u jvc-lrp-runner.service -n 100

# All logs from today
sudo journalctl -u jvc-lrp-runner.service --since today
```

### Stop the service

```bash
sudo systemctl stop jvc-lrp-runner.service
```

### Restart the service

```bash
sudo systemctl restart jvc-lrp-runner.service
```

### Disable auto-start on boot

```bash
sudo systemctl disable jvc-lrp-runner.service
```

## Troubleshooting

### Service won't start

1. Check the status for errors:
   ```bash
   sudo systemctl status jvc-lrp-runner.service
   ```

2. Check the full logs:
   ```bash
   sudo journalctl -u jvc-lrp-runner.service -n 100
   ```

3. Verify paths in the service file:
   ```bash
   cat /etc/systemd/system/jvc-lrp-runner.service
   ```

4. Test the command manually:
   ```bash
   cd /home/speriya/jvclrpctl
   source venv/bin/activate
   python runner/runner.py
   ```

### Permission issues

If you get permission errors, ensure:

1. The user `speriya` owns the project directory:
   ```bash
   sudo chown -R speriya:speriya /home/speriya/jvclrpctl
   ```

2. The virtual environment is accessible:
   ```bash
   ls -la /home/speriya/jvclrpctl/venv/bin/python
   ```

### Serial port access

If the service can't access serial ports (Lumagen connection), add the user to the dialout group:

```bash
sudo usermod -a -G dialout speriya
```

Then reboot or restart the service:
```bash
sudo reboot
```

### Network not ready

If the service starts before the network is ready, it will automatically retry due to `Restart=on-failure` and `RestartSec=10` settings.

## Service Configuration

### Key settings in the service file

- **User=speriya** - Runs as user speriya
- **Restart=on-failure** - Automatically restarts if it crashes
- **RestartSec=10** - Waits 10 seconds before restarting
- **After=network-online.target** - Waits for network to be ready
- **StandardOutput=journal** - Logs to systemd journal (viewable with journalctl)
- **PYTHONUNBUFFERED=1** - Ensures logs appear immediately

### Environment variables

You can add more environment variables in the service file:

```ini
Environment="DEBUG=true"
Environment="PROJECTOR_IP=192.168.1.100"
Environment="LUMAGEN_PORT=/dev/ttyUSB0"
```

## Viewing Logs on Console/TTY

To view logs on a console (TTY), you can:

### Option 1: SSH and follow logs

```bash
ssh speriya@raspberrypi.local
sudo journalctl -u jvc-lrp-runner.service -f
```

### Option 2: Console on boot

If you want to see logs on the physical console during boot, you can enable a getty service that shows logs:

```bash
# This will show all system logs on TTY1
sudo systemctl enable getty@tty1.service
```

### Option 3: Auto-display logs on login

Add to `/home/speriya/.bashrc`:

```bash
# Show JVC-LRP Runner logs on login
if systemctl is-active --quiet jvc-lrp-runner.service; then
    echo "=== JVC-LRP Runner Status ==="
    sudo journalctl -u jvc-lrp-runner.service -n 20 --no-pager
    echo ""
fi
```

## Uninstall

To completely remove the service:

```bash
# Stop and disable the service
sudo systemctl stop jvc-lrp-runner.service
sudo systemctl disable jvc-lrp-runner.service

# Remove the service file
sudo rm /etc/systemd/system/jvc-lrp-runner.service

# Reload systemd
sudo systemctl daemon-reload
```

## Additional Notes

### Auto-login Setup

If you want the Raspberry Pi to auto-login as `speriya`, run:

```bash
sudo raspi-config
```

Then navigate to:
- System Options → Boot / Auto Login → Console Autologin

### Running with polling

To use the polling function instead of single run, modify the service file's `ExecStart` line to use a custom script.

Create `/home/speriya/jvclrpctl/runner/start_polling.py`:

```python
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from runner.runner import JVC_LRP_Runner, poll

runner = JVC_LRP_Runner()
poll(runner, interval=2)  # Poll every 2 seconds
```

Then update the service file:
```ini
ExecStart=/home/speriya/jvclrpctl/venv/bin/python /home/speriya/jvclrpctl/runner/start_polling.py
```

## Support

For more information, see:
- [Raspberry Pi Setup Guide](RASPBERRY_PI_SETUP.md)
- [Project README](../README.md)
