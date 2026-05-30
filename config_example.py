"""
Configuration example for jvclrpctl
Copy this file and customize it for your setup
"""

# JVC Projector Configuration
JVC_CONFIG = {
    # IP address of your JVC projector
    'host': '192.168.1.100',
    
    # TCP port (default for JVC projectors is 20554)
    'port': 20554,
    
    # Connection timeout in seconds
    'timeout': 5.0,
}

# Lumagen Radiance Configuration
LUMAGEN_CONFIG = {
    # Serial port for Lumagen (USB connection)
    # Linux/Mac: '/dev/ttyUSB0', '/dev/cu.usbserial', etc.
    # Windows: 'COM3', 'COM4', etc.
    'port': '/dev/ttyUSB0',
    
    # Serial baud rate (default is 9600)
    'baudrate': 9600,
    
    # Connection timeout in seconds
    'timeout': 2.0,
}

# HDR Automation Configuration
AUTOMATION_CONFIG = {
    # How often to poll Lumagen for HDR status (seconds)
    'poll_interval': 2.0,
    
    # Picture mode to use for SDR content
    'sdr_mode': 'USER1',  # or use PictureMode.USER1
    
    # Picture mode to use for HDR content
    'hdr_mode': 'USER2',  # or use PictureMode.USER2
}

# Default picture modes for different content types
CONTENT_MODES = {
    'movies_sdr': 'CINEMA',
    'movies_hdr': 'HDR',
    'gaming': 'USER1',
    'sports': 'NATURAL',
    'animation': 'FILM',
    'user_calibrated_sdr': 'USER1',
    'user_calibrated_hdr': 'USER2',
}

# Input assignments
INPUTS = {
    'apple_tv': 'HDMI-1',
    'roku': 'HDMI-2',
}

# Example usage:
if __name__ == '__main__':
    print("Configuration:")
    print(f"\nJVC Projector:")
    print(f"  Host: {JVC_CONFIG['host']}:{JVC_CONFIG['port']}")
    
    print(f"\nLumagen Radiance:")
    print(f"  Serial Port: {LUMAGEN_CONFIG['port']}")
    print(f"  Baud Rate: {LUMAGEN_CONFIG['baudrate']}")
    
    print(f"\nAutomation:")
    print(f"  Poll Interval: {AUTOMATION_CONFIG['poll_interval']}s")
    print(f"  SDR Mode: {AUTOMATION_CONFIG['sdr_mode']}")
    print(f"  HDR Mode: {AUTOMATION_CONFIG['hdr_mode']}")
    
    print(f"\nContent Modes:")
    for content, mode in CONTENT_MODES.items():
        print(f"  {content}: {mode}")
    
    print(f"\nInputs:")
    for device, input_name in INPUTS.items():
        print(f"  {device}: {input_name}")
