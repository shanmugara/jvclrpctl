"""
JVC and Lumagen Control Library
Control JVC D-ILA projectors and Lumagen Radiance processors
"""

# JVC imports
from .jvcctl import JVCProjector, JVCCommands, PictureMode, PictureModeController

# Lumagen imports
from .lumagen import LumagenRadiance, LumagenCommands

# Automation
from .automation import HDRAutomation

# Logger
from .logger import get_logger, set_logger_enabled, info, warn, error, raw

__version__ = "0.1.0"
__all__ = [
    # JVC
    "JVCProjector", 
    "JVCCommands", 
    "PictureMode", 
    "PictureModeController",
    # Lumagen
    "LumagenRadiance",
    "LumagenCommands",
    # Automation
    "HDRAutomation",
    # Logger
    "get_logger",
    "set_logger_enabled",
    "info",
    "warn",
    "error",
    "raw",
]
