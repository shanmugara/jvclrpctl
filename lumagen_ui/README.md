# Lumagen + JVC Web UI

Unified Flask web control panel for the Lumagen Radiance Pro (USB serial) and JVC D-ILA projector (TCP/IP). Designed to run as a systemd service on Raspberry Pi and be accessed from any browser on the local network, including phones and tablets.

![Web UI](../web_ui.png)

## Pages

### Lumagen (`/`)
Power, input selection (1–8), configuration memory (A–D), aspect ratio, zoom, output resolution, test patterns, save config, Lumagen status, and HDR automation control.

### JVC Projector (`/jvc`)
Power, HDMI input, picture mode (Film / Cinema / Natural / HDR / THX / HLG / Frame Adapt / User 1–6), and projector status query.

**Both power buttons (ON and OFF) on both pages show a confirmation dialog before executing**, preventing accidental triggers.

### HDR Automation
A background thread polls the Lumagen every 30 seconds for HDR vs SDR content detection and automatically switches the JVC picture mode. Start/stop controls are on the Lumagen page.

---

## Requirements

- Raspberry Pi (any model with USB)
- USB-A to USB-B cable connecting Lumagen RS-232 port to Pi
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

The install script creates `/etc/systemd/system/lumagen-ui.service` and enables it. Key commands:

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

---

## API Endpoints

### Lumagen
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/power/<on\|standby>` | Power control |
| POST | `/api/input/<1-8>` | Select input |
| POST | `/api/memory/<A\|B\|C\|D>` | Select memory |
| POST | `/api/aspect/<4:3\|lbox\|16:9\|1.85\|2.35\|nls>` | Aspect ratio |
| POST | `/api/zoom/<in\|out>` | Zoom |
| POST | `/api/output/<480p\|720p\|1080p24\|1080p\|4k24\|4k60\|auto>` | Output mode |
| POST | `/api/test-pattern/<contrast\|off>` | Test pattern |
| POST | `/api/save` | Save config |
| GET  | `/api/status` | Lumagen status |

### HDR Automation
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/automation/status` | Running state + current content mode |
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
├── lumagen_control.py   # Lumagen serial command wrapper
├── jvc_control.py       # JVC TCP command wrapper
├── lumagen-ui.service   # systemd service template
├── install.sh / uninstall.sh
├── templates/
│   ├── index.html       # Lumagen control page
│   └── jvc.html         # JVC control page
└── static/
    ├── style.css        # Shared dark theme
    ├── script.js        # Lumagen page JS
    └── jvc_script.js    # JVC page JS
```

A single serial lock (`lumagen_lock`) serialises all Lumagen serial access between the automation background thread and Flask request handlers, preventing port conflicts.

---

## Keyboard Shortcuts (Lumagen page)

| Key | Action |
|-----|--------|
| `1`–`8` | Select input |
| `A`–`D` | Select memory |
| `+` / `=` | Zoom in |
| `-` / `_` | Zoom out |
| `Ctrl+S` | Save config |
