"""
Database schema definition using SQLAlchemy Core.
Implements the 3NF physical tables for the FONBEC system without any
database connections or engine configurations.
"""

from sqlalchemy import (
    ARRAY,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
)
from sqlalchemy.orm import registry

from src.domain.enums import (
    EstadoEnvioCarta,
    EstadoTutoria,
    EstadoVerificacion,
    NivelCursado,
)

# Create the global registry and metadata
mapper_registry = registry()
metadata = mapper_registry.metadata

# ==========================================
# Independent Entities (No outward FKs)
# ==========================================

tabla_padrinos = Table(
    "padrinos",
    metadata,
    Column("id_padrino", String, primary_key=True),
    Column("nombre", String, nullable=False),
    Column("apellido", String, nullable=False),
    Column("email", String, nullable=False),
    Column("telefono", String, nullable=False),
    Column("direccion", String, nullable=False),
)

# ==========================================
# Concrete Table Inheritance: Usuario Hierarchy
# ==========================================
# The abstract 'Usuario' and 'Referente' classes are flattened into these tables.

tabla_tutores = Table(
    "tutores",
    metadata,
    # Inherited from Usuario
    Column("id_usuario", String, primary_key=True),
    Column("nombre", String, nullable=False),
    Column("apellido", String, nullable=False),
    Column("email", String, nullable=False),
    Column("telefono", String, nullable=False),
    Column("edad", Integer, nullable=False),
    Column("sexo", String, nullable=False),
    Column("direccion", String, nullable=False),
    Column("rol", String, nullable=False, default="tutor"),
)

tabla_administradores = Table(
    "administradores",
    metadata,
    # Inherited from Usuario
    Column("id_usuario", String, primary_key=True),
    Column("nombre", String, nullable=False),
    Column("apellido", String, nullable=False),
    Column("email", String, nullable=False),
    Column("telefono", String, nullable=False),
    Column("edad", Integer, nullable=False),
    Column("sexo", String, nullable=False),
    Column("direccion", String, nullable=False),
    Column("rol", String, nullable=False, default="administrador"),
)

tabla_mediadores = Table(
    "mediadores",
    metadata,
    # Inherited from Usuario
    Column("id_usuario", String, primary_key=True),
    Column("nombre", String, nullable=False),
    Column("apellido", String, nullable=False),
    Column("email", String, nullable=False),
    Column("telefono", String, nullable=False),
    Column("edad", Integer, nullable=False),
    Column("sexo", String, nullable=False),
    Column("direccion", String, nullable=False),
    Column("rol", String, nullable=False, default="mediador"),
)

tabla_becarios = Table(
    "becarios",
    metadata,
    # Inherited from Usuario
    Column("id_usuario", String, primary_key=True),
    Column("nombre", String, nullable=False),
    Column("apellido", String, nullable=False),
    Column("email", String, nullable=False),
    Column("telefono", String, nullable=False),
    Column("edad", Integer, nullable=False),
    Column("sexo", String, nullable=False),
    Column("direccion", String, nullable=False),
    Column("rol", String, nullable=False, default="becario"),
    
    # Becario specific attributes
    Column("nivel_cursado", Enum(NivelCursado), nullable=True),
    
    # Punteros (Associations)
    Column("tutor_id", String, ForeignKey("tutores.id_usuario"), nullable=True),
    Column("mediador_id", String, ForeignKey("mediadores.id_usuario"), nullable=True),
    Column("padrino_id", String, ForeignKey("padrinos.id_padrino"), nullable=True),
)

# ==========================================
# Dependent Entities (FKs back to Becario)
# ==========================================

tabla_datos_academicos = Table(
    "datos_academicos",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("becario_id", String, ForeignKey("becarios.id_usuario"), nullable=False, unique=True),
    Column("nombre_carrera", String, nullable=True),
    Column("anio_ingreso", Integer, nullable=True),
    Column("anio_en_curso", Integer, nullable=True),
    Column("materias_a_cursar", ARRAY(String), nullable=False, default=[]),
    Column("materias_adeudadas", ARRAY(String), nullable=False, default=[]),
    Column("estado_verificacion", Enum(EstadoVerificacion), nullable=False),
    Column("observaciones", String, nullable=True),
    Column("fecha_observacion", DateTime, nullable=True),
)

tabla_documentos_academicos = Table(
    "documentos_academicos",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("datos_academicos_id", Integer, ForeignKey("datos_academicos.id"), nullable=False),
    Column("tipo_documento", String, nullable=False),
    Column("ruta_archivo", String, nullable=False),
    Column("fecha_carga", DateTime, nullable=False),
)

tabla_tutorias = Table(
    "tutorias",
    metadata,
    Column("id_tutoria", String, primary_key=True),
    Column("becario_id", String, ForeignKey("becarios.id_usuario"), nullable=False),
    Column("fecha_hora", DateTime, nullable=False),
    Column("estado", Enum(EstadoTutoria), nullable=False),
)

tabla_envios_cartas = Table(
    "envios_cartas",
    metadata,
    Column("id_envio", String, primary_key=True),
    Column("becario_id", String, ForeignKey("becarios.id_usuario"), nullable=False),
    Column("fecha_envio", DateTime, nullable=False),
    Column("estado", Enum(EstadoEnvioCarta), nullable=False),
)
