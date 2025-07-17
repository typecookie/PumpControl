from flask import Flask
from flask_login import LoginManager
from .utils.gpio_utils import GPIOManager
from .controllers.pump_controller import PumpController
from .controllers import Controller
from .utils.user_manager import UserManager

# Initialize singleton controller
pump_controller = PumpController()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this!

    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Initialize default users
    UserManager.init_default_users()

    @login_manager.user_loader
    def load_user(user_id):
        return UserManager.get_user_by_id(int(user_id))

    with app.app_context():
        # Initialize hardware
        GPIOManager.initialize()

        # Register blueprints
        from .routes.main_routes import bp as main_bp
        from .routes.api_routes import bp as api_bp
        from .routes.auth_routes import bp as auth_bp

        app.register_blueprint(main_bp)
        app.register_blueprint(api_bp, url_prefix='/api')
        app.register_blueprint(auth_bp, url_prefix='/auth')

    return app


__all__ = ['create_app', 'pump_controller']