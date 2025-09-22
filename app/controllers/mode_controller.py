from app.controllers.interfaces import IModeController
from app.models.tank_state import TankState
from app.services.notification_service import NotificationService
from app.controllers.mode_handlers.summer_handler import SummerModeHandler
from app.controllers.mode_handlers.winter_handler import WinterModeHandler
from app.controllers.mode_handlers.changeover_handler import ChangeoverModeHandler
from app.utils.gpio_utils import GPIOManager

class ModeController(IModeController):
    def __init__(self):
        self._current_mode = "SUMMER"
        self._pump_controller = None
        self._notification_service = None
        self._handlers = {}
        self._current_handler = None

    def set_pump_controller(self, controller):
        """Set pump controller and initialize handlers"""
        self._pump_controller = controller
        self._notification_service = NotificationService()
        
        # Initialize mode handlers
        self._handlers = {
            "SUMMER": SummerModeHandler(self._pump_controller, self._notification_service),
            "WINTER": WinterModeHandler(self._pump_controller, self._notification_service),
            "CHANGEOVER": ChangeoverModeHandler(self._pump_controller, self._notification_service)
        }
        
        # Set initial handler
        self._current_handler = self._handlers.get(self._current_mode)
        if self._current_handler:
            self._current_handler.on_mode_enter()

    def get_current_mode(self) -> str:
        return self._current_mode

    def request_mode_change(self, new_mode: str, confirm: bool = False):
        """Handle mode change requests"""
        print(f"Mode change request: new_mode={new_mode}, confirm={confirm}")
        
        if new_mode not in ["SUMMER", "WINTER", "CHANGEOVER"]:
            print(f"Invalid mode specified: {new_mode}")
            return {"status": "error", "message": "Invalid mode specified"}

        if new_mode == self._current_mode:
            print(f"System is already in {new_mode} mode")
            return {"status": "error", "message": f"System is already in {new_mode} mode"}

        if confirm:
            print(f"Confirming mode change from {self._current_mode} to {new_mode}")
            # Exit current mode handler
            if self._current_handler:
                print(f"Exiting current handler: {type(self._current_handler).__name__}")
                try:
                    self._current_handler.on_mode_exit()
                except Exception as e:
                    print(f"Error exiting current mode: {e}")
                    import traceback
                    print(traceback.format_exc())

            self._current_mode = new_mode
        
        # Enter new mode handler
            self._current_handler = self._handlers.get(new_mode)
            if self._current_handler:
                print(f"Entering new handler: {type(self._current_handler).__name__}")
                try:
                    self._current_handler.on_mode_enter()
                except Exception as e:
                    print(f"Error entering new mode: {e}")
                    import traceback
                    print(traceback.format_exc())

            return {"status": "success", "message": f"Mode changed to {new_mode}"}
        else:
            print(f"Requesting confirmation for mode change to {new_mode}")
            return {
                "status": "confirm",
                "message": f"Please confirm changing to {new_mode} mode",
                "data": {"new_mode": new_mode}
            }

    def handle_mode_controls(self, tank_state):
        """Route control to appropriate mode handler"""
        try:
            print(f"Mode controller handling tank state: {tank_state.state} in mode: {self._current_mode}")
        
            if self._current_handler:
                print(f"Routing to handler: {type(self._current_handler).__name__}")
                self._current_handler.handle(tank_state)
            else:
                print(f"No handler for current mode: {self._current_mode}")
        except Exception as e:
            print(f"Error in mode controller: {e}")
            import traceback
            print(traceback.format_exc())
