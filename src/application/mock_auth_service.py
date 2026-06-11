"""
Mock Authentication Service.

Provides a temporary stub for resolving the current active user
while the web/session layer is not yet implemented.
"""


def obtener_usuario_actual() -> str:
    """
    Return the ID of the currently authenticated Becario or Tutor.

    # TODO: ELIMINAR CUANDO SE IMPLEMENTE LA AUTENTICACIÓN REAL.
    # Soporta múltiples sesiones leyendo la cookie de flask.session.
    """
    from flask import session, request, has_request_context
    
    if has_request_context():
        # 1. Permite forzar el usuario por URL: ?force_user=tut-001
        forced = request.args.get("force_user")
        if forced:
            session["user_id"] = forced
            return forced
            
        # 2. Lee de la sesión HTTP (para soportar incognito / 2 navegadores)
        if session.get("user_id"):
            return session["user_id"]

    # 3. Fallback por defecto si no hay sesión
    return "bec-002"
