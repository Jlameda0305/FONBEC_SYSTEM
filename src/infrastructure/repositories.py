"""
Concrete repository implementations using SQLAlchemy.

These classes satisfy the Protocols defined in the Application layer,
bridging the domain model to the physical PostgreSQL/Supabase database.
"""

from typing import Optional

from sqlalchemy.orm import Session, joinedload

from src.application.protocols import BecarioRepositoryProtocol, TutorRepositoryProtocol, UsuarioRepositoryProtocol, PadrinoRepositoryProtocol
from src.domain.actors.becario import Becario
from src.domain.actors.tutor import Tutor
from src.domain.actors.mediador import Mediador
from src.domain.actors.administrador import Administrador
from src.domain.actors.abstract_actor import Usuario
from src.domain.domain_entities.padrino import Padrino
from src.infrastructure.schema import tabla_becarios


class SQLAlchemyTutorRepository(TutorRepositoryProtocol):
    """
    Concrete implementation of TutorRepositoryProtocol using SQLAlchemy.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def obtener_por_id(self, tutor_id: str) -> Optional[Tutor]:
        """
        Retrieve a Tutor by its user ID. Eagerly loads its list of Becarios 
        and their respective DatosAcademicos to prevent N+1 queries.
        """
        return (
            self.session.query(Tutor)
            .options(
                joinedload(Tutor.lista_becarios)
                .joinedload(Becario.datos_academicos)
            )
            .filter_by(id_usuario=tutor_id)
            .first()
        )

    def guardar(self, tutor: Tutor) -> None:
        """
        Persists the Tutor aggregate back to the storage backend.
        Because of the cascade relationships, this synchronizes the Becarios 
        and their nested compositions.
        """
        self.session.add(tutor)
        self.session.commit()


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


class SQLAlchemyUsuarioRepository(UsuarioRepositoryProtocol):
    """
    Concrete implementation of UsuarioRepositoryProtocol using SQLAlchemy.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def obtener_por_id(self, id_usuario: str) -> Optional[Usuario]:
        for cls in [Becario, Tutor, Mediador, Administrador, Padrino]:
            user = self.session.query(cls).filter_by(id_usuario=id_usuario).first()
            if user:
                return user
        return None

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        for cls in [Becario, Tutor, Mediador, Administrador, Padrino]:
            user = self.session.query(cls).filter_by(email=email).first()
            if user:
                return user
        return None

    def guardar(self, usuario: Usuario) -> None:
        """
        Persists a generic Usuario (Becario, Tutor, Mediador, Administrador) to the database.
        """
        self.session.add(usuario)
        self.session.commit()

    def listar_usuarios(
        self,
        limite: int,
        offset: int,
        rol: str,
        busqueda: Optional[str] = None,
    ) -> tuple[list[Usuario], int]:
        """
        Retrieves actors paginated. Since Concrete Table Inheritance is used,
        the role MUST be provided to determine which physical table to query.
        """
        from sqlalchemy import or_

        clases_map = {
            "becario": Becario,
            "tutor": Tutor,
            "mediador": Mediador,
            "administrador": Administrador,
            "padrino": Padrino
        }

        cls = clases_map.get(rol.lower())
        if not cls:
            raise ValueError(f"Rol '{rol}' no soportado.")

        query = self.session.query(cls)

        if busqueda:
            termino = f"%{busqueda}%"
            query = query.filter(
                or_(
                    cls.nombre.ilike(termino),
                    cls.apellido.ilike(termino),
                    cls.email.ilike(termino)
                )
            )

        # Applying Limit and Offset strictly to avoid Eager Loading massive memory bloat
        total = query.count()
        resultados = query.offset(offset).limit(limite).all()
        return resultados, total

class SQLAlchemyPadrinoRepository(PadrinoRepositoryProtocol):
    """
    Concrete implementation of PadrinoRepositoryProtocol using SQLAlchemy.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def crear_padrino(self, padrino: Padrino) -> None:
        self.session.add(padrino)
        self.session.commit()

    def obtener_padrino_por_id(self, id_padrino: str) -> Optional[Padrino]:
        return self.session.query(Padrino).filter_by(id_padrino=id_padrino).first()

    def actualizar_padrino(self, padrino: Padrino) -> None:
        self.session.add(padrino)
        self.session.commit()

    def eliminar_padrino(self, id_padrino: str) -> None:
        # Check if any Becario uses this Padrino
        # Since we use concrete table mapping, we query Becario directly
        becarios_asignados = self.session.query(Becario).filter(tabla_becarios.c.padrino_id == id_padrino).count()
        if becarios_asignados > 0:
            raise ValueError("debes eliminar la relacion antes de eliminar al padrino")
        
        padrino = self.obtener_padrino_por_id(id_padrino)
        if padrino:
            self.session.delete(padrino)
            self.session.commit()

