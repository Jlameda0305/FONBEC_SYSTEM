"""
Application layer protocols (interfaces).

Defines the contracts that the Infrastructure layer must implement
to satisfy the Dependency Inversion Principle. Use Cases depend on
these abstractions, never on concrete repositories.
"""

from typing import Optional, Protocol, List, Dict, Any

from src.domain.actors.becario import Becario
from src.domain.actors.tutor import Tutor
from src.domain.actors.abstract_actor import Usuario
from src.domain.domain_entities.padrino import Padrino


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
        rol: str,
        busqueda: Optional[str] = None,
    ) -> tuple[List[Usuario], int]:
        """
        Retrieves a paginated list of actors matching the criteria.

        Args:
            limite: Maximum number of records to return.
            offset: Number of records to skip.
            rol: Filter by specific role (e.g., 'becario', 'tutor').
            busqueda: Case-insensitive partial match on name, surname, or email.

        Returns:
            A tuple containing a list of Usuario (or its subclasses) instances and the total count.
        """
        ...

    def obtener_por_id(self, id_usuario: str) -> Optional[Usuario]:
        """
        Retrieve a generic Usuario by its ID.
        """
        ...

    def obtener_por_id_y_rol(self, id_usuario: str, rol: str) -> Optional[Usuario]:
        """
        Retrieve a generic Usuario by its ID and explicitly known role.
        """
        ...

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        """
        Retrieve a generic Usuario by its email.
        """
        ...

    def guardar(self, usuario: Usuario) -> None:
        """
        Persists a generic Usuario to the database.
        """
        ...

class PadrinoRepositoryProtocol(Protocol):
    """
    Abstract contract for accessing Padrino persistence.
    """

    def crear_padrino(self, padrino: "Padrino") -> None:
        """Create a new Padrino."""
        ...

    def obtener_padrino_por_id(self, id_padrino: str) -> Optional["Padrino"]:
        """Retrieve a Padrino by ID."""
        ...

    def actualizar_padrino(self, padrino: "Padrino") -> None:
        """Update an existing Padrino."""
        ...

    def eliminar_padrino(self, id_padrino: str) -> None:
        """
        Delete a Padrino by ID.
        Must check for assigned Becarios and raise ValueError if any exist.
        """
        ...


class AuthServiceProtocol(Protocol):
    """
    Abstract contract for handling authentication and authorization operations.
    """

    def invitar_usuario(self, email: str, rol: str) -> str:
        """
        Invites a user by email and assigns them a predefined role.

        Args:
            email: The email address to invite.
            rol: The role to assign (e.g., 'becario', 'administrador').

        Returns:
            The user ID of the invited user or a status message.
        """
        ...

    def intercambiar_codigo(self, code: str) -> dict:
        """
        Exchanges an auth code for a session.
        Returns dict with access_token and refresh_token.
        """
        ...

    def obtener_usuario(self, access_token: str) -> Optional[dict]:
        """
        Retrieves user information using an access token.

        Args:
            access_token: The auth access token.

        Returns:
            A dictionary containing user info if valid, None otherwise.
        """
        ...

    def establecer_contrasena(self, access_token: str, nueva_contrasena: str, refresh_token: str) -> None:
        """
        Sets a new password for the authenticated user.
        
        Args:
            access_token: The session access token.
            nueva_contrasena: The new password to set.
            refresh_token: The session refresh token.
        """
        ...

    def login(self, email: str, password: str) -> dict:
        """
        Authenticates a user with email and password.
        
        Returns:
            dict containing access_token, refresh_token, and user object.
        """
        ...

    def recuperar_contrasena(self, email: str) -> None:
        """
        Initiates a password recovery process via email.
        """
        ...

    def logout(self, access_token: str) -> None:
        """
        Invalidates a session remotely using an access token.
        
        Args:
            access_token: The session access token to invalidate.
        """
        ...

