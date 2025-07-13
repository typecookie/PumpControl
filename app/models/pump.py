# app/models/pump.py
class Pump:
    def __init__(self, name, pin):
        self.name = name
        self.pin = pin
        self.state = False
        self.runtime = 0
        self.total_volume = 0
        
    def turn_on(self):
        self.state = True
        
    def turn_off(self):
        self.state = False
        
    def update_stats(self, running_time):
        if self.state:
            self.runtime += running_time
            # Assuming 1 gallon per second flow rate
            self.total_volume += running_time

    def get_state(self):
        return {
            'name': self.name,
            'state': 'ON' if self.state else 'OFF',
            'runtime': self.runtime,
            'total_volume': round(self.total_volume, 1)
        }