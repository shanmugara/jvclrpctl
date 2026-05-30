"""
JVC Projector Diagnostic Tool
Tests which commands are supported by your specific JVC model
"""

import sys
import os

# Add parent directory to path so we can import jvclrpctl
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from jvclrpctl.jvcctl import JVCProjector, PictureMode, PictureModeController, JVCCommands

# Configuration
PROJECTOR_IP = "192.168.100.240"
PROJECTOR_PORT = 20554


def test_command(name, func, *args):
    """Test a command and report if it works"""
    try:
        result = func(*args)
        print(f"   ✓ {name}: SUPPORTED (result: {result})")
        return True
    except Exception as e:
        print(f"   ✗ {name}: NOT SUPPORTED ({str(e)})")
        return False


def main():
    """Run diagnostic tests"""
    
    print("=" * 70)
    print("JVC Projector Diagnostic Tool")
    print("=" * 70)
    print(f"\nProjector: {PROJECTOR_IP}:{PROJECTOR_PORT}")
    print("\nTesting basic query commands...\n")
    
    results = {}
    
    with JVCProjector(PROJECTOR_IP, PROJECTOR_PORT) as projector:
        commands = JVCCommands(projector)
        controller = PictureModeController(projector)
        
        results['power_status'] = test_command(
            "Power Status", 
            commands.get_power_status
        )
        
        results['current_input'] = test_command(
            "Current Input", 
            commands.get_current_input
        )
        
        results['picture_mode'] = test_command(
            "Picture Mode", 
            controller.get_current_mode
        )
        
    print("\n" + "=" * 70)
    supported = sum(1 for v in results.values() if v)
    print(f"Result: {supported}/{len(results)} commands working")
    print("=" * 70)


if __name__ == "__main__":
    main()
