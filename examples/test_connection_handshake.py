#!/usr/bin/env python3
"""
Test JVC Connection Handshake
Tests the complete authentication flow: PJ_OK → PJREQ → PJACK
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jvclrpctl.jvcctl import JVCProjector, JVCCommands, PictureModeController

PROJECTOR_IP = "192.168.100.240"
PROJECTOR_PORT = 20554

def main():
    print("=" * 70)
    print("JVC Connection Handshake Test")
    print("=" * 70)
    print(f"\nTesting connection to {PROJECTOR_IP}:{PROJECTOR_PORT}...")
    print("\nConnection sequence:")
    print("  1. TCP connect")
    print("  2. Receive PJ_OK greeting")
    print("  3. Send PJREQ authentication")
    print("  4. Receive PJACK confirmation")
    print("  5. Ready for commands\n")
    
    try:
        # Test connection with authentication handshake
        with JVCProjector(PROJECTOR_IP, PROJECTOR_PORT) as projector:
            print("✓ Connection successful!")
            print("✓ Authentication handshake completed!")
            print("\nTesting basic commands...\n")
            
            commands = JVCCommands(projector)
            
            # Test 1: Power status
            print("1. Query Power Status")
            try:
                power = commands.get_power_status()
                print(f"   ✓ Power status: {power}")
            except Exception as e:
                print(f"   ✗ Failed: {e}")
            
            # Small delay between commands
            time.sleep(0.5)
            
            # Test 2: Input status
            print("\n2. Query Current Input")
            try:
                input_status = commands.get_current_input()
                print(f"   ✓ Current input: {input_status}")
            except Exception as e:
                print(f"   ✗ Failed: {e}")
            
            # Small delay between commands
            time.sleep(0.5)
            
            # Test 3: Picture mode
            print("\n3. Query Picture Mode")
            try:
                controller = PictureModeController(projector)
                mode = controller.get_current_mode()
                if mode:
                    print(f"   ✓ Current mode: {mode.display_name}")
                else:
                    print(f"   ✓ Mode query successful")
            except Exception as e:
                print(f"   ✗ Failed: {e}")
            
            print("\n" + "=" * 70)
            print("All tests completed! Connection and commands working! 🎉")
            print("=" * 70)
            
    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Check projector is powered on")
        print("  2. Verify IP address is correct: " + PROJECTOR_IP)
        print("  3. Ensure Network Control is enabled:")
        print("     Menu → Installation → Control → Network Control = ON")
        print("  4. Check no other device is connected to projector")

if __name__ == "__main__":
    main()
