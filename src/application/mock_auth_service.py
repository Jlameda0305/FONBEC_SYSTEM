"""
Mock Authentication Service.

Provides a temporary stub for resolving the current active user
while the web/session layer is not yet implemented.
"""


def obtener_usuario_actual() -> str:
    """
    Return the ID of the currently authenticated Becario.

    # TODO: ELIMINAR CUANDO SE IMPLEMENTE FLASK/SESSION Y LA AUTENTICACIÓN REAL.
    # Este stub será reemplazado por la lectura de la sesión HTTP real
    # (ej. flask.session["user_id"] o un token JWT de Supabase Auth).

    Returns:
        A hardcoded becario_id for development and testing purposes.
    """
    return "bec-002"
