"""
Supabase Storage implementation.
"""
import os
import re
import time
from typing import Any

from supabase import create_client, Client

from src.application.protocols import IStorageServiceProtocol


class SupabaseStorageServiceImpl(IStorageServiceProtocol):
    """
    Concrete implementation of the storage service using Supabase.

    File naming convention:
        becarios/{becario_id}/{tipo_documento}_{nombre_completo}.pdf

    Examples:
        becarios/bec-001/Programa_Juan_Perez.pdf
        becarios/bec-001/CartaCompromiso_Juan_Perez.pdf
        becarios/bec-001/Inscripcion_Juan_Perez.pdf

    Upsert behaviour:
        When a file with the same path already exists it is replaced
        (upsert=true), so re-submitting the form overwrites the
        previous version without creating duplicates.
    """

    def __init__(self) -> None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_ANON_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment.")
        self.supabase: Client = create_client(url, key)
        self.bucket_name = "documentos_academicos"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitizar(texto: str) -> str:
        """
        Replace whitespace with underscores and strip characters that
        are unsafe for object-storage paths (keeps alphanumeric, dash,
        underscore).
        """
        texto = texto.strip().replace(" ", "_")
        texto = re.sub(r"[^\w\-]", "", texto)
        return texto

    # ------------------------------------------------------------------
    # Protocol implementation
    # ------------------------------------------------------------------

    def subir_documento(
        self,
        archivo: Any,
        becario_id: str,
        tipo_documento: str,
        nombre_completo: str,
    ) -> str:
        """
        Uploads a file to Supabase storage using a deterministic path.

        Args:
            archivo: File-like object with a read() method.
            becario_id: ID of the becario for path organization.
            tipo_documento: Document classification key
                (e.g. "Programa", "CartaCompromiso", "Inscripcion").
            nombre_completo: Full name of the becario
                (e.g. "Juan Perez" → sanitized to "Juan_Perez").

        Returns:
            The public URL of the uploaded document.
        """
        if hasattr(archivo, "read"):
            file_bytes = archivo.read()
        else:
            raise ValueError("El archivo provisto no tiene un método read().")

        tipo_safe = self._sanitizar(tipo_documento)
        nombre_safe = self._sanitizar(nombre_completo)

        path_on_supa = f"becarios/{becario_id}/{tipo_safe}_{nombre_safe}.pdf"

        # upsert=true ensures re-uploads replace the previous version
        self.supabase.storage.from_(self.bucket_name).upload(
            path=path_on_supa,
            file=file_bytes,
            file_options={
                "content-type": "application/pdf",
                "upsert": "true",
            },
        )

        public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(path_on_supa)
        return public_url

    def eliminar_documento_por_url(self, ruta_archivo: str) -> None:
        """
        Deletes a file from Supabase Storage by extracting the path from the URL.

        Args:
            ruta_archivo: The full public URL of the uploaded file.

        Raises:
            Exception: If the Supabase API returns an error.
        """
        # A typical public URL looks like:
        # https://[PROJECT_ID].supabase.co/storage/v1/object/public/[BUCKET_NAME]/becarios/bec-003/Programa_Maria.pdf
        # We need to extract the part after the bucket name.
        delimiter = f"/{self.bucket_name}/"
        if delimiter not in ruta_archivo:
            raise ValueError(f"La URL proporcionada no pertenece al bucket '{self.bucket_name}'.")
        
        path_on_supa = ruta_archivo.split(delimiter, 1)[1]

        # Call remove using the extracted path
        response = self.supabase.storage.from_(self.bucket_name).remove([path_on_supa])
        
        # 'remove' returns a list of dictionaries of successfully deleted objects.
        # If the file didn't exist or deletion failed, we may get an empty list or an exception.
        if not response:
             # Depending on the supabase-py version, we might need to raise if it's empty
             # But if it's already deleted, that's fine.
             pass
