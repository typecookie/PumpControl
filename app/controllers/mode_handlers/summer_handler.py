
from .base_handler import BaseModeHandler
from app.models.tank_state import TankState
from app.utils.notification_config import AlertType
from app.utils.gpio_utils import GPIOManager  # Add this import

class SummerModeHandler(BaseModeHandler):
    def __init__(self, pump_controller, notification_service):
        super().__init__(pump_controller, notification_service)
        self._last_state = None

    def on_mode_enter(self):
        """Initialize state when entering summer mode"""
        self._last_state = None
        # Make sure pump is off when entering mode
        self.pump_controller.set_well_pump(False)
        self.pump_controller.set_distribution_pump(True)

    def on_mode_exit(self):
        """Cleanup when exiting summer mode"""
        self._last_state = None
        # Make sure pump is off when exiting mode
        self.pump_controller.set_well_pump(False)
        self.pump_controller.set_distribution_pump(False)

    def handle(self, tank_state: TankState) -> None:
        """Handle summer mode pump control logic"""
        try:
            # Check if we have a summer tank state
            if tank_state.name != 'Summer':
                print(f"Warning: Summer handler received {tank_state.name} tank state")
                return
                
            # Get current states
            current_state = tank_state.state
            print(f"Summer tank state: {current_state}")
            print(f"Raw sensor values - High: {tank_state.summer_high}, Low: {tank_state.summer_low}, Empty: {tank_state.summer_empty}")
            
            # If state is unknown, try to update it
            if current_state == 'unknown':
                print("Warning: Unknown tank state, updating sensors")
                tank_state.update_from_sensors(GPIOManager)
                current_state = tank_state.state
                if current_state == 'unknown':
                    print("Still unknown after sensor update, aborting control logic")
                    return
        
            # Get pump states safely
            pump_states = self.pump_controller.get_pump_states()
            well_running = False
            
            # Extract well pump state from pump_states safely
            if isinstance(pump_states, dict) and 'well_pump' in pump_states:
                if isinstance(pump_states['well_pump'], dict):
                    well_running = pump_states['well_pump'].get('state') == 'ON'
                else:
                    well_running = bool(pump_states['well_pump'])
            
            print(f"Summer handler - current state: {current_state}, well pump: {well_running}")

            # Handle state changes for notifications
            if self._last_state is not None and current_state != self._last_state:
                try:
                    self.notification_service.send_alert(
                        AlertType.TANK_STATE_CHANGE,
                        f"Summer tank state changed from {self._last_state} to {current_state}",
                        {"Previous": self._last_state, "Current": current_state}
                    )
                except Exception as e:
                    print(f"Error sending notification: {e}")
                    
            self._last_state = current_state

            # Control logic
            if current_state == 'LOW':
                self.pump_controller.set_distribution_pump(True)
                if not well_running:
                    print("Starting well pump - tank empty or low")
                    self.pump_controller.set_well_pump(True)
            elif current_state == 'HIGH':
                self.pump_controller.set_distribution_pump(True)
                if well_running:
                    print("Stopping well pump - tank full")
                    self.pump_controller.set_well_pump(False)
            elif current_state == 'EMPTY':
                if well_running:
                    self.pump_controller.set_distribution_pump(False)
                    print("Stopping distribution pump - tank empty")
                elif not well_running:
                    self.pump_controller.set_well_pump(True)
                    self.pump_controller.set_distribution_pump(True)
            elif current_state == 'ERROR':
                # Keep current pump state in error condition
                print("Tank in error state - maintaining current pump state")
                
        except Exception as e:
            print(f"Error in summer handler: {e}")
            import traceback
            print(traceback.format_exc())
            
    def get_handler_state(self):
        """Get current handler state for diagnostics"""
        return {
            'current_state': self._last_state,
            'well_pump_running': self.pump_controller.get_well_pump_state(),
            'dist_pump_running': self.pump_controller.get_distribution_pump_state()
        }