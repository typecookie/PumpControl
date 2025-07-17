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
from ..services.notification_service import NotificationService, AlertType  # New import

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

            # Initialize notification service
            self.notification_service = NotificationService()  # New line

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
            
            # Initialize distribution pump to ON by default
            GPIOManager.set_pump(DIST_PUMP, True)
            
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
            # [Existing summer tank logic]
            summer_high = GPIOManager.get_sensor_state(SUMMER_HIGH)
            summer_low = GPIOManager.get_sensor_state(SUMMER_LOW)
            summer_empty = GPIOManager.get_sensor_state(SUMMER_EMPTY)

            print(f"Summer tank sensors - High: {summer_high}, Low: {summer_low}, Empty: {summer_empty}")

            previous_summer_state = self.summer_tank.state if hasattr(self, 'summer_tank') else None
            previous_winter_state = self.winter_tank.state if hasattr(self, 'winter_tank') else None

            # Summer Tank Logic [no changes]
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

            # Winter Tank Logic [no changes]
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

            # New: Send notifications for state changes
            if previous_summer_state and self.summer_tank.state != previous_summer_state:
                self.notification_service.send_alert(
                    AlertType.TANK_STATE_CHANGE,
                    f"Summer tank state changed from {previous_summer_state} to {self.summer_tank.state}",
                    {"Tank": "Summer", "Previous": previous_summer_state, "Current": self.summer_tank.state}
                )

            if previous_winter_state and self.winter_tank.state != previous_winter_state:
                self.notification_service.send_alert(
                    AlertType.TANK_STATE_CHANGE,
                    f"Winter tank state changed from {previous_winter_state} to {self.winter_tank.state}",
                    {"Tank": "Winter", "Previous": previous_winter_state, "Current": self.winter_tank.state}
                )

        except Exception as e:
            print(f"Error updating tank states: {e}")
            self.summer_tank.state = "ERROR"
            self.winter_tank.state = "ERROR"
            self.notification_service.send_alert(
                AlertType.SYSTEM_ERROR,
                f"Error updating tank states: {str(e)}",
                {"Error": str(e)}
            )

    def _control_loop(self):
        """Main control loop"""
        pump_running = False
        last_mode = None  # Track mode changes

        while self.running:
            try:
                # Get latest mode from mode controller
                self.current_mode = self.mode_controller.get_current_mode()
                self._update_tank_states()
                print(f"Current mode: {self.current_mode}")

                # Check if mode has changed
                if last_mode != self.current_mode:
                    print(f"Mode changed from {last_mode} to {self.current_mode}")
                    self.notification_service.send_alert(  # New notification
                        AlertType.MODE_CHANGE,
                        f"System mode changed from {last_mode} to {self.current_mode}",
                        {"Previous": last_mode, "Current": self.current_mode}
                    )
                    if self.current_mode == 'CHANGEOVER':
                        # Set distribution pump ON by default when entering CHANGEOVER mode
                        GPIOManager.set_pump(DIST_PUMP, True)
                    last_mode = self.current_mode

                # [Rest of the control logic remains exactly the same]
                if self.current_mode == 'SUMMER':
                    # [Existing summer mode logic]
                    if self.summer_tank.state in ['EMPTY', 'LOW']:
                        pump_running = True
                    elif self.summer_tank.state == 'HIGH':
                        pump_running = False

                    print(f"DEBUG: Summer tank state: {self.summer_tank.state}, Setting well pump to: {pump_running}")
                    GPIOManager.set_pump(WELL_PUMP, pump_running)

                    # Distribution pump control for summer mode
                    if self.summer_tank.state in ['ERROR', 'EMPTY']:
                        dist_pump_state = False
                    else:
                        dist_pump_state = True  # Run in all other states (HIGH, MID, LOW)

                    print(f"DEBUG: Summer tank state: {self.summer_tank.state}, Setting distribution pump to: {dist_pump_state}")
                    GPIOManager.set_pump(DIST_PUMP, dist_pump_state)

                    if pump_running:
                        self.summer_tank.update_stats(True)

                elif self.current_mode == 'WINTER':
                    # [Existing winter mode logic]
                    if self.winter_tank.state in ['LOW']:
                        pump_running = True
                    elif self.winter_tank.state == 'HIGH':
                        pump_running = False

                    print(f"DEBUG: Winter tank state: {self.winter_tank.state}, Setting well pump to: {pump_running}")
                    GPIOManager.set_pump(WELL_PUMP, pump_running)

                    # Distribution pump control for winter mode
                    dist_pump_state = not (self.winter_tank.state == 'ERROR')  # Only turn off on ERROR
                    print(f"DEBUG: Winter tank state: {self.winter_tank.state}, Setting distribution pump to: {dist_pump_state}")
                    GPIOManager.set_pump(DIST_PUMP, dist_pump_state)

                    if pump_running:
                        self.winter_tank.update_stats(True)

                elif self.current_mode == 'CHANGEOVER':
                    pump_running = self.manual_pump_running
                    GPIOManager.set_pump(WELL_PUMP, pump_running)
                    print(f"Changeover mode - Manual control: Well Pump {'ON' if pump_running else 'OFF'}, Dist Pump {GPIOManager.get_pump_state(DIST_PUMP)}")

                # Safety check for errors
                if (self.summer_tank.state == 'ERROR' or self.winter_tank.state == 'ERROR'):
                    pump_running = False
                    GPIOManager.set_pump(WELL_PUMP, False)
                    GPIOManager.set_pump(DIST_PUMP, False)  # Also stop dist pump on error
                    print("Tank error state detected - All pumps OFF for safety")
                    self.notification_service.send_alert(  # New notification
                        AlertType.TANK_ERROR,
                        "Tank error detected - All pumps stopped for safety",
                        {
                            "Summer Tank": self.summer_tank.state,
                            "Winter Tank": self.winter_tank.state,
                            "Time": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                    )

                actual_pump_state = GPIOManager.get_pump_state(WELL_PUMP)
                actual_dist_state = GPIOManager.get_pump_state(DIST_PUMP)
                print(f"DEBUG: Final pump state verification: Well pump: {actual_pump_state}, Dist pump: {actual_dist_state}")

                time.sleep(1)

            except Exception as e:
                error_msg = f"Error in control loop: {e}"
                print(error_msg)
                self.notification_service.send_alert(  # New notification
                    AlertType.SYSTEM_ERROR,
                    error_msg,
                    {"Time": time.strftime("%Y-%m-%d %H:%M:%S")}
                )
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

    def set_distribution_pump(self, state):
        """Control distribution pump state
        
        Args:
            state (bool): True to turn on, False to turn off
            
        Returns:
            dict: Status response
        """
        try:
            GPIOManager.set_pump(DIST_PUMP, state)
            actual_state = GPIOManager.get_pump_state(DIST_PUMP)
            
            if actual_state == state:
                return {
                    'status': 'success',
                    'message': f'Distribution pump {"started" if state else "stopped"}',
                    'pump_running': actual_state
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Failed to verify distribution pump state',
                    'pump_running': actual_state
                }
        except Exception as e:
            print(f"Error controlling distribution pump: {e}")
            return {
                'status': 'error',
                'message': f'Error controlling distribution pump: {str(e)}',
                'pump_running': GPIOManager.get_pump_state(DIST_PUMP)
            }