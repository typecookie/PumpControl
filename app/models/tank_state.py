from app.utils.stats_manager import StatsManager


class TankState:
    def __init__(self, name):
        self.name = name
        self.state = 'unknown'
        self.stats = {
            'today_runtime': 0,
            'today_gallons': 0,
            'week_runtime': 0,
            'week_gallons': 0,
            'month_runtime': 0,
            'month_gallons': 0
        }
        self._load_stats()

    def _load_stats(self):
        """Load saved statistics"""
        summer_stats, winter_stats = StatsManager.load_stats()
        if self.name == 'Summer':
            if summer_stats:  # Add null check
                self.stats.update(summer_stats)
        elif self.name == 'Winter':
            if winter_stats:  # Add null check
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