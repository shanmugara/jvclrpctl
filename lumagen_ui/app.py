"""
Flask Web UI for Lumagen Radiance Pro + JVC D-ILA Projector Control
Unified service: manual controls + background HDR automation (runner.py).
"""

import sys
import os
import json
import threading
import time

# Project root on path so runner and jvclrpctl are importable
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from flask import Flask, render_template, jsonify, request
from lumagen_control import LumagenControl
from jvc_control import JVCControl
from runner.runner import JVC_LRP_Runner, POLLING_INTERVAL
from jvclrpctl import PictureMode
from jvclrpctl.lumagen.constants import LRPInputModes
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config file ───────────────────────────────────────────────────────────
# Path is configurable via CONFIG_FILE env var; defaults to config.json
# next to app.py so the service can find it without extra setup.
CONFIG_FILE = os.getenv(
    'CONFIG_FILE',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json'),
)

# ── Shared serial lock ─────────────────────────────────────────────────────
# Serialises all Lumagen serial-port access across the automation thread and
# Flask request handlers.  LumagenControl.send_command() is connect-per-call,
# so the lock just prevents two callers from opening the port simultaneously.
lumagen_lock = threading.Lock()

# ── Lumagen (manual controls) ──────────────────────────────────────────────
LUMAGEN_PORT = os.getenv('LUMAGEN_PORT', '/dev/ttyUSB0')
lumagen = LumagenControl(port=LUMAGEN_PORT)   # connect-per-command; no connect() here

# ── JVC (manual controls) ──────────────────────────────────────────────────
JVC_HOST = os.getenv('JVC_HOST', '192.168.100.240')
jvc = JVCControl(host=JVC_HOST) if JVC_HOST else None
if JVC_HOST:
    logger.info(f"JVC controller configured for {JVC_HOST}:20554")
else:
    logger.warning("JVC_HOST not set — JVC controls unavailable")

# ── HDR automation runner ──────────────────────────────────────────────────
runner = JVC_LRP_Runner(
    projector_ip=JVC_HOST,
    lumagen_port=LUMAGEN_PORT,
    lumagen_lock=lumagen_lock,      # shared lock — serialises all serial access
    lumagen_control=lumagen,        # reuse Flask's LumagenControl; only one
)                                   # serial object ever opens /dev/ttyUSB0

_automation_enabled = True


def _load_config():
    """Apply settings from CONFIG_FILE to the live runner/automation objects."""
    global jvc, lumagen, _automation_enabled
    if not os.path.exists(CONFIG_FILE):
        logger.info(f"No config file at {CONFIG_FILE} — using defaults")
        return
    try:
        with open(CONFIG_FILE) as f:
            data = json.load(f)

        jvc_host = str(data.get('jvc_host', runner.projector_ip)).strip()
        jvc_port = int(data.get('jvc_port', runner.projector_port))
        runner.projector_ip   = jvc_host
        runner.projector_port = jvc_port
        jvc = JVCControl(host=jvc_host) if jvc_host else None

        lport = str(data.get('lumagen_port', runner.lumagen_port)).strip()
        if lport:
            runner.lumagen_port     = lport
            lumagen                 = LumagenControl(port=lport)
            runner._lumagen_control = lumagen

        if 'poll_interval' in data:
            automation._interval = max(2, min(300, int(data['poll_interval'])))
        if 'hdr_mode' in data:
            runner.hdr_mode = PictureMode[data['hdr_mode']]
        if 'sdr_mode' in data:
            runner.sdr_mode = PictureMode[data['sdr_mode']]
        if 'settle_time' in data:
            runner.settle_time = max(1, min(60, int(data['settle_time'])))
        if 'automation_enabled' in data:
            _automation_enabled = bool(data['automation_enabled'])

        logger.info(f"Config loaded from {CONFIG_FILE}")
    except Exception as e:
        logger.warning(f"Failed to load config from {CONFIG_FILE}: {e}")


