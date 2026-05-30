# Logger Documentation

## Color-Coded Logger

The `jvclrpctl` library includes a built-in color-coded logger that provides clear, categorized output to stdout.

### Features

- **Color-coded output**: Different message types use different colors for easy identification
- **Prefixed messages**: Each log level has a clear prefix
- **Global control**: Enable or disable logging globally
- **Simple API**: Easy-to-use functions for different log levels

### Log Levels

| Level | Prefix | Color | Use Case |
|-------|--------|-------|----------|
| Info | `[INFO]` | Green | Success messages, confirmations |
| Warning | `[WARN]` | Yellow | Non-critical warnings, status unchanged |
| Error | `[ERROR]` | Red | Failures, exceptions, critical issues |
| Raw | None | None | Headers, separators, plain text |

### Usage

#### Basic Usage

```python
from jvclrpctl import info, warn, error, raw

# Info messages (green)
info("Connected to projector successfully")
info("Picture mode set to USER3")

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

### Examples

See the complete example in [examples/logger_demo.py](../examples/logger_demo.py):

```bash
python examples/logger_demo.py
```

### Integration

The logger is automatically used throughout the library:
- **Connection operations**: Success/failure messages
- **Command execution**: Status updates
- **Error handling**: Clear error reporting
- **Status displays**: Formatted output

All `print()` statements in core library modules have been replaced with appropriate logger calls for consistent, color-coded output.
