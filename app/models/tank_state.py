from app.utils.stats_manager import StatsManager  # Changed from stats_manager to status_manager

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
        if self.name == 'Summer':
            StatsManager.save_stats(self.stats, None)
        elif self.name == 'Winter':
            StatsManager.save_stats(None, self.stats)
    
    def update_stats(self, pump_running):
        """Update runtime statistics when pump is running"""
        if pump_running:
            self.stats['today_runtime'] += 1
            self.stats['today_gallons'] += 1
            self.stats['week_runtime'] += 1
            self.stats['week_gallons'] += 1
            self.stats['month_runtime'] += 1
            self.stats['month_gallons'] += 1
            self.save_stats()  # Save stats after updating