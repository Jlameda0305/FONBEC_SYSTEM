"""
Recuperar Contraseña Use Case.
"""

from src.application.protocols import AuthServiceProtocol, UsuarioRepositoryProtocol

class RecuperarContrasenaUseCase:
    """
    Handles the password recovery request flow.
    """

    def __init__(self, auth_service: AuthServiceProtocol, usuario_repo: UsuarioRepositoryProtocol):
        self.auth_service = auth_service
        self.usuario_repo = usuario_repo

    def ejecutar(self, email: str) -> None:
        """
        Executes the password recovery logic.
        
        Args:
            email: The user's email address.
            
        Raises:
            ValueError: If the email is not registered in the system.
        """
        usuario = self.usuario_repo.obtener_por_email(email)
        if not usuario:
            raise ValueError("El correo no existe, contacta a Fonbec para mas informacion")
            
        self.auth_service.recuperar_contrasena(email)
