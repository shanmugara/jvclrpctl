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
    # PJREQ with empty password (16 null bytes)
    auth_command = b'PJREQ_' + b'\x00' * 16
    print(f"\n{description}")
    print(f"   Sending: {command_bytes.hex().upper()}")
    pj_ok = False
    try:
        sock.connect((PROJECTOR_IP, PROJECTOR_PORT))
        greeting = sock.recv(1024)
        print(f"Greeting from projector: {greeting}")
        if greeting == b'PJ_OK':
            pj_ok = True
    except Exception as e:
        print(f"Connection error: {e}")

    if not pj_ok:
        print("Projector did not respond with PJ_OK. Please check connection and settings.")
        return b''
    
    try:
        sock.sendall(auth_command)
        time.sleep(0.3)  # Longer wait for NX7
        auth_response = sock.recv(1024)
        print(f"Authentication Response: {auth_response} ({auth_response.hex().upper()})")
    except Exception as e:
        print(f"Authentication error: {e}")
        return b''
    
    if auth_response != b'PJACK':
        print("Authentication failed. Projector did not accept empty password.")
        return b''
    
    try:
        sock.sendall(command_bytes)
        time.sleep(0.3)  # Longer wait for NX7
        response = sock.recv(1024)
        return response
    except socket.timeout:
        print("   Response: TIMEOUT")
        return b''
    except Exception as e:
        print(f"   Error: {e}")
        return b''

def ok_test():
    """This is a placeholder test function to avoid execution errors when imported"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10.0)
    try:
        sock.connect((PROJECTOR_IP, PROJECTOR_PORT))
        greeting = sock.recv(1024)
        print(f"Greeting from projector: {greeting}")
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        sock.close()

def null_test():
    """This is a placeholder test function to avoid execution errors when imported"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10.0)
    
    response = send_and_receive(sock, b'\x21\x89\x01\x00\x00\x0A', "NULL Command Test (empty bytes)")
    print(f"NULL Command Response: {response} ({response.hex().upper()})")
    sock.close()

def model_query_test():
    """Test model query command on NX7/RS2000"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10.0)
    
    response = send_and_receive(sock, b'?\x89\x01MD\x0A', "Model Info Query (?MD)")
    print(f"Model Query Response: {response} ({response.hex().upper()})")
    
    sock.close()

def get_power_status_test():
    """Test power status query on NX7/RS2000"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10.0)
    
    response = send_and_receive(sock, b'?\x89\x01PW\x0A', "Power Status Query (?PW)")
    print(f"Power Status Response: {response} ({response.hex().upper()})")
    
    sock.close()