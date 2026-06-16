from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Dict, Any

from src.domain.enums import EstadoVerificacion
from .abstract_actor import Usuario

if TYPE_CHECKING:
    from .becario import Becario


@dataclass
class Administrador(Usuario):
    """
    Administrador actor (AOO) — global system manager.
    Responsible for user lifecycle and relationships.
    Does not hold global collections (lists) in memory to avoid eager loading bloat.
    """
    rol: str = "administrador"



    def visualizar_datos_academicos(self, becario: Optional[Becario] = None) -> Dict[str, Any]:
        """
        Visualize academic data of a selected Becario (CU-ADM-06).
        Administrators can only view the full details if the state is 'Aprobado'.
        """
        if becario is None:
            raise ValueError("Debe seleccionar un becario para visualizar sus datos.")

        datos = becario.datos_academicos

        if datos.estado_verificacion != EstadoVerificacion.APROBADO:
            return {
                "estado": datos.estado_verificacion.value,
                "mensaje": f"El becario se encuentra en estado: {datos.estado_verificacion.value}"
            }

        return {
            "estado": datos.estado_verificacion.value,
            "datos": {
                "nombre_carrera": datos.nombre_carrera,
                "anio_ingreso": datos.anio_ingreso,
                "anio_en_curso": datos.anio_en_curso,
                "materias_a_cursar": datos.materias_a_cursar,
                "materias_adeudadas": datos.materias_adeudadas,
                "observaciones": datos.observaciones,
            }
        }
