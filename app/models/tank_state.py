# app/models/tank_state.py
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
    
    def update_stats(self, pump_running):
        """Update runtime statistics when pump is running"""
        if pump_running:
            self.stats['today_runtime'] += 1
            self.stats['today_gallons'] += 1  # Assuming 1 gallon per second
            self.stats['week_runtime'] += 1
            self.stats['week_gallons'] += 1
            self.stats['month_runtime'] += 1
            self.stats['month_gallons'] += 1

    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.stats['today_runtime'] = 0
        self.stats['today_gallons'] = 0

    def reset_weekly_stats(self):
        """Reset weekly statistics"""
        self.stats['week_runtime'] = 0
        self.stats['week_gallons'] = 0

    def reset_monthly_stats(self):
        """Reset monthly statistics"""
        self.stats['month_runtime'] = 0
        self.stats['month_gallons'] = 0