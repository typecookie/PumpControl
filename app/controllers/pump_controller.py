# app/controllers/pump_controller.py
import threading
import time
from app.utils import GPIOManager, ConfigManager, TimeFormatter
from app.models.tank_state import TankState
from app.config import (
    WELL_PUMP, DIST_PUMP,
    SUMMER_HIGH, SUMMER_LOW, SUMMER_EMPTY,
    WINTER_HIGH, WINTER_LOW,
    MODES
)

class PumpController:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PumpController, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.config = ConfigManager.load_config()
        self.current_mode = self.config.get('current_mode', 'SUMMER')
        self.manual_pump_running = False
        self.pump_thread = None
        self.running = False
        self.mode_change_requested = None

        # Initialize tanks
        self.summer_tank = TankState('Summer')
        self.winter_tank = TankState('Winter')

        self._initialized = True

    def start(self):
        """Start the pump control thread"""
        if not self.running:
            print("Attempting to initialize GPIO...")
            try:
                if GPIOManager.initialize():
                    print("GPIO initialized successfully")
                    self.running = True
                    self.pump_thread = threading.Thread(target=self._control_loop, daemon=True)
                    self.pump_thread.start()
                    print("Pump controller thread started")
                    return True
                else:
                    print("Failed to initialize GPIO")
                    return False
            except Exception as e:
                print(f"Error during GPIO initialization: {e}")
                return False

    def stop(self):
        """Stop the pump control thread"""
        self.running = False
        if self.pump_thread:
            self.pump_thread.join(timeout=2.0)
        GPIOManager.cleanup()
        # Save final state
        self.save_current_state()
        print("Pump controller stopped")

    def save_current_state(self):
        """Save current configuration state"""
        self.config['current_mode'] = self.current_mode
        ConfigManager.save_config(self.config)

    def get_system_state(self):
        """Get current system state"""
        try:
            print("Getting system state...")
            # Start the controller if it's not running
            if not self.is_running:
                print("Controller not running, attempting to start...")
                self.start()
        
            active_tank = self.summer_tank if self.current_mode in ['SUMMER', 'CHANGEOVER'] else self.winter_tank
        
            # Get pump states with debug logging
            well_pump_state = GPIOManager.get_pump_state(WELL_PUMP)
            dist_pump_state = GPIOManager.get_pump_state(DIST_PUMP)
            print(f"Pump states - Well: {well_pump_state}, Distribution: {dist_pump_state}")
        
            state = {
                'current_mode': self.current_mode,
                'summer_tank': {
                    'state': self.summer_tank.state,
                    'stats': TimeFormatter.format_tank_stats(self.summer_tank.stats)
                },
                'winter_tank': {
                    'state': self.winter_tank.state,
                    'stats': TimeFormatter.format_tank_stats(self.winter_tank.stats)
                },
                'well_pump_status': 'ON' if well_pump_state else 'OFF',
                'dist_pump_status': 'ON' if dist_pump_state else 'OFF',
                'active_tank': active_tank.name,
                'thread_running': self.pump_thread.is_alive() if self.pump_thread else False,
                'timestamp': TimeFormatter.get_timestamp()
            }
        
            print(f"System state: {state}")
            return state
        
        except Exception as e:
            print(f"Error getting system state: {e}")
            raise

    def request_mode_change(self, new_mode, confirm=False):
        """Request or confirm a mode change"""
        try:
            if new_mode not in MODES:
                return {
                    'status': 'error',
                    'message': 'Invalid mode requested'
                }, 400

            if not confirm:
                self.mode_change_requested = new_mode
                return {
                    'status': 'confirmation_required',
                    'message': f'Confirm changing mode to {MODES[new_mode]}?'
                }

            # Confirmed mode change
            self.current_mode = new_mode
            self.mode_change_requested = None

            # Safety: turn off pumps during mode change
            GPIOManager.set_pump(WELL_PUMP, False)
            GPIOManager.set_pump(DIST_PUMP, False)

            # Save the new mode
            self.save_current_state()

            return {
                'status': 'success',
                'message': f'Mode changed to {MODES[new_mode]}',
                'current_mode': new_mode
            }

        except Exception as e:
            print(f"Error in mode change: {e}")
            return {'error': str(e)}, 500

    def set_manual_pump(self, running):
        """Control manual pump in changeover mode"""
        try:
            if self.current_mode != 'CHANGEOVER':
                return {
                    'status': 'error',
                    'message': 'Manual pump control only available in CHANGEOVER mode'
                }, 400

            self.manual_pump_running = running
            GPIOManager.set_pump(WELL_PUMP, running)

            return {
                'status': 'success',
                'pump_running': self.manual_pump_running
            }

        except Exception as e:
            print(f"Error in manual pump control: {e}")
            return {'error': str(e)}, 500

    def _update_tank_states(self):
        """Update tank states based on sensor readings"""
        try:
            print("Updating tank states...")
            # Summer Tank State Logic
            summer_high = GPIOManager.get_sensor_state(SUMMER_HIGH)
            summer_low = GPIOManager.get_sensor_state(SUMMER_LOW)
            summer_empty = GPIOManager.get_sensor_state(SUMMER_EMPTY)
        
            print(f"Summer tank sensors - High: {summer_high}, Low: {summer_low}, Empty: {summer_empty}")

            # Summer Tank Logic
            if summer_empty and summer_low and summer_high:
                self.summer_tank.state = "HIGH"
            elif summer_empty and summer_low and not summer_high:
                self.summer_tank.state = "MID"
            elif summer_empty and not summer_low and not summer_high:
                self.summer_tank.state = "LOW"
            elif not summer_empty and not summer_low and not summer_high:
                self.summer_tank.state = "EMPTY"
            else:
                self.summer_tank.state = "ERROR"

            print(f"Summer tank state set to: {self.summer_tank.state}")

            # Winter Tank Logic
            winter_high = GPIOManager.get_sensor_state(WINTER_HIGH)
            winter_low = GPIOManager.get_sensor_state(WINTER_LOW)
        
            print(f"Winter tank sensors - High: {winter_high}, Low: {winter_low}")

            if winter_high and winter_low:
                self.winter_tank.state = "HIGH"
            elif not winter_high and winter_low:
                self.winter_tank.state = "MID"
            elif not winter_high and not winter_low:
                self.winter_tank.state = "LOW"
            else:
                self.winter_tank.state = "ERROR"

            print(f"Winter tank state set to: {self.winter_tank.state}")

        except Exception as e:
            print(f"Error updating tank states: {e}")
            self.summer_tank.state = "ERROR"
            self.winter_tank.state = "ERROR"

    def _control_loop(self):
        """Main control loop"""
        pump_running = False

        while self.running:
            try:
                self._update_tank_states()

                print(f"Current mode: {self.current_mode}")

                if self.current_mode == 'SUMMER':
                    if self.summer_tank.state in ['EMPTY', 'LOW']:
                        pump_running = True
                    elif self.summer_tank.state == 'HIGH':
                        pump_running = False

                    GPIOManager.set_pump(WELL_PUMP, pump_running)
                    if pump_running:
                        self.summer_tank.update_stats(True)
                    print(f"Summer mode: {self.summer_tank.state} - Well pump {'ON' if pump_running else 'OFF'}")

                elif self.current_mode == 'WINTER':
                    if self.winter_tank.state == 'LOW':
                        pump_running = True
                    elif self.winter_tank.state == 'HIGH':
                        pump_running = False

                    GPIOManager.set_pump(WELL_PUMP, pump_running)
                    if pump_running:
                        self.winter_tank.update_stats(True)
                    print(f"Winter mode: {self.winter_tank.state} - Well pump {'ON' if pump_running else 'OFF'}")

                elif self.current_mode == 'CHANGEOVER':
                    print(f"Changeover mode - Manual control only")
                    print(f"Summer tank: {self.summer_tank.state}, Winter tank: {self.winter_tank.state}")
                    pump_running = self.manual_pump_running
                    if not pump_running:
                        GPIOManager.set_pump(WELL_PUMP, False)

                # Safety check for errors
                if (self.summer_tank.state == 'ERROR' or self.winter_tank.state == 'ERROR'):
                    pump_running = False
                    GPIOManager.set_pump(WELL_PUMP, False)
                    print("Tank error state detected - Well pump OFF for safety")

                time.sleep(1)

            except Exception as e:
                print(f"Error in control loop: {e}")
                pump_running = False
                GPIOManager.set_pump(WELL_PUMP, False)
                GPIOManager.set_pump(DIST_PUMP, False)
                time.sleep(1)

    @property
    def is_running(self):
        """Check if pump controller is running"""
        return self.running and (self.pump_thread and self.pump_thread.is_alive())