"""
JVC Projector Command Interface
High-level command methods for controlling the projector
"""

import time
from .connection import JVCProjector
from .constants import (
    CMD_POWER, POWER_ON, POWER_OFF,
    CMD_INPUT, INPUT_HDMI_1, INPUT_HDMI_2,
    CMD_PICTURE_MODE
)
from ..logger import info, warn, debug


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
    
    def set_picture_mode(self, mode_value: bytes, max_retries: int = 3) -> bool:
        """
        Set picture mode with verification and retry logic
        
        Args:
            mode_value: Picture mode value (from PictureModes constants)
            max_retries: Maximum number of attempts (default: 3)
            
        Returns:
            True if successful
        """
        for attempt in range(max_retries):
            # Send the command
            response = self.projector.send_operation(CMD_PICTURE_MODE, mode_value)
            debug(f"JVC set picture mode raw response: {response}")
            
            # Check if command was acknowledged
            if not (b'\x06' in response or b'PJACK' in response):
                if attempt < max_retries - 1:
                    warn(f"JVC Picture mode command no PJACK (attempt {attempt + 1}/{max_retries}). Retrying in 1 second...")
                    time.sleep(1)
                    continue
                else:
                    warn(f"JVC Picture mode command no PJACK after {max_retries} attempts")
                    return False
            
            # Verify the mode was actually set
            time.sleep(0.5)  # Brief delay to let the projector update
            debug("JVC Verifying picture mode...")
            current_mode = self.get_picture_mode()

            debug(f"JVC Expected picture mode: {mode_value.hex()}, Current picture mode: {current_mode.hex()}")
            
            if current_mode == mode_value:
                info(f"JVC Picture mode successfully set and verified (attempt {attempt + 1})")
                return True
            else:
                if attempt < max_retries - 1:
                    warn(f"JVC Picture mode verification failed (attempt {attempt + 1}/{max_retries}). Expected {mode_value.hex()}, got {current_mode.hex()}. Retrying in 1 second...")
                    time.sleep(1)
                else:
                    warn(f"JVC Picture mode verification failed after {max_retries} attempts. Expected {mode_value.hex()}, got {current_mode.hex()}")
                    return False
        
        return False
    
    def get_picture_mode(self) -> bytes:
        """
        Query current picture mode
        
        Returns:
            Picture mode value
        """
        response = self.projector.send_reference(CMD_PICTURE_MODE)
        # Parse response to extract mode value
        return response
