import os
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict

class StatsManager:
    """Manager for statistics collection and persistence"""
    
    # File paths for stats
    _stats_dir = os.path.join(os.path.expanduser('~'), '.pump_control')
    _pump_stats_file = os.path.join(_stats_dir, 'pump_stats.json')
    _tank_history_file = os.path.join(_stats_dir, 'tank_history.json')
    _config_file = os.path.join(_stats_dir, 'stats_config.json')
    
    # Default config
    _default_config = {
        'well_pump_gpm': 40.0,
        'dist_pump_gpm': 15.0,
        'reset_hour': 0  # Hour of day when daily stats reset (midnight)
    }
    
    # Runtime data
    _pump_stats = {
        'well_pump': {
            'today': {'runtime': 0, 'volume': 0},
            'week': {'runtime': 0, 'volume': 0},
            'month': {'runtime': 0, 'volume': 0},
            'year': {'runtime': 0, 'volume': 0},
            'total': {'runtime': 0, 'volume': 0},
            'last_active': None
        },
        'dist_pump': {
            'today': {'runtime': 0, 'volume': 0},
            'week': {'runtime': 0, 'volume': 0},
            'month': {'runtime': 0, 'volume': 0}, 
            'year': {'runtime': 0, 'volume': 0},
            'total': {'runtime': 0, 'volume': 0},
            'last_active': None
        }
    }
    
    # Last reset timestamps
    _last_reset = {
        'day': None,
        'week': None,
        'month': None,
        'year': None
    }
    
    # Tank state history
    _tank_history = {
        'summer': [],  # List of {state, start_time, duration}
        'winter': []
    }
    
    # Current tank states
    _current_tank_states = {
        'summer': {'state': 'unknown', 'since': None},
        'winter': {'state': 'unknown', 'since': None}
    }
    
    _config = _default_config.copy()
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize the stats manager"""
        if cls._initialized:
            return
        
        os.makedirs(cls._stats_dir, exist_ok=True)
        cls._load_config()
        cls._load_pump_stats()
        cls._load_tank_history()
        cls._check_reset_periods()
        cls._initialized = True
    
    @classmethod
    def _load_config(cls):
        """Load configuration from file"""
        try:
            if os.path.exists(cls._config_file):
                with open(cls._config_file, 'r') as f:
                    config = json.load(f)
                    # Update with loaded values but keep defaults for missing keys
                    for key, value in config.items():
                        cls._config[key] = value
                    print(f"Loaded stats config: {cls._config}")
            else:
                cls._save_config()  # Save defaults
        except Exception as e:
            print(f"Error loading stats config: {e}")
    
    @classmethod
    def _save_config(cls):
        """Save configuration to file"""
        try:
            with open(cls._config_file, 'w') as f:
                json.dump(cls._config, f, indent=4)
        except Exception as e:
            print(f"Error saving stats config: {e}")
    
    @classmethod
    def _load_pump_stats(cls):
        """Load pump statistics from file"""
        try:
            if os.path.exists(cls._pump_stats_file):
                with open(cls._pump_stats_file, 'r') as f:
                    data = json.load(f)
                    # Update pump stats
                    for pump_name, stats in data.get('pump_stats', {}).items():
                        if pump_name in cls._pump_stats:
                            cls._pump_stats[pump_name] = stats
                    
                    # Update reset timestamps
                    for period, timestamp in data.get('last_reset', {}).items():
                        cls._last_reset[period] = timestamp
                        
                    print("Pump stats loaded successfully")
            else:
                # Initialize reset timestamps if file doesn't exist
                now = datetime.now().isoformat()
                for period in cls._last_reset:
                    cls._last_reset[period] = now
                cls._save_pump_stats()
        except Exception as e:
            print(f"Error loading pump stats: {e}")
    
    @classmethod
    def _save_pump_stats(cls):
        """Save pump statistics to file"""
        try:
            data = {
                'pump_stats': cls._pump_stats,
                'last_reset': cls._last_reset
            }
            with open(cls._pump_stats_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving pump stats: {e}")
    
    @classmethod
    def _load_tank_history(cls):
        """Load tank history from file"""
        try:
            if os.path.exists(cls._tank_history_file):
                with open(cls._tank_history_file, 'r') as f:
                    data = json.load(f)
                    cls._tank_history = data.get('history', cls._tank_history)
                    current_states = data.get('current_states', {})
                    for tank, state_info in current_states.items():
                        if tank in cls._current_tank_states:
                            cls._current_tank_states[tank] = state_info
                    print("Tank history loaded successfully")
        except Exception as e:
            print(f"Error loading tank history: {e}")
    
    @classmethod
    def _save_tank_history(cls):
        """Save tank history to file"""
        try:
            data = {
                'history': cls._tank_history,
                'current_states': cls._current_tank_states
            }
            with open(cls._tank_history_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving tank history: {e}")
    
    @classmethod
    def _check_reset_periods(cls):
        """Check if any stats periods need to be reset"""
        now = datetime.now()
        
        # Convert ISO string timestamps to datetime objects
        last_reset = {}
        for period, timestamp in cls._last_reset.items():
            if timestamp:
                try:
                    last_reset[period] = datetime.fromisoformat(timestamp)
                except (ValueError, TypeError):
                    last_reset[period] = now
            else:
                last_reset[period] = now
        
        # Check daily reset (at configured hour)
        if (now.day != last_reset.get('day', now).day or 
            now.month != last_reset.get('day', now).month or
            now.year != last_reset.get('day', now).year):
            if now.hour >= cls._config['reset_hour']:
                cls._reset_period('day')
        
        # Check weekly reset (on Monday)
        if now.weekday() == 0 and last_reset.get('week', now).weekday() != 0:
            cls._reset_period('week')
        
        # Check monthly reset (on the 1st)
        if now.day == 1 and last_reset.get('month', now).day != 1:
            cls._reset_period('month')
        
        # Check yearly reset (on Jan 1st)
        if now.day == 1 and now.month == 1 and (
            last_reset.get('year', now).day != 1 or last_reset.get('year', now).month != 1):
            cls._reset_period('year')
    
    @classmethod
    def _reset_period(cls, period):
        """Reset stats for a specific period"""
        print(f"Resetting {period} statistics")
        for pump_name in cls._pump_stats:
            if period in cls._pump_stats[pump_name]:
                cls._pump_stats[pump_name][period] = {'runtime': 0, 'volume': 0}
        
        cls._last_reset[period] = datetime.now().isoformat()
        
        # Trim tank history when resetting daily stats
        if period == 'day':
            # Keep only last 30 entries per tank
            for tank in cls._tank_history:
                cls._tank_history[tank] = cls._tank_history[tank][-30:]
        
        cls._save_pump_stats()
    
    @classmethod
    def update_pump_stats(cls, pump_name, running, elapsed_seconds):
        """Update pump runtime and volume stats
        
        Args:
            pump_name: Name of the pump ('well_pump' or 'dist_pump')
            running: Whether the pump is running
            elapsed_seconds: Seconds since last update
        """
        if not cls._initialized:
            cls.initialize()
            
        if pump_name not in cls._pump_stats:
            return
        
        # Update last active timestamp if running
        if running:
            cls._pump_stats[pump_name]['last_active'] = datetime.now().isoformat()
            
            # Calculate volume based on GPM rate
            gpm = cls._config.get(f'{pump_name}_gpm', 
                                 40.0 if pump_name == 'well_pump' else 15.0)
            volume = (gpm / 60.0) * elapsed_seconds
            
            # Update all periods
            for period in ['today', 'week', 'month', 'year', 'total']:
                cls._pump_stats[pump_name][period]['runtime'] += elapsed_seconds
                cls._pump_stats[pump_name][period]['volume'] += volume
                
            # Save updated stats (every 5 minutes to reduce disk writes)
            total_runtime = cls._pump_stats[pump_name]['today']['runtime']
            if total_runtime % 300 < elapsed_seconds:
                cls._save_pump_stats()
                cls._check_reset_periods()
    
    @classmethod
    def update_tank_state(cls, tank_name, state):
        """Update the current state of a tank
        
        Args:
            tank_name: Name of the tank ('summer' or 'winter')
            state: Current state of the tank
        """
        if not cls._initialized:
            cls.initialize()
            
        if tank_name not in cls._current_tank_states:
            return
        
        now = datetime.now()
        current = cls._current_tank_states[tank_name]
        
        # If state has changed
        if current['state'] != state:
            # Record previous state duration if it exists
            if current['since']:
                try:
                    start_time = datetime.fromisoformat(current['since'])
                    duration = (now - start_time).total_seconds()
                    
                    # Add to history
                    cls._tank_history[tank_name].append({
                        'state': current['state'],
                        'start_time': current['since'],
                        'duration': duration,
                        'end_time': now.isoformat()
                    })
                    
                    # Save history (not too frequently)
                    if len(cls._tank_history[tank_name]) % 5 == 0:
                        cls._save_tank_history()
                except Exception as e:
                    print(f"Error updating tank history: {e}")
            
            # Update current state
            cls._current_tank_states[tank_name] = {
                'state': state,
                'since': now.isoformat()
            }
            cls._save_tank_history()
    
    @classmethod
    def get_pump_stats(cls, pump_name=None):
        """Get pump statistics
        
        Args:
            pump_name: Name of the pump, or None to get all stats
            
        Returns:
            Dict with pump statistics
        """
        if not cls._initialized:
            cls.initialize()
            
        if pump_name:
            return cls._pump_stats.get(pump_name, {})
        return cls._pump_stats
    
    @classmethod
    def get_tank_history(cls, tank_name=None, max_entries=10):
        """Get tank state history
        
        Args:
            tank_name: Name of the tank, or None to get all history
            max_entries: Maximum number of entries to return
            
        Returns:
            Dict with tank history
        """
        if not cls._initialized:
            cls.initialize()
            
        if tank_name:
            history = cls._tank_history.get(tank_name, [])
            return history[-max_entries:] if max_entries else history
        
        result = {}
        for tank, history in cls._tank_history.items():
            result[tank] = history[-max_entries:] if max_entries else history
        return result
    
    @classmethod
    def get_current_tank_states(cls):
        """Get current tank states with duration"""
        if not cls._initialized:
            cls.initialize()
            
        result = {}
        now = datetime.now()
        
        for tank, state_info in cls._current_tank_states.items():
            result[tank] = state_info.copy()
            if state_info['since']:
                try:
                    since = datetime.fromisoformat(state_info['since'])
                    result[tank]['duration'] = (now - since).total_seconds()
                except Exception:
                    result[tank]['duration'] = 0
            else:
                result[tank]['duration'] = 0
                
        return result
    
    @classmethod
    def update_pump_config(cls, well_gpm=None, dist_gpm=None):
        """Update pump flow rate configuration"""
        if not cls._initialized:
            cls.initialize()
            
        if well_gpm is not None:
            cls._config['well_pump_gpm'] = float(well_gpm)
        
        if dist_gpm is not None:
            cls._config['dist_pump_gpm'] = float(dist_gpm)
            
        cls._save_config()
        return cls._config
    
    @classmethod
    def get_config(cls):
        """Get current configuration"""
        if not cls._initialized:
            cls.initialize()
            
        return cls._config.copy()