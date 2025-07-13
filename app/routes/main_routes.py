# app/routes/main_routes.py
from flask import Blueprint, render_template
from app.controllers.pump_controller import PumpController
from app.config import MODES

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    controller = PumpController()
    try:
        state = controller.get_system_state()
        initial_state = {
            'current_mode': state['current_mode'],
            'available_modes': MODES,
            'summer_tank_state': state['summer_tank']['state'],
            'winter_tank_state': state['winter_tank']['state'],
            'well_pump_status': state['well_pump_status'],
            'dist_pump_status': state['dist_pump_status'],
            'active_tank': state['active_tank']
        }
        return render_template('index.html', **initial_state)
    except Exception as e:
        print(f"Error in index route: {e}")
        return render_template('index.html',
                           error=str(e),
                           current_mode='unknown',
                           available_modes=MODES,
                           summer_tank_state='unknown',
                           winter_tank_state='unknown',
                           well_pump_status='unknown',
                           dist_pump_status='unknown',
                           active_tank='none')