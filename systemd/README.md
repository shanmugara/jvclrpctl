# Systemd Service for Raspberry Pi

This directory contains the systemd service configuration for running JVC-LRP Runner automatically on a Raspberry Pi.

## Quick Start

### Installation

On your Raspberry Pi, run:

```bash
cd ~/jvclrpctl/systemd
./install.sh
```

The script will:
- ✓ Detect your paths automatically
- ✓ Install the service file
- ✓ Add you to the dialout group (for serial port access)
- ✓ Optionally enable auto-start on boot
- ✓ Optionally start the service immediately

### View Logs

```bash
# Follow logs in real-time
sudo journalctl -u jvc-lrp-runner.service -f

# View last 50 lines
sudo journalctl -u jvc-lrp-runner.service -n 50
```

### Control the Service

```bash
# Check status
sudo systemctl status jvc-lrp-runner.service

# Stop/Start/Restart
sudo systemctl stop jvc-lrp-runner.service
sudo systemctl start jvc-lrp-runner.service
sudo systemctl restart jvc-lrp-runner.service
```

### Uninstallation

```bash
cd ~/jvclrpctl/systemd
./uninstall.sh
```

## Files

- **jvc-lrp-runner.service** - Systemd unit file template
- **install.sh** - Automated installation script
- **uninstall.sh** - Automated uninstall script

## Documentation

For detailed information, see:
- [docs/SYSTEMD_SERVICE.md](../docs/SYSTEMD_SERVICE.md) - Complete systemd service documentation
- [docs/RASPBERRY_PI_SETUP.md](../docs/RASPBERRY_PI_SETUP.md) - Raspberry Pi setup guide

## Features

- ✓ Auto-starts on boot
- ✓ Restarts automatically on failure
- ✓ Runs as your user (no root required)
- ✓ Logs to systemd journal (view with journalctl)
- ✓ Waits for network to be ready
- ✓ Environment variable support (DEBUG mode)

## Enable Debug Mode

Edit the service file and uncomment the DEBUG line:

```bash
sudo nano /etc/systemd/system/jvc-lrp-runner.service
```

Change:
```ini
#Environment="DEBUG=true"
```

To:
```ini
Environment="DEBUG=true"
```

Then reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart jvc-lrp-runner.service
```

## Troubleshooting

If the service doesn't start:

1. Check the logs:
   ```bash
   sudo journalctl -u jvc-lrp-runner.service -n 100
   ```

2. Verify the service status:
   ```bash
   sudo systemctl status jvc-lrp-runner.service
   ```

3. Test manually:
   ```bash
   cd ~/jvclrpctl
   source venv/bin/activate
   python runner/runner.py
   ```

4. Check serial port permissions:
   ```bash
   groups  # Should show 'dialout'
   ls -l /dev/ttyUSB*  # Should be accessible
   ```

If you just added the dialout group, log out and back in, or reboot.
