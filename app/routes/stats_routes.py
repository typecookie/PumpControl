from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from ..models.user import UserRole, operator_required
from ..utils.stats_manager import StatsManager
from ..controllers import pump_controller

bp = Blueprint('stats', __name__, url_prefix='/stats')

@bp.route('/')
@login_required
def stats_dashboard():
    """Stats dashboard page"""
    try:
        # Get current pump stats
        pump_stats = StatsManager.get_pump_stats()
        
        # Get pump configuration
        pump_config = StatsManager.get_config()
        
        # Get tank states history
        tank_history = {
            'summer': StatsManager.get_tank_history('summer', max_entries=20),
            'winter': StatsManager.get_tank_history('winter', max_entries=20)
        }
        
        # Get current tank states
        current_tank_states = StatsManager.get_current_tank_states()
        
        return render_template('stats/dashboard.html', 
                              pump_stats=pump_stats,
                              pump_config=pump_config,
                              tank_history=tank_history,
                              current_tank_states=current_tank_states,
                              UserRole=UserRole)
    except Exception as e:
        print(f"Error in stats dashboard: {e}")
        import traceback
        print(traceback.format_exc())
        flash(f"Error loading stats: {str(e)}", "error")
        return render_template('stats/dashboard.html', 
                              pump_stats={},
                              pump_config={},
                              tank_history={},
                              current_tank_states={},
                              UserRole=UserRole)

@bp.route('/config', methods=['GET', 'POST'])
@login_required
@operator_required
def pump_config():
    """Pump configuration page"""
    if request.method == 'POST':
        try:
            # Update flow rates
            well_gpm = float(request.form.get('well_pump_gpm', 40.0))
            dist_gpm = float(request.form.get('dist_pump_gpm', 15.0))
            
            if well_gpm <= 0 or dist_gpm <= 0:
                flash("Flow rates must be positive numbers", "warning")
                return redirect(url_for('stats.pump_config'))
            
            config = StatsManager.update_pump_config(well_gpm=well_gpm, dist_gpm=dist_gpm)
            flash("Pump configuration updated successfully", "success")
            
            return redirect(url_for('stats.stats_dashboard'))
        except ValueError:
            flash("Invalid values provided. Flow rates must be numbers.", "error")
        except Exception as e:
            flash(f"Error updating configuration: {str(e)}", "error")
    
    # Get current configuration
    pump_config = StatsManager.get_config()
    
    return render_template('stats/config.html', 
                         pump_config=pump_config,
                         UserRole=UserRole)

@bp.route('/api/pump_stats')
@login_required
def api_pump_stats():
    """API endpoint to get pump stats"""
    try:
        pump_stats = StatsManager.get_pump_stats()
        return jsonify({
            'status': 'success',
            'data': pump_stats
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/api/tank_history')
@login_required
def api_tank_history():
    """API endpoint to get tank history"""
    try:
        tank_name = request.args.get('tank')
        max_entries = int(request.args.get('max_entries', 20))
        
        if tank_name:
            history = StatsManager.get_tank_history(tank_name, max_entries=max_entries)
        else:
            history = StatsManager.get_tank_history(max_entries=max_entries)
            
        current_states = StatsManager.get_current_tank_states()
        
        return jsonify({
            'status': 'success',
            'history': history,
            'current_states': current_states
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500