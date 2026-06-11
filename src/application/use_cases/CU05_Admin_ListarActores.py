"""
Use Case: CU-ADM-05 Listar Actores del Sistema.
Orchestrates the paginated retrieval of actors (Becarios, Tutores, etc.)
by delegating to the injected UsuarioRepository.
"""

from typing import List, Dict, Any, Optional

from src.application.protocols import UsuarioRepositoryProtocol
from src.domain.actors.administrador import Administrador


class ListarActoresUseCase:
    """
    CU-ADM-05: Listar Actores del Sistema.
    """

    def __init__(self, repositorio: UsuarioRepositoryProtocol) -> None:
        """
        Inyecta la dependencia del repositorio, respetando el Clean Architecture.
        """
        self.repositorio = repositorio

    def ejecutar(
        self,
        actor_admin: object,
        tipo_actor: str,
        pagina: int = 1,
        limite: int = 50,
        busqueda: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Ejecuta el caso de uso para listar actores paginados.

        Args:
            actor_admin: La instancia del actor que ejecuta la acción (debe ser Administrador).
            tipo_actor: El rol de los actores a listar (ej. 'becario', 'tutor').
            pagina: Página solicitada (1-indexed).
            limite: Cantidad de resultados por página.
            busqueda: Término de búsqueda opcional.

        Returns:
            Una lista de diccionarios con los atributos puros de los actores.
        """
        # 1. Validación de Seguridad (Pureza del Dominio)
        if not isinstance(actor_admin, Administrador):
            raise PermissionError("Acceso denegado: Solo los administradores pueden listar actores globales.")

        # 2. Conversión de parámetros para la capa de infraestructura
        if pagina < 1:
            pagina = 1
        offset = (pagina - 1) * limite

        # 3. Delegación al Repositorio (Capa de Aplicación orquestando infraestructura)
        actores = self.repositorio.listar_usuarios(
            limite=limite,
            offset=offset,
            rol=tipo_actor,
            busqueda=busqueda
        )

        # 4. Transformación de DTOs para la Capa de Presentación Web
        # (Esto garantiza que la web no reciba entidades atadas a la sesión de SQLAlchemy)
        return [actor.to_dict() for actor in actores]
