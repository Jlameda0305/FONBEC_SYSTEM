from src.application.dto_mapper import usuario_to_dict, datos_academicos_to_dict
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
            archivos: A list of tuples (tipo_documento, file_object).
                      tipo_documento is an explicit classification key
                      (e.g. "Programa", "CartaCompromiso", "Inscripcion").

        Returns:
            dict: The serialized DTO of the updated academic data.

        Raises:
            ValueError: If the Becario is not found, or file constraints fail.
            TypeError: If domain validations fail.
        """
        becario = self.repositorio.obtener_por_id(becario_id)
        if not becario:
            raise ValueError(f"Becario con ID '{becario_id}' no encontrado.")

        nombre_completo = f"{becario.nombre}_{becario.apellido}".replace(" ", "_")

        # 1. Validate files before any mutations
        for tipo_documento, file_obj in archivos:
            if isinstance(tipo_documento, str) and "." in tipo_documento:
                if not tipo_documento.lower().endswith(".pdf"):
                    raise ValueError(
                        f"Formato no permitido para '{tipo_documento}'. "
                        "Solo se permiten archivos PDF."
                    )

            if hasattr(file_obj, "content_length") and getattr(file_obj, "content_length") is not None:
                if getattr(file_obj, "content_length") > 5 * 1024 * 1024:
                    raise ValueError(
                        f"El archivo '{tipo_documento}' supera el tamaño máximo de 5MB."
                    )

        # 2. Update domain FIRST (evaluates all business rules and raises immediately if invalid)
        becario.llenar_actualizar_formulario_academico(datos)

        # 3. If domain is valid, upload files to Supabase Storage
        archivos_subidos = []
        try:
            for tipo_documento, file_obj in archivos:
                ruta_archivo = self.storage_service.subir_documento(
                    file_obj, becario_id, tipo_documento, nombre_completo
                )
                archivos_subidos.append(ruta_archivo)
                documento = DocumentoAcademico(
                    tipo_documento=tipo_documento,
                    ruta_archivo=ruta_archivo,
                    fecha_carga=datetime.now(),
                )
                becario.datos_academicos.agregar_documento(documento)

            # 4. Persist changes to SQL Database
            self.repositorio.guardar(becario)

        except Exception as e:
            # Compensatory transaction (Saga pattern):
            # If the database save fails (e.g. network partition), or an upload fails midway,
            # we must delete the successfully uploaded physical files to prevent orphans.
            for ruta in archivos_subidos:
                try:
                    self.storage_service.eliminar_documento_por_url(ruta)
                except Exception:
                    pass # Best effort cleanup
            raise e

        # 5. Return serialized DTO
        return datos_academicos_to_dict(becario.datos_academicos)
