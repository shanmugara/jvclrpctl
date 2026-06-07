"""
Lumagen Radiance Pro Control via RS232
Based on Lumagen RS232 Command Interface (Tech Tip 11)
"""

import serial
import time
from typing import Optional, Dict, Any
from enum import Enum


class LumagenInput(Enum):
    """Input selection"""
    INPUT_1 = 1
    INPUT_2 = 2
    INPUT_3 = 3
    INPUT_4 = 4
    INPUT_5 = 5
    INPUT_6 = 6
    INPUT_7 = 7
    INPUT_8 = 8
    INPUT_9 = 9
    INPUT_10 = 10


class LumagenMemory(Enum):
    """Configuration memory"""
    MEM_A = 'A'
    MEM_B = 'B'
    MEM_C = 'C'
    MEM_D = 'D'


class LumagenAspect(Enum):
    """Input aspect ratios"""
    ASPECT_4_3 = '4:3'
    ASPECT_LBOX = 'LBOX'
    ASPECT_16_9 = '16:9'
    ASPECT_1_85 = '1.85'
    ASPECT_2_35 = '2.35'
    ASPECT_NLS = 'NLS'


class LumagenControl:
    """Control interface for Lumagen Radiance Pro"""
    
    def __init__(self, port: str = '/dev/ttyUSB1', baudrate: int = 115200):
        """
        Initialize Lumagen control
        
        Args:
            port: Serial port for Lumagen RS232
            baudrate: Default 115200 for Lumagen
        """
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.timeout = 1.0
        
    def connect(self):
        """Connect to Lumagen via RS232"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )
            time.sleep(0.1)  # Let connection stabilize
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to Lumagen on {self.port}: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Lumagen"""
        if self.serial and self.serial.is_open:
            self.serial.close()
    
    def send_command(self, command: str) -> str:
        """
        Send command to Lumagen and get response
        
        Args:
            command: RS232 command string
            
        Returns:
            Response from Lumagen
        """
        if not self.serial or not self.serial.is_open:
            raise ConnectionError("Not connected to Lumagen")
        
        # Lumagen expects commands ending with carriage return
        cmd = f"{command}\r"
        self.serial.write(cmd.encode('ascii'))
        self.serial.flush()
        
        # Read response
        time.sleep(0.1)
        response = b''
        while self.serial.in_waiting > 0:
            response += self.serial.read(self.serial.in_waiting)
            time.sleep(0.05)
        
        return response.decode('ascii', errors='ignore').strip()
    
    # Power Commands
    def power_on(self) -> str:
        """Turn Lumagen on"""
        return self.send_command("!PWR1")
    
    def power_standby(self) -> str:
        """Put Lumagen in standby"""
        return self.send_command("!PWR0")
    
    def get_power_status(self) -> str:
        """Get power status"""
        return self.send_command("?PWR")
    
    # Input Selection
    def select_input(self, input_num: int) -> str:
        """
        Select input (1-10)
        
        Args:
            input_num: Input number 1-10
        """
        if not 1 <= input_num <= 10:
            raise ValueError("Input must be 1-10")
        return self.send_command(f"!INP{input_num}")
    
    def get_current_input(self) -> str:
        """Get current input"""
        return self.send_command("?INP")
    
    # Memory Selection
    def select_memory(self, memory: str) -> str:
        """
        Select configuration memory (A, B, C, D)
        
        Args:
            memory: Memory letter A, B, C, or D
        """
        memory = memory.upper()
        if memory not in ['A', 'B', 'C', 'D']:
            raise ValueError("Memory must be A, B, C, or D")
        return self.send_command(f"!MEM{memory}")
    
    # Aspect Ratio Control
    def set_aspect_4_3(self) -> str:
        """Set input aspect to 4:3"""
        return self.send_command("!AR0")
    
    def set_aspect_lbox(self) -> str:
        """Set input aspect to Letterbox"""
        return self.send_command("!AR1")
    
    def set_aspect_16_9(self) -> str:
        """Set input aspect to 16:9"""
        return self.send_command("!AR2")
    
    def set_aspect_1_85(self) -> str:
        """Set input aspect to 1.85"""
        return self.send_command("!AR3")
    
    def set_aspect_2_35(self) -> str:
        """Set input aspect to 2.35"""
        return self.send_command("!AR4")
    
    def set_aspect_nls(self) -> str:
        """Set Non-Linear Stretch"""
        return self.send_command("!AR5")
    
    # Zoom Control
    def zoom_in(self) -> str:
        """Zoom in"""
        return self.send_command("!ZIN")
    
    def zoom_out(self) -> str:
        """Zoom out"""
        return self.send_command("!ZUT")
    
    # Output Mode Direct Commands (from manual Section 14)
    def set_output_480p(self) -> str:
        """Set output to 480p60"""
        return self.send_command("!MENU021")
    
    def set_output_720p(self) -> str:
        """Set output to 720p60"""
        return self.send_command("!MENU024")
    
    def set_output_1080p24(self) -> str:
        """Set output to 1080p24"""
        return self.send_command("!MENU020")
    
    def set_output_1080p(self) -> str:
        """Set output to 1080p60"""
        return self.send_command("!MENU027")
    
    def set_output_4k24(self) -> str:
        """Set output to 4k24"""
        return self.send_command("!MENU023")
    
    def set_output_4k60(self) -> str:
        """Set output to 4k60"""
        return self.send_command("!MENU029")
    
    def set_output_auto(self) -> str:
        """Set output to Auto mode"""
        return self.send_command("!MENU0870")
    
    # Status and Info
    def get_status(self) -> str:
        """Get status information"""
        return self.send_command("?STA")
    
    def get_info(self) -> str:
        """Get detailed info"""
        return self.send_command("?INF")
    
    # Save Configuration
    def save_config(self) -> str:
        """Save current configuration"""
        return self.send_command("!SAV")
    
    # Factory Reset
    def factory_reset(self) -> str:
        """Reset to factory defaults (MENU 0999)"""
        return self.send_command("!MENU0999")
    
    # Test Patterns
    def test_pattern_off(self) -> str:
        """Turn off test pattern"""
        return self.send_command("!TPT0")
    
    def test_pattern_contrast(self) -> str:
        """Display contrast test pattern"""
        return self.send_command("!TPT1")
    
    # Quick Commands
    def quick_4_3(self) -> str:
        """Quick key: 4:3 aspect"""
        return self.send_command("!QK0")
    
    def quick_lbox(self) -> str:
        """Quick key: Letterbox"""
        return self.send_command("!QK1")
    
    def quick_16_9(self) -> str:
        """Quick key: 16:9"""
        return self.send_command("!QK2")
    
    def quick_zoom_in(self) -> str:
        """Quick key: Zoom+"""
        return self.send_command("!QK6")
    
    def quick_zoom_out(self) -> str:
        """Quick key: Zoom-"""
        return self.send_command("!QK7")
