"""
FONBEC Domain Layer — Pure-Python business logic.

Exports all domain enumerations and model classes.
No dependencies on Flask, Supabase, or any external framework.
"""

from .enums import (
    EstadoEnvioCarta,
    EstadoTutoria,
    EstadoVerificacion,
    NivelCursado,
)
from .models import (
    Becario,
    DatosAcademicos,
    DocumentoAcademico,
    EnvioCarta,
    Mediador,
    Padrino,
    Referente,
    Tutor,
    Tutoria,
    Usuario,
)

__all__ = [
    # Enums
    "NivelCursado",
    "EstadoVerificacion",
    "EstadoTutoria",
    "EstadoEnvioCarta",
    # Models
    "Usuario",
    "Becario",
    "Referente",
    "Tutor",
    "Mediador",
    "Administrador",
    "Padrino",
    "DatosAcademicos",
    "DocumentoAcademico",
    "Tutoria",
    "EnvioCarta",
]
