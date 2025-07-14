from app.utils.config_utils import ConfigManager, MODES
from app.controllers import Controller
from .interfaces import IModeController

class ModeController(Controller, IModeController):
    def _init(self):
        """Initialize mode controller"""
        self.config = ConfigManager.load_config()
        if 'current_mode' not in self.config:
            raise ValueError("Invalid config: missing current_mode")
        self.current_mode = self.config['current_mode']
        self.mode_change_requested = None
        print(f"Mode Controller initialized with mode: {self.current_mode}")


    def get_current_mode(self):
        return self.current_mode

    def request_mode_change(self, new_mode, confirm=False):
        print(f"Mode change request received - New mode: {new_mode}, Current mode: {self.current_mode}, Confirm: {confirm}")
        print(f"Current config state: {self.config}")

        if new_mode not in MODES:
            print(f"Invalid mode requested: {new_mode}")
            return {
                'status': 'error',
                'message': f'Invalid mode requested: {new_mode}'
            }, 400

        if not confirm:
            print(f"Requesting confirmation for mode change to: {new_mode}")
            self.mode_change_requested = new_mode
            return {
                'status': 'confirmation_required',
                'message': f'Confirm changing mode to {MODES[new_mode]}?'
            }

        try:
            print(f"Confirmed mode change from {self.current_mode} to {new_mode}")
            old_mode = self.current_mode
            self.current_mode = new_mode
            self.mode_change_requested = None

            # Save the new mode
            print("Saving current state...")
            self.save_current_state()
            print("State saved, reloading config...")

            # Force reload config and verify
            ConfigManager.reload_config()
            saved_config = ConfigManager.load_config()
            saved_mode = saved_config.get('current_mode')
            print(f"Verified saved mode: {saved_mode}")

            if saved_mode != new_mode:
                print(f"Mode save verification failed! Config shows {saved_mode}, expected {new_mode}")
                self.current_mode = old_mode
                return {
                    'status': 'error',
                    'message': 'Failed to persist mode change'
                }, 500

            print(f"Mode change successful - now in {new_mode} mode")
            return {
                'status': 'success',
                'message': f'Mode changed to {MODES[new_mode]}',
                'current_mode': new_mode
            }

        except Exception as e:
            print(f"Error in mode change: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error changing mode: {str(e)}'
            }, 500

    def save_current_state(self):
        """Save current mode to config"""
        try:
            config = ConfigManager.load_config()
            config['current_mode'] = self.current_mode
            ConfigManager.save_config(config)
            print(f"Saved current mode to config: {self.current_mode}")
        except Exception as e:
            print(f"Error saving current mode to config: {e}")
            raise