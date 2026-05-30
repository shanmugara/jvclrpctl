"""
HDR Automation Module
Polls Lumagen for HDR status and automatically adjusts JVC picture mode
"""

import time
import threading
from typing import Optional, Callable
from .jvcctl import JVCProjector, PictureMode, PictureModeController
from .lumagen import LumagenRadiance, LumagenCommands


class HDRAutomation:
    """
    Automated HDR detection and JVC picture mode switching
    
    Polls Lumagen Radiance at regular intervals to detect HDR vs SDR content
    and automatically switches JVC projector picture mode accordingly.
    
    Example:
        >>> automation = HDRAutomation(
        ...     jvc_ip='192.168.1.100',
        ...     lumagen_ip='192.168.1.50',
        ...     poll_interval=2.0,
        ...     sdr_mode=PictureMode.USER1,
        ...     hdr_mode=PictureMode.USER2
        ... )
        >>> automation.start()
        >>> # ... runs in background ...
        >>> automation.stop()
    """
    
    def __init__(
        self,
        jvc_ip: str,
        lumagen_port: str,
        poll_interval: float = 2.0,
        sdr_mode: PictureMode = PictureMode.USER1,
        hdr_mode: PictureMode = PictureMode.USER2,
        jvc_port: int = 20554,
        lumagen_baudrate: int = 9600,
        on_mode_change: Optional[Callable[[str, PictureMode], None]] = None
    ):
        """
        Initialize HDR automation
        
        Args:
            jvc_ip: IP address of JVC projector
            lumagen_port: Serial port for Lumagen (e.g., '/dev/ttyUSB0', 'COM3')
            poll_interval: How often to check HDR status (seconds)
            sdr_mode: Picture mode to use for SDR content
            hdr_mode: Picture mode to use for HDR content
            jvc_port: JVC projector TCP port (default: 20554)
            lumagen_baudrate: Lumagen serial baudrate (default: 9600)
            on_mode_change: Optional callback function(content_type, mode)
        """
        self.jvc_ip = jvc_ip
        self.lumagen_port = lumagen_port
        self.poll_interval = poll_interval
        self.sdr_mode = sdr_mode
        self.hdr_mode = hdr_mode
        self.jvc_port = jvc_port
        self.lumagen_baudrate = lumagen_baudrate
        self.on_mode_change = on_mode_change
        
        # State tracking
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_hdr_state: Optional[bool] = None
        
        # Device connections (created when starting)
        self.jvc: Optional[JVCProjector] = None
        self.jvc_controller: Optional[PictureModeController] = None
        self.lumagen: Optional[LumagenRadiance] = None
        self.lumagen_commands: Optional[LumagenCommands] = None
    
    def _connect_devices(self):
        """Connect to both JVC and Lumagen"""
        print(f"Connecting to JVC at {self.jvc_ip}...")
        self.jvc = JVCProjector(self.jvc_ip, self.jvc_port)
        self.jvc.connect()
        self.jvc_controller = PictureModeController(self.jvc)
        
        print(f"Connecting to Lumagen on {self.lumagen_port}...")
        self.lumagen = LumagenRadiance(self.lumagen_port, self.lumagen_baudrate)
        self.lumagen.connect()
        self.lumagen_commands = LumagenCommands(self.lumagen)
        
        print("✓ Both devices connected")
    
    def _disconnect_devices(self):
        """Disconnect from both devices"""
        if self.jvc:
            self.jvc.disconnect()
            self.jvc = None
            self.jvc_controller = None
        
        if self.lumagen:
            self.lumagen.disconnect()
            self.lumagen = None
            self.lumagen_commands = None
        
        print("Disconnected from devices")
    
    def _poll_loop(self):
        """Main polling loop (runs in background thread)"""
        print(f"HDR automation started (polling every {self.poll_interval}s)")
        print(f"  SDR → {self.sdr_mode.display_name}")
        print(f"  HDR → {self.hdr_mode.display_name}")
        print()
        
        while self._running:
            try:
                # Query Lumagen for HDR status
                is_hdr = self.lumagen_commands.is_hdr()
                
                # Check if HDR state changed
                if is_hdr != self._last_hdr_state:
                    content_type = "HDR" if is_hdr else "SDR"
                    target_mode = self.hdr_mode if is_hdr else self.sdr_mode
                    
                    print(f"\n[{time.strftime('%H:%M:%S')}] Content type changed: {content_type}")
                    print(f"  → Switching JVC to {target_mode.display_name}...")
                    
                    # Switch JVC picture mode
                    success = self.jvc_controller.set_mode(target_mode)
                    
                    if success:
                        print(f"  ✓ Picture mode changed to {target_mode.display_name}")
                        self._last_hdr_state = is_hdr
                        
                        # Call callback if provided
                        if self.on_mode_change:
                            self.on_mode_change(content_type, target_mode)
                    else:
                        print(f"  ✗ Failed to change picture mode")
                
                # Wait before next poll
                time.sleep(self.poll_interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error in polling loop: {e}")
                time.sleep(self.poll_interval)
    
    def start(self):
        """Start the HDR automation (runs in background thread)"""
        if self._running:
            print("Automation already running")
            return
        
        try:
            # Connect to devices
            self._connect_devices()
            
            # Start polling thread
            self._running = True
            self._thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._thread.start()
            
        except Exception as e:
            print(f"Failed to start automation: {e}")
            self._disconnect_devices()
            raise
    
    def stop(self):
        """Stop the HDR automation"""
        if not self._running:
            return
        
        print("\nStopping HDR automation...")
        self._running = False
        
        # Wait for thread to finish
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        
        # Disconnect devices
        self._disconnect_devices()
        
        print("Automation stopped")
    
    def get_status(self) -> dict:
        """
        Get current automation status
        
        Returns:
            Dictionary with current state information
        """
        if not self._running:
            return {'running': False}
        
        try:
            hdr_status = self.lumagen_commands.get_hdr_status()
            
            return {
                'running': True,
                'current_mode': 'HDR' if self._last_hdr_state else 'SDR',
                'is_hdr': hdr_status['is_hdr'],
                'lumagen_connected': self.lumagen.is_connected(),
                'jvc_connected': self.jvc.is_connected(),
            }
        except:
            return {
                'running': True,
                'error': 'Failed to get status'
            }
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
