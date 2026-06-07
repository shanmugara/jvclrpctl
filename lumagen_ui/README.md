# Lumagen Radiance Pro Web UI

A Flask-based web interface for controlling the Lumagen Radiance Pro video processor over RS232. Designed to run on Raspberry Pi and accessible via browser on your network.

## Features

- **Power Control**: Turn on/standby
- **Input Selection**: Switch between inputs 1-10
- **Memory Selection**: Choose configuration memories A, B, C, D
- **Aspect Ratio**: Set input aspect (4:3, LBOX, 16:9, 1.85, 2.35, NLS)
- **Zoom Control**: Zoom in/out
- **Output Resolution**: Set output mode (480p, 720p, 1080p, 4K, Auto)
- **Test Patterns**: Display and control test patterns
- **Configuration**: Save current settings
- **Status Display**: View current Lumagen status and info

## Hardware Requirements

- Raspberry Pi (any model with USB ports)
- USB-to-RS232 adapter
- Lumagen Radiance Pro with RS232 connection

## Installation

### 1. Install Dependencies

```bash
pip install flask pyserial
```

Or use the requirements file:

```bash
pip install -r requirements.txt
```

### 2. Configure Serial Port

Edit `app.py` to set your Lumagen serial port:

```python
LUMAGEN_PORT = '/dev/ttyUSB1'  # Change to your port
```

To find your serial port:

```bash
ls -l /dev/ttyUSB*
```

### 3. Set Permissions (Raspberry Pi)

Add your user to the dialout group:

```bash
sudo usermod -a -G dialout $USER
```

Then log out and back in.

### 4. Run the Application

```bash
python app.py
```

The web UI will be available at:
- Local: `http://localhost:5001`
- Network: `http://<raspberry-pi-ip>:5001`

## Running as a Service

To run the web UI automatically on boot, create a systemd service:

### 1. Create Service File

```bash
sudo nano /etc/systemd/system/lumagen-ui.service
```

Add this content (adjust paths):

```ini
[Unit]
Description=Lumagen Web UI
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/jvclrpctl/lumagen_ui
Environment="PATH=/home/pi/jvclrpctl/venv/bin"
ExecStart=/home/pi/jvclrpctl/venv/bin/python /home/pi/jvclrpctl/lumagen_ui/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable lumagen-ui.service
sudo systemctl start lumagen-ui.service
```

### 3. Check Status

```bash
sudo systemctl status lumagen-ui.service
```

## Usage

### Web Interface

1. Open your browser to `http://<raspberry-pi-ip>:5001`
2. Use the buttons to control your Lumagen
3. Click "Get Status" to view current configuration
4. Changes take effect immediately
5. Click "Save Configuration" to persist settings

### Keyboard Shortcuts

- `1-8`: Select input 1-8
- `A, B, C, D`: Select memory A, B, C, D
- `+/=`: Zoom in
- `-/_`: Zoom out
- `Ctrl+S`: Save configuration

## API Endpoints

The Flask app exposes a REST API:

- `POST /api/power/<on|standby>` - Power control
- `POST /api/input/<1-10>` - Select input
- `POST /api/memory/<A|B|C|D>` - Select memory
- `POST /api/aspect/<4:3|lbox|16:9|1.85|2.35|nls>` - Set aspect ratio
- `POST /api/zoom/<in|out>` - Zoom control
- `POST /api/output/<480p|720p|1080p|4k24|4k60|auto>` - Set output mode
- `POST /api/test-pattern/<contrast|off>` - Test patterns
- `POST /api/save` - Save configuration
- `GET /api/status` - Get Lumagen status

## Troubleshooting

### Cannot connect to serial port

1. Check port name: `ls -l /dev/ttyUSB*`
2. Check permissions: `sudo usermod -a -G dialout $USER`
3. Verify cable connection
4. Check Lumagen RS232 settings (115200 baud)

### Web UI not accessible on network

1. Check firewall: `sudo ufw allow 5001/tcp`
2. Verify Pi IP: `hostname -I`
3. Ensure app.py has `host='0.0.0.0'`

### Commands not working

1. Check Lumagen is powered on
2. Verify RS232 cable is properly connected
3. Check baud rate matches Lumagen settings (default 115200)
4. View logs: `sudo journalctl -u lumagen-ui.service -f`

## Architecture

- `app.py`: Flask web server with REST API
- `lumagen_control.py`: RS232 communication layer
- `templates/index.html`: Web UI interface
- `static/style.css`: UI styling
- `static/script.js`: Frontend JavaScript for API calls

## Integration with jvclrpctl

This web UI is **separate** from the main jvclrpctl automation. Both can run simultaneously:

- **jvclrpctl**: Automated HDR/SDR detection and JVC picture mode switching
- **lumagen_ui**: Manual web-based control of Lumagen settings

They use different serial ports:
- jvclrpctl: `/dev/ttyUSB0` (Lumagen status monitoring)
- lumagen_ui: `/dev/ttyUSB1` (Lumagen control)

## License

Same as jvclrpctl project.
