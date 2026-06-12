from dataclasses import dataclass, field
from typing import ClassVar, Optional
from datetime import datetime

from src.domain.enums import EstadoVerificacion
from src.domain.domain_entities.documentos_academicos import DocumentoAcademico

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
    fecha_observacion: Optional[datetime] = None

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
        Check whether all required fields and documents are filled.

        Returns:
            True if all required scalar fields are present, AND the 3 mandatory
            documents (Programa, CartaCompromiso, Inscripcion) are attached.
            False otherwise.
        """
        campos_ok = all([
            self.nombre_carrera,
            self.anio_ingreso is not None,
            self.anio_en_curso is not None,
            len(self.materias_a_cursar) > 0,
        ])
        
        documentos_requeridos = {"Programa", "CartaCompromiso", "Inscripcion"}
        documentos_actuales = {doc.tipo_documento for doc in self.lista_documentos}
        docs_ok = documentos_requeridos.issubset(documentos_actuales)
        
        return campos_ok and docs_ok

    def revaluar_estado(self) -> None:
        """
        Reevaluates and updates the state based on data completeness.
        Does nothing if the state is APROBADO.
        """
        if self.estado_verificacion == EstadoVerificacion.APROBADO:
            return
            
        if self.validar_completitud():
            self.actualizar_estado(EstadoVerificacion.PENDIENTE_REVISION)
        else:
            self.actualizar_estado(EstadoVerificacion.INCOMPLETO)

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
                self.revaluar_estado()
                return
        self.lista_documentos.append(documento)
        self.revaluar_estado()

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
                self.revaluar_estado()
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
        
        documentos_requeridos_info = [
            ("Programa", "Programa de la carrera"),
            ("CartaCompromiso", "Carta de compromiso"),
            ("Inscripcion", "Inscripción al año en curso")
        ]
        
        return {
            "nombre_carrera": self.nombre_carrera,
            "anio_ingreso": self.anio_ingreso,
            "anio_en_curso": self.anio_en_curso,
            "materias_a_cursar": self.materias_a_cursar,
            "materias_adeudadas": self.materias_adeudadas,
            "estado_verificacion": self.estado_verificacion.value,
            "observaciones": self.observaciones,
            "fecha_observacion": self.fecha_observacion.isoformat() if self.fecha_observacion else None,
            "documentos": documentos,
            "documentos_requeridos": documentos_requeridos_info,
        }
