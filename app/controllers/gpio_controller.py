

from app.controllers import Controller
from app.utils.gpio_utils import GPIOManager
from app.config import (
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
@classmethod
def initialize(cls):
    """Initialize GPIO settings"""
    try:
        print("Setting up GPIO...")
        GPIO.setwarnings(False)
        GPIO.cleanup()
        GPIO.setmode(GPIO.BCM)

        # Setup outputs
        print("Setting up pump pins...")
        GPIO.setup(WELL_PUMP, GPIO.OUT)
        GPIO.setup(DIST_PUMP, GPIO.OUT)

        # Setup inputs with pull-up resistors
        print("Setting up sensor pins...")
        GPIO.setup(SUMMER_HIGH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(SUMMER_LOW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(SUMMER_EMPTY, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(WINTER_HIGH, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(WINTER_LOW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Initialize outputs to OFF
        GPIO.output(WELL_PUMP, GPIO.LOW)
        GPIO.output(DIST_PUMP, GPIO.LOW)

        print("GPIO initialization complete")
        return True

    except Exception as e:
        print(f"Error in GPIO initialization: {e}")
        return False