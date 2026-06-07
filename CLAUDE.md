# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

`jvclrpctl` is a Python library for controlling JVC D-ILA projectors (via TCP/IP on port 20554) and Lumagen Radiance video processors (via USB serial at 9600 baud). The primary use case is the `runner/runner.py` daemon that polls Lumagen for HDR vs SDR content detection and automatically switches the JVC projector picture mode.

## Setup

```bash
# Install dependencies (only pyserial is required at runtime)
pip install -r requirements.txt

# Install the package in editable mode for development
pip install -e ".[dev]"
```

## Common commands

```bash
# Run the HDR polling daemon (requires real hardware)
python runner/runner.py

# Run tests
pytest
pytest tests/test_connection.py          # single file
pytest tests/test_picture_modes.py -v   # verbose

# Lint / format
flake8 jvclrpctl/
black jvclrpctl/
mypy jvclrpctl/

# Run an example script (edit the IP/port constants first)
python examples/basic_control.py
python examples/hdr_automation.py

# Enable debug output via environment variable
DEBUG=true python runner/runner.py
```

## Architecture

The package has three sub-systems wired together by `automation.py`:

```
jvclrpctl/
├── jvcctl/          # JVC projector control (TCP/IP)
│   ├── connection.py   # JVCProjector — socket connect/disconnect, _send_command
│   ├── commands.py     # JVCCommands — power, input, picture_mode helpers
│   ├── picture_modes.py # PictureMode enum + PictureModeController
│   └── constants.py    # Wire-level bytes: HEADER_OPERATION/REFERENCE, PictureModes, etc.
├── lumagen/         # Lumagen Radiance control (USB serial via pyserial)
│   ├── connection.py   # LumagenRadiance — serial open/close, send_command, query
│   ├── commands.py     # LumagenCommands — get_hdr_status, get_full_status_v4, is_hdr
│   └── constants.py    # ZQI* query bytes, LRPInputModes enum
├── automation.py    # HDRAutomation — background thread, poll loop, connects both devices
└── logger.py        # Global Logger singleton, color-coded stdout + rotating file at /var/log/jvclrpctl
```

**JVC wire protocol** (from JVC spec v1.2): 3-way TCP handshake (`PJ_OK` → `PJREQ_\x00*16` → `PJACK`), then ASCII commands: `HEADER + UNIT_ID(\x89\x01) + CMD + DATA + \x0A`. Operation (`!`) gets ACK only; Reference (`?`) gets ACK then `@` response frame.

**Lumagen wire protocol**: Serial at 9600/8N1. Query commands start with `ZQ` (e.g. `ZQI52` for HDR status); responses are `!<data>\r\n`. The HDR flag lives in the `F` field of `ZQI22`/`ZQI23`/`ZQI24` responses.

**runner/runner.py** is the production entry point — `JVC_LRP_Runner` connects both devices each poll cycle (connect → check → disconnect), compares against the last known `LRPInputModes` state, and only sends a picture-mode change when content type transitions. The `poll()` function wraps this in a `while True` / `sleep` loop.

**logger.py**: A global singleton (`get_logger()`) is shared across the library. Debug output is gated by the `DEBUG` env var. File logging defaults to `/var/log/jvclrpctl` with midnight rotation and 30-day retention. Use `set_log_dir(None)` to disable file logging in tests or scripts.

## systemd service

`systemd/` contains install/uninstall scripts and `jvc-lrp-runner.service`. The service runs `runner/runner.py` under a venv at `/home/speriya/venv`. Uncomment `#Environment="DEBUG=true"` to enable debug logging. Logs go to `/dev/tty1` and to the rotating file at `/var/log/jvclrpctl`.

## lumagen_ui (separate Flask app)

`lumagen_ui/` is an independent Flask web UI for Lumagen-only control (no JVC). It runs on port 5001 and has its own `requirements.txt`, `install.sh`, and systemd service. The serial port is configured via the `LUMAGEN_PORT` env var (default `/dev/ttyUSB1`).
