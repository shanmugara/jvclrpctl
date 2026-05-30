# Logger Documentation

## Color-Coded Logger

The `jvclrpctl` library includes a built-in color-coded logger that provides clear, categorized output to stdout.

### Features

- **Color-coded output**: Different message types use different colors for easy identification
- **Prefixed messages**: Each log level has a clear prefix
- **Log level filtering**: Set minimum log level to control which messages are displayed
- **Global control**: Enable or disable logging globally
- **Simple API**: Easy-to-use functions for different log levels

### Log Levels

| Level | Prefix | Color | Use Case |
|-------|--------|-------|----------|
| Info | `[INFO]` | Green | Success messages, confirmations |
| Debug | `[DEBUG]` | Yellow | Debug information, variable values, detailed traces |
| Warning | `[WARN]` | Yellow | Non-critical warnings, status unchanged |
| Error | `[ERROR]` | Red | Failures, exceptions, critical issues |
| Raw | None | None | Headers, separators, plain text |

### Usage

#### Basic Usage

```python
from jvclrpctl import info, debug, warn, error, raw

# Info messages (green)
info("Connected to projector successfully")
info("Picture mode set to USER3")

# Debug messages (yellow)
debug("Sending command: 0x21 0x89 0x01 0x50 0x57")
debug("Response: ACK received")

# Warning messages (yellow)
warn("HDR status has not changed")
warn("Retrying connection...")

# Error messages (red)
error("Failed to connect to projector")
error("Command timeout")

# Raw messages (no color, no prefix)
raw("=" * 60)
raw("JVC Projector Control")
raw("=" * 60)
```

#### Using Logger Instance

```python
from jvclrpctl.logger import get_logger

logger = get_logger()

logger.info("This is an info message")
logger.debug("This is a debug message")
logger.warn("This is a warning")
logger.error("This is an error")
logger.raw("This is a raw message")
```

#### Enable/Disable Logging

```python
from jvclrpctl import set_logger_enabled

# Disable all logging
set_logger_enabled(False)

# Re-enable logging
set_logger_enabled(True)
```

#### Set Log Level

Control which messages are displayed by setting a minimum log level. Only messages at or above the set level will be shown.

```python
from jvclrpctl import set_log_level, LogLevel

# Show all messages including debug (useful during development)
set_log_level(LogLevel.DEBUG)

# Show info and above, hide debug (default)
set_log_level(LogLevel.INFO)

# Show only warnings and errors
set_log_level(LogLevel.WARN)

# Show only errors
set_log_level(LogLevel.ERROR)
```

**Common Usage Pattern:**

```python
from jvclrpctl import set_log_level, LogLevel, debug, info

# In development/debug mode
if debug_mode:
    set_log_level(LogLevel.DEBUG)
else:
    set_log_level(LogLevel.INFO)

# Debug messages only show when level is DEBUG
debug("Detailed trace information")
info("Normal operation message")
```

### Examples

See the complete examples:
- [examples/logger_demo.py](../examples/logger_demo.py) - Full feature demonstration
- [examples/log_level_example.py](../examples/log_level_example.py) - Log level control examples

```bash
# Run the full demo
python examples/logger_demo.py

# Run log level examples
python examples/log_level_example.py

# Run with debug enabled via environment variable
DEBUG=true python examples/log_level_example.py
```

### Practical Usage

#### In Your Application

```python
import os
from jvclrpctl import set_log_level, LogLevel, info, debug

# Set log level based on environment or config
DEBUG_MODE = os.getenv('DEBUG', 'false').lower() == 'true'

if DEBUG_MODE:
    set_log_level(LogLevel.DEBUG)
    debug("Debug mode enabled")
else:
    set_log_level(LogLevel.INFO)

# Use throughout your code
info("Application started")
debug("Connection parameters: host=192.168.1.100, port=20554")
```

#### In runner.py

The runner includes a `DEBUG_MODE` configuration variable:

```python
# In runner/runner.py
DEBUG_MODE = False  # Set to True to see debug messages

if DEBUG_MODE:
    set_log_level(LogLevel.DEBUG)
else:
    set_log_level(LogLevel.INFO)
```

When `DEBUG_MODE = True`, you'll see detailed debug output like:
- Command/response traces
- HDR status details
- Connection parameters

#### Command Line Control

You can also control log level via environment variables:

```bash
# Normal mode (INFO level)
python runner/runner.py

# Debug mode (DEBUG level)
DEBUG_MODE=true python runner/runner.py
```

### Integration

The logger is automatically used throughout the library:
- **Connection operations**: Success/failure messages
- **Command execution**: Status updates
- **Error handling**: Clear error reporting
- **Status displays**: Formatted output

All `print()` statements in core library modules have been replaced with appropriate logger calls for consistent, color-coded output.
