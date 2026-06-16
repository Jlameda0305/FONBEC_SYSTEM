"""
Authentication and Authorization Utilities for the Web Layer.
"""

from functools import wraps
from flask import abort, g



def requiere_rol(rol_requerido: str):
    """
    Decorador que verifica que el usuario autenticado posea el rol solicitado.
    Si el rol no coincide o no hay sesión, aborta la petición con 403 Forbidden.
    Asume que g.usuario_actual fue inyectado por @app.before_request.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not getattr(g, "usuario_actual", None):
                # No session or user not found in DB
                from flask import redirect, url_for, flash
                flash("Debes iniciar sesión para acceder a esta ruta.", "error")
                return redirect(url_for("auth.login"))
                
            # Verifica que el usuario tenga el rol requerido
            # Para mayor flexibilidad, permitimos que rol_requerido sea una lista o un string
            roles_permitidos = [rol_requerido.lower()] if isinstance(rol_requerido, str) else [r.lower() for r in rol_requerido]
            
            if g.usuario_actual.rol.lower() not in roles_permitidos:
                abort(403, description=f"Acceso denegado. Se requiere uno de estos roles: {roles_permitidos}")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
