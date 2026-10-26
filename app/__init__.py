"""
Electricity Bill Prediction Application Package
"""
import os
from flask import Flask
from app.config import Config
from app.models import db


def create_app(config_class=Config):
    """
    Application Factory Pattern for Flask.
    Configures SQLAlchemy, registers blueprints/routes, and creates database tables.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Ensure instance and trained_models directories exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "..", "trained_models"), exist_ok=True)

    with app.app_context():
        # Create database tables if they do not exist
        db.create_all()

    return app
