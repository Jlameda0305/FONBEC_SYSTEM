"""
Supabase Storage implementation.
"""
import os
import time
from typing import Any

from supabase import create_client, Client

from src.application.protocols import IStorageServiceProtocol


class SupabaseStorageServiceImpl(IStorageServiceProtocol):
    """
    Concrete implementation of the storage service using Supabase.
    """

    def __init__(self) -> None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_ANON_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment.")
        self.supabase: Client = create_client(url, key)
        self.bucket_name = "documentos_academicos"

    def subir_documento(self, archivo: Any, becario_id: str) -> str:
        """
        Uploads a file to Supabase storage.

        Args:
            archivo: File-like object to upload.
            becario_id: ID of the becario for path organization.

        Returns:
            The public URL of the uploaded document.
        """
        if hasattr(archivo, "read"):
            file_bytes = archivo.read()
        else:
            raise ValueError("El archivo provisto no tiene un método read().")

        timestamp = int(time.time())
        path_on_supa = f"becarios/{becario_id}/formulario_{timestamp}.pdf"

        # Upload using the supabase-py SDK
        self.supabase.storage.from_(self.bucket_name).upload(
            path=path_on_supa,
            file=file_bytes,
            file_options={"content-type": "application/pdf"}
        )

        public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(path_on_supa)
        return public_url
