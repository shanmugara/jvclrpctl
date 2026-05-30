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
]
