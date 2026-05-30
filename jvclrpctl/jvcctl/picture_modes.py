"""
JVC Projector Picture Mode Controls
Simplified interface for selecting and managing picture modes
"""

from enum import Enum
from typing import Optional
from .connection import JVCProjector
from .commands import JVCCommands
from .constants import PictureModes, CMD_PICTURE_MODE


class PictureMode(Enum):
    """
    Available picture modes on JVC projectors
    """
    FILM = ("Film", PictureModes.FILM)
    CINEMA = ("Cinema", PictureModes.CINEMA)
    NATURAL = ("Natural", PictureModes.NATURAL)
    HDR = ("HDR", PictureModes.HDR)
    THX = ("THX", PictureModes.THX)
    FRAME_ADAPT_HDR = ("Frame Adapt HDR", PictureModes.FRAME_ADAPT_HDR)
    USER1 = ("User1", PictureModes.USER1)
    USER2 = ("User2", PictureModes.USER2)
    USER3 = ("User3", PictureModes.USER3)
    USER4 = ("User4", PictureModes.USER4)
    USER5 = ("User5", PictureModes.USER5)
    USER6 = ("User6", PictureModes.USER6)
    HLG = ("HLG", PictureModes.HLG)
    
    def __init__(self, display_name: str, value: bytes):
        self.display_name = display_name
        self.mode_value = value
    
    @classmethod
    def from_value(cls, value: bytes) -> Optional['PictureMode']:
        """Get PictureMode enum from byte value"""
        for mode in cls:
            if mode.mode_value == value:
                return mode
        return None
    
    @classmethod
    def list_all(cls):
        """List all available picture modes"""
        return [mode for mode in cls]


class PictureModeController:
    """
    High-level controller for picture mode operations
    """
    
    def __init__(self, projector: JVCProjector):
        """
        Initialize picture mode controller
        
        Args:
            projector: Connected JVCProjector instance
        """
        self.projector = projector
        self.commands = JVCCommands(projector)
    
    def set_mode(self, mode: PictureMode) -> bool:
        """
        Set the picture mode
        
        Args:
            mode: PictureMode enum value
            
        Returns:
            True if successful
            
        Example:
            >>> controller.set_mode(PictureMode.CINEMA)
        """
        return self.commands.set_picture_mode(mode.mode_value)
    
    def set_mode_by_name(self, name: str) -> bool:
        """
        Set picture mode by name (case-insensitive)
        
        Args:
            name: Name of the picture mode (e.g., "Cinema", "HDR")
            
        Returns:
            True if successful
            
        Example:
            >>> controller.set_mode_by_name("cinema")
        """
        name_upper = name.upper().replace(" ", "_")
        try:
            mode = PictureMode[name_upper]
            return self.set_mode(mode)
        except KeyError:
            raise ValueError(f"Unknown picture mode: {name}. Available modes: {self.list_mode_names()}")
    
    def get_current_mode(self) -> Optional[PictureMode]:
        """
        Get the current picture mode
        
        Returns:
            Current PictureMode enum value or None if unknown
        """
        response = self.commands.get_picture_mode()
        # Response is ASCII: e.g., b'0E' for USER3, b'01' for CINEMA
        if len(response) >= 2:
            # Response is 2 ASCII characters representing the mode
            mode_bytes = response[:2]  # First 2 bytes are the ASCII mode value
            return PictureMode.from_value(mode_bytes)
        return None
    
    @staticmethod
    def list_mode_names() -> list:
        """
        Get list of all available picture mode names
        
        Returns:
            List of mode names
        """
        return [mode.name for mode in PictureMode]
    
    @staticmethod
    def list_modes() -> list:
        """
        Get list of all available picture modes
        
        Returns:
            List of PictureMode enums
        """
        return PictureMode.list_all()
    
    def print_available_modes(self):
        """Print all available picture modes"""
        print("\nAvailable Picture Modes:")
        print("-" * 40)
        for mode in PictureMode:
            print(f"  {mode.name:<20} - {mode.display_name}")
        print("-" * 40)
