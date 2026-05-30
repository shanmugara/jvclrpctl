"""
Example: Interactive Picture Mode Selector
Interactive CLI tool for selecting picture modes
"""

import sys
import os

# Add parent directory to path so we can import jvclrpctl
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jvclrpctl import JVCProjector, PictureMode
from jvclrpctl.jvcctl.picture_modes import PictureModeController

# Configuration
PROJECTOR_IP = "192.168.1.100"  # Change to your projector's IP address
PROJECTOR_PORT = 20554


def display_menu(controller: PictureModeController):
    """Display available picture modes menu"""
    print("\n" + "=" * 60)
    print("JVC Projector - Picture Mode Selector")
    print("=" * 60)
    
    modes = PictureMode.list_all()
    for idx, mode in enumerate(modes, 1):
        print(f"  {idx:2d}. {mode.display_name}")
    
    print("\n  0. Exit")
    print("=" * 60)


def main():
    """Main interactive function"""
    
    # Create projector connection
    projector = JVCProjector(PROJECTOR_IP, PROJECTOR_PORT)
    
    try:
        print(f"Connecting to projector at {PROJECTOR_IP}...")
        projector.connect()
        print("✓ Connected!\n")
        
        # Create picture mode controller
        controller = PictureModeController(projector)
        
        # Interactive loop
        while True:
            display_menu(controller)
            
            try:
                choice = input("\nSelect picture mode (0 to exit): ").strip()
                
                if choice == "0":
                    print("\nExiting...")
                    break
                
                idx = int(choice)
                modes = PictureMode.list_all()
                
                if 1 <= idx <= len(modes):
                    selected_mode = modes[idx - 1]
                    print(f"\nSetting picture mode to: {selected_mode.display_name}")
                    
                    if controller.set_mode(selected_mode):
                        print(f"✓ Successfully changed to {selected_mode.display_name}")
                    else:
                        print(f"✗ Failed to change picture mode")
                else:
                    print(f"Invalid choice. Please enter 1-{len(modes)} or 0 to exit.")
                    
            except ValueError:
                print("Invalid input. Please enter a number.")
            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Exiting...")
                break
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        projector.disconnect()
        print("Disconnected from projector.")


if __name__ == "__main__":
    main()
