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
PM_SETTLE_TIME = 6  # Seconds to wait after changing picture mode before checking again
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
        self.pm_controller = None
        self.lumagen = None
        self.lumagen_commands = None
        self.lumagen_input_mode = LRPInputModes.NA

    def connect_lumagen(self):
        """Connect to the Lumagen and initialize commands"""
        debug(f"Connecting to Lumagen on {self.lumagen_port}...")
        self.lumagen = LumagenRadiance(self.lumagen_port)
        if self.lumagen.connect():
            debug("Lumagen connected!")
            self.lumagen_commands = LumagenCommands(self.lumagen)
            debug("Lumagen commands initialized!")
            return True
        else:
            error("Failed to connect to Lumagen")
            return False
    
    def connect_projector(self):
        """Connect to the projector and initialize picture mode controller"""
        debug(f"Connecting to JVC projector at {self.projector_ip}:{self.projector_port}...")
        self.projector = JVCProjector(self.projector_ip, self.projector_port)

        if self.projector.connect():
            debug("Connected to projector!")
            self.pm_controller = PictureModeController(self.projector)
            debug("Picture mode controller initialized!")
            return True
        else:
            error("Failed to connect to projector")
            return False
    
    def disconnect(self):
        """Disconnect from all devices"""
        if self.projector:
            self.projector.disconnect()
            debug("Disconnected from projector")
        
        if self.lumagen:
            self.lumagen.disconnect()
            debug("Disconnected from Lumagen")
    
    def disconnect_projector(self):
        """Disconnect from the projector"""
        if self.projector:
            self.projector.disconnect()
            debug("Disconnected from projector")

    def get_lumagen_input_mode(self):
        """Get current Lumagen input mode"""
        try:
            hdr_status = self.lumagen_commands.get_hdr_status()
            debug(f"Input status response: {hdr_status}")
            error_msg = hdr_status.get("error")
            if error_msg:
                error(f"Lumagen HDR status error: {error_msg}")
                return LRPInputModes.ERR

            is_hdr = hdr_status.get("is_hdr", False)
            if is_hdr:
                return LRPInputModes.HDR
            else:
                return LRPInputModes.SDR
    
        except Exception as e:
            error(f"Failed to get Lumagen input mode: {e}")
            return LRPInputModes.ERR
    
    def set_jvc_picture_mode(self, mode: PictureMode, initial_run=False):
        """Set the projector picture mode"""
        if not initial_run:
            info(f"Wait for projector {PM_SETTLE_TIME} sec...")
            sleep(PM_SETTLE_TIME)

        # connect_projector() raises JVCConnectionError on failure
        self.connect_projector()

        info(f"Setting picture mode to {mode.display_name}...")
        try:
            if self.pm_controller.set_mode(mode):
                info(f"SET: {mode.display_name}\n")
            else:
                debug(f"FAIL: {mode.display_name}\n")
                raise RuntimeError(f"FAIL: {mode.display_name}")
        except Exception as e:
            debug(f"Error setting JVC picture mode: {e}")
            raise
        finally:
            self.disconnect_projector()

    def get_jvc_picture_mode(self):
        """Get the current projector picture mode"""
        # connect_projector() raises JVCConnectionError on failure
        self.connect_projector()
        try:
            mode = self.pm_controller.get_current_mode()
            if mode is not None:
                debug(f"Current JVC picture mode: {mode.display_name}")
                return mode
            else:
                debug("Current JVC picture mode is unknown")
                raise ValueError("Unknown JVC picture mode")
        except Exception as e:
            debug(f"Error querying current JVC picture mode: {e}")
            raise
        finally:
            self.disconnect_projector()
    
    def jvc_confirm_picture_mode(self, expected_mode: PictureMode) -> bool:
        """Confirm that the projector is currently set to the expected picture mode"""
        try:
            current_mode = self.get_jvc_picture_mode()
            if current_mode == expected_mode:
                debug(f"JVC picture mode confirmed: {current_mode.display_name}")
                return True
            else:
                debug(f"JVC picture mode mismatch: expected {expected_mode.display_name}, got {current_mode.display_name}")
                return False
        except Exception as e:
            debug(f"Error confirming JVC picture mode: {e}")
            return False

    def run(self):
        """Run the main test sequence"""
        try:
            # Connect to Lumagen
            if not self.connect_lumagen():
                error("Failed to connect to Lumagen. Aborting run.")
                return
            # Get current HDR mode from Lumagen
            debug("Checking Lumagen input status...")
            current_input_mode = self.get_lumagen_input_mode()

            debug(f"Current Lumagen input mode: {current_input_mode.name}")
            debug(f"Last known Lumagen input mode: {self.lumagen_input_mode.name}")

            if current_input_mode == LRPInputModes.ERR:
                error("Error retrieving Lumagen input mode. Skipping this cycle.")
                return
            
            if current_input_mode == self.lumagen_input_mode:
                debug("Lumagen input status has not changed since last check.")
                return
            
            if self.lumagen_input_mode == LRPInputModes.NA:
                _initial_run = True
                debug("Initial run detected. Verifying current JVC picture mode...")
                try:
                    current_jvc_mode = self.get_jvc_picture_mode()
                except Exception as e:
                    error(f"Could not read current JVC picture mode: {e}. Skipping this cycle.")
                    return
                # if current_jvc_mode is None:
                #     error("Could not read current JVC picture mode. Skipping this cycle.")
                #     return
                # else:
                debug(f"Current JVC picture mode: {current_jvc_mode.display_name}")
                if current_input_mode == LRPInputModes.HDR and current_jvc_mode == JVC_PICTURE_MODE_HDR:
                    debug("JVC picture mode matches for HDR input mode. No change needed.")
                    info("✓ HDR\n")
                    self.lumagen_input_mode = current_input_mode
                    return
                elif current_input_mode == LRPInputModes.SDR and current_jvc_mode == JVC_PICTURE_MODE_SDR:
                    debug("JVC picture mode matches for SDR input mode. No change needed.")
                    info("✓ SDR\n")
                    self.lumagen_input_mode = current_input_mode
                    return
            else:
                _initial_run = False
            # Set JVC picture mode based on HDR status
            
            if current_input_mode == LRPInputModes.HDR:
                debug("HDR input detected. Setting JVC picture mode to HDR...")
                info("HDR → USER3")
                try:
                    # set_jvc_picture_mode raises if set_mode could not verify, so a
                    # clean return means the mode is set and verified on the live
                    # connection. Avoid a redundant reconnect-confirm here: the
                    # projector refuses TCP connects for a moment after a switch.
                    self.set_jvc_picture_mode(JVC_PICTURE_MODE_HDR, _initial_run)
                    debug("updating last known input mode to HDR")
                    self.lumagen_input_mode = current_input_mode
                except Exception as e:
                    error(f"Failed to set JVC picture mode to HDR: {e}")

            elif current_input_mode == LRPInputModes.SDR:
                debug("SDR input detected. Setting JVC picture mode to SDR...")
                info("SDR → USER1")
                try:
                    # set_mode already verifies on the live connection; skip the
                    # redundant reconnect-confirm (projector refuses TCP connects
                    # briefly after a switch).
                    self.set_jvc_picture_mode(JVC_PICTURE_MODE_SDR, _initial_run)  # USER1 for SDR
                    debug("updating last known input mode to SDR")
                    self.lumagen_input_mode = current_input_mode
                except Exception as e:
                    error(f"Failed to set JVC picture mode to SDR: {e}")
            else:
                debug(f"Unknown Lumagen input mode: {current_input_mode}. No action taken.")
                
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