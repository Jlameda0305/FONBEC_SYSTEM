"""
Use Case for permanently deleting a Referente (Padrino, Tutor, Mediador) 
and unlinking their assigned Becarios utilizing a Saga Pattern.
"""

from src.application.protocols import UsuarioRepositoryProtocol, AuthServiceProtocol
from src.domain.actors.administrador import Administrador

class EliminarReferenteUseCase:
    """
    Coordinates the deletion of a Referente actor.
    """

    def __init__(
        self,
        usuario_repo: UsuarioRepositoryProtocol,
        auth_service: AuthServiceProtocol
    ):
        self.usuario_repo = usuario_repo
        self.auth_service = auth_service

    def execute(self, actor_admin: Administrador, referente_id: str, rol: str, email_confirmacion: str) -> None:
        """
        Executes the Saga Pattern for deleting a Referente.
        
        1. Unlinks the Referente from all assigned Becarios.
        2. Deletes the database record.
        3. Deletes the Supabase Auth identity (only for system users).
        
        Args:
            actor_admin: The administrator executing the action.
            referente_id: The ID of the Referente to delete.
            rol: The specific role ('padrino', 'tutor', 'mediador').
            email_confirmacion: The email typed by the admin to confirm deletion.
            
        Raises:
            PermissionError: If the executor is not an admin.
            ValueError: If the user doesn't exist, email doesn't match, or an external service fails.
        """
        if not isinstance(actor_admin, Administrador):
            raise PermissionError("Sólo los administradores pueden eliminar usuarios.")

        usuario = self.usuario_repo.obtener_por_id_y_rol(referente_id, rol)
        if not usuario:
            raise ValueError(f"El {rol} especificado no existe.")

        if usuario.email.lower() != email_confirmacion.lower():
            raise ValueError(f"El email de confirmación no coincide con el del {rol}.")

        # 1. Desvincular de los Becarios
        self.usuario_repo.desvincular_referente(referente_id, rol)

        # 2. Eliminar de la Base de Datos
        # For Padrino, the mapping uses id_padrino instead of id_usuario, but 
        # the repository's `eliminar` method uses the object instance, so SQLAlchemy 
        # handles it correctly via the primary key.
        self.usuario_repo.eliminar(usuario)
        
        # 3. Eliminar de Supabase Auth (solo usuarios del sistema con id_usuario, excluye Padrinos)
        if hasattr(usuario, 'id_usuario'):
            try:
                self.auth_service.eliminar_usuario_auth(usuario.id_usuario)
            except Exception as e:
                raise ValueError(f"Fallo al eliminar identidad en Auth: {str(e)}")
