"""
CU-ADM-03: Gestionar Vinculaciones de Becarios

Permite a un Administrador asignar o desasignar Tutores, Mediadores o Padrinos a un Becario.
Asegura que el tipo de actor destino coincide con el rol buscado, previniendo
asignaciones corruptas.
"""

from typing import Literal

from src.application.protocols import (
    BecarioRepositoryProtocol,
    UsuarioRepositoryProtocol,
    PadrinoRepositoryProtocol
)


class GestionarVinculacionesUseCase:
    """
    Use case interactor for assigning/unassigning support roles to a Becario.
    """

    def __init__(
        self,
        becario_repo: BecarioRepositoryProtocol,
        usuario_repo: UsuarioRepositoryProtocol,
        padrino_repo: PadrinoRepositoryProtocol
    ):
        self.becario_repo = becario_repo
        self.usuario_repo = usuario_repo
        self.padrino_repo = padrino_repo

    def _verificar_permisos(self, actor: object) -> None:
        """Internal helper to assert the actor has the required permissions."""
        if getattr(actor, "rol", None) != "administrador":
            raise PermissionError("Solo un Administrador puede gestionar las vinculaciones.")

    def asignar_vinculo(
        self,
        actor_admin: object,
        id_becario: str,
        tipo_vinculacion: Literal["tutor", "mediador", "padrino"],
        id_objetivo: str
    ) -> None:
        """
        Assigns a support role to a Becario.
        
        Args:
            actor_admin: The actor executing this action (must be an Administrador).
            id_becario: The ID of the Becario receiving the assignment.
            tipo_vinculacion: The role to assign ("tutor", "mediador", "padrino").
            id_objetivo: The ID of the specific actor to assign.
            
        Raises:
            PermissionError: If executor is not an Administrador.
            ValueError: If the Becario or target actor are not found or their roles do not match.
            TypeError: Raised by Domain if the object type is invalid.
        """
        self._verificar_permisos(actor_admin)
        
        # 1. Obtener Becario
        becario = self.becario_repo.obtener_por_id(id_becario)
        if not becario:
            raise ValueError(f"No se encontró un becario con ID: {id_becario}")

        # 2. Obtener y Validar Objetivo
        if tipo_vinculacion == "tutor":
            objetivo = self.usuario_repo.obtener_por_id(id_objetivo)
            if not objetivo or getattr(objetivo, "rol", None) != "tutor":
                raise ValueError("El ID proporcionado no pertenece a un Tutor válido.")
            becario.asignar_tutor(objetivo)
            
        elif tipo_vinculacion == "mediador":
            objetivo = self.usuario_repo.obtener_por_id(id_objetivo)
            if not objetivo or getattr(objetivo, "rol", None) != "mediador":
                raise ValueError("El ID proporcionado no pertenece a un Mediador válido.")
            becario.asignar_mediador(objetivo)
            
        elif tipo_vinculacion == "padrino":
            objetivo = self.padrino_repo.obtener_padrino_por_id(id_objetivo)
            if not objetivo:
                raise ValueError("El ID proporcionado no pertenece a un Padrino válido.")
            becario.asignar_padrino(objetivo)
            
        else:
            raise ValueError(f"Tipo de vinculación desconocido: {tipo_vinculacion}")

        # 3. Guardar cambios
        self.becario_repo.guardar(becario)

    def desasignar_vinculo(
        self,
        actor_admin: object,
        id_becario: str,
        tipo_vinculacion: Literal["tutor", "mediador", "padrino"]
    ) -> None:
        """
        Removes a support role from a Becario.
        """
        self._verificar_permisos(actor_admin)
        
        becario = self.becario_repo.obtener_por_id(id_becario)
        if not becario:
            raise ValueError(f"No se encontró un becario con ID: {id_becario}")

        if tipo_vinculacion == "tutor":
            becario.desasignar_tutor()
        elif tipo_vinculacion == "mediador":
            becario.desasignar_mediador()
        elif tipo_vinculacion == "padrino":
            becario.desasignar_padrino()
        else:
            raise ValueError(f"Tipo de vinculación desconocido: {tipo_vinculacion}")

        self.becario_repo.guardar(becario)
