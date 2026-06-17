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

    # ── Navigation ─────────────────────────────────────────────────────────
    # Spec: M=Menu, X=Exit, k=OK/Accept, <=Left, >=Right, ^=Up, v=Down, P=Prev
    def menu(self) -> str:
        return self.send_command("M")

    def exit_key(self) -> str:
        return self.send_command("X")

    def ok(self) -> str:
        return self.send_command("k")

    def arrow_up(self) -> str:
        return self.send_command("^")

    def arrow_down(self) -> str:
        return self.send_command("v")

    def arrow_left(self) -> str:
        return self.send_command("<")

    def arrow_right(self) -> str:
        return self.send_command(">")

    def prev_input(self) -> str:
        return self.send_command("P")

    def osd_on(self) -> str:
        return self.send_command("g")

    def osd_off(self) -> str:
        return self.send_command("s")

    # ── Extended Aspect Ratios (Radiance Pro) ──────────────────────────────
    # Spec: "1.90 A" / "2.00 C" / "2.20 E" / "2.40 G"
    def set_aspect_1_90(self) -> str:
        return self.send_command("A")

    def set_aspect_2_00(self) -> str:
        return self.send_command("C")

    def set_aspect_2_20(self) -> str:
        return self.send_command("E")

    def set_aspect_2_40(self) -> str:
        return self.send_command("G")

    # ── No-Zoom Aspect Variants ────────────────────────────────────────────
    # Spec: "4:3NZ [" / "LBOXNZ ]" / "16:9NZ *" / "1.85NZ /" / "2.35NZ K"
    def set_aspect_4_3_nz(self) -> str:
        return self.send_command("[")

    def set_aspect_lbox_nz(self) -> str:
        return self.send_command("]")

    def set_aspect_16_9_nz(self) -> str:
        return self.send_command("*")

    def set_aspect_1_85_nz(self) -> str:
        return self.send_command("/")

    def set_aspect_2_35_nz(self) -> str:
        return self.send_command("K")

    # ── Auto Aspect ────────────────────────────────────────────────────────
    # Spec: "~ Auto Aspect Enable" / "V Auto Aspect Disable" / "ZY550<CR> Reset"
    def auto_aspect_enable(self) -> str:
        return self.send_command("~")

    def auto_aspect_disable(self) -> str:
        return self.send_command("V")

    def reset_auto_aspect(self) -> str:
        return self.send_command("ZY550\r")

    # ── Game Mode ──────────────────────────────────────────────────────────
    # Spec: "ZQI53 Gamemode query" / "ZY551X<CR> Set Game-mode (0=off, 1=on)"
    def get_game_mode(self) -> str:
        return self.send_command("ZQI53")

    def set_game_mode(self, on: bool) -> str:
        return self.send_command(f"ZY551{'1' if on else '0'}\r")

    # ── HDMI Hotplug ───────────────────────────────────────────────────────
    # Spec: "ZY520X<CR>" X=0-7 maps to HDMI inputs 1-8, 'A' for All (Pro)
    def hdmi_hotplug(self, input_id) -> str:
        if str(input_id).lower() == 'all':
            return self.send_command("ZY520A\r")
        n = int(input_id)
        if not 1 <= n <= 8:
            raise ValueError("Input must be 1-8 or 'all'")
        return self.send_command(f"ZY520{n - 1}\r")

    # ── Sharpness ──────────────────────────────────────────────────────────
    # Spec: "ZQI30 Query sharpness" / "ZY521ELS<CR>" E=Y/N, L=0-7, S=H/N
    def get_sharpness(self) -> str:
        return self.send_command("ZQI30")

    def set_sharpness(self, enabled: bool, level: int, sensitivity: str = 'N') -> str:
        e = 'Y' if enabled else 'N'
        lv = max(0, min(7, int(level)))
        s = 'H' if sensitivity.upper() == 'H' else 'N'
        return self.send_command(f"ZY521{e}{lv}{s}\r")

    # ── Test Patterns (ZY7T) ───────────────────────────────────────────────
    # Spec: "ZY7TGSIII<CR>" G=group 'a'-'r', S=sub#, III=IRE 000-100
    def test_pattern_full(self, group: str, sub: int, ire: int = 100) -> str:
        ire_val = max(0, min(100, int(ire)))
        return self.send_command(f"ZY7T{group}{sub}{ire_val:03d}\r")

    # ── Output Format ──────────────────────────────────────────────────────
    # Spec: "ZY46F<CR>" F: 0=YCbCr422, 1=YCbCr444, 2=RGBPC, 3=RGBVID, 8=automax, 9=auto9
    # Query: "ZQO18" → !O18,N where N: 0=yc422, 1=yc444, 2=rgbvid, 3=rgbpc, 4=yc420
    def get_output_format(self) -> str:
        return self.send_command("ZQO18")

    def set_output_format(self, fmt: int) -> str:
        if fmt not in (0, 1, 2, 3, 8, 9):
            raise ValueError("Format must be 0,1,2,3,8,9")
        return self.send_command(f"ZY46{fmt}\r")

    # ── CMS / Style ────────────────────────────────────────────────────────
    # Spec: "ZY530MCDS<CR>" M=mode(K/0-7), C=CMS-SDR(K/0-7), D=CMS-HDR(K/0-7), S=style(K/0-7)
    def set_cms_style(self, mode='K', cms_sdr='K', cms_hdr='K', style='K') -> str:
        def _v(x):
            s = str(x).upper()
            return s if s == 'K' else str(int(s))
        return self.send_command(f"ZY530{_v(mode)}{_v(cms_sdr)}{_v(cms_hdr)}{_v(style)}\r")

    # ── PIP Controls ───────────────────────────────────────────────────────
    # Spec: "PIP-OFF e" / "PIP-SEL p" / "PIP-SWAP r" / "PIP-MODE m"
    def pip_off(self) -> str:
        return self.send_command("e")

    def pip_select(self) -> str:
        return self.send_command("p")

    def pip_swap(self) -> str:
        return self.send_command("r")

    def pip_mode(self) -> str:
        return self.send_command("m")

    # ── Deinterlacing ──────────────────────────────────────────────────────
    # Spec: "ZQI15 Current input deinterlacing mode" / "ZY515X<CR>" 0=auto,1=film,2=video
    def get_deinterlace_mode(self) -> str:
        return self.send_command("ZQI15")

    def set_deinterlace_mode(self, mode: int) -> str:
        if mode not in (0, 1, 2):
            raise ValueError("Mode must be 0 (auto), 1 (film), or 2 (video)")
        return self.send_command(f"ZY515{mode}\r")

    # ── Rich Status Queries ────────────────────────────────────────────────
    def get_input_video(self) -> str:
        """ZQI01 – source video: status, rate*100, hres, vres, interlaced, 3D"""
        return self.send_command("ZQI01")

    def get_input_aspect(self) -> str:
        """ZQI20 – current aspect index + NLS flag"""
        return self.send_command("ZQI20")

    def get_output_mode_name(self) -> str:
        """ZQO16 – output mode name (matches Output:Configs menu)"""
        return self.send_command("ZQO16")
