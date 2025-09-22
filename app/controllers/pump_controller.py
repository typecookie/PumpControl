import threading
import time
from app.utils.gpio_utils import GPIOManager
from app.utils.config_utils import WELL_PUMP, DIST_PUMP
from app.models.tank_state import TankState
from app.controllers.interfaces import IPumpController
from typing import Dict, Any
# Add this to your imports
from app.utils.stats_manager import StatsManager
import time

class PumpController(IPumpController):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PumpController, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    # Add the following in your PumpController class
    def __init__(self):
        if self._initialized:
            return
        
        try:
            # Initialize GPIO
            if not GPIOManager.initialize():
                raise RuntimeError("Failed to initialize GPIO")
        
            # Initialize stats manager
            StatsManager.initialize()
        
            self.running = False
            self.pump_thread = None
            self._last_state = None
            self._state_timestamp = 0
            self.mode_controller = None
        
            # Add these lines for tracking last update time
            self._last_well_update = time.time()
            self._last_dist_update = time.time()
            self._well_running = False
            self._dist_running = False
        
            self._initialized = True
        
        except Exception as e:
            print(f"Error initializing PumpController: {e}")
            raise

    def set_mode_controller(self, controller):
        """Set the mode controller reference"""
        self.mode_controller = controller

    def set_manual_pump(self, running: bool) -> Dict[str, Any]:
        """Control manual pump operation
        
        Args:
            running: True to turn on, False to turn off
            
        Returns:
            Dict[str, Any]: Status response
        """
        try:
            print(f"\n=== Setting Manual Pump ===")
            print(f"Requested State: {running}")
            
            # Set the well pump directly
            result = self.set_well_pump(running)
            print(f"Manual pump set result: {result}")
            print(f"=== End Setting Manual Pump ===\n")
            
            return result
        except Exception as e:
            print(f"Error in manual pump control: {e}")
            import traceback
            print(traceback.format_exc())
            return {'status': 'error', 'message': str(e)}

    def start(self):
        """Start the pump controller thread"""
        if not self.running:
            try:
                self.running = True
                self.pump_thread = threading.Thread(target=self._control_loop, daemon=True)
                self.pump_thread.start()
                print("Pump controller thread started")
                return True
            except Exception as e:
                print(f"Error starting pump controller: {e}")
                return False
        return True

    def _control_loop(self):
        """Main control loop"""
        print("Starting pump controller loop")
        while self.running:
            try:
                # Create current tank states based on mode
                current_mode = self.mode_controller.get_current_mode() if self.mode_controller else "WINTER"
                print(f"\n=== Control Loop Iteration (Mode: {current_mode}) ===")
            
                # Create the appropriate tank state based on mode
                if current_mode == "SUMMER":
                    tank_state = TankState('Summer')
                else:
                    tank_state = TankState('Winter')
                
                # Update the tank state from sensors
                print(f"Tank state created: name={tank_state.name}, state={tank_state.state}")
            
                # Update tank state history
                StatsManager.update_tank_state(tank_state.name.lower(), tank_state.state)
            
                # Let mode controller handle the logic
                if self.mode_controller:
                    self.mode_controller.handle_mode_controls(tank_state)
                else:
                    print("Warning: No mode controller set")

                # Get current pump states
                current_well_running = self.get_well_pump_state()
                current_dist_running = self.get_distribution_pump_state()
                current_time = time.time()
            
                # Update well pump stats if state has changed or pump is running
                if current_well_running != self._well_running or current_well_running:
                    elapsed = current_time - self._last_well_update
                    StatsManager.update_pump_stats('well_pump', self._well_running, elapsed)
                    self._last_well_update = current_time
                    self._well_running = current_well_running
            
                # Update distribution pump stats if state has changed or pump is running
                if current_dist_running != self._dist_running or current_dist_running:
                    elapsed = current_time - self._last_dist_update
                    StatsManager.update_pump_stats('dist_pump', self._dist_running, elapsed)
                    self._last_dist_update = current_time
                    self._dist_running = current_dist_running

                # Update cached state
                current_state = {
                    'well_pump': {
                        'state': 'ON' if current_well_running else 'OFF'
                    },
                    'dist_pump': {
                        'state': 'ON' if current_dist_running else 'OFF'
                    }
                }
                self._last_state = current_state
                self._state_timestamp = time.time()

                # Log current system state
                print(f"Current system state: well={current_state['well_pump']['state']}, dist={current_state['dist_pump']['state']}")
                print("=== End Control Loop Iteration ===")
        
                time.sleep(1)

            except Exception as e:
                print(f"Error in control loop: {e}")
                import traceback
                print(traceback.format_exc())
                time.sleep(1)

    def set_well_pump(self, state: bool) -> dict:
        """Set well pump state"""
        try:
            print("\n=== Setting Well Pump State ===")
            print(f"Requested State: {state}")
        
            current_state = GPIOManager.get_pump_state(WELL_PUMP)
            print(f"Current State: {current_state}")
        
            if current_state == state:
                print("Pump already in requested state")
                return {
                    'status': 'success',
                    'pump_running': current_state,
                    'message': 'Pump already in requested state'
                }
        
            print("Setting new pump state...")
            success = GPIOManager.set_pump(WELL_PUMP, state)
            actual_state = GPIOManager.get_pump_state(WELL_PUMP)
        
            print(f"Set Pump Result:")
            print(f"  Success: {success}")
            print(f"  Actual State: {actual_state}")
            print(f"  Requested State: {state}")
            print("=== End Setting Well Pump ===\n")
        
            return {
                'status': 'success' if success and actual_state == state else 'error',
                'pump_running': actual_state,
                'message': 'Pump state changed successfully' if success else 'Failed to change pump state'
            }
        except Exception as e:
            print(f"Error controlling well pump: {e}")
            import traceback
            print(traceback.format_exc())
            return {'status': 'error', 'message': str(e)}

    def set_distribution_pump(self, state: bool) -> dict:
        """Set distribution pump state"""
        try:
            GPIOManager.set_pump(DIST_PUMP, state)
            actual_state = GPIOManager.get_pump_state(DIST_PUMP)
            return {
                'status': 'success' if actual_state == state else 'error',
                'pump_running': actual_state
            }
        except Exception as e:
            print(f"Error controlling distribution pump: {e}")
            return {'status': 'error', 'message': str(e)}

    def get_well_pump_state(self) -> bool:
        """Get current well pump state"""
        return GPIOManager.get_pump_state(WELL_PUMP)

    def get_distribution_pump_state(self) -> bool:
        """Get current distribution pump state"""
        return GPIOManager.get_pump_state(DIST_PUMP)

    def get_pump_states(self) -> dict:
        """Get current states of both pumps"""
        try:
            well_state = self.get_well_pump_state()
            dist_state = self.get_distribution_pump_state()
        
            return {
                'well_pump': {
                    'state': 'ON' if well_state else 'OFF'
                },
                'distribution_pump': {
                    'state': 'ON' if dist_state else 'OFF'
                }
            }
        except Exception as e:
            print(f"Error getting system state: {e}")
            return {
                'well_pump': {'state': 'ERROR'},
                'distribution_pump': {'state': 'ERROR'},
                'tank_state': {'state': 'ERROR'}
            }

    def get_system_state(self) -> dict:
        """Get current system state"""
        try:
            if not self.is_running:
                if not self.start():
                    return {
                        'well_pump': {'state': 'ERROR'},
                        'distribution_pump': {'state': 'ERROR'},
                        'tank_state': {'state': 'ERROR'}
                    }

            # Get pump stats
            pump_stats = {
                'well_pump': StatsManager.get_pump_stats('well_pump'),
                'dist_pump': StatsManager.get_pump_stats('dist_pump')
            }

            # Get pump configuration
            pump_config = StatsManager.get_config()

            return {
                'well_pump': {
                    'state': 'ON' if self.get_well_pump_state() else 'OFF'
                },
                'distribution_pump': {
                    'state': 'ON' if self.get_distribution_pump_state() else 'OFF'
                },
                'thread_running': self.pump_thread.is_alive() if self.pump_thread else False,
                'pump_stats': pump_stats,
                'pump_config': pump_config
            }

        except Exception as e:
            print(f"Error getting system state: {e}")
            return {
                'well_pump': {'state': 'ERROR'},
                'distribution_pump': {'state': 'ERROR'},
                'tank_state': {'state': 'ERROR'}
            }

    @property
    def is_running(self):
        """Check if pump controller is running"""
        return self.running and (self.pump_thread and self.pump_thread.is_alive())
