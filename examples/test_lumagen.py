"""
Example: Test Lumagen Connection
Test connectivity and query Lumagen Radiance status via USB serial
"""

import sys
import os
# Add parent directory to path so we can import jvclrpctl
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jvclrpctl import LumagenRadiance, LumagenCommands


def main():
    """Main test function"""
    
    print("=" * 60)
    print("Lumagen Radiance Connection Test")
    print("=" * 60)
    
    # Configuration - Update to match your serial port
    LUMAGEN_PORT = "/dev/cu.usbserial-BG0183YB"  # Linux/Mac: /dev/ttyUSB0, /dev/cu.usbserial
                                    # Windows: COM3, COM4, etc.
    
    print(f"\nConnecting to Lumagen on {LUMAGEN_PORT}...")
    
    # Using context manager
    with LumagenRadiance(LUMAGEN_PORT) as radiance:
        commands = LumagenCommands(radiance)
        
        # Test 1: Check if alive
        print("\n--- Test 1: Alive Check ---")
        if commands.get_alive_status():
            print("✓ Lumagen is responding")
        else:
            print("✗ No response from Lumagen")
            return
        
        # Test 2: Get device info
        print("\n--- Test 2: Device Information ---")
        info = commands.get_device_info()
        if info:
            print(f"  Model:         {info.get('model', 'N/A')}")
            print(f"  Firmware:      {info.get('firmware', 'N/A')}")
            print(f"  Model Number:  {info.get('model_number', 'N/A')}")
            print(f"  Serial Number: {info.get('serial_number', 'N/A')}")
        
        # Test 3: Check power status
        print("\n--- Test 3: Power Status ---")
        power = commands.get_power_status()
        print(f"  Power: {power}")
        
        # Test 4: Check HDR status
        print("\n--- Test 4: HDR Status ---")
        hdr_status = commands.get_hdr_status()
        print(f"  Is HDR:          {hdr_status.get('is_hdr', False)}")
        print(f"  Min Luminance:   {hdr_status.get('min_luminance', 0)}")
        print(f"  Max Luminance:   {hdr_status.get('max_luminance', 0)}")
        print(f"  Max CLL:         {hdr_status.get('max_cll', 0)}")
        
        # Test 5: Get full status
        print("\n--- Test 5: Full Status (v4) ---")
        status = commands.get_full_status_v4()
        if status:
            input_status_map = {0: 'No source', 1: 'Active video', 2: 'Internal pattern'}
            print(f"  Input Status:       {input_status_map.get(status.get('input_status', 0), 'Unknown')}")
            print(f"  Source Resolution:  {status.get('source_resolution', 0)}p")
            print(f"  Source Rate:        {status.get('source_rate', 0) / 100:.2f} Hz")
            print(f"  Source Aspect:      {status.get('source_aspect', 0) / 100:.2f}")
            print(f"  Is HDR:             {status.get('is_hdr', False)}")
            print(f"  Output Resolution:  {status.get('output_resolution', 0)}p")
            print(f"  Output Rate:        {status.get('output_rate', 0) / 100:.2f} Hz")
            print(f"  CMS Active:         {status.get('cms_active', 0)}")
            print(f"  Style Active:       {status.get('style_active', 0)}")
        
    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)


if __name__ == "__main__":
    main()
