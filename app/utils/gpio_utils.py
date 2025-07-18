import os
import json
from RPi import GPIO
from app.utils.config_utils import (
    SUMMER_HIGH, SUMMER_LOW, SUMMER_EMPTY,
    WINTER_HIGH, WINTER_LOW,
    WELL_PUMP, DIST_PUMP
)

class GPIOManager:
    _initialized = False
    _reverse_well_pump = False
    _config_file = os.path.join(os.path.expanduser('~'), '.pump_control', 'gpio_config.json')

    @classmethod
    def _save_config(cls):
        """Save GPIO configuration to file"""
        try:
            config = {
                'reverse_well_pump': cls._reverse_well_pump
            }
            os.makedirs(os.path.dirname(cls._config_file), exist_ok=True)
            with open(cls._config_file, 'w') as f:
                json.dump(config, f, indent=4)
            print("GPIO configuration saved successfully")
        except Exception as e:
            print(f"Error saving GPIO configuration: {e}")

    @classmethod
    def _load_config(cls):
        """Load GPIO configuration from file"""
        try:
            if os.path.exists(cls._config_file):
                with open(cls._config_file, 'r') as f:
                    config = json.load(f)
                cls._reverse_well_pump = config.get('reverse_well_pump', False)
                print(f"GPIO configuration loaded - Reverse mode: {cls._reverse_well_pump}")
            else:
                print("No GPIO configuration found, using defaults")
        except Exception as e:
            print(f"Error loading GPIO configuration: {e}")

    @classmethod
    def get_well_pump_reverse_state(cls):
        """Get current reverse mode state"""
        return cls._reverse_well_pump

    @classmethod
    def set_well_pump_reverse(cls, enabled):
        """Enable or disable well pump reverse mode"""
        cls._reverse_well_pump = enabled
        cls._save_config()  # Save the new state
        print(f"Well pump reverse mode {'enabled' if enabled else 'disabled'}")
        return {"status": "success", "reverse_mode": enabled}

    @classmethod
    def get_pump_state(cls, pin):
        """Get pump state, accounting for reverse mode
        Returns the LOGICAL state (what the user expects to see)
        """
        try:
            physical_state = bool(GPIO.input(pin))
            logical_state = physical_state
            if pin == WELL_PUMP and cls._reverse_well_pump:
                logical_state = not physical_state
            print(f"Pump state - Pin: {pin}, Physical: {physical_state}, Logical: {logical_state}, Reverse: {cls._reverse_well_pump}")
            return logical_state
        except Exception as e:
            print(f"Error getting pump state: {e}")
            return False

    @classmethod
    def set_pump(cls, pin, state):
        """Set pump state with reverse mode support
        state: The LOGICAL state (what the user wants)
        """
        try:
            desired_logical_state = bool(state)
            physical_state = desired_logical_state
            if pin == WELL_PUMP and cls._reverse_well_pump:
                physical_state = not desired_logical_state
            
            gpio_state = GPIO.HIGH if physical_state else GPIO.LOW
            GPIO.output(pin, gpio_state)
            
            actual_physical_state = bool(GPIO.input(pin))
            success = actual_physical_state == physical_state
            
            print(f"Setting pump - Pin: {pin}, "
                  f"Desired logical: {desired_logical_state}, "
                  f"Physical: {physical_state}, "
                  f"Actual: {actual_physical_state}, "
                  f"Reverse: {cls._reverse_well_pump}, "
                  f"Success: {success}")
            
            return success
        except Exception as e:
            print(f"Error setting pump state: {e}")
            return False

    @staticmethod
    def get_raw_sensor_state(pin):
        """Get raw GPIO input state"""
        return GPIO.input(pin)

    @staticmethod
    def get_sensor_state(pin):
        """Get inverted sensor state (True when closed)"""
        return not GPIO.input(pin)

    @classmethod
    def cleanup(cls):
        """Clean up GPIO configuration"""
        if cls._initialized:
            GPIO.cleanup()
            cls._initialized = False

    @classmethod
    def initialize(cls):
        """Initialize GPIO if not already initialized"""
        if not cls._initialized:
            try:
                print("Initializing GPIO...")
                GPIO.setwarnings(False)
                GPIO.cleanup()
                GPIO.setmode(GPIO.BCM)
                
                # Load saved configuration first
                cls._load_config()
                
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
                print(f"GPIO initialized successfully - Reverse mode: {cls._reverse_well_pump}")
                return True
            except Exception as e:
                print(f"Error initializing GPIO: {e}")
                cls._initialized = False
                return False
        return True