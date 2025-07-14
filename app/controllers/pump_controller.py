import threading
import time

# Local imports
from .base_controller import Controller
from .mode_controller import ModeController
from ..utils.gpio_utils import GPIOManager
from ..utils.config_utils import (
    ConfigManager,
    WELL_PUMP,
    DIST_PUMP,
    SUMMER_HIGH,
    SUMMER_LOW,
    SUMMER_EMPTY,
    WINTER_HIGH,
    WINTER_LOW
)
from ..models.tank_state import TankState
from .interfaces import IPumpController


class PumpController(IPumpController):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PumpController, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        try:
            self.config = ConfigManager.load_config()
            # Use the singleton mode_controller instance
            from . import mode_controller as mc
            self.mode_controller = mc
            self.current_mode = self.mode_controller.get_current_mode()

            # Initialize GPIO first
            if not GPIOManager.initialize():
                raise RuntimeError("Failed to initialize GPIO")
            
            # Initialize tanks after GPIO is ready
            self.summer_tank = TankState('Summer')
            self.winter_tank = TankState('Winter')
            self._update_tank_states()  # Initial state update
            
            self.manual_pump_running = False
            self.pump_thread = None
            self.running = False
            self._last_state = None
            self._state_timestamp = 0
            
            print(f"PumpController initialized with mode: {self.current_mode}")
            self._initialized = True
            
        except Exception as e:
            print(f"Error initializing PumpController: {e}")
            raise

    def start(self):
        """Start the pump control thread"""
        if not self.running:
            print("Attempting to initialize GPIO...")
            try:
                if GPIOManager.initialize():
                    print("GPIO initialized successfully")
                    self.running = True
                    self.pump_thread = threading.Thread(target=self._control_loop, daemon=True)
                    self.pump_thread.start()
                    print("Pump controller thread started")
                    return True
                else:
                    print("Failed to initialize GPIO")
                    return False
            except Exception as e:
                print(f"Error during GPIO initialization: {e}")
                return False

    def stop(self):
        """Stop the pump control thread"""
        self.running = False
        if self.pump_thread:
            self.pump_thread.join(timeout=2.0)
        GPIOManager.cleanup()
        print("Pump controller stopped")

    def _update_tank_states(self):
        """Update tank states based on sensor readings"""
        try:
            # Summer Tank State Logic
            summer_high = GPIOManager.get_sensor_state(SUMMER_HIGH)
            summer_low = GPIOManager.get_sensor_state(SUMMER_LOW)
            summer_empty = GPIOManager.get_sensor_state(SUMMER_EMPTY)

            print(f"Summer tank sensors - High: {summer_high}, Low: {summer_low}, Empty: {summer_empty}")

            # Summer Tank Logic
            if summer_empty and summer_low and summer_high:
                self.summer_tank.state = "HIGH"
            elif summer_empty and summer_low and not summer_high:
                self.summer_tank.state = "MID"
            elif summer_empty and not summer_low and not summer_high:
                self.summer_tank.state = "LOW"
            elif not summer_empty and not summer_low and not summer_high:
                self.summer_tank.state = "EMPTY"
            else:
                self.summer_tank.state = "ERROR"

            print(f"Summer tank state set to: {self.summer_tank.state}")

            # Winter Tank Logic
            winter_high = GPIOManager.get_sensor_state(WINTER_HIGH)
            winter_low = GPIOManager.get_sensor_state(WINTER_LOW)

            print(f"Winter tank sensors - High: {winter_high}, Low: {winter_low}")

            if winter_high and winter_low:
                self.winter_tank.state = "HIGH"
            elif not winter_high and winter_low:
                self.winter_tank.state = "MID"
            elif not winter_high and not winter_low:
                self.winter_tank.state = "LOW"
            else:
                self.winter_tank.state = "ERROR"

            print(f"Winter tank state set to: {self.winter_tank.state}")

        except Exception as e:
            print(f"Error updating tank states: {e}")
            self.summer_tank.state = "ERROR"
            self.winter_tank.state = "ERROR"

    def _control_loop(self):
        """Main control loop"""
        pump_running = False

        while self.running:
            try:
                # Get latest mode from mode controller
                self.current_mode = self.mode_controller.get_current_mode()
                self._update_tank_states()
                print(f"Current mode: {self.current_mode}")

                # Handle pump control based on mode
                if self.current_mode == 'SUMMER':
                    if self.summer_tank.state in ['EMPTY', 'LOW']:
                        pump_running = True
                    elif self.summer_tank.state == 'HIGH':
                        pump_running = False

                    print(f"DEBUG: Summer tank state: {self.summer_tank.state}, Setting pump to: {pump_running}")
                    GPIOManager.set_pump(WELL_PUMP, pump_running)

                    if pump_running:
                        self.summer_tank.update_stats(True)

                elif self.current_mode == 'WINTER':
                    if self.winter_tank.state in ['LOW']:
                        pump_running = True
                    elif self.winter_tank.state == 'HIGH':
                        pump_running = False

                    print(f"DEBUG: Winter tank state: {self.winter_tank.state}, Setting pump to: {pump_running}")
                    GPIOManager.set_pump(WELL_PUMP, pump_running)

                    if pump_running:
                        self.winter_tank.update_stats(True)

                elif self.current_mode == 'CHANGEOVER':
                    pump_running = self.manual_pump_running
                    GPIOManager.set_pump(WELL_PUMP, pump_running)
                    print(f"Changeover mode - Manual control: Pump {'ON' if pump_running else 'OFF'}")

                # Safety check for errors
                if (self.summer_tank.state == 'ERROR' or self.winter_tank.state == 'ERROR'):
                    pump_running = False
                    GPIOManager.set_pump(WELL_PUMP, False)
                    print("Tank error state detected - Well pump OFF for safety")

                actual_pump_state = GPIOManager.get_pump_state(WELL_PUMP)
                print(f"DEBUG: Final pump state verification: {actual_pump_state}")

                time.sleep(1)

            except Exception as e:
                print(f"Error in control loop: {e}")
                pump_running = False
                GPIOManager.set_pump(WELL_PUMP, False)
                GPIOManager.set_pump(DIST_PUMP, False)
                time.sleep(1)

    def get_system_state(self):
        """Get current system state with caching"""
        current_time = time.time()

        if self._last_state is None or (current_time - self._state_timestamp) >= 0.5:
            try:
                if not self.is_running:
                    self.start()

                # Get latest mode from mode controller
                self.current_mode = self.mode_controller.get_current_mode()
                self._update_tank_states()

                state = {
                    'current_mode': self.current_mode,
                    'summer_tank': {
                        'state': self.summer_tank.state,
                        'stats': self.summer_tank.get_formatted_stats()
                    },
                    'winter_tank': {
                        'state': self.winter_tank.state,
                        'stats': self.winter_tank.get_formatted_stats()
                    },
                    'well_pump_status': 'ON' if GPIOManager.get_pump_state(WELL_PUMP) else 'OFF',
                    'dist_pump_status': 'ON' if GPIOManager.get_pump_state(DIST_PUMP) else 'OFF',
                    'thread_running': self.pump_thread.is_alive() if self.pump_thread else False
                }

                self._last_state = state
                self._state_timestamp = current_time

            except Exception as e:
                print(f"Error getting system state: {e}")
                if self._last_state is None:
                    raise

        return self._last_state

    def set_manual_pump(self, running):
        """Control manual pump in changeover mode"""
        if self.current_mode != 'CHANGEOVER':
            return {'status': 'error', 'message': 'Manual pump control only available in CHANGEOVER mode'}, 400

        try:
            self.manual_pump_running = running
            GPIOManager.set_pump(WELL_PUMP, running)
            return {'status': 'success', 'pump_running': self.manual_pump_running}
        except Exception as e:
            print(f"Error in manual pump control: {e}")
            return {'error': str(e)}, 500

    @property
    def is_running(self):
        """Check if pump controller is running"""
        return self.running and (self.pump_thread and self.pump_thread.is_alive())