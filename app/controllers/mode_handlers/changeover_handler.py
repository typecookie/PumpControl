
from .base_handler import BaseModeHandler
from app.models.tank_state import TankState
from app.utils.notification_config import AlertType

class ChangeoverModeHandler(BaseModeHandler):
    def __init__(self, pump_controller, notification_service):
        super().__init__(pump_controller, notification_service)
        self._manual_well_pump_state = False

    def on_mode_enter(self):
        """Initialize state when entering changeover mode"""
        # Start distribution pump by default in changeover mode
        self.pump_controller.set_distribution_pump(True)
        # Ensure well pump is off initially
        self.pump_controller.set_well_pump(False)
        self._manual_well_pump_state = False
        self.notification_service.send_alert(
            AlertType.MODE_CHANGE,
            "Entered changeover mode - distribution pump started",
            {"Mode": "CHANGEOVER"}
        )

    def on_mode_exit(self):
        """Cleanup when exiting changeover mode"""
        # Turn off both pumps when exiting changeover mode
        self.pump_controller.set_well_pump(False)
        self.pump_controller.set_distribution_pump(False)
        self._manual_well_pump_state = False

    def handle(self, tank_state: TankState):
        """In changeover mode, we only monitor states but don't control pumps automatically"""
        # Monitor both tanks' states for notifications
        summer_states = self.get_tank_states()['summer']
        winter_states = self.get_tank_states()['winter']

        # Log critical states
        if summer_states['empty'] and not summer_states['low']:
            self.notification_service.send_alert(
                AlertType.TANK_EMPTY,
                "Summer tank is empty in changeover mode",
                {"Tank": "Summer"}
            )

        if not winter_states['low']:
            self.notification_service.send_alert(
                AlertType.TANK_LOW,
                "Winter tank is low in changeover mode",
                {"Tank": "Winter"}
            )

    def set_manual_well_pump(self, state: bool) -> dict:
        """Handle manual well pump control"""
        try:
            result = self.pump_controller.set_well_pump(state)
            if result.get('status') == 'success':
                self._manual_well_pump_state = state
                self.notification_service.send_alert(
                    AlertType.PUMP_STATE_CHANGE,
                    f"Well pump manually {'started' if state else 'stopped'} in changeover mode",
                    {"Pump": "Well", "State": "ON" if state else "OFF"}
                )
            return result
        except Exception as e:
            print(f"Error in manual well pump control: {e}")
            return {'status': 'error', 'message': str(e)}

    def set_manual_distribution_pump(self, state: bool) -> dict:
        """Handle manual distribution pump control"""
        try:
            result = self.pump_controller.set_distribution_pump(state)
            if result.get('status') == 'success':
                self.notification_service.send_alert(
                    AlertType.PUMP_STATE_CHANGE,
                    f"Distribution pump manually {'started' if state else 'stopped'} in changeover mode",
                    {"Pump": "Distribution", "State": "ON" if state else "OFF"}
                )
            return result
        except Exception as e:
            print(f"Error in manual distribution pump control: {e}")
            return {'status': 'error', 'message': str(e)}