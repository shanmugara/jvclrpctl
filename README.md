# JVC & Lumagen Control Library (jvclrpctl)

A comprehensive Python library for controlling JVC D-ILA projectors and Lumagen Radiance video processors, with automated HDR detection and picture mode switching.

## Supported Devices

### JVC Projectors
- DLA-NX7, N8, V7 Series
- DLA-NX9, NX5, N5
- DLA-RS2000, RS1000, RS500
- And other models supporting the JVC External Command Communication Specification v1.2

### Lumagen Radiance
- Radiance Pro (all models)
- Radiance 2XXX series
- Radiance XD, XE
- Any model with RS-232 command interface (USB-A to USB-B cable)

**Connection**: Serial via USB at 9600 baud

## Features

### JVC Control
- 🌐 **Network Control**: Connect to projectors via TCP/IP (default port 20554)
- 🎬 **Picture Mode Selection**: Easy-to-use interface for switching between picture modes
- ⚡ **Power Control**: Turn projector on/off and monitor power status
- 📺 **Input Selection**: Switch between HDMI inputs
- 🐍 **Pure Python**: No external dependencies beyond standard library

### Lumagen Control
- 📡 **RS-232 Communication**: Network or serial connection support
- 📊 **Status Queries**: Comprehensive status information (resolution, HDR, aspect ratio, etc.)
- 🎥 **USB Serial Communication**: RS-232 via USB-A to USB-B cable
- 🔍 **Device Information**: Query model, firmware, and configuration

### Automation
- 🤖 **HDR Auto-Switching**: Automatically adjust JVC picture mode based on Lumagen HDR detection
- ⏱️ **Background Polling**: Non-blocking continuous monitoring

## Installation

### Requirements
- **Python**: 3.7 or higher
- **pyserial**: For Lumagen USB serial communication

### Install

```bash
# Install pyserial
pip install pyserial

# Or from requirements.txt
pip install -r requirements.txt
```

### Supported Platforms
- ✅ **Windows** (COM3, COM4, etc.)
- ✅ **macOS** (/dev/cu.usbserial*)
- ✅ **Linux** (/dev/ttyUSB*, /dev/ttyACM*)
- ✅ **Raspberry Pi 3/4** (Perfect for 24/7 automation server!)

**📘 For Raspberry Pi setup:** See [Raspberry Pi Setup Guide](docs/RASPBERRY_PI_SETUP.md)

## Usage Examples
Automatically switch JVC picture modes based on Lumagen HDR detection:

```python
from jvclrpctl import HDRAutomation, PictureMode

# Create automation
automation = HDRAutomation(
    jvc_ip='192.168.1.100',
    lumagen_port='/dev/ttyUSB0',  # USB serial port
    poll_interval=2.0,           # Check every 2 seconds
    sdr_mode=PictureMode.USER1,  # SDR → USER1
    hdr_mode=PictureMode.USER2   # HDR → USER2
)

# Start automation (runs in background)
automation.start()

# ... automation runs continuously ...

# Stop when done
automation.stop()
```

### JVC Control
```python
from jvclrpctl import JVCProjector, PictureMode
from jvclrpctl.jvcctl import PictureModeController

# Using context manager
with JVCProjector('192.168.1.100') as projector:
    controller = PictureModeController(projector)
    
    # Set picture mode
    controller.set_mode(PictureMode.CINEMA)
    controller.set_mode_by_name("HDR")
    
    # Get current mode
    current = controller.get_current_mode()
    print(f"Current mode: {current.display_name}")
```

