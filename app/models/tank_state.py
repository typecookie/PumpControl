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
        
        self.stats = {
            'today_runtime': 0,
            'today_gallons': 0,
            'week_runtime': 0,
            'week_gallons': 0,
            'month_runtime': 0,
            'month_gallons': 0
        }
        self._load_stats()

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
                print(
                    f"Raw sensor values - High: {self.summer_high}, Low: {self.summer_low}, Empty: {self.summer_empty}")

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

        except Exception as e:
            print(f"Error updating tank state: {e}")
            import traceback
            print(traceback.format_exc())
            self.state = 'ERROR'

    def _load_stats(self):
        """Load saved statistics"""
        summer_stats, winter_stats = StatsManager.load_stats()
        if self.name == 'Summer':
            if summer_stats:
                self.stats.update(summer_stats)
        elif self.name == 'Winter':
            if winter_stats:
                self.stats.update(winter_stats)

    def save_stats(self):
        """Save current statistics"""
        current_summer_stats, current_winter_stats = StatsManager.load_stats()
        if self.name == 'Summer':
            StatsManager.save_stats(self.stats, current_winter_stats)
        elif self.name == 'Winter':
            StatsManager.save_stats(current_summer_stats, self.stats)

    def get_formatted_stats(self):
        """Return formatted statistics"""
        from app.utils.time_utils import TimeFormatter
        return TimeFormatter.format_tank_stats(self.stats)

    def update_stats(self, is_running):
        """Update tank statistics"""
        if is_running:
            self.stats['today_runtime'] += 1
            self.stats['today_gallons'] += 40/60  # Assuming 40 GPM flow rate
            self.stats['week_runtime'] += 1
            self.stats['week_gallons'] += 40/60
            self.stats['month_runtime'] += 1
            self.stats['month_gallons'] += 40/60
            self.save_stats()