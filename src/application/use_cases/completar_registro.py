"""
Application Use Case for completing user registration after invitation.
"""

from typing import Optional
from src.application.protocols import AuthServiceProtocol, UsuarioRepositoryProtocol
from src.domain.actors.becario import Becario
from src.domain.actors.tutor import Tutor
from src.domain.actors.mediador import Mediador
from src.domain.actors.administrador import Administrador


class CompletarRegistroUseCase:
    """
    Handles the registration completion flow.
    1. Validates the password and token.
    2. Calls auth service to set the password.
    3. Fetches the user metadata from auth to determine the role.
    4. Persists the domain entity in the corresponding table.
    """

    def __init__(self, auth_service: AuthServiceProtocol, usuario_repo: UsuarioRepositoryProtocol):
        self.auth_service = auth_service
        self.usuario_repo = usuario_repo

    def ejecutar(self, access_token: str, password: str, password_confirm: str, datos_usuario: dict, refresh_token: str) -> bool:
        if not access_token or not refresh_token:
            raise ValueError("Token de sesión o refresh token faltantes.")
        if not password:
            raise ValueError("Contraseña faltante.")
            
        if password != password_confirm:
            raise ValueError("Las contraseñas no coinciden.")
            
        if len(password) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres.")
            
        # 1. Obtain user info from Supabase via access token
        user_data = self.auth_service.obtener_usuario(access_token)
        if not user_data:
            raise ValueError("Token inválido o expirado.")
            
        email = user_data.get("email")
        rol = user_data.get("user_metadata", {}).get("rol")
        user_id = user_data.get("id")
        
        if not email or not rol or not user_id:
            raise ValueError("Datos de usuario incompletos en el token.")
            
        # 2. Check if the user already exists in the domain table
        if self.usuario_repo.obtener_por_email(email):
            raise ValueError("El usuario ya completó su registro previamente.")
            
        # 3. Create the domain entity based on the role
        nuevo_usuario = None
        
        # We need to construct the entity with the expected base class attributes
        kwargs = {
            "id_usuario": user_id,
            "email": email,
            "rol": rol,
            "nombre": datos_usuario.get("nombre", ""),
            "apellido": datos_usuario.get("apellido", ""),
            "telefono": datos_usuario.get("telefono", ""),
            "edad": datos_usuario.get("edad", 0),
            "sexo": datos_usuario.get("sexo", ""),
            "direccion": datos_usuario.get("direccion", "")
        }
        
        if rol == "becario":
            nuevo_usuario = Becario(**kwargs)
        elif rol == "tutor":
            nuevo_usuario = Tutor(**kwargs)
        elif rol == "mediador":
            nuevo_usuario = Mediador(**kwargs)
        elif rol == "administrador":
            nuevo_usuario = Administrador(**kwargs)
        else:
            raise ValueError(f"Rol '{rol}' no reconocido.")
            
        # 4. Persist the new domain entity in the database FIRST
        self.usuario_repo.guardar(nuevo_usuario)
        
        # 5. Set the password in Supabase
        try:
            self.auth_service.establecer_contrasena(access_token, password, refresh_token=refresh_token)
        except Exception as e:
            # Saga pattern: Revert the local database change if Supabase fails
            try:
                self.usuario_repo.eliminar(nuevo_usuario)
            except Exception:
                pass
            raise ValueError(f"Hubo un error al establecer la contraseña en el servidor de autenticación: {str(e)}")
            
        return True
