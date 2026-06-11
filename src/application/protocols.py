"""
Application layer protocols (interfaces).

Defines the contracts that the Infrastructure layer must implement
to satisfy the Dependency Inversion Principle. Use Cases depend on
these abstractions, never on concrete repositories.
"""

from typing import Optional, Protocol, List, Dict, Any

from src.domain.models import Becario, Tutor, Usuario


class TutorRepositoryProtocol(Protocol):
    """
    Abstract contract for accessing Tutor persistence.
    """

    def obtener_por_id(self, tutor_id: str) -> Optional[Tutor]:
        """
        Retrieve a Tutor aggregate by its unique user ID.

        Args:
            tutor_id: The unique identifier of the Tutor.

        Returns:
            The Tutor instance if found, None otherwise.
        """
        ...

    def guardar(self, tutor: Tutor) -> None:
        """
        Persist the Tutor aggregate back to the storage backend.

        Args:
            tutor: The Tutor instance to save.
        """
        ...


class BecarioRepositoryProtocol(Protocol):
    """
    Abstract contract for accessing Becario persistence.

    Any concrete implementation (SQLAlchemy, in-memory, mock) must
    satisfy this interface to be injectable into Use Cases.
    """

    def obtener_por_id(self, becario_id: str) -> Optional[Becario]:
        """
        Retrieve a Becario aggregate by its unique user ID.

        Args:
            becario_id: The unique identifier of the Becario.

        Returns:
            The Becario instance if found, None otherwise.
        """
        ...

    def guardar(self, becario: Becario) -> None:
        """
        Persist the Becario aggregate back to the storage backend.

        Args:
            becario: The Becario instance to save.
        """
        ...


class IStorageServiceProtocol(Protocol):
    """
    Abstract contract for handling file storage operations.
    """

    def subir_documento(
        self,
        archivo: object,
        becario_id: str,
        tipo_documento: str,
        nombre_completo: str,
    ) -> str:
        """
        Uploads an academic document to the storage backend.

        Args:
            archivo: The file-like object to upload.
            becario_id: The ID of the Becario owning the document.
            tipo_documento: Explicit document classification
                (e.g. "Programa", "CartaCompromiso", "Inscripcion").
            nombre_completo: Full name of the Becario, used for
                file naming (e.g. "Juan_Perez").

        Returns:
            str: The public URL or access path of the uploaded file.
        """
        ...

    def eliminar_documento_por_url(self, ruta_archivo: str) -> None:
        """
        Deletes an academic document from the storage backend using its URL.

        Parses the URL to extract the deterministic object path and removes it.

        Args:
            ruta_archivo: The full public URL or access path of the uploaded file.

        Raises:
            Exception: If the storage backend reports an error.
        """
        ...


class UsuarioRepositoryProtocol(Protocol):
    """
    Abstract contract for querying multiple users (actors) with pagination and filtering.
    """

    def listar_usuarios(
        self,
        limite: int,
        offset: int,
        rol: Optional[str] = None,
        busqueda: Optional[str] = None,
    ) -> List[Usuario]:
        """
        Retrieves a paginated list of actors matching the criteria.

        Args:
            limite: Maximum number of records to return.
            offset: Number of records to skip.
            rol: Filter by specific role (e.g., 'becario', 'tutor').
            busqueda: Case-insensitive partial match on name, surname, or email.

        Returns:
            A list of Usuario (or its subclasses) instances.
        """
        ...
