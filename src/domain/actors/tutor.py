from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.domain.enums import EstadoVerificacion
from .abstract_actor import Referente

if TYPE_CHECKING:
    from .becario import Becario

@dataclass
class Tutor(Referente):
    """
    Tutor actor (AOO §1.4) — tutorías-only referent.

    MVP methods: seleccionar_becario, visualizar_datos_academicos,
    get_datos_contacto, contactar_mediador_becario.
    """
    rol: str = "tutor"

    def seleccionar_becario(self, id_becario: str) -> Becario:
        """
        Select a Becario from lista_becarios by ID (CU-06).
        Loads: becario data + calendario tutorias + contacto mediador.

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
        """
        Visualize academic data of a selected Becario (CU-04 Tutor view).

        Args:
            becario: The selected Becario whose data to visualize.

        Returns:
            Dictionary with academic data and available options per state.
        """
        if becario is None:
            raise ValueError("Debe seleccionar un becario primero")

        datos = becario.datos_academicos
        resultado = {
            "estado": datos.estado_verificacion.value,
            "datos": {
                "nombre_carrera": datos.nombre_carrera,
                "anio_ingreso": datos.anio_ingreso,
                "anio_en_curso": datos.anio_en_curso,
                "materias_a_cursar": datos.materias_a_cursar,
                "materias_adeudadas": datos.materias_adeudadas,
                "observaciones": datos.observaciones,
            },
            "opciones": [],
        }

        if datos.estado_verificacion == EstadoVerificacion.VACIO:
            resultado["mensaje"] = "El becario no ha cargado datos"
        elif datos.estado_verificacion == EstadoVerificacion.PENDIENTE_REVISION:
            pass
        elif datos.estado_verificacion == EstadoVerificacion.INCOMPLETO:
            resultado["mensaje"] = "Contactar al becario para completar los datos"

        return resultado

    def get_datos_contacto(self) -> dict:
        """
        Return contact information for this Tutor (CU-02).
        """
        return {
            "nombre": self.nombre,
            "apellido": self.apellido,
            "email": self.email,
            "telefono": self.telefono
        }

    def contactar_mediador_becario(self, becario: Becario) -> dict:
        """
        Get the Mediador contact info for a selected Becario (CU-02).

        Raises:
            ValueError: If the Becario has no assigned Mediador.
        """
        if becario.puntero_mediador is None:
            raise ValueError("No posee mediador asignado")
        return becario.puntero_mediador.get_datos_contacto()
