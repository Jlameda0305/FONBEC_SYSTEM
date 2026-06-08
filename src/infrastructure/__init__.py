"""
Infrastructure package mapping domain models to database tables.
"""

from .mapping import iniciar_mapeo
from .schema import metadata

__all__ = ["iniciar_mapeo", "metadata"]
