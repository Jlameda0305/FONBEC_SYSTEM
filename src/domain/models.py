"""
Domain models for the FONBEC scholarship management system.

Contains all domain classes as defined in AOO_FONBEC.md and the class diagram.
Only methods backed by .puml use-case diagrams are implemented (MVP scope).

Architecture:
    - Usuario (abstract) → Becario (Aggregate Root)
    - Usuario (abstract) → Referente (abstract) → Tutor, Mediador
    - Standalone entities: Padrino, DatosAcademicos, DocumentoAcademico, Tutoria, EnvioCarta
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar, Optional

from .enums import (
    EstadoEnvioCarta,
    EstadoTutoria,
    EstadoVerificacion,
    NivelCursado,
)


# ---------------------------------------------------------------------------
# Standalone domain entities (no user access)
# ---------------------------------------------------------------------------

@dataclass
class Padrino:
    """
    External reference entity — sponsor without system access.
    Used as a letter recipient in the EnvioCarta flow (out of MVP scope).
    """
    id_padrino: str
    nombre: str
    apellido: str
    email: str
    telefono: str
    direccion: str


@dataclass
class DocumentoAcademico:
    """
    PDF attachment linked to a Becario's academic data.
    Data-only container; no methods in MVP.
    """
    tipo_documento: str
    ruta_archivo: str
    fecha_carga: datetime


@dataclass
class Tutoria:
    """
    Tutoring session stub — attributes only (CU-09 to CU-12 out of MVP).
    """
    id_tutoria: str
    fecha_hora: datetime
    estado: EstadoTutoria = EstadoTutoria.PROGRAMADA


@dataclass
class EnvioCarta:
    """
    Letter-sending event stub — attributes only (CU-13 to CU-15 out of MVP).
    """
    id_envio: str
    fecha_envio: datetime
    estado: EstadoEnvioCarta = EstadoEnvioCarta.PROGRAMADA


# ---------------------------------------------------------------------------
# DatosAcademicos — core domain entity with state machine
# ---------------------------------------------------------------------------

@dataclass
class DatosAcademicos:
    """
    Academic data composite owned by a Becario (composition).
    Implements the state machine from Diag_Est_DatosA.puml.

    Business rules:
        - RN-02: Cannot modify data when estado_verificacion == APROBADO.
        - State transitions are validated against TRANSICIONES_VALIDAS.
    """

    TRANSICIONES_VALIDAS: ClassVar[dict[EstadoVerificacion, set[EstadoVerificacion]]] = {
        EstadoVerificacion.VACIO: {
            EstadoVerificacion.INCOMPLETO,
            EstadoVerificacion.PENDIENTE_REVISION,
        },
        EstadoVerificacion.INCOMPLETO: {
            EstadoVerificacion.INCOMPLETO,
            EstadoVerificacion.PENDIENTE_REVISION,
        },
        EstadoVerificacion.PENDIENTE_REVISION: {
            EstadoVerificacion.APROBADO,
            EstadoVerificacion.PENDIENTE_MODIFICAR,
            EstadoVerificacion.PENDIENTE_REVISION,
            EstadoVerificacion.INCOMPLETO,
        },
        EstadoVerificacion.PENDIENTE_MODIFICAR: {
            EstadoVerificacion.INCOMPLETO,
            EstadoVerificacion.PENDIENTE_REVISION,
        },
        EstadoVerificacion.APROBADO: set(),  # terminal state — RN-02
    }

    nombre_carrera: Optional[str] = None
    anio_ingreso: Optional[int] = None
    anio_en_curso: Optional[int] = None
    materias_a_cursar: list[str] = field(default_factory=list)
    materias_adeudadas: list[str] = field(default_factory=list)
    lista_documentos: list[DocumentoAcademico] = field(default_factory=list)
    estado_verificacion: EstadoVerificacion = EstadoVerificacion.VACIO
    observaciones: Optional[str] = None  # CU-08 reject flow (approved deviation)

    def actualizar_estado(self, nuevo_estado: EstadoVerificacion) -> None:
        """
        Transition the verification state. Validates against TRANSICIONES_VALIDAS.

        Raises:
            ValueError: If the transition is not permitted from the current state.
        """
        destinos_validos = self.TRANSICIONES_VALIDAS.get(self.estado_verificacion, set())
        if nuevo_estado not in destinos_validos:
            raise ValueError(
                f"Transición inválida: {self.estado_verificacion.value} → {nuevo_estado.value}"
            )
        self.estado_verificacion = nuevo_estado

    def validar_completitud(self) -> bool:
        """
        Check whether all required fields are filled.

        Returns:
            True if all required fields (nombre_carrera, anio_ingreso,
            anio_en_curso, materias_a_cursar) are present and non-empty.
            False otherwise.
        """
        return all([
            self.nombre_carrera,
            self.anio_ingreso is not None,
            self.anio_en_curso is not None,
            len(self.materias_a_cursar) > 0,
        ])

    def actualizar_datos(self, **kwargs) -> None:
        """
        Update academic data fields. Guards RN-02: rejects changes
        when estado_verificacion is APROBADO.

        Args:
            **kwargs: Field names and their new values. Only known
                      fields (nombre_carrera, anio_ingreso, anio_en_curso,
                      materias_a_cursar, materias_adeudadas) are accepted.

        Raises:
            ValueError: If estado_verificacion == APROBADO.
            AttributeError: If an unknown field name is provided.
        """
        if self.estado_verificacion == EstadoVerificacion.APROBADO:
            raise ValueError(
                "Los datos académicos han sido aprobados y no pueden modificarse"
            )

        campos_permitidos = {
            "nombre_carrera", "anio_ingreso", "anio_en_curso",
            "materias_a_cursar", "materias_adeudadas",
        }
        
        from datetime import datetime
        current_year = datetime.now().year

        for campo, valor in kwargs.items():
            if campo not in campos_permitidos:
                raise AttributeError(f"Campo no permitido: {campo}")

            if valor is not None:
                if campo == "anio_ingreso":
                    if not isinstance(valor, int) or isinstance(valor, bool):
                        raise TypeError("anio_ingreso debe ser un entero.")
                    if valor > current_year or valor < 1900:
                        raise ValueError(f"anio_ingreso inválido: {valor}")
                elif campo == "anio_en_curso":
                    if not isinstance(valor, int) or isinstance(valor, bool):
                        raise TypeError("anio_en_curso debe ser un entero.")
                    if valor < 1 or valor > 15:
                        raise ValueError("anio_en_curso inválido. Debe ser el año de la carrera que cursas (ej: 1, 2, 3), máximo 15.")
                elif campo in ("materias_a_cursar", "materias_adeudadas"):
                    if not isinstance(valor, list):
                        raise TypeError(f"{campo} debe ser una lista.")
                    if not all(isinstance(m, str) for m in valor):
                        raise TypeError(f"Todos los elementos en {campo} deben ser texto.")

            setattr(self, campo, valor)

    def agregar_documento(self, documento: 'DocumentoAcademico') -> None:
        """
        Add or replace a DocumentoAcademico in lista_documentos.

        If a document with the same tipo_documento already exists it is
        replaced in-place, preventing duplicates. Otherwise the new
        document is appended.

        Guards RN-02: rejects changes when estado_verificacion is APROBADO.
        """
        if self.estado_verificacion == EstadoVerificacion.APROBADO:
            raise ValueError(
                "Los datos académicos han sido aprobados y no pueden modificarse"
            )
        if not isinstance(documento, DocumentoAcademico):
            raise TypeError("Se esperaba una instancia de DocumentoAcademico.")

        # Replace existing document of the same type (upsert semantics)
        for i, doc in enumerate(self.lista_documentos):
            if doc.tipo_documento == documento.tipo_documento:
                self.lista_documentos[i] = documento
                return
        self.lista_documentos.append(documento)

    def eliminar_documento(self, tipo_documento: str) -> None:
        """
        Remove a DocumentoAcademico by its tipo_documento key.

        Guards RN-02: rejects changes when estado_verificacion is APROBADO.

        Args:
            tipo_documento: The classification key of the document to remove
                (e.g. "Programa", "CartaCompromiso", "Inscripcion").

        Raises:
            ValueError: If estado is APROBADO or no document of that type exists.
        """
        if self.estado_verificacion == EstadoVerificacion.APROBADO:
            raise ValueError(
                "Los datos académicos han sido aprobados y no pueden modificarse"
            )
        for i, doc in enumerate(self.lista_documentos):
            if doc.tipo_documento == tipo_documento:
                self.lista_documentos.pop(i)
                return
        raise ValueError(
            f"No existe un documento de tipo '{tipo_documento}' para eliminar."
        )

    def to_dict(self) -> dict:
        """
        Serialize academic data to a plain dictionary (DTO).

        Translates Enum values to their string representations to prevent
        domain model leakage into the application/presentation layers.
        Includes a 'documentos' map keyed by tipo_documento.

        Returns:
            A dictionary with all academic data fields.
        """
        documentos = {
            doc.tipo_documento: {
                "ruta_archivo": doc.ruta_archivo,
                "fecha_carga": doc.fecha_carga.isoformat() if doc.fecha_carga else None,
            }
            for doc in self.lista_documentos
        }
        return {
            "nombre_carrera": self.nombre_carrera,
            "anio_ingreso": self.anio_ingreso,
            "anio_en_curso": self.anio_en_curso,
            "materias_a_cursar": self.materias_a_cursar,
            "materias_adeudadas": self.materias_adeudadas,
            "estado_verificacion": self.estado_verificacion.value,
            "observaciones": self.observaciones,
            "documentos": documentos,
        }


# ---------------------------------------------------------------------------
# Abstract base classes
# ---------------------------------------------------------------------------

@dataclass
class Usuario(ABC):
    """
    Abstract base for all system actors (AOO §1.1).

    login() and logout() raise NotImplementedError because actual
    authentication is handled by Supabase Auth in the infrastructure layer.
    """
    id_usuario: str
    nombre: str
    apellido: str
    email: str
    telefono: str
    edad: int
    sexo: str
    direccion: str
    password_hash: str
    rol: str

    def login(self) -> None:
        """Authenticate the user. Delegated to infrastructure/Supabase Auth."""
        raise NotImplementedError(
            "Autenticación delegada a la capa de infraestructura (Supabase Auth)"
        )

    def logout(self) -> None:
        """End the user session. Delegated to infrastructure/Supabase Auth."""
        raise NotImplementedError(
            "Cierre de sesión delegado a la capa de infraestructura (Supabase Auth)"
        )

    def actualizar_datos_personales(self, **kwargs) -> None:
        """Update personal data fields. Stub — no .puml for this CU."""
        raise NotImplementedError

    def restablecer_contrasena(self) -> None:
        """Reset password. Stub — no .puml for this CU."""
        raise NotImplementedError

    @abstractmethod
    def visualizar_datos_academicos(self) -> dict:
        """
        Retrieve academic data for visualization (CU-04).
        Each subclass provides its own implementation.
        """


@dataclass
class Referente(Usuario, ABC):
    """
    Abstract base for Tutor and Mediador (AOO §1.3).
    Shares lista_becarios and listar_becarios_asignados().
    """
    lista_becarios: list[Becario] = field(default_factory=list)

    def listar_becarios_asignados(self) -> list[Becario]:
        """
        Return the list of assigned Becarios (CU-05).
        """
        return self.lista_becarios

    @abstractmethod
    def seleccionar_becario(self, id_becario: str) -> Becario:
        """
        Select a Becario by ID and load their context (CU-06/CU-07).
        Each subclass loads different context data.
        """


# ---------------------------------------------------------------------------
# Concrete actor classes
# ---------------------------------------------------------------------------

@dataclass
class Tutor(Referente):
    """
    Tutor actor (AOO §1.4) — academic auditor.

    MVP methods: seleccionar_becario, visualizar_datos_academicos,
    auditar_datos_academicos_becario, get_datos_contacto,
    contactar_mediador_becario.
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
            "El becario no se encuentra registrado, contactar al sistema fonbec"
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
            resultado["opciones"] = ["aprobar", "rechazar"]
        elif datos.estado_verificacion in (
            EstadoVerificacion.INCOMPLETO, EstadoVerificacion.VACIO
        ):
            resultado["mensaje"] = "Contactar al becario para completar los datos"

        return resultado

    def auditar_datos_academicos_becario(
        self,
        becario: Becario,
        decision: str,
        observaciones: str = "",
    ) -> None:
        """
        Approve or reject a Becario's academic data (CU-08).

        Args:
            becario: The Becario whose data is being audited.
            decision: "aprobar" or "rechazar".
            observaciones: Required when rejecting (stored on DatosAcademicos).

        Raises:
            ValueError: If decision is invalid or state doesn't allow auditing.
        """
        datos = becario.datos_academicos

        if datos.estado_verificacion != EstadoVerificacion.PENDIENTE_REVISION:
            raise ValueError(
                "Solo se pueden auditar datos en estado Pendiente_Revision"
            )

        if decision == "aprobar":
            datos.actualizar_estado(EstadoVerificacion.APROBADO)
            datos.observaciones = None
        elif decision == "rechazar":
            datos.actualizar_estado(EstadoVerificacion.PENDIENTE_MODIFICAR)
            datos.observaciones = observaciones
        else:
            raise ValueError(
                f"Decisión inválida: '{decision}'. Debe ser 'aprobar' o 'rechazar'"
            )

    def get_datos_contacto(self) -> dict:
        """
        Return contact information for this Tutor (CU-02).
        """
        return {"email": self.email, "telefono": self.telefono}

    def contactar_mediador_becario(self, becario: Becario) -> dict:
        """
        Get the Mediador contact info for a selected Becario (CU-02).

        Raises:
            ValueError: If the Becario has no assigned Mediador.
        """
        if becario.puntero_mediador is None:
            raise ValueError("No posee mediador asignado")
        return becario.puntero_mediador.get_datos_contacto()


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
        return {"email": self.email, "telefono": self.telefono}


# ---------------------------------------------------------------------------
# Aggregate Root
# ---------------------------------------------------------------------------

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

        Updates the fields, then runs validar_completitud() to decide
        whether the state should be PENDIENTE_REVISION or INCOMPLETO.

        Args:
            datos: Dictionary with field names and values to update.

        Raises:
            ValueError: If estado_verificacion is APROBADO (RN-02).
        """
        da = self.datos_academicos
        da.actualizar_datos(**datos)

        if da.validar_completitud():
            da.actualizar_estado(EstadoVerificacion.PENDIENTE_REVISION)
        else:
            da.actualizar_estado(EstadoVerificacion.INCOMPLETO)

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
