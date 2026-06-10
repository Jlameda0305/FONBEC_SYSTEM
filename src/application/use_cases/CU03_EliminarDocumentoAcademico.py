"""
Use case: CU03 - Eliminar Documento Académico.

Allows a Becario to remove a specific academic document (by type)
from both Supabase Storage and the domain entity.
"""

from typing import Any

from src.application.protocols import BecarioRepositoryProtocol, IStorageServiceProtocol


class CU03_EliminarDocumentoAcademico:
    """
    Orchestrates the deletion of a single academic document.

    Flow:
        1. Load the Becario aggregate from the repository.
        2. Build the nombre_completo for path reconstruction.
        3. Delete the physical file from Storage.
        4. Remove the reference from the domain entity.
        5. Persist changes.
    """

    def __init__(
        self,
        repositorio: BecarioRepositoryProtocol,
        storage_service: IStorageServiceProtocol,
    ):
        self.repositorio = repositorio
        self.storage_service = storage_service

    def ejecutar(self, becario_id: str, tipo_documento: str) -> dict[str, Any]:
        """
        Execute the document deletion.

        Args:
            becario_id: The unique identifier of the Becario.
            tipo_documento: The classification key of the document to delete
                (e.g. "Programa", "CartaCompromiso", "Inscripcion").

        Returns:
            dict: The serialized DTO of the updated academic data.

        Raises:
            ValueError: If the Becario is not found or no document of
                that type exists.
        """
        becario = self.repositorio.obtener_por_id(becario_id)
        if not becario:
            raise ValueError(f"Becario con ID '{becario_id}' no encontrado.")

        # 1. Find the actual document to extract its exact URL
        documento_a_borrar = None
        for doc in becario.datos_academicos.lista_documentos:
            if doc.tipo_documento == tipo_documento:
                documento_a_borrar = doc
                break
                
        if not documento_a_borrar:
            raise ValueError(f"No existe un documento de tipo '{tipo_documento}' para eliminar.")

        ruta_archivo = documento_a_borrar.ruta_archivo

        # 2. Delete from physical storage using the exact public URL
        try:
            self.storage_service.eliminar_documento_por_url(ruta_archivo)
        except ValueError as ve:
             # URL parsing error
             print(f"Warning: URL no pertenece a este bucket o es inválida: {ve}")
        except Exception as e:
            error_str = str(e).lower()
            if "not found" not in error_str and "object not found" not in error_str:
                # If it's a network, auth, or DB error, we must abort
                raise RuntimeError(f"Error crítico al borrar archivo físico en Supabase: {str(e)}")
            # If it just doesn't exist, we proceed to clean up the DB safely

        # 3. Remove from domain entity
        becario.datos_academicos.eliminar_documento(tipo_documento)

        # 4. Persist
        self.repositorio.guardar(becario)

        # 5. Return updated DTO
        return becario.datos_academicos.to_dict()