def _save_config():
    """Write current runner/automation settings to CONFIG_FILE."""
    data = {
        'jvc_host':           runner.projector_ip,
        'jvc_port':           runner.projector_port,
        'lumagen_port':       runner.lumagen_port,
        'poll_interval':      automation._interval,
        'hdr_mode':           runner.hdr_mode.name,
        'sdr_mode':           runner.sdr_mode.name,
        'settle_time':        runner.settle_time,
        'automation_enabled': _automation_enabled,
    }
    try:
        config_dir = os.path.dirname(os.path.abspath(CONFIG_FILE))
        os.makedirs(config_dir, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Config saved to {CONFIG_FILE}")
    except Exception as e:
        logger.warning(f"Failed to save config to {CONFIG_FILE}: {e}")


class AutomationManager:
    """Wraps JVC_LRP_Runner in a background thread with start/stop control."""

    def __init__(self, jvc_runner: JVC_LRP_Runner, interval: float = POLLING_INTERVAL):
        self._runner = jvc_runner
        self._interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()   # guards start/stop against concurrent calls

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        with self._lock:
            if self.running:
                return
            self._stop.clear()
            self._thread = threading.Thread(target=self._loop, daemon=True, name="hdr-automation")
            self._thread.start()
        logger.info("HDR automation started")

    def stop(self):
        with self._lock:
            if not self.running:
                return
            self._stop.set()
            thread = self._thread
            self._thread = None
        thread.join(timeout=15)   # join outside lock so start() can proceed if needed
        logger.info("HDR automation stopped")

    def _loop(self):
        while not self._stop.is_set():
            try:
                self._runner.run()
            except Exception:
                logger.exception("Automation loop error")
            self._stop.wait(self._interval)

    def status(self) -> dict:
        mode = self._runner.lumagen_input_mode
        return {
            'running': self.running,
            'content': mode.name,   # 'HDR', 'SDR', 'NA', 'ERR'
        }


automation = AutomationManager(runner)
_load_config()          # overlay persisted settings before starting the loop
if runner.projector_ip and _automation_enabled:
    automation.start()


def jvc_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not jvc:
            return jsonify({'success': False, 'error': 'JVC_HOST not configured'}), 503
        return fn(*args, **kwargs)
    return wrapper


# ══════════════════════════════════════════════════════════════════════════
#  Page routes
# ══════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/jvc')
def jvc_page():
    return render_template('jvc.html', jvc_host=JVC_HOST)


@app.route('/config')
def config_page():
    return render_template('config.html')


# ══════════════════════════════════════════════════════════════════════════
#  Automation API
# ══════════════════════════════════════════════════════════════════════════

@app.route('/api/automation/status', methods=['GET'])
def get_automation_status():
    return jsonify({'success': True, **automation.status()})


@app.route('/api/automation/start', methods=['POST'])
def start_automation():
    if not JVC_HOST:
        return jsonify({'success': False, 'error': 'JVC_HOST not configured'}), 503
    automation.start()
    return jsonify({'success': True, **automation.status()})


@app.route('/api/automation/stop', methods=['POST'])
def stop_automation():
    automation.stop()
    return jsonify({'success': True, **automation.status()})


@app.route('/api/automation/config', methods=['GET'])
def get_automation_config():
    return jsonify({
        'success':            True,
        'jvc_host':           runner.projector_ip,
        'jvc_port':           runner.projector_port,
        'lumagen_port':       runner.lumagen_port,
        'poll_interval':      automation._interval,
        'hdr_mode':           runner.hdr_mode.name,
        'sdr_mode':           runner.sdr_mode.name,
        'settle_time':        runner.settle_time,
        'automation_enabled': _automation_enabled,
        'picture_modes':      [m.name for m in PictureMode],
        'config_file':        CONFIG_FILE,
    })


@app.route('/api/automation/config', methods=['POST'])
def set_automation_config():
    global jvc, lumagen, _automation_enabled
    data = request.get_json() or {}

    if 'jvc_host' in data or 'jvc_port' in data:
        new_host = str(data.get('jvc_host', runner.projector_ip)).strip()
        new_port = int(data.get('jvc_port', runner.projector_port))
        runner.projector_ip   = new_host
        runner.projector_port = new_port
        jvc = JVCControl(host=new_host) if new_host else None
        logger.info(f"JVC config updated: {new_host}:{new_port}")

    if 'lumagen_port' in data:
        new_lport = str(data.get('lumagen_port', '')).strip()
        if new_lport:
            runner.lumagen_port        = new_lport
            lumagen                    = LumagenControl(port=new_lport)
            runner._lumagen_control    = lumagen
            logger.info(f"Lumagen port updated: {new_lport}")

    if 'poll_interval' in data:
        automation._interval = max(2, min(300, int(data['poll_interval'])))

    if 'hdr_mode' in data:
        try:
            runner.hdr_mode = PictureMode[data['hdr_mode']]
        except KeyError:
            return jsonify({'success': False, 'error': f"Unknown picture mode: {data['hdr_mode']}"}), 400

    if 'sdr_mode' in data:
        try:
            runner.sdr_mode = PictureMode[data['sdr_mode']]
        except KeyError:
            return jsonify({'success': False, 'error': f"Unknown picture mode: {data['sdr_mode']}"}), 400

    if 'settle_time' in data:
        runner.settle_time = max(1, min(60, int(data['settle_time'])))

    if 'automation_enabled' in data:
        _automation_enabled = bool(data['automation_enabled'])
        if _automation_enabled and runner.projector_ip:
            automation.start()
        elif not _automation_enabled:
            automation.stop()

    _save_config()
    return jsonify({
        'success':            True,
        'jvc_host':           runner.projector_ip,
        'jvc_port':           runner.projector_port,
        'lumagen_port':       runner.lumagen_port,
        'poll_interval':      automation._interval,
        'hdr_mode':           runner.hdr_mode.name,
        'sdr_mode':           runner.sdr_mode.name,
        'settle_time':        runner.settle_time,
        'automation_enabled': _automation_enabled,
        'config_file':        CONFIG_FILE,
    })


# ══════════════════════════════════════════════════════════════════════════
#  Lumagen API  (all handlers acquire lumagen_lock)
# ══════════════════════════════════════════════════════════════════════════

@app.route('/api/power/<action>', methods=['POST'])
def power_control(action):
    try:
        with lumagen_lock:
            if action == 'on':
                return jsonify({'success': True, 'message': 'Power On', 'response': lumagen.power_on()})
            elif action == 'standby':
                return jsonify({'success': True, 'message': 'Standby', 'response': lumagen.power_standby()})
            elif action == 'status':
                return jsonify({'success': True, 'status': lumagen.get_power_status()})
        return jsonify({'success': False, 'error': 'Invalid action'}), 400
    except Exception as e:
        logger.error(f"Power control error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/input/<int:input_num>', methods=['POST'])
def select_input(input_num):
    try:
        with lumagen_lock:
            return jsonify({'success': True, 'input': input_num, 'response': lumagen.select_input(input_num)})
    except Exception as e:
        logger.error(f"Input selection error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/memory/<memory>', methods=['POST'])
def select_memory(memory):
    try:
        with lumagen_lock:
            return jsonify({'success': True, 'memory': memory, 'response': lumagen.select_memory(memory)})
    except Exception as e:
        logger.error(f"Memory selection error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/aspect/<aspect>', methods=['POST'])
def set_aspect(aspect):
    try:
        aspect_map = {
            # Standard
            '4:3':        lumagen.set_aspect_4_3,
            'lbox':       lumagen.set_aspect_lbox,
            '16:9':       lumagen.set_aspect_16_9,
            '1.85':       lumagen.set_aspect_1_85,
            '2.35':       lumagen.set_aspect_2_35,
            'nls':        lumagen.set_aspect_nls,
            # Extended (Radiance Pro)
            '1.90':       lumagen.set_aspect_1_90,
            '2.00':       lumagen.set_aspect_2_00,
            '2.20':       lumagen.set_aspect_2_20,
            '2.40':       lumagen.set_aspect_2_40,
            # No-Zoom variants
            '4:3nz':      lumagen.set_aspect_4_3_nz,
            'lboxnz':     lumagen.set_aspect_lbox_nz,
            '16:9nz':     lumagen.set_aspect_16_9_nz,
            '1.85nz':     lumagen.set_aspect_1_85_nz,
            '2.35nz':     lumagen.set_aspect_2_35_nz,
            # Auto-aspect
            'auto_on':    lumagen.auto_aspect_enable,
            'auto_off':   lumagen.auto_aspect_disable,
            'auto_reset': lumagen.reset_auto_aspect,
        }
        if aspect not in aspect_map:
            return jsonify({'success': False, 'error': 'Invalid aspect ratio'}), 400
        with lumagen_lock:
            return jsonify({'success': True, 'aspect': aspect, 'response': aspect_map[aspect]()})
    except Exception as e:
        logger.error(f"Aspect ratio error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/zoom/<action>', methods=['POST'])
def zoom_control(action):
    try:
        with lumagen_lock:
            if action == 'in':
                return jsonify({'success': True, 'response': lumagen.zoom_in()})
            elif action == 'out':
                return jsonify({'success': True, 'response': lumagen.zoom_out()})
        return jsonify({'success': False, 'error': 'Invalid zoom action'}), 400
    except Exception as e:
        logger.error(f"Zoom control error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/output/<mode>', methods=['POST'])
def set_output_mode(mode):
    try:
        mode_map = {
            '480p':    lumagen.set_output_480p,
            '720p':    lumagen.set_output_720p,
            '1080p24': lumagen.set_output_1080p24,
            '1080p':   lumagen.set_output_1080p,
            '4k24':    lumagen.set_output_4k24,
            '4k60':    lumagen.set_output_4k60,
            'auto':    lumagen.set_output_auto,
        }
        if mode not in mode_map:
            return jsonify({'success': False, 'error': 'Invalid output mode'}), 400
        with lumagen_lock:
            return jsonify({'success': True, 'mode': mode, 'response': mode_map[mode]()})
    except Exception as e:
        logger.error(f"Output mode error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        with lumagen_lock:
            return jsonify({
                'success': True,
                'status':        lumagen.get_status(),
                'info':          lumagen.get_info(),
                'current_input': lumagen.get_current_input(),
            })
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/save', methods=['POST'])
def save_config():
    try:
        with lumagen_lock:
            return jsonify({'success': True, 'message': 'Configuration saved', 'response': lumagen.save_config()})
    except Exception as e:
        logger.error(f"Save error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/test-pattern/<action>', methods=['POST'])
def test_pattern(action):
    try:
        with lumagen_lock:
            if action == 'off':
                return jsonify({'success': True, 'response': lumagen.test_pattern_off()})
            elif action == 'contrast':
                return jsonify({'success': True, 'response': lumagen.test_pattern_contrast()})
        return jsonify({'success': False, 'error': 'Invalid test pattern'}), 400
    except Exception as e:
        logger.error(f"Test pattern error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════
#  JVC API
# ══════════════════════════════════════════════════════════════════════════

@app.route('/api/jvc/power/<action>', methods=['POST'])
@jvc_required
def jvc_power(action):
    try:
        if action == 'on':
            jvc.power_on()
            return jsonify({'success': True, 'message': 'Power On'})
        elif action == 'off':
            jvc.power_off()
            return jsonify({'success': True, 'message': 'Power Off'})
        return jsonify({'success': False, 'error': 'Invalid action'}), 400
    except Exception as e:
        logger.error(f"JVC power error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/jvc/input/<source>', methods=['POST'])
@jvc_required
def jvc_input(source):
    try:
        if source == 'hdmi1':
            jvc.select_hdmi1()
        elif source == 'hdmi2':
            jvc.select_hdmi2()
        else:
            return jsonify({'success': False, 'error': 'Invalid input'}), 400
        return jsonify({'success': True, 'input': source})
    except Exception as e:
        logger.error(f"JVC input error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/jvc/picture-mode/<mode_key>', methods=['POST'])
@jvc_required
def jvc_picture_mode(mode_key):
    try:
        jvc.set_picture_mode(mode_key)
        return jsonify({'success': True, 'mode': mode_key})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"JVC picture mode error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/jvc/status', methods=['GET'])
@jvc_required
def jvc_status():
    try:
        return jsonify({'success': True, **jvc.get_status()})
    except Exception as e:
        logger.error(f"JVC status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════
#  Navigation API
# ══════════════════════════════════════════════════════════════════════════

@app.route('/api/navigate/<action>', methods=['POST'])
def navigate(action):
    try:
        nav_map = {
            'menu':    lumagen.menu,
            'exit':    lumagen.exit_key,
            'ok':      lumagen.ok,
            'up':      lumagen.arrow_up,
            'down':    lumagen.arrow_down,
            'left':    lumagen.arrow_left,
            'right':   lumagen.arrow_right,
            'prev':    lumagen.prev_input,
            'osd_on':  lumagen.osd_on,
            'osd_off': lumagen.osd_off,
        }
        # digit_N → send the ASCII digit character directly
        if action.startswith('digit_') and len(action) == 7 and action[6].isdigit():
            digit = action[6]
            with lumagen_lock:
                return jsonify({'success': True, 'response': lumagen.send_command(digit)})
        if action not in nav_map:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400
        with lumagen_lock:
            return jsonify({'success': True, 'response': nav_map[action]()})
    except Exception as e:
        logger.error(f"Navigate error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════
#  Game Mode API
# ══════════════════════════════════════════════════════════════════════════

@app.route('/api/game-mode', methods=['GET'])
def get_game_mode():
    try:
        with lumagen_lock:
            raw = lumagen.get_game_mode()
        return jsonify({'success': True, 'game_mode': '1' in raw, 'raw': raw})
    except Exception as e:
        logger.error(f"Game mode query error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/game-mode/<int:state>', methods=['POST'])
def set_game_mode(state):
    try:
        with lumagen_lock:
            lumagen.set_game_mode(bool(state))
        return jsonify({'success': True, 'game_mode': bool(state)})
    except Exception as e:
        logger.error(f"Game mode set error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════
#  HDMI Hotplug API
# ══════════════════════════════════════════════════════════════════════════

@app.route('/api/hdmi-hotplug/<input_id>', methods=['POST'])
def hdmi_hotplug(input_id):
    try:
        with lumagen_lock:
            resp = lumagen.hdmi_hotplug(input_id)
        return jsonify({'success': True, 'input': input_id, 'response': resp})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"HDMI hotplug error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════
#  Sharpness API
# ══════════════════════════════════════════════════════════════════════════

@app.route('/api/sharpness', methods=['GET'])
def get_sharpness():
    try:
        with lumagen_lock:
            raw = lumagen.get_sharpness()
        return jsonify({'success': True, 'raw': raw})
    except Exception as e:
        logger.error(f"Sharpness query error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sharpness', methods=['POST'])
def set_sharpness():
    try:
        data = request.get_json() or {}
        enabled = bool(data.get('enabled', True))
        level = int(data.get('level', 4))
        sensitivity = data.get('sensitivity', 'N')
        with lumagen_lock:
            resp = lumagen.set_sharpness(enabled, level, sensitivity)
        return jsonify({'success': True, 'response': resp})
    except Exception as e:
        logger.error(f"Sharpness set error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════
#  Test Pattern (full library) API
# ══════════════════════════════════════════════════════════════════════════

@app.route('/api/test-pattern-full', methods=['POST'])
def test_pattern_full():
    try:
        data = request.get_json() or {}
        group = str(data.get('group', 'b'))
        sub = int(data.get('sub', 0))
        ire = int(data.get('ire', 100))
        with lumagen_lock:
            resp = lumagen.test_pattern_full(group, sub, ire)
        return jsonify({'success': True, 'pattern': f'{group},{sub}', 'ire': ire, 'response': resp})
    except Exception as e:
        logger.error(f"Test pattern full error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════
#  Output Format API
# ══════════════════════════════════════════════════════════════════════════

_FMT_NAMES = {0: 'YCbCr 4:2:2', 1: 'YCbCr 4:4:4', 2: 'RGB Video', 3: 'RGB PC', 4: 'YCbCr 4:2:0'}


@app.route('/api/output-format', methods=['GET'])
def get_output_format():
    try:
        with lumagen_lock:
            raw = lumagen.get_output_format()
        val = None
        if raw:
            try:
                val = int(raw.split(',')[-1].strip())
            except (ValueError, IndexError):
                pass
        return jsonify({'success': True, 'format': val,
                        'format_name': _FMT_NAMES.get(val, 'Unknown'), 'raw': raw})
    except Exception as e:
        logger.error(f"Output format query error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/output-format/<int:fmt>', methods=['POST'])
def set_output_format(fmt):
    try:
        with lumagen_lock:
            resp = lumagen.set_output_format(fmt)
        return jsonify({'success': True, 'format': fmt,
                        'format_name': _FMT_NAMES.get(fmt, 'Unknown'), 'response': resp})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Output format set error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════
#  CMS / Style API
# ══════════════════════════════════════════════════════════════════════════

@app.route('/api/cms-style', methods=['POST'])
def set_cms_style():
    try:
        data = request.get_json() or {}
        with lumagen_lock:
            resp = lumagen.set_cms_style(
                mode=data.get('mode', 'K'),
                cms_sdr=data.get('cms_sdr', 'K'),
                cms_hdr=data.get('cms_hdr', 'K'),
                style=data.get('style', 'K'),
            )
        return jsonify({'success': True, 'response': resp})
    except Exception as e:
        logger.error(f"CMS/Style error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════
#  PIP API
# ══════════════════════════════════════════════════════════════════════════

@app.route('/api/pip/<action>', methods=['POST'])
def pip_control(action):
    try:
        pip_map = {
            'off':    lumagen.pip_off,
            'select': lumagen.pip_select,
            'swap':   lumagen.pip_swap,
            'mode':   lumagen.pip_mode,
        }
        if action not in pip_map:
            return jsonify({'success': False, 'error': 'Invalid PIP action'}), 400
        with lumagen_lock:
            return jsonify({'success': True, 'response': pip_map[action]()})
    except Exception as e:
        logger.error(f"PIP error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════
#  Deinterlace API
# ══════════════════════════════════════════════════════════════════════════

_DEINT_NAMES = {'0': 'Auto', '1': 'Film', '2': 'Video'}


@app.route('/api/deinterlace', methods=['GET'])
def get_deinterlace():
    try:
        with lumagen_lock:
            raw = lumagen.get_deinterlace_mode()
        val = raw.split(',')[-1].strip() if raw else None
        return jsonify({'success': True, 'mode': val,
                        'mode_name': _DEINT_NAMES.get(val, 'Unknown'), 'raw': raw})
    except Exception as e:
        logger.error(f"Deinterlace query error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/deinterlace/<int:mode>', methods=['POST'])
def set_deinterlace(mode):
    try:
        with lumagen_lock:
            resp = lumagen.set_deinterlace_mode(mode)
        return jsonify({'success': True, 'mode': mode, 'response': resp})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Deinterlace set error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════
#  Rich Status API
# ══════════════════════════════════════════════════════════════════════════

_ASPECT_IDX = {'0': '4:3', '1': 'LBOX', '2': '16:9', '3': '1.85', '4': '2.35',
               '8': 'ALT-1.85', '9': 'ALT-2.35'}
_CS_NAMES    = {0: 'BT.601', 1: 'BT.709', 2: 'BT.2020', 3: 'BT.2100'}


def _parse_rich(full, info, input_video, input_aspect, output_mode_name, output_fmt, game_mode_raw):
    r = {}

    if full:
        p = full.split(',')
        try:
            m = int(p[1]) if len(p) > 1 else -1
            r['input_status'] = {0: 'No Source', 1: 'Active Video', 2: 'Test Pattern'}.get(m, '?')
            r['input_active'] = m == 1

            if len(p) > 17:
                rate = int(p[2])
                vres = int(p[3])
                f_val = int(p[17])
                r['source_resolution'] = vres
                r['source_rate'] = rate
                r['hdr'] = f_val == 1
                r['hdr_label'] = 'HDR' if f_val == 1 else 'SDR'

            if len(p) > 18:
                g = p[18]
                r['source_scan'] = 'Progressive' if g == 'p' else ('Interlaced' if g == 'i' else 'No Input')

            if len(p) > 8:
                asp = int(p[7])
                r['source_aspect'] = f"{asp / 100:.2f}" if asp else '—'
                r['nls_active'] = p[8] == 'N'

            if len(p) > 16:
                prate = int(p[13])
                qres = int(p[14])
                cs = int(p[16])
                r['output_resolution'] = qres
                r['output_rate'] = prate
                r['output_colorspace'] = _CS_NAMES.get(cs, '?')
                out_asp = int(p[15])
                r['output_aspect'] = f"{out_asp / 100:.2f}" if out_asp else '—'

            if len(p) > 12:
                r['cms'] = int(p[11])
                r['style'] = int(p[12])

            if len(p) > 19:
                h = p[19]
                r['output_scan'] = 'Progressive' if h == 'P' else ('Interlaced' if h == 'I' else '?')

            if len(p) > 21:
                r['virtual_input'] = int(p[20])
                r['physical_input'] = int(p[21])
        except (ValueError, IndexError):
            pass

    if info:
        p = info.split(',')
        if len(p) >= 5:
            r['model'] = p[1]
            r['firmware'] = p[2]
            r['serial'] = p[4].strip()

    if input_video:
        p = input_video.split(',')
        try:
            if len(p) >= 5:
                rate100 = int(p[2])
                hres = int(p[3])
                vres = int(p[4])
                interlaced = int(p[5]) if len(p) > 5 else 0
                scan = 'i' if interlaced else 'p'
                rate_hz = rate100 / 100
                r['source_detail'] = f"{hres}×{vres}{scan} @ {rate_hz:.2f} Hz" if hres else '—'
        except (ValueError, IndexError):
            pass

    if input_aspect:
        p = input_aspect.split(',')
        if len(p) >= 2:
            xy = p[1].strip()
            if xy:
                r['input_aspect'] = _ASPECT_IDX.get(xy[0], '?')
                r['nls_mode'] = len(xy) > 1 and xy[1] == 'N'

    if output_mode_name:
        name = output_mode_name
        if ',' in name:
            name = name.split(',', 1)[1]
        r['output_mode_name'] = name.strip()

    if output_fmt:
        try:
            val = int(output_fmt.split(',')[-1].strip())
            r['output_format'] = _FMT_NAMES.get(val, '?')
        except (ValueError, IndexError):
            pass

    if game_mode_raw:
        r['game_mode'] = '1' in game_mode_raw

    return r


@app.route('/api/rich-status', methods=['GET'])
def get_rich_status():
    try:
        with lumagen_lock:
            full          = lumagen.get_status()
            info          = lumagen.get_info()
            input_video   = lumagen.get_input_video()
            input_aspect  = lumagen.get_input_aspect()
            output_mode   = lumagen.get_output_mode_name()
            output_fmt    = lumagen.get_output_format()
            game_mode_raw = lumagen.get_game_mode()
        parsed = _parse_rich(full, info, input_video, input_aspect, output_mode, output_fmt, game_mode_raw)
        return jsonify({'success': True, **parsed,
                        '_raw': {'full': full, 'info': info, 'input_video': input_video,
                                 'input_aspect': input_aspect, 'output_mode': output_mode,
                                 'output_fmt': output_fmt}})
    except Exception as e:
        logger.error(f"Rich status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
