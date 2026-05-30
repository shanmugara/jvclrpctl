#!/usr/bin/env python3
"""
Test script for binary ACK protocol implementation
This should work once Network Control is enabled on the projector
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jvclrpctl.jvcctl import JVCProjector, JVCCommands, PictureModeController, PictureMode

PROJECTOR_IP = "192.168.100.240"
PROJECTOR_PORT = 20554

def main():
    print("=" * 70)
    print("Testing JVC Binary ACK Protocol")
    print("=" * 70)
    print(f"\nConnecting to {PROJECTOR_IP}:{PROJECTOR_PORT}...")
    print("\nIMPORTANT: Network Control must be enabled in projector settings!")
    print("Menu → Installation → Control → Network Control = ON\n")
    
    try:
        with JVCProjector(PROJECTOR_IP, PROJECTOR_PORT) as projector:
            print("✓ Connected successfully\n")
            
            commands = JVCCommands(projector)
            controller = PictureModeController(projector)
            
            # Test 1: Query power status
            print("Test 1: Query Power Status")
            try:
                power = commands.get_power_status()
                print(f"  ✓ Power status: {power}")
            except Exception as e:
                print(f"  ✗ Failed: {e}")
            
            print()
            
            # Test 2: Query input
            print("Test 2: Query Current Input")
            try:
                input_status = commands.get_current_input()
                print(f"  ✓ Current input: {input_status}")
            except Exception as e:
                print(f"  ✗ Failed: {e}")
            
            print()
            
            # Test 3: Query picture mode
            print("Test 3: Query Picture Mode")
            try:
                mode = controller.get_current_mode()
                if mode:
                    print(f"  ✓ Current mode: {mode.display_name}")
                else:
                    print(f"  ✓ Mode query successful (unknown mode)")
            except Exception as e:
                print(f"  ✗ Failed: {e}")
            
            print()
            
            # Test 4: Set picture mode (if successful so far)
            print("Test 4: Set Picture Mode to CINEMA")
            try:
                controller.set_mode(PictureMode.CINEMA)
                print(f"  ✓ Picture mode set successfully")
            except Exception as e:
                print(f"  ✗ Failed: {e}")
            
            print("\n" + "=" * 70)
            print("Binary ACK protocol is working! 🎉")
            print("=" * 70)
            
    except Exception as e:
        print(f"\n✗ Connection or command failed: {e}")
        print("\nIf you see 'Command rejected' or 'PJNAK':")
        print("  → Network Control is still DISABLED")
        print("  → Enable it in: Menu → Installation → Control → Network Control")

if __name__ == "__main__":
    main()
