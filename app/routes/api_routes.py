# app/routes/api_routes.py
from flask import Blueprint, jsonify, request
from app.controllers.pump_controller import PumpController
from app.utils.gpio_utils import GPIOManager
from app.config import SUMMER_HIGH, SUMMER_LOW, SUMMER_EMPTY, WINTER_HIGH, WINTER_LOW, WELL_PUMP, DIST_PUMP

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/state')
def get_state():
    controller = PumpController()
    try:
        return jsonify(controller.get_system_state())
    except Exception as e:
        print(f"Error in get_state: {e}")
        return jsonify({
            'error': str(e),
            'current_mode': controller.current_mode,
            'summer_tank': {'state': 'unknown', 'stats': {}},
            'winter_tank': {'state': 'unknown', 'stats': {}},
            'well_pump_status': 'unknown',
            'dist_pump_status': 'unknown',
            'timestamp': controller.get_timestamp()
        })

@bp.route('/mode', methods=['POST'])
def change_mode():
    controller = PumpController()
    try:
        new_mode = request.json.get('mode')
        confirm = request.json.get('confirm', False)
        return jsonify(controller.request_mode_change(new_mode, confirm))
    except Exception as e:
        print(f"Error in change_mode: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/gpio_states')
def get_gpio_states():
    try:
        gpio_states = {
            'summer_tank': {
                'high': {
                    'pin': SUMMER_HIGH,
                    'raw_value': GPIOManager.get_raw_sensor_state(SUMMER_HIGH),
                    'inverted_value': GPIOManager.get_sensor_state(SUMMER_HIGH)
                },
                'low': {
                    'pin': SUMMER_LOW,
                    'raw_value': GPIOManager.get_raw_sensor_state(SUMMER_LOW),
                    'inverted_value': GPIOManager.get_sensor_state(SUMMER_LOW)
                },
                'empty': {
                    'pin': SUMMER_EMPTY,
                    'raw_value': GPIOManager.get_raw_sensor_state(SUMMER_EMPTY),
                    'inverted_value': GPIOManager.get_sensor_state(SUMMER_EMPTY)
                }
            },
            'winter_tank': {
                'high': {
                    'pin': WINTER_HIGH,
                    'raw_value': GPIOManager.get_raw_sensor_state(WINTER_HIGH),
                    'inverted_value': GPIOManager.get_sensor_state(WINTER_HIGH)
                },
                'low': {
                    'pin': WINTER_LOW,
                    'raw_value': GPIOManager.get_raw_sensor_state(WINTER_LOW),
                    'inverted_value': GPIOManager.get_sensor_state(WINTER_LOW)
                }
            },
            'pumps': {
                'well': {
                    'pin': WELL_PUMP,
                    'value': GPIOManager.get_pump_state(WELL_PUMP)
                },
                'distribution': {
                    'pin': DIST_PUMP,
                    'value': GPIOManager.get_pump_state(DIST_PUMP)
                }
            }
        }
        return jsonify(gpio_states)
    except Exception as e:
        print(f"Error getting GPIO states: {e}")
        return jsonify({'error': str(e)})

@bp.route('/thread_status')
def get_thread_status():
    controller = PumpController()
    try:
        return jsonify({
            'thread_running': controller.is_running,
            'last_update': controller.get_timestamp()
        })
    except Exception as e:
        return jsonify({
            'thread_running': False,
            'error': str(e)
        })

@bp.route('/manual_pump', methods=['POST'])
def manual_pump():
    controller = PumpController()
    try:
        running = request.json.get('running', False)
        return jsonify(controller.set_manual_pump(running))
    except Exception as e:
        print(f"Error in manual_pump: {e}")
        return jsonify({'error': str(e)}), 500