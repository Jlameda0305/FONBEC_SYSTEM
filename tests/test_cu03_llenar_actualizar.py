"""
Unit tests for the CU03_LlenarActualizarFormularioAcademico Use Case.
"""

import sys
import os
import unittest
from typing import Optional

from src.application.protocols import BecarioRepositoryProtocol, IStorageServiceProtocol
from src.application.use_cases.CU03_LlenarActualizarFormularioAcademico import CU03_LlenarActualizarFormularioAcademico
from src.domain.models import Becario


class MockFile:
    def __init__(self, size: int):
        self.content_length = size


class MockBecarioRepository(BecarioRepositoryProtocol):
    def __init__(self, becario: Optional[Becario] = None):
        self.becario = becario
        self.guardado = False

    def obtener_por_id(self, becario_id: str) -> Optional[Becario]:
        if self.becario and self.becario.id_usuario == becario_id:
            return self.becario
        return None

    def guardar(self, becario: Becario) -> None:
        self.guardado = True


class MockStorageService(IStorageServiceProtocol):
    def __init__(self, fail_on_upload: bool = False):
        self.fail_on_upload = fail_on_upload
        self.uploaded: list[dict] = []
        self.deleted: list[dict] = []

    def subir_documento(
        self,
        archivo: object,
        becario_id: str,
        tipo_documento: str,
        nombre_completo: str,
    ) -> str:
        if self.fail_on_upload:
            raise Exception("Network error simulating storage failure")
        self.uploaded.append({
            "becario_id": becario_id,
            "tipo_documento": tipo_documento,
            "nombre_completo": nombre_completo,
        })
        return f"/mock/path/{becario_id}/{tipo_documento}_{nombre_completo}.pdf"

    def eliminar_documento(
        self,
        becario_id: str,
        tipo_documento: str,
        nombre_completo: str,
    ) -> None:
        self.deleted.append({
            "becario_id": becario_id,
            "tipo_documento": tipo_documento,
            "nombre_completo": nombre_completo,
        })


def _make_becario() -> Becario:
    return Becario(
        id_usuario="bec-123",
        nombre="Test",
        apellido="User",
        email="test@example.com",
        telefono="+5491100000000",
        edad=20,
        sexo="M",
        direccion="Fake St 123",
        password_hash="hash"
    )


class TestCU03LlenarActualizarFormularioAcademico(unittest.TestCase):

    def setUp(self):
        self.becario = _make_becario()
        self.repo = MockBecarioRepository(self.becario)
        self.storage = MockStorageService()
        self.use_case = CU03_LlenarActualizarFormularioAcademico(self.repo, self.storage)

    def test_ejecutar_exitoso(self):
        """Should upload files, update domain, and save the aggregate."""
        archivos = [("Programa", MockFile(1024))]
        datos = {"nombre_carrera": "Abogacía"}
        
        result = self.use_case.ejecutar("bec-123", datos, archivos)
        
        self.assertTrue(self.repo.guardado)
        self.assertEqual(result["nombre_carrera"], "Abogacía")
        self.assertEqual(len(self.becario.datos_academicos.lista_documentos), 1)
        # Verify document type is preserved from the explicit key
        doc = self.becario.datos_academicos.lista_documentos[0]
        self.assertEqual(doc.tipo_documento, "Programa")
        # Verify documentos map is present in DTO
        self.assertIn("Programa", result["documentos"])

    def test_ejecutar_multiples_documentos(self):
        """Should handle uploading all three document types."""
        archivos = [
            ("Programa", MockFile(1024)),
            ("CartaCompromiso", MockFile(2048)),
            ("Inscripcion", MockFile(512)),
        ]
        datos = {"nombre_carrera": "Ingeniería"}
        
        result = self.use_case.ejecutar("bec-123", datos, archivos)
        
        self.assertTrue(self.repo.guardado)
        self.assertEqual(len(self.becario.datos_academicos.lista_documentos), 3)
        tipos = [d.tipo_documento for d in self.becario.datos_academicos.lista_documentos]
        self.assertEqual(tipos, ["Programa", "CartaCompromiso", "Inscripcion"])

    def test_upsert_reemplaza_documento_existente(self):
        """Uploading the same tipo_documento twice should replace, not duplicate."""
        archivos_1 = [("Programa", MockFile(1024))]
        self.use_case.ejecutar("bec-123", {"nombre_carrera": "Derecho"}, archivos_1)
        self.assertEqual(len(self.becario.datos_academicos.lista_documentos), 1)
        url_original = self.becario.datos_academicos.lista_documentos[0].ruta_archivo

        # Reset repo.guardado for second call
        self.repo.guardado = False
        archivos_2 = [("Programa", MockFile(2048))]
        self.use_case.ejecutar("bec-123", {"nombre_carrera": "Derecho"}, archivos_2)

        # Should still be 1, not 2
        self.assertEqual(len(self.becario.datos_academicos.lista_documentos), 1)
        self.assertTrue(self.repo.guardado)

    def test_nombre_completo_en_storage(self):
        """Should pass the sanitized full name to the storage service."""
        archivos = [("Programa", MockFile(1024))]
        self.use_case.ejecutar("bec-123", {"nombre_carrera": "Derecho"}, archivos)
        
        self.assertEqual(len(self.storage.uploaded), 1)
        self.assertEqual(self.storage.uploaded[0]["nombre_completo"], "Test_User")
        self.assertEqual(self.storage.uploaded[0]["tipo_documento"], "Programa")

    def test_fallo_formato_archivo_legacy(self):
        """Should reject non-PDF files when filename is passed (backwards compat)."""
        archivos = [("foto.jpg", MockFile(1024))]
        with self.assertRaises(ValueError) as ctx:
            self.use_case.ejecutar("bec-123", {}, archivos)
            
        self.assertIn("Solo se permiten archivos PDF", str(ctx.exception))
        self.assertFalse(self.repo.guardado)

    def test_fallo_tamanio_archivo(self):
        """Should reject files over 5MB and NOT call guardar()."""
        archivos = [("Programa", MockFile(6 * 1024 * 1024))]
        with self.assertRaises(ValueError) as ctx:
            self.use_case.ejecutar("bec-123", {}, archivos)
            
        self.assertIn("supera el tamaño máximo", str(ctx.exception))
        self.assertFalse(self.repo.guardado)

    def test_rollback_si_falla_storage(self):
        """If storage fails, should raise exception and NOT call guardar()."""
        self.storage.fail_on_upload = True
        archivos = [("Programa", MockFile(1024))]
        
        with self.assertRaises(Exception) as ctx:
            self.use_case.ejecutar("bec-123", {"nombre_carrera": "Medicina"}, archivos)
            
        self.assertIn("Network error", str(ctx.exception))
        self.assertFalse(self.repo.guardado)

    def test_becario_no_encontrado(self):
        """Should raise ValueError if becario does not exist."""
        with self.assertRaises(ValueError):
            self.use_case.ejecutar("no-existe", {}, [])


if __name__ == "__main__":
    unittest.main()
