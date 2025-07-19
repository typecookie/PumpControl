from flask import Blueprint, render_template, current_app
from flask_login import login_required
from ..models.user import operator_required, UserRole
from ..utils.notification_config import AlertType, AlertChannel

# Change the blueprint name to be unique
bp = Blueprint('alerts_config_ui', __name__, url_prefix='/alerts/ui')

@bp.route('/config', methods=['GET'])
@login_required
@operator_required
def alerts_config_page():
    try:
        return render_template(
            'alerts_config.html',
            alert_types=AlertType,
            channels=AlertChannel,
            UserRole=UserRole
        )
    except Exception as e:
        current_app.logger.error(f"Error rendering alerts config page: {str(e)}")
        return f"Error loading configuration page: {str(e)}", 500