# app/utils/config_utils.py
import json
import os
from app.config import CONFIG_FILE, DEFAULT_CONFIG

class ConfigManager:
    @staticmethod
    def save_config(config):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving config: {e}")

    @staticmethod
    def load_config():
        """Load configuration from file"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()