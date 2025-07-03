from flask import Flask, render_template, jsonify, request
from datetime import datetime
import RPi.GPIO as GPIO
import threading
import atexit
import time
import json
import os

# First, define the GPIO Pin Definitions
WELL_PUMP = 17
DIST_PUMP = 18
SUMMER_HIGH = 22
SUMMER_LOW = 23
SUMMER_EMPTY = 24
WINTER_HIGH = 26
WINTER_LOW = 27

# System Modes
MODES = {
    'SUMMER': 'Summer Mode',
    'WINTER': 'Winter Mode',
    'CHANGEOVER': 'Changeover Mode'
}

# Configuration settings
CONFIG_FILE = 'pump_config.json'
DEFAULT_CONFIG = {
    'current_mode': 'SUMMER'
}

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    except Exception as e:
        print(f"Error saving config: {e}")

def load_config():
    """Load configuration from file"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
    return DEFAULT_CONFIG.copy()

# Global Variables
config = load_config()
current_mode = config.get('current_mode', 'SUMMER')
gpio_initialized = False
pump_thread = None
manual_pump_running = False

class TankState:
    def __init__(self, name):
        self.name = name
        self.state = 'unknown'
        self.stats = {
            'today_runtime': 0,
            'today_gallons': 0,
            'week_runtime': 0,
            'week_gallons': 0,
            'month_runtime': 0,
            'month_gallons': 0
        }
    
    def format_runtime(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# Create tank instances
summer_tank = TankState('Summer')
winter_tank = TankState('Winter')

def initialize_gpio():
    """Initialize GPIO if not already initialized"""
    global gpio_initialized
    if not gpio_initialized:
        try:
            GPIO.setwarnings(False)
            GPIO.cleanup()
            GPIO.setmode(GPIO.BCM)
            
            # Setup outputs
            GPIO.setup(WELL_PUMP, GPIO.OUT)
            GPIO.setup(DIST_PUMP, GPIO.OUT)
            
            # Setup inputs with pull-up resistors
            GPIO.setup(SUMMER_HIGH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(SUMMER_LOW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(SUMMER_EMPTY, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(WINTER_HIGH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(WINTER_LOW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Initialize outputs to OFF
            GPIO.output(WELL_PUMP, GPIO.LOW)
            GPIO.output(DIST_PUMP, GPIO.LOW)
            
            gpio_initialized = True
            print("GPIO initialized successfully")
        except Exception as e:
            print(f"Error initializing GPIO: {e}")
            gpio_initialized = False


def update_tank_states():
    """Update tank states based on sensor readings"""
    try:
        # Summer Tank State Logic
        summer_high = not GPIO.input(SUMMER_HIGH)  # Inverted value (true when closed)
        summer_low = not GPIO.input(SUMMER_LOW)  # Inverted value (true when closed)
        summer_empty = not GPIO.input(SUMMER_EMPTY)  # Inverted value (true when closed)

        # Summer Tank Logic:
        # HIGH: all sensors closed (empty, low, and high all true)
        # MID: empty and low closed, high open (empty and low true, high false)
        # LOW: only empty closed (empty true, low and high false)
        # EMPTY: all sensors open (all false)

        if summer_empty and summer_low and summer_high:
            summer_tank.state = "HIGH"
        elif summer_empty and summer_low and not summer_high:
            summer_tank.state = "MID"
        elif summer_empty and not summer_low and not summer_high:
            summer_tank.state = "LOW"
        elif not summer_empty and not summer_low and not summer_high:
            summer_tank.state = "EMPTY"
        else:
            summer_tank.state = "ERROR"  # For any unexpected combination

        # Winter Tank State Logic
        winter_high = not GPIO.input(WINTER_HIGH)  # Inverted value (true when closed)
        winter_low = not GPIO.input(WINTER_LOW)  # Inverted value (true when closed)

        # Winter Tank Logic:
        # HIGH: both sensors closed (both true)
        # MID: high open, low closed (high false, low true)
        # LOW: both open (both false)

        if winter_high and winter_low:
            winter_tank.state = "HIGH"
        elif not winter_high and winter_low:
            winter_tank.state = "MID"
        elif not winter_high and not winter_low:
            winter_tank.state = "LOW"
        else:
            winter_tank.state = "ERROR"  # For any unexpected combination

    except Exception as e:
        print(f"Error updating tank states: {e}")
        summer_tank.state = "ERROR"
        winter_tank.state = "ERROR"

def control_pumps():
    """Main pump control logic"""
    print("Control pump thread starting...")
    pump_running = False  # Track pump state to implement hysteresis
    
    while True:
        try:
            update_tank_states()  # Update tank states
            
            # Add mode change logging
            print(f"Current mode: {current_mode}")  # Add this line
            
            if current_mode == 'SUMMER':
                if summer_tank.state in ['EMPTY', 'LOW']:
                    pump_running = True
                elif summer_tank.state == 'HIGH':
                    pump_running = False
                
                GPIO.output(WELL_PUMP, GPIO.HIGH if pump_running else GPIO.LOW)
                print(f"Summer mode: {summer_tank.state} - Well pump {'ON' if pump_running else 'OFF'}")
                
            elif current_mode == 'WINTER':
                if winter_tank.state == 'LOW':
                    pump_running = True
                elif winter_tank.state == 'HIGH':
                    pump_running = False
                
                GPIO.output(WELL_PUMP, GPIO.HIGH if pump_running else GPIO.LOW)
                print(f"Winter mode: {winter_tank.state} - Well pump {'ON' if pump_running else 'OFF'}")
                
            elif current_mode == 'CHANGEOVER':
                # In changeover mode, pump control is manual only
                print(f"Changeover mode - Manual control only")
                print(f"Summer tank: {summer_tank.state}, Winter tank: {winter_tank.state}")
                if not manual_pump_running:
                    GPIO.output(WELL_PUMP, GPIO.LOW)
                # Note: Well pump in changeover mode is controlled by manual_pump endpoint
                
            # Safety check for errors in any mode
            if (summer_tank.state == 'ERROR' or winter_tank.state == 'ERROR'):
                pump_running = False
                GPIO.output(WELL_PUMP, GPIO.LOW)
                print(f"Tank error state detected - Well pump OFF for safety")
            
            time.sleep(1)  # Check every second
            
        except Exception as e:
            print(f"Error in control_pumps: {e}")
            pump_running = False
            GPIO.output(WELL_PUMP, GPIO.LOW)
            GPIO.output(DIST_PUMP, GPIO.LOW)
            time.sleep(1)

def create_app():
    app = Flask(__name__)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # Initialize the pump thread during app creation
    global pump_thread, current_mode
    config = load_config()
    current_mode = config.get('current_mode', 'SUMMER')
    
    if pump_thread is None or not pump_thread.is_alive():
        initialize_gpio()
        pump_thread = threading.Thread(target=control_pumps, daemon=True)
        pump_thread.start()
        print("Control pump thread starting...")
    
    # Register cleanup handler
    atexit.register(lambda: GPIO.cleanup())
    
    # Register all routes
    @app.route('/')
    def index():
        initialize_gpio()  # Ensure GPIO is initialized
        try:
            active_tank = summer_tank if current_mode in ['SUMMER', 'CHANGEOVER'] else winter_tank
            initial_state = {
                'current_mode': current_mode,
                'available_modes': MODES,
                'summer_tank_state': summer_tank.state,
                'winter_tank_state': winter_tank.state,
                'well_pump_status': 'ON' if GPIO.input(WELL_PUMP) else 'OFF',
                'dist_pump_status': 'ON' if GPIO.input(DIST_PUMP) else 'OFF',
                'active_tank': active_tank.name
            }
            return render_template('index.html', **initial_state)
        except Exception as e:
            print(f"Error in index route: {e}")
            return render_template('index.html', 
                                error=str(e),
                                current_mode='unknown',
                                available_modes=MODES,
                                summer_tank_state='unknown',
                                winter_tank_state='unknown',
                                well_pump_status='unknown',
                                dist_pump_status='unknown',
                                active_tank='none')

    @app.route('/api/state')
    def get_state():
        initialize_gpio()  # Ensure GPIO is initialized
        try:
            active_tank = summer_tank if current_mode in ['SUMMER', 'CHANGEOVER'] else winter_tank
            state = {
                'current_mode': current_mode,
                'summer_tank': {
                    'state': summer_tank.state,
                    'stats': {
                        'today_runtime': summer_tank.format_runtime(summer_tank.stats['today_runtime']),
                        'today_gallons': round(summer_tank.stats['today_gallons'], 1),
                        'week_runtime': summer_tank.format_runtime(summer_tank.stats['week_runtime']),
                        'week_gallons': round(summer_tank.stats['week_gallons'], 1),
                        'month_runtime': summer_tank.format_runtime(summer_tank.stats['month_runtime']),
                        'month_gallons': round(summer_tank.stats['month_gallons'], 1)
                    }
                },
                'winter_tank': {
                    'state': winter_tank.state,
                    'stats': {
                        'today_runtime': winter_tank.format_runtime(winter_tank.stats['today_runtime']),
                        'today_gallons': round(winter_tank.stats['today_gallons'], 1),
                        'week_runtime': winter_tank.format_runtime(winter_tank.stats['week_runtime']),
                        'week_gallons': round(winter_tank.stats['week_gallons'], 1),
                        'month_runtime': winter_tank.format_runtime(winter_tank.stats['month_runtime']),
                        'month_gallons': round(winter_tank.stats['month_gallons'], 1)
                    }
                },
                'well_pump_status': 'ON' if GPIO.input(WELL_PUMP) else 'OFF',
                'dist_pump_status': 'ON' if GPIO.input(DIST_PUMP) else 'OFF',
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            return jsonify(state)
        except Exception as e:
            print(f"Error in get_state: {e}")
            return jsonify({
                'error': str(e),
                'current_mode': current_mode,
                'summer_tank': {'state': 'unknown', 'stats': {}},
                'winter_tank': {'state': 'unknown', 'stats': {}},
                'well_pump_status': 'unknown',
                'dist_pump_status': 'unknown',
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    @app.route('/api/mode', methods=['POST'])
    def change_mode():
        global current_mode, mode_change_requested
        try:
            new_mode = request.json.get('mode')
            confirm = request.json.get('confirm', False)
            
            print(f"Mode change request received - New mode: {new_mode}, Confirm: {confirm}")
            
            if new_mode not in MODES:
                print(f"Invalid mode requested: {new_mode}")
                return jsonify({'error': 'Invalid mode'}), 400
            
            if not confirm:
                mode_change_requested = new_mode
                print(f"Awaiting confirmation for mode change to: {MODES[new_mode]}")
                return jsonify({
                    'status': 'confirmation_required',
                    'message': f'Confirm changing mode to {MODES[new_mode]}?'
                })
            
            current_mode = new_mode
            mode_change_requested = None
            
            # Save the new mode to config file
            config['current_mode'] = current_mode
            save_config(config)
            
            GPIO.output(WELL_PUMP, GPIO.LOW)
            GPIO.output(DIST_PUMP, GPIO.LOW)
            
            print(f"Mode successfully changed to: {MODES[new_mode]}")
            
            return jsonify({
                'status': 'success',
                'message': f'Mode changed to {MODES[new_mode]}',
                'current_mode': new_mode
            })
        except Exception as e:
            print(f"Error in change_mode: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/gpio_states')
    def get_gpio_states():
        try:
            gpio_states = {
                'summer_tank': {
                    'high': {
                        'pin': SUMMER_HIGH,
                        'raw_value': GPIO.input(SUMMER_HIGH),
                        'inverted_value': not GPIO.input(SUMMER_HIGH)
                    },
                    'low': {
                        'pin': SUMMER_LOW,
                        'raw_value': GPIO.input(SUMMER_LOW),
                        'inverted_value': not GPIO.input(SUMMER_LOW)
                    },
                    'empty': {
                        'pin': SUMMER_EMPTY,
                        'raw_value': GPIO.input(SUMMER_EMPTY),
                        'inverted_value': not GPIO.input(SUMMER_EMPTY)
                    }
                },
                'winter_tank': {
                    'high': {
                        'pin': WINTER_HIGH,
                        'raw_value': GPIO.input(WINTER_HIGH),
                        'inverted_value': not GPIO.input(WINTER_HIGH)
                    },
                    'low': {
                        'pin': WINTER_LOW,
                        'raw_value': GPIO.input(WINTER_LOW),
                        'inverted_value': not GPIO.input(WINTER_LOW)
                    }
                },
                'pumps': {
                    'well': {
                        'pin': WELL_PUMP,
                        'value': GPIO.input(WELL_PUMP)
                    },
                    'distribution': {
                        'pin': DIST_PUMP,
                        'value': GPIO.input(DIST_PUMP)
                    }
                }
            }
            return jsonify(gpio_states)
        except Exception as e:
            print(f"Error getting GPIO states: {e}")
            return jsonify({'error': str(e)})

    @app.route('/api/thread_status')
    def get_thread_status():
        global pump_thread
        try:
            return jsonify({
                'thread_running': pump_thread.is_alive(),
                'last_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as e:
            return jsonify({
                'thread_running': False,
                'error': str(e)
            })

    @app.route('/api/manual_pump', methods=['POST'])
    def manual_pump():
        global manual_pump_running
        try:
            manual_pump_running = request.json.get('running', False)
            if current_mode == 'CHANGEOVER':
                GPIO.output(WELL_PUMP, GPIO.HIGH if manual_pump_running else GPIO.LOW)
                return jsonify({
                    'status': 'success',
                    'pump_running': manual_pump_running
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Manual pump control only available in CHANGEOVER mode'
                }), 400
        except Exception as e:
            print(f"Error in manual_pump: {e}")
            return jsonify({'error': str(e)}), 500

    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Force disable Flask's development features
    import os
    os.environ['FLASK_ENV'] = 'production'
    os.environ['WERKZEUG_RUN_MAIN'] = 'true'
    
    print(f"Starting server on 0.0.0.0:5000... (Current mode: {current_mode})")
    # Explicitly bind to all interfaces
    from werkzeug.serving import WSGIServer
    http_server = WSGIServer(('0.0.0.0', 5000), app)
    try:
        print("Server is ready to accept connections")
        http_server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        # Save final state before shutdown
        save_config(config)