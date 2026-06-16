from src.application.dto_mapper import usuario_to_dict, datos_academicos_to_dict
"""
CU-ADM-04: Gestionar Padrinos (ABM)

Este caso de uso orquesta la creación, lectura, actualización y eliminación
de los Padrinos del sistema.
Solo un Administrador puede ejecutar estas acciones.
"""

from typing import Dict, Any, List, Optional
import uuid

from src.domain.domain_entities.padrino import Padrino
from src.application.protocols import PadrinoRepositoryProtocol


class GestionarPadrinosUseCase:
    """
    Use case interactor for managing Padrinos (Create, Read, Update, Delete).
    """

    def __init__(self, padrino_repo: PadrinoRepositoryProtocol):
        self.padrino_repo = padrino_repo

    def _verificar_permisos(self, actor: object) -> None:
        """
        Internal helper to assert the actor has the required permissions.
        """
        if getattr(actor, "rol", None) != "administrador":
            raise PermissionError("Solo un Administrador puede gestionar padrinos.")

    def crear(self, actor_admin: object, datos: Dict[str, Any]) -> str:
        """
        Create a new Padrino.
        
        Args:
            actor_admin: The actor executing the action (must be an Administrador).
            datos: Dictionary containing the Padrino's data.
            
        Returns:
            str: The ID of the newly created Padrino.
        """
        self._verificar_permisos(actor_admin)
        
        nuevo_id = f"pad-{uuid.uuid4().hex[:6]}"
        nuevo_padrino = Padrino(
            id_padrino=nuevo_id,
            nombre=datos.get("nombre", ""),
            apellido=datos.get("apellido", ""),
            email=datos.get("email", ""),
            telefono=datos.get("telefono", ""),
            direccion=datos.get("direccion", "")
        )
        
        self.padrino_repo.crear_padrino(nuevo_padrino)
        return nuevo_id

    def obtener(self, actor_admin: object, id_padrino: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a Padrino by ID and return it as a DTO.
        """
        self._verificar_permisos(actor_admin)
        
        padrino = self.padrino_repo.obtener_padrino_por_id(id_padrino)
        if not padrino:
            return None
            
        return usuario_to_dict(padrino)

    def modificar(self, actor_admin: object, id_padrino: str, datos: Dict[str, Any]) -> None:
        """
        Update an existing Padrino's data.
        """
        self._verificar_permisos(actor_admin)
        
        padrino = self.padrino_repo.obtener_padrino_por_id(id_padrino)
        if not padrino:
            raise ValueError(f"No se encontró un padrino con el ID: {id_padrino}")
            
        padrino.actualizar_datos(
            nombre=datos.get("nombre", padrino.nombre),
            apellido=datos.get("apellido", padrino.apellido),
            email=datos.get("email", padrino.email),
            telefono=datos.get("telefono", padrino.telefono),
            direccion=datos.get("direccion", padrino.direccion)
        )
        
        self.padrino_repo.actualizar_padrino(padrino)

    def eliminar(self, actor_admin: object, id_padrino: str) -> None:
        """
        Delete a Padrino by ID.
        Raises ValueError if the Padrino has associated Becarios.
        """
        self._verificar_permisos(actor_admin)
        
        padrino = self.padrino_repo.obtener_padrino_por_id(id_padrino)
        if not padrino:
            raise ValueError(f"No se encontró un padrino con el ID: {id_padrino}")
            
        self.padrino_repo.eliminar_padrino(id_padrino)
