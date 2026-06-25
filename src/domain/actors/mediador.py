from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING
from datetime import datetime

from src.domain.enums import EstadoVerificacion
from .abstract_actor import Referente

if TYPE_CHECKING:
    from .becario import Becario

@dataclass
class Mediador(Referente):
    """
    Mediador actor (AOO §1.5) — audit + cartas referent.

    MVP methods: seleccionar_becario, visualizar_datos_academicos,
    auditar_datos_academicos_becario, get_datos_contacto.
    """
    rol: str = "mediador"

    def seleccionar_becario(self, id_becario: str) -> Becario:
        """
        Select a Becario from lista_becarios by ID (CU-07).
        Loads: becario data + calendario envíos + padrino + contacto tutor.

        Raises:
            ValueError: If no Becario with the given ID is found.
        """
        for becario in self.lista_becarios:
            if becario.id_usuario == id_becario:
                return becario
        raise ValueError(
            "No posee permisos para acceder al becario solicitado."
        )

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
