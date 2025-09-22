from .base_controller import Controller
from .pump_controller import PumpController
from .mode_controller import ModeController
from RPi import GPIO
from app.utils.config_utils import ConfigManager
from app.utils.gpio_utils import GPIOManager
from app.utils.config_utils import ConfigManager
from app.models.tank_state import TankState
from app.utils.config_utils import *
from .interfaces import *

# Create instances
pump_controller = PumpController()
mode_controller = ModeController()

# Connect controllers
mode_controller.set_pump_controller(pump_controller)
pump_controller.set_mode_controller(mode_controller)

# Force initial config reload
ConfigManager.reload_config()


__all__ = [
    'Controller',
    'PumpController',
    'ModeController',
    'GPIO',
    'ConfigManager',
    'GPIOManager',
    'ConfigManager',
    'TankState',
    'WELL_PUMP', 'SUMMER_HIGH', 'SUMMER_LOW', 'SUMMER_EMPTY', 'WINTER_HIGH', 'WINTER_LOW', 'MODES',
    'IPumpController', 'IModeController'
]