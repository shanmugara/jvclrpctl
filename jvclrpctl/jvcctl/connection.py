"""
JVC Projector TCP/IP Connection Module
Handles network communication with JVC D-ILA projectors
"""

import socket
import time
from typing import Optional, Tuple
import sys
import os
from .constants import (
    DEFAULT_PORT, DEFAULT_TIMEOUT, HEADER_OPERATION, HEADER_REFERENCE,
    HEADER_RESPONSE, UNIT_ID, END_MARKER, HEADER_ACK, PJNAK, PJACK, AUTH_COMMAND, PJ_OK
)

# Add parent directory to path so we can import jvclrpctl
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ..logger import debug, warn, error, info


class JVCProjectorError(Exception):
    """Base exception for JVC projector errors"""
    pass


class JVCConnectionError(JVCProjectorError):
    """Connection-related errors"""
    pass


class JVCCommandError(JVCProjectorError):
    """Command execution errors"""
    pass


class JVCProjector:
    """
    JVC Projector connection and communication handler
    
    Example:
        >>> projector = JVCProjector('192.168.1.100')
        >>> projector.connect()
        >>> projector.power_on()
        >>> projector.disconnect()
    """
    
    def __init__(self, host: str, port: int = DEFAULT_PORT, timeout: float = DEFAULT_TIMEOUT):
        """
        Initialize JVC projector connection
        
        Args:
            host: IP address of the projector
            port: TCP port (default: 20554)
            timeout: Socket timeout in seconds (default: 5.0)
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
        self._connected = False
    
    def connect(self) -> bool:
        """
        Establish connection to the projector and perform authentication handshake
        
        Connection sequence:
        1. TCP connect
        2. Receive PJ_OK greeting
        3. Send PJREQ authentication (empty password)
        4. Receive PJACK confirmation
        5. Ready for commands
        
        Returns:
            True if connection successful
            
        Raises:
            JVCConnectionError: If connection or authentication fails
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            
            # Step 1: Wait for PJ_OK greeting
            greeting = self.socket.recv(1024)

            # PJ_NG means the projector is busy (another controller connected or
            # mid-processing) - a normal, recoverable condition, not a fault.
            if greeting.startswith(b'PJ_NG'):
                self.disconnect()  # Clean up socket
                raise JVCConnectionError(
                    "Projector busy (PJ_NG): another controller is connected or it "
                    "is processing. Will retry next cycle."
                )
            if not greeting.startswith(PJ_OK):
                self.disconnect()  # Clean up socket
                raise JVCConnectionError(f"Expected PJ_OK greeting, got: {greeting!r}. Check projector connection.")
            
            # Step 2: Send authentication (PJREQ with empty password)
            self.socket.sendall(AUTH_COMMAND)
            time.sleep(0.3)  # Wait for authentication to process
            
            # Step 3: Wait for PJACK authentication confirmation
            auth_response = self.socket.recv(1024)
            
            if auth_response == PJACK:
                # Authentication successful - ready for commands
                debug("JVC authentication successful")
                self._connected = True
                return True
            elif auth_response == PJNAK:
                debug("JVC authentication failed: PJNAK received")
                self.disconnect()  # Clean up socket
                raise JVCConnectionError("Authentication failed: Projector rejected PJREQ. Check that Network Control is enabled.")
            else:
                debug(f"JVC authentication unexpected response: {auth_response}")
                self.disconnect()  # Clean up socket
                raise JVCConnectionError(f"Unexpected authentication response: {auth_response}")
            
        except socket.timeout:
            debug("JVC connection timeout")
            self.disconnect()  # Clean up socket
            raise JVCConnectionError(f"Connection timeout - no response from projector at {self.host}:{self.port}")
        except socket.error as e:
            debug(f"JVC connection error: {e}")
            self.disconnect()  # Clean up socket
            raise JVCConnectionError(f"Failed to connect to {self.host}:{self.port}: {e}")
        except Exception as e:
            debug(f"Unexpected error during JVC connection: {e}")
            self.disconnect()  # Clean up socket
            raise JVCConnectionError(f"Unexpected error: {e}")
    
    def disconnect(self):
        """Close connection to the projector"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            finally:
                self.socket = None
                self._connected = False
    
    def is_connected(self) -> bool:
        """Check if connected to projector"""
        return self._connected and self.socket is not None
    
    def _send_command(self, header: bytes, command: bytes, data: bytes = b'') -> bytes:
        """
        Send a command to the projector
        
        Args:
            header: Command header (! for operation, ? for reference)
            command: Command code (e.g., b'PW' for power)
            data: Command data/parameters
            
        Returns:
            Response from projector
            
        Raises:
            JVCConnectionError: If not connected
            JVCCommandError: If command fails
        """
        if not self.is_connected():
            raise JVCConnectionError("Not connected to projector")
        
        # Build command: Header + UnitID + Command + Data + End
        full_command = header + UNIT_ID + command + data + END_MARKER
        
        try:
            # Send command
            self.socket.sendall(full_command)
            
            # Read response
            response = self.socket.recv(1024)
            
            # Check for ASCII error response (Network Control disabled)
            if PJNAK in response:
                raise JVCCommandError(f"Command rejected: {response}. Check that Network Control is enabled in projector settings.")
            
            # Expected ACK format: ACK (0x06) + UNIT_ID + first 2 bytes of command + END
            expected_ack = HEADER_ACK + UNIT_ID + command[:2] + END_MARKER
            ack_length = len(expected_ack)
            
            # For operation commands (!), expect only ACK
            if header == HEADER_OPERATION:
                if response == expected_ack:
                    return response
                else:
                    raise JVCCommandError(f"Unexpected response: {response.hex()} (expected ACK: {expected_ack.hex()})")
            
            # For reference commands (?), expect ACK followed by Response
            # ACK: 0x06 + UNIT_ID + CMD[:2] + END
            # Response: 0x40 (@) + UNIT_ID + CMD[:2] + DATA + END
            elif header == HEADER_REFERENCE:
                # Check if we got the ACK first
                if not response.startswith(expected_ack):
                    raise JVCCommandError(f"Expected ACK not found. Got: {response.hex()}")
                
                # Extract the response part after the ACK
                if len(response) > ack_length:
                    # Response is concatenated after ACK
                    response_data = response[ack_length:]
                else:
                    # Need to read the response separately
                    response_data = self.socket.recv(1024)
                
                # Parse the response: @ + UNIT_ID + CMD[:2] + DATA + END
                expected_response_header = HEADER_RESPONSE + UNIT_ID + command[:2]
                if response_data.startswith(expected_response_header) and response_data.endswith(END_MARKER):
                    # Extract data between header and END marker
                    data_start = len(expected_response_header)
                    data_end = -1  # Exclude END_MARKER
                    return response_data[data_start:data_end]
                else:
                    raise JVCCommandError(f"Unexpected response format: {response_data.hex()}")
            
            return response
            
        except socket.timeout:
            raise JVCCommandError("Command timeout - no response from projector")
        except socket.error as e:
            raise JVCConnectionError(f"Communication error: {e}")
        except JVCProjectorError:
            raise
        except Exception as e:
            raise JVCCommandError(f"Unexpected error: {e}")
    
    def send_operation(self, command: bytes, data: bytes = b'') -> bytes:
        """
        Send an operation command (header: !)
        
        Args:
            command: Command code
            data: Command parameters
            
        Returns:
            Response from projector
        """
        try:
            return self._send_command(HEADER_OPERATION, command, data)
        except JVCCommandError as e:
            error(f"Operation command failed: {e}")
            raise
        except JVCConnectionError as e:
            error(f"Connection error during operation command: {e}")
            raise
        except Exception as e:
            error(f"Unexpected error during operation command: {e}")
            raise JVCCommandError(f"Unexpected error: {e}")
    
    def send_reference(self, command: bytes, data: bytes = b'') -> bytes:
        """
        Send a reference/query command (header: ?)

        Args:
            command: Command code
            data: Command parameters

        Returns:
            Response from projector
        """
        try:
            return self._send_command(HEADER_REFERENCE, command, data)
        except JVCCommandError as e:
            error(f"Reference command failed: {e}")
            raise
        except JVCConnectionError as e:
            error(f"Connection error during reference command: {e}")
            raise
        except Exception as e:
            error(f"Unexpected error during reference command: {e}")
            raise JVCCommandError(f"Unexpected error: {e}")
           
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
