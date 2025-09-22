from app.utils.gpio_utils import GPIOManager
from app.utils.config_utils import (
    SUMMER_HIGH, SUMMER_LOW, SUMMER_EMPTY,
    WINTER_HIGH, WINTER_LOW
)
from app.utils.stats_manager import StatsManager

class TankState:
    def __init__(self, name):
        self.name = name
        self.state = 'unknown'
        # Add winter and summer sensor states
        self.winter_high = False
        self.winter_low = False
        self.summer_high = False
        self.summer_low = False
        self.summer_empty = False
        
        # Initialize StatsManager to ensure it's ready
        StatsManager.initialize()
        
        # No call to _load_stats() here - removed as it's no longer needed

    def update_from_sensors(self, gpio_manager):
        """Update tank state from sensors"""
        try:
            # Get sensor states for both tanks
            self.winter_high = gpio_manager.get_sensor_state(WINTER_HIGH)
            self.winter_low = gpio_manager.get_sensor_state(WINTER_LOW)
            self.summer_high = gpio_manager.get_sensor_state(SUMMER_HIGH)
            self.summer_low = gpio_manager.get_sensor_state(SUMMER_LOW)
            self.summer_empty = gpio_manager.get_sensor_state(SUMMER_EMPTY)

            # Winter tank logic
            if self.name == 'Winter':
                print("\n=== Winter Tank State Update ===")
                print(f"Raw sensor values - High: {self.winter_high}, Low: {self.winter_low}")

                # State determination
                if self.winter_high:
                    self.state = 'HIGH'
                elif not self.winter_low:  # LOW when sensor is NOT triggered
                    self.state = 'LOW'
                elif self.winter_low and not self.winter_high:
                    self.state = 'MID'
                else:
                    self.state = 'ERROR'

                print(f"Computed state: {self.state}")
                print("=== End Winter Tank Update ===\n")

            # Summer tank logic
            elif self.name == 'Summer':
                print("\n=== Summer Tank State Update ===")
                print(f"Raw sensor values - High: {self.summer_high}, Low: {self.summer_low}, Empty: {self.summer_empty}")

                # State determination for summer tank
                if self.summer_high:
                    self.state = 'HIGH'
                elif self.summer_low and not self.summer_high:
                    self.state = 'MID'
                elif self.summer_empty and not self.summer_low and not self.summer_high:
                    self.state = 'LOW'
                elif not self.summer_empty and not self.summer_low and not self.summer_high:
                    self.state = 'EMPTY'
                else:
                    self.state = 'ERROR'

                print(f"Computed state: {self.state}")
                print("=== End Summer Tank Update ===\n")

            # Update tank state history in StatsManager
            StatsManager.update_tank_state(self.name.lower(), self.state)
            
        except Exception as e:
            print(f"Error updating tank state: {e}")
            import traceback
            print(traceback.format_exc())
            self.state = 'ERROR'

    def get_formatted_stats(self):
        """Return formatted statistics from StatsManager"""
        try:
            # For backward compatibility, return a dict in the expected format
            pump_type = 'well_pump'  # Default to well pump stats
            stats = StatsManager.get_pump_stats(pump_type)
            
            if not stats:
                return {}
                
            # Convert from StatsManager format to the old format
            return {
                'today_runtime': stats.get('today', {}).get('runtime', 0),
                'today_gallons': stats.get('today', {}).get('volume', 0),
                'week_runtime': stats.get('week', {}).get('runtime', 0),
                'week_gallons': stats.get('week', {}).get('volume', 0),
                'month_runtime': stats.get('month', {}).get('runtime', 0),
                'month_gallons': stats.get('month', {}).get('volume', 0)
            }
        except Exception as e:
            print(f"Error getting formatted stats: {e}")
            return {}
            
