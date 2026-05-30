"""
JVC NX7/RS2000 Specific Test
Special tests for NX7/RS2000 models
"""

import socket
import time

PROJECTOR_IP = "192.168.100.240"
PROJECTOR_PORT = 20554

def send_and_receive(sock, command_bytes, description):
    """Send command and print detailed response"""
    print(f"\n{description}")
    print(f"   Sending: {command_bytes.hex().upper()}")
    try:
        sock.sendall(command_bytes)
        time.sleep(0.3)  # Longer wait for NX7
        response = sock.recv(1024)
        print(f"   Response: {response}")
        print(f"   Hex: {response.hex().upper()}")
        return response
    except socket.timeout:
        print("   Response: TIMEOUT")
        return b''
    except Exception as e:
        print(f"   Error: {e}")
        return b''


def main():
    print("=" * 70)
    print("JVC NX7/RS2000 Network Control Test")
    print("=" * 70)
    print("\nIMPORTANT: Before running this test, please verify:")
    print("  1. Menu → Installation → Control → Network Control = ON")
    print("  2. Menu → Installation → Control → Control Lock = OFF")
    print("  3. No other device (app/remote) is controlling the projector")
    print("\nPress Ctrl+C to cancel, or wait 5 seconds to continue...")
    
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\nTest cancelled")
        return
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10.0)  # Longer timeout for NX7
    
    try:
        print(f"\n\nConnecting to {PROJECTOR_IP}:{PROJECTOR_PORT}...")
        sock.connect((PROJECTOR_IP, PROJECTOR_PORT))
        print("✓ TCP connection established")
        
        # Read greeting
        greeting = sock.recv(1024)
        print(f"\nGreeting from projector: {greeting}")
        print(f"Greeting hex: {greeting.hex().upper()}")
        
        if greeting != b'PJ_OK':
            print("\n⚠ WARNING: Unexpected greeting. Expected 'PJ_OK'")
            print("This might indicate the projector is not ready for commands.")
        
        print("\n" + "=" * 70)
        print("Testing NX7/RS2000 Commands")
        print("=" * 70)
        
        # Test 1: Null command (ACK test)
        send_and_receive(sock, b'\x00', "1. Null byte (ACK test)")
        
        # Test 2: Model query (this usually works even when locked)
        send_and_receive(sock, b'?\x89\x01MD\x0A', "2. Model Info Query (?MD)")

        # Test 2: Model query (this usually works even when locked)
        send_and_receive(sock, b'\x3F\x89\x01\x4D\x44\x0A', "2a. Model Info Query (?MD)")
        
        # Test 3: Try with different line ending
        send_and_receive(sock, b'?\x89\x01MD\x0D', "3. Model Query with CR instead of LF")
        
        # Test 4: Try with both CR+LF
        send_and_receive(sock, b'?\x89\x01MD\x0D\x0A', "4. Model Query with CR+LF")
        
        # Test 5: Remote code (some models need this)
        send_and_receive(sock, b'!\x89\x01RC73\x0A', "5. Remote Code (RC73 = Menu button)")
        
        # Test 6: Information query
        send_and_receive(sock, b'?\x89\x01IF\x0A', "6. Information Query (?IF)")
        
        # Test 7: Try power query with longer wait
        print("\n7. Power Query with extended wait")
        print("   Sending: 3F890150570A")
        sock.sendall(b'?\x89\x01PW\x0A')
        time.sleep(1.0)  # Wait longer
        response = sock.recv(1024)
        print(f"   Response: {response}")
        print(f"   Hex: {response.hex().upper()}")
        
        # Test 8: Check if we can send ACK
        send_and_receive(sock, b'\x06', "8. Send ACK byte")
        
        # Test 9: Unit ID 00 (for some models)
        send_and_receive(sock, b'?\x00\x00PW\x0A', "9. Power Query with Unit ID 00 00")
        
        # Test 10: Picture mode set (operation command)
        send_and_receive(sock, b'!\x89\x01PMPM\x00\x01\x0A', "10. Set Picture Mode to CINEMA")
        
    except Exception as e:
        print(f"\nConnection error: {e}")
    finally:
        sock.close()
        
        print("\n" + "=" * 70)
        print("ANALYSIS")
        print("=" * 70)
        print("\nIf ALL responses are 'PJNAK':")
        print("  → Network Control is likely DISABLED in projector settings")
        print("  → Check: Menu → Installation → Control → Network Control")
        print("\nIf you see 'PJACK' or data responses:")
        print("  → Network Control is working!")
        print("  → We need to adjust the command format in the library")
        print("\nIf connection fails completely:")
        print("  → Check IP address is correct")
        print("  → Check projector and Mac are on same network")
        print("\nNX7/RS2000 Control Settings Path:")
        print("  Menu → Installation (scroll down) → Control → Network Control → ON")
        print("=" * 70)


if __name__ == "__main__":
    main()
