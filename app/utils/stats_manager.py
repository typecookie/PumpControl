import json
import os
from datetime import datetime


class StatsManager:
    STATS_FILE = 'tank_stats.json'

    @classmethod
    def save_stats(cls, summer_stats, winter_stats):
        """Save tank statistics to file"""
        try:
            data = {
                'summer_tank': summer_stats or {},  # Use empty dict if None
                'winter_tank': winter_stats or {},  # Use empty dict if None
                'last_updated': datetime.now().isoformat()
            }
            with open(cls.STATS_FILE, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Error saving stats: {e}")

    @classmethod
    def load_stats(cls):
        """Load tank statistics from file"""
        try:
            if os.path.exists(cls.STATS_FILE):
                with open(cls.STATS_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('summer_tank', {}), data.get('winter_tank', {})
        except Exception as e:
            print(f"Error loading stats: {e}")
        return {}, {}  # Return empty stats if file doesn't exist or there's an error