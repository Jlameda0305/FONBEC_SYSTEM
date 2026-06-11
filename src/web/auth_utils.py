"""
Authentication and Authorization Utilities for the Web Layer.
"""

from functools import wraps
from flask import abort, g
from src.web.mock_auth_service import obtener_usuario_actual
from src.domain.models import Administrador, Becario, Tutor, Mediador, Padrino


def requiere_rol(rol_requerido: str):
    """
    Decorador que verifica que el usuario autenticado posea el rol solicitado.
    Si el rol no coincide, aborta la petición con 403 Forbidden.
    Si coincide, inyecta la instancia del actor en `g.usuario_actual`.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = obtener_usuario_actual()
            
            clases_map = {
                "administrador": Administrador,
                "becario": Becario,
                "tutor": Tutor,
                "mediador": Mediador,
                "padrino": Padrino
            }
            
            cls = clases_map.get(rol_requerido.lower())
            if not cls:
                abort(500, description=f"Rol requerido '{rol_requerido}' no soportado.")

            # Verifica si el user_id existe en la tabla correspondiente a ese rol
            user = g.db_session.query(cls).filter_by(id_usuario=user_id).first()
            if not user:
                abort(403, description=f"Acceso denegado. Se requiere rol '{rol_requerido}'.")
            
            # Inyecta el actor para que el controlador pueda usarlo en Casos de Uso
            g.usuario_actual = user
            return f(*args, **kwargs)
        return decorated_function
    return decorator
