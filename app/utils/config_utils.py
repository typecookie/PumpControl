import os
import json
from app.config import CONFIG_FILE, DEFAULT_CONFIG, MODES

class ConfigManager:
    @staticmethod
    def save_config(config):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    @staticmethod
    def load_config():
        """Load configuration from file"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    loaded_config = json.load(f)
                    return ConfigManager._merge_configs(DEFAULT_CONFIG.copy(), loaded_config)
        except Exception as e:
            print(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()

    @staticmethod
    def _merge_configs(default, loaded):
        """Recursively merge loaded config with defaults"""
        for key in default:
            if key not in loaded:
                loaded[key] = default[key]
            elif isinstance(default[key], dict) and isinstance(loaded[key], dict):
                loaded[key] = ConfigManager._merge_configs(default[key], loaded[key])
        return loaded

    @staticmethod
    def get_config(key, default=None):
        """Get a specific config value"""
        config = ConfigManager.load_config()
        try:
            return config.get(key, default)
        except (KeyError, TypeError):
            return default

    @staticmethod
    def set_config(key, value):
        """Set a specific config value"""
        if key not in DEFAULT_CONFIG:
            raise ValueError(f"Invalid config key: {key}")
            
        config = ConfigManager.load_config()
        config[key] = value
        ConfigManager.save_config(config)

    @staticmethod
    def get_available_modes():
        """Get list of available modes"""
        return list(MODES.keys())

    @staticmethod
    def is_valid_mode(mode):
        """Check if mode is valid"""
        return mode in MODES