# app/routes/__init__.py
from . import main_routes, api_routes

def init_app(app):
    """Initialize routes with the app"""
    app.register_blueprint(main_routes.bp)
    app.register_blueprint(api_routes.bp)