"""
Lumagen Radiance RS-232 Connection Module
Handles serial communication with Lumagen Radiance processors via USB
"""

import serial
import time
from typing import Optional
from ..logger import get_logger
from .constants import (
    DEFAULT_BAUDRATE, DEFAULT_TIMEOUT, DEFAULT_BYTESIZE,
    DEFAULT_PARITY, DEFAULT_STOPBITS,
    RESPONSE_PREFIX, RESPONSE_TERMINATOR
)

logger = get_logger()


class LumagenError(Exception):
    """Base exception for Lumagen errors"""
    pass


class LumagenConnectionError(LumagenError):
    """Connection-related errors"""
    pass


class LumagenCommandError(LumagenError):
    """Command execution errors"""
    pass


class LumagenRadiance:
    """
    Lumagen Radiance connection and communication handler
    
    Connects via USB serial port (USB-A to USB-B cable).
    
    Example:
        >>> radiance = LumagenRadiance('/dev/ttyUSB0')  # Linux/Mac
        >>> # or LumagenRadiance('COM3')  # Windows
        >>> radiance.connect()
        >>> status = radiance.query('ZQI52')
        >>> radiance.disconnect()
    """
    
    def __init__(self, port: str, baudrate: int = DEFAULT_BAUDRATE, 
                 timeout: float = DEFAULT_TIMEOUT):
        """
        Initialize Lumagen Radiance connection
        
        Args:
            port: Serial port path (e.g., '/dev/ttyUSB0', '/dev/cu.usbserial', 'COM3')
            baudrate: Serial baud rate (default: 9600)
            timeout: Serial timeout in seconds (default: 2.0)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None
        self._connected = False
    
    def connect(self) -> bool:
        """
        Establish serial connection to the Radiance
        
        Returns:
            True if connection successful
            
        Raises:
            LumagenConnectionError: If connection fails
        """
        try:
            # Open serial port
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=DEFAULT_BYTESIZE,
                parity=DEFAULT_PARITY,
                stopbits=DEFAULT_STOPBITS,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            
            # Small delay after connection
            time.sleep(0.2)
            
            # Clear any pending data
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            self._connected = True
            logger.info(f"Connected to Lumagen Radiance on {self.port} at {self.baudrate} baud")
            return True
            
        except (serial.SerialException, OSError) as e:
            if hasattr(e, 'errno') and e.errno == 2:  # FileNotFoundError
                logger.error(f"Port {self.port} not found. Check the port name and connection.")
                return False          
            if hasattr(e, 'errno') and e.errno == 13:  # PermissionError
                raise LumagenConnectionError(f"Permission denied for port {self.port}. Try running with elevated permissions or check port access.")
            raise LumagenConnectionError(f"Failed to connect to {self.port}: {e}")
    
    def disconnect(self):
        """Close serial connection to the Radiance"""
        if self.serial:
            try:
                self.serial.close()
            except:
                pass
            finally:
                self.serial = None
                self._connected = False
                logger.info("Disconnected from Lumagen Radiance")
    
    def is_connected(self) -> bool:
        """Check if connected to Radiance"""
        return self._connected and self.serial is not None and self.serial.is_open
    
    def send_command(self, command: bytes) -> bytes:
        """
        Send a command to the Radiance via serial
        
        Args:
            command: Command bytes to send
            
        Returns:
            Response from Radiance
            
        Raises:
            LumagenConnectionError: If not connected
            LumagenCommandError: If command fails
        """
        if not self.is_connected():
            raise LumagenConnectionError("Not connected to Radiance")
        
        try:
            # Send command via serial
            self.serial.write(command)
            self.serial.flush()
            
            # For query commands, wait for response
            if command.startswith(b'ZQ'):
                # Read response - Lumagen sends !<response><CR><LF>
                response = b''
                start_time = time.time()
                
                while time.time() - start_time < self.timeout:
                    if self.serial.in_waiting > 0:
                        chunk = self.serial.read(self.serial.in_waiting)
                        response += chunk
                        
                        # Check if we have a complete response
                        if RESPONSE_TERMINATOR in response:
                            break
                    
                    # Small delay to avoid busy-waiting
                    time.sleep(0.01)
                
                return response.strip()
            
            # For non-query commands, no response expected
            return b''
            
        except serial.SerialException as e:
            raise LumagenCommandError(f"Serial communication error: {e}")
    
    def query(self, command: str) -> str:
        """
        Send a query command and return the response
        
        Args:
            command: Query command string (e.g., 'ZQI52')
            
        Returns:
            Response string (without prefix and terminator)
        """
        cmd_bytes = command.encode('ascii')
        response = self.send_command(cmd_bytes)
        
        # Parse response: !<command>,<data><CR><LF>
        if response.startswith(RESPONSE_PREFIX):
            response = response[1:]  # Remove '!'
        
        # Remove terminator
        response = response.replace(RESPONSE_TERMINATOR, b'')
        
        return response.decode('ascii', errors='ignore')
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
