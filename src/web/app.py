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
    # --- Dummy Login Routes (For Development) ---
    from flask import redirect, url_for, render_template, session
    from src.domain.actors.becario import Becario
    from src.domain.actors.tutor import Tutor
    from src.domain.actors.mediador import Mediador
    from src.domain.actors.administrador import Administrador
    from src.domain.domain_entities.padrino import Padrino
    
    @app.route("/")
    def index():
        # Get DB session from g (since this runs within request context)
        db = g.db_session
        
        usuarios = {
            "administrador": db.query(Administrador).all(),
            "becario": db.query(Becario).all(),
            "tutor": db.query(Tutor).all(),
            "mediador": db.query(Mediador).all(),
            "padrino": db.query(Padrino).all(),
        }
        
        return render_template("login.html", usuarios=usuarios, session=session)

    @app.route("/login/<user_id>/<rol>")
    def set_login(user_id, rol):
        session["user_id"] = user_id
        
        # Redirigir según rol
        if rol == "administrador":
            return redirect(url_for("admin.dashboard"))
        elif rol == "becario":
            return redirect(url_for("becario.visualizar_academico"))
        elif rol == "tutor":
            return redirect(url_for("tutor.dashboard"))
        else:
            return redirect(url_for("index"))

    @app.route("/logout")
    def logout():
        session.pop("user_id", None)
        return redirect(url_for("index"))

    return app
