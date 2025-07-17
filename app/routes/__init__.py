from .main_routes import bp as main_bp
from .api_routes import bp as api_bp
from . import alert_routes, alerts_config

__all__ = ['main_bp', 'api_bp', 'alert_routes', 'alerts_config']