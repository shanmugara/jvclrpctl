import sys
import os
from time import sleep

# Add parent directory to path so we can import jvclrpctl
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jvclrpctl import JVCProjector, PictureMode
from jvclrpctl.jvcctl.picture_modes import PictureModeController
from jvclrpctl import LumagenRadiance, LumagenCommands
from jvclrpctl.lumagen.constants import LRPInputModes

# Configuration
PROJECTOR_IP = "192.168.100.240"  # Change to your projector's IP address
PROJECTOR_PORT = 20554  # Default JVC port
POLLING_INTERVAL = 2  # Seconds to wait between mode changes
LUMAGEN_PORT = "/dev/ttyUSB0"  # Change to your Lumagen serial port (e.g., /dev/ttyUSB0, /dev/cu.usbserial, COM3, etc.)


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
        print(f"Connecting to JVC projector at {self.projector_ip}:{self.projector_port}...")
        self.projector = JVCProjector(self.projector_ip, self.projector_port)
        self.projector.connect()
        print("✓ Connected to projector!")
        
        self.picture_mode_controller = PictureModeController(self.projector)
        print("✓ Picture mode controller initialized!")

        print(f"Connecting to Lumagen on {self.lumagen_port}...")
        self.lumagen = LumagenRadiance(self.lumagen_port)
        self.lumagen.connect()
        print("✓ Lumagen connected!")
        
        self.lumagen_commands = LumagenCommands(self.lumagen)
        print("✓ Lumagen commands initialized!")
    
    def disconnect(self):
        """Disconnect from all devices"""
        if self.projector:
            self.projector.disconnect()
            print("✓ Disconnected from projector")
        
        if self.lumagen:
            self.lumagen.disconnect()
            print("✓ Disconnected from Lumagen")

    def get_lumagen_hdr_mode(self):
        """Get current Lumagen HDR mode"""
        try:
            hdr_status = self.lumagen_commands.get_hdr_status()
            is_hdr = hdr_status.get("is_hdr", False)
            if is_hdr:
                return LRPInputModes.HDR
            else:
                return LRPInputModes.SDR
    
        except Exception as e:
            print(f"✗ Failed to get Lumagen HDR mode: {e}")
            return LRPInputModes.NA
    
    def set_jvc_picture_mode(self, mode: PictureMode):
        """Set the projector picture mode"""
        print(f"Setting picture mode to {mode.display_name}...")
        if self.picture_mode_controller.set_mode(mode):
            print(f"✓ Picture mode set to {mode.display_name}")
        else:
            print(f"✗ Failed to set picture mode to {mode.display_name}")

    def run(self):
        """Run the main test sequence"""
        try:
            # Connect to both devices
            self.connect()
            # Get current HDR mode from Lumagen
            print("\nChecking Lumagen HDR status...")
            current_hdr_mode = self.get_lumagen_hdr_mode()

            print(f"Current Lumagen HDR mode: {current_hdr_mode.name}")
            print(f"Last known Lumagen HDR mode: {self.lumagen_hdr_mode.name}")
            
            if current_hdr_mode == self.lumagen_hdr_mode:
                print("✓ Lumagen HDR status has not changed since last check.")
                return
            
            # Set JVC picture mode based on HDR status
            
            if current_hdr_mode == LRPInputModes.HDR:
                print("\nLumagen is in HDR mode, setting JVC picture mode to USER3...")
                self.set_jvc_picture_mode(PictureMode.USER3)  # USER3 for HDR
                self.lumagen_hdr_mode = current_hdr_mode
            elif current_hdr_mode == LRPInputModes.SDR:
                print("\nLumagen is in SDR mode, setting JVC picture mode to USER1...")
                self.set_jvc_picture_mode(PictureMode.USER1)  # USER1 for SDR
                self.lumagen_hdr_mode = current_hdr_mode
            
            print("\n✓ Run completed successfully!")
            
        except Exception as e:
            print(f"\n✗ Error during run: {e}")
        finally:
            # Always disconnect at the end
            self.disconnect()


if __name__ == "__main__":
    print("=" * 70)
    print("JVC-LRP Runner - HDR Mode Detection and Picture Mode Control")
    print("=" * 70)
    
    runner = JVC_LRP_Runner()
    runner.run()

def poll(runner: JVC_LRP_Runner, interval=POLLING_INTERVAL):
    """Poll the Lumagen HDR status at regular intervals"""
    try:
        while True:
            print("\nPolling Lumagen HDR status...")
            runner.run()
            print(f"\nWaiting for {interval} seconds before next poll...")
            sleep(interval)
    except KeyboardInterrupt:
        print("\nPolling stopped by user.")

