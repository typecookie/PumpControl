from flask import Flask
from .utils.gpio_utils import GPIOManager
from .controllers.pump_controller import PumpController

# Initialize singleton controller
pump_controller = PumpController()

def create_app():
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    with app.app_context():
        # Initialize hardware
        GPIOManager.initialize()
        
        # Register blueprints
        from .routes.main_routes import bp as main_bp
        from .routes.api_routes import bp as api_bp
        
        app.register_blueprint(main_bp)
        app.register_blueprint(api_bp, url_prefix='/api')
    
    return app

__all__ = ['create_app', 'pump_controller']