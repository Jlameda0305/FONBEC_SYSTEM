"""
Use case: CU03 - Llenar / Actualizar Formulario Académico.
"""

from datetime import datetime
from typing import Any

from src.application.protocols import BecarioRepositoryProtocol, IStorageServiceProtocol
from src.domain.models import DocumentoAcademico


class CU03_LlenarActualizarFormularioAcademico:
    """
    Orchestrates the update of a Becario's academic data and documents.
    """

    def __init__(
        self,
        repositorio: BecarioRepositoryProtocol,
        storage_service: IStorageServiceProtocol,
    ):
        self.repositorio = repositorio
        self.storage_service = storage_service

    def ejecutar(
        self,
        becario_id: str,
        datos: dict[str, Any],
        archivos: list[tuple[str, Any]],
    ) -> dict[str, Any]:
        """
        Executes the update of academic data.

        Args:
            becario_id: The ID of the Becario.
            datos: A dictionary containing the text fields to update.
            archivos: A list of tuples (filename, file_object).

        Returns:
            dict: The serialized DTO of the updated academic data.

        Raises:
            ValueError: If the Becario is not found, or file constraints fail.
            TypeError: If domain validations fail.
        """
        becario = self.repositorio.obtener_por_id(becario_id)
        if not becario:
            raise ValueError(f"Becario con ID '{becario_id}' no encontrado.")

        # 1. Validate files before any mutations or external calls
        for filename, file_obj in archivos:
            if not filename.lower().endswith(".pdf"):
                raise ValueError(f"Formato no permitido para '{filename}'. Solo se permiten archivos PDF.")
            
            # Enforce max 5MB. In a real Flask app, file_obj is a FileStorage.
            # We assume it has a read method or content_length. We check content_length if available.
            if hasattr(file_obj, "content_length") and getattr(file_obj, "content_length") is not None:
                if getattr(file_obj, "content_length") > 5 * 1024 * 1024:
                    raise ValueError(f"El archivo '{filename}' supera el tamaño máximo de 5MB.")

        # 2. Upload files and apply domain updates inside a rollback boundary
        try:
            for filename, file_obj in archivos:
                ruta_archivo = self.storage_service.subir_documento(file_obj, becario_id)
                documento = DocumentoAcademico(
                    tipo_documento="Certificado Académico",
                    ruta_archivo=ruta_archivo,
                    fecha_carga=datetime.now(),
                )
                becario.datos_academicos.agregar_documento(documento)

            # Update text data and evaluate verification state
            becario.llenar_actualizar_formulario_academico(datos)
            
        except Exception as e:
            # Re-raise the exception without calling guardar, effectively 
            # rolling back the transaction at the application level.
            raise e

        # 3. Persist changes
        self.repositorio.guardar(becario)

        # 4. Return serialized DTO
        return becario.datos_academicos.to_dict()
