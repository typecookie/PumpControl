from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from ..models.user import UserRole
from ..controllers import pump_controller, mode_controller
from app.models.user import operator_required
from ..utils.config_utils import (
    WELL_PUMP, DIST_PUMP, SUMMER_HIGH, SUMMER_LOW, 
    SUMMER_EMPTY, WINTER_HIGH, WINTER_LOW
)
from ..utils.gpio_utils import GPIOManager

bp = Blueprint('api', __name__)

@bp.route('/state', methods=['GET'])
@login_required
def get_state():
    """Get current system state"""
    try:
        # Use the existing get_system_state method which has all the info we need
        state = pump_controller.get_system_state()
        return jsonify(state)
    except Exception as e:
        import traceback
        print(f"Error in get_state: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/gpio_states', methods=['GET'])
@login_required
def get_gpio_states():
    try:
        states = {
            'summer_tank': {
                'high': {
                    'pin': SUMMER_HIGH,
                    'raw_value': GPIOManager.get_sensor_state(SUMMER_HIGH),
                    'inverted_value': not GPIOManager.get_sensor_state(SUMMER_HIGH)
                },
                'low': {
                    'pin': SUMMER_LOW,
                    'raw_value': GPIOManager.get_sensor_state(SUMMER_LOW),
                    'inverted_value': not GPIOManager.get_sensor_state(SUMMER_LOW)
                },
                'empty': {
                    'pin': SUMMER_EMPTY,
                    'raw_value': GPIOManager.get_sensor_state(SUMMER_EMPTY),
                    'inverted_value': not GPIOManager.get_sensor_state(SUMMER_EMPTY)
                }
            },
            'winter_tank': {
                'high': {
                    'pin': WINTER_HIGH,
                    'raw_value': GPIOManager.get_sensor_state(WINTER_HIGH),
                    'inverted_value': not GPIOManager.get_sensor_state(WINTER_HIGH)
                },
                'low': {
                    'pin': WINTER_LOW,
                    'raw_value': GPIOManager.get_sensor_state(WINTER_LOW),
                    'inverted_value': not GPIOManager.get_sensor_state(WINTER_LOW)
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
        return jsonify(states)
    except Exception as e:
        import traceback
        print(f"Error in get_gpio_states: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/pump', methods=['POST'])
@login_required
@operator_required
def control_pump():
    try:
        data = request.get_json()
        if not data or 'running' not in data:
            return jsonify({'status': 'error', 'message': 'Running state not specified'}), 400

        result = pump_controller.set_manual_pump(bool(data['running']))
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/distribution_pump', methods=['POST'])
@login_required
@operator_required
def control_distribution_pump():
    try:
        data = request.get_json()
        if not data or 'running' not in data:
            return jsonify({'status': 'error', 'message': 'Running state not specified'}), 400

        result = pump_controller.set_distribution_pump(bool(data['running']))
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/mode', methods=['POST'])
@login_required
@operator_required
def change_mode():
    try:
        data = request.get_json()
        new_mode = data.get('mode')
        confirm = data.get('confirm', False)
        
        if new_mode not in ['SUMMER', 'WINTER', 'CHANGEOVER']:
            return jsonify({'status': 'error', 'message': 'Invalid mode specified'}), 400
        
        # Use the mode controller's request_mode_change method
        result = mode_controller.request_mode_change(new_mode, confirm)
        
        # If it's a dictionary, return it directly
        if isinstance(result, dict):
            return jsonify(result)
        
        # If it's a tuple (result, status_code), return it properly
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
            
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500