from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .abstract_actor import Referente

if TYPE_CHECKING:
    from .becario import Becario

@dataclass
class Mediador(Referente):
    """
    Mediador actor (AOO §1.5) — reference class for MVP.

    Only get_datos_contacto() is implemented. All active methods
    (CU-07, CU-13 to CU-15) are out of MVP scope.
    """
    rol: str = "mediador"

    def seleccionar_becario(self, id_becario: str) -> Becario:
        """Out of MVP scope (CU-07 — no .puml)."""
        raise NotImplementedError("CU-07: fuera del alcance del MVP")

    def visualizar_datos_academicos(self, becario: Becario = None) -> dict:
        """Out of MVP scope — no Mediador .puml for CU-04."""
        raise NotImplementedError("Visualización de datos por Mediador: fuera del alcance del MVP")

    def get_datos_contacto(self) -> dict:
        """
        Return contact information for this Mediador (CU-02).
        Called by Becario.contacto_mediador() and Tutor.contactar_mediador_becario().
        """
        return {
            "nombre": self.nombre,
            "apellido": self.apellido,
            "email": self.email,
            "telefono": self.telefono
        }
