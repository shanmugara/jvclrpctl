"""
Flask Web UI for Lumagen Radiance Pro Control
Runs on Raspberry Pi - accessible via browser
"""

from flask import Flask, render_template, jsonify, request
from lumagen_control import LumagenControl
import os
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Lumagen controller
# Change port to match your setup
LUMAGEN_PORT = os.getenv('LUMAGEN_PORT', '/dev/ttyUSB1')
lumagen = LumagenControl(port=LUMAGEN_PORT)

# Try to connect on startup
try:
    if lumagen.connect():
        logger.info(f"Connected to Lumagen on {LUMAGEN_PORT}")
    else:
        logger.warning(f"Could not connect to Lumagen on {LUMAGEN_PORT}")
except Exception as e:
    logger.error(f"Error connecting to Lumagen: {e}")


@app.route('/')
def index():
    """Main UI page"""
    return render_template('index.html')


@app.route('/api/power/<action>', methods=['POST'])
def power_control(action):
    """Power on/off/status"""
    try:
        if action == 'on':
            response = lumagen.power_on()
            return jsonify({'success': True, 'message': 'Power On', 'response': response})
        elif action == 'standby':
            response = lumagen.power_standby()
            return jsonify({'success': True, 'message': 'Standby', 'response': response})
        elif action == 'status':
            response = lumagen.get_power_status()
            return jsonify({'success': True, 'status': response})
        else:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400
    except Exception as e:
        logger.error(f"Power control error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/input/<int:input_num>', methods=['POST'])
def select_input(input_num):
    """Select input 1-10"""
    try:
        response = lumagen.select_input(input_num)
        return jsonify({'success': True, 'input': input_num, 'response': response})
    except Exception as e:
        logger.error(f"Input selection error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/memory/<memory>', methods=['POST'])
def select_memory(memory):
    """Select memory A/B/C/D"""
    try:
        response = lumagen.select_memory(memory)
        return jsonify({'success': True, 'memory': memory, 'response': response})
    except Exception as e:
        logger.error(f"Memory selection error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/aspect/<aspect>', methods=['POST'])
def set_aspect(aspect):
    """Set aspect ratio"""
    try:
        aspect_map = {
            '4:3': lumagen.set_aspect_4_3,
            'lbox': lumagen.set_aspect_lbox,
            '16:9': lumagen.set_aspect_16_9,
            '1.85': lumagen.set_aspect_1_85,
            '2.35': lumagen.set_aspect_2_35,
            'nls': lumagen.set_aspect_nls
        }
        
        if aspect not in aspect_map:
            return jsonify({'success': False, 'error': 'Invalid aspect ratio'}), 400
        
        response = aspect_map[aspect]()
        return jsonify({'success': True, 'aspect': aspect, 'response': response})
    except Exception as e:
        logger.error(f"Aspect ratio error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/zoom/<action>', methods=['POST'])
def zoom_control(action):
    """Zoom in/out"""
    try:
        if action == 'in':
            response = lumagen.zoom_in()
        elif action == 'out':
            response = lumagen.zoom_out()
        else:
            return jsonify({'success': False, 'error': 'Invalid zoom action'}), 400
        
        return jsonify({'success': True, 'action': action, 'response': response})
    except Exception as e:
        logger.error(f"Zoom control error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/output/<mode>', methods=['POST'])
def set_output_mode(mode):
    """Set output resolution"""
    try:
        mode_map = {
            '480p': lumagen.set_output_480p,
            '720p': lumagen.set_output_720p,
            '1080p24': lumagen.set_output_1080p24,
            '1080p': lumagen.set_output_1080p,
            '4k24': lumagen.set_output_4k24,
            '4k60': lumagen.set_output_4k60,
            'auto': lumagen.set_output_auto
        }
        
        if mode not in mode_map:
            return jsonify({'success': False, 'error': 'Invalid output mode'}), 400
        
        response = mode_map[mode]()
        return jsonify({'success': True, 'mode': mode, 'response': response})
    except Exception as e:
        logger.error(f"Output mode error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get Lumagen status"""
    try:
        status = lumagen.get_status()
        info = lumagen.get_info()
        current_input = lumagen.get_current_input()
        
        return jsonify({
            'success': True,
            'status': status,
            'info': info,
            'current_input': current_input
        })
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/save', methods=['POST'])
def save_config():
    """Save current configuration"""
    try:
        response = lumagen.save_config()
        return jsonify({'success': True, 'message': 'Configuration saved', 'response': response})
    except Exception as e:
        logger.error(f"Save error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/test-pattern/<action>', methods=['POST'])
def test_pattern(action):
    """Control test patterns"""
    try:
        if action == 'off':
            response = lumagen.test_pattern_off()
        elif action == 'contrast':
            response = lumagen.test_pattern_contrast()
        else:
            return jsonify({'success': False, 'error': 'Invalid test pattern'}), 400
        
        return jsonify({'success': True, 'pattern': action, 'response': response})
    except Exception as e:
        logger.error(f"Test pattern error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # Run on all interfaces so it's accessible on network
    app.run(host='0.0.0.0', port=5001, debug=True)
