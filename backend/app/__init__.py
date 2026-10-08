from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy import text

from .config import Config
from .models import db
from .career_api import career_api
from .auth_api import auth_api


jwt = JWTManager()


def create_app():
    app = Flask(__name__)

    # -------------------------------------------------
    # Application configuration
    # -------------------------------------------------

    app.config.from_object(Config)

    # -------------------------------------------------
    # JWT configuration
    # -------------------------------------------------

    jwt.init_app(app)

    # -------------------------------------------------
    # CORS
    # -------------------------------------------------

    CORS(app)

    # -------------------------------------------------
    # Database
    # -------------------------------------------------

    db.init_app(app)

    # -------------------------------------------------
    # API blueprints
    # -------------------------------------------------

    app.register_blueprint(auth_api)
    app.register_blueprint(career_api)

    # -------------------------------------------------
    # Create database tables
    # -------------------------------------------------

    with app.app_context():
        db.create_all()

    # -------------------------------------------------
    # Home
    # -------------------------------------------------

    @app.route("/", methods=["GET"])
    def home():
        return {
            "message": "CareerPilot AI Backend is running!",
            "status": "success"
        }

    # -------------------------------------------------
    # Health
    # -------------------------------------------------

    @app.route("/health", methods=["GET"])
    def health():
        return {
            "status": "healthy"
        }

    # -------------------------------------------------
    # Database test
    # -------------------------------------------------

    @app.route("/db-test", methods=["GET"])
    def db_test():
        try:
            db.session.execute(
                text("SELECT 1")
            )

            return {
                "database": "connected",
                "status": "success"
            }

        except Exception as e:

            return {
                "database": "connection failed",
                "status": "error",
                "error": str(e)
            }, 500

    return app