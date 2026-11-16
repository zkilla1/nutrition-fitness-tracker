import os

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from .extensions import db


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=normalize_db_url(os.environ.get("DATABASE_URL", "sqlite:///nutrition.db")),
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-insecure-key-change-me-in-production"),
        TOKEN_TTL_HOURS=int(os.environ.get("TOKEN_TTL_HOURS", "24")),
        CORS_ORIGINS=os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(","),
    )
    if config:
        app.config.update(config)

    db.init_app(app)
    CORS(app, origins=app.config["CORS_ORIGINS"])

    from .routes import auth_bp, foods_bp, meals_bp, profile_bp, summary_bp, workouts_bp

    for bp in (auth_bp, profile_bp, foods_bp, meals_bp, workouts_bp, summary_bp):
        app.register_blueprint(bp)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return jsonify(error=err.description), err.code

    with app.app_context():
        from .seed import seed_foods

        db.create_all()
        seed_foods()

    return app


def normalize_db_url(url):
    """Accept postgres:// URLs (Heroku/Render style) and use the psycopg 3 driver."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url
