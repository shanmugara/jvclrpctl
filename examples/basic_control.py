"""
Example: Basic Projector Control
Demonstrates basic power and input control operations
"""

import sys
import os
import time

# Add parent directory to path so we can import jvclrpctl
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jvclrpctl import JVCProjector, JVCCommands

# Configuration
PROJECTOR_IP = "192.168.100.240"  # Change to your projector's IP address
PROJECTOR_PORT = 20554


def main():
    """Main example function"""
    
    print("JVC Projector Basic Control Example")
    print("=" * 50)
    
    # Using context manager for automatic connection/disconnection
    with JVCProjector(PROJECTOR_IP, PROJECTOR_PORT) as projector:
        # Create command interface
        commands = JVCCommands(projector)
        
        # Check power status
        print("\n1. Checking power status...")
        try:
            status = commands.get_power_status()
            print(f"   Power status: {status}")
        except Exception as e:
            print(f"   Power status query not supported: {str(e)}")
            print("   (This is normal for some JVC projectors)")
            status = "unknown"
        
        # Power on (if needed) - skip if status unknown
        if status == "standby":
            print("\n2. Turning projector on...")
            if commands.power_on():
                print("   ✓ Power on command sent")
                print("   Waiting for projector to warm up (30 seconds)...")
                time.sleep(30)
            else:
                print("   ✗ Failed to power on")
                return
        elif status == "unknown":
            print("\n2. Skipping power on (status unknown - assume already on)")
        
        # Select HDMI 1
        print("\n3. Selecting HDMI 1 input...")
        try:
            if commands.select_hdmi_1():
                print("   ✓ Switched to HDMI 1")
            else:
                print("   ✗ Failed to switch input")
        except Exception as e:
            print(f"   HDMI 1 command not supported: {str(e)}")
        
        time.sleep(2)
        
        # Select HDMI 2
        print("\n4. Selecting HDMI 2 input...")
        try:
            if commands.select_hdmi_2():
                print("   ✓ Switched to HDMI 2")
            else:
                print("   ✗ Failed to switch input")
        except Exception as e:
            print(f"   HDMI 2 command not supported: {str(e)}")
        
        # Check current input
        print("\n5. Checking current input...")
        try:
            current_input = commands.get_current_input()
            print(f"   Current input: {current_input}")
        except Exception as e:
            print(f"   Input status query not supported: {str(e)}")
            print("   (This is normal for some JVC projectors)")
        
        # Note: Uncomment below to power off
        # print("\n6. Powering off projector...")
        # if commands.power_off():
        #     print("   ✓ Power off command sent")
        # else:
        #     print("   ✗ Failed to power off")
    
    print("\n" + "=" * 50)
    print("Example completed")


if __name__ == "__main__":
    main()
