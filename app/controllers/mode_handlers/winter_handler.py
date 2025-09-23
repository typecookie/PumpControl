from datetime import datetime
from app.utils.config_utils import ConfigManager
from app.utils.notification_config import AlertType
from .base_handler import BaseModeHandler
from app.models.tank_state import TankState
from app.utils.gpio_utils import GPIOManager


class WinterModeHandler(BaseModeHandler):
    def __init__(self, pump_controller, notification_service):
        super().__init__(pump_controller, notification_service)
        self._last_state = None
        self._pump_started_from_low = False
        self._low_state_time = None
        print("WinterModeHandler initialized")

    def on_mode_enter(self):
        """Initialize state when entering winter mode"""
        self._pump_started_from_low = False
        self._last_state = None
        self._low_state_time = None
        # Start with pumps off
        self.pump_controller.set_well_pump(False)
        self.pump_controller.set_distribution_pump(True)
        print("Entered winter mode")

    def on_mode_exit(self):
        """Cleanup when exiting winter mode"""
        self.pump_controller.set_well_pump(False)
        self.pump_controller.set_distribution_pump(False)
        print("Exited winter mode")

    def handle(self, tank_state):
        """Handle winter mode pump control logic"""
        try:
            print("\n=== Winter Handler Called ===")
            print(f"Tank state object: {tank_state}")
            print(f"Tank name: {tank_state.name}")
            print(f"Tank state value: {tank_state.state}")
            print(f"Raw sensor values - High: {tank_state.winter_high}, Low: {tank_state.winter_low}")
            print(f"Last state: {self._last_state}")
            print(f"Pump started from low: {self._pump_started_from_low}")
        
            # Ensure we're working with a valid tank state
            current_state = tank_state.state
            if current_state == 'unknown':
                print("Warning: Unknown tank state, skipping control logic")
                # Force an update of the sensors to try to get a valid state
                tank_state.update_from_sensors(GPIOManager)
                current_state = tank_state.state
                if current_state == 'unknown':
                    print("Still unknown after sensor update, aborting control logic")
                    return
            
            # Keep track of last state for state change detection
            if self._last_state != current_state:
                print(f"State CHANGED from {self._last_state} to {current_state}")
                self._last_state = current_state
            else:
                print(f"State unchanged: {current_state}")

            # Get current pump state
            current_pump_state = self.pump_controller.get_well_pump_state()
            print(f"Current pump state: {'ON' if current_pump_state else 'OFF'}")

            # Handle pump control based on tank state
            if current_state == 'LOW':
                if not self._pump_started_from_low:
                    print("Tank LOW & pump not started - STARTING well pump")
                    self._pump_started_from_low = True
                    self._low_state_time = datetime.now()
                    result = self.pump_controller.set_well_pump(True)
                    print(f"Pump start result: {result}")
                else:
                    print("Tank LOW & pump already started - maintaining pump state")

            elif current_state == 'MID':
                if self._pump_started_from_low:
                    print("Tank MID & started from LOW - continuing pump operation")
                    result = self.pump_controller.set_well_pump(True)
                    print(f"Pump continue result: {result}")
                else:
                    print("Tank MID & NOT started from LOW - maintaining current state")

            elif current_state == 'HIGH':
                if self._pump_started_from_low:
                    print("Tank HIGH & started from LOW - STOPPING pump cycle")
                    result = self.pump_controller.set_well_pump(False)
                    print(f"Pump stop result: {result}")
                    self._pump_started_from_low = False
                    self._low_state_time = None
                else:
                    print("Tank HIGH & NOT started from LOW - maintaining off state")

            elif current_state == 'ERROR':
                print("Tank ERROR - SAFETY SHUTDOWN")
                result = self.pump_controller.set_well_pump(False)
                print(f"Pump emergency stop result: {result}")
                self._pump_started_from_low = False
                self._low_state_time = None
                self.notification_service.send_alert(
                    AlertType.TANK_ERROR,
                    "Winter tank in ERROR state",
                    {
                        "previous_state": self._last_state,
                        "pump_state": self.pump_controller.get_well_pump_state()
                    }
                )
        
            # Verify final state
            final_pump_state = self.pump_controller.get_well_pump_state()
            print(f"After processing, pump state: {'ON' if final_pump_state else 'OFF'}")
            print(f"Pump cycle active: {self._pump_started_from_low}")
            print(f"Low state time: {self._low_state_time}")
            print("=== End Winter Handler ===\n")

        except Exception as e:
            print(f"ERROR in winter mode handler: {e}")
            import traceback
            print(traceback.format_exc())
            # Safety measure - stop pump on error
            self.pump_controller.set_well_pump(False)
            self._pump_started_from_low = False
            self._low_state_time = None

    def get_handler_state(self):
        """Get current handler state for diagnostics"""
        return {
            'current_state': self._last_state,
            'low_state_active': self._low_state_time is not None,
            'pump_started_from_low': self._pump_started_from_low,
            'low_state_time': self._low_state_time.isoformat() if self._low_state_time else None,
            'well_pump_running': self.pump_controller.get_well_pump_state(),
            'dist_pump_running': self.pump_controller.get_distribution_pump_state()
        }