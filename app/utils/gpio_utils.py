# app/utils/gpio_utils.py
import RPi.GPIO as GPIO
from app.utils.config_utils import WELL_PUMP, DIST_PUMP, SUMMER_HIGH, SUMMER_LOW, SUMMER_EMPTY, WINTER_HIGH, WINTER_LOW

class GPIOManager:
    _initialized = False

    @classmethod
    def initialize(cls):
        """Initialize GPIO if not already initialized"""
        if not cls._initialized:
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
                
                cls._initialized = True
                print("GPIO initialized successfully")
                return True
            except Exception as e:
                print(f"Error initializing GPIO: {e}")
                cls._initialized = False
                return False
        return True

    @classmethod
    def cleanup(cls):
        """Clean up GPIO configuration"""
        if cls._initialized:
            GPIO.cleanup()
            cls._initialized = False

    @staticmethod
    def get_raw_sensor_state(pin):
        """Get raw GPIO input state"""
        return GPIO.input(pin)

    @staticmethod
    def get_sensor_state(pin):
        """Get inverted sensor state (True when closed)"""
        return not GPIO.input(pin)

    @staticmethod
    def get_pump_state(pin):
        """Get pump state"""
        return GPIO.input(pin)

    @staticmethod
    def set_pump(pin, state):
        """Set pump state"""
        gpio_state = GPIO.HIGH if bool(state) else GPIO.LOW
        GPIO.output(pin, gpio_state)
        # Verify the state was set correctly
        actual_state = GPIO.input(pin)
        return actual_state == gpio_state