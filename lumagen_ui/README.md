# Lumagen + JVC Web UI

Unified Flask web control panel for the Lumagen Radiance Pro (USB serial) and JVC D-ILA projector (TCP/IP). Designed to run as a systemd service on a Raspberry Pi and be accessed from any browser on the local network, including phones and tablets.

## Pages

### Lumagen (`/`)

The Lumagen page is organised into six tabs to avoid screen clutter:

| Tab | Contents |
|-----|----------|
| **Control** | Power on/standby, input selection (1–8), configuration memory (A–D), zoom, output resolution, HDR automation |
| **Navigate** | On-screen menu D-pad (▲▼◀▶ + OK in centre), MENU corner button, pill-shaped PREV/EXIT, OSD on/off, number pad (0–9) |
| **Aspect** | Standard aspects (4:3 / LBOX / 16:9 / 1.85 / 2.35 / NLS), extended Pro aspects (1.90 / 2.00 / 2.20 / 2.40), no-zoom variants, auto-aspect enable/disable/reset |
| **Patterns** | Full test pattern library with IRE slider — Geometry (Crosshatch, Overscan, H/V Lines), Calibration (Contrast 1/2, Ramp, Clip, Targets…), Color (Bars, solid R/G/B/Y/C/M, gray windows) |
| **Status** | Rich parsed live status — source resolution/rate/HDR/aspect, output mode/format/colorspace/CMS/style, device model/firmware/serial, game mode. Manual refresh or auto-refresh every 5 s |
| **Settings** | Game mode toggle, HDMI hotplug per input (1–8 + All), sharpness (enable/level 0–7/sensitivity), output format (YCbCr 4:2:2 / 4:4:4 / RGB / Auto), CMS/Style selector (ZY530, K or 0–7 per field), PIP controls, deinterlacing mode, **Save to Flash** |

Both the Lumagen Power ON and Standby buttons show a confirmation dialog before executing.

### JVC Projector (`/jvc`)

Power, HDMI input selection, picture mode (Film / Cinema / Natural / HDR / THX / HLG / Frame Adapt / User 1–6), and projector status.

### HDR Automation

A background thread polls the Lumagen every 30 seconds for HDR vs SDR content and automatically switches the JVC picture mode. The start/stop toggle and current content mode are shown in the **Control** tab.

---

## Requirements

- Raspberry Pi (any model with USB)
- USB-A to USB-B cable connecting the Lumagen RS-232 port to the Pi
- JVC projector on the local network with network control enabled
- Python 3.7+ with `flask`, `gunicorn`, `pyserial`

---

## Installation

Use the provided install script:

```bash
cd lumagen_ui
chmod +x install.sh
./install.sh
```

The script prompts for install directory, venv path, serial port, and JVC IP, then installs the systemd service.

### Manual setup

```bash
pip install -r requirements.txt
```

Configure via environment variables:

```bash
export LUMAGEN_PORT=/dev/ttyUSB0   # default
export JVC_HOST=192.168.100.240
```

Run directly:

```bash
python app.py
# or with gunicorn (production)
gunicorn --workers 1 --bind 0.0.0.0:5001 app:app
```

Access at `http://<pi-ip>:5001`

---

## systemd Service

The install script creates `/etc/systemd/system/lumagen-ui.service` and enables it.

```bash
sudo systemctl status lumagen-ui.service
sudo systemctl restart lumagen-ui.service
sudo journalctl -u lumagen-ui.service -f      # live logs
```

To enable debug logging, uncomment `Environment="DEBUG=true"` in the service file and restart.

---

## Serial Port

The Lumagen connects at **9600 baud** via USB serial. Find your port:

```bash
ls /dev/ttyUSB*
```

Add your user to the `dialout` group if permission is denied:

```bash
sudo usermod -a -G dialout $USER
# then log out and back in
```

A single serial lock (`lumagen_lock`) serialises all Lumagen serial access between the automation background thread and Flask request handlers, preventing port conflicts.

---

## API Endpoints

