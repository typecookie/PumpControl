from flask import Flask
from app.routes.main_routes import bp as main_bp
from app.routes.api_routes import bp as api_bp
from app.utils.gpio_utils import GPIOManager  # Add this import

def create_app():
    app = Flask(__name__,
                template_folder='templates',    # Explicitly set template folder
                static_folder='static')         # Explicitly set static folder
    
    # Configure the app
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # Initialize GPIO
    with app.app_context():
        GPIOManager.initialize()  # Initialize GPIO before any routes are called
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app