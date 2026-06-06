import sys
import os
from time import sleep

# Add parent directory to path so we can import jvclrpctl
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jvclrpctl import JVCProjector, PictureMode
from jvclrpctl.jvcctl.picture_modes import PictureModeController
from jvclrpctl import LumagenRadiance, LumagenCommands
from jvclrpctl.lumagen.constants import LRPInputModes
from jvclrpctl import DEBUG, info, debug, warn, error, raw

# Configuration
PROJECTOR_IP = "192.168.100.240"  # Change to your projector's IP address
PROJECTOR_PORT = 20554  # Default JVC port
POLLING_INTERVAL = 2  # Seconds to wait between mode changes
LUMAGEN_PORT = "/dev/ttyUSB0"  # Change to your Lumagen serial port (e.g., /dev/ttyUSB0, /dev/cu.usbserial, COM3, etc.)
JVC_PICTURE_MODE_HDR = PictureMode.USER3  # Picture mode to use when HDR is detected
JVC_PICTURE_MODE_SDR = PictureMode.USER1  # Picture mode to use when SDR is detected
# DEBUG is automatically set from environment variable (DEBUG=true or DEBUG=false)
# When DEBUG=true, debug messages will be visible


class JVC_LRP_Runner:
    """Runner class for JVC LRP testing"""
    
    def __init__(self, projector_ip=PROJECTOR_IP, projector_port=PROJECTOR_PORT, lumagen_port=LUMAGEN_PORT):
        self.projector_ip = projector_ip
        self.projector_port = projector_port
        self.lumagen_port = lumagen_port
        self.projector = None
        self.picture_mode_controller = None
        self.lumagen = None
        self.lumagen_commands = None
        self.lumagen_hdr_mode = LRPInputModes.NA
    
    def connect(self):
        """Connect to the projector and initialize controllers"""
        debug(f"Connecting to JVC projector at {self.projector_ip}:{self.projector_port}...")
        self.projector = JVCProjector(self.projector_ip, self.projector_port)
        self.projector.connect()
        debug("Connected to projector!")
        
        self.picture_mode_controller = PictureModeController(self.projector)
        debug("Picture mode controller initialized!")

        debug(f"Connecting to Lumagen on {self.lumagen_port}...")
        self.lumagen = LumagenRadiance(self.lumagen_port)
        self.lumagen.connect()
        debug("Lumagen connected!")
        
        self.lumagen_commands = LumagenCommands(self.lumagen)
        debug("Lumagen commands initialized!")
    
    def disconnect(self):
        """Disconnect from all devices"""
        if self.projector:
            self.projector.disconnect()
            debug("Disconnected from projector")
        
        if self.lumagen:
            self.lumagen.disconnect()
            debug("Disconnected from Lumagen")

    def get_lumagen_hdr_mode(self):
        """Get current Lumagen HDR mode"""
        try:
            hdr_status = self.lumagen_commands.get_hdr_status()
            debug(f"HDR status response: {hdr_status}")
            is_hdr = hdr_status.get("is_hdr", False)
            if is_hdr:
                return LRPInputModes.HDR
            else:
                return LRPInputModes.SDR
    
        except Exception as e:
            error(f"Failed to get Lumagen HDR mode: {e}")
            return LRPInputModes.NA
    
    def set_jvc_picture_mode(self, mode: PictureMode):
        """Set the projector picture mode"""
        debug(f"Setting picture mode to {mode.display_name}...")
        if self.picture_mode_controller.set_mode(mode):
            info(f"SET: {mode.display_name}\n")
        else:
            error(f"FAIL: {mode.display_name}\n")

    def run(self):
        """Run the main test sequence"""
        try:
            # Connect to both devices
            self.connect()
            # Get current HDR mode from Lumagen
            debug("Checking Lumagen HDR status...")
            current_hdr_mode = self.get_lumagen_hdr_mode()

            debug(f"Current Lumagen HDR mode: {current_hdr_mode.name}")
            debug(f"Last known Lumagen HDR mode: {self.lumagen_hdr_mode.name}")
            
            if current_hdr_mode == self.lumagen_hdr_mode:
                debug("Lumagen HDR status has not changed since last check.")
                return
            
            if self.lumagen_hdr_mode == LRPInputModes.NA:
                current_jvc_mode = self.picture_mode_controller.get_current_mode()
                debug(f"Initial JVC picture mode: {current_jvc_mode.display_name}")
                if current_hdr_mode == LRPInputModes.HDR and current_jvc_mode == JVC_PICTURE_MODE_HDR:
                    debug("Initial state is already correct for HDR. No change needed.")
                    info("✓ HDR\n")
                    self.lumagen_hdr_mode = current_hdr_mode
                    return
                elif current_hdr_mode == LRPInputModes.SDR and current_jvc_mode == JVC_PICTURE_MODE_SDR:
                    debug("Initial state is already correct for SDR. No change needed.")
                    info("✓ SDR\n")
                    self.lumagen_hdr_mode = current_hdr_mode
                    return
            
            # Set JVC picture mode based on HDR status
            
            if current_hdr_mode == LRPInputModes.HDR:
                info("HDR → U3")
                self.set_jvc_picture_mode(JVC_PICTURE_MODE_HDR)  # USER3 for HDR
                self.lumagen_hdr_mode = current_hdr_mode
            elif current_hdr_mode == LRPInputModes.SDR:
                info("SDR → U1")
                self.set_jvc_picture_mode(JVC_PICTURE_MODE_SDR)  # USER1 for SDR
                self.lumagen_hdr_mode = current_hdr_mode
            
            debug("Run completed successfully!")
            
        except Exception as e:
            error(f"Error during run: {e}")
        finally:
            # Always disconnect at the end
            self.disconnect()


def poll(runner: JVC_LRP_Runner, interval=POLLING_INTERVAL):
    """Poll the Lumagen HDR status at regular intervals"""
    info(f"Starting polling with interval of {interval} seconds...")
    # raw(f"\n--Starting polling loop with interval of {interval} seconds...")
    try:
        while True:
            runner.run()
            debug(f"\nWaiting for {interval} seconds before next poll...")
            debug("sleeping...")
            sleep(interval)
    except KeyboardInterrupt:
        warn("\nPolling stopped by user.")

if __name__ == "__main__":
    raw("=" * 70)
    raw("JVC-LRP Runner - HDR Mode Detection and Picture Mode Control")
    raw("=" * 70)
    
    runner = JVC_LRP_Runner()
    poll(runner, interval=POLLING_INTERVAL)