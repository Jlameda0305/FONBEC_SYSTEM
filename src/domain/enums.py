"""
Domain enumerations for the FONBEC scholarship management system.

Defines the value sets used across domain entities. Each enum corresponds
to a constrained attribute in the AOO class diagram.
"""

from enum import Enum


class NivelCursado(Enum):
    """Academic level currently being pursued by a Becario."""
    PRIMARIO = "Primario"
    SECUNDARIO = "Secundario"
    TERCIARIO = "Terciario"
    UNIVERSITARIO = "Universitario"


class EstadoVerificacion(Enum):
    """
    Verification lifecycle of DatosAcademicos.

    State transitions (from Diag_Est_DatosA.puml):
        [*]                  → VACIO
        VACIO                → INCOMPLETO | PENDIENTE_REVISION
        INCOMPLETO           → INCOMPLETO | PENDIENTE_REVISION
        PENDIENTE_REVISION   → APROBADO | PENDIENTE_MODIFICAR
        PENDIENTE_MODIFICAR  → INCOMPLETO | PENDIENTE_REVISION
        APROBADO             → [*]  (terminal — RN-02)
    """
    VACIO = "Vacio"
    INCOMPLETO = "Incompleto"
    PENDIENTE_REVISION = "Pendiente_Revision"
    PENDIENTE_MODIFICAR = "Pendiente_Modificar"
    APROBADO = "Aprobado"


class EstadoTutoria(Enum):
    """State of a scheduled tutoring session."""
    PROGRAMADA = "Programada"
    REALIZADA = "Realizada"
    AUSENTE = "Ausente"
    CANCELADA = "Cancelada"


class EstadoEnvioCarta(Enum):
    """State of a letter-sending event."""
    PROGRAMADA = "Programada"
    REPROGRAMADA = "Reprogramada"
    CANCELADA = "Cancelada"
    ENVIADA = "Enviada"