### Lumagen Control
```python
from jvclrpctl import LumagenRadiance, LumagenCommands

# Connect to Lumagen via USB serial
with LumagenRadiance('/dev/ttyUSB0') as radiance:
    commands = LumagenCommands(radiance)
    
    # Check HDR status
    is_hdr = commands.is_hdr()
    print(f"HDR: {is_hdr}")
    
    # Get full status
    status = commands.get_full_status_v4()
    print(f"Resolution: {status['source_resolution']}p")
    print(f"HDR: {status['is_hdr']
from jvclrpctl.picture_modes import PictureModeController

# Using context manager
with JVCProjector('192.168.1.100') as projector:
    controller = PictureModeController(projector)
    
    # Set picture mode by enum
    controller.set_mode(PictureMode.CINEMA)
    
    # Set picture mode by name
    controller.set_mode_by_name("HDR")
    
    # List available modes
    controller.print_available_modes()
    
    # Get current mode
    current = controller.get_current_mode()
    print(f"Current mode: {current.display_name}")
```
### Automation
1. **hdr_automation.py**: Automated HDR detection and picture mode switching
2. **test_lumagen.py**: Test Lumagen connection and query status

### JVC Control
3. **basic_control.py**: Power and input control
4. **picture_mode_control.py**: Picture mode switching demonstrations
5. **interactive_selector.py**: Interactive CLI for selecting picture modes

To run an example:
```bash
# Edit the IP addresses in the example file first
cd examples
python hdr_automatione Adapt HDR
- **USER1-USER6**: User-defined modes
- **HLG**: HLG (Hybrid Log-Gamma)

## Examples

The `examples/` directory contains several ready-to-use scripts:

1. **basic_control.py**: Demonstrates power and input control
2. **picture_mode_control.py**: Shows how to change picture modes
3. **interactive_selector.py**: Interactive CLI for selecting picture modes

To run an example:
```bash
# Edit the PROJECTOR_IP in the example file first
cd examples
python picture_mode_control.py
```
automation.py       # HDR automation module
│   ├── jvcctl/            # JVC-specific modules
│   │   ├── __init__.py
│   │   ├── connection.py   # TCP/IP connection handler
│   │   ├── commands.py     # High-level command interface
│   │   ├── picture_modes.py # Picture mode controls
│   │   └── constants.py    # JVC protocol constants
│   └── lumagen/           # Lumagen-specific modules
│       ├── __init__.py
│       ├── connection.py   # RS-232 connection handler
│       ├── commands.py     # Lumagen command interface
│       └── constants.py    # Lumagen protocol constants
├── examples/               # Example scripts
│   ├── hdr_automation.py   # HDR auto-switching
│   ├── test_lumagen.py     # Lumagen connection test
│   ├── basic_control.py    # JVC basic control
│   ├── picture_mode_control.py
│   └── interactive_selector.py
├── tests/                  # Test files
├── docs/                   # Documentation
│   ├── 2018_ILA-FPJ_Ext_Command_List_v1.2.pdf  # JVC spec
│   └── Tip0011_RS232CommandInterface_111023.pdf # Lumagen spec
```python
projector = JVCProjector('192.168.1.100', timeout=10.0)
```

## Project Structure

```
jvclrpctl/
├── jvclrpctl/              # Main package
│   ├── __init__.py         # Package initialization
│   ├── connection.py       # TCP/IP connection handler
│   ├── commands.py         # High-level command interface
│   ├── picture_modes.py    # Picture mode controls
│   HDRAutomation
Automated HDR detection and picture mode switching.

**Methods:**
- `start()`: Start automation (runs in background thread)
- `stop()`: Stop automation
- `get_status()`: Get current automation status

**Parameters:**
- `jvc_ip`: JVC projector IP address
- `lumagen_ip`: Lumagen Radiance IP address
- `poll_interval`: How often to check HDR status (seconds)
- `sdr_mode`: Picture mode for SDR content
- `hdr_mode`: Picture mode for HDR content
- `on_mode_change`: Optional callback function

### JVC Classes

#### JVCProjector
Main connection class for communicating with the projector.

**Methods:**
- `connect()`: Establish connection
- `disconnect()`: Close connection
- `is_connected()`: Check connection status
- `send_operation(command, data)`: Send operation command
- `send_reference(command, data)`: Send reference/query command

