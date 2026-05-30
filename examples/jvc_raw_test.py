"""
JVC Raw Command Tester
Tests different command formats to find what works with your projector
"""

import socket
import time

PROJECTOR_IP = "192.168.100.240"
PROJECTOR_PORT = 20554

def send_raw_command(sock, command_bytes):
    """Send raw bytes and get response"""
    try:
        sock.sendall(command_bytes)
        time.sleep(0.2)
        response = sock.recv(1024)
        return response
    except Exception as e:
        return f"Error: {e}".encode()


def main():
    print("=" * 70)
    print("JVC Raw Command Tester")
    print("=" * 70)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5.0)
    
    try:
        print(f"\nConnecting to {PROJECTOR_IP}:{PROJECTOR_PORT}...")
        sock.connect((PROJECTOR_IP, PROJECTOR_PORT))
        
        # Read greeting
        greeting = sock.recv(1024)
        print(f"Greeting: {greeting}")
        
        print("\n" + "=" * 70)
        print("Testing different command formats...")
        print("=" * 70)
        
        # Test 1: Original format with Unit ID
        print("\n1. Standard format: Header + UnitID + Command + Data + End")
        print("   Command: Power Status Query")
        cmd = b'?\x89\x01PW\x0A'
        print(f"   Bytes: {cmd.hex()}")
        response = send_raw_command(sock, cmd)
        print(f"   Response: {response} ({response.hex()})")
        
        # Test 2: Without Unit ID
        print("\n2. Without Unit ID: Header + Command + Data + End")
        print("   Command: Power Status Query")
        cmd = b'?PW\x0A'
        print(f"   Bytes: {cmd.hex()}")
        response = send_raw_command(sock, cmd)
        print(f"   Response: {response} ({response.hex()})")
        
        # Test 3: Different Unit ID
        print("\n3. Different Unit ID: Header + 0x0001 + Command + Data + End")
        print("   Command: Power Status Query")
        cmd = b'?\x00\x01PW\x0A'
        print(f"   Bytes: {cmd.hex()}")
        response = send_raw_command(sock, cmd)
        print(f"   Response: {response} ({response.hex()})")
        
        # Test 4: Try operation command (power on)
        print("\n4. Operation command: Power On")
        cmd = b'!\x89\x01PW1\x0A'
        print(f"   Bytes: {cmd.hex()}")
        response = send_raw_command(sock, cmd)
        print(f"   Response: {response} ({response.hex()})")
        
        # Test 5: Picture mode query
        print("\n5. Picture Mode Query")
        cmd = b'?\x89\x01PMPM\x0A'
        print(f"   Bytes: {cmd.hex()}")
        response = send_raw_command(sock, cmd)
        print(f"   Response: {response} ({response.hex()})")
        
        # Test 6: Input query
        print("\n6. Input Query")
        cmd = b'?\x89\x01IP\x0A'
        print(f"   Bytes: {cmd.hex()}")
        response = send_raw_command(sock, cmd)
        print(f"   Response: {response} ({response.hex()})")
        
        # Test 7: Model info query
        print("\n7. Model Info Query")
        cmd = b'?\x89\x01MD\x0A'
        print(f"   Bytes: {cmd.hex()}")
        response = send_raw_command(sock, cmd)
        print(f"   Response: {response} ({response.hex()})")
        
        # Test 8: Software version query
        print("\n8. Software Version Query")
        cmd = b'?\x89\x01SV\x0A'
        print(f"   Bytes: {cmd.hex()}")
        response = send_raw_command(sock, cmd)
        print(f"   Response: {response} ({response.hex()})")
        
        # Test 9: Try with just header and command
        print("\n9. Minimal format: Header + Command")
        cmd = b'?PW'
        print(f"   Bytes: {cmd.hex()}")
        response = send_raw_command(sock, cmd)
        print(f"   Response: {response} ({response.hex()})")
        
        # Test 10: ASCII only (no control chars)
        print("\n10. ASCII only: ?PWQRY")
        cmd = b'?PWQRY'
        print(f"   Bytes: {cmd.hex()}")
        response = send_raw_command(sock, cmd)
        print(f"   Response: {response} ({response.hex()})")
        
    finally:
        sock.close()
        print("\n" + "=" * 70)
        print("Test completed")
        print("=" * 70)
        print("\nLook for any response that is NOT 'PJNAK'.")
        print("That will tell us the correct command format for your projector.")


if __name__ == "__main__":
    main()
