# Logger Documentation

## Color-Coded Logger

The `jvclrpctl` library includes a built-in color-coded logger that provides clear, categorized output to stdout.

### Automatic Debug Mode Discovery

The logger automatically discovers the `DEBUG` environment variable on startup:
- **`DEBUG=true`**, **`DEBUG=1`**, or **`DEBUG=yes`** → Debug mode enabled (shows all messages)
- **`DEBUG=false`** or undefined → Normal mode (hides debug messages)

All modules that import the logger inherit this setting automatically.

### Features

- **Automatic environment detection**: Discovers DEBUG environment variable on import
- **Global DEBUG variable**: Single source of truth for debug mode across all modules
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

**Note:** The log level is automatically set based on the `DEBUG` environment variable on import. You typically don't need to call `set_log_level()` unless you want to override the environment-based behavior.

```python
from jvclrpctl import set_log_level, LogLevel

# Show all messages including debug (useful during development)
set_log_level(LogLevel.DEBUG)

# Show info and above, hide debug (default when DEBUG is not set)
set_log_level(LogLevel.INFO)

# Show only warnings and errors
set_log_level(LogLevel.WARN)

# Show only errors
set_log_level(LogLevel.ERROR)
```

#### Using the DEBUG Variable

The `DEBUG` variable is automatically set from the environment and can be imported by any module:

```python
from jvclrpctl import DEBUG, info, debug

if DEBUG:
    info("Running in debug mode")
    debug("Detailed information...")
else:
    info("Running in normal mode")
```

**Environment Variable Control:**

```bash
# Normal mode - debug messages hidden (default)
python your_script.py

# Debug mode - all messages visible
DEBUG=true python your_script.py

# Also works with:
DEBUG=1 python your_script.py
DEBUG=yes python your_script.py
```

### Examples

See the complete examples:
- [examples/logger_demo.py](../examples/logger_demo.py) - Full feature demonstration
- [examples/log_level_example.py](../examples/log_level_example.py) - Log level control examples
- [examples/test_debug_env.py](../examples/test_debug_env.py) - DEBUG environment variable test

```bash
# Run the full demo
python examples/logger_demo.py

# Run log level examples
python examples/log_level_example.py

# Test DEBUG environment variable
python examples/test_debug_env.py
DEBUG=true python examples/test_debug_env.py

# Run with debug enabled via environment variable
DEBUG=true python examples/log_level_example.py
```

### Practical Usage

#### In Your Application

The logger automatically discovers the DEBUG environment variable, so you don't need to configure it manually:

```python
from jvclrpctl import DEBUG, info, debug

# DEBUG is automatically set from environment
info("Application started")
debug("Debug info - only visible when DEBUG=true")

# You can check the DEBUG flag if needed
if DEBUG:
    debug("Verbose diagnostic information")
```

#### In runner.py

The runner automatically inherits the DEBUG setting from the environment:

```bash
# Normal mode - hides debug messages
python runner/runner.py

# Debug mode - shows all debug output
DEBUG=true python runner/runner.py
```

The runner includes debug statements that show:
- HDR status response details
- Connection parameters
- State transitions

#### All Modules Inherit DEBUG

Any module that imports from `jvclrpctl` automatically inherits the DEBUG setting:

```python
# In any module
from jvclrpctl import DEBUG, debug, info

# DEBUG is already set from environment
debug("This respects the global DEBUG setting")
```

**No need to:**
- Define DEBUG in each module
- Pass DEBUG as a parameter
- Manually set log levels

### Integration

The logger is automatically used throughout the library:
- **Connection operations**: Success/failure messages
- **Command execution**: Status updates
- **Error handling**: Clear error reporting
- **Status displays**: Formatted output

All `print()` statements in core library modules have been replaced with appropriate logger calls for consistent, color-coded output.
