"""
Example: HDR Automation
Automatically switches JVC picture mode based on Lumagen HDR detection
"""

import sys
import os
import time

# Add parent directory to path so we can import jvclrpctl
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jvclrpctl import HDRAutomation, PictureMode


def on_mode_change(content_type: str, mode):
    """Callback function when mode changes"""
    print(f"\n*** Callback: Content changed to {content_type}, mode is {mode.display_name} ***\n")


def main():
    """Main automation example"""
    
    print("=" * 70)
    print("JVC + Lumagen HDR Automation")
    print("=" * 70)
    
    # Configuration
    JVC_IP = "192.168.1.100"              # Change to your JVC projector IP
    LUMAGEN_PORT = "/dev/ttyUSB0"         # Change to your serial port
                                           # Linux/Mac: /dev/ttyUSB0, /dev/cu.usbserial
                                           # Windows: COM3, COM4, etc.
    POLL_INTERVAL = 2.0                    # Check every 2 seconds
    
    print(f"\nConfiguration:")
    print(f"  JVC Projector:    {JVC_IP}")
    print(f"  Lumagen Radiance: {LUMAGEN_PORT}")
    print(f"  Poll Interval:    {POLL_INTERVAL}s")
    print(f"\nPicture Mode Mapping:")
    print(f"  SDR Content → USER1")
    print(f"  HDR Content → USER2")
    print()
    
    # Create automation instance
    automation = HDRAutomation(
        jvc_ip=JVC_IP,
        lumagen_port=LUMAGEN_PORT,
        poll_interval=POLL_INTERVAL,
        sdr_mode=PictureMode.USER1,
        hdr_mode=PictureMode.USER2,
        on_mode_change=on_mode_change  # Optional callback
    )
    
    try:
        # Start automation
        automation.start()
        
        print("\n" + "-" * 70)
        print("Automation is now running. Press Ctrl+C to stop.")
        print("-" * 70)
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
            # Optional: Print status every 30 seconds
            # status = automation.get_status()
            # print(f"Status: {status}")
    
    except KeyboardInterrupt:
        print("\n\nReceived interrupt signal...")
    
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Stop automation
        automation.stop()
    
    print("\n" + "=" * 70)
    print("Automation stopped")
    print("=" * 70)


if __name__ == "__main__":
    main()
