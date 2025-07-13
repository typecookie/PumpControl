# app/models/system_state.py
from datetime import datetime
from app.utils.time_utils import TimeFormatter

class SystemState:
    def __init__(self):
        self.current_mode = None
        self.summer_tank = None
        self.winter_tank = None
        self.well_pump = None
        self.dist_pump = None
        self.last_update = None
        
    def update(self, mode, summer_tank, winter_tank, well_pump, dist_pump):
        self.current_mode = mode
        self.summer_tank = summer_tank
        self.winter_tank = winter_tank
        self.well_pump = well_pump
        self.dist_pump = dist_pump
        self.last_update = datetime.now()
        
    def get_state(self):
        return {
            'current_mode': self.current_mode,
            'summer_tank': self.summer_tank.get_state() if self.summer_tank else {'state': 'unknown'},
            'winter_tank': self.winter_tank.get_state() if self.winter_tank else {'state': 'unknown'},
            'well_pump': self.well_pump.get_state() if self.well_pump else {'state': 'unknown'},
            'dist_pump': self.dist_pump.get_state() if self.dist_pump else {'state': 'unknown'},
            'timestamp': TimeFormatter.get_timestamp()
        }