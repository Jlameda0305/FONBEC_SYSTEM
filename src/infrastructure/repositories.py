"""
Concrete repository implementations using SQLAlchemy.

These classes satisfy the Protocols defined in the Application layer,
bridging the domain model to the physical PostgreSQL/Supabase database.
"""

from typing import Optional

from sqlalchemy.orm import Session, joinedload

from src.application.protocols import BecarioRepositoryProtocol
from src.domain.models import Becario


class SQLAlchemyBecarioRepository(BecarioRepositoryProtocol):
    """
    Concrete implementation of BecarioRepositoryProtocol using SQLAlchemy.

    Uses the imperative mapping configured in mapping.py to query the
    'becarios' table and hydrate Becario domain entities.
    """

    def __init__(self, session: Session) -> None:
        """
        Initialize the repository with an active SQLAlchemy session.

        Args:
            session: An active SQLAlchemy Session instance. The caller
                     is responsible for managing the session lifecycle
                     (commit, rollback, close).
        """
        self.session = session

    def obtener_por_id(self, becario_id: str) -> Optional[Becario]:
        """
        Retrieve a Becario aggregate by its unique user ID.

        Uses joinedload to eagerly fetch the datos_academicos composition
        in a single SQL query (LEFT OUTER JOIN), preventing the N+1
        problem and DetachedInstanceError when the Application layer
        serializes the entity outside the session context.

        Args:
            becario_id: The unique identifier of the Becario (id_usuario).

        Returns:
            The fully hydrated Becario instance if found, None otherwise.
        """
        return (
            self.session.query(Becario)
            .options(joinedload(Becario.datos_academicos))
            .filter_by(id_usuario=becario_id)
            .first()
        )

    def guardar(self, becario: Becario) -> None:
        """
        Persists the Becario aggregate back to the storage backend.
        Because of the cascade="all, delete-orphan" relationships in the SQLAlchemy mapping,
        adding the aggregate automatically synchronizes its nested compositions.
        """
        self.session.add(becario)
        self.session.commit()
