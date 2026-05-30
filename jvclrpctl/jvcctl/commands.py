"""
JVC Projector Command Interface
High-level command methods for controlling the projector
"""

from .connection import JVCProjector
from .constants import (
    CMD_POWER, POWER_ON, POWER_OFF,
    CMD_INPUT, INPUT_HDMI_1, INPUT_HDMI_2,
    CMD_PICTURE_MODE
)


class JVCCommands:
    """
    High-level command interface for JVC projectors
    Wraps low-level connection methods with easy-to-use functions
    """
    
    def __init__(self, projector: JVCProjector):
        """
        Initialize commands interface
        
        Args:
            projector: Connected JVCProjector instance
        """
        self.projector = projector
    
    # Power commands
    
    def power_on(self) -> bool:
        """
        Turn projector power on
        
        Returns:
            True if successful
        """
        response = self.projector.send_operation(CMD_POWER, POWER_ON)
        return b'\x06' in response or b'PJACK' in response
    
    def power_off(self) -> bool:
        """
        Turn projector power off
        
        Returns:
            True if successful
        """
        response = self.projector.send_operation(CMD_POWER, POWER_OFF)
        return b'\x06' in response or b'PJACK' in response
    
    def get_power_status(self) -> str:
        """
        Query current power status
        
        Returns:
            Power status string
        """
        response = self.projector.send_reference(CMD_POWER)
        # Response is ASCII: b'0' = standby, b'1' = on, b'2' = cooling, b'3' = warming
        if response == b'0':
            return "standby"
        elif response == b'1':
            return "on"
        elif response == b'2':
            return "cooling"
        elif response == b'3':
            return "warming"
        return "unknown"
    
    # Input selection commands
    
    def select_hdmi_1(self) -> bool:
        """
        Select HDMI 1 input
        
        Returns:
            True if successful
        """
        response = self.projector.send_operation(CMD_INPUT, INPUT_HDMI_1)
        return b'\x06' in response or b'PJACK' in response
    
    def select_hdmi_2(self) -> bool:
        """
        Select HDMI 2 input
        
        Returns:
            True if successful
        """
        response = self.projector.send_operation(CMD_INPUT, INPUT_HDMI_2)
        return b'\x06' in response or b'PJACK' in response
    
    def get_current_input(self) -> str:
        """
        Query current input selection
        
        Returns:
            Input name string
        """
        response = self.projector.send_reference(CMD_INPUT)
        # Response is ASCII: b'6' = HDMI-1, b'7' = HDMI-2
        if response == b'6':
            return "HDMI-1"
        elif response == b'7':
            return "HDMI-2"
        return "unknown"
    
    # Picture mode commands
    
    def set_picture_mode(self, mode_value: bytes) -> bool:
        """
        Set picture mode
        
        Args:
            mode_value: Picture mode value (from PictureModes constants)
            
        Returns:
            True if successful
        """
        response = self.projector.send_operation(CMD_PICTURE_MODE, mode_value)
        return b'\x06' in response or b'PJACK' in response
    
    def get_picture_mode(self) -> bytes:
        """
        Query current picture mode
        
        Returns:
            Picture mode value
        """
        response = self.projector.send_reference(CMD_PICTURE_MODE)
        # Parse response to extract mode value
        return response
