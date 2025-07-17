from enum import Enum
from typing import List, Dict, Optional
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class AlertChannel(Enum):
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"

class AlertType(Enum):
    TANK_ERROR = "tank_error"               # When tank sensors report error state
    PUMP_ERROR = "pump_error"               # When pump operation fails
    TANK_EMPTY = "tank_empty"               # When summer tank is empty
    TANK_LOW = "tank_low"                   # When either tank reaches low state
    TANK_HIGH = "tank_high"                 # When either tank reaches high state
    TANK_STATE_CHANGE = "tank_state_change" # Any tank state change
    MODE_CHANGE = "mode_change"             # System mode changes (summer/winter/changeover)
    SYSTEM_ERROR = "system_error"           # General system errors
    PUMP_STATE_CHANGE = "pump_state_change" # When pumps turn on/off

class AlertConfig:
    def __init__(self, config_dir: str = None):
        """Initialize alert configuration
        
        Args:
            config_dir: Optional directory for config file. Defaults to app config directory.
        """
        if config_dir is None:
            config_dir = os.path.join(os.path.expanduser('~'), '.pump_control')
        
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / 'alert_config.json'
        
        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Initialize empty configuration
        self.channels: Dict[AlertChannel, Dict] = {}
        self.alert_types: Dict[AlertType, List[AlertChannel]] = {}
        self.rate_limits: Dict[AlertType, int] = {}  # Minimum seconds between alerts of same type
        
        # Load existing configuration
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    
                    # Load channel configurations
                    if 'channels' in data:
                        for channel, config in data['channels'].items():
                            try:
                                self.channels[AlertChannel(channel)] = config
                            except ValueError as e:
                                logger.error(f"Invalid channel type in config: {channel}")
                    
                    # Load alert type configurations
                    if 'alert_types' in data:
                        for alert_type, channels in data['alert_types'].items():
                            try:
                                self.alert_types[AlertType(alert_type)] = [
                                    AlertChannel(c) for c in channels
                                ]
                            except ValueError as e:
                                logger.error(f"Invalid alert type in config: {alert_type}")
                    
                    # Load rate limits
                    if 'rate_limits' in data:
                        for alert_type, seconds in data['rate_limits'].items():
                            try:
                                self.rate_limits[AlertType(alert_type)] = int(seconds)
                            except ValueError as e:
                                logger.error(f"Invalid rate limit in config: {alert_type}")
            else:
                logger.info("No alert configuration file found. Using empty configuration.")
                self._create_default_config()
        except Exception as e:
            logger.error(f"Error loading alert configuration: {e}")
            self._create_default_config()

    def _create_default_config(self):
        """Create a default configuration"""
        self.channels = {}
        self.alert_types = {alert_type: [] for alert_type in AlertType}
        self.rate_limits = {alert_type: 0 for alert_type in AlertType}
        self.save_config()

    def save_config(self) -> None:
        """Save current configuration to file"""
        try:
            data = {
                'channels': {
                    channel.value: config 
                    for channel, config in self.channels.items()
                },
                'alert_types': {
                    alert_type.value: [c.value for c in channels]
                    for alert_type, channels in self.alert_types.items()
                },
                'rate_limits': {
                    alert_type.value: seconds
                    for alert_type, seconds in self.rate_limits.items()
                }
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=4)
                
        except Exception as e:
            logger.error(f"Error saving alert configuration: {e}")
            raise

    def add_channel(self, channel: AlertChannel, config: Dict) -> None:
        """Add or update a notification channel configuration"""
        if not self._validate_channel_config(channel, config):
            raise ValueError(f"Invalid configuration for channel {channel}")
        
        self.channels[channel] = config
        self.save_config()

    def remove_channel(self, channel: AlertChannel) -> None:
        """Remove a notification channel"""
        if channel in self.channels:
            del self.channels[channel]
            # Remove this channel from all alert types
            for alert_type in self.alert_types:
                if channel in self.alert_types[alert_type]:
                    self.alert_types[alert_type].remove(channel)
            self.save_config()

    def configure_alert(self, alert_type: AlertType, channels: List[AlertChannel]) -> None:
        """Configure which channels should receive which types of alerts"""
        # Validate that all channels exist
        for channel in channels:
            if channel not in self.channels:
                raise ValueError(f"Channel {channel} not configured")
        
        self.alert_types[alert_type] = channels
        self.save_config()

    def set_rate_limit(self, alert_type: AlertType, seconds: int) -> None:
        """Set the minimum time between alerts of the same type"""
        if seconds < 0:
            raise ValueError("Rate limit cannot be negative")
        
        self.rate_limits[alert_type] = seconds
        self.save_config()

    def get_channels_for_alert(self, alert_type: AlertType) -> List[AlertChannel]:
        """Get list of channels configured for an alert type"""
        return self.alert_types.get(alert_type, [])

    def get_channel_config(self, channel: AlertChannel) -> Optional[Dict]:
        """Get configuration for a specific channel"""
        return self.channels.get(channel)

    def get_rate_limit(self, alert_type: AlertType) -> int:
        """Get the rate limit for an alert type"""
        return self.rate_limits.get(alert_type, 0)

    def _validate_channel_config(self, channel: AlertChannel, config: Dict) -> bool:
        """Validate channel-specific configuration"""
        try:
            if channel == AlertChannel.EMAIL:
                required = ['smtp_server', 'smtp_port', 'username', 'password', 
                          'from_email', 'to_emails']
                return all(key in config for key in required)
                
            elif channel == AlertChannel.SLACK:
                return 'webhook_url' in config
                
            elif channel == AlertChannel.DISCORD:
                return 'webhook_url' in config
                
            return False
            
        except Exception as e:
            logger.error(f"Error validating channel config: {e}")
            return False