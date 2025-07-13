# GPIO Pin Definitions
WELL_PUMP = 17
DIST_PUMP = 18
SUMMER_HIGH = 22
SUMMER_LOW = 23
SUMMER_EMPTY = 24
WINTER_HIGH = 26
WINTER_LOW = 27

# System Modes
MODES = {
    'SUMMER': 'Summer Mode',
    'WINTER': 'Winter Mode',
    'CHANGEOVER': 'Changeover Mode'
}

# Configuration settings
CONFIG_FILE = 'pump_config.json'
DEFAULT_CONFIG = {
    'current_mode': 'SUMMER'
}