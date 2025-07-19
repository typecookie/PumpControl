from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required
from ..models.user import operator_required
from ..utils.notification_config import AlertConfig, AlertType, AlertChannel

# Change the blueprint name to be unique
bp = Blueprint('alerts_config_api', __name__, url_prefix='/api/alerts')

@bp.route('/config', methods=['GET'])
@login_required
@operator_required
def get_alert_config():
    """Get current alert configuration"""
    try:
        config = AlertConfig()
        alert_config = config.get_serializable_config()
        
        return jsonify({
            'status': 'success',
            **alert_config  # Spread the config directly into response
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting alert config: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'channels': {},
            'alert_types': {},
            'rate_limits': {}
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
            
        channel_name = data.get('channel')
        config_data = data.get('config', {})
        
        if not channel_name:
            return jsonify({
                'status': 'error',
                'message': 'Missing channel name'
            }), 400
            
        config = AlertConfig()
        channel = AlertChannel(channel_name)
        config.add_channel(channel, config_data)
        
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

@bp.route('/types', methods=['POST'])
@login_required
@operator_required
def configure_alert_types():
    """Configure alert type settings"""
    try:
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Content-Type must be application/json'
            }), 400

        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No configuration data provided'
            }), 400

        current_app.logger.debug(f"Configuring alert type with data: {data}")
        
        alert_type_name = data.get('alert_type')
        channels = data.get('channels', [])
        
        if not alert_type_name:
            return jsonify({
                'status': 'error',
                'message': 'Missing alert type'
            }), 400

        try:
            # Find matching enum by value instead of name
            alert_type = None
            for at in AlertType:
                if at.value == alert_type_name:
                    alert_type = at
                    break
                    
            if alert_type is None:
                raise ValueError(f"Invalid alert type: {alert_type_name}")
                
            channel_enums = [AlertChannel(c) for c in channels]
            
            config = AlertConfig()
            config.configure_alert(alert_type, channel_enums)
            
            return jsonify({
                'status': 'success',
                'message': f'Alert type {alert_type.value} configured successfully'
            })
            
        except ValueError as e:
            current_app.logger.error(f"ValueError in configure_alert_types: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f"Invalid alert type or channel: {str(e)}"
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Error in configure_alert_types: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/test', methods=['POST'])
@login_required
@operator_required
def test_alert():
    """Send test notification to a channel"""
    try:
        data = request.get_json()
        if not data or 'channel' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Channel not specified'
            }), 400
            
        channel = AlertChannel(data['channel'])
        config = AlertConfig()
        
        if channel not in config.channels:
            return jsonify({
                'status': 'error',
                'message': f'Channel {channel.value} not configured'
            }), 400
            
        from ..services.notification_service import NotificationService
        service = NotificationService()
        success = service.send_test_message(
            channel,
            "This is a test message from the Water System Alert Configuration"
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Test message sent to {channel.value}'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to send test message to {channel.value}'
            }), 500
        
    except Exception as e:
        current_app.logger.error(f"Error sending test alert: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error sending test: {str(e)}'
        }), 500