#### JVCCommands
High-level command interface.

**Methods:**
- `power_on()`, `power_off()`: Power control
- `get_power_status()`: Query power status
- `select_hdmi_1()`, `select_hdmi_2()`: Input selection
- `get_current_input()`: Query current input
- `set_picture_mode(mode_value)`: Set picture mode
- `get_picture_mode()`: Query current picture mode

#### PictureModeController
Simplified picture mode control interface.

**Methods:**
- `set_mode(mode)`: Set picture mode using enum
- `set_mode_by_name(name)`: Set picture mode by name
- `get_current_mode()`: Get current picture mode
- `print_available_modes()`: Print all available modes

### Lumagen Classes

#### LumagenRadiance
Connection handler for Lumagen Radiance processors.

**Methods:**
- `connect()`: Establish connection
- `disconnect()`: Close connection
- `query(command)`: Send query and return response

###Use Cases

### Home Theater Automation
- Automatically switch between SDR and HDR picture modes
- Eliminate manual picture mode adjustments
- Optimize picture quality for different content types

### Professional Installation
- Integrate with control systems (Crestron, Control4, etc.)
- Monitor projector and processor status
- Automate calibration workflows

### Custom Workflows
- Build custom automation scripts
- Integrate with media servers (Plex, Kodi, etc.)
- Create advanced picture mode management

## Troubleshooting

### JVC Projector
- **Cannot connect**: Verify IP address, network control enabled, port 20554 open
- **Commands not working**: Ensure projector is powered on, check model compatibility

### Lumagen Radiance
- **Cannot connect**: Verify IP address, check port 23 (telnet) or serial connection
- **No HDR detection**: Ensure content is playing, check Lumagen firmware version
- **Polling issues**: Increase poll_interval, check network stability

### Automation
- **Mode not switching**: Verify both devices are connected, check console output for errors
- **Delayed switching**: Adjust poll_interval (lower = faster detection, higher = less network traffic) input
- `set_picture_mode(mode_value)`: Set picture mode
- `get_picture_mode()`: Query current picture mode

### PictureModeController
Simplified picture mode control interface.

**Methods:**
- `set_mode(mode)`: Set picture mode using enum
- `set_mode_by_name(name)`: Set picture mode by name string
- `get_current_mode()`: Get current picture mode
- `print_available_modes()`: Print all available modes
- `list_modes()`: Get list of all modes
- `list_mode_names()`: Get list of mode names

## Error Handling

The library defines custom exceptions:

```python
from jvclrpctl.connection import JVCConnectionError, JVCCommandError

try:
    projector.connect()
    commands.power_on()
except JVCConnectionError as e:
    print(f"Connection error: {e}")
except JVCCommandError as e:
    print(f"Command error: {e}")
```

## Technical Details

- **Protocol**: ASCII-based command protocol
- **Communication**: Synchronous TCP/IP
- **Default Port**: 20554
- **Command Format**: Header + Unit ID + Command + Data + End marker
- **Based on**: JVC D-ILA External Command Communication Specification Ver. 1.2

## Troubleshooting

### Cannot connect to projector
1. Verify the projector is on the same network
2. Check the IP address is correct
3. Ensure the projector's network control is enabled
4. Verify firewall settings allow connections on port 20554

### Commands not working
1. Ensure projector is powered on (not in standby)
2. Check the command is supported by your specific model
3. Verify network connection is stable

## Contributing

Contributions are welcome! Areas for improvement:
- Add more commands (lens control, gamma adjustments, etc.)
- Add unit tests
- Add async support
- Improve error handling and response parsing

## License

MIT License - See LICENSE file for details

## Credits

Based on the JVC D-ILA Projector External Command Communication Specification Ver. 1.2
Document No. PJ09020002B (9/Oct/2018)

## Author

Created for controlling JVC D-ILA projectors over IP networks.
