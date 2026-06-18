import sys
import os
import contextlib
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
PM_SETTLE_TIME = 4  # Seconds to wait after changing picture mode before checking again
LUMAGEN_PORT = "/dev/ttyUSB0"  # Change to your Lumagen serial port (e.g., /dev/ttyUSB0, /dev/cu.usbserial, COM3, etc.)
JVC_PICTURE_MODE_HDR = PictureMode.USER3  # Picture mode to use when HDR is detected
JVC_PICTURE_MODE_SDR = PictureMode.USER1  # Picture mode to use when SDR is detected
# DEBUG is automatically set from environment variable (DEBUG=true or DEBUG=false)
# When DEBUG=true, debug messages will be visible


class JVC_LRP_Runner:
    """Runner class for JVC LRP testing"""

    def __init__(self, projector_ip=PROJECTOR_IP, projector_port=PROJECTOR_PORT,
                 lumagen_port=LUMAGEN_PORT, lumagen_lock=None, lumagen_control=None):
        self.projector_ip = projector_ip
        self.projector_port = projector_port
        self.lumagen_port = lumagen_port
        self.projector = None
        self.pm_controller = None
        self.lumagen = None
        self.lumagen_commands = None
        self.lumagen_input_mode = LRPInputModes.NA
        # Runtime-configurable picture modes and settle time (can be updated live).
        self.hdr_mode   = JVC_PICTURE_MODE_HDR
        self.sdr_mode   = JVC_PICTURE_MODE_SDR
        self.settle_time = PM_SETTLE_TIME
        # Optional threading.Lock for shared serial port access (used when embedded
        # in the Flask app). When None (standalone), a no-op context is used.
        self._lumagen_lock = lumagen_lock if lumagen_lock is not None else contextlib.nullcontext()
        # Optional LumagenControl from the Flask app. When set, the runner reuses
        # this object for serial access instead of creating its own LumagenRadiance,
        # so only one serial connection ever opens /dev/ttyUSB0.
        self._lumagen_control = lumagen_control

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

    def _hdr_via_control(self) -> LRPInputModes:
        """Query ZQI52 through the shared LumagenControl (embedded mode only)."""
        try:
            response = self._lumagen_control.send_command("ZQI52")
            parts = response.split(',')
            if parts and not parts[0].lstrip('-').isdigit():
                parts = parts[1:]
            if len(parts) >= 4:
                v = int(parts[0])
                return LRPInputModes.HDR if v == 1 else LRPInputModes.SDR
            error(f"Unexpected ZQI52 response: {response!r}")
            return LRPInputModes.ERR
        except Exception as e:
            error(f"Failed to get HDR status: {e}")
            return LRPInputModes.ERR

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
            info(f"Wait for projector {self.settle_time} sec...")
            sleep(self.settle_time)

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
        """Run the main polling cycle."""
        current_input_mode = None
        try:
            # ── Lumagen phase (lock held only here) ───────────────────────
            with self._lumagen_lock:
                if self._lumagen_control is not None:
                    # Embedded: reuse the Flask app's LumagenControl so only
                    # one serial object ever opens /dev/ttyUSB0.
                    debug("Checking Lumagen input status (shared control)...")
                    current_input_mode = self._hdr_via_control()
                else:
                    # Standalone: create our own LumagenRadiance connection.
                    if not self.connect_lumagen():
                        error("Failed to connect to Lumagen. Aborting run.")
                        return
                    debug("Checking Lumagen input status...")
                    current_input_mode = self.get_lumagen_input_mode()
                    if self.lumagen:
                        self.lumagen.disconnect()
                        self.lumagen = None

            # ── Evaluation (no devices held) ──────────────────────────────
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
                debug(f"Current JVC picture mode: {current_jvc_mode.display_name}")
                if current_input_mode == LRPInputModes.HDR and current_jvc_mode == self.hdr_mode:
                    debug("JVC picture mode matches for HDR input mode. No change needed.")
                    info("✓ HDR\n")
                    self.lumagen_input_mode = current_input_mode
                    return
                elif current_input_mode == LRPInputModes.SDR and current_jvc_mode == self.sdr_mode:
                    debug("JVC picture mode matches for SDR input mode. No change needed.")
                    info("✓ SDR\n")
                    self.lumagen_input_mode = current_input_mode
                    return
            else:
                _initial_run = False

            # ── JVC phase (lock NOT held; serial port free) ───────────────
            if current_input_mode == LRPInputModes.HDR:
                debug("HDR input detected. Setting JVC picture mode to HDR...")
                info(f"HDR → {self.hdr_mode.display_name}")
                try:
                    self.set_jvc_picture_mode(self.hdr_mode, _initial_run)
                    debug("updating last known input mode to HDR")
                    self.lumagen_input_mode = current_input_mode
                except Exception as e:
                    error(f"Failed to set JVC picture mode to HDR: {e}")
            elif current_input_mode == LRPInputModes.SDR:
                debug("SDR input detected. Setting JVC picture mode to SDR...")
                info(f"SDR → {self.sdr_mode.display_name}")
                try:
                    self.set_jvc_picture_mode(self.sdr_mode, _initial_run)
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
            self.disconnect()  # clean up projector if still connected


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