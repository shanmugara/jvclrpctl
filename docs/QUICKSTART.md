# Quick Start Guide

## Installation

1. Clone or download this repository
2. Install the package in development mode:

```bash
cd jvclrpctl
pip install -e .
```

## Basic Usage

### Step 1: Find Your Projector's IP Address

Check your projector's network settings menu to find its IP address. Common locations:
- Menu → Installation → Network → Information
- Note the IP address (e.g., 192.168.1.100)

### Step 2: Test Connection

Create a simple test script:

```python
from jvclrpctl import JVCProjector

# Replace with your projector's IP
projector = JVCProjector('192.168.1.100')

try:
    projector.connect()
    print("✓ Connected successfully!")
except Exception as e:
    print(f"✗ Connection failed: {e}")
finally:
    projector.disconnect()
```

### Step 3: Control Picture Modes

```python
from jvclrpctl import JVCProjector, PictureMode
from jvclrpctl.picture_modes import PictureModeController

with JVCProjector('192.168.1.100') as projector:
    controller = PictureModeController(projector)
    
    # Change to Cinema mode
    controller.set_mode(PictureMode.CINEMA)
    
    # Or use name
    controller.set_mode_by_name("HDR")
```

## Running Examples

The project includes ready-to-use examples:

1. **Edit the IP address** in the example file:
   ```python
   PROJECTOR_IP = "192.168.1.100"  # Change to your projector's IP
   ```

2. **Run the example**:
   ```bash
   cd examples
   python picture_mode_control.py
   ```

### Available Examples:

- `basic_control.py` - Power and input control
- `picture_mode_control.py` - Picture mode switching
- `interactive_selector.py` - Interactive CLI menu

## Common Issues

### Cannot connect
- Ensure projector is on the network
- Check IP address is correct
- Verify port 20554 is open (default)
- Enable network control in projector settings

### Commands not working
- Projector must be powered on (not standby)
- Wait for projector to fully warm up (~30 seconds)
- Some commands may not be available in certain modes

## Next Steps

- Read the full [README.md](../README.md) for detailed API documentation
- Explore the [examples/](../examples/) directory
- Check the [JVC specification PDF](../docs/2018_ILA-FPJ_Ext_Command_List_v1.2.pdf) for all available commands

## Getting Help

- Review the API documentation in README.md
- Check the JVC specification document in docs/
- Examine the example scripts for usage patterns
