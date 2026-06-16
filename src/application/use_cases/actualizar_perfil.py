"""
Use case for updating user profile data.
"""

from dataclasses import dataclass
from typing import Optional

from src.application.protocols import UsuarioRepositoryProtocol, AuthServiceProtocol


@dataclass
class ActualizarPerfilRequest:
    user_id: str
    rol: str
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    edad: Optional[int] = None
    sexo: Optional[str] = None
    password_actual: Optional[str] = None
    nueva_contrasena: Optional[str] = None


class ActualizarPerfilUseCase:
    """
    Use case to update a user's profile and optionally change their password.
    """

    def __init__(
        self,
        usuario_repo: UsuarioRepositoryProtocol,
        auth_service: AuthServiceProtocol,
    ) -> None:
        self.usuario_repo = usuario_repo
        self.auth_service = auth_service

    def ejecutar(self, request: ActualizarPerfilRequest) -> None:
        """
        Executes the profile update.

        Args:
            request: The validated data to update.
            
        Raises:
            ValueError: If user is not found or validation fails.
        """
        usuario = self.usuario_repo.obtener_por_id_y_rol(request.user_id, request.rol)
        if not usuario:
            raise ValueError(f"Usuario {request.user_id} no encontrado.")

        # If user wants to change password
        if request.password_actual and request.nueva_contrasena:
            try:
                # Validate current password using Supabase Auth (simulating a login)
                session_data = self.auth_service.login(usuario.email, request.password_actual)
                access_token = session_data["access_token"]
                refresh_token = session_data["refresh_token"]
                
                try:
                    # If login was successful, we use the fresh tokens to establish new password
                    self.auth_service.establecer_contrasena(
                        access_token=access_token,
                        nueva_contrasena=request.nueva_contrasena,
                        refresh_token=refresh_token
                    )
                finally:
                    # Siempre limpiamos la sesión de validación
                    self.auth_service.logout(access_token)
            except Exception as e:
                raise ValueError(f"Error al cambiar contraseña: {str(e)}")
        elif request.password_actual or request.nueva_contrasena:
            raise ValueError("Debe proveer tanto la contraseña actual como la nueva para cambiarla.")

        # Update local domain fields
        usuario.actualizar_datos_personales(
            telefono=request.telefono,
            direccion=request.direccion,
            edad=request.edad,
            sexo=request.sexo,
        )

        # Persist changes
        self.usuario_repo.guardar(usuario)
