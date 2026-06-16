"""
Authentication HTTP Controller (Flask Blueprint).
"""

import logging
import traceback
from flask import Blueprint, request, redirect, url_for, flash, render_template, session, g

from src.infrastructure.database import get_supabase_client
from src.infrastructure.repositories import SQLAlchemyUsuarioRepository
from src.infrastructure.auth_service import SupabaseAuthService
from src.application.use_cases.login import LoginUseCase
from src.application.use_cases.completar_registro import CompletarRegistroUseCase

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET"])
def login():
    """
    GET /auth/login
    Renders the login form.
    """
    return render_template("auth/login.html")

@auth_bp.route("/login", methods=["POST"])
def login_post():
    """
    POST /auth/login
    Handles the login submission.
    """

    email = request.form.get("email")
    password = request.form.get("password")
    
    if not email or not password:
        flash("Email y contraseña requeridos.", "error")
        return redirect(url_for("auth.login"))
        
    try:
        auth_service = SupabaseAuthService(get_supabase_client())
        repo = SQLAlchemyUsuarioRepository(g.db_session)
        use_case = LoginUseCase(auth_service, repo)
        
        result = use_case.ejecutar(email, password)
        
        # Save session data
        session.permanent = True
        session["access_token"] = result["access_token"]
        session["refresh_token"] = result["refresh_token"]
        session["rol"] = result["rol"]
        session["user_id"] = result["usuario"].id_usuario
        
        # Routing based on role
        rol = result["rol"]
        if rol == "administrador":
            return redirect(url_for("admin.dashboard"))
        elif rol == "becario":
            return redirect(url_for("becario.dashboard"))
        elif rol == "tutor":
            return redirect(url_for("tutor.dashboard"))
        else:
            return redirect(url_for("index"))
            
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("auth.login"))
    except Exception as e:
        logging.error(f"Error during login: {e}")
        logging.error(traceback.format_exc())
        flash("Ocurrió un error inesperado durante el login.", "error")
        return redirect(url_for("auth.login"))

@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    """
    Clears the session and logs the user out.
    """
    session.clear()
    flash("Has cerrado sesión exitosamente.", "success")
    return redirect(url_for("auth.login"))

@auth_bp.route("/callback", methods=["GET", "POST"])
def callback():
    """
    GET/POST /auth/callback
    Endpoint for Supabase redirect after an invitation is accepted.
    In Implicit Flow, Supabase sends the token as a URL fragment (#access_token=...).
    Flask cannot read URL fragments, so on GET we render a JS snippet to extract the token
    and POST it back to this same route.
    """
    if request.method == "GET":
        # Check if we got a code (PKCE flow)
        code = request.args.get("code")
        if code:
            try:
                auth_service = SupabaseAuthService(get_supabase_client())
                res = auth_service.intercambiar_codigo(code)
                session["temp_access_token"] = res["access_token"]
                session["temp_refresh_token"] = res["refresh_token"]
                return render_template("auth/completar_registro.html")
            except Exception as e:
                flash(f"El enlace de invitación expiró o es inválido: {str(e)}", "error")
                return redirect(url_for("index"))

        # Render a simple page that extracts the hash and POSTs it (Implicit Flow fallback)
        return render_template("auth/callback_fallback.html")
    
    # Handle POST
    access_token = request.form.get("access_token")
    if not access_token:
        flash("Token no encontrado.", "error")
        return redirect(url_for("index"))
        
    return render_template("auth/completar_registro.html", access_token=access_token)


@auth_bp.route("/set-password", methods=["POST"])
def set_password():
    
    access_token = request.form.get("access_token") or session.get("temp_access_token")
    refresh_token = request.form.get("refresh_token") or session.get("temp_refresh_token", "dummy")
    password = request.form.get("password")
    password_confirm = request.form.get("password_confirm")
    
    # Extra fields for the domain entity
    datos_usuario = {
        "nombre": request.form.get("nombre", ""),
        "apellido": request.form.get("apellido", ""),
        "telefono": request.form.get("telefono", ""),
        "edad": int(request.form.get("edad", 0)) if request.form.get("edad") else 0,
        "sexo": request.form.get("sexo", ""),
        "direccion": request.form.get("direccion", "")
    }
    
    if not access_token:
        flash("Token de sesión faltante.", "error")
        return redirect(url_for("index"))
        
    try:
        auth_service = SupabaseAuthService(get_supabase_client())
        repo = SQLAlchemyUsuarioRepository(g.db_session)
        use_case = CompletarRegistroUseCase(auth_service, repo)
        
        # We temporarily pass the refresh token to the execute logic
        use_case.ejecutar(access_token, password, password_confirm, datos_usuario, refresh_token=refresh_token)
        
        # Clear temp tokens
        session.pop("temp_access_token", None)
        session.pop("temp_refresh_token", None)
        
        flash("Registro completado exitosamente. Ahora podés iniciar sesión.", "success")
        return redirect(url_for("index"))  # In the future, this should redirect to login
        
    except ValueError as e:
        flash(str(e), "error")
        return render_template("auth/completar_registro.html", access_token=access_token)
    except Exception as e:
        flash("Ocurrió un error inesperado al completar el registro.", "error")
        logging.error(f"Error completing registration: {str(e)}")
        return render_template("auth/completar_registro.html", access_token=access_token)
