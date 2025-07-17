from RPi import GPIO

from app.controllers import Controller
from app.utils.gpio_utils import GPIOManager
from app.utils.config_utils import (
    SUMMER_HIGH, SUMMER_LOW, SUMMER_EMPTY,
    WINTER_HIGH, WINTER_LOW,
    WELL_PUMP, DIST_PUMP
)

class GPIOController(Controller):
    def _init(self):
        """Initialize GPIO controller"""
        self.gpio_manager = GPIOManager()
        GPIOManager.initialize()
    
    def cleanup(self):
        """Clean up GPIO resources"""
        self.gpio_manager.cleanup()

    def get_tank_states(self):
        """Get all tank sensor states"""
        return {
            'summer_tank': {
                'high': self.gpio_manager.get_sensor_state(SUMMER_HIGH),
                'low': self.gpio_manager.get_sensor_state(SUMMER_LOW),
                'empty': self.gpio_manager.get_sensor_state(SUMMER_EMPTY)
            },
            'winter_tank': {
                'high': self.gpio_manager.get_sensor_state(WINTER_HIGH),
                'low': self.gpio_manager.get_sensor_state(WINTER_LOW)
            }
        }

    def get_pump_states(self):
        """Get all pump states"""
        return {
            'well_pump': self.gpio_manager.get_pump_state(WELL_PUMP),
            'dist_pump': self.gpio_manager.get_pump_state(DIST_PUMP)
        }

    def set_pump_state(self, pump_name, state):
        """Set pump state"""
        pin = WELL_PUMP if pump_name == 'well' else DIST_PUMP
        self.gpio_manager.set_pump(pin, state)

    def get_raw_gpio_states(self):
        """Get raw GPIO states for debugging"""
        return {
            'summer_tank': {
                'high': {
                    'pin': SUMMER_HIGH,
                    'raw_value': self.gpio_manager.get_raw_sensor_state(SUMMER_HIGH),
                    'inverted_value': self.gpio_manager.get_sensor_state(SUMMER_HIGH)
                },
                'low': {
                    'pin': SUMMER_LOW,
                    'raw_value': self.gpio_manager.get_raw_sensor_state(SUMMER_LOW),
                    'inverted_value': self.gpio_manager.get_sensor_state(SUMMER_LOW)
                },
                'empty': {
                    'pin': SUMMER_EMPTY,
                    'raw_value': self.gpio_manager.get_raw_sensor_state(SUMMER_EMPTY),
                    'inverted_value': self.gpio_manager.get_sensor_state(SUMMER_EMPTY)
                }
            },
            'winter_tank': {
                'high': {
                    'pin': WINTER_HIGH,
                    'raw_value': self.gpio_manager.get_raw_sensor_state(WINTER_HIGH),
                    'inverted_value': self.gpio_manager.get_sensor_state(WINTER_HIGH)
                },
                'low': {
                    'pin': WINTER_LOW,
                    'raw_value': self.gpio_manager.get_raw_sensor_state(WINTER_LOW),
                    'inverted_value': self.gpio_manager.get_sensor_state(WINTER_LOW)
                }
            },
            'pumps': {
                'well': {
                    'pin': WELL_PUMP,
                    'value': self.gpio_manager.get_pump_state(WELL_PUMP)
                },
                'distribution': {
                    'pin': DIST_PUMP,
                    'value': self.gpio_manager.get_pump_state(DIST_PUMP)
                }
            }
        }
class GPIOManager:
    _initialized = False
    
    @staticmethod
    def initialize():
        """Initialize GPIO"""
        try:
            if GPIOManager._initialized:
                return True
                
            print("Initializing GPIO...")
            
            # Check if GPIO is already set up
            current_mode = GPIO.getmode()
            if current_mode is not None:
                print(f"GPIO already initialized in mode: {current_mode}")
            else:
                print("Setting GPIO mode to BCM")
                GPIO.setmode(GPIO.BCM)
                
            # Clean up any existing configurations
            GPIO.cleanup()
            
            # Setup all pins
            pins_config = [
                (WELL_PUMP, GPIO.OUT),
                (DIST_PUMP, GPIO.OUT),
                (SUMMER_HIGH, GPIO.IN, GPIO.PUD_UP),
                (SUMMER_LOW, GPIO.IN, GPIO.PUD_UP),
                (SUMMER_EMPTY, GPIO.IN, GPIO.PUD_UP),
                (WINTER_HIGH, GPIO.IN, GPIO.PUD_UP),
                (WINTER_LOW, GPIO.IN, GPIO.PUD_UP)
            ]
            
            for pin_config in pins_config:
                try:
                    if len(pin_config) == 2:
                        pin, mode = pin_config
                        GPIO.setup(pin, mode)
                        print(f"Set up pin {pin} as {'OUTPUT' if mode == GPIO.OUT else 'INPUT'}")
                    else:
                        pin, mode, pull_up_down = pin_config
                        GPIO.setup(pin, mode, pull_up_down=pull_up_down)
                        print(f"Set up pin {pin} as INPUT with pull-up")
                except Exception as e:
                    print(f"Error setting up pin {pin}: {e}")
                    raise
            
            # Initialize pump states to OFF
            GPIO.output(WELL_PUMP, GPIO.LOW)
            GPIO.output(DIST_PUMP, GPIO.LOW)
            
            GPIOManager._initialized = True
            print("GPIO initialization complete")
            return True
            
        except Exception as e:
            print(f"GPIO initialization failed: {e}")
            GPIOManager._initialized = False
            return False