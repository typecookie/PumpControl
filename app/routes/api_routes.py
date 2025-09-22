from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from ..models.user import UserRole, operator_required
from ..controllers import pump_controller, mode_controller
from ..utils.config_utils import (
    WELL_PUMP, DIST_PUMP, SUMMER_HIGH, SUMMER_LOW,
    SUMMER_EMPTY, WINTER_HIGH, WINTER_LOW
)
from ..utils.gpio_utils import GPIOManager
from RPi import GPIO
from ..models.tank_state import TankState
from ..utils.config_utils import ConfigManager
from app.models.tank_state import TankState

bp = Blueprint('api', __name__)
diagnostics_bp = Blueprint('diagnostics', __name__, url_prefix='/diagnostics')


@bp.route('/state', methods=['GET'])
@login_required
def get_state():
    """Get current system state"""
    try:
        # Get basic system state
        state = pump_controller.get_system_state()

        # Add current mode and well pump reverse state
        state['current_mode'] = mode_controller.get_current_mode()
        state['well_pump_reverse'] = GPIOManager.get_well_pump_reverse_state()

        # Add detailed GPIO states
        state['gpio_states'] = {
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
                    'value': GPIOManager.get_pump_state(WELL_PUMP),
                    'reverse_mode': GPIOManager.get_well_pump_reverse_state(),
                    'output_inverted': GPIOManager.get_well_output_invert_state()
                },
                'distribution': {
                    'pin': DIST_PUMP,
                    'value': GPIOManager.get_pump_state(DIST_PUMP)
                }
            }
        }

        return jsonify(state)
    except Exception as e:
        print(f"Error in get_state: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route('/gpio_states', methods=['GET'])
@login_required
def get_gpio_states():
    """Get raw GPIO states"""
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
                    'value': GPIOManager.get_pump_state(WELL_PUMP),
                    'reverse_mode': GPIOManager.get_well_pump_reverse_state(),
                    'output_inverted': GPIOManager.get_well_output_invert_state()
                },
                'distribution': {
                    'pin': DIST_PUMP,
                    'value': GPIOManager.get_pump_state(DIST_PUMP)
                }
            }
        }
        return jsonify(states)
    except Exception as e:
        print(f"Error in get_gpio_states: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route('/pump', methods=['POST'])
@login_required
@operator_required
def control_pump():
    """Control well pump"""
    try:
        data = request.get_json()
        if not data or 'running' not in data:
            return jsonify({'status': 'error', 'message': 'Running state not specified'}), 400

        current_mode = mode_controller.get_current_mode()
        if current_mode == 'CHANGEOVER':
            # In changeover mode, use the handler's manual control
            handler = mode_controller._handlers['CHANGEOVER']
            result = handler.set_manual_well_pump(bool(data['running']))
        else:
            # In other modes, use the pump controller directly
            result = pump_controller.set_well_pump(bool(data['running']))

        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route('/distribution_pump', methods=['POST'])
@login_required
@operator_required
def control_distribution_pump():
    """Control distribution pump"""
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
    """Change system mode"""
    try:
        data = request.get_json()
        new_mode = data.get('mode')
        confirm = data.get('confirm', False)

        if new_mode not in ['SUMMER', 'WINTER', 'CHANGEOVER']:
            return jsonify({'status': 'error', 'message': 'Invalid mode specified'}), 400

        result = mode_controller.request_mode_change(new_mode, confirm)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route('/well-pump-reverse', methods=['POST'])
@login_required
def toggle_well_pump_reverse():
    """Toggle well pump reverse mode"""
    if not current_user.has_role(UserRole.ADMINISTRATOR):
        return jsonify({'status': 'error', 'message': 'Administrator privileges required'}), 403

    try:
        data = request.get_json()
        if not data or 'enabled' not in data:
            return jsonify({'status': 'error', 'message': 'Enabled state not specified'}), 400

        result = GPIOManager.set_well_pump_reverse(bool(data['enabled']))
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route('/pump/output-invert', methods=['POST'])
@login_required
def toggle_pump_output_invert():
    """Toggle pump output inversion"""
    if not current_user.has_role(UserRole.ADMINISTRATOR):
        return jsonify({'status': 'error', 'message': 'Administrator privileges required'}), 403

    try:
        data = request.get_json()
        if not data or 'enabled' not in data:
            return jsonify({'status': 'error', 'message': 'Enabled state not specified'}), 400

        result = GPIOManager.set_well_output_invert(bool(data['enabled']))
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route('/winter-config', methods=['POST'])
@login_required
@operator_required
def configure_winter_mode():
    """Configure winter mode settings"""
    try:
        data = request.get_json()
        if not data or 'low_timeout' not in data:
            return jsonify({'status': 'error', 'message': 'Low state timeout not specified'}), 400

        timeout = int(data['low_timeout'])
        if timeout < 0:
            return jsonify({'status': 'error', 'message': 'Timeout must be positive'}), 400

        config = ConfigManager.get_config()
        config['winter_low_timeout'] = timeout
        ConfigManager.save_config()

        return jsonify({
            'status': 'success',
            'message': f'Winter mode low state timeout set to {timeout} seconds'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route('/mode/status', methods=['GET'])
@login_required
def get_mode_status():
    """Get detailed mode status"""
    try:
        current_mode = mode_controller.get_current_mode()
        handler = mode_controller._current_handler

        status = {
            'current_mode': current_mode,
            'tank_states': handler.get_tank_states() if handler else {},
            'pump_states': pump_controller.get_system_state(),
            'mode_specific': {}
        }

        # Add mode-specific information
        if current_mode == 'WINTER':
            config = ConfigManager.get_config()
            status['mode_specific'] = {
                'low_timeout': config.get('winter_low_timeout', 300),
                'low_state_active': handler._low_state_start_time is not None if handler else False
            }

        return jsonify(status)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

"""
@bp.route('/diagnostics/winter', methods=['GET'])
@login_required
def winter_diagnostics():
    # ... code removed to prevent duplicate ...
"""

@bp.route('/diagnostics/control-flow', methods=['POST'])
@login_required
@operator_required
def test_control_flow():
    """Test the control flow from mode controller to pump"""
    try:
        data = request.get_json()
        desired_state = data.get('state', True)
        
        steps = []
        
        # Step 1: Check current mode
        current_mode = mode_controller.get_current_mode()
        steps.append({
            'step': 'Check Mode',
            'mode': current_mode,
            'status': 'ok'
        })

        # Step 2: Get handler
        handler = mode_controller._current_handler
        steps.append({
            'step': 'Get Handler',
            'handler': type(handler).__name__ if handler else None,
            'status': 'ok' if handler else 'error'
        })

        # Step 3: Test pump controller
        try:
            result = pump_controller.set_well_pump(desired_state)
            steps.append({
                'step': 'Set Pump',
                'desired_state': desired_state,
                'result': result,
                'status': 'ok' if result.get('status') == 'success' else 'error'
            })
        except Exception as e:
            steps.append({
                'step': 'Set Pump',
                'error': str(e),
                'status': 'error'
            })

        # Step 4: Verify pump state
        actual_state = pump_controller.get_well_pump_state()
        steps.append({
            'step': 'Verify Pump',
            'desired_state': desired_state,
            'actual_state': actual_state,
            'status': 'ok' if actual_state == desired_state else 'error'
        })

        return jsonify({
            'status': 'complete',
            'steps': steps
        })
    except Exception as e:
        print(f"Error in control flow test: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'status': 'error', 'message': str(e)}), 500

from flask import Blueprint, jsonify
from flask_login import login_required
from ..controllers import pump_controller, mode_controller
from ..utils.config_utils import (
    WELL_PUMP, DIST_PUMP, WINTER_HIGH, WINTER_LOW
)
from ..utils.gpio_utils import GPIOManager
from RPi import GPIO
from datetime import datetime

@diagnostics_bp.route('/system', methods=['GET'])
@login_required
def system_diagnostics():
    """Get complete system diagnostics"""
    try:
        # Get mode information
        mode_info = {
            'current_mode': mode_controller.get_current_mode(),
            'handler_active': mode_controller._current_handler is not None,
            'handler_type': type(mode_controller._current_handler).__name__ if mode_controller._current_handler else None
        }

        # Get GPIO states
        gpio_states = {
            'winter_tank': {
                'high': {
                    'pin': WINTER_HIGH,
                    'raw': GPIOManager.get_raw_sensor_state(WINTER_HIGH),
                    'processed': GPIOManager.get_sensor_state(WINTER_HIGH)
                },
                'low': {
                    'pin': WINTER_LOW,
                    'raw': GPIOManager.get_raw_sensor_state(WINTER_LOW),
                    'processed': GPIOManager.get_sensor_state(WINTER_LOW)
                }
            },
            'pumps': {
                'well': {
                    'pin': WELL_PUMP,
                    'raw_state': GPIO.input(WELL_PUMP),
                    'processed_state': GPIOManager.get_pump_state(WELL_PUMP),
                    'reverse_mode': GPIOManager.get_well_pump_reverse_state(),
                    'inverted': GPIOManager.get_well_output_invert_state()
                },
                'distribution': {
                    'pin': DIST_PUMP,
                    'raw_state': GPIO.input(DIST_PUMP),
                    'processed_state': GPIOManager.get_pump_state(DIST_PUMP)
                }
            }
        }

        # Get pump controller state
        pump_info = {
            'initialized': pump_controller._initialized,
            'running': pump_controller.is_running,
            'thread_active': pump_controller.pump_thread and pump_controller.pump_thread.is_alive() if hasattr(pump_controller, 'pump_thread') else False
        }

        return jsonify({
            'mode': mode_info,
            'gpio': gpio_states,
            'pump_controller': pump_info,
            'last_system_state': pump_controller._last_state
        })
    except Exception as e:
        import traceback
        print(f"Error in system diagnostics: {e}")
        print(traceback.format_exc())
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route('/diagnostics/winter', methods=['GET'])
@login_required
def winter_diagnostics():
    """Get detailed winter mode diagnostics"""
    try:
        # Get raw sensor states
        winter_sensors = {
            'high': {
                'pin': WINTER_HIGH,
                'raw': GPIOManager.get_raw_sensor_state(WINTER_HIGH),
                'processed': GPIOManager.get_sensor_state(WINTER_HIGH)
            },
            'low': {
                'pin': WINTER_LOW,
                'raw': GPIOManager.get_raw_sensor_state(WINTER_LOW),
                'processed': GPIOManager.get_sensor_state(WINTER_LOW)
            }
        }

        # Get pump states
        well_pump = {
            'pin': WELL_PUMP,
            'raw_state': GPIO.input(WELL_PUMP),
            'logical_state': GPIOManager.get_pump_state(WELL_PUMP),
            'reverse_mode': GPIOManager.get_well_pump_reverse_state(),
            'inverted': GPIOManager.get_well_output_invert_state()
        }

        # Get current mode info
        current_mode = mode_controller.get_current_mode()
        handler = mode_controller._current_handler

        # Create tank state and update it
        tank_state = TankState('Winter')
        tank_state.update_from_sensors(GPIOManager)

        diagnostics = {
            'mode': {
                'current': current_mode,
                'handler_active': handler is not None,
                'handler_type': type(handler).__name__ if handler else None
            },
            'sensors': winter_sensors,
            'well_pump': well_pump,
            'tank_state': {
                'raw': {
                    'winter_high': tank_state.winter_high,
                    'winter_low': tank_state.winter_low
                },
                'computed_state': tank_state.state
            },
            'handler_state': handler.get_handler_state() if handler and current_mode == 'WINTER' else None,
            'system_state': pump_controller.get_system_state()
        }

        return jsonify(diagnostics)
    except Exception as e:
        print(f"Error in winter diagnostics: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'status': 'error', 'message': str(e)}), 500