"""
Application layer protocols (interfaces).

Defines the contracts that the Infrastructure layer must implement
to satisfy the Dependency Inversion Principle. Use Cases depend on
these abstractions, never on concrete repositories.
"""

from typing import Optional, Protocol

from src.domain.models import Becario


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

    def subir_documento(self, archivo: object, becario_id: str) -> str:
        """
        Uploads an academic document to the storage backend.

        Args:
            archivo: The file-like object to upload.
            becario_id: The ID of the Becario owning the document.

        Returns:
            str: The unique URL or access path of the uploaded file.
        """
        ...
