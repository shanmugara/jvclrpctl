"""
Flask Web UI for Lumagen Radiance Pro + JVC D-ILA Projector Control
Unified service: manual controls + background HDR automation (runner.py).
"""

import sys
import os
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
from jvclrpctl.lumagen.constants import LRPInputModes
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    lumagen_lock=lumagen_lock,   # shared lock — releases port before JVC ops
)


class AutomationManager:
    """Wraps JVC_LRP_Runner in a background thread with start/stop control."""

    def __init__(self, jvc_runner: JVC_LRP_Runner, interval: float = POLLING_INTERVAL):
        self._runner = jvc_runner
        self._interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="hdr-automation")
        self._thread.start()
        logger.info("HDR automation started")

    def stop(self):
        if not self.running:
            return
        self._stop.set()
        self._thread.join(timeout=15)
        self._thread = None
        logger.info("HDR automation stopped")

    def _loop(self):
        while not self._stop.is_set():
            try:
                self._runner.run()
            except Exception as e:
                logger.error(f"Automation loop error: {e}")
            self._stop.wait(self._interval)

    def status(self) -> dict:
        mode = self._runner.lumagen_input_mode
        return {
            'running': self.running,
            'content': mode.name,   # 'HDR', 'SDR', 'NA', 'ERR'
        }


automation = AutomationManager(runner)
if JVC_HOST:
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
            '4:3': lumagen.set_aspect_4_3,
            'lbox': lumagen.set_aspect_lbox,
            '16:9': lumagen.set_aspect_16_9,
            '1.85': lumagen.set_aspect_1_85,
            '2.35': lumagen.set_aspect_2_35,
            'nls': lumagen.set_aspect_nls,
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
