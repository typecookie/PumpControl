# app/controllers/mode_controller.py
from app.utils.config_utils import ConfigManager
from app.config import MODES

class ModeController:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModeController, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.config = ConfigManager.load_config()
        self.current_mode = self.config.get('current_mode', 'SUMMER')
        self.mode_change_requested = None

    def get_current_mode(self):
        """Get current system mode"""
        return self.current_mode

    def get_available_modes(self):
        """Get list of available modes"""
        return MODES

    def request_mode_change(self, new_mode, confirm=False):
        """Request or confirm a mode change"""
        if new_mode not in MODES:
            return {
                'status': 'error',
                'message': 'Invalid mode requested'
            }, 400

        if not confirm:
            self.mode_change_requested = new_mode
            return {
                'status': 'confirmation_required',
                'message': f'Confirm changing mode to {MODES[new_mode]}?'
            }

        self.current_mode = new_mode
        self.mode_change_requested = None
        
        # Save the new mode
        self.config['current_mode'] = self.current_mode
        ConfigManager.save_config(self.config)
        
        return {
            'status': 'success',
            'message': f'Mode changed to {MODES[new_mode]}',
            'current_mode': new_mode
        }

    def get_pending_mode_change(self):
        """Get any pending mode change request"""
        return self.mode_change_requested