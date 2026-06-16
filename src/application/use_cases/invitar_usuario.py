"""
Use case to invite a new user to the system.
"""

from typing import Any
from src.application.protocols import AuthServiceProtocol, UsuarioRepositoryProtocol


class InvitarUsuarioUseCase:
    """
    Handles the business logic for inviting a user.
    """

    def __init__(
        self,
        auth_service: AuthServiceProtocol,
        usuario_repo: UsuarioRepositoryProtocol
    ):
        self.auth_service = auth_service
        self.usuario_repo = usuario_repo

    def execute(self, actor_admin: Any, email: str, rol: str) -> str:
        """
        Invites a user if the email does not exist.

        Args:
            actor_admin: The user performing the action (must be an admin).
            email: The email of the user to invite.
            rol: The assigned role.

        Returns:
            The user ID from the auth service.

        Raises:
            PermissionError: If actor_admin is not an administrator.
            ValueError: If the email is already registered or the role is invalid.
        """
        if actor_admin.__class__.__name__ != "Administrador":
            raise PermissionError("Solo los administradores pueden invitar usuarios.")

        roles_permitidos = ["becario", "tutor", "mediador", "administrador", "padrino"]
        rol = rol.lower().strip()
        if rol not in roles_permitidos:
            raise ValueError(f"Rol '{rol}' no soportado.")

        email = email.lower().strip()
        usuario_existente = self.usuario_repo.obtener_por_email(email)
        if usuario_existente:
            raise ValueError(f"El email '{email}' ya se encuentra registrado.")

        user_id = self.auth_service.invitar_usuario(email=email, rol=rol)
        return user_id
