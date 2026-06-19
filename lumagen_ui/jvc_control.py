"""
JVC D-ILA Projector Control via TCP/IP (port 20554)
Implements JVC External Command spec v1.2 — connect-per-command pattern.
"""
import socket
import time


class JVCControl:
    """JVC D-ILA projector TCP/IP controller."""

    _OP   = b'!'
    _REF  = b'?'
    _RESP = b'@'
    _ACK  = b'\x06'
    _UNIT = b'\x89\x01'
    _END  = b'\x0A'
    _AUTH = b'PJREQ_' + b'\x00' * 16

    PICTURE_MODES = {
        'film':            (b'00', 'Film'),
        'cinema':          (b'01', 'Cinema'),
        'natural':         (b'03', 'Natural'),
        'hdr':             (b'04', 'HDR10'),
        'thx':             (b'06', 'THX'),
        'frame_adapt_hdr': (b'0B', 'Frame Adapt HDR'),
        'hlg':             (b'14', 'HLG'),
        'user1':           (b'0C', 'User 1'),
        'user2':           (b'0D', 'User 2'),
        'user3':           (b'0E', 'User 3'),
        'user4':           (b'0F', 'User 4'),
        'user5':           (b'10', 'User 5'),
        'user6':           (b'11', 'User 6'),
    }
    _MODE_BY_VALUE = {v[0]: k for k, v in PICTURE_MODES.items()}

    # Color Profile values
    COLOR_PROFILES = {
        '00': 'Off',    '01': 'Film1',   '02': 'Film2',  '03': 'BT.709',
        '04': 'Cinema', '06': 'Anime',   '08': 'Video',  '0A': 'HDR',
        '0B': 'BT.2020','0E': 'Custom1', '0F': 'Custom2','10': 'Custom3',
        '11': 'Custom4','12': 'Custom5', '22': 'Custom6','21': 'DCI',
    }

    # Color Temperature values
    COLOR_TEMPS = {
        '00': '5500K', '02': '6500K', '04': '7500K', '08': '9300K',
        '09': 'Hi Bright', '0A': 'Custom1', '0B': 'Custom2', '0C': 'HDR10', '14': 'HLG',
    }

    # Gamma Table values
    GAMMA_TABLES = {
        '00': '2.2',    '01': 'Cinema1', '02': 'Cinema2', '04': 'Custom1',
        '05': 'Custom2','06': 'Custom3', '07': 'HDR(HLG)', '08': '2.4',
        '09': '2.6',    '0A': 'Film1',  '0B': 'Film2',   '0C': 'HDR(PQ)',
        '10': 'THX',
    }

    # Image adjustments: (cmd4, label, min, max)
    IMAGE_ADJUSTMENTS = {
        'contrast':   (b'PMCN', 'Contrast',   -50, 50),
        'brightness': (b'PMBR', 'Brightness', -50, 50),
        'color':      (b'PMCO', 'Color',      -50, 50),
        'tint':       (b'PMTI', 'Tint',       -50, 50),
        'nr':         (b'PMRN', 'NR',           0, 60),
        'enhance':    (b'PMEN', 'Enhance',      0, 20),
        'smooth':     (b'PMST', 'Smooth',       0, 10),
    }

    def __init__(self, host: str, port: int = 20554, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout

    # ── Low-level transport ────────────────────────────────────────────────

    def _connect(self) -> socket.socket:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        s.connect((self.host, self.port))
        greeting = s.recv(1024)
        if greeting.startswith(b'PJ_NG'):
            s.close()
            raise ConnectionError("Projector busy (PJ_NG) — another client is connected")
        if not greeting.startswith(b'PJ_OK'):
            s.close()
            raise ConnectionError(f"Unexpected greeting: {greeting!r}")
        s.sendall(self._AUTH)
        time.sleep(0.3)
        auth = s.recv(1024)
        if auth != b'PJACK':
            s.close()
            raise ConnectionError(f"Authentication failed: {auth!r}")
        return s

    def _operation(self, cmd: bytes, data: bytes = b'') -> bool:
        s = self._connect()
        try:
            s.sendall(self._OP + self._UNIT + cmd + data + self._END)
            resp = s.recv(1024)
            expected = self._ACK + self._UNIT + cmd[:2] + self._END
            if resp != expected:
                raise RuntimeError(f"Unexpected ACK: {resp!r}")
            return True
        finally:
            s.close()

    def _reference(self, cmd: bytes) -> bytes:
        s = self._connect()
        try:
            return self._reference_on(s, cmd)
        finally:
            s.close()

    def _reference_on(self, s: socket.socket, cmd: bytes) -> bytes:
        """Send a reference query on an already-authenticated socket."""
        s.sendall(self._REF + self._UNIT + cmd + self._END)
        resp = s.recv(1024)
        ack = self._ACK + self._UNIT + cmd[:2] + self._END
        ack_len = len(ack)
        data = resp[ack_len:] if (resp.startswith(ack) and len(resp) > ack_len) else s.recv(1024)
        hdr = self._RESP + self._UNIT + cmd[:2]
        if data.startswith(hdr) and data.endswith(self._END):
            return data[len(hdr):-1]
        return data

    # ── Numeric encoding helpers ───────────────────────────────────────────

    @staticmethod
    def _num_encode(val: int) -> bytes:
        return f'{val & 0xFFFF:04X}'.encode()

    @staticmethod
    def _num_decode(raw: bytes) -> int:
        try:
            n = int(raw, 16)
            return n if n < 0x8000 else n - 0x10000
        except (ValueError, TypeError):
            return 0

    # ── Power ──────────────────────────────────────────────────────────────

    def power_on(self) -> bool:
        return self._operation(b'PW', b'1')

    def power_off(self) -> bool:
        return self._operation(b'PW', b'0')

    def get_power_status(self) -> str:
        r = self._reference(b'PW')
        return {b'0': 'Standby', b'1': 'On', b'2': 'Cooling', b'3': 'Warming', b'4': 'Emergency'}.get(r, 'Unknown')

    # ── Input ──────────────────────────────────────────────────────────────

    def select_hdmi1(self) -> bool:
        return self._operation(b'IP', b'6')

    def select_hdmi2(self) -> bool:
        return self._operation(b'IP', b'7')

    def get_current_input(self) -> str:
        r = self._reference(b'IP')
        return {b'6': 'HDMI 1', b'7': 'HDMI 2'}.get(r, 'Unknown')

    # ── Picture Mode ───────────────────────────────────────────────────────

    def set_picture_mode(self, mode_key: str) -> bool:
        entry = self.PICTURE_MODES.get(mode_key)
        if not entry:
            raise ValueError(f"Unknown picture mode: {mode_key}")
        return self._operation(b'PMPM', entry[0])

    def get_picture_mode(self) -> str:
        r = self._reference(b'PMPM')
        key = self._MODE_BY_VALUE.get(r[:2] if r else b'')
        return self.PICTURE_MODES[key][1] if key else 'Unknown'

    # ── Color Profile ──────────────────────────────────────────────────────

    def set_color_profile(self, val: str) -> bool:
        return self._operation(b'PMPR', val.encode())

    def get_color_profile(self) -> str:
        r = self._reference(b'PMPR')
        raw = r.decode(errors='replace').upper() if r else ''
        return self.COLOR_PROFILES.get(raw, raw or 'Unknown')

    # ── Color Temperature ──────────────────────────────────────────────────

    def set_color_temp(self, val: str) -> bool:
        return self._operation(b'PMCL', val.encode())

    def get_color_temp(self) -> str:
        r = self._reference(b'PMCL')
        raw = r.decode(errors='replace').upper() if r else ''
        return self.COLOR_TEMPS.get(raw, raw or 'Unknown')

    # ── Gamma Table ────────────────────────────────────────────────────────

    def set_gamma_table(self, val: str) -> bool:
        return self._operation(b'PMGT', val.encode())

    def get_gamma_table(self) -> str:
        r = self._reference(b'PMGT')
        raw = r.decode(errors='replace').upper() if r else ''
        return self.GAMMA_TABLES.get(raw, raw or 'Unknown')

    # ── Intelligent Lens Aperture ──────────────────────────────────────────

    def set_lens_aperture(self, val: str) -> bool:
        return self._operation(b'PMDI', val.encode())

    def get_lens_aperture(self) -> str:
        r = self._reference(b'PMDI')
        return {b'0': 'Off', b'1': 'Auto1', b'2': 'Auto2'}.get(r, 'Unknown')

    # ── Low Latency ────────────────────────────────────────────────────────

    def set_low_latency(self, on: bool) -> bool:
        return self._operation(b'PMLL', b'1' if on else b'0')

    def get_low_latency(self) -> bool:
        return self._reference(b'PMLL') == b'1'

    # ── Clear Motion Drive ─────────────────────────────────────────────────

    def set_clear_motion_drive(self, val: str) -> bool:
        return self._operation(b'PMCM', val.encode())

    def get_clear_motion_drive(self) -> str:
        r = self._reference(b'PMCM')
        return {b'0': 'Off', b'3': 'Low', b'4': 'High', b'5': 'Inv. Telecine'}.get(r, 'Unknown')

    # ── Motion Enhance ─────────────────────────────────────────────────────

    def set_motion_enhance(self, val: str) -> bool:
        return self._operation(b'PMME', val.encode())

    def get_motion_enhance(self) -> str:
        r = self._reference(b'PMME')
        return {b'0': 'Off', b'1': 'Low', b'2': 'High'}.get(r, 'Unknown')

    # ── Lamp Power ────────────────────────────────────────────────────────

    def set_lamp_power(self, val: str) -> bool:
        return self._operation(b'PMLP', val.encode())

    def get_lamp_power(self) -> str:
        r = self._reference(b'PMLP')
        return {b'0': 'Normal', b'1': 'High'}.get(r, 'Unknown')

    # ── 8K e-shift ────────────────────────────────────────────────────────

    def set_8k_eshift(self, on: bool) -> bool:
        return self._operation(b'PMUS', b'1' if on else b'0')

    def get_8k_eshift(self) -> str:
        r = self._reference(b'PMUS')
        return {b'0': 'Off', b'1': 'On'}.get(r, 'Unknown')

    # ── Auto Tone Mapping ──────────────────────────────────────────────────

    def set_auto_tone_mapping(self, on: bool) -> bool:
        return self._operation(b'PMTM', b'1' if on else b'0')

    def get_auto_tone_mapping(self) -> str:
        r = self._reference(b'PMTM')
        return {b'0': 'Off', b'1': 'On'}.get(r, 'Unknown')

    # ── Numeric image adjustments ──────────────────────────────────────────

    def adjust_image(self, param: str, val: int) -> bool:
        entry = self.IMAGE_ADJUSTMENTS.get(param)
        if not entry:
            raise ValueError(f"Unknown image param: {param}")
        cmd4, _, lo, hi = entry
        val = max(lo, min(hi, val))
        return self._operation(cmd4, self._num_encode(val))

    def get_image_value(self, param: str) -> int:
        entry = self.IMAGE_ADJUSTMENTS.get(param)
        if not entry:
            raise ValueError(f"Unknown image param: {param}")
        cmd4 = entry[0]
        return self._num_decode(self._reference(cmd4))

    def get_all_image_values(self) -> dict:
        """Fetch all numeric image adjustments in one TCP connection."""
        s = self._connect()
        result = {}
        try:
            for param, (cmd4, label, lo, hi) in self.IMAGE_ADJUSTMENTS.items():
                try:
                    raw = self._reference_on(s, cmd4)
                    result[param] = self._num_decode(raw)
                except Exception:
                    result[param] = None
        finally:
            s.close()
        return result

    # ── Lens control (continuous start/stop) ───────────────────────────────

    def lens_move(self, action: str, start: bool) -> bool:
        cmd_map = {
            'focus-near': b'INFN', 'focus-far': b'INFF',
            'zoom-tele':  b'INZT', 'zoom-wide': b'INZW',
            'shift-left': b'INSL', 'shift-right': b'INSR',
            'shift-up':   b'INSU', 'shift-down':  b'INSD',
        }
        cmd = cmd_map.get(action)
        if not cmd:
            raise ValueError(f"Unknown lens action: {action}")
        return self._operation(cmd, b'1' if start else b'0')

    def set_lens_lock(self, on: bool) -> bool:
        return self._operation(b'INLL', b'1' if on else b'0')

    # ── Input Signal ───────────────────────────────────────────────────────

    def set_hdmi_level(self, val: str) -> bool:
        return self._operation(b'ISIL', val.encode())

    def get_hdmi_level(self) -> str:
        r = self._reference(b'ISIL')
        return {b'0': 'Standard (16-235)', b'1': 'Enhanced (0-255)',
                b'2': 'Super White (16-255)', b'3': 'Auto'}.get(r, 'Unknown')

    def set_hdmi_colorspace(self, val: str) -> bool:
        return self._operation(b'ISHS', val.encode())

    def get_hdmi_colorspace(self) -> str:
        r = self._reference(b'ISHS')
        return {b'0': 'Auto', b'1': 'YCbCr 4:4:4', b'2': 'YCbCr 4:2:2', b'3': 'RGB'}.get(r, 'Unknown')

    def set_aspect(self, val: str) -> bool:
        return self._operation(b'ISAS', val.encode())

    def get_aspect(self) -> str:
        r = self._reference(b'ISAS')
        return {b'2': 'Zoom', b'3': 'Auto', b'4': 'Native'}.get(r, 'Unknown')

    def set_anamorphic(self, val: str) -> bool:
        return self._operation(b'INVS', val.encode())

    def get_anamorphic(self) -> str:
        r = self._reference(b'INVS')
        return {b'0': 'Off', b'1': 'A', b'2': 'B', b'3': 'C'}.get(r, 'Unknown')

    # ── Installation ───────────────────────────────────────────────────────

    def set_install_style(self, val: str) -> bool:
        return self._operation(b'INIS', val.encode())

    def get_install_style(self) -> str:
        r = self._reference(b'INIS')
        return {b'0': 'Front', b'1': 'Ceiling Mount (F)',
                b'2': 'Rear',  b'3': 'Ceiling Mount (R)'}.get(r, 'Unknown')

    def set_high_altitude(self, on: bool) -> bool:
        return self._operation(b'INHA', b'1' if on else b'0')

    def get_high_altitude(self) -> str:
        r = self._reference(b'INHA')
        return {b'0': 'Off', b'1': 'On'}.get(r, 'Unknown')

    # ── Display Setup ──────────────────────────────────────────────────────

    def set_back_color(self, val: str) -> bool:
        return self._operation(b'DSBC', val.encode())

    def get_back_color(self) -> str:
        r = self._reference(b'DSBC')
        return {b'0': 'Blue', b'1': 'Black'}.get(r, 'Unknown')

    # ── Function ───────────────────────────────────────────────────────────

    def set_eco_mode(self, on: bool) -> bool:
        return self._operation(b'FUEM', b'1' if on else b'0')

    def get_eco_mode(self) -> str:
        r = self._reference(b'FUEM')
        return {b'0': 'Off', b'1': 'On'}.get(r, 'Unknown')

    def set_off_timer(self, val: str) -> bool:
        return self._operation(b'FUOT', val.encode())

    def get_off_timer(self) -> str:
        r = self._reference(b'FUOT')
        return {b'0': 'Off', b'1': '1 Hour', b'2': '2 Hours',
                b'3': '3 Hours', b'4': '4 Hours'}.get(r, 'Unknown')

    # ── Information (reference only) ───────────────────────────────────────

    def get_source_status(self) -> str:
        r = self._reference(b'SC')
        return {b'0': 'No Signal', b'1': 'Signal OK'}.get(r, 'Unknown')

    def get_model(self) -> str:
        r = self._reference(b'MD')
        return r.decode(errors='replace').strip() if r else 'Unknown'

    def get_lamp_time(self) -> str:
        r = self._reference(b'IFLT')
        if r:
            try:
                return str(int(r, 16))
            except ValueError:
                return r.decode(errors='replace')
        return 'Unknown'

    def get_software_version(self) -> str:
        r = self._reference(b'IFSV')
        return r.decode(errors='replace').strip() if r else 'Unknown'

    def get_hdr_info(self) -> str:
        r = self._reference(b'IFHR')
        return {b'0': 'SDR', b'1': 'HDR', b'2': 'SMPTE ST 2084', b'F': 'None'}.get(r, 'Unknown')

    def get_h_resolution(self) -> str:
        r = self._reference(b'IFRH')
        if r:
            try:
                return str(int(r, 16) // 100)
            except ValueError:
                pass
        return 'Unknown'

    def get_v_resolution(self) -> str:
        r = self._reference(b'IFRV')
        if r:
            try:
                return str(int(r, 16) // 100)
            except ValueError:
                pass
        return 'Unknown'

    # ── Status bundles ─────────────────────────────────────────────────────

    def get_status(self) -> dict:
        s = self._connect()
        try:
            r_pw = self._reference_on(s, b'PW')
            r_ip = self._reference_on(s, b'IP')
            r_pm = self._reference_on(s, b'PMPM')
        finally:
            s.close()

        key = self._MODE_BY_VALUE.get(r_pm[:2] if r_pm else b'')
        return {
            'power':        {b'0': 'Standby', b'1': 'On', b'2': 'Cooling', b'3': 'Warming'}.get(r_pw, 'Unknown'),
            'input':        {b'6': 'HDMI 1', b'7': 'HDMI 2'}.get(r_ip, 'Unknown'),
            'picture_mode': self.PICTURE_MODES[key][1] if key else 'Unknown',
        }

    def get_full_status(self) -> dict:
        """Query comprehensive status in two connections."""
        result = {}

        # Connection 1: core state
        try:
            s = self._connect()
            try:
                pw = self._reference_on(s, b'PW')
                ip = self._reference_on(s, b'IP')
                pm = self._reference_on(s, b'PMPM')
                src = self._reference_on(s, b'SC')
            finally:
                s.close()

            key = self._MODE_BY_VALUE.get(pm[:2] if pm else b'')
            result['power'] = {b'0': 'Standby', b'1': 'On', b'2': 'Cooling',
                               b'3': 'Warming', b'4': 'Emergency'}.get(pw, 'Unknown')
            result['input'] = {b'6': 'HDMI 1', b'7': 'HDMI 2'}.get(ip, 'Unknown')
            result['picture_mode'] = self.PICTURE_MODES[key][1] if key else 'Unknown'
            result['source'] = {b'0': 'No Signal', b'1': 'Signal OK'}.get(src, 'Unknown')
        except Exception as e:
            result['power'] = 'Unavailable'
            result['error'] = str(e)
            return result

        # Connection 2: info fields (may fail in standby)
        try:
            s = self._connect()
            try:
                md  = self._reference_on(s, b'MD')
                lt  = self._reference_on(s, b'IFLT')
                sv  = self._reference_on(s, b'IFSV')
                hdr = self._reference_on(s, b'IFHR')
                il  = self._reference_on(s, b'ISIL')
                la  = self._reference_on(s, b'PMDI')
                lp  = self._reference_on(s, b'PMLP')
                ll  = self._reference_on(s, b'PMLL')
            finally:
                s.close()

            result['model'] = md.decode(errors='replace').strip() if md else 'Unknown'
            result['lamp_time'] = str(int(lt, 16)) + 'h' if lt else 'Unknown'
            result['software_version'] = sv.decode(errors='replace').strip() if sv else 'Unknown'
            result['hdr_type'] = {b'0': 'SDR', b'1': 'HDR',
                                  b'2': 'SMPTE ST 2084', b'F': 'None'}.get(hdr, 'Unknown')
            result['hdmi_level'] = {b'0': 'Standard (16-235)', b'1': 'Enhanced (0-255)',
                                    b'2': 'Super White (16-255)', b'3': 'Auto'}.get(il, 'Unknown')
            result['lens_aperture'] = {b'0': 'Off', b'1': 'Auto1', b'2': 'Auto2'}.get(la, 'Unknown')
            result['lamp_power'] = {b'0': 'Normal', b'1': 'High'}.get(lp, 'Unknown')
            result['low_latency'] = 'On' if ll == b'1' else 'Off'
        except Exception:
            pass  # info fields unavailable (standby or other)

        return result
