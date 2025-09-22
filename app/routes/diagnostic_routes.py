from datetime import datetime  # Make sure it's imported this way

from flask import Blueprint, jsonify
from flask_login import login_required
from ..controllers import pump_controller, mode_controller
from ..utils.config_utils import (
    WELL_PUMP, DIST_PUMP, WINTER_HIGH, WINTER_LOW
)
from ..utils.gpio_utils import GPIOManager
from RPi import GPIO
from app.models.tank_state import TankState

diagnostics_bp = Blueprint('diagnostics', __name__, url_prefix='/diagnostics')

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

@diagnostics_bp.route('/winter', methods=['GET'])
@login_required
def winter_diagnostics():
    """Get winter mode specific diagnostics"""
    try:
        # Create diagnostic snapshot
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'mode': mode_controller.get_current_mode(),
            'gpio_raw': {
                'winter_high': GPIO.input(WINTER_HIGH),
                'winter_low': GPIO.input(WINTER_LOW),
                'well_pump': GPIO.input(WELL_PUMP),
                'dist_pump': GPIO.input(DIST_PUMP)
            },
            'gpio_processed': {
                'winter_high': GPIOManager.get_sensor_state(WINTER_HIGH),
                'winter_low': GPIOManager.get_sensor_state(WINTER_LOW),
                'well_pump': GPIOManager.get_pump_state(WELL_PUMP),
                'dist_pump': GPIOManager.get_pump_state(DIST_PUMP)
            }
        }

        # Get handler state if in winter mode
        if mode_controller.get_current_mode() == "WINTER" and mode_controller._current_handler:
            handler = mode_controller._current_handler
            try:
                snapshot['handler_state'] = handler.get_handler_state()
            except AttributeError:
                # Fallback for backward compatibility
                snapshot['handler_state'] = {
                    'low_state_active': handler._low_state_time is not None,
                    'pump_started_from_low': handler._pump_started_from_low,
                    'last_state': handler._last_state
                }

        return jsonify(snapshot)
    except Exception as e:
        import traceback
        print(f"Error in winter diagnostics: {e}")
        print(traceback.format_exc())
        return jsonify({'status': 'error', 'message': str(e)}), 500

@diagnostics_bp.route('/tank-debug', methods=['GET'])
@login_required
def tank_debug():
    """Simple tank state debugging endpoint"""
    try:
        # Create a clean tank state
        tank = TankState('Winter')
        tank.update_from_sensors(GPIOManager)
        
        # Get handler info
        current_mode = mode_controller.get_current_mode()
        handler = mode_controller._current_handler
        
        # Build a simple response
        response = {
            'timestamp': datetime.now().isoformat(),
            'tank': {
                'name': tank.name,
                'state': tank.state,
                'winter_high': tank.winter_high,
                'winter_low': tank.winter_low
            },
            'mode': {
                'current_mode': current_mode,
                'handler_type': type(handler).__name__ if handler else None
            },
            'pumps': {
                'well': {
                    'state': GPIOManager.get_pump_state(WELL_PUMP)
                },
                'distribution': {
                    'state': GPIOManager.get_pump_state(DIST_PUMP)
                }
            }
        }
        
        # Add handler state if in winter mode
        if current_mode == 'WINTER' and handler:
            try:
                pump_started_from_low = getattr(handler, '_pump_started_from_low', None)
                last_state = getattr(handler, '_last_state', None)
                low_state_time = getattr(handler, '_low_state_time', None)
                
                response['handler'] = {
                    'pump_started_from_low': pump_started_from_low,
                    'last_state': last_state,
                    'low_state_time': low_state_time.isoformat() if low_state_time else None
                }
            except Exception as e:
                response['handler_error'] = str(e)
                
        return jsonify(response)
    except Exception as e:
        print(f"Error in tank debug: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'status': 'error', 'message': str(e)}), 500