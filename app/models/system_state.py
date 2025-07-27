from datetime import datetime
from app.utils.time_utils import TimeFormatter

class SystemState:
    def __init__(self, current_mode=None, summer_tank=None, winter_tank=None, 
                 well_pump_status=None, dist_pump_status=None, thread_running=False):
        self.current_mode = current_mode
        self.summer_tank = summer_tank or {'state': 'unknown'}
        self.winter_tank = winter_tank or {'state': 'unknown'}
        self.well_pump_status = well_pump_status
        self.dist_pump_status = dist_pump_status
        self.thread_running = thread_running
        self.last_update = datetime.now()

    @classmethod
    def create_error_state(cls):
        """Create an error state object"""
        return cls(
            current_mode='ERROR',
            summer_tank={'state': 'ERROR', 'stats': {}},
            winter_tank={'state': 'ERROR', 'stats': {}},
            well_pump_status='ERROR',
            dist_pump_status='ERROR',
            thread_running=False
        )

    def to_dict(self):
        """Convert state to dictionary"""
        return {
            'current_mode': self.current_mode,
            'summer_tank': self.summer_tank,
            'winter_tank': self.winter_tank,
            'well_pump_status': self.well_pump_status,
            'dist_pump_status': self.dist_pump_status,
            'thread_running': self.thread_running,
            'timestamp': TimeFormatter.get_timestamp()
        }