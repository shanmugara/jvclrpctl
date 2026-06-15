"""
Lumagen Radiance Pro Control via RS232
Commands per Tech Tip 11 (RS232 Command Interface, 11/20/2023).

Key protocol rules from the spec:
  - Commands that need a terminator are sent with \r; many do NOT use \r.
    Sending \r to a command that doesn't expect it brings up the Info page.
  - Query commands (ZQ*) never use a terminator.
  - Responses begin with '!' and end with <CR><LF>.
"""

import serial
import time
from typing import Optional


class LumagenControl:
    """Control interface for Lumagen Radiance Pro via RS232."""

    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.serial: Optional[serial.Serial] = None
        self.timeout = 1.0
        self._zoom_level = 0   # tracked locally; no RS232 query for zoom position

    def connect(self) -> bool:
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
            )
            time.sleep(0.1)
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to Lumagen on {self.port}: {e}")
            return False

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.serial = None

    def send_command(self, command: str) -> str:
        """
        Send a command and return any response.

        IMPORTANT: callers are responsible for including \\r when the spec
        requires it (ZY* set commands).  Query commands (ZQ*) must NOT have
        a terminator.  Single-char remote-key commands (%, $, i, a-d, n,
        l, w, j, W, N …) must NOT have a \\r either.
        """
        own_connection = (self.serial is None or not self.serial.is_open)
        if own_connection:
            if not self.connect():
                raise ConnectionError(f"Cannot connect to Lumagen on {self.port}")
        try:
            self.serial.write(command.encode('ascii'))
            self.serial.flush()
            time.sleep(0.15)
            response = b''
            while self.serial.in_waiting > 0:
                response += self.serial.read(self.serial.in_waiting)
                time.sleep(0.05)
            return response.decode('ascii', errors='ignore').strip()
        finally:
            if own_connection:
                self.disconnect()

    # ── Power ─────────────────────────────────────────────────────────────
    # Spec: "ON %  Power on"  /  "STBY $  Power to standby"
    def power_on(self) -> str:
        return self.send_command("%")

    def power_standby(self) -> str:
        return self.send_command("$")

    # Spec: ZQS02 → !S02,0 (off) or !S02,1 (on)
    def get_power_status(self) -> str:
        return self.send_command("ZQS02")

    # ── Input Selection ────────────────────────────────────────────────────
    # Spec: "INPUT i  Choose input (i.e. i2 for input 2 and i+2 for input 12)"
    #       "10+   +  Add 10 to the next digit entered for input selection"
    def select_input(self, input_num: int) -> str:
        if not 1 <= input_num <= 19:
            raise ValueError("Input must be 1-19")
        if input_num <= 9:
            cmd = f"i{input_num}"
        else:
            cmd = f"i+{input_num - 10}"
        return self.send_command(cmd)

    # Spec: ZQI00 → !I00,<logical_input>,<mem_a-d>,<physical_input>
    def get_current_input(self) -> str:
        return self.send_command("ZQI00")

    # ── Memory Selection ───────────────────────────────────────────────────
    # Spec: "MEMA a" / "MEMB b" / "MEMC c" / "MEMD d"
    def select_memory(self, memory: str) -> str:
        memory = memory.upper()
        mem_map = {'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd'}
        if memory not in mem_map:
            raise ValueError("Memory must be A, B, C, or D")
        return self.send_command(mem_map[memory])

    # ── Aspect Ratio ───────────────────────────────────────────────────────
    # Spec (all use previous zoom setting, no \r needed):
    #   "4:3 n"  /  "LBOX l"  /  "16:9 w"  /  "1.85 j"  /  "2.35 W"
    #   "NLS N  Non-Linear-Stretch. Send source aspect first, then send NLS"
    def set_aspect_4_3(self) -> str:
        return self.send_command("n")

    def set_aspect_lbox(self) -> str:
        return self.send_command("l")

    def set_aspect_16_9(self) -> str:
        return self.send_command("w")

    def set_aspect_1_85(self) -> str:
        return self.send_command("j")

    def set_aspect_2_35(self) -> str:
        return self.send_command("W")

    def set_aspect_nls(self) -> str:
        return self.send_command("N")

    # ── Zoom ───────────────────────────────────────────────────────────────
    # Spec: "ZY0M<CR>  Set zoom factor to M (0-2 for 15% steps, 0-7 for 5% steps)"
    # There is no RS232 query for current zoom position, so we track locally.
    # NOTE: if zoom is adjusted via the remote, local tracking will drift.
    def zoom_in(self) -> str:
        self._zoom_level = min(self._zoom_level + 1, 7)
        return self.send_command(f"ZY0{self._zoom_level}\r")

    def zoom_out(self) -> str:
        self._zoom_level = max(self._zoom_level - 1, 0)
        return self.send_command(f"ZY0{self._zoom_level}\r")

    # ── Output Resolution ──────────────────────────────────────────────────
    # Spec: "ZY44<ModeName><CR>  Sets output mode by name"
    # Mode names match what's shown in Output→Configs→ConfigX→Select Mode.
    # Query current mode name with ZQO16.  Common Radiance Pro names below;
    # if commands have no effect verify exact names with ZQO16 on your unit.
    def set_output_480p(self) -> str:
        return self.send_command("ZY44480p60\r")

    def set_output_720p(self) -> str:
        return self.send_command("ZY44720p60\r")

    def set_output_1080p24(self) -> str:
        return self.send_command("ZY441080p24\r")

    def set_output_1080p(self) -> str:
        return self.send_command("ZY441080p60\r")

    def set_output_4k24(self) -> str:
        return self.send_command("ZY442160p24\r")

    def set_output_4k60(self) -> str:
        return self.send_command("ZY442160p60\r")

    def set_output_auto(self) -> str:
        return self.send_command("ZY44Auto\r")

    # ── Status & Info ──────────────────────────────────────────────────────
    # Spec: ZQI24 → full status v4 (Radiance Pro only)
    #       ZQS01 → !S01,<model>,<firmware>,<model#>,<serial#>
    def get_status(self) -> str:
        return self.send_command("ZQI24")

    def get_info(self) -> str:
        return self.send_command("ZQS01")

    # ── Save Configuration ─────────────────────────────────────────────────
    # Spec: "ZY6SAVECONFIG<CR>  Save configuration to flash"
    # (Shortcut is "S" then "k" but ZY6SAVECONFIG is the clean single command)
    def save_config(self) -> str:
        return self.send_command("ZY6SAVECONFIG\r")

    # ── Test Patterns ──────────────────────────────────────────────────────
    # Spec: "EXIT X  Exit. Often acts as a cancel key" (exits test pattern)
    #       "ZY7TGSIII<CR>  Test pattern — G=group 'a'-'r', S=sub#, III=IRE"
    #       Group b, sub 0 = Contrast1 (always 100 IRE per old TcMM description)
    def test_pattern_off(self) -> str:
        return self.send_command("X")

    def test_pattern_contrast(self) -> str:
        return self.send_command("ZY7Tb0100\r")

    # ── CLR (force menu off) ───────────────────────────────────────────────
    # Spec: "CLR !  (exclamation point) Force menu off"
    # Useful to call before input selection to ensure menu is dismissed.
    def clear_menu(self) -> str:
        return self.send_command("!")
