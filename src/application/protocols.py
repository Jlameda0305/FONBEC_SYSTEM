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
