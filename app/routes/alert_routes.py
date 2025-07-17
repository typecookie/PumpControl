from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required
from ..models.user import operator_required
from ..utils.notification_config import AlertConfig, AlertChannel, AlertType
from ..services.notification_service import NotificationService

bp = Blueprint('alert_api', __name__, url_prefix='/api/alerts')

@bp.route('/config', methods=['GET'])
@login_required
@operator_required
def get_alert_config():
    """Get current alert configuration"""
    try:
        config = AlertConfig()
        
        # Convert configuration to JSON-serializable format
        alert_config = {
            'channels': {
                channel.value: conf 
                for channel, conf in config.channels.items()
            },
            'alert_types': {
                alert_type.value: [c.value for c in channels]
                for alert_type, channels in config.alert_types.items()
            },
            'rate_limits': {
                alert_type.value: seconds
                for alert_type, seconds in config.rate_limits.items()
            }
        }
        
        return jsonify({
            'status': 'success',
            'config': alert_config
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting alert config: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error getting configuration: {str(e)}'
        }), 500

@bp.route('/channels', methods=['POST'])
@login_required
@operator_required
def configure_channels():
    """Configure notification channels"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No configuration data provided'
            }), 400

        current_app.logger.debug(f"Configuring channel with data: {data}")
        
        channel_name = data.get('channel')
        channel_config = data.get('config')
        
        if not channel_name or not channel_config:
            return jsonify({
                'status': 'error',
                'message': 'Missing channel name or configuration'
            }), 400

        # Convert channel name to enum
        channel = AlertChannel(channel_name)
        
        # Initialize config and add channel
        config = AlertConfig()
        config.add_channel(channel, channel_config)
        
        return jsonify({
            'status': 'success',
            'message': f'Channel {channel.value} configured successfully'
        })
        
    except ValueError as e:
        current_app.logger.error(f"ValueError in configure_channels: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error in configure_channels: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error configuring channel: {str(e)}'
        }), 500

@bp.route('/alert-types', methods=['POST'])
@login_required
@operator_required
def configure_alert_types():
    """Configure alert type settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No configuration data provided'
            }), 400

        current_app.logger.debug(f"Configuring alert type with data: {data}")
        
        alert_type_name = data.get('alert_type')
        channels = data.get('channels', [])
        rate_limit = data.get('rate_limit', 0)
        
        if not alert_type_name:
            return jsonify({
                'status': 'error',
                'message': 'Missing alert type'
            }), 400

        # Convert alert type and channels to enums
        alert_type = AlertType(alert_type_name)
        channel_enums = [AlertChannel(c) for c in channels]
        
        # Initialize config and configure alert type
        config = AlertConfig()
        config.configure_alert(alert_type, channel_enums)
        
        if rate_limit is not None:
            config.set_rate_limit(alert_type, int(rate_limit))
        
        return jsonify({
            'status': 'success',
            'message': f'Alert type {alert_type.value} configured successfully'
        })
        
    except ValueError as e:
        current_app.logger.error(f"ValueError in configure_alert_types: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        current_app.logger.error(f"Error in configure_alert_types: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error configuring alert type: {str(e)}'
        }), 500

@bp.route('/test', methods=['POST'])
@login_required
@operator_required
def test_alert():
    """Send a test alert to a specified channel"""
    try:
        data = request.get_json()
        current_app.logger.debug(f"Received test alert request with data: {data}")
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data received'
            }), 400
            
        channel_name = data.get('channel')
        if not channel_name:
            return jsonify({
                'status': 'error',
                'message': 'No channel specified'
            }), 400
            
        current_app.logger.debug(f"Attempting to create channel from: {channel_name}")
        channel = AlertChannel(channel_name)
        
        # Initialize notification service
        current_app.logger.debug("Initializing notification service")
        notification_service = NotificationService()
        
        # Send a test message
        current_app.logger.debug(f"Sending test message to channel: {channel}")
        result = notification_service.send_test_message(
            channel,
            "Test alert message from Pump Control System"
        )
        
        if result:
            return jsonify({
                'status': 'success',
                'message': f'Test alert sent successfully to {channel.value}'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to send test alert to {channel.value}'
            }), 500
            
    except ValueError as e:
        current_app.logger.error(f"ValueError in test_alert: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Invalid channel specified: {str(e)}'
        }), 400
    except Exception as e:
        current_app.logger.error(f"Unexpected error in test_alert: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error sending test alert: {str(e)}'
        }), 500