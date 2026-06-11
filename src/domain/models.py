"""
Domain models for the FONBEC scholarship management system.

Architecture:
    - Usuario (abstract) → Becario (Aggregate Root)
    - Usuario (abstract) → Referente (abstract) → Tutor, Mediador
    - Standalone entities: Padrino, DatosAcademicos, DocumentoAcademico, Tutoria, EnvioCarta

This file is a facade re-exporting classes from `actors/` and `domain_entities/`
to maintain backward compatibility with external layers (infrastructure, use cases).
"""

from src.domain.actors.abstract_actor import Usuario, Referente
from src.domain.actors.becario import Becario
from src.domain.actors.tutor import Tutor
from src.domain.actors.mediador import Mediador
from src.domain.actors.administrador import Administrador

from src.domain.domain_entities.padrino import Padrino
from src.domain.domain_entities.datos_academicos import DatosAcademicos
from src.domain.domain_entities.documentos_academicos import DocumentoAcademico
from src.domain.domain_entities.tutoria import Tutoria
from src.domain.domain_entities.envio_carta import EnvioCarta

__all__ = [
    "Usuario",
    "Referente",
    "Becario",
    "Tutor",
    "Mediador",
    "Administrador",
    "Padrino",
    "DatosAcademicos",
    "DocumentoAcademico",
    "Tutoria",
    "EnvioCarta",
]
