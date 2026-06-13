"""
Imperative mapping configuration.
Binds the pure Python domain classes to the SQLAlchemy Table definitions.
"""

from sqlalchemy.orm import relationship

from src.domain.actors.becario import Becario
from src.domain.actors.tutor import Tutor
from src.domain.actors.mediador import Mediador
from src.domain.actors.administrador import Administrador
from src.domain.domain_entities.padrino import Padrino
from src.domain.domain_entities.datos_academicos import DatosAcademicos
from src.domain.domain_entities.documentos_academicos import DocumentoAcademico
from src.domain.domain_entities.tutoria import Tutoria
from src.domain.domain_entities.envio_carta import EnvioCarta
from .schema import (
    tabla_becarios,
    tabla_datos_academicos,
    tabla_documentos_academicos,
    tabla_envios_cartas,
    tabla_mediadores,
    tabla_padrinos,
    tabla_tutores,
    tabla_tutorias,
    tabla_administradores,
)
from .schema import mapper_registry

_mapped = False

def iniciar_mapeo() -> None:
    """
    Executes SQLAlchemy map_imperatively() to link classes and tables.
    Can be called once at application startup.
    """
    global _mapped
    if _mapped:
        return
    _mapped = True

    # 1. Independent entities
    mapper_registry.map_imperatively(Padrino, tabla_padrinos)
    mapper_registry.map_imperatively(Administrador, tabla_administradores)
    
    # We must map Referentes with their reverse relationship to Becario.
    # Since Becario is mapped later, we use string references for the relationship class.
    mapper_registry.map_imperatively(Tutor, tabla_tutores, properties={
        "lista_becarios": relationship(
            "Becario",
            back_populates="puntero_tutor",
            foreign_keys=[tabla_becarios.c.tutor_id],
            lazy="selectin"
        )
    })
    
    mapper_registry.map_imperatively(Mediador, tabla_mediadores, properties={
        "lista_becarios": relationship(
            "Becario",
            back_populates="puntero_mediador",
            foreign_keys=[tabla_becarios.c.mediador_id],
            lazy="selectin"
        )
    })

    # 2. DocumentoAcademico (belongs to DatosAcademicos)
    mapper_registry.map_imperatively(DocumentoAcademico, tabla_documentos_academicos)

    # 3. DatosAcademicos (belongs to Becario)
    mapper_registry.map_imperatively(DatosAcademicos, tabla_datos_academicos, properties={
        "lista_documentos": relationship(
            DocumentoAcademico,
            cascade="all, delete-orphan",
            lazy="joined",
        )
    })

    # 4. Becario dependent collections
    mapper_registry.map_imperatively(Tutoria, tabla_tutorias)
    mapper_registry.map_imperatively(EnvioCarta, tabla_envios_cartas)

    # 5. Becario (Aggregate Root)
    mapper_registry.map_imperatively(Becario, tabla_becarios, properties={
        # Composition relationships
        "datos_academicos": relationship(
            DatosAcademicos,
            uselist=False,
            cascade="all, delete-orphan"
        ),
        "lista_tutorias": relationship(
            Tutoria,
            cascade="all, delete-orphan",
            lazy="joined"
        ),
        "lista_envios_cartas": relationship(
            EnvioCarta,
            cascade="all, delete-orphan",
            lazy="joined"
        ),
        
        # Punteros (Associations)
        "puntero_tutor": relationship(
            Tutor,
            back_populates="lista_becarios",
            foreign_keys=[tabla_becarios.c.tutor_id],
            lazy="joined"
        ),
        "puntero_mediador": relationship(
            Mediador,
            back_populates="lista_becarios",
            foreign_keys=[tabla_becarios.c.mediador_id],
            lazy="joined"
        ),
        "puntero_padrino": relationship(
            Padrino,
            foreign_keys=[tabla_becarios.c.padrino_id],
            lazy="joined"
        ),
    })
