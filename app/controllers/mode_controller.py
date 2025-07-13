from app.controllers import Controller
from app.utils.config_utils import ConfigManager

class ModeController(Controller):
    def _init(self):
        """Initialize mode controller"""
        self.config = ConfigManager.load_config()
        self.current_mode = self.config.get('current_mode', 'SUMMER')
    
    def set_mode(self, mode):
        """Change system mode"""
        if mode in ['SUMMER', 'WINTER', 'CHANGEOVER']:
            self.current_mode = mode
            self.config['current_mode'] = mode
            ConfigManager.save_config(self.config)
            return True
        return False