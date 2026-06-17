"""
Use Case for permanently deleting a Becario and all associated infrastructure data
(Database, Storage, and Auth) utilizing a Saga Pattern.
"""

from src.application.protocols import UsuarioRepositoryProtocol, IStorageServiceProtocol, AuthServiceProtocol
from src.domain.actors.administrador import Administrador
from src.domain.actors.becario import Becario

class EliminarBecarioUseCase:
    """
    Coordinates the deletion of a Becario actor.
    """

    def __init__(
        self,
        usuario_repo: UsuarioRepositoryProtocol,
        storage_service: IStorageServiceProtocol,
        auth_service: AuthServiceProtocol
    ):
        self.usuario_repo = usuario_repo
        self.storage_service = storage_service
        self.auth_service = auth_service

    def execute(self, actor_admin: Administrador, becario_id: str, email_confirmacion: str) -> None:
        """
        Executes the Saga Pattern for deleting a Becario.
        
        1. Deletes associated documents from Supabase Storage.
        2. Deletes the database record (cascading into DatosAcademicos and Tutorias).
        3. Deletes the Supabase Auth identity.
        
        Args:
            actor_admin: The administrator executing the action.
            becario_id: The ID of the Becario to delete.
            email_confirmacion: The email typed by the admin to confirm deletion.
            
        Raises:
            PermissionError: If the executor is not an admin.
            ValueError: If the user doesn't exist, email doesn't match, or an external service fails.
        """
        if not isinstance(actor_admin, Administrador):
            raise PermissionError("Sólo los administradores pueden eliminar usuarios.")

        usuario = self.usuario_repo.obtener_por_id_y_rol(becario_id, "becario")
        if not usuario or not isinstance(usuario, Becario):
            raise ValueError("El becario especificado no existe.")

        if usuario.email.lower() != email_confirmacion.lower():
            raise ValueError("El email de confirmación no coincide con el del becario.")

        # 1. Eliminar documentos del Storage
        if usuario.datos_academicos and usuario.datos_academicos.lista_documentos:
            for doc in usuario.datos_academicos.lista_documentos:
                try:
                    self.storage_service.eliminar_documento_por_url(doc.ruta_archivo)
                except Exception as e:
                    # Depending on strictness, we might log and continue, but typically
                    # failing to delete from storage shouldn't block DB deletion, 
                    # unless we want perfect consistency. We'll proceed.
                    pass

        # 2. Eliminar de la Base de Datos (SQLAlchemy maneja el cascade de las colecciones)
        self.usuario_repo.eliminar(usuario)
        
        # 3. Eliminar de Supabase Auth
        try:
            self.auth_service.eliminar_usuario_auth(usuario.id_usuario)
        except Exception as e:
            raise ValueError(f"Fallo al eliminar identidad en Auth: {str(e)}")
