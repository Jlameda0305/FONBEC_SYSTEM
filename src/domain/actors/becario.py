from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

from src.domain.enums import EstadoVerificacion, NivelCursado
from src.domain.domain_entities.datos_academicos import DatosAcademicos
from src.domain.domain_entities.tutoria import Tutoria
from src.domain.domain_entities.envio_carta import EnvioCarta
from src.domain.domain_entities.padrino import Padrino
from .abstract_actor import Usuario

if TYPE_CHECKING:
    from .tutor import Tutor
    from .mediador import Mediador

@dataclass
class Becario(Usuario):
    """
    Becario — Aggregate Root of the domain model (AOO §1.2).

    All navigation to Tutoria, EnvioCarta, or DatosAcademicos passes
    through a Becario instance. There is no direct relationship between
    Tutor and Mediador (RN-03).
    """
    rol: str = "becario"
    nivel_cursado: Optional[NivelCursado] = None
    datos_academicos: DatosAcademicos = field(default_factory=DatosAcademicos)
    puntero_tutor: Optional[Tutor] = None
    puntero_mediador: Optional[Mediador] = None
    puntero_padrino: Optional[Padrino] = None
    lista_tutorias: list[Tutoria] = field(default_factory=list)
    lista_envios_cartas: list[EnvioCarta] = field(default_factory=list)

    def visualizar_datos_academicos(self) -> dict:
        """
        Visualize own academic data (CU-04 Becario view).

        Returns:
            Dictionary with academic data and state-dependent options/messages.
        """
        datos = self.datos_academicos
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
            resultado["mensaje"] = "Debes llenar el formulario"
        elif datos.estado_verificacion == EstadoVerificacion.PENDIENTE_MODIFICAR:
            resultado["mensaje"] = f"Observaciones del tutor: {datos.observaciones}"
        elif datos.estado_verificacion in (
            EstadoVerificacion.INCOMPLETO,
            EstadoVerificacion.PENDIENTE_MODIFICAR,
        ):
            resultado["opciones"] = ["llenar_formulario"]

        return resultado

    def visualizar_formulario_academico(self) -> dict:
        """
        Retrieve current academic data for form display (CU-03 step 1-2).

        Returns:
            Dictionary with current field values for the form.

        Raises:
            ValueError: If estado_verificacion is APROBADO (RN-02).
        """
        if self.datos_academicos.estado_verificacion == EstadoVerificacion.APROBADO:
            raise ValueError(
                "Los datos académicos han sido aprobados y no pueden modificarse"
            )
        documentos = {
            doc.tipo_documento: {
                "ruta_archivo": doc.ruta_archivo,
                "fecha_carga": doc.fecha_carga.isoformat() if doc.fecha_carga else None,
            }
            for doc in self.datos_academicos.lista_documentos
        }
        return {
            "nombre_carrera": self.datos_academicos.nombre_carrera,
            "anio_ingreso": self.datos_academicos.anio_ingreso,
            "anio_en_curso": self.datos_academicos.anio_en_curso,
            "materias_a_cursar": self.datos_academicos.materias_a_cursar,
            "materias_adeudadas": self.datos_academicos.materias_adeudadas,
            "documentos": documentos,
        }

    def llenar_actualizar_formulario_academico(self, datos: dict) -> None:
        """
        Fill or update academic data and determine resulting state (CU-03).

        Updates the fields, then re-evaluates the state.

        Args:
            datos: Dictionary with field names and values to update.

        Raises:
            ValueError: If estado_verificacion is APROBADO (RN-02).
        """
        if self.datos_academicos.estado_verificacion == EstadoVerificacion.APROBADO:
            raise ValueError(
                "Los datos académicos han sido aprobados y no pueden modificarse"
            )
            
        da = self.datos_academicos
        da.actualizar_datos(**datos)
        da.revaluar_estado()

    def get_datos_contacto(self) -> dict:
        """
        Return contact information for this Becario (CU-02).
        """
        return {"email": self.email, "telefono": self.telefono}

    def contacto_tutor(self) -> dict:
        """
        Get assigned Tutor's contact info (CU-02).

        Raises:
            ValueError: If no Tutor is assigned.
        """
        if self.puntero_tutor is None:
            raise ValueError("No posee tutor asignado")
        return self.puntero_tutor.get_datos_contacto()

    def contacto_mediador(self) -> dict:
        """
        Get assigned Mediador's contact info (CU-02).

        Raises:
            ValueError: If no Mediador is assigned.
        """
        if self.puntero_mediador is None:
            raise ValueError("No posee mediador asignado")
        return self.puntero_mediador.get_datos_contacto()

    # --- Métodos de Gestión de Vinculaciones (CU-ADM-03) ---
    
    def asignar_tutor(self, tutor: 'Tutor') -> None:
        from .tutor import Tutor
        if not isinstance(tutor, Tutor):
            raise TypeError("El objeto provisto no es de clase Tutor")
        self.puntero_tutor = tutor

    def desasignar_tutor(self) -> None:
        self.puntero_tutor = None

    def asignar_mediador(self, mediador: 'Mediador') -> None:
        from .mediador import Mediador
        if not isinstance(mediador, Mediador):
            raise TypeError("El objeto provisto no es de clase Mediador")
        self.puntero_mediador = mediador

    def desasignar_mediador(self) -> None:
        self.puntero_mediador = None

    def asignar_padrino(self, padrino: 'Padrino') -> None:
        # Padrino is already imported at the top of the file
        if not isinstance(padrino, Padrino):
            raise TypeError("El objeto provisto no es de clase Padrino")
        self.puntero_padrino = padrino

    def desasignar_padrino(self) -> None:
        self.puntero_padrino = None
