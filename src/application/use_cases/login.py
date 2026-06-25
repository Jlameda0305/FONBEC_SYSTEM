from typing import Dict, Any
from src.application.protocols import AuthServiceProtocol, UsuarioRepositoryProtocol

class LoginUseCase:
    """
    Use case for authenticating a user.
    Coordinates between Supabase Auth and the local database repository
    to ensure the user has a valid profile before granting access.
    """
    
    def __init__(self, auth_service: AuthServiceProtocol, usuario_repo: UsuarioRepositoryProtocol):
        self.auth_service = auth_service
        self.usuario_repo = usuario_repo
        
    def ejecutar(self, email: str, password: str) -> Dict[str, Any]:
        """
        Executes the login process.
        
        Args:
            email: User's email.
            password: User's password.
            
        Returns:
            A dictionary containing the access token, refresh token, role, and user entity.
            
        Raises:
            ValueError: If authentication fails or the user profile does not exist.
        """
        if not email or not password:
            raise ValueError("Email y contraseña son requeridos.")
            
        email = email.lower().strip()
            
        # 1. Authenticate with Supabase Auth
        try:
            auth_response = self.auth_service.login(email, password)
        except ValueError as e:
            # Re-raise authentication errors directly
            raise ValueError(f"Credenciales inválidas o error de auth: {str(e)}")
            
        user_metadata = auth_response["user"].get("user_metadata", {})
        rol = user_metadata.get("rol")
        
        if not rol:
            raise ValueError("El usuario no tiene un rol asignado en Supabase.")
            
        # 2. Check if the profile exists in the local database
        usuario_db = self.usuario_repo.obtener_por_email(email)
        
        if not usuario_db:
            # The account exists in Supabase but the profile was deleted in PostgreSQL.
            # Applying rudimentary Saga pattern: we revoke the Supabase session
            # since the local database check failed.
            try:
                self.auth_service.logout(auth_response["access_token"])
            except Exception:
                pass
                
            raise ValueError("Tu cuenta existe pero tu perfil fue eliminado localmente. Contactá al administrador.")
            
        return {
            "access_token": auth_response["access_token"],
            "refresh_token": auth_response["refresh_token"],
            "rol": rol,
            "usuario": usuario_db
        }
