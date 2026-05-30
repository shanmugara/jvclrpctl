"""
Example: Picture Mode Control
Demonstrates how to connect to a JVC projector and change picture modes
"""

import sys
import os
from time import sleep

# Add parent directory to path so we can import jvclrpctl
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jvclrpctl import JVCProjector, PictureMode
from jvclrpctl.jvcctl.picture_modes import PictureModeController

# Configuration
PROJECTOR_IP = "192.168.100.240"  # Change to your projector's IP address
PROJECTOR_PORT = 20554  # Default JVC port
TEST_WAIT_TIME = 10  # Seconds to wait between mode changes


def main():
    """Main example function"""
    
    print("=" * 60)
    print("JVC Projector Picture Mode Control Example")
    print("=" * 60)
    
    # Create projector connection
    projector = JVCProjector(PROJECTOR_IP, PROJECTOR_PORT)
    
    try:
        # Connect to projector
        print(f"\nConnecting to projector at {PROJECTOR_IP}:{PROJECTOR_PORT}...")
        projector.connect()
        
        # Create picture mode controller
        controller = PictureModeController(projector)
        
        # Display available picture modes
        controller.print_available_modes()
        
        # Example 1: Set picture mode using enum
        print("\n--- Setting picture mode to CINEMA ---")
        if controller.set_mode(PictureMode.CINEMA):
            print("✓ Successfully set picture mode to CINEMA")
        else:
            print("✗ Failed to set picture mode")

        sleep(TEST_WAIT_TIME)  # Wait before next change
        
        # Example 2: Set picture mode by name
        print("\n--- Setting picture mode to NATURAL ---")
        if controller.set_mode_by_name("Natural"):
            print("✓ Successfully set picture mode to NATURAL")
        else:
            print("✗ Failed to set picture mode")

        sleep(TEST_WAIT_TIME)  # Wait before next change
        
        # Example 3: Get current picture mode
        print("\n--- Querying current picture mode ---")
        current_mode = controller.get_current_mode()
        if current_mode:
            print(f"Current mode: {current_mode.display_name}")
        else:
            print("Could not determine current mode")
        
        # Example 4: Cycle through some modes
        print("\n--- Cycling through picture modes ---")
        test_modes = [PictureMode.FILM, PictureMode.NATURAL, PictureMode.USER3]
        
        for mode in test_modes:
            print(f"\nSwitching to {mode.display_name}...")
            if controller.set_mode(mode):
                print(f"  ✓ Set to {mode.display_name}")
                sleep(TEST_WAIT_TIME)  # Wait before next change
            else:
                print(f"  ✗ Failed to set {mode.display_name}")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Always disconnect
        projector.disconnect()
    
    print("\n" + "=" * 60)
    print("Example completed")
    print("=" * 60)


if __name__ == "__main__":
    main()
