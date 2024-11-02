from flask import Flask, jsonify
import os
from src.auth import auth
from src.foods import foods
from src.log import log
from src.user import user
from src.database import db
from flask_jwt_extended import JWTManager
from src.constants.http_status_code import *

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration from environment or test config
    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=os.environ.get("SECRET_KEY"),
            SQLALCHEMY_DATABASE_URI=os.environ.get("SQLALCHEMY_DB_URI"),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            JWT_SECRET_KEY=os.environ.get('JWT_SECRET_KEY')
        )
    else:
        app.config.from_mapping(test_config)

    # Initialize database and JWT
    db.init_app(app)
    JWTManager(app)

    # Register blueprints
    app.register_blueprint(auth)
    app.register_blueprint(foods)
    app.register_blueprint(log)
    app.register_blueprint(user)

    with app.app_context():
        db.create_all()

    @app.errorhandler(HTTP_404_NOT_FOUND)
    def handle_404(e):
        return jsonify({'error': 'Not found'}), HTTP_404_NOT_FOUND

    @app.errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
    def handle_500(e):
        return jsonify({'error': 'Something went wrong, we are working on it'}), HTTP_500_INTERNAL_SERVER_ERROR

    return app
