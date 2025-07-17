from flask import Blueprint, render_template, current_app
from flask_login import login_required
from ..controllers import pump_controller
from ..utils.config_utils import MODES
from ..models.user import UserRole  # Add this import
import logging

bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

@bp.route('/')
@login_required
def index():
    try:
        state = pump_controller.get_system_state()
        return render_template('index.html',
                             current_mode=state.get('current_mode', 'Unknown'),
                             available_modes=MODES,
                             summer_tank_state=state.get('summer_tank', {}).get('state', 'Unknown'),
                             winter_tank_state=state.get('winter_tank', {}).get('state', 'Unknown'),
                             well_pump_status=state.get('well_pump_status', 'Unknown'),
                             dist_pump_status=state.get('dist_pump_status', 'Unknown'),
                             summer_tank_stats=state.get('summer_tank', {}).get('stats', {}),
                             winter_tank_stats=state.get('winter_tank', {}).get('stats', {}),
                             thread_running=state.get('thread_running', False),
                             UserRole=UserRole)  # Add this line
    except Exception as e:
        logger.error(f"Error in index route: {e}", exc_info=True)
        return render_template('index.html',
                             current_mode='Error',
                             available_modes=MODES,
                             summer_tank_state='Error',
                             winter_tank_state='Error',
                             well_pump_status='Error',
                             dist_pump_status='Error',
                             summer_tank_stats={},
                             winter_tank_stats={},
                             thread_running=False,
                             UserRole=UserRole)  # Add this line