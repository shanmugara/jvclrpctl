# Raspberry Pi Setup Guide

End-to-end walkthrough for installing the Lumagen + JVC Web UI on a Raspberry Pi — from a blank SD card to a running service.

---

## What You Need

**Hardware**
- Raspberry Pi 4 or 5 (recommended) — or Pi 3B+ for a budget option
- MicroSD card, 8 GB minimum (16 GB+ recommended)
- USB-A to USB-B cable (standard "printer" cable) — for Lumagen serial connection
- Ethernet cable — to put the Pi on the same network as the JVC projector or WiFi works too
- 5V power supply (Pi 4/5: USB-C; Pi 3: micro-USB)

**On your computer**
- [Raspberry Pi Imager](https://www.raspberrypi.com/software/) for writing the OS
- An SSH client (Terminal on macOS/Linux; PuTTY or Windows Terminal on Windows)

---

## 1. Flash Raspberry Pi OS

1. Open **Raspberry Pi Imager**.
2. Click **Choose Device** → select your Pi model.
3. Click **Choose OS** → **Raspberry Pi OS (other)** → **Raspberry Pi OS Lite (64-bit)**.
   - Lite = no desktop. This Pi will run headless as a server.
4. Click **Choose Storage** → select your SD card.
5. Click **Next** → **Edit Settings** and configure:

   | Field | Value |
   |-------|-------|
   | Hostname | `lumagen` (or whatever you like) |
   | Username | your preferred username (e.g. `frodo`) |
   | Password | a strong password |
   | WiFi SSID/password | fill in if not using Ethernet |
   | Enable SSH | Yes — use password authentication |
   | Locale / timezone | set to match your location |

6. Click **Save** → **Yes** to apply → **Yes** to write.
7. When imaging is complete, eject the card and insert it into the Pi.

---

## 2. Hardware Connections

### Lumagen Radiance Pro → Raspberry Pi

The Lumagen communicates over RS-232 exposed through its rear **USB port** (USB-B connector). When plugged into the Pi, Linux enumerates it as a USB serial device.

1. Connect a **USB-A to USB-B cable** from any USB port on the Pi to the **USB** port on the back of the Lumagen.
2. Power on both devices.
3. After the Pi boots, verify the device appeared:
   ```bash
   ls /dev/ttyUSB*
   ```
   You should see `/dev/ttyUSB0` (or `/dev/ttyUSB1` if another USB-serial device is also connected). Note this — the installer will ask for it.

> **Baud rate**: The Lumagen serial interface runs at **9600 8N1**. This is handled by the library; you do not need to configure it manually.

### JVC D-ILA Projector → Network

The JVC projector has a **LAN** port on its rear panel. Connect it to the same switch or router as the Raspberry Pi.

**Assign the projector a static IP** so the Pi can always find it:

1. On the JVC remote, press **Menu**.
2. Navigate to **Function** → **Network** → **Network Setup** (exact path varies by model).
3. Set **DHCP** to **Off**.
4. Enter a static IP (e.g. `192.168.100.240`), subnet mask, and gateway to match your network.
5. Save and exit.

Verify connectivity from the Pi once it's running:
```bash
ping 192.168.100.240
nc -zv 192.168.100.240 20554   # port 20554 is the JVC control port
```

> **Note**: The JVC LAN control port is **20554 TCP**. Make sure nothing on your network is blocking it.

---

## 3. First Boot

1. Insert the SD card, connect Ethernet and power. The Pi will boot in about 30–60 seconds.
2. Find its IP address. If you set the hostname to `lumagen`:
   ```bash
   ping lumagen.local        # works on most home networks (mDNS)
   ```
   Or check your router's DHCP leases. You can also use the IP address of the Pi instead of the hostname.
3. SSH in:
   ```bash
   ssh frodo@lumagen.local
   ```
4. Update the system before installing anything:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

---

## 4. Copy the Project to the Pi

**Git clone the project**
```bash
# On the Pi
git clone https://github.com/shanmugara/jvclrpctl.git
```

---

## 5. Run the Installer

```bash
cd ~/jvclrpctl/lumagen_ui
sudo ./install.sh
```

The installer will prompt for:

| Prompt | What to enter |
|--------|---------------|
| Lumagen serial port | `/dev/ttyUSB0` (confirm with `ls /dev/ttyUSB*` first) |
| JVC projector IP | e.g. `192.168.100.240` — whatever you set in step 2 |
| Web UI port | `5001` (default) |
| Config file path | accept the default |
| Enable HDR automation on startup? | `Y` to auto-switch JVC picture modes; `N` for remote-control-only |
| HDR picture mode | e.g. `USER3` |
| SDR picture mode | e.g. `USER1` |

The installer will then:
- Install `python3-pip` and `python3-venv` via `apt`
- Create a Python virtual environment under `lumagen_ui/venv/`
- Install all Python dependencies including Gunicorn
- Add your user to the `dialout` group (required for serial port access)
- Write `config.json` with your settings
- Create and enable the `lumagen-ui` systemd service
- Start the service immediately

When it finishes you will see:
```
✓ Service is running!

  Web UI:  http://192.168.x.x:5001
  Config:  /home/frodo/jvclrpctl/lumagen_ui/config.json
  Logs:    journalctl -u lumagen-ui -f
```

> **Serial port group**: The `dialout` group change takes effect on next login. The installer starts the service as your user, which already has the new group for this session. If you later SSH in and see permission errors, log out and back in.

---

## 6. Verify Everything Is Working

**Service status**
```bash
sudo systemctl status lumagen-ui
```

**Live logs**
```bash
sudo journalctl -u lumagen-ui -f
```

**Web UI** — open a browser on any device on the same network:
```
http://lumagen.local:5001
```

**Test Lumagen serial** — look for successful command responses in the logs when you press a button in the UI.

**Test JVC** — go to the JVC page (`/jvc`) and try a picture mode change. If the projector is on, it should respond.

---

## 7. Service Management

```bash
sudo systemctl start   lumagen-ui   # start
sudo systemctl stop    lumagen-ui   # stop
sudo systemctl restart lumagen-ui   # restart
sudo systemctl enable  lumagen-ui   # auto-start on boot (already set by installer)
sudo systemctl disable lumagen-ui   # disable auto-start
sudo journalctl -u lumagen-ui -f    # live log tail
sudo journalctl -u lumagen-ui -n 50 # last 50 lines
```

---

## 8. Changing Settings Later

All settings are editable from the **Configuration** page at `http://lumagen.local:5001/config` — no need to re-run the installer. Changes take effect immediately and are saved to `config.json`.

To **enable or disable HDR automation** after installation, use the **Enable Automation** toggle on the Configuration page. Turning it off stops the background thread immediately and saves the preference so it stays off after a restart.

To edit the config file directly:
```bash
nano ~/jvclrpctl/lumagen_ui/config.json
sudo systemctl restart lumagen-ui
```

---

## 9. Troubleshooting

### Cannot reach the web UI

```bash
# Is the service running?
sudo systemctl status lumagen-ui

# Is port 5001 open?
sudo ss -tlnp | grep 5001

# Is a firewall blocking it?
sudo ufw status
sudo ufw allow 5001/tcp   # if ufw is active
```

### Lumagen serial errors / commands not working

```bash
# Confirm device is present
ls -l /dev/ttyUSB*

# Check what the kernel saw when you plugged it in
dmesg | grep -i usb | tail -20

# Permission check
groups   # should include 'dialout'
```

If `dialout` is missing from your groups, log out and back in (the installer added you but the running session predates the change).

### Cannot connect to JVC

```bash
# Basic reachability
ping 192.168.100.240

# Port check — should respond (connection refused or open, not timeout)
nc -zv 192.168.100.240 20554

# Wrong IP? Check the config
cat ~/jvclrpctl/lumagen_ui/config.json
```

JVC LAN control must be **enabled** in the projector's network menu. Some models call it "Network Standby" or "LAN Control" — ensure it is set to On.

### Enable debug logging

```bash
sudo systemctl edit lumagen-ui
```
Add:
```ini
[Service]
Environment="DEBUG=true"
```
Then:
```bash
sudo systemctl daemon-reload && sudo systemctl restart lumagen-ui
sudo journalctl -u lumagen-ui -f
```

---

## 10. Keeping the System Updated

**Update the OS**
```bash
sudo apt update && sudo apt upgrade -y
```

**Update the project**
```bash
cd ~/jvclrpctl
git pull https://github.com/shanmugara/jvclrpctl.git
```
Then restart the service:
```bash
sudo systemctl restart lumagen-ui
```
