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
        'hdr':             (b'04', 'HDR'),
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

    def __init__(self, host: str, port: int = 20554, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout

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

    # ── Power ──────────────────────────────────────────────────────────────
    def power_on(self) -> bool:
        return self._operation(b'PW', b'1')

    def power_off(self) -> bool:
        return self._operation(b'PW', b'0')

    def get_power_status(self) -> str:
        r = self._reference(b'PW')
        return {b'0': 'Standby', b'1': 'On', b'2': 'Cooling', b'3': 'Warming'}.get(r, 'Unknown')

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
        if key:
            return self.PICTURE_MODES[key][1]
        return 'Unknown'

    # ── Combined Status ────────────────────────────────────────────────────
    def get_status(self) -> dict:
        # Use a single TCP connection for all three queries — rapid reconnects
        # cause the projector to return connection refused on the 2nd/3rd attempt.
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
