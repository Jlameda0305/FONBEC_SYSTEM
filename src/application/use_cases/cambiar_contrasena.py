"""
Cambiar Contraseña Use Case.
"""

from src.application.protocols import AuthServiceProtocol

class CambiarContrasenaUseCase:
    """
    Handles the password update flow using a recovery token.
    """

    def __init__(self, auth_service: AuthServiceProtocol):
        self.auth_service = auth_service

    def ejecutar(self, access_token: str, password: str, password_confirm: str, refresh_token: str) -> None:
        """
        Executes the password change logic.
        
        Args:
            access_token: The auth session access token.
            password: The new password.
            password_confirm: Confirmation of the new password.
            refresh_token: The auth session refresh token.
            
        Raises:
            ValueError: If tokens are missing or passwords do not match.
        """
        if not access_token or not refresh_token:
            raise ValueError("Tokens de sesión inválidos o expirados.")
        if not password or not password_confirm:
            raise ValueError("La contraseña y su confirmación son obligatorias.")
            
        if password != password_confirm:
            raise ValueError("Las contraseñas no coinciden.")
            
        if len(password) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres.")
            
        self.auth_service.establecer_contrasena(access_token, password, refresh_token)
