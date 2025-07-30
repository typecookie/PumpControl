from app.utils.config_utils import ConfigManager, MODES
from app.controllers import Controller
from .interfaces import IModeController
import time

class ModeController(Controller, IModeController):
    def _init(self):
        """Initialize mode controller"""
        self.config = ConfigManager.load_config()
        if 'current_mode' not in self.config:
            raise ValueError("Invalid config: missing current_mode")
        self.current_mode = self.config['current_mode']
        self.mode_change_requested = None
        
        # Add mode retention variables
        self.last_valid_mode = self.current_mode
        self.last_error_time = None
        self.MODE_RETENTION_TIME = 30  # seconds
        
        print(f"Mode Controller initialized with mode: {self.current_mode}")

    def get_current_mode(self):
        """Get current mode with retention logic"""
        try:
            current_time = time.time()
            
            # If current mode is invalid but within retention period, return last valid mode
            if self.current_mode in [None, 'ERROR', 'unknown']:
                if (self.last_valid_mode and self.last_error_time and 
                    current_time - self.last_error_time < self.MODE_RETENTION_TIME):
                    print(f"Using retained mode: {self.last_valid_mode}")
                    return self.last_valid_mode
            else:
                # Update last valid mode and timestamp
                self.last_valid_mode = self.current_mode
                self.last_error_time = current_time
                
            return self.current_mode
            
        except Exception as e:
            print(f"Error getting mode: {e}")
            if self.last_valid_mode:
                return self.last_valid_mode
            return 'ERROR'

    def request_mode_change(self, new_mode, confirm=False):
        print(f"Mode change request received - New mode: {new_mode}, Current mode: {self.current_mode}, Confirm: {confirm}")
        
        if new_mode not in MODES:
            print(f"Invalid mode requested: {new_mode}")
            return {
                'status': 'error',
                'message': f'Invalid mode requested: {new_mode}'
            }, 400

        if not confirm:
            self.mode_change_requested = new_mode
            return {
                'status': 'confirmation_required',
                'message': f'Confirm changing mode to {MODES[new_mode]}?'
            }

        try:
            old_mode = self.current_mode
            self.current_mode = new_mode
            self.mode_change_requested = None
            
            # Update last valid mode immediately for mode changes
            self.last_valid_mode = new_mode
            self.last_error_time = time.time()

            print("Saving current state...")
            self.save_current_state()
            
            # Verify the change
            ConfigManager.reload_config()
            saved_config = ConfigManager.load_config()
            saved_mode = saved_config.get('current_mode')
            
            if saved_mode != new_mode:
                print(f"Mode save verification failed! Config shows {saved_mode}, expected {new_mode}")
                self.current_mode = old_mode
                self.last_valid_mode = old_mode  # Reset last valid mode on failure
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