### Lumagen — Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/power/<on\|standby>` | Power on / standby |
| POST | `/api/input/<1-8>` | Select input |
| POST | `/api/memory/<A\|B\|C\|D>` | Select memory |
| POST | `/api/zoom/<in\|out>` | Zoom |
| POST | `/api/output/<480p\|720p\|1080p24\|1080p\|4k24\|4k60\|auto>` | Output resolution |
| POST | `/api/save` | Save config to flash |

### Lumagen — Navigation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/navigate/<action>` | `menu` `exit` `ok` `up` `down` `left` `right` `prev` `osd_on` `osd_off` `digit_0`–`digit_9` |

### Lumagen — Aspect

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/aspect/<aspect>` | Standard: `4:3` `lbox` `16:9` `1.85` `2.35` `nls` |
| POST | `/api/aspect/<aspect>` | Extended Pro: `1.90` `2.00` `2.20` `2.40` |
| POST | `/api/aspect/<aspect>` | No-zoom: `4:3nz` `lboxnz` `16:9nz` `1.85nz` `2.35nz` |
| POST | `/api/aspect/<aspect>` | Auto-aspect: `auto_on` `auto_off` `auto_reset` |

### Lumagen — Test Patterns

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/test-pattern/<contrast\|off>` | Legacy single-pattern shortcut |
| POST | `/api/test-pattern-full` | Full library — JSON body `{"group":"b","sub":0,"ire":100}` |

### Lumagen — Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | Raw ZQI24 / ZQS01 / ZQI00 strings |
| GET | `/api/rich-status` | Parsed status — source, output, device fields as JSON |

### Lumagen — Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/game-mode` | Query game mode |
| POST | `/api/game-mode/<0\|1>` | Set game mode off/on |
| POST | `/api/hdmi-hotplug/<1-8\|all>` | Pulse HDMI hotplug to force EDID re-read |
| GET | `/api/sharpness` | Query sharpness (ZQI30) |
| POST | `/api/sharpness` | Set sharpness — JSON `{"enabled":true,"level":4,"sensitivity":"N"}` |
| GET | `/api/output-format` | Query output format (ZQO18) |
| POST | `/api/output-format/<fmt>` | Set format — `0`=YCbCr 4:2:2 `1`=4:4:4 `2`=RGB Video `3`=RGB PC `8`=Auto Max `9`=Auto |
| POST | `/api/cms-style` | Set CMS/Style — JSON `{"mode":"K","cms_sdr":"K","cms_hdr":"K","style":"K"}` (`K`=keep) |
| POST | `/api/pip/<off\|select\|swap\|mode>` | PIP control |
| GET | `/api/deinterlace` | Query deinterlace mode (ZQI15) |
| POST | `/api/deinterlace/<0\|1\|2>` | Set deinterlace — `0`=Auto `1`=Film `2`=Video |

### HDR Automation

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/automation/status` | Running state + current content mode (HDR/SDR/NA) |
| POST | `/api/automation/start` | Start background polling |
| POST | `/api/automation/stop` | Stop background polling |

### JVC

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/jvc/power/<on\|off>` | Power on/off |
| POST | `/api/jvc/input/<hdmi1\|hdmi2>` | Select input |
| POST | `/api/jvc/picture-mode/<mode>` | Set picture mode |
| GET  | `/api/jvc/status` | Power, input, picture mode |

---

## Architecture

```
lumagen_ui/
├── app.py               # Flask app + all API routes + AutomationManager
├── lumagen_control.py   # Lumagen RS232 command wrapper (all commands)
├── jvc_control.py       # JVC TCP command wrapper
├── lumagen-ui.service   # systemd service template
├── install.sh / uninstall.sh
├── templates/
│   ├── index.html       # Lumagen page (6-tab layout)
│   └── jvc.html         # JVC page
└── static/
    ├── style.css        # Shared dark theme + tab/d-pad/status styles
    ├── script.js        # Lumagen page JS
    └── jvc_script.js    # JVC page JS
```

---

## Keyboard Shortcuts (Lumagen page)

| Key | Action |
|-----|--------|
| `1`–`8` | Select input |
| `A`–`D` | Select memory |
| `+` / `=` | Zoom in |
| `-` / `_` | Zoom out |
| `Ctrl+S` | Save config to flash |
| `Arrow keys` | Navigate D-pad (up/down/left/right) |
| `Enter` | OK / Accept |
| `M` | Open Lumagen menu |
