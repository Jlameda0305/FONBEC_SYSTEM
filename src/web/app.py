"""
Flask Application Factory.

Initializes the Flask app, configures database session lifecycle hooks,
and registers all Blueprints. This is the single entry point for the
web layer.
"""

import os

from flask import Flask, g

from src.infrastructure.database import SessionLocal, init_db


def create_app() -> Flask:
    """
    Create and configure the Flask application.

    Returns:
        A fully configured Flask instance with registered blueprints
        and database session middleware.
    """
    # Resolve template and static folder paths relative to the src directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(base_dir, "templates")
    static_dir = os.path.join(base_dir, "static")

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
    )
    
    # Required for flash() messages and session management
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-fonbec-1234")

    # --- Database Initialization ---
    # Initialize the imperative mapping and sync tables once at startup.
    with app.app_context():
        init_db()

    # --- Request Lifecycle: Database Session ---
    @app.before_request
    def _open_db_session() -> None:
        """Create a fresh SQLAlchemy session for each HTTP request."""
        g.db_session = SessionLocal()

    @app.teardown_appcontext
    def _close_db_session(exception=None) -> None:
        """Close the SQLAlchemy session when the request ends."""
        session = g.pop("db_session", None)
        if session is not None:
            session.close()

    # --- Register Blueprints ---
    from src.web.routes.becario import becario_bp
    from src.web.routes.tutor import tutor_bp
    from src.web.routes.admin import admin_bp
    app.register_blueprint(becario_bp)
    app.register_blueprint(tutor_bp)
    app.register_blueprint(admin_bp)

    # --- Default Route ---
    from flask import redirect, url_for
    @app.route("/")
    def index():
        return redirect(url_for("becario.visualizar_academico"))

    return app
