import smtplib
from email.mime.text import MIMEText
import requests
import json
import time
import logging
import threading
from ..utils.notification_config import AlertConfig, AlertChannel, AlertType

logger = logging.getLogger(__name__)

class NotificationService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NotificationService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.config = AlertConfig()
        self.last_alert_times = {}  # Track last alert time for rate limiting
        self._initialized = True

    def send_alert(self, alert_type: AlertType, message: str, data: dict = None):
        """Send an alert through configured channels
        
        Args:
            alert_type: Type of alert (from AlertType enum)
            message: Alert message
            data: Optional dictionary of additional data
        """
        try:
            channels = self.config.get_channels_for_alert(alert_type)
            
            if not channels:
                logger.warning(f"No channels configured for alert type: {alert_type}")
                return

            # Check rate limiting
            current_time = time.time()
            alert_key = f"{alert_type.value}"
            
            with self._lock:
                last_time = self.last_alert_times.get(alert_key, 0)
                rate_limit = self.config.get_rate_limit(alert_type)
                
                if current_time - last_time < rate_limit:
                    logger.info(f"Rate limited alert: {alert_type}")
                    return
                
                self.last_alert_times[alert_key] = current_time

            # Prepare full message with data
            full_message = message
            if data:
                full_message += "\n\nDetails:\n" + "\n".join(f"{k}: {v}" for k, v in data.items())

            # Send through each configured channel
            for channel in channels:
                try:
                    channel_config = self.config.get_channel_config(channel)
                    if not channel_config:
                        continue

                    if channel == AlertChannel.EMAIL:
                        self._send_email(alert_type, full_message, channel_config)
                    elif channel == AlertChannel.SLACK:
                        self._send_slack(alert_type, full_message, channel_config)
                    elif channel == AlertChannel.DISCORD:
                        self._send_discord(alert_type, full_message, channel_config)

                except Exception as e:
                    logger.error(f"Error sending {channel} alert: {e}")

        except Exception as e:
            logger.error(f"Error in send_alert: {e}")

    def _send_email(self, alert_type: AlertType, message: str, config: dict):
        """Send email alert"""
        try:
            msg = MIMEText(message)
            msg['Subject'] = f'Water System Alert: {alert_type.value}'
            msg['From'] = config['from_email']
            msg['To'] = ', '.join(config['to_emails'])

            with smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port']) as server:
                server.login(config['username'], config['password'])
                server.send_message(msg)

            logger.info(f"Email alert sent: {alert_type}")

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise

    def _send_slack(self, alert_type: AlertType, message: str, config: dict):
        """Send Slack alert"""
        try:
            payload = {
                "text": f"*Water System Alert: {alert_type.value}*\n{message}"
            }

            response = requests.post(
                config['webhook_url'],
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code != 200:
                raise Exception(f"Slack API error: {response.status_code} - {response.text}")

            logger.info(f"Slack alert sent: {alert_type}")

        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
            raise

    def _send_discord(self, alert_type: AlertType, message: str, config: dict):
        """Send Discord alert"""
        try:
            payload = {
                "content": f"**Water System Alert: {alert_type.value}**\n{message}"
            }

            response = requests.post(
                config['webhook_url'],
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code != 204:  # Discord returns 204 on success
                raise Exception(f"Discord API error: {response.status_code} - {response.text}")

            logger.info(f"Discord alert sent: {alert_type}")

        except Exception as e:
            logger.error(f"Error sending Discord alert: {e}")
            raise

    def send_test_message(self, channel: AlertChannel, message: str) -> bool:
        """Send a test message through a specific channel
        
        Args:
            channel: The channel to test
            message: Test message to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get channel config
            channel_config = self.config.get_channel_config(channel)
            if not channel_config:
                logger.error(f"Channel {channel} not configured")
                return False

            if channel == AlertChannel.EMAIL:
                self._send_email(AlertType.SYSTEM_ERROR, message, channel_config)
            elif channel == AlertChannel.SLACK:
                self._send_slack(AlertType.SYSTEM_ERROR, message, channel_config)
            elif channel == AlertChannel.DISCORD:
                self._send_discord(AlertType.SYSTEM_ERROR, message, channel_config)
            else:
                logger.error(f"Unknown channel type: {channel}")
                return False
                
            return True

        except Exception as e:
            logger.error(f"Error sending test message: {e}")
            return False