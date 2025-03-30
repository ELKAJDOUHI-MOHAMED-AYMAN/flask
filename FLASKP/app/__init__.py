from flask import Flask, send_from_directory
from .extensions import db, login_manager, cache, migrate
from .config import Config
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'],
            filename
        )
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    cache.init_app(app)
    migrate.init_app(app, db)
    
    # Import blueprints
    from .controllers.auth import auth_bp
    from .controllers.main import main_bp
    from .controllers.admin import admin_bp
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app