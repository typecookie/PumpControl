# app/routes/api_routes.py
from flask import Blueprint, jsonify, request
from app.controllers.pump_controller import PumpController
from app.utils.gpio_utils import GPIOManager
from app.utils.config_utils import SUMMER_HIGH, SUMMER_LOW, SUMMER_EMPTY, WINTER_HIGH, WINTER_LOW, WELL_PUMP, DIST_PUMP
from .. import pump_controller  # Import the pump_controller instance from app package


from ..controllers.mode_controller import ModeController

bp = Blueprint('api', __name__, url_prefix='/api')

mode_controller = ModeController()

@bp.route('/state')
def get_state():
    try:
        return jsonify(pump_controller.get_system_state())
    except Exception as e:
        print(f"Error in get_state: {e}")
        return jsonify({
            'error': str(e),
            'current_mode': pump_controller.mode_controller.get_current_mode(),
            'summer_tank': {'state': 'unknown', 'stats': {}},
            'winter_tank': {'state': 'unknown', 'stats': {}},
            'well_pump_status': 'unknown',
            'dist_pump_status': 'unknown',
            'timestamp': pump_controller.get_timestamp()
        })

@bp.route('/mode', methods=['POST'])
def change_mode():
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data received'
            }), 400

        new_mode = data.get('mode')
        confirm = data.get('confirm', False)
        
        print(f"Mode change request - New mode: {new_mode}, Confirm: {confirm}")
        
        if not new_mode:
            return jsonify({
                'status': 'error',
                'message': 'No mode specified'
            }), 400
            
        result = pump_controller.mode_controller.request_mode_change(new_mode, confirm)
        
        if isinstance(result, tuple):
            response, status_code = result
            return jsonify(response), status_code
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in mode change endpoint: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

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