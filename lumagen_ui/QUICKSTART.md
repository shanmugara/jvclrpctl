# Lumagen + JVC Web UI — Quick Start

## What is This?

A browser-based control panel for your Lumagen Radiance Pro video processor (and JVC projector), running as a service on your Raspberry Pi. Works on phone, tablet, and desktop — no app required.

---

## Quick Setup (5 minutes)

### 1. Install on Raspberry Pi

```bash
cd /path/to/jvclrpctl/lumagen_ui
sudo ./install.sh
```

The installer will ask for your install directory, venv path, serial port, and JVC IP.

### 2. Confirm Serial Port

The Lumagen connects at **9600 baud** via USB serial. Find your port:
```bash
ls -l /dev/ttyUSB*
```

Override the default (`/dev/ttyUSB0`) with an environment variable in the systemd service file:
```ini
Environment="LUMAGEN_PORT=/dev/ttyUSB1"
```

### 3. Start the Service

```bash
sudo systemctl start lumagen-ui.service
sudo systemctl enable lumagen-ui.service   # auto-start on boot
```

### 4. Open in Browser

```bash
hostname -I   # find your Pi's IP
```

Open: `http://YOUR_PI_IP:5001`

---

## Features at a Glance

The Lumagen page is split into **six tabs** to keep things organised:

| Tab | What you can do |
|-----|-----------------|
| **Control** | Power on/standby, select input 1–8, switch memory A–D, zoom, output resolution, start/stop HDR automation |
| **Navigate** | D-pad (▲▼◀▶) with OK in the centre, MENU corner button, pill-shaped PREV/EXIT, OSD on/off, number pad 0–9 |
| **Aspect** | Standard ratios (4:3 / LBOX / 16:9 / 1.85 / 2.35 / NLS), extended Pro (1.90 / 2.00 / 2.20 / 2.40), no-zoom variants, auto-aspect on/off/reset |
| **Patterns** | Full test pattern library with IRE slider — Geometry, Calibration, Color. Exit Pattern button to dismiss |
| **Status** | Live parsed status — source resolution/rate/HDR, output mode/format/colorspace/CMS/style, device info. Refresh manually or enable auto-refresh (every 5 s) |
| **Settings** | Game mode, HDMI hotplug, sharpness, output format, CMS/Style (ZY530), PIP, deinterlacing, **Save to Flash** |

The JVC page is at `http://YOUR_PI_IP:5001/jvc` — power, HDMI input, and picture mode.

---

## Keyboard Shortcuts (Lumagen page)

| Key | Action |
|-----|--------|
| `1`–`8` | Switch to input 1–8 |
| `A`–`D` | Select memory A, B, C, or D |
| `+` / `=` | Zoom in |
| `-` / `_` | Zoom out |
| `Ctrl+S` | Save configuration to flash |
| `Arrow keys` | Navigate OSD (up / down / left / right) |
| `Enter` | OK / Accept in OSD |
| `M` | Open Lumagen menu |

---

## Common Tasks

### Navigate the Lumagen On-Screen Menu

1. Go to the **Navigate** tab
2. Press **MENU** (corner button) to open the menu
3. Use ▲▼◀▶ to move, **OK** to select
4. Press **EXIT** to back out one level, or **PREV** to go back

You can also use keyboard arrow keys, Enter, and M once the Navigate tab is open.

### Change Input Source

1. Go to **Control** tab
2. Click the input button (e.g. **Input 1**)
3. Done — no confirmation needed

### Switch Aspect Ratio

1. Go to **Aspect** tab
2. Click the ratio — standard, extended Pro, no-zoom, or auto-aspect controls

### Run a Test Pattern

1. Go to **Patterns** tab
2. Adjust the **IRE slider** (0–100) to set white level
3. Click any pattern button (Crosshatch, Contrast, Color Bars, etc.)
4. Click **Exit Pattern** when done

### Check What the Lumagen is Seeing

1. Go to **Status** tab
2. Click **Refresh** (or enable **Auto-refresh**)
3. Source section shows: input, resolution, frame rate, HDR/SDR, aspect ratio, scan type
4. Output section shows: output mode, resolution/rate, colorspace, CMS slot, style

### Change CMS or Style

1. Go to **Settings** tab → CMS / Style section
2. Click the desired slot for each field (Mode, CMS-SDR, CMS-HDR, Style) — **K** means "keep current"
3. Click **Apply CMS / Style**

### Save Settings to Flash

1. Go to **Settings** tab (scroll to bottom)
2. Click **Save to Flash** — this persists all Lumagen settings across power cycles

### Toggle Game Mode

1. Go to **Settings** tab → Game Mode section
2. Click **On** or **Off**

---

## Troubleshooting

### Can't access the web UI
```bash
ping YOUR_PI_IP
sudo systemctl status lumagen-ui.service
sudo ufw allow 5001/tcp   # if firewall is enabled
```

### Commands not working / serial errors
```bash
ls -l /dev/ttyUSB*
sudo journalctl -u lumagen-ui.service -f
sudo systemctl restart lumagen-ui.service
```

### Permission denied on serial port
```bash
sudo usermod -a -G dialout $USER
# log out and back in, then restart the service
```

### Debug logging
Edit `/etc/systemd/system/lumagen-ui.service`, uncomment:
```ini
Environment="DEBUG=true"
```
Then: `sudo systemctl daemon-reload && sudo systemctl restart lumagen-ui.service`

---

## Service Management

```bash
sudo systemctl start   lumagen-ui.service
sudo systemctl stop    lumagen-ui.service
sudo systemctl restart lumagen-ui.service
sudo systemctl status  lumagen-ui.service
sudo journalctl -u lumagen-ui.service -f    # live logs
```

---

## Integration Notes

The web UI and the background HDR automation **share the same serial port**. A threading lock (`lumagen_lock`) ensures only one caller talks to the Lumagen at a time, so running both simultaneously is safe.

- **HDR automation** (Control tab): polls Lumagen every 30 s and auto-switches the JVC picture mode
- **Manual controls** (all tabs): send commands on demand; automation pauses momentarily while the lock is held

---

## Mobile Access

The UI is designed for mobile — minimum 44 px touch targets, horizontally scrolling tab bar, responsive layout.

1. Connect phone/tablet to the same network as the Pi
2. Navigate to `http://YOUR_PI_IP:5001`
3. Add to home screen (iOS: Share → Add to Home Screen)

---

## Security Note

No authentication is built in — designed for a trusted home network. To restrict access, use firewall rules or a VPN.

---

## Uninstall

```bash
cd /path/to/jvclrpctl/lumagen_ui
sudo ./uninstall.sh
```

---

## Getting Help

```bash
sudo journalctl -u lumagen-ui.service -f   # service logs
```

Full reference: `lumagen_ui/README.md`
