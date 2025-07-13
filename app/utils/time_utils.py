# app/utils/time_utils.py
from datetime import datetime

class TimeFormatter:
    @staticmethod
    def format_runtime(seconds):
        """Format seconds into HH:MM:SS"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @staticmethod
    def format_tank_stats(stats):
        """Format tank statistics for API response"""
        return {
            'today_runtime': TimeFormatter.format_runtime(stats['today_runtime']),
            'today_gallons': round(stats['today_gallons'], 1),
            'week_runtime': TimeFormatter.format_runtime(stats['week_runtime']),
            'week_gallons': round(stats['week_gallons'], 1),
            'month_runtime': TimeFormatter.format_runtime(stats['month_runtime']),
            'month_gallons': round(stats['month_gallons'], 1)
        }

    @staticmethod
    def get_timestamp():
        """Get current timestamp in standard format"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")